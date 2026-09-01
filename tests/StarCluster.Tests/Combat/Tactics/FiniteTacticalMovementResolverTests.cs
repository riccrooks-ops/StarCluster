using StarCluster.Core.Combat.Tactics;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class FiniteTacticalMovementResolverTests
{
    [Fact]
    public void RadiusFiveMapHasProductionSystemGeometry()
    {
        HexMap map = HexMap.CreateHexagon(5);
        Assert.Equal(11, map.Diameter);
        Assert.Equal(91, map.CellCount);
    }

    [Fact]
    public void CloseOrderMovesTowardObservedTarget()
    {
        HexMap map = HexMap.CreateHexagon(5);
        HexCoord origin = new(-2, 0);
        HexCoord target = new(2, 0);
        var plan = new TacticalOrderPlan(RangeOrder.Close, "test", 3);

        FiniteTacticalMove move = FiniteTacticalMovementResolver.Resolve(
            map, origin, target, 1, plan);

        Assert.Equal(1, move.MovementHexes);
        Assert.Equal(3, move.FinalRangeHexes);
    }

    [Fact]
    public void OpenOrderCannotLeaveFiniteMap()
    {
        HexMap map = HexMap.CreateHexagon(5);
        HexCoord origin = new(-5, 0);
        HexCoord target = HexCoord.Zero;
        var plan = new TacticalOrderPlan(RangeOrder.Open, "test", 6);

        FiniteTacticalMove move = FiniteTacticalMovementResolver.Resolve(
            map, origin, target, 1, plan);

        Assert.True(map.Contains(move.Destination));
        Assert.True(move.FinalRangeHexes <= 5);
    }

    [Fact]
    public void PathRecordsClosestApproachSeparatelyFromFinalRange()
    {
        HexMap map = HexMap.CreateHexagon(5);
        HexCoord origin = new(-1, 0);
        HexCoord target = HexCoord.Zero;
        var plan = new TacticalOrderPlan(RangeOrder.Open, "test", 2);

        FiniteTacticalMove move = FiniteTacticalMovementResolver.Resolve(
            map, origin, target, 3, plan);

        Assert.Equal(2, move.FinalRangeHexes);
        Assert.True(move.ClosestApproachHexes <= move.FinalRangeHexes);
    }
}
