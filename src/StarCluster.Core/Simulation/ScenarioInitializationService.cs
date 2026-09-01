using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Simulation;

/// <summary>
/// Builds the same authoritative tactical state a host would create before the
/// board is shown. The normal sensor evaluator and track-update service run
/// before scripted actions. Pre-existing Missile Flights are then represented
/// by the normal lifetime objects and included in that initial observation pass.
/// </summary>
public static class ScenarioInitializationService
{
    // Frozen diagnostic schema label retained for deterministic scenario-output compatibility.
    private const string DiagnosticContractVersion = "checkpoint-19";

    public static ScenarioInitializationResult Initialize(
        ScenarioInitializationRequest request,
        bool recordDiagnostics = true,
        IScenarioInitializationStageRecorder? stageRecorder = null)
    {
        ArgumentNullException.ThrowIfNull(request);

        SystemMap map;
        ScenarioInitializationStageToken stageToken =
            StartStage(stageRecorder);
        try
        {
            map = SystemMap.Create(
                request.MapRadius,
                MapObject.CreateStar(request.StarId, request.StarName));
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.MapCreation,
                stageToken);
        }

        stageToken = StartStage(stageRecorder);
        try
        {
            foreach (ScenarioMapObjectDefinition item in request.MapObjects)
            {
                MapObject mapObject = item.Kind switch
                {
                    ScenarioMapObjectKind.Planet =>
                        MapObject.CreatePlanet(item.Id, item.Name),
                    ScenarioMapObjectKind.Station =>
                        MapObject.CreateStation(item.Id, item.Name),
                    _ => throw new InvalidOperationException(
                        $"Unsupported scenario map-object kind {item.Kind}."),
                };
                map.Place(mapObject, item.Coordinate);
            }
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.StaticObjectPlacement,
                stageToken);
        }

        Dictionary<string, ScenarioShipState> shipStates;
        stageToken = StartStage(stageRecorder);
        try
        {
            shipStates = new Dictionary<string, ScenarioShipState>(
                StringComparer.Ordinal);
            foreach (ScenarioShipDefinition ship in request.Ships)
            {
                map.Place(
                    MapObject.CreateShip(ship.Id, ship.Name),
                    ship.Coordinate);
                shipStates.Add(ship.Id, new ScenarioShipState(ship));
            }
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.ShipStateCreation,
                stageToken);
        }

        TacticalTrackRepository tracks;
        stageToken = StartStage(stageRecorder);
        try
        {
            tracks = new TacticalTrackRepository();
            foreach (ScenarioPriorTrackDefinition prior in request.PriorTracks)
            {
                tracks.SeedPriorIntelligence(
                    prior.ObserverId,
                    prior.TargetId,
                    prior.LastKnownCoordinate,
                    request.InitialSequence,
                    prior.UncertaintyRadiusHexes);
            }
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.PriorTrackSeeding,
                stageToken);
        }

        MissileEngagementState engagement;
        Dictionary<string, ScenarioMissileDefinition> missileDefinitions;
        stageToken = StartStage(stageRecorder);
        try
        {
            engagement = new MissileEngagementState();
            missileDefinitions = new Dictionary<string, ScenarioMissileDefinition>(
                StringComparer.Ordinal);
            foreach (ScenarioMissileDefinition definition in request.Missiles)
            {
                ValidateMissileReferences(definition, shipStates);
                GuidedMissileSalvo salvo = CreateSeededMissile(definition);
                engagement.Add(salvo);
                missileDefinitions.Add(definition.Id, definition);
            }
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.MissileStateCreation,
                stageToken);
        }

        TacticalTurnState turnState;
        DiagnosticEventJournal journal;
        long sequence = request.InitialSequence;
        stageToken = StartStage(stageRecorder);
        try
        {
            turnState = CreateTurnState(
                request.InitialTurnNumber,
                request.InitialPhase);
            journal = new DiagnosticEventJournal(
                DiagnosticContractVersion,
                request.ScenarioId);

            if (recordDiagnostics)
            {
                journal.Record(
                    NextTimestamp(journal),
                    DiagnosticEventType.SessionStarted,
                    $"Headless scenario '{request.Name}' started.",
                    turnState.TurnNumber,
                    turnState.Phase,
                    data: Data(
                        ("scenarioId", request.ScenarioId),
                        ("randomSeed", request.RandomSeed.ToString()),
                        ("preExistingMissiles", engagement.Salvos.Count.ToString())));
            }
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.TurnAndJournalCreation,
                stageToken);
        }

        IReadOnlyList<TacticalTrackUpdateResult> initialUpdates;
        stageToken = StartStage(stageRecorder);
        try
        {
            initialUpdates = RefreshAllTracks(
                request,
                map,
                shipStates,
                tracks,
                engagement,
                ref sequence,
                request.ObservationEpoch,
                TrackUpdateTrigger.SystemEntry,
                captureResults: recordDiagnostics);
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.InitialTrackRefresh,
                stageToken);
        }

        stageToken = StartStage(stageRecorder);
        try
        {
            if (recordDiagnostics)
            {
                journal.Record(
                    NextTimestamp(journal),
                    DiagnosticEventType.ScenarioInitialized,
                    $"Scenario '{request.Name}' completed authoritative pre-simulation initialization.",
                    turnState.TurnNumber,
                    turnState.Phase,
                    data: Data(
                        ("shipCount", shipStates.Count.ToString()),
                        ("missileCount", engagement.Salvos.Count.ToString()),
                        ("trackUpdates", initialUpdates.Count.ToString()),
                        ("sequence", sequence.ToString()),
                        ("observationEpoch", request.ObservationEpoch.ToString())));

                foreach (TacticalTrackUpdateResult update in initialUpdates)
                {
                    journal.Record(
                        NextTimestamp(journal),
                        DiagnosticEventType.TrackUpdated,
                        $"{update.ObserverId} initialized track on {update.TargetId}: " +
                        $"{update.PreviousQuality?.ToString() ?? "Unknown"} -> " +
                        $"{update.CurrentQuality?.ToString() ?? "Unknown"}.",
                        turnState.TurnNumber,
                        turnState.Phase,
                        actorId: update.ObserverId,
                        targetId: update.TargetId,
                        coordinateAfter: update.Record?.EstimatedCoordinate,
                        data: Data(
                            ("trigger", update.Trigger.ToString()),
                            ("ageAdvanced", update.AgeAdvanced.ToString()),
                            ("uncertaintyRadius", update.Record?.UncertaintyRadiusHexes.ToString() ?? "none")));
                }
            }
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.InitializationDiagnostics,
                stageToken);
        }

        stageToken = StartStage(stageRecorder);
        try
        {
            return new ScenarioInitializationResult(
                request,
                map,
                shipStates,
                tracks,
                engagement,
                missileDefinitions,
                turnState,
                journal,
                sequence,
                request.ObservationEpoch);
        }
        finally
        {
            StopStage(
                stageRecorder,
                ScenarioInitializationStage.ResultConstruction,
                stageToken);
        }
    }

    private static ScenarioInitializationStageToken StartStage(
        IScenarioInitializationStageRecorder? recorder) =>
        recorder?.StartInitializationStage() ?? default;

    private static void StopStage(
        IScenarioInitializationStageRecorder? recorder,
        ScenarioInitializationStage stage,
        ScenarioInitializationStageToken token) =>
        recorder?.StopInitializationStage(stage, token);

    public static IReadOnlyList<TacticalTrackUpdateResult> RefreshAllTracks(
        ScenarioInitializationResult runtime,
        TrackUpdateTrigger trigger,
        int? observationEpoch = null)
    {
        ArgumentNullException.ThrowIfNull(runtime);
        int epoch = observationEpoch ?? runtime.ObservationEpoch;
        long sequence = runtime.Sequence;
        IReadOnlyList<TacticalTrackUpdateResult> results = RefreshAllTracks(
            runtime.Request,
            runtime.Map,
            runtime.Ships,
            runtime.Tracks,
            runtime.MissileEngagement,
            ref sequence,
            epoch,
            trigger,
            captureResults: true);
        runtime.Sequence = sequence;
        runtime.ObservationEpoch = epoch;
        return results;
    }

    public static void RefreshAllTracksWithoutResults(
        ScenarioInitializationResult runtime,
        TrackUpdateTrigger trigger,
        int? observationEpoch = null)
    {
        ArgumentNullException.ThrowIfNull(runtime);
        int epoch = observationEpoch ?? runtime.ObservationEpoch;
        long sequence = runtime.Sequence;
        _ = RefreshAllTracks(
            runtime.Request,
            runtime.Map,
            runtime.Ships,
            runtime.Tracks,
            runtime.MissileEngagement,
            ref sequence,
            epoch,
            trigger,
            captureResults: false);
        runtime.Sequence = sequence;
        runtime.ObservationEpoch = epoch;
    }

    private static IReadOnlyList<TacticalTrackUpdateResult> RefreshAllTracks(
        ScenarioInitializationRequest request,
        SystemMap map,
        IReadOnlyDictionary<string, ScenarioShipState> ships,
        TacticalTrackRepository tracks,
        MissileEngagementState engagement,
        ref long sequence,
        int observationEpoch,
        TrackUpdateTrigger trigger,
        bool captureResults)
    {
        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }

        sequence++;
        List<TacticalTrackUpdateResult>? allResults = captureResults
            ? new List<TacticalTrackUpdateResult>()
            : null;

        foreach (ScenarioShipState observer in ships.Values
                     .OrderBy(state => state.Definition.Id, StringComparer.Ordinal))
        {
            if (captureResults)
            {
                var observations = new List<TacticalTrackObservation>();
                AddShipObservations(
                    request,
                    map,
                    ships,
                    observer,
                    observations);
                AddMissileObservations(
                    request,
                    map,
                    engagement,
                    observer,
                    observations);
                allResults!.AddRange(SystemEntryTrackInitializer.Initialize(
                    tracks,
                    observer.Definition.Id,
                    observations,
                    observer.Definition.ComputingProfile,
                    sequence,
                    observationEpoch,
                    trigger));
            }
            else
            {
                ApplyShipObservationsWithoutResults(
                    request,
                    map,
                    ships,
                    tracks,
                    observer,
                    sequence,
                    observationEpoch,
                    trigger);
                ApplyMissileObservationsWithoutResults(
                    request,
                    map,
                    engagement,
                    tracks,
                    observer,
                    sequence,
                    observationEpoch,
                    trigger);
            }
        }

        return captureResults
            ? Array.AsReadOnly(allResults!.ToArray())
            : Array.Empty<TacticalTrackUpdateResult>();
    }

    private static void AddShipObservations(
        ScenarioInitializationRequest request,
        SystemMap map,
        IReadOnlyDictionary<string, ScenarioShipState> ships,
        ScenarioShipState observer,
        ICollection<TacticalTrackObservation> observations)
    {
        foreach (ScenarioShipState target in ships.Values
                     .Where(target => !string.Equals(
                         target.Definition.Id,
                         observer.Definition.Id,
                         StringComparison.Ordinal))
                     .OrderBy(target => target.Definition.Id, StringComparer.Ordinal))
        {
            observations.Add(EvaluateShipObservation(
                request,
                map,
                observer,
                target));
        }
    }

    private static void AddMissileObservations(
        ScenarioInitializationRequest request,
        SystemMap map,
        MissileEngagementState engagement,
        ScenarioShipState observer,
        ICollection<TacticalTrackObservation> observations)
    {
        foreach (GuidedMissileSalvo missile in engagement.Salvos
                     .OrderBy(salvo => salvo.Id, StringComparer.Ordinal))
        {
            observations.Add(EvaluateMissileObservation(
                request,
                map,
                observer,
                missile));
        }
    }

    private static void ApplyShipObservationsWithoutResults(
        ScenarioInitializationRequest request,
        SystemMap map,
        IReadOnlyDictionary<string, ScenarioShipState> ships,
        TacticalTrackRepository tracks,
        ScenarioShipState observer,
        long sequence,
        int observationEpoch,
        TrackUpdateTrigger trigger)
    {
        foreach (ScenarioShipState target in ships.Values
                     .Where(target => !string.Equals(
                         target.Definition.Id,
                         observer.Definition.Id,
                         StringComparison.Ordinal))
                     .OrderBy(target => target.Definition.Id, StringComparer.Ordinal))
        {
            TacticalTrackUpdateService.ApplyWithoutResult(
                tracks,
                observer.Definition.Id,
                EvaluateShipObservation(request, map, observer, target),
                observer.Definition.ComputingProfile,
                sequence,
                trigger,
                observationEpoch);
        }
    }

    private static void ApplyMissileObservationsWithoutResults(
        ScenarioInitializationRequest request,
        SystemMap map,
        MissileEngagementState engagement,
        TacticalTrackRepository tracks,
        ScenarioShipState observer,
        long sequence,
        int observationEpoch,
        TrackUpdateTrigger trigger)
    {
        foreach (GuidedMissileSalvo missile in engagement.Salvos
                     .OrderBy(salvo => salvo.Id, StringComparer.Ordinal))
        {
            TacticalTrackUpdateService.ApplyWithoutResult(
                tracks,
                observer.Definition.Id,
                EvaluateMissileObservation(request, map, observer, missile),
                observer.Definition.ComputingProfile,
                sequence,
                trigger,
                observationEpoch);
        }
    }

    private static TacticalTrackObservation EvaluateShipObservation(
        ScenarioInitializationRequest request,
        SystemMap map,
        ScenarioShipState observer,
        ScenarioShipState target)
    {
        SensorContactEvaluationContext context = new(
            observer.Definition.SensorMode,
            target.Definition.SignatureProfile,
            target.Definition.SensorMode,
            observer.Definition.ElectronicWarfareProfile,
            target.Definition.ElectronicWarfareProfile,
            target.Definition.JammingEnabled,
            request.EnvironmentProfile);
        return SensorContactEvaluator.Evaluate(
            map,
            target.Definition.Id,
            observer.Coordinate,
            target.Coordinate,
            observer.Definition.SensorProfile,
            context).Observation;
    }

    private static TacticalTrackObservation EvaluateMissileObservation(
        ScenarioInitializationRequest request,
        SystemMap map,
        ScenarioShipState observer,
        GuidedMissileSalvo missile)
    {
        ScenarioMissileDefinition missileDefinition = FindMissileDefinition(
            request,
            missile.Id);
        if (missile.OwnerSide == observer.Definition.Side)
        {
            return TacticalTrackObservation.Firm(
                missile.Id,
                missile.CurrentCoordinate,
                TacticalTrackSourceType.MissileSeeker);
        }

        SensorContactEvaluationContext context = new(
            observer.Definition.SensorMode,
            missileDefinition.SignatureProfile,
            SensorMode.Passive,
            observer.Definition.ElectronicWarfareProfile,
            ElectronicWarfareProfile.None,
            targetJammingEnabled: false,
            environment: request.EnvironmentProfile);
        return SensorContactEvaluator.Evaluate(
            map,
            missile.Id,
            observer.Coordinate,
            missile.CurrentCoordinate,
            observer.Definition.SensorProfile,
            context).Observation;
    }

    private static ScenarioMissileDefinition FindMissileDefinition(
        ScenarioInitializationRequest request,
        string missileId)
    {
        foreach (ScenarioMissileDefinition definition in request.Missiles)
        {
            if (string.Equals(definition.Id, missileId, StringComparison.Ordinal))
            {
                return definition;
            }
        }

        throw new InvalidOperationException(
            $"Scenario missile definition '{missileId}' was not found.");
    }

    private static GuidedMissileSalvo CreateSeededMissile(
        ScenarioMissileDefinition definition)
    {
        var salvo = new GuidedMissileSalvo(
            definition.Id,
            definition.OwnerSide,
            definition.LauncherId,
            definition.TargetId,
            definition.LaunchCoordinate,
            definition.FlightProfile,
            definition.TerminalProfile);

        if (definition.EnteredCoordinates.Count > 0)
        {
            salvo.MoveThrough(definition.EnteredCoordinates);
        }

        int restoredGuidancePhaseCount = definition.GuidancePhaseCount;
        if (definition.RetainedDatalink is not null)
        {
            restoredGuidancePhaseCount = Math.Max(
                restoredGuidancePhaseCount,
                definition.RetainedDatalink.ReceivedGuidancePhase);
        }
        salvo.RestoreGuidancePhaseCount(restoredGuidancePhaseCount);

        if (definition.RetainedDatalink is not null)
        {
            ScenarioRetainedDatalinkDefinition seed = definition.RetainedDatalink;
            var report = new MissileDatalinkReport(
                definition.TargetId,
                seed.ReceivedQuality,
                seed.GuidanceCoordinate,
                seed.SourceObservationEpoch,
                seed.ReceivedGuidancePhase,
                seed.UncertaintyRadiusHexes,
                seed.AgePhases);
            salvo.ApplyDatalinkEvaluation(
                seed.ReceivedGuidancePhase,
                seed.LinkState,
                report);
        }

        if (definition.LocalTrack is not null)
        {
            ScenarioLocalTrackDefinition seed = definition.LocalTrack;
            salvo.SetLocalSensorTrack(new MissileLocalTrackReport(
                definition.TargetId,
                seed.Quality,
                seed.GuidanceCoordinate,
                seed.SourceObservationEpoch,
                seed.UncertaintyRadiusHexes,
                seed.SensorMode,
                seed.AgeEpochs,
                seed.LastAgedObservationEpoch));
        }

        if (definition.InitialStatus == GuidedMissileStatus.Searching)
        {
            salvo.BeginTerminalOpportunity(salvo.CurrentCoordinate);
            salvo.EnterSearchWait(new MissileTerminalResolution(
                salvo.CurrentCoordinate,
                MissileGuidanceReportSource.None,
                MissileTargetTrackQuality.Stale,
                targetCoLocated: false,
                usedSeekerAcquisition: false,
                acquisitionRoll: null,
                acquisitionChancePercent: null,
                hasFirmSolution: false,
                seekerAccuracyApplied: false,
                attackRoll: null,
                effectiveHitChancePercent: null,
                MissileTerminalOutcome.AcquisitionFailed,
                "The scenario began with this Missile Flight in Search/Wait."));
        }
        else if (definition.InitialStatus != GuidedMissileStatus.InFlight)
        {
            salvo.SetStatus(definition.InitialStatus);
        }

        return salvo;
    }

    private static void ValidateMissileReferences(
        ScenarioMissileDefinition missile,
        IReadOnlyDictionary<string, ScenarioShipState> ships)
    {
        if (!ships.ContainsKey(missile.LauncherId))
        {
            throw new ArgumentException(
                $"Missile '{missile.Id}' references unknown launcher '{missile.LauncherId}'.");
        }

        if (!ships.ContainsKey(missile.TargetId))
        {
            throw new ArgumentException(
                $"Missile '{missile.Id}' references unknown target '{missile.TargetId}'.");
        }
    }

    private static TacticalTurnState CreateTurnState(
        int turnNumber,
        TacticalTurnPhase phase)
    {
        var state = new TacticalTurnState();
        int safety = 0;
        while ((state.TurnNumber != turnNumber || state.Phase != phase) &&
               safety++ < turnNumber * 8 + 8)
        {
            state.AdvancePhase();
        }

        if (state.TurnNumber != turnNumber || state.Phase != phase)
        {
            throw new InvalidOperationException(
                $"Could not initialize tactical cursor to Turn {turnNumber} {phase}.");
        }

        return state;
    }

    private static DateTimeOffset NextTimestamp(DiagnosticEventJournal journal) =>
        DateTimeOffset.UnixEpoch.AddMilliseconds(journal.Events.Count);

    private static IEnumerable<KeyValuePair<string, string>> Data(
        params (string Key, string Value)[] items) =>
        items.Select(item => new KeyValuePair<string, string>(item.Key, item.Value));
}
