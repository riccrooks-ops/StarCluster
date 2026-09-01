using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Immutable report from one missile guidance, movement, interception, and
/// possible terminal-resolution action.
/// </summary>
public sealed class GuidedMissileAdvanceResult
{
    internal GuidedMissileAdvanceResult(
        GuidedMissileStatus status,
        HexCoord startingCoordinate,
        HexCoord endingCoordinate,
        HexCoord? guidanceCoordinate,
        MissileRouteResult? routePlan,
        IEnumerable<HexCoord> enteredCoordinates)
        : this(
            status,
            startingCoordinate,
            endingCoordinate,
            guidanceCoordinate,
            routePlan,
            enteredCoordinates,
            Array.Empty<MissileInterceptionAttemptResult>(),
            stationarySearchFuelSpentThisPhase: 0,
            terminalResolution: null)
    {
    }

    internal GuidedMissileAdvanceResult(
        GuidedMissileStatus status,
        HexCoord startingCoordinate,
        HexCoord endingCoordinate,
        HexCoord? guidanceCoordinate,
        MissileRouteResult? routePlan,
        IEnumerable<HexCoord> enteredCoordinates,
        IEnumerable<MissileInterceptionAttemptResult> interceptionAttempts,
        int stationarySearchFuelSpentThisPhase = 0,
        MissileTerminalResolution? terminalResolution = null)
    {
        ArgumentNullException.ThrowIfNull(enteredCoordinates);
        ArgumentNullException.ThrowIfNull(interceptionAttempts);
        if (!Enum.IsDefined(status))
        {
            throw new ArgumentOutOfRangeException(nameof(status));
        }
        if (stationarySearchFuelSpentThisPhase < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(stationarySearchFuelSpentThisPhase));
        }

        Status = status;
        StartingCoordinate = startingCoordinate;
        EndingCoordinate = endingCoordinate;
        GuidanceCoordinate = guidanceCoordinate;
        RoutePlan = routePlan;
        EnteredCoordinates = Array.AsReadOnly(enteredCoordinates.ToArray());
        InterceptionAttempts = Array.AsReadOnly(interceptionAttempts.ToArray());
        StationarySearchFuelSpentThisPhase = stationarySearchFuelSpentThisPhase;
        TerminalResolution = terminalResolution;
    }

    public GuidedMissileStatus Status { get; }

    public HexCoord StartingCoordinate { get; }

    public HexCoord EndingCoordinate { get; }

    public HexCoord? GuidanceCoordinate { get; }

    public MissileRouteResult? RoutePlan { get; }

    public IReadOnlyList<HexCoord> EnteredCoordinates { get; }

    public IReadOnlyList<MissileInterceptionAttemptResult> InterceptionAttempts { get; }

    public MissileTerminalResolution? TerminalResolution { get; }

    public int StationarySearchFuelSpentThisPhase { get; }

    public int FuelSpentThisPhase => checked(
        DistanceTraveledThisPhase + StationarySearchFuelSpentThisPhase);

    public int DistanceTraveledThisPhase => EnteredCoordinates.Count;

    public bool WasIntercepted =>
        InterceptionAttempts.Any(attempt => attempt.Intercepted);

    public bool TerminalAttackResolved =>
        TerminalResolution?.AttackWasResolved == true;

    public bool Waited => DistanceTraveledThisPhase == 0 &&
        (Status is
            GuidedMissileStatus.WaitingForRoute or
            GuidedMissileStatus.WaitingForTrack or
            GuidedMissileStatus.Searching);
}
