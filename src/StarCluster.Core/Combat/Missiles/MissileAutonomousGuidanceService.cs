using System;
using System.Collections.Generic;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Resolves one missile action with action-start datalink input, missile-local
/// sensing, deterministic arbitration, per-entered-hex replanning, two-window
/// terminal defense, seeker-assisted acquisition, and one bounded d100 attack.
/// Movement already spent before a new report is never refunded.
/// </summary>
public static class MissileAutonomousGuidanceService
{
    public static MissileAutonomousGuidanceResult AdvanceOnePhase(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileDatalinkUpdateResult datalinkUpdate,
        MissileSensorProfile sensorProfile,
        HexCoord targetCoordinate,
        SensorSignatureProfile targetSignature,
        SensorMode targetSensorMode,
        ElectronicWarfareProfile targetElectronicWarfare,
        bool targetJammingEnabled,
        SensorEnvironmentProfile environment,
        int observationEpoch,
        MissileInterceptionPhaseContext? interceptionContext = null,
        IMissileTerminalRandomSource? terminalRandomSource = null)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(datalinkUpdate);
        ArgumentNullException.ThrowIfNull(sensorProfile);
        ArgumentNullException.ThrowIfNull(targetSignature);
        ArgumentNullException.ThrowIfNull(targetElectronicWarfare);
        ArgumentNullException.ThrowIfNull(environment);

        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }

        if (!string.Equals(
                salvo.TargetId,
                datalinkUpdate.GuidanceSnapshot.TargetId,
                StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "The datalink update belongs to a different target.",
                nameof(datalinkUpdate));
        }

        IMissileTerminalRandomSource randomSource =
            terminalRandomSource ??
            new FixedMissileTerminalRandomSource(50);
        HexCoord startingCoordinate = salvo.CurrentCoordinate;
        int startingSearchFuel = salvo.StationarySearchFuelSpent;
        var enteredCoordinates = new List<HexCoord>();
        var interceptionAttempts = new List<MissileInterceptionAttemptResult>();
        var steps = new List<MissileAutonomousGuidanceStep>();

        if (salvo.IsTerminal)
        {
            MissileGuidanceDecision terminalDecision =
                MissileGuidanceArbitrator.Select(salvo.TargetId);
            return CreateResult(
                salvo,
                startingCoordinate,
                terminalDecision,
                terminalDecision,
                steps,
                enteredCoordinates,
                interceptionAttempts,
                salvo.LastRoutePlan,
                    startingSearchFuel);
        }

        MissileGuidanceReportCandidate? datalinkCandidate =
            MissileGuidanceReportCandidate.FromDatalink(datalinkUpdate);
        MissileLocalSensorObservationResult localObservation = ObserveLocal(
            map,
            salvo,
            sensorProfile,
            targetCoordinate,
            targetSignature,
            targetSensorMode,
            targetElectronicWarfare,
            targetJammingEnabled,
            environment,
            observationEpoch);
        MissileGuidanceDecision decision = MissileGuidanceArbitrator.Select(
            salvo.TargetId,
            datalinkCandidate,
            MissileGuidanceReportCandidate.FromLocalSensor(
                localObservation.TrackReport));
        MissileGuidanceDecision initialDecision = decision;
        salvo.BeginGuidancePhase(decision.SelectedSnapshot);
        salvo.SetGuidanceDecision(decision);
        MissileRouteResult? routePlan = PlanCurrentRoute(map, salvo, decision);
        MissileRouteResult? lastUsableRoutePlan = routePlan;
        salvo.SetRoutePlan(routePlan);
        steps.Add(new MissileAutonomousGuidanceStep(
            MissileGuidanceObservationOpportunity.ActionStart,
            salvo.CurrentCoordinate,
            localObservation,
            decision,
            guidanceChanged: false,
            movementSpentThisAction: 0,
            routePlan: routePlan));

        if (salvo.Status == GuidedMissileStatus.Searching)
        {
            HexCoord? selectedCoordinate =
                decision.SelectedSnapshot.GuidanceCoordinate;
            bool guidanceMoved =
                selectedCoordinate.HasValue &&
                selectedCoordinate.Value != salvo.CurrentCoordinate;
            if (guidanceMoved)
            {
                salvo.ClearTerminalOpportunity();
            }
            else
            {
                salvo.SetRoutePlan(null);
                salvo.SpendStationarySearchFuel();
                ResolveTerminalOrSearch(
                    salvo,
                    targetCoordinate,
                    decision,
                    datalinkUpdate.State,
                    sensorProfile.IsInstalled,
                    targetJammingEnabled
                        ? targetElectronicWarfare.JammingRangePenaltyHexes
                        : 0,
                    interceptionContext,
                    randomSource,
                    interceptionAttempts,
                    isNewArrival: false);
                return CreateResult(
                    salvo,
                    startingCoordinate,
                    initialDecision,
                    decision,
                    steps,
                    enteredCoordinates,
                    interceptionAttempts,
                    lastUsableRoutePlan,
                    startingSearchFuel);
            }
        }

        int availableSteps = Math.Min(
            salvo.Profile.SpeedHexesPerTurn,
            salvo.RemainingRange);
        int movementSpent = 0;

        while (!salvo.IsTerminal && movementSpent < availableSteps)
        {
            HexCoord? guidanceCoordinate =
                decision.SelectedSnapshot.GuidanceCoordinate;
            if (!guidanceCoordinate.HasValue)
            {
                salvo.SetRoutePlan(null);
                salvo.SetStatus(GuidedMissileStatus.WaitingForTrack);
                ResolveInterception(
                    salvo,
                    interceptionContext,
                    MissileInterceptionOpportunity.Stationary,
                    interceptionAttempts);
                break;
            }

            if (salvo.CurrentCoordinate == guidanceCoordinate.Value)
            {
                salvo.SetRoutePlan(null);
                ResolveTerminalOrSearch(
                    salvo,
                    targetCoordinate,
                    decision,
                    datalinkUpdate.State,
                    sensorProfile.IsInstalled,
                    targetJammingEnabled
                        ? targetElectronicWarfare.JammingRangePenaltyHexes
                        : 0,
                    interceptionContext,
                    randomSource,
                    interceptionAttempts,
                    isNewArrival: false);
                break;
            }

            if (salvo.RemainingRange == 0)
            {
                salvo.SetRoutePlan(null);
                salvo.SetStatus(GuidedMissileStatus.RangeExhausted);
                break;
            }

            routePlan = PlanCurrentRoute(map, salvo, decision);
            if (routePlan is not null)
            {
                lastUsableRoutePlan = routePlan;
            }
            salvo.SetRoutePlan(routePlan);
            if (routePlan is not { HasRoute: true } ||
                routePlan.Path.Count < 2)
            {
                salvo.SetStatus(GuidedMissileStatus.WaitingForRoute);
                ResolveInterception(
                    salvo,
                    interceptionContext,
                    MissileInterceptionOpportunity.Stationary,
                    interceptionAttempts);
                break;
            }

            HexCoord entered = routePlan.Path[1];
            salvo.MoveThrough(new[] { entered });
            enteredCoordinates.Add(entered);
            movementSpent++;

            MissileGuidanceDecision previousDecision = decision;
            localObservation = ObserveLocal(
                map,
                salvo,
                sensorProfile,
                targetCoordinate,
                targetSignature,
                targetSensorMode,
                targetElectronicWarfare,
                targetJammingEnabled,
                environment,
                observationEpoch);
            decision = MissileGuidanceArbitrator.Select(
                salvo.TargetId,
                datalinkCandidate,
                MissileGuidanceReportCandidate.FromLocalSensor(
                    localObservation.TrackReport));
            bool guidanceChanged = GuidanceChanged(
                previousDecision,
                decision);
            salvo.SetGuidanceDecision(decision);
            MissileRouteResult? replannedRoute =
                PlanCurrentRoute(map, salvo, decision);
            if (replannedRoute is not null)
            {
                lastUsableRoutePlan = replannedRoute;
            }
            salvo.SetRoutePlan(replannedRoute);
            steps.Add(new MissileAutonomousGuidanceStep(
                MissileGuidanceObservationOpportunity.AfterEnteredHex,
                salvo.CurrentCoordinate,
                localObservation,
                decision,
                guidanceChanged,
                movementSpentThisAction: movementSpent,
                routePlan: replannedRoute));

            if (salvo.CurrentCoordinate == targetCoordinate)
            {
                ResolveTerminalOrSearch(
                    salvo,
                    targetCoordinate,
                    decision,
                    datalinkUpdate.State,
                    sensorProfile.IsInstalled,
                    targetJammingEnabled
                        ? targetElectronicWarfare.JammingRangePenaltyHexes
                        : 0,
                    interceptionContext,
                    randomSource,
                    interceptionAttempts,
                    isNewArrival: true);
                break;
            }

            ResolveInterception(
                salvo,
                interceptionContext,
                MissileInterceptionOpportunity.Transit,
                interceptionAttempts);
            if (salvo.Status == GuidedMissileStatus.Intercepted)
            {
                break;
            }

            HexCoord? selectedCoordinate =
                decision.SelectedSnapshot.GuidanceCoordinate;
            if (selectedCoordinate.HasValue &&
                salvo.CurrentCoordinate == selectedCoordinate.Value)
            {
                EnterSearchAtCandidate(salvo, decision);
                break;
            }
        }

        if (!salvo.IsTerminal &&
            salvo.Status != GuidedMissileStatus.Searching)
        {
            HexCoord? finalGuidance =
                decision.SelectedSnapshot.GuidanceCoordinate;
            if (!finalGuidance.HasValue)
            {
                salvo.SetStatus(GuidedMissileStatus.WaitingForTrack);
            }
            else if (salvo.CurrentCoordinate == finalGuidance.Value)
            {
                ResolveTerminalOrSearch(
                    salvo,
                    targetCoordinate,
                    decision,
                    datalinkUpdate.State,
                    sensorProfile.IsInstalled,
                    targetJammingEnabled
                        ? targetElectronicWarfare.JammingRangePenaltyHexes
                        : 0,
                    interceptionContext,
                    randomSource,
                    interceptionAttempts,
                    isNewArrival: false);
            }
            else if (salvo.RemainingRange == 0)
            {
                salvo.SetStatus(GuidedMissileStatus.RangeExhausted);
            }
            else if (salvo.Status != GuidedMissileStatus.WaitingForRoute)
            {
                salvo.SetStatus(GuidedMissileStatus.InFlight);
            }
        }

        return CreateResult(
            salvo,
            startingCoordinate,
            initialDecision,
            decision,
            steps,
            enteredCoordinates,
            interceptionAttempts,
            lastUsableRoutePlan,
                    startingSearchFuel);
    }

    public static MissileLocalSensorObservationResult ObserveAfterTargetMovement(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileSensorProfile sensorProfile,
        HexCoord targetCoordinate,
        SensorSignatureProfile targetSignature,
        SensorMode targetSensorMode,
        ElectronicWarfareProfile targetElectronicWarfare,
        bool targetJammingEnabled,
        SensorEnvironmentProfile environment,
        int observationEpoch)
    {
        ArgumentNullException.ThrowIfNull(salvo);
        return ObserveLocal(
            map,
            salvo,
            sensorProfile,
            targetCoordinate,
            targetSignature,
            targetSensorMode,
            targetElectronicWarfare,
            targetJammingEnabled,
            environment,
            observationEpoch);
    }

    private static void ResolveTerminalOrSearch(
        GuidedMissileSalvo salvo,
        HexCoord targetCoordinate,
        MissileGuidanceDecision decision,
        MissileDatalinkState datalinkState,
        bool onboardNavigationSensorInstalled,
        int targetTerminalEcmStrength,
        MissileInterceptionPhaseContext? interceptionContext,
        IMissileTerminalRandomSource randomSource,
        ICollection<MissileInterceptionAttemptResult> interceptionAttempts,
        bool isNewArrival)
    {
        if (salvo.CurrentCoordinate != targetCoordinate)
        {
            EnterSearchAtCandidate(salvo, decision);
            return;
        }

        bool newOpportunity = salvo.BeginTerminalOpportunity(
            salvo.CurrentCoordinate);
        if (isNewArrival || newOpportunity ||
            !salvo.TerminalEntryDefenseResolved)
        {
            ResolveInterception(
                salvo,
                interceptionContext,
                MissileInterceptionOpportunity.TerminalEntry,
                interceptionAttempts);
            salvo.MarkTerminalEntryDefenseResolved();
        }

        if (salvo.IsTerminal)
        {
            return;
        }

        MissileTerminalResolution acquisition =
            MissileTerminalResolutionService.EvaluateAcquisition(
                salvo,
                targetCoordinate,
                decision.SelectedSource,
                decision.SelectedSnapshot,
                datalinkState,
                onboardNavigationSensorInstalled,
                targetTerminalEcmStrength,
                randomSource);
        salvo.RecordTerminalAcquisition(acquisition);
        if (!acquisition.HasFirmSolution)
        {
            salvo.EnterSearchWait(acquisition);
            return;
        }

        ResolveInterception(
            salvo,
            interceptionContext,
            MissileInterceptionOpportunity.PreTerminalAttack,
            interceptionAttempts);
        if (salvo.IsTerminal)
        {
            return;
        }

        MissileTerminalResolution attack =
            MissileTerminalResolutionService.ResolveAttack(
                salvo,
                acquisition,
                randomSource);
        salvo.RecordTerminalAttack(attack);
    }

    private static void EnterSearchAtCandidate(
        GuidedMissileSalvo salvo,
        MissileGuidanceDecision decision)
    {
        salvo.BeginTerminalOpportunity(salvo.CurrentCoordinate);
        var resolution = new MissileTerminalResolution(
            salvo.CurrentCoordinate,
            decision.SelectedSource,
            decision.SelectedSnapshot.Quality,
            targetCoLocated: false,
            usedSeekerAcquisition: false,
            acquisitionRoll: null,
            acquisitionChancePercent: null,
            hasFirmSolution: false,
            seekerAccuracyApplied: false,
            attackRoll: null,
            effectiveHitChancePercent: null,
            MissileTerminalOutcome.AcquisitionFailed,
            "The Missile Flight reached its selected report coordinate, but no Current/Firm co-located terminal solution existed.");
        salvo.EnterSearchWait(resolution);
    }

    private static void ResolveInterception(
        GuidedMissileSalvo salvo,
        MissileInterceptionPhaseContext? interceptionContext,
        MissileInterceptionOpportunity opportunity,
        ICollection<MissileInterceptionAttemptResult> results)
    {
        if (interceptionContext is null || salvo.IsTerminal)
        {
            return;
        }

        foreach (MissileInterceptionAttemptResult result in
                 interceptionContext.ResolveAt(
                     salvo,
                     salvo.CurrentCoordinate,
                     opportunity))
        {
            results.Add(result);
        }
    }

    private static MissileLocalSensorObservationResult ObserveLocal(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileSensorProfile sensorProfile,
        HexCoord targetCoordinate,
        SensorSignatureProfile targetSignature,
        SensorMode targetSensorMode,
        ElectronicWarfareProfile targetElectronicWarfare,
        bool targetJammingEnabled,
        SensorEnvironmentProfile environment,
        int observationEpoch)
    {
        MissileLocalSensorObservationResult observation =
            MissileLocalSensorService.Observe(
                map,
                salvo.Id,
                salvo.TargetId,
                salvo.CurrentCoordinate,
                targetCoordinate,
                sensorProfile,
                salvo.LocalSensorTrack,
                targetSignature,
                targetSensorMode,
                targetElectronicWarfare,
                targetJammingEnabled,
                environment,
                observationEpoch);
        salvo.SetLocalSensorTrack(observation.TrackReport);
        return observation;
    }

    private static MissileRouteResult? PlanCurrentRoute(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileGuidanceDecision decision)
    {
        HexCoord? coordinate = decision.SelectedSnapshot.GuidanceCoordinate;
        if (!coordinate.HasValue ||
            salvo.CurrentCoordinate == coordinate.Value ||
            salvo.RemainingRange == 0)
        {
            return null;
        }

        return MissileRoutePlanner.FindRoute(
            map,
            salvo.CurrentCoordinate,
            coordinate.Value,
            salvo.RemainingRange);
    }

    private static bool GuidanceChanged(
        MissileGuidanceDecision before,
        MissileGuidanceDecision after) =>
        before.SelectedSource != after.SelectedSource ||
        before.SelectedSnapshot.Quality != after.SelectedSnapshot.Quality ||
        !Nullable.Equals(
            before.SelectedSnapshot.GuidanceCoordinate,
            after.SelectedSnapshot.GuidanceCoordinate);

    private static MissileAutonomousGuidanceResult CreateResult(
        GuidedMissileSalvo salvo,
        HexCoord startingCoordinate,
        MissileGuidanceDecision initialDecision,
        MissileGuidanceDecision finalDecision,
        IEnumerable<MissileAutonomousGuidanceStep> steps,
        IEnumerable<HexCoord> enteredCoordinates,
        IEnumerable<MissileInterceptionAttemptResult> interceptionAttempts,
        MissileRouteResult? routePlan,
        int startingSearchFuel)
    {
        HexCoord? guidanceCoordinate =
            finalDecision.SelectedSnapshot.GuidanceCoordinate;
        var advance = new GuidedMissileAdvanceResult(
            salvo.Status,
            startingCoordinate,
            salvo.CurrentCoordinate,
            guidanceCoordinate,
            routePlan,
            enteredCoordinates,
            interceptionAttempts,
            stationarySearchFuelSpentThisPhase: Math.Max(
                0,
                salvo.StationarySearchFuelSpent - startingSearchFuel),
            terminalResolution: salvo.LastTerminalResolution);
        return new MissileAutonomousGuidanceResult(
            advance,
            initialDecision,
            finalDecision,
            steps);
    }
}
