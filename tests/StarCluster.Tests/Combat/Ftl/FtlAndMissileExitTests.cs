using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Ftl;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Ftl;

public sealed class FtlAndMissileExitTests
{
    [Fact]
    public void Regular_jump_requires_legal_outer_ring_hex()
    {
        HexMap map = HexMap.CreateHexagon(5);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        Assert.Throws<InvalidOperationException>(() => FtlJumpService.Declare(
            FtlJumpType.Regular,
            map,
            HexCoord.Zero,
            Array.Empty<HexCoord>(),
            knowinglyEngaged: false,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: power,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>()));
    }

    [Fact]
    public void Perimeter_hex_adjacent_to_celestial_body_is_gravity_restricted()
    {
        HexMap map = HexMap.CreateHexagon(5);
        var body = new HexCoord(4, 0);
        var restricted = new HexCoord(5, 0);

        Assert.True(JumpPerimeterService.IsGravityRestricted(
            map,
            restricted,
            new[] { body }));
        Assert.False(JumpPerimeterService.IsLegalRegularJumpHex(
            map,
            restricted,
            new[] { body }));
        IReadOnlyList<HexCoord> legal = JumpPerimeterService.LegalRegularJumpHexes(
            map,
            new[] { body });
        Assert.DoesNotContain(restricted, legal);
        Assert.All(legal, coordinate => Assert.True(map.IsBoundary(coordinate)));
    }

    [Fact]
    public void Emergency_jump_ignores_perimeter_and_gravity_location_rule()
    {
        HexMap map = HexMap.CreateHexagon(5);
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        PoweredFtlJump jump = FtlJumpService.Declare(
            FtlJumpType.Emergency,
            map,
            HexCoord.Zero,
            new[] { HexCoord.Zero },
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: power,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>());

        Assert.Equal(5, jump.Declaration.DedicatedTacticalPower);
        Assert.Equal(5, power.PoweredPower);
    }

    [Fact]
    public void Ftl_power_up_is_public_but_non_positional()
    {
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        PoweredFtlJump jump = FtlJumpService.Declare(
            FtlJumpType.Regular,
            HexMap.CreateHexagon(5),
            new HexCoord(5, 0),
            Array.Empty<HexCoord>(),
            knowinglyEngaged: false,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: power,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>());

        Assert.True(jump.Declaration.Signature.DetectedByEveryoneOnMap);
        Assert.False(jump.Declaration.Signature.RevealsLocation);
        Assert.False(jump.Declaration.Signature.RevealsIdentity);
        Assert.False(jump.Declaration.Signature.RevealsDestination);
        Assert.False(jump.Declaration.Signature.RevealsJumpType);
    }

    [Fact]
    public void Hidden_hostile_does_not_prevent_regular_jump_declaration()
    {
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        PoweredFtlJump jump = FtlJumpService.Declare(
            FtlJumpType.Regular,
            HexMap.CreateHexagon(5),
            new HexCoord(5, 0),
            Array.Empty<HexCoord>(),
            knowinglyEngaged: false,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: power,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>());

        Assert.True(jump.Declaration.ExecutesAtNextTurnRefresh);
    }

    [Fact]
    public void Known_engagement_requires_emergency_jump()
    {
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        Assert.Throws<InvalidOperationException>(() => FtlJumpService.Declare(
            FtlJumpType.Regular,
            HexMap.CreateHexagon(5),
            new HexCoord(5, 0),
            Array.Empty<HexCoord>(),
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: power,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>()));
    }

    [Fact]
    public void Disabled_ftl_emergency_egress_is_player_only()
    {
        var playerPower = new TacticalPowerLedger();
        playerPower.BeginTurn(1);
        PoweredFtlJump player = FtlJumpService.Declare(
            FtlJumpType.Emergency,
            HexMap.CreateHexagon(5),
            HexCoord.Zero,
            Array.Empty<HexCoord>(),
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Disabled,
            isPlayerShip: true,
            power: playerPower,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>());
        Assert.NotNull(player);

        var npcPower = new TacticalPowerLedger();
        npcPower.BeginTurn(1);
        Assert.Throws<InvalidOperationException>(() => FtlJumpService.Declare(
            FtlJumpType.Emergency,
            HexMap.CreateHexagon(5),
            HexCoord.Zero,
            Array.Empty<HexCoord>(),
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Disabled,
            isPlayerShip: false,
            power: npcPower,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>()));
    }

    [Fact]
    public void Once_powered_only_ship_or_ftl_destruction_stops_jump()
    {
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);
        PoweredFtlJump jump = FtlJumpService.Declare(
            FtlJumpType.Emergency,
            HexMap.CreateHexagon(5),
            HexCoord.Zero,
            Array.Empty<HexCoord>(),
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: power,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>());

        Assert.True(jump.Execute(
            shipDestroyed: false,
            ftlCondition: ComponentCondition.Disabled));

        var destroyedDrivePower = new TacticalPowerLedger();
        destroyedDrivePower.BeginTurn(5);
        PoweredFtlJump destroyedDriveJump = FtlJumpService.Declare(
            FtlJumpType.Emergency,
            HexMap.CreateHexagon(5),
            HexCoord.Zero,
            Array.Empty<HexCoord>(),
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: destroyedDrivePower,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>());
        Assert.False(destroyedDriveJump.Execute(
            shipDestroyed: false,
            ftlCondition: ComponentCondition.Destroyed));

        var destroyedShipPower = new TacticalPowerLedger();
        destroyedShipPower.BeginTurn(5);
        PoweredFtlJump destroyedShipJump = FtlJumpService.Declare(
            FtlJumpType.Emergency,
            HexMap.CreateHexagon(5),
            HexCoord.Zero,
            Array.Empty<HexCoord>(),
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: destroyedShipPower,
            outboundMissiles: Array.Empty<GuidedMissileSalvo>());
        Assert.False(destroyedShipJump.Execute(
            shipDestroyed: true,
            ftlCondition: ComponentCondition.Operational));
    }

    [Fact]
    public void Ftl_declaration_self_destructs_all_outbound_missiles_immediately()
    {
        GuidedMissileSalvo command = Missile("command");
        GuidedMissileSalvo autonomous = Missile("autonomous");
        var power = new TacticalPowerLedger();
        power.BeginTurn(5);

        PoweredFtlJump jump = FtlJumpService.Declare(
            FtlJumpType.Emergency,
            HexMap.CreateHexagon(5),
            HexCoord.Zero,
            Array.Empty<HexCoord>(),
            knowinglyEngaged: true,
            ftlCondition: ComponentCondition.Operational,
            isPlayerShip: true,
            power: power,
            outboundMissiles: new[] { command, autonomous });

        Assert.Equal(2, jump.Declaration.OutboundMissileFlightsSelfDestructed);
        Assert.Equal(GuidedMissileStatus.SelfDestructed, command.Status);
        Assert.Equal(GuidedMissileStatus.SelfDestructed, autonomous.Status);

        GuidedMissileSalvo inbound = Missile("inbound");
        Assert.Equal(1,
            MissileFlightTerminationService.RemoveInboundAfterSuccessfulDeparture(
                new[] { inbound }));
        Assert.Equal(GuidedMissileStatus.SelfDestructed, inbound.Status);
    }

    [Fact]
    public void Datalink_requires_comms_and_at_least_one_functioning_launcher()
    {
        MissileDatalinkAvailability active =
            MissileFlightTerminationService.EvaluateDatalink(
                ComponentCondition.Degraded,
                new[] { ComponentCondition.Disabled, ComponentCondition.Degraded });
        MissileDatalinkAvailability down =
            MissileFlightTerminationService.EvaluateDatalink(
                ComponentCondition.Disabled,
                new[] { ComponentCondition.Operational });

        Assert.True(active.Active);
        Assert.Equal(1, active.FunctioningLauncherCount);
        Assert.False(down.Active);
    }

    [Fact]
    public void Voluntary_self_destruct_requires_los_track_and_datalink()
    {
        GuidedMissileSalvo missile = Missile("voluntary");

        Assert.False(MissileFlightTerminationService.TryVoluntarySelfDestruct(
            missile,
            hasLineOfSight: true,
            hasCurrentTrackOnFlight: false,
            hasActiveDatalink: true,
            terminalAttackCommitted: false));
        Assert.True(MissileFlightTerminationService.TryVoluntarySelfDestruct(
            missile,
            hasLineOfSight: true,
            hasCurrentTrackOnFlight: true,
            hasActiveDatalink: true,
            terminalAttackCommitted: false));
    }

    [Fact]
    public void Destroyed_launcher_ship_terminates_command_but_not_autonomous_flights()
    {
        GuidedMissileSalvo command = Missile("command");
        GuidedMissileSalvo autonomous = Missile("autonomous");
        GuidedMissileSalvo hybridFallback = Missile("hybrid-fallback");
        GuidedMissileSalvo hybridNoFallback = Missile("hybrid-no-fallback");

        int terminated = MissileFlightTerminationService.ResolveLaunchingShipDestroyed(
            new[]
            {
                (command, MissileGuidanceDependency.CommandGuided),
                (autonomous, MissileGuidanceDependency.Autonomous),
                (hybridFallback, MissileGuidanceDependency.HybridWithAutonomousFallback),
                (hybridNoFallback, MissileGuidanceDependency.HybridWithoutAutonomousFallback),
            });

        Assert.Equal(2, terminated);
        Assert.Equal(GuidedMissileStatus.SelfDestructed, command.Status);
        Assert.Equal(GuidedMissileStatus.SelfDestructed, hybridNoFallback.Status);
        Assert.False(autonomous.IsTerminal);
        Assert.False(hybridFallback.IsTerminal);
    }

    private static GuidedMissileSalvo Missile(string id) => new(
        id,
        TacticalSide.Player,
        "launcher",
        "target",
        HexCoord.Zero,
        new MissileFlightProfile(1, 8, 2));
}
