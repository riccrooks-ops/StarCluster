using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class GuidedMissileOwnershipTests
{
    [Fact]
    public void OwnershipAndLaunchCoordinateAreRecorded()
    {
        var launch = new HexCoord(-2, 2);
        var salvo = new GuidedMissileSalvo(
            "friendly-1",
            TacticalSide.Player,
            "ship-player",
            "ship-enemy",
            launch,
            new MissileFlightProfile(2, 8, 2));

        Assert.Equal(TacticalSide.Player, salvo.OwnerSide);
        Assert.Equal("ship-player", salvo.LauncherId);
        Assert.Equal("ship-enemy", salvo.TargetId);
        Assert.Equal(new[] { launch }, salvo.TravelHistory);
    }

    [Fact]
    public void TravelHistoryAccumulatesAcrossGuidanceReplans()
    {
        SystemMap map = CreateMap(6);
        var launch = new HexCoord(-3, 3);
        GuidedMissileSalvo salvo = CreateOwnedSalvo(launch);

        MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-enemy",
                new HexCoord(0, 3)));
        MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-enemy",
                new HexCoord(2, 3)));

        Assert.Equal(5, salvo.TravelHistory.Count);
        Assert.Equal(launch, salvo.TravelHistory[0]);
        Assert.Equal(salvo.CurrentCoordinate, salvo.TravelHistory[^1]);
        Assert.Equal(salvo.DistanceTraveled + 1, salvo.TravelHistory.Count);
    }

    [Fact]
    public void CompatibilityConstructorUsesUnspecifiedSide()
    {
        var salvo = new GuidedMissileSalvo(
            "legacy",
            "ship-launcher",
            "ship-target",
            new HexCoord(-1, 1),
            new MissileFlightProfile(1, 5, 1));

        Assert.Equal(TacticalSide.Unspecified, salvo.OwnerSide);
    }

    [Fact]
    public void NamedInterceptionRecordsDefenseSystemId()
    {
        GuidedMissileSalvo salvo = CreateOwnedSalvo(new HexCoord(-2, 2));

        salvo.MarkIntercepted("point-defense-player");

        Assert.Equal(GuidedMissileStatus.Intercepted, salvo.Status);
        Assert.Equal(
            "point-defense-player",
            salvo.InterceptedByDefenseSystemId);
    }

    private static GuidedMissileSalvo CreateOwnedSalvo(HexCoord launch) =>
        new(
            "salvo",
            TacticalSide.Player,
            "ship-player",
            "ship-enemy",
            launch,
            new MissileFlightProfile(2, 10, 2));

    private static SystemMap CreateMap(int radius) =>
        SystemMap.Create(
            radius,
            MapObject.CreateStar("star", "Primary Star"));
}
