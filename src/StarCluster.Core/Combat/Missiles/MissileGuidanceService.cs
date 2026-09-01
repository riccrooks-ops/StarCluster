using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Compatibility guidance path for one supplied launcher track. Reaching the
/// target hex creates a terminal opportunity rather than an automatic impact.
/// Standard PDS resolves once at terminal entry and, if a Firm solution is
/// produced, once immediately before the terminal attack roll.
/// </summary>
public static class MissileGuidanceService
{
    public static GuidedMissileAdvanceResult AdvanceOnePhase(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileTargetTrackSnapshot targetTrack) =>
        AdvanceOnePhase(
            map,
            salvo,
            targetTrack,
            interceptionContext: null,
            terminalRandomSource: null);

    public static GuidedMissileAdvanceResult AdvanceOnePhase(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileTargetTrackSnapshot targetTrack,
        MissileInterceptionPhaseContext? interceptionContext) =>
        AdvanceOnePhase(
            map,
            salvo,
            targetTrack,
            interceptionContext,
            terminalRandomSource: null);

    public static GuidedMissileAdvanceResult AdvanceOnePhase(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileTargetTrackSnapshot targetTrack,
        MissileInterceptionPhaseContext? interceptionContext,
        IMissileTerminalRandomSource? terminalRandomSource)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(targetTrack);

        if (!string.Equals(
                salvo.TargetId,
                targetTrack.TargetId,
                StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "The supplied target track does not belong to this Missile Flight.",
                nameof(targetTrack));
        }

        IMissileTerminalRandomSource randomSource =
            terminalRandomSource ??
            new FixedMissileTerminalRandomSource(50);
        HexCoord startingCoordinate = salvo.CurrentCoordinate;
        int startingSearchFuel = salvo.StationarySearchFuelSpent;
        var enteredCoordinates = new List<HexCoord>();
        var interceptionAttempts = new List<MissileInterceptionAttemptResult>();

        if (salvo.IsTerminal)
        {
            return CreateResult(
                salvo,
                startingCoordinate,
                guidanceCoordinate: null,
                routePlan: salvo.LastRoutePlan,
                enteredCoordinates,
                interceptionAttempts,
                    startingSearchFuel);
        }

        salvo.BeginGuidancePhase(targetTrack);
        salvo.SetGuidanceDecision(CreateCompatibilityDecision(targetTrack));
        HexCoord? guidanceCoordinate = targetTrack.GuidanceCoordinate;

        if (salvo.Status == GuidedMissileStatus.Searching)
        {
            bool guidanceMoved =
                guidanceCoordinate.HasValue &&
                guidanceCoordinate.Value != salvo.CurrentCoordinate;
            if (guidanceMoved)
            {
                salvo.ClearTerminalOpportunity();
            }
            else
            {
                ResolveStationarySearchActivation(
                    salvo,
                    targetTrack,
                    interceptionContext,
                    randomSource,
                    interceptionAttempts);
                return CreateResult(
                    salvo,
                    startingCoordinate,
                    guidanceCoordinate,
                    routePlan: null,
                    enteredCoordinates,
                    interceptionAttempts,
                    startingSearchFuel);
            }
        }

        if (!guidanceCoordinate.HasValue)
        {
            salvo.SetRoutePlan(null);
            salvo.SetStatus(GuidedMissileStatus.WaitingForTrack);
            ResolveInterception(
                salvo,
                interceptionContext,
                MissileInterceptionOpportunity.Stationary,
                interceptionAttempts);
            return CreateResult(
                salvo,
                startingCoordinate,
                guidanceCoordinate,
                routePlan: null,
                enteredCoordinates,
                interceptionAttempts,
                    startingSearchFuel);
        }

        bool currentTrack =
            targetTrack.Quality == MissileTargetTrackQuality.Current;
        if (salvo.CurrentCoordinate == guidanceCoordinate.Value)
        {
            salvo.SetRoutePlan(null);
            if (currentTrack)
            {
                ResolveTerminalOpportunity(
                    salvo,
                    guidanceCoordinate.Value,
                    targetTrack,
                    interceptionContext,
                    randomSource,
                    interceptionAttempts);
            }
            else
            {
                EnterSearchAtCandidate(salvo, targetTrack);
            }

            return CreateResult(
                salvo,
                startingCoordinate,
                guidanceCoordinate,
                routePlan: null,
                enteredCoordinates,
                interceptionAttempts,
                    startingSearchFuel);
        }

        if (salvo.RemainingRange == 0)
        {
            salvo.SetRoutePlan(null);
            salvo.SetStatus(GuidedMissileStatus.RangeExhausted);
            return CreateResult(
                salvo,
                startingCoordinate,
                guidanceCoordinate,
                routePlan: null,
                enteredCoordinates,
                interceptionAttempts,
                    startingSearchFuel);
        }

        MissileRouteResult routePlan = MissileRoutePlanner.FindRoute(
            map,
            salvo.CurrentCoordinate,
            guidanceCoordinate.Value,
            salvo.RemainingRange);
        salvo.SetRoutePlan(routePlan);

        if (!routePlan.HasRoute)
        {
            salvo.SetStatus(GuidedMissileStatus.WaitingForRoute);
            ResolveInterception(
                salvo,
                interceptionContext,
                MissileInterceptionOpportunity.Stationary,
                interceptionAttempts);
            return CreateResult(
                salvo,
                startingCoordinate,
                guidanceCoordinate,
                routePlan,
                enteredCoordinates,
                interceptionAttempts,
                    startingSearchFuel);
        }

        int availableSteps = Math.Min(
            salvo.Profile.SpeedHexesPerTurn,
            salvo.RemainingRange);

        foreach (HexCoord coordinate in routePlan.Path
                     .Skip(1)
                     .Take(availableSteps))
        {
            salvo.MoveThrough(new[] { coordinate });
            enteredCoordinates.Add(coordinate);

            bool reachedGuidance = coordinate == guidanceCoordinate.Value;
            if (reachedGuidance && currentTrack)
            {
                ResolveTerminalOpportunity(
                    salvo,
                    guidanceCoordinate.Value,
                    targetTrack,
                    interceptionContext,
                    randomSource,
                    interceptionAttempts);
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

            if (reachedGuidance)
            {
                EnterSearchAtCandidate(salvo, targetTrack);
                break;
            }
        }

        if (!salvo.IsTerminal &&
            salvo.Status != GuidedMissileStatus.Searching)
        {
            if (salvo.RemainingRange == 0)
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
            guidanceCoordinate,
            routePlan,
            enteredCoordinates,
            interceptionAttempts,
                    startingSearchFuel);
    }

    private static void ResolveStationarySearchActivation(
        GuidedMissileSalvo salvo,
        MissileTargetTrackSnapshot targetTrack,
        MissileInterceptionPhaseContext? interceptionContext,
        IMissileTerminalRandomSource randomSource,
        ICollection<MissileInterceptionAttemptResult> interceptionAttempts)
    {
        salvo.SpendStationarySearchFuel();
        if (targetTrack.Quality == MissileTargetTrackQuality.Current &&
            targetTrack.CurrentCoordinate == salvo.CurrentCoordinate)
        {
            ResolveTerminalOpportunity(
                salvo,
                salvo.CurrentCoordinate,
                targetTrack,
                interceptionContext,
                randomSource,
                interceptionAttempts);
            return;
        }

        EnterSearchAtCandidate(salvo, targetTrack);
    }

    private static void ResolveTerminalOpportunity(
        GuidedMissileSalvo salvo,
        HexCoord actualTargetCoordinate,
        MissileTargetTrackSnapshot targetTrack,
        MissileInterceptionPhaseContext? interceptionContext,
        IMissileTerminalRandomSource randomSource,
        ICollection<MissileInterceptionAttemptResult> interceptionAttempts)
    {
        bool newOpportunity = salvo.BeginTerminalOpportunity(
            salvo.CurrentCoordinate);
        if (newOpportunity || !salvo.TerminalEntryDefenseResolved)
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
                actualTargetCoordinate,
                MissileGuidanceReportSource.FreshDatalink,
                targetTrack,
                MissileDatalinkState.Live,
                onboardNavigationSensorInstalled: false,
                targetTerminalEcmStrength: 0,
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
        MissileTargetTrackSnapshot targetTrack)
    {
        salvo.BeginTerminalOpportunity(salvo.CurrentCoordinate);
        var resolution = new MissileTerminalResolution(
            salvo.CurrentCoordinate,
            MissileGuidanceReportSource.FreshDatalink,
            targetTrack.Quality,
            targetCoLocated: false,
            usedSeekerAcquisition: false,
            acquisitionRoll: null,
            acquisitionChancePercent: null,
            hasFirmSolution: false,
            seekerAccuracyApplied: false,
            attackRoll: null,
            effectiveHitChancePercent: null,
            MissileTerminalOutcome.AcquisitionFailed,
            "The Missile Flight reached the supplied guidance coordinate without a Current/Firm terminal solution.");
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

    private static MissileGuidanceDecision CreateCompatibilityDecision(
        MissileTargetTrackSnapshot targetTrack)
    {
        var candidate = new MissileGuidanceReportCandidate(
            MissileGuidanceReportSource.FreshDatalink,
            targetTrack,
            sourceObservationEpoch: 1,
            uncertaintyRadiusHexes: targetTrack.UncertaintyRadiusHexes,
            age: 0);
        return new MissileGuidanceDecision(
            targetTrack.TargetId,
            candidate,
            new[] { candidate },
            "The compatibility guidance path consumed the supplied launcher report.");
    }

    private static GuidedMissileAdvanceResult CreateResult(
        GuidedMissileSalvo salvo,
        HexCoord startingCoordinate,
        HexCoord? guidanceCoordinate,
        MissileRouteResult? routePlan,
        IEnumerable<HexCoord> enteredCoordinates,
        IEnumerable<MissileInterceptionAttemptResult> interceptionAttempts,
        int startingSearchFuel) =>
        new(
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
}
