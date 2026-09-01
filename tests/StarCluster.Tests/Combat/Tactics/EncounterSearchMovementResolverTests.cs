using StarCluster.Core.Combat.Tactics;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class EncounterSearchMovementResolverTests
{
    [Fact]
    public void EdgeSearchMovesExactlyOneHexTowardCenter()
    {
        HexMap map = HexMap.CreateHexagon(5);
        EncounterSearchMove move = EncounterSearchMovementResolver.ResolveTowardCenter(
            map,
            new HexCoord(-5, 0),
            availableMovementHexes: 4);
        Assert.Equal(1, move.MovementHexes);
        Assert.Equal(4, move.Destination.Length());
    }

    [Fact]
    public void SearchDoesNotMoveWhenStlIsUnavailable()
    {
        HexMap map = HexMap.CreateHexagon(5);
        EncounterSearchMove move = EncounterSearchMovementResolver.ResolveTowardCenter(
            map,
            new HexCoord(-5, 0),
            availableMovementHexes: 0);
        Assert.Equal(0, move.MovementHexes);
        Assert.Equal(new HexCoord(-5, 0), move.Destination);
    }

    [Fact]
    public void SearchHoldsAtMapCenter()
    {
        HexMap map = HexMap.CreateHexagon(5);
        EncounterSearchMove move = EncounterSearchMovementResolver.ResolveTowardCenter(
            map,
            HexCoord.Zero,
            availableMovementHexes: 4);
        Assert.Equal(0, move.MovementHexes);
        Assert.Equal(HexCoord.Zero, move.Destination);
    }
}
