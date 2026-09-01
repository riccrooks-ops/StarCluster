using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class TacticalMissileKnowledgeTests
{
    [Fact]
    public void OwnMissileUsesExactCoordinateAndHistory()
    {
        GuidedMissileSalvo salvo = CreateSalvo(TacticalSide.Player);
        var repository = new TacticalTrackRepository();

        TacticalMissileContact contact = Assert.Single(
            TacticalMissileKnowledgeService.Build(
                new[] { salvo },
                repository,
                "player",
                TacticalSide.Player));

        Assert.Equal(salvo.CurrentCoordinate, contact.Coordinate);
        Assert.Equal(TacticalTrackQuality.Firm, contact.TrackQuality);
        Assert.Equal(
            salvo.TravelHistory.ToArray(),
            contact.VisibleTravelHistory.ToArray());
    }

    [Fact]
    public void HostileStaleMissileUsesTrackCoordinateWithoutTruthHistory()
    {
        GuidedMissileSalvo salvo = CreateSalvo(TacticalSide.Enemy);
        var repository = new TacticalTrackRepository();
        var estimated = new HexCoord(1, -1);
        repository.SeedPriorIntelligence(
            "player",
            salvo.Id,
            estimated,
            sequence: 1);

        TacticalMissileContact contact = Assert.Single(
            TacticalMissileKnowledgeService.Build(
                new[] { salvo },
                repository,
                "player",
                TacticalSide.Player));

        Assert.Equal(estimated, contact.Coordinate);
        Assert.NotEqual(salvo.CurrentCoordinate, contact.Coordinate);
        Assert.Equal(TacticalTrackQuality.Stale, contact.TrackQuality);
        Assert.Empty(contact.VisibleTravelHistory);
        Assert.Null(contact.VisibleLastExecutedRoute);
    }

    [Fact]
    public void UnknownHostileMissileIsNotPresented()
    {
        GuidedMissileSalvo salvo = CreateSalvo(TacticalSide.Enemy);
        var repository = new TacticalTrackRepository();

        Assert.Empty(TacticalMissileKnowledgeService.Build(
            new[] { salvo },
            repository,
            "player",
            TacticalSide.Player));
    }

    private static GuidedMissileSalvo CreateSalvo(TacticalSide side) =>
        new(
            "salvo",
            side,
            side == TacticalSide.Player ? "player" : "enemy",
            side == TacticalSide.Player ? "enemy" : "player",
            new HexCoord(3, -1),
            new MissileFlightProfile(
                technologyLevel: 2,
                maximumRange: 10,
                speedHexesPerTurn: 2));
}
