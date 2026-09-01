using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Geometry;
using StarCluster.Core.Movement;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

public sealed class ScenarioExecutor
{
    private readonly ScenarioDocument _document;
    private readonly ScenarioExecutionPlan _executionPlan;
    private readonly ScenarioInitializationResult _runtime;
    private readonly IMissileInterceptionResolver _interceptionResolver;
    private readonly IMissileTerminalRandomSource _terminalRandomSource;
    private readonly List<MissileInterceptionOpportunity> _interceptionOpportunities = new();
    private readonly List<MissileInterceptionAttemptResult> _interceptionAttempts = new();
    private readonly List<ScenarioTerminalOpportunity> _terminalOpportunities = new();
    private readonly Dictionary<string, ScenarioTerminalOpportunitySource>
        _pendingColocationSources = new(StringComparer.Ordinal);
    private readonly ScenarioExecutionOptions _options;
    private readonly ScenarioExecutionMetrics? _metrics;
    private readonly ScenarioAllocationProfile? _allocationProfile;
    private MissileInterceptionPhaseContext? _interceptionContext;

    public ScenarioExecutor(
        ScenarioDocument document,
        ScenarioExecutionOptions? options = null)
        : this(ScenarioExecutionPlan.Prepare(document), options)
    {
    }

    public ScenarioExecutor(
        ScenarioExecutionPlan executionPlan,
        ScenarioExecutionOptions? options = null)
    {
        _executionPlan = executionPlan ??
            throw new ArgumentNullException(nameof(executionPlan));
        _document = executionPlan.Document;
        _options = options ?? new ScenarioExecutionOptions();
        _allocationProfile = _options.AllocationProfile;
        _metrics = _options.CaptureExecutionMetrics
            ? new ScenarioExecutionMetrics()
            : null;
        ScenarioAllocationToken initializationToken = StartAllocation();
        try
        {
            _runtime = ScenarioInitializationService.Initialize(
                executionPlan.InitializationRequest,
                recordDiagnostics: _options.RecordDiagnostics,
                stageRecorder: _allocationProfile);
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.RuntimeInitialization,
                initializationToken);
        }
        _metrics?.ObserveTurn(_runtime.TurnState.TurnNumber);

        _interceptionResolver = _options.InterceptionResolver ??
            CreateDefaultInterceptionResolver();
        _terminalRandomSource = _options.TerminalRandomSource ??
            (_document.TerminalRolls.Count == 0
                ? new SeededMissileTerminalRandomSource(_document.RandomSeed)
                : new FixedMissileTerminalRandomSource(_document.TerminalRolls.ToArray()));
    }


    private IMissileInterceptionResolver CreateDefaultInterceptionResolver()
    {
        MissileInterceptionOutcome[] outcomes =
            _document.InterceptionOutcomes.Count == 0
                ? new[] { MissileInterceptionOutcome.Missed }
                : _document.InterceptionOutcomes
                    .Select(value =>
                        ScenarioDocumentMapper.ParseEnum<MissileInterceptionOutcome>(
                            value,
                            "interception outcome"))
                    .ToArray();
        return new QueuedMissileInterceptionResolver(outcomes);
    }

    public ScenarioRunResult Execute()
    {
        for (int actionIndex = 0; actionIndex < _document.Actions.Count; actionIndex++)
        {
            ActionDocument action = _document.Actions[actionIndex];
            ScenarioActionKind actionKind = _executionPlan.ActionKinds[actionIndex];
            ScenarioAllocationStage actionStage = actionKind switch
            {
                ScenarioActionKind.MoveShip => ScenarioAllocationStage.ShipMovement,
                ScenarioActionKind.AdvanceMissile => ScenarioAllocationStage.MissileAdvancement,
                ScenarioActionKind.AdvancePhase => ScenarioAllocationStage.PhaseAdvancement,
                _ => throw new InvalidOperationException(
                    $"Unsupported prepared action kind '{actionKind}'."),
            };
            ScenarioAllocationToken actionToken = StartAllocation();
            try
            {
                switch (actionKind)
                {
                    case ScenarioActionKind.MoveShip:
                        ExecuteMoveShip(action);
                        break;
                    case ScenarioActionKind.AdvanceMissile:
                        ExecuteAdvanceMissile(action);
                        break;
                    case ScenarioActionKind.AdvancePhase:
                        ExecuteAdvancePhase();
                        break;
                    default:
                        throw new InvalidOperationException(
                            $"Unsupported prepared action kind '{actionKind}'.");
                }
            }
            finally
            {
                StopAllocation(actionStage, actionToken);
            }

            _metrics?.ObserveTurn(_runtime.TurnState.TurnNumber);
            if (_document.StopWhenAllMissilesTerminal &&
                _runtime.MissileEngagement.Salvos.Count > 0 &&
                _runtime.MissileEngagement.Salvos.All(missile => missile.IsTerminal))
            {
                break;
            }
        }

        ScenarioAllocationToken finalizationToken = StartAllocation();
        try
        {
            IReadOnlyList<string> failures = _options.EvaluateAssertions
                ? ScenarioAssertionEvaluator.Evaluate(
                    _document,
                    _runtime,
                    _interceptionOpportunities)
                : Array.Empty<string>();
            if (_options.RecordCompletionEvent && _options.RecordDiagnostics)
            {
                _runtime.Journal.Record(
                        NextTimestamp(),
                        DiagnosticEventType.SessionEnded,
                        failures.Count == 0
                            ? "Headless scenario completed with all assertions satisfied."
                            : $"Headless scenario completed with {failures.Count} assertion failure(s).",
                        _runtime.TurnState.TurnNumber,
                        _runtime.TurnState.Phase,
                    data: Data(("passed", (failures.Count == 0).ToString())));
            }

            return new ScenarioRunResult(
                _document,
                _runtime,
                _interceptionOpportunities.AsReadOnly(),
                _interceptionAttempts.AsReadOnly(),
                _terminalOpportunities.AsReadOnly(),
                failures,
                _metrics);
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.ScenarioFinalization,
                finalizationToken);
        }
    }

    private void ExecuteMoveShip(ActionDocument action)
    {
        RequirePhase(TacticalTurnPhase.Movement, "moveShip");
        string shipId = Required(action.ShipId, "moveShip shipId");
        if (action.Destination is null)
        {
            throw new InvalidOperationException("moveShip requires a destination.");
        }

        if (!_runtime.Ships.TryGetValue(shipId, out ScenarioShipState? ship))
        {
            throw new InvalidOperationException($"Unknown ship '{shipId}'.");
        }

        HexCoord startingCoordinate = ship.Coordinate;
        HexCoord destination = ScenarioDocumentMapper.ToCoordinate(action.Destination);
        ShipMovementTurnState movementState;
        ShipMovementResult plan;
        ScenarioAllocationToken planningToken = StartAllocation();
        try
        {
            movementState = ShipMovementTurnService.Begin(
                startingCoordinate,
                ship.Definition.MovementProfile);
            plan = ShipMovementTurnService.PlanDestination(
                _runtime.Map,
                movementState,
                destination);
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.ShipMovementPlanning,
                planningToken);
        }

        if (_options.RecordDiagnostics)
        {
            _runtime.Journal.Record(
                NextTimestamp(),
                DiagnosticEventType.ShipMovementDestinationCommitted,
                $"{shipId} committed movement from {startingCoordinate} to {destination}.",
                _runtime.TurnState.TurnNumber,
                _runtime.TurnState.Phase,
                actorId: shipId,
                coordinateBefore: startingCoordinate,
                coordinateAfter: destination,
                data: Data(
                    ("status", plan.Status.ToString()),
                    ("plannedDistance", plan.Route?.Distance.ToString() ?? "none")));
        }

        if (!plan.CanMove || plan.Route is null)
        {
            if (_options.RecordDiagnostics)
            {
                _runtime.Journal.Record(
                    NextTimestamp(),
                    DiagnosticEventType.ShipMovementResolved,
                    $"{shipId} movement was rejected as {plan.Status}.",
                    _runtime.TurnState.TurnNumber,
                    _runtime.TurnState.Phase,
                    actorId: shipId,
                    coordinateBefore: startingCoordinate,
                    coordinateAfter: startingCoordinate,
                    data: Data(("status", plan.Status.ToString())));
            }
            throw new InvalidOperationException(
                $"Scripted movement for '{shipId}' was rejected as {plan.Status}.");
        }

        foreach (HexCoord entered in plan.Route.Path.Skip(1))
        {
            ScenarioAllocationToken stepToken = StartAllocation();
            try
            {
                ShipMovementStepExecutionResult step =
                    ShipMovementTurnService.ExecuteStep(
                        _runtime.Map,
                        shipId,
                        movementState,
                        entered);
                if (!step.WasCommitted)
                {
                    throw new InvalidOperationException(
                        $"Authoritative movement step for '{shipId}' failed as {step.Status}.");
                }

                movementState = step.State;
                ship.ApplyCommittedMovement(step.CoordinateAfter);
                if (_options.RecordDiagnostics)
                {
                    _runtime.Journal.Record(
                        NextTimestamp(),
                        DiagnosticEventType.ShipMovementStepResolved,
                        $"{shipId} entered {step.CoordinateAfter}; " +
                        $"{movementState.RemainingDistance} movement remains.",
                        _runtime.TurnState.TurnNumber,
                        _runtime.TurnState.Phase,
                        actorId: shipId,
                        coordinateBefore: step.CoordinateBefore,
                        coordinateAfter: step.CoordinateAfter,
                        data: Data(
                            ("distanceSpent", movementState.DistanceSpent.ToString()),
                            ("remainingMovement", movementState.RemainingDistance.ToString()),
                            ("status", step.Status.ToString())));
                }
            }
            finally
            {
                StopAllocation(
                    ScenarioAllocationStage.ShipMovementStepExecution,
                    stepToken);
            }

            ScenarioAllocationToken observationToken = StartAllocation();
            try
            {
                ObserveTargetMovement(shipId, ship);
            }
            finally
            {
                StopAllocation(
                    ScenarioAllocationStage.TargetMovementObservation,
                    observationToken);
            }

            ScenarioAllocationToken refreshToken = StartAllocation();
            try
            {
                RefreshTracks(TrackUpdateTrigger.ShipMovementStepCommitted);
            }
            finally
            {
                StopAllocation(
                    ScenarioAllocationStage.TrackRefreshAfterShipMovement,
                    refreshToken);
            }
        }

        movementState = ShipMovementTurnService.EndMovement(movementState);
        if (_options.RecordDiagnostics)
        {
            _runtime.Journal.Record(
                NextTimestamp(),
                DiagnosticEventType.ShipMovementResolved,
                $"{shipId} ended movement at {ship.Coordinate}.",
                _runtime.TurnState.TurnNumber,
                _runtime.TurnState.Phase,
                actorId: shipId,
                coordinateBefore: startingCoordinate,
                coordinateAfter: ship.Coordinate,
                data: Data(
                    ("distanceSpent", movementState.DistanceSpent.ToString()),
                    ("remainingMovement", movementState.RemainingDistance.ToString()),
                    ("status", movementState.DistanceSpent == 0 ? "Held" : "Moved")));
        }
    }

    private void ObserveTargetMovement(
        string shipId,
        ScenarioShipState ship)
    {
        foreach (GuidedMissileSalvo missile in _runtime.MissileEngagement.ActiveSalvos
                     .Where(missile => string.Equals(
                         missile.TargetId,
                         shipId,
                         StringComparison.Ordinal)))
        {
            ScenarioMissileDefinition definition = _runtime.MissileDefinitions[missile.Id];
            MissileAutonomousGuidanceService.ObserveAfterTargetMovement(
                _runtime.Map,
                missile,
                definition.SensorProfile,
                ship.Coordinate,
                ship.Definition.SignatureProfile,
                ship.Definition.SensorMode,
                ship.Definition.ElectronicWarfareProfile,
                ship.Definition.JammingEnabled,
                _runtime.Request.EnvironmentProfile,
                _runtime.TurnState.TurnNumber);

            if (ship.Coordinate == missile.CurrentCoordinate)
            {
                _pendingColocationSources[missile.Id] =
                    ScenarioTerminalOpportunitySource.TargetEnteredMissileHex;
            }
            else
            {
                _pendingColocationSources.Remove(missile.Id);
            }
        }
    }

    private void ExecuteAdvancePhase()
    {
        TacticalTurnPhase before = _runtime.TurnState.Phase;
        int turnBefore = _runtime.TurnState.TurnNumber;
        _runtime.TurnState.AdvancePhase();
        if (_runtime.TurnState.Phase == TacticalTurnPhase.MissileAndInterception)
        {
            _interceptionContext = null;
        }

        if (_options.RecordDiagnostics)
        {
            _runtime.Journal.Record(
                NextTimestamp(),
                DiagnosticEventType.PhaseAdvanced,
                $"Phase advanced from Turn {turnBefore} {before} to " +
                $"Turn {_runtime.TurnState.TurnNumber} {_runtime.TurnState.Phase}.",
                _runtime.TurnState.TurnNumber,
                _runtime.TurnState.Phase,
                data: Data(
                    ("previousTurn", turnBefore.ToString()),
                    ("previousPhase", before.ToString())));
        }
    }

    private void ExecuteAdvanceMissile(ActionDocument action)
    {
        RequirePhase(TacticalTurnPhase.MissileAndInterception, "advanceMissile");
        string missileId = Required(action.MissileId, "advanceMissile missileId");
        GuidedMissileSalvo salvo = _runtime.MissileEngagement.Find(missileId) ??
            throw new InvalidOperationException($"Unknown Missile Flight '{missileId}'.");
        ScenarioMissileDefinition definition = _runtime.MissileDefinitions[missileId];
        ScenarioShipState launcher = _runtime.Ships[salvo.LauncherId];
        ScenarioShipState target = _runtime.Ships[salvo.TargetId];

        ScenarioAllocationToken contextToken = StartAllocation();
        try
        {
            if (action.NewInterceptionPhase || _interceptionContext is null)
            {
                _interceptionContext = new MissileInterceptionPhaseContext(
                    _executionPlan.CreateDefenses(_runtime),
                    _interceptionResolver,
                    _runtime.Map,
                    new ScenarioMissileDefenseTrackProvider(_runtime));
            }
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.MissileInterceptionContext,
                contextToken);
        }

        MissileDatalinkUpdateResult datalink;
        ScenarioAllocationToken datalinkToken = StartAllocation();
        try
        {
            TacticalTrackRecord? launcherRecord = _runtime.Tracks.Get(
                salvo.LauncherId,
                salvo.TargetId);
            MissileTargetTrackSnapshot launcherTrack =
                MissileTargetTrackSnapshot.FromTacticalTrack(
                    salvo.TargetId,
                    launcherRecord);
            int sourceEpoch = launcherRecord?.LastObservedEpoch ??
                _runtime.ObservationEpoch;
            datalink = MissileDatalinkService.UpdateForGuidancePhase(
                _runtime.Map,
                salvo,
                definition.DatalinkProfile,
                launcher.Coordinate,
                launcherTrack,
                sourceEpoch);
            _metrics?.ObserveDatalink(datalink);
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.MissileDatalinkUpdate,
                datalinkToken);
        }

        if (_options.RecordDiagnostics)
        {
            _runtime.Journal.Record(
                NextTimestamp(),
                DiagnosticEventType.MissileDatalinkUpdated,
                $"{missileId} datalink resolved as {datalink.State}; " +
                $"guidance source {datalink.GuidanceSource}.",
                _runtime.TurnState.TurnNumber,
                TacticalTurnPhase.MissileAndInterception,
                actorId: missileId,
                targetId: salvo.TargetId,
                coordinateBefore: launcher.Coordinate,
                coordinateAfter: salvo.CurrentCoordinate,
                data: Data(
                    ("datalinkState", datalink.State.ToString()),
                    ("guidanceSource", datalink.GuidanceSource.ToString()),
                    ("reportDelivered", datalink.ReportDelivered.ToString()),
                    ("retainedReportAged", datalink.RetainedReportAged.ToString()),
                    ("retainedReportExpired", datalink.RetainedReportExpired.ToString()),
                    ("guidanceQuality", datalink.GuidanceSnapshot.Quality.ToString())));
        }

        MissileAutonomousGuidanceResult result;
        ScenarioAllocationToken guidanceToken = StartAllocation();
        try
        {
            result = MissileAutonomousGuidanceService.AdvanceOnePhase(
                _runtime.Map,
                salvo,
                datalink,
                definition.SensorProfile,
                target.Coordinate,
                target.Definition.SignatureProfile,
                target.Definition.SensorMode,
                target.Definition.ElectronicWarfareProfile,
                target.Definition.JammingEnabled,
                _runtime.Request.EnvironmentProfile,
                _runtime.TurnState.TurnNumber,
                _interceptionContext,
                _terminalRandomSource);
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.MissileGuidanceAdvance,
                guidanceToken);
        }

        ScenarioAllocationToken captureToken = StartAllocation();
        try
        {
            RecordMissileAction(salvo, target.Coordinate, result);
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.MissileOutcomeCapture,
                captureToken);
        }

        ScenarioAllocationToken refreshToken = StartAllocation();
        try
        {
            RefreshTracks(TrackUpdateTrigger.MissileMovementCompleted);
        }
        finally
        {
            StopAllocation(
                ScenarioAllocationStage.TrackRefreshAfterMissileMovement,
                refreshToken);
        }
    }

    private void RecordMissileAction(
        GuidedMissileSalvo salvo,
        HexCoord targetCoordinate,
        MissileAutonomousGuidanceResult result)
    {
        GuidedMissileAdvanceResult advance = result.AdvanceResult;
        _metrics?.ObserveGuidance(salvo, result.ReplanCount);
        if (!_options.RecordDiagnostics)
        {
            RecordCompactMissileAction(salvo, targetCoordinate, advance);
            return;
        }

        var attemptsByCoordinate = advance.InterceptionAttempts
            .GroupBy(attempt => attempt.MissileCoordinate)
            .ToDictionary(group => group.Key, group => group.ToArray());

        bool terminalOpportunityRecorded = false;
        foreach (HexCoord coordinate in advance.EnteredCoordinates)
        {
            if (_options.RecordDiagnostics)
            {
                _runtime.Journal.Record(
                    NextTimestamp(),
                    DiagnosticEventType.MissileMovementEdgeResolved,
                    $"{salvo.Id} entered {coordinate}.",
                    _runtime.TurnState.TurnNumber,
                    TacticalTurnPhase.MissileAndInterception,
                    actorId: salvo.Id,
                    targetId: salvo.TargetId,
                    coordinateAfter: coordinate);
            }

            if (attemptsByCoordinate.TryGetValue(coordinate, out MissileInterceptionAttemptResult[]? attempts))
            {
                RecordAttempts(attempts.Where(attempt =>
                    attempt.Opportunity == MissileInterceptionOpportunity.Transit));
                if (coordinate == targetCoordinate)
                {
                    terminalOpportunityRecorded = RecordTerminalOpportunityIfPresent(
                        salvo,
                        targetCoordinate,
                        advance);
                }
                RecordAttempts(attempts.Where(attempt =>
                    attempt.Opportunity == MissileInterceptionOpportunity.TerminalEntry));
            }
            else if (coordinate == targetCoordinate)
            {
                terminalOpportunityRecorded = RecordTerminalOpportunityIfPresent(
                    salvo,
                    targetCoordinate,
                    advance);
            }
        }

        var enteredCoordinateSet = advance.EnteredCoordinates.ToHashSet();
        if (!terminalOpportunityRecorded)
        {
            terminalOpportunityRecorded = RecordTerminalOpportunityIfPresent(
                salvo,
                targetCoordinate,
                advance);
        }
        RecordAttempts(advance.InterceptionAttempts.Where(attempt =>
            attempt.Opportunity == MissileInterceptionOpportunity.TerminalEntry &&
            !enteredCoordinateSet.Contains(attempt.MissileCoordinate)));
        RecordAttempts(advance.InterceptionAttempts.Where(attempt =>
            attempt.Opportunity == MissileInterceptionOpportunity.Stationary));

        MissileTerminalResolution? terminal = advance.TerminalResolution;
        if (advance.StationarySearchFuelSpentThisPhase > 0)
        {
            RecordSearchWaitDiagnostic(
                salvo,
                advance.StationarySearchFuelSpentThisPhase,
                "StationaryRetry",
                terminal?.TargetCoLocated == true,
                "The Missile Flight continued Search/Wait from its current coordinate.");
        }

        if (terminal is not null)
        {
            if (!terminal.TargetCoLocated &&
                salvo.Status == GuidedMissileStatus.Searching &&
                advance.StationarySearchFuelSpentThisPhase == 0)
            {
                RecordSearchWaitDiagnostic(
                    salvo,
                    0,
                    "CandidateCoordinateReached",
                    false,
                    terminal.Reason);
            }

            if (terminal.TargetCoLocated &&
                (terminal.Outcome != MissileTerminalOutcome.Intercepted ||
                 terminal.HasFirmSolution))
            {
                if (_metrics is not null)
                {
                    _metrics.AcquisitionAttempted = true;
                }
                if (_options.RecordDiagnostics)
                {
                    _runtime.Journal.Record(
                        NextTimestamp(),
                        DiagnosticEventType.MissileTerminalAcquisitionResolved,
                        terminal.HasFirmSolution
                            ? $"{salvo.Id} obtained a Firm terminal solution."
                            : $"{salvo.Id} failed terminal acquisition.",
                        _runtime.TurnState.TurnNumber,
                        TacticalTurnPhase.MissileAndInterception,
                        actorId: salvo.Id,
                        targetId: salvo.TargetId,
                        coordinateAfter: terminal.OpportunityCoordinate,
                        data: Data(
                            ("reportSource", terminal.ReportSource.ToString()),
                            ("reportQuality", terminal.ReportQuality.ToString()),
                            ("usedSeekerAcquisition", terminal.UsedSeekerAcquisition.ToString()),
                            ("acquisitionRoll", terminal.AcquisitionRoll?.ToString() ?? "none"),
                            ("acquisitionChance", terminal.AcquisitionChancePercent?.ToString() ?? "none"),
                            ("hasFirmSolution", terminal.HasFirmSolution.ToString()),
                            ("targetCoLocated", terminal.TargetCoLocated.ToString()),
                            ("reason", terminal.Reason)));
                }
            }

            RecordAttempts(advance.InterceptionAttempts.Where(attempt =>
                attempt.Opportunity == MissileInterceptionOpportunity.PreTerminalAttack));

            if (terminal.AttackWasResolved)
            {
                if (_options.RecordDiagnostics)
                {
                    _runtime.Journal.Record(
                        NextTimestamp(),
                        DiagnosticEventType.MissileTerminalAttackResolved,
                        $"{salvo.Id} terminal attack resolved as {terminal.Outcome}.",
                        _runtime.TurnState.TurnNumber,
                        TacticalTurnPhase.MissileAndInterception,
                        actorId: salvo.Id,
                        targetId: salvo.TargetId,
                        coordinateAfter: terminal.OpportunityCoordinate,
                        data: Data(
                            ("attackRoll", terminal.AttackRoll?.ToString() ?? "none"),
                            ("effectiveHitChance", terminal.EffectiveHitChancePercent?.ToString() ?? "none"),
                            ("critical", terminal.IsCriticalHit.ToString()),
                            ("reason", terminal.Reason)));
                }
            }
            else if (terminal.Outcome == MissileTerminalOutcome.SelfDestructed)
            {
                if (_options.RecordDiagnostics)
                {
                    _runtime.Journal.Record(
                        NextTimestamp(),
                        DiagnosticEventType.MissileSelfDestructed,
                        $"{salvo.Id} self-destructed after exhausting its search fuel.",
                        _runtime.TurnState.TurnNumber,
                        TacticalTurnPhase.MissileAndInterception,
                        actorId: salvo.Id,
                        targetId: salvo.TargetId,
                        coordinateAfter: terminal.OpportunityCoordinate);
                }
            }
        }

        if (_options.RecordDiagnostics)
        {
            _runtime.Journal.Record(
                NextTimestamp(),
                DiagnosticEventType.MissileGuidanceResolved,
                $"{salvo.Id} action ended as {salvo.Status}.",
                _runtime.TurnState.TurnNumber,
                TacticalTurnPhase.MissileAndInterception,
                actorId: salvo.Id,
                targetId: salvo.TargetId,
                coordinateBefore: advance.StartingCoordinate,
                coordinateAfter: advance.EndingCoordinate,
                data: Data(
                    ("distanceTraveledThisPhase", advance.DistanceTraveledThisPhase.ToString()),
                    ("stationarySearchFuelSpentThisPhase", advance.StationarySearchFuelSpentThisPhase.ToString()),
                    ("remainingRange", salvo.RemainingRange.ToString()),
                    ("replanCount", result.ReplanCount.ToString()),
                    ("guidanceSource", salvo.LastGuidanceSource.ToString()),
                    ("localSensorMode", salvo.LocalSensorTrack?.SensorMode.ToString() ?? "none"),
                    ("status", salvo.Status.ToString())));
        }
    }

    private void RecordCompactMissileAction(
        GuidedMissileSalvo salvo,
        HexCoord targetCoordinate,
        GuidedMissileAdvanceResult advance)
    {
        _ = RecordTerminalOpportunityIfPresent(
            salvo,
            targetCoordinate,
            advance);
        RecordAttempts(advance.InterceptionAttempts);

        MissileTerminalResolution? terminal = advance.TerminalResolution;
        if (advance.StationarySearchFuelSpentThisPhase > 0)
        {
            RecordSearchWaitDiagnostic(
                salvo,
                advance.StationarySearchFuelSpentThisPhase,
                "StationaryRetry",
                terminal?.TargetCoLocated == true,
                "The Missile Flight continued Search/Wait from its current coordinate.");
        }

        if (terminal is null)
        {
            return;
        }

        if (!terminal.TargetCoLocated &&
            salvo.Status == GuidedMissileStatus.Searching &&
            advance.StationarySearchFuelSpentThisPhase == 0)
        {
            RecordSearchWaitDiagnostic(
                salvo,
                0,
                "CandidateCoordinateReached",
                false,
                terminal.Reason);
        }

        if (terminal.TargetCoLocated &&
            (terminal.Outcome != MissileTerminalOutcome.Intercepted ||
             terminal.HasFirmSolution) &&
            _metrics is not null)
        {
            _metrics.AcquisitionAttempted = true;
        }
    }

    private void RecordSearchWaitDiagnostic(
        GuidedMissileSalvo salvo,
        int stationarySearchFuelSpentThisPhase,
        string searchTrigger,
        bool targetCoLocated,
        string reason)
    {
        if (_metrics is not null)
        {
            _metrics.SearchActivated = true;
        }
        if (_options.RecordDiagnostics)
        {
            _runtime.Journal.Record(
                NextTimestamp(),
                DiagnosticEventType.MissileSearchActivated,
                stationarySearchFuelSpentThisPhase > 0
                    ? $"{salvo.Id} spent {stationarySearchFuelSpentThisPhase} fuel on stationary Search/Wait."
                    : $"{salvo.Id} entered Search/Wait after reaching a guidance coordinate without the target.",
                _runtime.TurnState.TurnNumber,
                TacticalTurnPhase.MissileAndInterception,
                actorId: salvo.Id,
                targetId: salvo.TargetId,
                coordinateAfter: salvo.CurrentCoordinate,
                data: Data(
                    ("searchTrigger", searchTrigger),
                    ("targetCoLocated", targetCoLocated.ToString()),
                    ("stationarySearchFuelSpentThisPhase", stationarySearchFuelSpentThisPhase.ToString()),
                    ("remainingRange", salvo.RemainingRange.ToString()),
                    ("reason", reason)));
        }
    }

    private bool RecordTerminalOpportunityIfPresent(
        GuidedMissileSalvo salvo,
        HexCoord targetCoordinate,
        GuidedMissileAdvanceResult advance)
    {
        MissileTerminalResolution? terminal = advance.TerminalResolution;
        bool missileEnteredTargetHex = advance.EnteredCoordinates.Contains(targetCoordinate);
        bool actionBeganColocated = advance.StartingCoordinate == targetCoordinate;
        bool targetCoLocated =
            missileEnteredTargetHex ||
            actionBeganColocated ||
            terminal?.TargetCoLocated == true ||
            advance.InterceptionAttempts.Any(attempt =>
                attempt.Opportunity is
                    MissileInterceptionOpportunity.TerminalEntry or
                    MissileInterceptionOpportunity.PreTerminalAttack);
        if (!targetCoLocated)
        {
            _pendingColocationSources.Remove(salvo.Id);
            return false;
        }

        ScenarioTerminalOpportunitySource source;
        if (missileEnteredTargetHex)
        {
            source = ScenarioTerminalOpportunitySource.MissileEnteredTargetHex;
        }
        else if (advance.StationarySearchFuelSpentThisPhase > 0)
        {
            source = ScenarioTerminalOpportunitySource.StationarySearchRetry;
        }
        else if (_pendingColocationSources.TryGetValue(salvo.Id, out var pendingSource))
        {
            source = pendingSource;
        }
        else
        {
            source = ScenarioTerminalOpportunitySource.ActionBeganColocated;
        }

        _pendingColocationSources.Remove(salvo.Id);
        HexCoord coordinate = terminal?.OpportunityCoordinate ?? targetCoordinate;
        var opportunity = new ScenarioTerminalOpportunity(
            salvo.Id,
            salvo.TargetId,
            coordinate,
            source,
            _runtime.TurnState.TurnNumber);
        _terminalOpportunities.Add(opportunity);
        _metrics?.ObserveOpportunity(source);
        if (_options.RecordDiagnostics)
        {
            _runtime.Journal.Record(
                NextTimestamp(),
                DiagnosticEventType.MissileTerminalOpportunity,
                $"{salvo.Id} opened a terminal opportunity via {source}.",
                _runtime.TurnState.TurnNumber,
                TacticalTurnPhase.MissileAndInterception,
                actorId: salvo.Id,
                targetId: salvo.TargetId,
                coordinateAfter: coordinate,
                data: Data(("source", source.ToString())));
        }
        return true;
    }

    private void RecordAttempts(IEnumerable<MissileInterceptionAttemptResult> attempts)
    {
        foreach (MissileInterceptionAttemptResult attempt in attempts)
        {
            _interceptionOpportunities.Add(attempt.Opportunity);
            _interceptionAttempts.Add(attempt);
            if (_options.RecordDiagnostics)
            {
                _runtime.Journal.Record(
                    NextTimestamp(),
                    DiagnosticEventType.MissileInterceptionAttempted,
                    $"{attempt.DefenseSystemId} attempted {attempt.Opportunity} interception: {attempt.Outcome}.",
                    _runtime.TurnState.TurnNumber,
                    TacticalTurnPhase.MissileAndInterception,
                    actorId: attempt.DefenseSystemId,
                    targetId: attempt.SalvoId,
                    coordinateAfter: attempt.MissileCoordinate,
                    data: Data(
                        ("defenderShip", attempt.DefenderShipId),
                        ("opportunity", attempt.Opportunity.ToString()),
                        ("outcome", attempt.Outcome.ToString()),
                        ("attemptNumber", attempt.AttemptNumberForSystemThisPhase.ToString())));
            }
        }
    }

    private void RefreshTracks(TrackUpdateTrigger trigger)
    {
        if (_options.RecordDiagnostics)
        {
            RecordTrackRefresh(ScenarioInitializationService.RefreshAllTracks(
                _runtime,
                trigger,
                _runtime.TurnState.TurnNumber));
        }
        else
        {
            ScenarioInitializationService.RefreshAllTracksWithoutResults(
                _runtime,
                trigger,
                _runtime.TurnState.TurnNumber);
        }
    }

    private void RecordTrackRefresh(IReadOnlyList<TacticalTrackUpdateResult> updates)
    {
        foreach (TacticalTrackUpdateResult update in updates)
        {
            if (_options.RecordDiagnostics)
            {
                _runtime.Journal.Record(
                    NextTimestamp(),
                    DiagnosticEventType.TrackUpdated,
                    $"{update.ObserverId} track on {update.TargetId} became " +
                    $"{update.CurrentQuality?.ToString() ?? "Unknown"}.",
                    _runtime.TurnState.TurnNumber,
                    _runtime.TurnState.Phase,
                    actorId: update.ObserverId,
                    targetId: update.TargetId,
                    coordinateAfter: update.Record?.EstimatedCoordinate,
                    data: Data(("trigger", update.Trigger.ToString())));
            }
        }
    }

    private void RequirePhase(
        TacticalTurnPhase requiredPhase,
        string actionType)
    {
        if (_runtime.TurnState.Phase != requiredPhase)
        {
            throw new InvalidOperationException(
                $"Action '{actionType}' requires phase {requiredPhase}, but the " +
                $"scenario is at Turn {_runtime.TurnState.TurnNumber} " +
                $"{_runtime.TurnState.Phase}.");
        }
    }

    private DateTimeOffset NextTimestamp() =>
        DateTimeOffset.UnixEpoch.AddMilliseconds(_runtime.Journal.Events.Count);

    private static IEnumerable<KeyValuePair<string, string>> Data(
        params (string Key, string Value)[] items) =>
        items.Select(item => new KeyValuePair<string, string>(item.Key, item.Value));

    private ScenarioAllocationToken StartAllocation() =>
        _allocationProfile?.Start() ?? default;

    private void StopAllocation(
        ScenarioAllocationStage stage,
        ScenarioAllocationToken token) =>
        _allocationProfile?.Stop(stage, token);

    private static string Required(string? value, string description)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"A {description} is required.");
        }

        return value;
    }
}
