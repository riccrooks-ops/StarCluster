using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileGuidanceInterceptionTests
{
    [Fact]
    public void InterceptionStopsMovementAtTheEngagementHex()
    {
        SystemMap map = CreateMap(7);
        GuidedMissileSalvo salvo = CreateSalvo(
            "hostile",
            TacticalSide.Enemy,
            new HexCoord(-3, 3),
            range: 10,
            speed: 4);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(-1, 3),
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Intercepted,
            MissileDefenseSourceType.HeldDirectFireWeapon);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-player",
                new HexCoord(3, 3)),
            context);

        Assert.Equal(new HexCoord(-1, 3), salvo.CurrentCoordinate);
        Assert.Equal(2, result.DistanceTraveledThisPhase);
        Assert.True(result.WasIntercepted);
        Assert.Equal(GuidedMissileStatus.Intercepted, result.Status);
    }

    [Fact]
    public void FinalInterceptionOccursBeforeImpact()
    {
        SystemMap map = CreateMap(5);
        GuidedMissileSalvo salvo = CreateSalvo(
            "hostile",
            TacticalSide.Enemy,
            new HexCoord(-2, 2),
            range: 6,
            speed: 2);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(0, 2),
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Intercepted);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-player",
                new HexCoord(0, 2)),
            context);

        MissileInterceptionAttemptResult attempt =
            Assert.Single(result.InterceptionAttempts);
        Assert.True(attempt.IsFinalApproach);
        Assert.Equal(GuidedMissileStatus.Intercepted, result.Status);
        Assert.True(salvo.HasTerminalOpportunity);
    }

    [Fact]
    public void MissedFinalInterceptionAllowsArrival()
    {
        SystemMap map = CreateMap(5);
        GuidedMissileSalvo salvo = CreateSalvo(
            "hostile",
            TacticalSide.Enemy,
            new HexCoord(-2, 2),
            range: 6,
            speed: 2);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(0, 2),
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Missed);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-player",
                new HexCoord(0, 2)),
            context);

        Assert.Single(result.InterceptionAttempts);
        Assert.Equal(GuidedMissileStatus.Expended, result.Status);
        Assert.True(salvo.HasTerminalOpportunity);
        Assert.Equal(MissileTerminalOutcome.Hit, result.TerminalResolution!.Outcome);
    }

    [Fact]
    public void FastMissileCannotSkipShortDefenseEnvelope()
    {
        SystemMap map = CreateMap(8);
        GuidedMissileSalvo salvo = CreateSalvo(
            "hostile",
            TacticalSide.Enemy,
            new HexCoord(-4, 4),
            range: 12,
            speed: 6);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(0, 4),
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Intercepted,
            MissileDefenseSourceType.HeldDirectFireWeapon);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-player",
                new HexCoord(2, 4)),
            context);

        Assert.Equal(new HexCoord(0, 4), salvo.CurrentCoordinate);
        Assert.Equal(4, result.DistanceTraveledThisPhase);
        Assert.Equal(GuidedMissileStatus.Intercepted, result.Status);
    }

    [Fact]
    public void WaitingNoRouteMissileCanBeInterceptedAtItsCurrentCoordinate()
    {
        SystemMap map = CreateMap(4);
        var target = new HexCoord(1, 0);
        EncloseTarget(map, target);
        var launch = new HexCoord(-3, 3);
        GuidedMissileSalvo salvo = CreateSalvo(
            "hostile",
            TacticalSide.Enemy,
            launch,
            range: 9,
            speed: 2);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            launch,
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Intercepted,
            MissileDefenseSourceType.HeldDirectFireWeapon);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current("ship-player", target),
            context);

        Assert.Equal(0, result.DistanceTraveledThisPhase);
        Assert.Equal(GuidedMissileStatus.Intercepted, result.Status);
        Assert.Equal(9, salvo.RemainingRange);
    }

    [Fact]
    public void FriendlyMissileIsIgnoredByFriendlyDefenseDuringMovement()
    {
        SystemMap map = CreateMap(6);
        GuidedMissileSalvo salvo = CreateSalvo(
            "friendly",
            TacticalSide.Player,
            new HexCoord(-3, 3),
            range: 10,
            speed: 2);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(-1, 3),
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Intercepted);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-enemy",
                new HexCoord(2, 3)),
            context);

        Assert.Empty(result.InterceptionAttempts);
        Assert.Equal(GuidedMissileStatus.InFlight, result.Status);
    }

    [Fact]
    public void RangeSpentBeforeInterceptionRemainsSpent()
    {
        SystemMap map = CreateMap(7);
        GuidedMissileSalvo salvo = CreateSalvo(
            "hostile",
            TacticalSide.Enemy,
            new HexCoord(-3, 3),
            range: 10,
            speed: 4);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(-1, 3),
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Intercepted,
            MissileDefenseSourceType.HeldDirectFireWeapon);

        MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(
                "ship-player",
                new HexCoord(2, 3)),
            context);

        Assert.Equal(2, salvo.DistanceTraveled);
        Assert.Equal(8, salvo.RemainingRange);
        Assert.Equal(3, salvo.TravelHistory.Count);
    }

    [Fact]
    public void SharedAttemptBudgetAllowsOnlyFirstOfTwoSalvosAnAttempt()
    {
        SystemMap map = CreateMap(6);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(0, 3),
            range: 1,
            attempts: 1,
            MissileInterceptionOutcome.Missed,
            MissileDefenseSourceType.HeldDirectFireWeapon);
        GuidedMissileSalvo first = CreateSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            new HexCoord(-2, 3),
            range: 8,
            speed: 2);
        GuidedMissileSalvo second = CreateSalvo(
            "hostile-2",
            TacticalSide.Enemy,
            new HexCoord(-2, 3),
            range: 8,
            speed: 2);

        GuidedMissileAdvanceResult firstResult =
            MissileGuidanceService.AdvanceOnePhase(
                map,
                first,
                MissileTargetTrackSnapshot.Current(
                    "ship-player",
                    new HexCoord(2, 3)),
                context);
        GuidedMissileAdvanceResult secondResult =
            MissileGuidanceService.AdvanceOnePhase(
                map,
                second,
                MissileTargetTrackSnapshot.Current(
                    "ship-player",
                    new HexCoord(2, 3)),
                context);

        Assert.Single(firstResult.InterceptionAttempts);
        Assert.Empty(secondResult.InterceptionAttempts);
    }

    [Fact]
    public void LaunchServiceRecordsOwnershipAndAppliesInterception()
    {
        SystemMap map = CreateMap(5);
        MissileInterceptionPhaseContext context = CreateContext(
            TacticalSide.Player,
            new HexCoord(0, 2),
            range: 0,
            attempts: 1,
            MissileInterceptionOutcome.Intercepted);

        GuidedMissileLaunchResult launch =
            MissileLaunchService.LaunchAndAdvanceOnePhase(
                map,
                "hostile-launch",
                TacticalSide.Enemy,
                "ship-enemy",
                "ship-player",
                new HexCoord(-2, 2),
                new MissileFlightProfile(2, 6, 2),
                MissileTargetTrackSnapshot.Current(
                    "ship-player",
                    new HexCoord(0, 2)),
                context);

        Assert.Equal(TacticalSide.Enemy, launch.Salvo.OwnerSide);
        Assert.Equal(GuidedMissileStatus.Intercepted, launch.Salvo.Status);
        Assert.True(launch.AdvanceResult.WasIntercepted);
    }

    private static MissileInterceptionPhaseContext CreateContext(
        TacticalSide defenseSide,
        HexCoord defenseCoordinate,
        int range,
        int attempts,
        MissileInterceptionOutcome outcome,
        MissileDefenseSourceType sourceType =
            MissileDefenseSourceType.PointDefenseSystem)
    {
        var defense = new MissileDefenseSystem(
            "point-defense",
            defenseSide == TacticalSide.Player ? "ship-player" : "ship-enemy",
            defenseSide,
            defenseCoordinate,
            new MissileDefenseProfile(2, range, attempts),
            sourceType: sourceType);
        return new MissileInterceptionPhaseContext(
            new[] { defense },
            new FixedMissileInterceptionResolver(outcome));
    }

    private static GuidedMissileSalvo CreateSalvo(
        string id,
        TacticalSide side,
        HexCoord launch,
        int range,
        int speed) =>
        new(
            id,
            side,
            side == TacticalSide.Player ? "ship-player" : "ship-enemy",
            side == TacticalSide.Player ? "ship-enemy" : "ship-player",
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
                MapObject.CreatePlanet($"wall-{index}", $"Wall {index}"),
                neighbor);
            index++;
        }
    }
}
