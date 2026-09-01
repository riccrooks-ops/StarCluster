using StarCluster.Core.Combat.DirectFire;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class Tl1PdsCalibrationTests
{
    private static Tl1WeaponMatrixSideProfile Side(
        string family,
        string pdsFamily = "none",
        int reactorOutput = 5,
        int pdsPowerCost = 0,
        int pdsReactionCapacity = 0,
        int pdsChance = 0,
        int pdsAmmunition = 0,
        bool pdsUnlimitedAmmunition = false,
        int missileLaunchesPerTurn = 1,
        bool evasive = false,
        int computerBonus = 10,
        int missileGuidance = 55,
        int missileDamage = 5) =>
        new(
            family,
            "standard",
            family == "energy" ? 25 : family == "kinetic" ? 20 : 0,
            computerBonus,
            evasive,
            reactorOutput,
            family == "missile" ? 25 : family == "energy" ? 0 : 100,
            missileGuidance,
            missileDamage,
            1,
            2,
            1,
            6,
            0,
            missileLaunchesPerTurn,
            pdsFamily,
            pdsPowerCost,
            pdsReactionCapacity,
            pdsChance,
            pdsAmmunition,
            pdsUnlimitedAmmunition);

    private static Tl1WeaponMatrixProfile Profile(
        Tl1WeaponMatrixSideProfile a,
        Tl1WeaponMatrixSideProfile b,
        int range = 0,
        int turnCap = 1) =>
        new(2, 0, 1, 0, 4, 12, range, 5, turnCap, a, b);

    private static Tl1WeaponMatrixSideProfile KineticPds(
        int chance = 35,
        int reactions = 1,
        int ammunition = 50,
        int reactorOutput = 5,
        bool evasive = false,
        int computerBonus = 10) =>
        Side(
            "kinetic",
            "kinetic",
            reactorOutput,
            1,
            reactions,
            chance,
            ammunition,
            false,
            1,
            evasive,
            computerBonus);

    [Fact]
    public void Pds_readiness_locks_power_before_weapon_commitment()
    {
        Tl1WeaponMatrixSideProfile defender = Side(
            "energy",
            "energy",
            reactorOutput: 3,
            pdsPowerCost: 2,
            pdsReactionCapacity: 1,
            pdsChance: 40,
            pdsUnlimitedAmmunition: true);
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(defender, Side("kinetic")))
            .Run(() => 100, () => 1);

        Assert.Equal(2, result.PdsPowerCommittedA);
        Assert.Equal(0, result.ShotsA);
    }

    [Fact]
    public void Kinetic_pds_consumes_and_reloads_one_ready_package_on_a_miss()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 0, computerBonus: 0),
                    Side("missile")))
            .Run(() => 1, () => 1, () => 100, () => 100);

        Assert.Equal(1, result.PdsAttemptsA);
        Assert.Equal(0, result.PdsInterceptsA);
        Assert.Equal(49, result.PdsAmmunitionA);
        Assert.Equal(1, result.PdsReadyAmmunitionA);
        Assert.Equal(48, result.PdsReserveAmmunitionA);
    }

    [Fact]
    public void Kinetic_pds_consumes_and_reloads_one_ready_package_on_an_intercept()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(KineticPds(chance: 100), Side("missile")))
            .Run(() => 1, () => 100, () => 1, () => 1);

        Assert.Equal(1, result.PdsAttemptsA);
        Assert.Equal(1, result.PdsInterceptsA);
        Assert.Equal(49, result.PdsAmmunitionA);
        Assert.Equal(1, result.PdsReadyAmmunitionA);
        Assert.Equal(48, result.PdsReserveAmmunitionA);
        Assert.Equal(0, result.MissilesReachedGuidanceB);
    }

    [Fact]
    public void Energy_pds_uses_no_conventional_ammunition()
    {
        Tl1WeaponMatrixSideProfile defender = Side(
            "kinetic",
            "energy",
            pdsPowerCost: 2,
            pdsReactionCapacity: 1,
            pdsChance: 100,
            pdsUnlimitedAmmunition: true);
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(defender, Side("missile")))
            .Run(() => 1, () => 100, () => 1, () => 1);

        Assert.Equal(1, result.PdsAttemptsA);
        Assert.Equal(1, result.PdsInterceptsA);
        Assert.Equal(0, result.PdsAmmunitionA);
        Assert.Equal(0, result.PdsReadyAmmunitionA);
        Assert.Equal(0, result.PdsReserveAmmunitionA);
    }

    [Fact]
    public void Reaction_capacity_one_allows_one_attempt_against_saturation()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 0, reactions: 1, computerBonus: 0),
                    Side("missile", missileLaunchesPerTurn: 2)))
            .Run(() => 1, () => 1, () => 100, () => 100);

        Assert.Equal(1, result.PdsAttemptsA);
        Assert.Equal(1, result.PdsEntryAttemptsA);
        Assert.Equal(0, result.PdsPreAttackAttemptsA);
        Assert.Equal(2, result.MissilesReachedGuidanceB);
    }

    [Fact]
    public void Reaction_capacity_two_exposes_the_second_terminal_window()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 0, reactions: 2, computerBonus: 0),
                    Side("missile")))
            .Run(() => 1, () => 1, () => 100, () => 100);

        Assert.Equal(2, result.PdsAttemptsA);
        Assert.Equal(1, result.PdsEntryAttemptsA);
        Assert.Equal(1, result.PdsPreAttackAttemptsA);
        Assert.Equal(1, result.MissilesReachedGuidanceB);
    }

    [Fact]
    public void Entry_intercept_prevents_guidance_and_damage()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 100),
                    Side("missile", missileGuidance: 100, missileDamage: 20)))
            .Run(() => 1, () => 100, () => 1, () => 1);

        Assert.Equal(1, result.PdsInterceptsA);
        Assert.Equal(0, result.MissilesReachedGuidanceB);
        Assert.Equal(0, result.MissileHitsB);
        Assert.Equal(12, result.SideA.Defense.CurrentHull);
    }

    [Fact]
    public void Unpowered_pds_does_not_attempt_interception()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 100, reactorOutput: 0),
                    Side("missile", missileGuidance: 100)))
            .Run(() => 1, () => 100, () => 1, () => 1);

        Assert.Equal(0, result.PdsPowerCommittedA);
        Assert.Equal(0, result.PdsAttemptsA);
        Assert.Equal(1, result.MissilesReachedGuidanceB);
    }

    [Fact]
    public void Pds_retains_its_local_base_chance_without_targeting_computer()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 35, computerBonus: 0),
                    Side("missile")))
            .Run(() => 1, () => 100, () => 35, () => 1);

        Assert.Equal(1, result.PdsInterceptsA);
    }

    [Fact]
    public void Operational_targeting_computer_assists_pds_by_ten_points()
    {
        Tl1WeaponMatrixResult assisted = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 35, computerBonus: 10),
                    Side("missile")))
            .Run(() => 1, () => 100, () => 45, () => 1);
        Tl1WeaponMatrixResult localOnly = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 35, computerBonus: 0),
                    Side("missile")))
            .Run(() => 1, () => 100, () => 45, () => 1);

        Assert.Equal(1, assisted.PdsInterceptsA);
        Assert.Equal(0, localOnly.PdsInterceptsA);
    }

    [Fact]
    public void Degraded_targeting_computer_assists_pds_by_five_points()
    {
        Tl1WeaponMatrixResult assisted = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 35, computerBonus: 5),
                    Side("missile")))
            .Run(() => 1, () => 100, () => 40, () => 1);
        Tl1WeaponMatrixResult localOnly = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(chance: 35, computerBonus: 0),
                    Side("missile")))
            .Run(() => 1, () => 100, () => 40, () => 1);

        Assert.Equal(1, assisted.PdsInterceptsA);
        Assert.Equal(0, localOnly.PdsInterceptsA);
    }

    [Fact]
    public void Own_evm_reduces_ship_mounted_pds_chance_by_five_points()
    {
        Tl1WeaponMatrixResult evasive = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(
                        chance: 35,
                        evasive: true,
                        computerBonus: 10),
                    Side("missile")))
            .Run(() => 1, () => 1, () => 41, () => 1);
        Tl1WeaponMatrixResult steady = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(
                        chance: 35,
                        evasive: false,
                        computerBonus: 10),
                    Side("missile")))
            .Run(() => 1, () => 1, () => 41, () => 1);

        Assert.Equal(0, evasive.PdsInterceptsA);
        Assert.Equal(1, steady.PdsInterceptsA);
    }

    [Fact]
    public void Own_evm_does_not_reduce_amm_interception_chance()
    {
        Tl1WeaponMatrixSideProfile amm = Side(
            "kinetic",
            "amm",
            pdsPowerCost: 1,
            pdsReactionCapacity: 1,
            pdsChance: 50,
            pdsAmmunition: 25,
            evasive: true,
            computerBonus: 0);
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(amm, Side("missile")))
            .Run(() => 1, () => 100, () => 50, () => 1);

        Assert.Equal(1, result.PdsInterceptsA);
    }

    [Fact]
    public void Finite_pds_stops_after_magazine_depletion()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    KineticPds(
                        chance: 0,
                        ammunition: 1,
                        computerBonus: 0),
                    Side("missile", missileLaunchesPerTurn: 2),
                    turnCap: 2))
            .Run(() => 1, () => 1, () => 100, () => 100);

        Assert.Equal(1, result.PdsAttemptsA);
        Assert.Equal(0, result.PdsAmmunitionA);
        Assert.Equal(0, result.PdsReadyAmmunitionA);
        Assert.Equal(0, result.PdsReserveAmmunitionA);
        Assert.Equal(4, result.MissilesReachedGuidanceB);
    }

    [Fact]
    public void No_pds_control_preserves_terminal_guidance()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side("kinetic"),
                    Side("missile", missileGuidance: 100, missileDamage: 20)))
            .Run(() => 1, () => 100, () => 1, () => 1);

        Assert.Equal(0, result.PdsAttemptsA);
        Assert.Equal(1, result.MissilesReachedGuidanceB);
        Assert.Equal(1, result.MissileHitsB);
    }
}
