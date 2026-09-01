using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tactics;

/// <summary>
/// Advances a finite-map missile toward the target's current coordinate while
/// respecting missile speed and total travel range. Equal shortest routes use
/// a target-relative tie break so physical 180-degree mirrors remain mirrors.
/// </summary>
public static class FiniteMissileMovementResolver
{
    public static FiniteMissileAdvance Resolve(
        HexMap map,
        HexCoord missileCoordinate,
        HexCoord targetCoordinate,
        int speedHexesPerTurn,
        int maximumTravelHexes,
        int distanceTraveled)
    {
        ArgumentNullException.ThrowIfNull(map);
        if (!map.Contains(missileCoordinate) || !map.Contains(targetCoordinate))
        {
            throw new ArgumentOutOfRangeException(nameof(missileCoordinate));
        }
        if (speedHexesPerTurn < 0 || maximumTravelHexes < 0 || distanceTraveled < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(speedHexesPerTurn));
        }

        int remainingRange = Math.Max(0, maximumTravelHexes - distanceTraveled);
        int stepBudget = Math.Min(speedHexesPerTurn, remainingRange);
        var path = new List<HexCoord> { missileCoordinate };
        int moved = 0;
        for (int step = 0;
             step < stepBudget && missileCoordinate != targetCoordinate;
             step++)
        {
            int currentDistance = missileCoordinate.DistanceTo(targetCoordinate);
            missileCoordinate = map.NeighborsOf(missileCoordinate)
                .Where(cell => cell.DistanceTo(targetCoordinate) == currentDistance - 1)
                .OrderBy(cell => RelativeTie(missileCoordinate, targetCoordinate, cell).AbsoluteCross)
                .ThenBy(cell => RelativeTie(missileCoordinate, targetCoordinate, cell).Cross)
                .ThenBy(cell => RelativeTie(missileCoordinate, targetCoordinate, cell).NegativeDot2)
                .First();
            path.Add(missileCoordinate);
            moved++;
        }

        int total = checked(distanceTraveled + moved);
        int distance = missileCoordinate.DistanceTo(targetCoordinate);
        return new FiniteMissileAdvance(
            missileCoordinate,
            Array.AsReadOnly(path.ToArray()),
            moved,
            total,
            Terminal: distance == 0,
            RangeExhausted: distance > 0 && total >= maximumTravelHexes);
    }

    private static (int AbsoluteCross, int Cross, int NegativeDot2) RelativeTie(
        HexCoord origin,
        HexCoord target,
        HexCoord candidate)
    {
        int vq = target.Q - origin.Q;
        int vr = target.R - origin.R;
        int wq = candidate.Q - origin.Q;
        int wr = candidate.R - origin.R;
        int cross = checked((vq * wr) - (vr * wq));
        int dot2 = checked((2 * vq * wq) + (vq * wr) + (vr * wq) + (2 * vr * wr));
        return (Math.Abs(cross), cross, -dot2);
    }
}

public sealed record FiniteMissileAdvance(
    HexCoord Destination,
    IReadOnlyList<HexCoord> Path,
    int DistanceTraveledThisPhase,
    int TotalDistanceTraveled,
    bool Terminal,
    bool RangeExhausted);
