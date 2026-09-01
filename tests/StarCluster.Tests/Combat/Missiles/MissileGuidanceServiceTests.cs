using System;
using System.Linq;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileGuidanceServiceTests
{
    [Fact]
    public void CurrentTrackAdvancesByAtMostTheMissileSpeed()
    {
        SystemMap map = CreateMap(6);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 10, speed: 2);

        GuidedMissileAdvanceResult result = Advance(map, salvo, new HexCoord(2, 3));

        Assert.Equal(2, result.DistanceTraveledThisPhase);
        Assert.Equal(2, salvo.DistanceTraveled);
        Assert.Equal(8, salvo.RemainingRange);
        Assert.Equal(GuidedMissileStatus.InFlight, salvo.Status);
    }

    [Fact]
    public void ReachingTheCurrentTrackedCoordinateResolvesTerminalAttack()
    {
        SystemMap map = CreateMap(5);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-2, 2), range: 8, speed: 3);
        var target = new HexCoord(0, 2);

        GuidedMissileAdvanceResult result = Advance(map, salvo, target);

        Assert.Equal(target, result.EndingCoordinate);
        Assert.Equal(GuidedMissileStatus.Expended, result.Status);
        Assert.True(salvo.HasTerminalOpportunity);
        Assert.Equal(MissileTerminalOutcome.Hit, result.TerminalResolution!.Outcome);
    }

    [Fact]
    public void ReplanningPreservesCumulativeDistanceAndRangeUse()
    {
        SystemMap map = CreateMap(7);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 10, speed: 2);

        Advance(map, salvo, new HexCoord(0, 3));
        Advance(map, salvo, new HexCoord(3, 3));

        Assert.Equal(4, salvo.DistanceTraveled);
        Assert.Equal(6, salvo.RemainingRange);
    }

    [Fact]
    public void ReplanningReplacesTheFutureDestination()
    {
        SystemMap map = CreateMap(7);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 10, speed: 1);
        var firstTarget = new HexCoord(0, 3);
        var secondTarget = new HexCoord(3, 2);

        Advance(map, salvo, firstTarget);
        Advance(map, salvo, secondTarget);

        Assert.NotNull(salvo.LastRoutePlan);
        Assert.Equal(
            secondTarget,
            salvo.LastRoutePlan!.Path[salvo.LastRoutePlan.Path.Count - 1]);
    }

    [Fact]
    public void OutOfRangePlanStillAdvancesWhileFuelRemains()
    {
        SystemMap map = CreateMap(6);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 3, speed: 1);

        GuidedMissileAdvanceResult result = Advance(map, salvo, new HexCoord(2, 3));

        Assert.Equal(MissileRouteStatus.OutOfRange, result.RoutePlan!.Status);
        Assert.Equal(1, result.DistanceTraveledThisPhase);
        Assert.Equal(GuidedMissileStatus.InFlight, result.Status);
    }

    [Fact]
    public void NoRouteWaitsWithoutConsumingRange()
    {
        SystemMap map = CreateMap(4);
        var enclosedTarget = new HexCoord(1, 0);
        EncloseTarget(map, enclosedTarget);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 9, speed: 2);

        GuidedMissileAdvanceResult result = Advance(map, salvo, enclosedTarget);

        Assert.Equal(GuidedMissileStatus.WaitingForRoute, result.Status);
        Assert.True(result.Waited);
        Assert.Equal(0, salvo.DistanceTraveled);
        Assert.Equal(9, salvo.RemainingRange);
    }

    [Fact]
    public void WaitingMissileResumesWhenTheTrackedTargetCreatesAReachableRoute()
    {
        SystemMap map = CreateMap(4);
        var enclosedTarget = new HexCoord(1, 0);
        EncloseTarget(map, enclosedTarget);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 9, speed: 2);
        Advance(map, salvo, enclosedTarget);

        GuidedMissileAdvanceResult result = Advance(map, salvo, new HexCoord(-1, 3));

        Assert.Equal(GuidedMissileStatus.Expended, result.Status);
        Assert.Equal(MissileTerminalOutcome.Hit, result.TerminalResolution!.Outcome);
        Assert.Equal(2, salvo.DistanceTraveled);
    }

    [Fact]
    public void LostTrackWaitsWithoutUsingFuel()
    {
        SystemMap map = CreateMap(4);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-2, 2), range: 6, speed: 2);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Lost(TargetId));

        Assert.Equal(GuidedMissileStatus.WaitingForTrack, result.Status);
        Assert.Equal(0, salvo.DistanceTraveled);
        Assert.Null(salvo.LastRoutePlan);
    }

    [Fact]
    public void StaleTrackAdvancesTowardTheLastKnownCoordinate()
    {
        SystemMap map = CreateMap(5);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 8, speed: 1);
        var lastKnown = new HexCoord(0, 3);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Stale(TargetId, lastKnown));

        Assert.Equal(lastKnown, result.GuidanceCoordinate!.Value);
        Assert.Equal(1, result.DistanceTraveledThisPhase);
        Assert.Equal(lastKnown, salvo.LastKnownTargetCoordinate!.Value);
    }

    [Fact]
    public void ReachingAStaleLastKnownCoordinateWaitsForANewTrack()
    {
        SystemMap map = CreateMap(4);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-2, 2), range: 5, speed: 2);
        var lastKnown = new HexCoord(-1, 2);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Stale(TargetId, lastKnown));

        Assert.Equal(lastKnown, salvo.CurrentCoordinate);
        Assert.Equal(GuidedMissileStatus.Searching, result.Status);
        Assert.True(salvo.HasTerminalOpportunity);
        Assert.Equal(MissileTerminalOutcome.AcquisitionFailed, result.TerminalResolution!.Outcome);
    }

    [Fact]
    public void SpendingTheFinalRangeHexWithoutArrivalExhaustsTheMissile()
    {
        SystemMap map = CreateMap(6);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 2, speed: 2);

        GuidedMissileAdvanceResult result = Advance(map, salvo, new HexCoord(2, 3));

        Assert.Equal(2, salvo.DistanceTraveled);
        Assert.Equal(0, salvo.RemainingRange);
        Assert.Equal(GuidedMissileStatus.RangeExhausted, result.Status);
        Assert.True(salvo.IsTerminal);
    }

    [Fact]
    public void TerminalInterceptedMissileDoesNotMoveAgain()
    {
        SystemMap map = CreateMap(5);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-2, 2), range: 6, speed: 2);
        salvo.MarkIntercepted();

        GuidedMissileAdvanceResult result = Advance(map, salvo, new HexCoord(2, 2));

        Assert.Equal(0, result.DistanceTraveledThisPhase);
        Assert.Equal(new HexCoord(-2, 2), salvo.CurrentCoordinate);
        Assert.Equal(GuidedMissileStatus.Intercepted, result.Status);
    }

    [Fact]
    public void TrackForADifferentTargetIsRejected()
    {
        SystemMap map = CreateMap(4);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-2, 2), range: 6, speed: 2);

        Assert.Throws<ArgumentException>(
            () => MissileGuidanceService.AdvanceOnePhase(
                map,
                salvo,
                MissileTargetTrackSnapshot.Current("other-target", new HexCoord(1, 2))));
    }

    [Fact]
    public void FasterTargetCanOutrunASlowerFiniteRangeMissile()
    {
        SystemMap map = CreateMap(8);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 5, speed: 1);

        Advance(map, salvo, new HexCoord(0, 3));
        Advance(map, salvo, new HexCoord(2, 3));
        Advance(map, salvo, new HexCoord(4, 3));
        Advance(map, salvo, new HexCoord(5, 3));
        GuidedMissileAdvanceResult final = Advance(map, salvo, new HexCoord(5, 3));

        Assert.Equal(GuidedMissileStatus.RangeExhausted, final.Status);
        Assert.NotEqual(new HexCoord(5, 3), salvo.CurrentCoordinate);
        Assert.Equal(5, salvo.DistanceTraveled);
    }

    [Fact]
    public void CloseLaunchCanCatchATargetThatMovedFartherThatTurn()
    {
        SystemMap map = CreateMap(6);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-3, 3), range: 8, speed: 3);
        var targetAfterMoving = new HexCoord(-1, 3);

        GuidedMissileAdvanceResult result = Advance(map, salvo, targetAfterMoving);

        Assert.Equal(GuidedMissileStatus.Expended, result.Status);
        Assert.Equal(MissileTerminalOutcome.Hit, result.TerminalResolution!.Outcome);
        Assert.Equal(targetAfterMoving, salvo.CurrentCoordinate);
    }

    [Fact]
    public void EveryNonterminalGuidanceAttemptCountsAsAPhaseIncludingWaiting()
    {
        SystemMap map = CreateMap(4);
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(-2, 2), range: 6, speed: 2);

        MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Lost(TargetId));
        Advance(map, salvo, new HexCoord(0, 2));

        Assert.Equal(2, salvo.GuidancePhaseCount);
    }

    private static GuidedMissileAdvanceResult Advance(
        SystemMap map,
        GuidedMissileSalvo salvo,
        HexCoord targetCoordinate) =>
        MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, targetCoordinate));

    private static GuidedMissileSalvo CreateSalvo(
        HexCoord launch,
        int range,
        int speed) =>
        new(
            "salvo",
            "ship-launcher",
            TargetId,
            launch,
            new MissileFlightProfile(2, range, speed));

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

    private const string TargetId = "ship-target";
}
