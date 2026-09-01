using System.Text.Json;
using StarCluster.Core.Combat.Tactics;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class SystemMapResearchParityTests
{
    [Fact]
    public void SharedResearchFixtureMatchesProductionGeometryPrimitives()
    {
        string fixturePath = FindRepositoryFile(
            "docs", "archive", "testing", "pre-cp165-active", "system_map_research_parity_fixtures_v0_1.json");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(fixturePath));
        JsonElement root = document.RootElement;
        int radius = root.GetProperty("mapRadius").GetInt32();
        HexMap map = HexMap.CreateHexagon(radius);

        Assert.Equal(root.GetProperty("expectedCellCount").GetInt32(), map.CellCount);

        foreach (JsonElement row in root.GetProperty("searchCases").EnumerateArray())
        {
            EncounterSearchMove move = EncounterSearchMovementResolver.ResolveTowardCenter(
                map,
                ReadCoord(row.GetProperty("origin")),
                row.GetProperty("available").GetInt32());
            Assert.Equal(ReadCoord(row.GetProperty("destination")), move.Destination);
            Assert.Equal(row.GetProperty("movement").GetInt32(), move.MovementHexes);
        }

        foreach (JsonElement row in root.GetProperty("movementCases").EnumerateArray())
        {
            RangeOrder order = Enum.Parse<RangeOrder>(row.GetProperty("order").GetString()!, ignoreCase: false);
            var plan = new TacticalOrderPlan(
                order,
                "CP126 shared research parity fixture",
                row.GetProperty("desired").GetInt32());
            FiniteTacticalMove move = FiniteTacticalMovementResolver.Resolve(
                map,
                ReadCoord(row.GetProperty("origin")),
                ReadCoord(row.GetProperty("target")),
                row.GetProperty("available").GetInt32(),
                plan);

            Assert.Equal(ReadCoord(row.GetProperty("destination")), move.Destination);
            Assert.Equal(ReadPath(row.GetProperty("path")), move.Path);
            Assert.Equal(row.GetProperty("finalRange").GetInt32(), move.FinalRangeHexes);
            Assert.Equal(row.GetProperty("closest").GetInt32(), move.ClosestApproachHexes);
            Assert.Equal(row.GetProperty("farthest").GetInt32(), move.FarthestSeparationHexes);
            Assert.Equal(row.GetProperty("movement").GetInt32(), move.MovementHexes);
            Assert.Equal(row.GetProperty("boundary").GetBoolean(), move.EndedOnBoundary);
        }

        foreach (JsonElement row in root.GetProperty("missileCases").EnumerateArray())
        {
            FiniteMissileAdvance move = FiniteMissileMovementResolver.Resolve(
                map,
                ReadCoord(row.GetProperty("origin")),
                ReadCoord(row.GetProperty("target")),
                row.GetProperty("speed").GetInt32(),
                row.GetProperty("maximumTravel").GetInt32(),
                row.GetProperty("alreadyTraveled").GetInt32());

            Assert.Equal(ReadCoord(row.GetProperty("destination")), move.Destination);
            Assert.Equal(ReadPath(row.GetProperty("path")), move.Path);
            Assert.Equal(row.GetProperty("movement").GetInt32(), move.DistanceTraveledThisPhase);
            Assert.Equal(row.GetProperty("totalTraveled").GetInt32(), move.TotalDistanceTraveled);
            Assert.Equal(row.GetProperty("terminal").GetBoolean(), move.Terminal);
            Assert.Equal(row.GetProperty("rangeExhausted").GetBoolean(), move.RangeExhausted);
        }
    }

    [Fact]
    public void FiniteMovementAndMissilePursuitRespectPhysicalMirrorSymmetry()
    {
        HexMap map = HexMap.CreateHexagon(5);
        HexCoord origin = new(-2, 1);
        HexCoord target = new(3, -1);
        var plan = new TacticalOrderPlan(RangeOrder.Close, "mirror symmetry", 2);

        FiniteTacticalMove first = FiniteTacticalMovementResolver.Resolve(map, origin, target, 3, plan);
        FiniteTacticalMove mirror = FiniteTacticalMovementResolver.Resolve(
            map, Mirror(origin), Mirror(target), 3, plan);
        Assert.Equal(Mirror(first.Destination), mirror.Destination);
        Assert.Equal(first.Path.Select(Mirror).ToArray(), mirror.Path);

        HexCoord colocated = new(2, 3);
        var openPlan = new TacticalOrderPlan(RangeOrder.Open, "co-located mirror symmetry", 4);
        FiniteTacticalMove colocatedFirst = FiniteTacticalMovementResolver.Resolve(
            map, colocated, colocated, 3, openPlan, new HexCoord(-5, 0));
        FiniteTacticalMove colocatedMirror = FiniteTacticalMovementResolver.Resolve(
            map, Mirror(colocated), Mirror(colocated), 3, openPlan, new HexCoord(5, 0));
        Assert.Equal(Mirror(colocatedFirst.Destination), colocatedMirror.Destination);
        Assert.Equal(colocatedFirst.Path.Select(Mirror).ToArray(), colocatedMirror.Path);

        FiniteMissileAdvance missile = FiniteMissileMovementResolver.Resolve(
            map, new HexCoord(-5, 0), new HexCoord(2, -1), 3, 9, 0);
        FiniteMissileAdvance missileMirror = FiniteMissileMovementResolver.Resolve(
            map, new HexCoord(5, 0), new HexCoord(-2, 1), 3, 9, 0);
        Assert.Equal(Mirror(missile.Destination), missileMirror.Destination);
        Assert.Equal(missile.Path.Select(Mirror).ToArray(), missileMirror.Path);
    }

    private static HexCoord Mirror(HexCoord coordinate) => new(-coordinate.Q, -coordinate.R);

    private static HexCoord ReadCoord(JsonElement element)
    {
        int[] values = element.EnumerateArray().Select(item => item.GetInt32()).ToArray();
        return new HexCoord(values[0], values[1]);
    }

    private static IReadOnlyList<HexCoord> ReadPath(JsonElement element) =>
        element.EnumerateArray().Select(ReadCoord).ToArray();

    private static string FindRepositoryFile(params string[] parts)
    {
        IEnumerable<string> starts = new[] { Directory.GetCurrentDirectory(), AppContext.BaseDirectory };
        foreach (string start in starts)
        {
            DirectoryInfo? current = new(start);
            while (current is not null)
            {
                string candidate = Path.Combine(new[] { current.FullName }.Concat(parts).ToArray());
                if (File.Exists(candidate))
                {
                    return candidate;
                }
                current = current.Parent;
            }
        }

        throw new FileNotFoundException(
            $"Unable to locate repository fixture: {Path.Combine(parts)}");
    }
}
