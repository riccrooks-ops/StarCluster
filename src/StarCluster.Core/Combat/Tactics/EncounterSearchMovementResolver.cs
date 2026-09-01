using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tactics;

/// <summary>
/// Deterministic pre-contact search movement. The mover advances at most one
/// hex toward the map center and does not require or inspect a target location.
/// </summary>
public static class EncounterSearchMovementResolver
{
    public static EncounterSearchMove ResolveTowardCenter(
        HexMap map,
        HexCoord origin,
        int availableMovementHexes)
    {
        ArgumentNullException.ThrowIfNull(map);
        if (!map.Contains(origin))
        {
            throw new ArgumentOutOfRangeException(nameof(origin));
        }
        if (availableMovementHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(availableMovementHexes));
        }
        if (availableMovementHexes == 0 || origin == HexCoord.Zero)
        {
            return new EncounterSearchMove(
                origin,
                origin,
                Array.AsReadOnly(new[] { origin }),
                0,
                map.IsBoundary(origin));
        }

        HexCoord destination = map.NeighborsOf(origin)
            .OrderBy(cell => cell.Length())
            .ThenByDescending(cell => map.Radius - cell.Length())
            .ThenBy(cell => cell.Q)
            .ThenBy(cell => cell.R)
            .First();
        return new EncounterSearchMove(
            origin,
            destination,
            Array.AsReadOnly(new[] { origin, destination }),
            1,
            map.IsBoundary(destination));
    }
}

public sealed record EncounterSearchMove(
    HexCoord Origin,
    HexCoord Destination,
    IReadOnlyList<HexCoord> Path,
    int MovementHexes,
    bool EndedOnBoundary);
