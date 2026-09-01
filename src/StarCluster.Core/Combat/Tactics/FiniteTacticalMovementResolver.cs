using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tactics;

/// <summary>
/// Resolves one ship's movement on a finite hex map against the opponent's
/// currently observed coordinate. This is intentionally a movement primitive,
/// not a full tactical AI.
/// </summary>
public static class FiniteTacticalMovementResolver
{
    public static FiniteTacticalMove Resolve(
        HexMap map,
        HexCoord origin,
        HexCoord target,
        int availableMovementHexes,
        TacticalOrderPlan plan,
        HexCoord? tieBreakReference = null)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(plan);
        if (!map.Contains(origin))
        {
            throw new ArgumentOutOfRangeException(nameof(origin));
        }
        if (!map.Contains(target))
        {
            throw new ArgumentOutOfRangeException(nameof(target));
        }
        if (availableMovementHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(availableMovementHexes));
        }

        int initialRange = origin.DistanceTo(target);
        if (availableMovementHexes == 0 || plan.RangeOrder == RangeOrder.Hold)
        {
            return BuildMove(map, origin, target, plan, new[] { origin });
        }

        HexCoord destination = map.Cells
            .Where(cell => origin.DistanceTo(cell) <= availableMovementHexes)
            .OrderBy(cell => DirectionPenalty(plan.RangeOrder, initialRange, cell.DistanceTo(target)))
            .ThenBy(cell => DesiredRangeError(plan, initialRange, availableMovementHexes, cell.DistanceTo(target)))
            .ThenByDescending(cell => InteriorMargin(map, cell))
            .ThenBy(cell => origin.DistanceTo(cell))
            .ThenBy(cell => RelativeTie(origin, target, cell, tieBreakReference).AbsoluteCross)
            .ThenBy(cell => RelativeTie(origin, target, cell, tieBreakReference).Cross)
            .ThenBy(cell => RelativeTie(origin, target, cell, tieBreakReference).NegativeDot2)
            .First();

        IReadOnlyList<HexCoord> path = BuildShortestPath(
            map,
            origin,
            destination,
            target,
            plan,
            tieBreakReference);
        return BuildMove(map, origin, target, plan, path);
    }

    private static FiniteTacticalMove BuildMove(
        HexMap map,
        HexCoord origin,
        HexCoord target,
        TacticalOrderPlan plan,
        IReadOnlyList<HexCoord> path)
    {
        HexCoord destination = path[^1];
        int closest = path.Min(cell => cell.DistanceTo(target));
        int farthest = path.Max(cell => cell.DistanceTo(target));
        return new FiniteTacticalMove(
            origin,
            destination,
            Array.AsReadOnly(path.ToArray()),
            destination.DistanceTo(target),
            closest,
            farthest,
            path.Count - 1,
            map.IsBoundary(destination),
            plan.RangeOrder,
            plan.DesiredRangeHexes);
    }

    private static int DirectionPenalty(
        RangeOrder order,
        int initialRange,
        int candidateRange) => order switch
        {
            RangeOrder.Close when candidateRange > initialRange => 1,
            RangeOrder.Open when candidateRange < initialRange => 1,
            _ => 0,
        };

    private static int DesiredRangeError(
        TacticalOrderPlan plan,
        int initialRange,
        int availableMovementHexes,
        int candidateRange)
    {
        int desired = plan.DesiredRangeHexes ?? plan.RangeOrder switch
        {
            RangeOrder.Close => Math.Max(0, initialRange - availableMovementHexes),
            RangeOrder.Open => initialRange + availableMovementHexes,
            _ => initialRange,
        };
        return Math.Abs(candidateRange - desired);
    }

    private static int InteriorMargin(HexMap map, HexCoord coordinate) =>
        map.Radius - coordinate.Length();

    private static IReadOnlyList<HexCoord> BuildShortestPath(
        HexMap map,
        HexCoord origin,
        HexCoord destination,
        HexCoord target,
        TacticalOrderPlan plan,
        HexCoord? tieBreakReference)
    {
        var path = new List<HexCoord> { origin };
        HexCoord current = origin;
        while (current != destination)
        {
            int remaining = current.DistanceTo(destination);
            HexCoord next = map.NeighborsOf(current)
                .Where(cell => cell.DistanceTo(destination) == remaining - 1)
                .OrderBy(cell => PathOrderScore(plan, cell.DistanceTo(target)))
                .ThenByDescending(cell => InteriorMargin(map, cell))
                .ThenBy(cell => RelativeTie(current, target, cell, tieBreakReference).AbsoluteCross)
                .ThenBy(cell => RelativeTie(current, target, cell, tieBreakReference).Cross)
                .ThenBy(cell => RelativeTie(current, target, cell, tieBreakReference).NegativeDot2)
                .First();
            path.Add(next);
            current = next;
        }
        return path;
    }

    private static int PathOrderScore(TacticalOrderPlan plan, int range) =>
        plan.RangeOrder switch
        {
            RangeOrder.Close => range,
            RangeOrder.Open => -range,
            RangeOrder.MaintainPreferredRange when plan.DesiredRangeHexes is int desired =>
                Math.Abs(range - desired),
            _ => 0,
        };

    private static (int AbsoluteCross, int Cross, int NegativeDot2) RelativeTie(
        HexCoord origin,
        HexCoord target,
        HexCoord candidate,
        HexCoord? tieBreakReference)
    {
        int vq = target.Q - origin.Q;
        int vr = target.R - origin.R;
        if (vq == 0 && vr == 0 && tieBreakReference is HexCoord reference)
        {
            vq = reference.Q - origin.Q;
            vr = reference.R - origin.R;
        }
        if (vq == 0 && vr == 0)
        {
            vq = -origin.Q;
            vr = -origin.R;
        }
        int wq = candidate.Q - origin.Q;
        int wr = candidate.R - origin.R;
        int cross = checked((vq * wr) - (vr * wq));
        int dot2 = checked((2 * vq * wq) + (vq * wr) + (vr * wq) + (2 * vr * wr));
        return (Math.Abs(cross), cross, -dot2);
    }
}

public sealed record FiniteTacticalMove(
    HexCoord Origin,
    HexCoord Destination,
    IReadOnlyList<HexCoord> Path,
    int FinalRangeHexes,
    int ClosestApproachHexes,
    int FarthestSeparationHexes,
    int MovementHexes,
    bool EndedOnBoundary,
    RangeOrder RequestedOrder,
    int? DesiredRangeHexes);
