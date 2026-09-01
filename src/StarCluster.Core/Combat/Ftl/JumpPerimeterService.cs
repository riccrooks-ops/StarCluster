using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Ftl;

public static class JumpPerimeterService
{
    public static bool IsGravityRestricted(
        HexMap map,
        HexCoord coordinate,
        IEnumerable<HexCoord> celestialBodies)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(celestialBodies);
        if (!map.IsBoundary(coordinate))
        {
            return false;
        }
        return celestialBodies.Any(body => coordinate.DistanceTo(body) == 1);
    }

    public static bool IsLegalRegularJumpHex(
        HexMap map,
        HexCoord coordinate,
        IEnumerable<HexCoord> celestialBodies) =>
        map.IsBoundary(coordinate) &&
        !IsGravityRestricted(map, coordinate, celestialBodies);

    public static IReadOnlyList<HexCoord> LegalRegularJumpHexes(
        HexMap map,
        IEnumerable<HexCoord> celestialBodies)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(celestialBodies);
        HexCoord[] bodies = celestialBodies.ToArray();
        HexCoord[] result = map.Cells
            .Where(map.IsBoundary)
            .Where(coordinate => !IsGravityRestricted(map, coordinate, bodies))
            .OrderBy(coordinate => coordinate.Q)
            .ThenBy(coordinate => coordinate.R)
            .ToArray();
        if (result.Length == 0)
        {
            throw new InvalidOperationException(
                "A tactical system map must provide at least one legal Jump Perimeter hex.");
        }
        return Array.AsReadOnly(result);
    }
}
