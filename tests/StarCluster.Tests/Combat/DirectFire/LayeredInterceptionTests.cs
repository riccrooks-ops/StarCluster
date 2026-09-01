using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class LayeredInterceptionTests
{
    [Fact]
    public void SpecificHeldOrderIgnoresDifferentHostileSalvo()
    {
        MissileDefenseSystem held = CreateSpecificHeld("hostile-1");
        var context = new MissileInterceptionPhaseContext(
            new[] { held },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Intercepted),
            CreateMap());

        IReadOnlyList<MissileInterceptionAttemptResult> results =
            context.ResolveAt(
                CreateSalvo("hostile-2"),
                new HexCoord(-1, 0),
                false);

        Assert.Empty(results);
        Assert.Equal(0, context.AttemptsUsed("held-main"));
    }

    [Fact]
    public void SpecificHeldOrderEngagesNamedHostileSalvo()
    {
        MissileDefenseSystem held = CreateSpecificHeld("hostile-1");
        var context = new MissileInterceptionPhaseContext(
            new[] { held },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Missed),
            CreateMap());

        MissileInterceptionAttemptResult result = Assert.Single(
            context.ResolveAt(
                CreateSalvo("hostile-1"),
                new HexCoord(-1, 0),
                false));

        Assert.Equal("held-main", result.DefenseSystemId);
    }

    [Fact]
    public void HoldForAnyEngagesFirstEligibleHostileSalvoOnly()
    {
        MissileDefenseSystem held = CreateAnyHeld();
        var context = new MissileInterceptionPhaseContext(
            new[] { held },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Missed),
            CreateMap());

        Assert.Single(context.ResolveAt(
            CreateSalvo("hostile-1"),
            new HexCoord(-1, 0),
            false));
        Assert.Empty(context.ResolveAt(
            CreateSalvo("hostile-2"),
            new HexCoord(-1, 0),
            false));
    }

    [Fact]
    public void MissedHeldWeaponLeavesPointDefenseForTerminalWindows()
    {
        MissileDefenseSystem held = CreateAnyHeld();
        MissileDefenseSystem pointDefense = CreatePointDefense(priority: 10);
        var context = new MissileInterceptionPhaseContext(
            new[] { pointDefense, held },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Missed),
            CreateMap());

        GuidedMissileSalvo salvo = CreateSalvo("hostile");
        MissileInterceptionAttemptResult transit = Assert.Single(
            context.ResolveAt(
                salvo,
                new HexCoord(-1, 0),
                MissileInterceptionOpportunity.Transit));
        MissileInterceptionAttemptResult terminalEntry = Assert.Single(
            context.ResolveAt(
                salvo,
                new HexCoord(-2, 0),
                MissileInterceptionOpportunity.TerminalEntry));

        Assert.Equal("held-main", transit.DefenseSystemId);
        Assert.Equal("player-pds", terminalEntry.DefenseSystemId);
    }

    [Fact]
    public void SuccessfulHeldWeaponPreventsRedundantPointDefenseShot()
    {
        MissileDefenseSystem held = CreateAnyHeld();
        MissileDefenseSystem pointDefense = CreatePointDefense(priority: 10);
        var context = new MissileInterceptionPhaseContext(
            new[] { held, pointDefense },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Intercepted),
            CreateMap());

        IReadOnlyList<MissileInterceptionAttemptResult> results =
            context.ResolveAt(
                CreateSalvo("hostile"),
                new HexCoord(-1, 0),
                false);

        MissileInterceptionAttemptResult result = Assert.Single(results);
        Assert.Equal("held-main", result.DefenseSystemId);
        Assert.Equal(0, context.AttemptsUsed("player-pds"));
    }

    [Fact]
    public void PointDefenseOperatesWithoutHeldMainWeapon()
    {
        MissileDefenseSystem pointDefense = CreatePointDefense(priority: 0);
        var context = new MissileInterceptionPhaseContext(
            new[] { pointDefense },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Intercepted));

        MissileInterceptionAttemptResult result = Assert.Single(
            context.ResolveAt(
                CreateSalvo("hostile"),
                new HexCoord(-2, 0),
                MissileInterceptionOpportunity.TerminalEntry));

        Assert.Equal(
            MissileDefenseSourceType.PointDefenseSystem,
            result.Attempt.DefenseSystem.SourceType);
    }

    [Fact]
    public void HeldLineOfSightDefenseRequiresMapContext()
    {
        MissileDefenseSystem held = CreateAnyHeld();

        Assert.Throws<ArgumentException>(() =>
            new MissileInterceptionPhaseContext(
                new[] { held },
                new FixedMissileInterceptionResolver(
                    MissileInterceptionOutcome.Missed)));
    }

    [Fact]
    public void StarBlocksHeldWeaponAndPointDefenseWaitsForTerminalEntry()
    {
        SystemMap map = CreateMap();
        MissileDefenseSystem held = CreateAnyHeld();
        MissileDefenseSystem pointDefense = new(
            "player-pds",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new MissileDefenseProfile(2, 4, 1),
            priority: 10,
            sourceType: MissileDefenseSourceType.PointDefenseSystem);
        var context = new MissileInterceptionPhaseContext(
            new[] { held, pointDefense },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Missed),
            map);

        GuidedMissileSalvo salvo = CreateSalvo("hostile");
        Assert.Empty(context.ResolveAt(
            salvo,
            new HexCoord(2, 0),
            MissileInterceptionOpportunity.Transit));

        MissileInterceptionAttemptResult result = Assert.Single(
            context.ResolveAt(
                salvo,
                new HexCoord(-2, 0),
                MissileInterceptionOpportunity.TerminalEntry));

        Assert.Equal("player-pds", result.DefenseSystemId);
        Assert.Equal(0, context.AttemptsUsed("held-main"));
    }

    private static MissileDefenseSystem CreateSpecificHeld(string salvoId) =>
        DirectFireOrder.InterceptSpecificMissile(
            "order",
            "main-weapon",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new DirectFireWeaponProfile(3, 4),
            salvoId)
        .CreateHeldDefenseSystem("held-main", priority: 0);

    private static MissileDefenseSystem CreateAnyHeld() =>
        DirectFireOrder.HoldForAnyMissile(
            "order",
            "main-weapon",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new DirectFireWeaponProfile(3, 4))
        .CreateHeldDefenseSystem("held-main", priority: 0);

    private static MissileDefenseSystem CreatePointDefense(int priority) =>
        new(
            "player-pds",
            "ship-player",
            TacticalSide.Player,
            new HexCoord(-2, 0),
            new MissileDefenseProfile(2, 1, 1),
            priority,
            MissileDefenseSourceType.PointDefenseSystem);

    private static GuidedMissileSalvo CreateSalvo(string id) =>
        new(
            id,
            TacticalSide.Enemy,
            "ship-enemy",
            "ship-player",
            new HexCoord(2, 0),
            new MissileFlightProfile(2, 10, 2));

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            5,
            MapObject.CreateStar("star", "Primary Star"));
}
