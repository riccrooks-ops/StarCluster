using StarCluster.Core.Combat.DirectFire;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class Tl1ScriptedRangeControlTests
{
    private static int CriticalMissRoll() => 1;
    private static int CriticalHitRoll() => 100;

    [Fact]
    public void Range_schedule_applies_changes_at_the_start_of_the_named_turn()
    {
        var schedule = new Tl1RelativeRangeSchedule(
            2,
            6,
            new[]
            {
                new Tl1RelativeRangeChange(2, 4),
                new Tl1RelativeRangeChange(5, 3),
            });
        int range = 2;

        Assert.False(schedule.TryApplyTurn(1, ref range, out int turnOneDelta));
        Assert.Equal(0, turnOneDelta);
        Assert.True(schedule.TryApplyTurn(2, ref range, out int turnTwoDelta));
        Assert.Equal(2, turnTwoDelta);
        Assert.Equal(4, range);
        Assert.True(schedule.TryApplyTurn(5, ref range, out int turnFiveDelta));
        Assert.Equal(-1, turnFiveDelta);
        Assert.Equal(3, range);
    }

    [Fact]
    public void Range_schedule_rejects_separation_beyond_the_eleven_hex_board()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new Tl1RelativeRangeSchedule(
                2,
                4,
                new[] { new Tl1RelativeRangeChange(2, 11) }));
    }

    [Fact]
    public void Range_schedule_requires_strictly_ordered_unique_turns()
    {
        Assert.Throws<ArgumentException>(() =>
            new Tl1RelativeRangeSchedule(
                2,
                6,
                new[]
                {
                    new Tl1RelativeRangeChange(4, 5),
                    new Tl1RelativeRangeChange(3, 4),
                }));
    }

    [Fact]
    public void Outward_step_reroutes_live_missile_and_preserves_spent_range()
    {
        Tl1WeaponMatrixSideProfile missile = Side("missile") with
        {
            Ammunition = 1,
            MissileSpeed = 1,
            MissileRange = 3,
            MissileGuidance = 95,
        };
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
            MatrixProfile(
                missile,
                Side("kinetic") with { Ammunition = 0 },
                2,
                3,
                new[] { new Tl1RelativeRangeChange(2, 4) }))
            .Run(CriticalHitRoll, CriticalMissRoll);

        Assert.Equal(1, result.RangeChangesApplied);
        Assert.Equal(1, result.MissileReroutesA);
        Assert.Equal(1, result.RangeExhaustedA);
        Assert.Equal(0, result.MissileHitsA);
        Assert.Equal(4, result.FinalRangeHexes);
    }

    [Fact]
    public void Inward_step_can_advance_an_existing_flight_arrival()
    {
        Tl1WeaponMatrixSideProfile missile = Side("missile") with
        {
            Ammunition = 1,
            MissileSpeed = 1,
            MissileRange = 4,
            MissileGuidance = 95,
        };
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
            MatrixProfile(
                missile,
                Side("kinetic") with { Ammunition = 0 },
                4,
                2,
                new[] { new Tl1RelativeRangeChange(2, 2) }))
            .Run(CriticalHitRoll, CriticalMissRoll);

        Assert.Equal(1, result.MissileReroutesA);
        Assert.Equal(1, result.MissileHitsA);
        Assert.Equal(0, result.RangeExhaustedA);
        Assert.Equal(2, result.FinalRangeHexes);
    }

    [Fact]
    public void Sensor_track_is_recomputed_after_the_scripted_range_change()
    {
        Tl1WeaponMatrixSideProfile passive = Side("kinetic") with
        {
            Ammunition = 0,
            SensorTrackGateEnabled = true,
            PassiveFirmRange = 3,
        };
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
            MatrixProfile(
                passive,
                passive,
                2,
                3,
                new[] { new Tl1RelativeRangeChange(2, 4) }))
            .Run(CriticalMissRoll, CriticalMissRoll);

        Assert.Equal(1, result.FirmTrackTurnsA);
        Assert.Equal(2, result.TrackDeniedTurnsA);
        Assert.Equal(1, result.FirmTrackTurnsB);
        Assert.Equal(2, result.TrackDeniedTurnsB);
    }

    [Fact]
    public void Delayed_arrival_still_resolves_held_main_before_pds()
    {
        Tl1PowerEnvelopeSideProfile defender = PowerSide("kinetic") with
        {
            HeldInterception = true,
            PdsFamily = "kinetic",
            PdsPowerCost = 1,
            PdsReactionCapacity = 1,
            PdsInterceptionChance = 100,
            PdsAmmunition = 4,
        };
        Tl1PowerEnvelopeSideProfile attacker = PowerSide("missile") with
        {
            Ammunition = 1,
            MissileSpeed = 1,
            MissileRange = 5,
            MissileGuidance = 95,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            PowerProfile(
                defender,
                attacker,
                2,
                4,
                new[] { new Tl1RelativeRangeChange(2, 4) }))
            .Run(
                CriticalMissRoll,
                CriticalHitRoll,
                nextPdsRollA: CriticalHitRoll,
                nextHeldRollA: CriticalHitRoll);

        Assert.Equal(1, result.RangeChangesApplied);
        Assert.Equal(1, result.MissileReroutesB);
        Assert.Equal(1, result.HeldAttemptsA);
        Assert.Equal(1, result.HeldInterceptsA);
        Assert.Equal(0, result.PdsAttemptsA);
        Assert.True(result.HeldUnusedA >= 1);
    }

    [Fact]
    public void Pds_follows_a_held_miss_after_delayed_arrival()
    {
        Tl1PowerEnvelopeSideProfile defender = PowerSide("kinetic") with
        {
            HeldInterception = true,
            PdsFamily = "kinetic",
            PdsPowerCost = 1,
            PdsReactionCapacity = 1,
            PdsInterceptionChance = 100,
            PdsAmmunition = 4,
        };
        Tl1PowerEnvelopeSideProfile attacker = PowerSide("missile") with
        {
            Ammunition = 1,
            MissileSpeed = 1,
            MissileRange = 5,
            MissileGuidance = 95,
        };
        Tl1PowerEnvelopeResult result = new Tl1PowerEnvelopeSimulator(
            PowerProfile(
                defender,
                attacker,
                2,
                4,
                new[] { new Tl1RelativeRangeChange(2, 4) }))
            .Run(
                CriticalMissRoll,
                CriticalHitRoll,
                nextPdsRollA: CriticalHitRoll,
                nextHeldRollA: CriticalMissRoll);

        Assert.Equal(1, result.HeldAttemptsA);
        Assert.Equal(0, result.HeldInterceptsA);
        Assert.Equal(1, result.PdsAttemptsA);
        Assert.Equal(1, result.PdsInterceptsA);
    }

    [Fact]
    public void Faster_target_exhausts_a_slower_missile_under_scalar_pursuit()
    {
        Tl1WeaponMatrixSideProfile missile = Side("missile") with
        {
            Ammunition = 1,
            MissileSpeed = 1,
            MissileRange = 6,
            TargetMovePerTurn = 2,
        };
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
            MatrixProfile(
                missile,
                Side("kinetic") with { Ammunition = 0 },
                2,
                8,
                Array.Empty<Tl1RelativeRangeChange>()))
            .Run(CriticalHitRoll, CriticalMissRoll);

        Assert.Equal(1, result.RangeExhaustedA);
        Assert.Equal(0, result.MissileHitsA);
    }

    private static Tl1WeaponMatrixSideProfile Side(string family) => new(
        family,
        "standard",
        20,
        10,
        false,
        5,
        100,
        55,
        2,
        1,
        2,
        1,
        6);

    private static Tl1WeaponMatrixProfile MatrixProfile(
        Tl1WeaponMatrixSideProfile a,
        Tl1WeaponMatrixSideProfile b,
        int range,
        int turnCap,
        IReadOnlyList<Tl1RelativeRangeChange> schedule) => new(
        4,
        0,
        1,
        0,
        8,
        30,
        range,
        5,
        turnCap,
        a,
        b,
        schedule);

    private static Tl1PowerEnvelopeSideProfile PowerSide(string family) => new()
    {
        Family = family,
        Doctrine = "standard",
        Accuracy = 20,
        ComputerBonus = 10,
        ReactorOutput = 5,
        Ammunition = family == "missile" ? 8 : 100,
        MissileGuidance = 55,
        MissileDamage = 2,
        MissileShieldPenetration = 1,
        MissileArmorPenetration = 2,
        MissileSpeed = 1,
        MissileRange = 6,
        MissileLaunchesPerTurn = 1,
    };

    private static Tl1PowerEnvelopeProfile PowerProfile(
        Tl1PowerEnvelopeSideProfile a,
        Tl1PowerEnvelopeSideProfile b,
        int range,
        int turnCap,
        IReadOnlyList<Tl1RelativeRangeChange> schedule) => new()
    {
        ShieldCapacity = 4,
        BaseShieldRecharge = 1,
        ArmorIntegrity = 8,
        Hull = 30,
        RangeHexes = range,
        RangePenaltyPerHex = 5,
        TurnCap = turnCap,
        RangeSchedule = schedule,
        SideA = a,
        SideB = b,
    };
}
