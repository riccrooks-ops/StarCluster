using System.Linq;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileLaunchServiceTests
{
    [Fact]
    public void CloseTargetCanBeHitDuringTheSingleLaunchAdvance()
    {
        SystemMap map = CreateMap(5);
        var target = new HexCoord(0, 2);

        GuidedMissileLaunchResult result = Launch(
            map,
            new HexCoord(-2, 2),
            target,
            range: 8,
            speed: 2);

        Assert.Equal(GuidedMissileStatus.Expended, result.Salvo.Status);
        Assert.Equal(MissileTerminalOutcome.Hit, result.AdvanceResult.TerminalResolution!.Outcome);
        Assert.Equal(target, result.Salvo.CurrentCoordinate);
        Assert.Equal(2, result.AdvanceResult.DistanceTraveledThisPhase);
        Assert.Equal(1, result.Salvo.GuidancePhaseCount);
    }

    [Fact]
    public void LongRouteRemainsInFlightAfterOnlyOneLaunchAdvance()
    {
        SystemMap map = CreateMap(6);
        var launch = new HexCoord(-4, 0);
        var target = new HexCoord(4, 0);

        GuidedMissileLaunchResult result = Launch(
            map,
            launch,
            target,
            range: 12,
            speed: 2);

        Assert.Equal(GuidedMissileStatus.InFlight, result.Salvo.Status);
        Assert.NotEqual(target, result.Salvo.CurrentCoordinate);
        Assert.Equal(2, result.Salvo.DistanceTraveled);
        Assert.Equal(1, result.Salvo.GuidancePhaseCount);
        Assert.NotNull(result.AdvanceResult.RoutePlan);
        Assert.True(
            result.AdvanceResult.RoutePlan!.RoutedDistance.GetValueOrDefault() > 2);
    }

    [Fact]
    public void LaunchServiceNeverFastForwardsBeyondMissileSpeed()
    {
        SystemMap map = CreateMap(7);

        GuidedMissileLaunchResult result = Launch(
            map,
            new HexCoord(-5, 1),
            new HexCoord(5, -1),
            range: 14,
            speed: 3);

        Assert.Equal(1, result.Salvo.GuidancePhaseCount);
        Assert.InRange(result.Salvo.DistanceTraveled, 0, 3);
        Assert.Equal(
            result.Salvo.DistanceTraveled,
            result.AdvanceResult.DistanceTraveledThisPhase);
    }

    [Fact]
    public void NoRouteAtLaunchWaitsWithoutSpendingRange()
    {
        SystemMap map = CreateMap(4);
        var target = new HexCoord(1, 0);
        EncloseTarget(map, target);

        GuidedMissileLaunchResult result = Launch(
            map,
            new HexCoord(-3, 3),
            target,
            range: 9,
            speed: 2);

        Assert.Equal(GuidedMissileStatus.WaitingForRoute, result.Salvo.Status);
        Assert.Equal(0, result.Salvo.DistanceTraveled);
        Assert.Equal(9, result.Salvo.RemainingRange);
        Assert.True(result.AdvanceResult.Waited);
    }

    [Fact]
    public void LostTrackAtLaunchWaitsWithoutSpendingRange()
    {
        SystemMap map = CreateMap(5);
        var launch = new HexCoord(-3, 3);
        var profile = new MissileFlightProfile(2, 8, 2);

        GuidedMissileLaunchResult result =
            MissileLaunchService.LaunchAndAdvanceOnePhase(
                map,
                "salvo",
                "launcher",
                TargetId,
                launch,
                profile,
                MissileTargetTrackSnapshot.Lost(TargetId));

        Assert.Equal(GuidedMissileStatus.WaitingForTrack, result.Salvo.Status);
        Assert.Equal(launch, result.Salvo.CurrentCoordinate);
        Assert.Equal(0, result.Salvo.DistanceTraveled);
        Assert.Equal(1, result.Salvo.GuidancePhaseCount);
    }

    private static GuidedMissileLaunchResult Launch(
        SystemMap map,
        HexCoord launch,
        HexCoord target,
        int range,
        int speed) =>
        MissileLaunchService.LaunchAndAdvanceOnePhase(
            map,
            "salvo",
            "launcher",
            TargetId,
            launch,
            new MissileFlightProfile(2, range, speed),
            MissileTargetTrackSnapshot.Current(TargetId, target));

    private static SystemMap CreateMap(int radius) =>
        SystemMap.Create(
            radius,
            MapObject.CreateStar("star", "Primary Star"));

    private static void EncloseTarget(SystemMap map, HexCoord target)
    {
        int index = 0;

        foreach (HexCoord neighbor in target.Neighbors().Where(map.Geometry.Contains))
        {
            if (map.GetCell(neighbor).Occupants.Any(
                    item => item.Kind is MapObjectKind.Star or MapObjectKind.Planet))
            {
                continue;
            }

            map.Place(
                MapObject.CreatePlanet($"blocker-{index}", $"Blocker {index}"),
                neighbor);
            index++;
        }
    }

    private const string TargetId = "target";
}
