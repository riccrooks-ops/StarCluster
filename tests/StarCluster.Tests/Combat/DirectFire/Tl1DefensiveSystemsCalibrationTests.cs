using StarCluster.Core.Combat.DirectFire;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class Tl1DefensiveSystemsCalibrationTests
{
    private static Tl1WeaponMatrixSideProfile Side(
        string family,
        int reactorOutput = 5,
        int sensorPower = 0,
        int ecmPower = 0,
        int eccmPower = 0,
        int hardenerPower = 0,
        int rechargePower = 0,
        int batteryCharges = 0,
        int batteryRestore = 0,
        string pdsFamily = "none",
        int pdsPowerCost = 0,
        int pdsChance = 0,
        int pdsAmmunition = 0,
        bool pdsUnlimited = false) =>
        new(
            family,
            "standard",
            family == "energy" ? 25 : family == "kinetic" ? 20 : 0,
            10,
            false,
            reactorOutput,
            family == "missile" ? 25 : family == "energy" ? 0 : 100,
            55,
            5,
            1,
            2,
            1,
            6,
            0,
            1,
            pdsFamily,
            pdsPowerCost,
            pdsFamily == "none" ? 0 : 1,
            pdsChance,
            pdsAmmunition,
            pdsUnlimited,
            true,
            3,
            5,
            6,
            sensorPower,
            ecmPower,
            eccmPower,
            hardenerPower,
            rechargePower,
            batteryCharges,
            batteryRestore);

    private static Tl1WeaponMatrixProfile Profile(
        Tl1WeaponMatrixSideProfile a,
        Tl1WeaponMatrixSideProfile b,
        int range,
        int turnCap = 1,
        int shieldCapacity = 2) =>
        new(shieldCapacity, 0, 1, 0, 4, 12, range, 5, turnCap, a, b);

    private static int CriticalMissRoll() => 1;

    private static int CriticalHitRoll() => 100;

    [Fact]
    public void Passive_sensors_require_range_three_or_less_for_a_firm_solution()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(Side("kinetic"), Side("kinetic"), range: 4))
            .Run(() => 1, () => 1);

        Assert.Equal(0, result.ShotsA);
        Assert.Equal(0, result.ShotsB);
        Assert.Equal(1, result.TrackDeniedTurnsA);
        Assert.Equal(1, result.TrackDeniedTurnsB);
    }

    [Fact]
    public void One_power_active_sensors_extend_firm_range_to_five()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side("kinetic", sensorPower: 1),
                    Side("kinetic", sensorPower: 1),
                    range: 5))
            .Run(() => 1, () => 1);

        Assert.Equal(1, result.ShotsA);
        Assert.Equal(1, result.ShotsB);
        Assert.Equal(1, result.FirmTrackTurnsA);
        Assert.Equal(1, result.SensorPowerCommittedA);
    }

    [Fact]
    public void Net_ecm_shrinks_the_firm_range_after_active_sensor_extension()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side("kinetic", sensorPower: 1),
                    Side("kinetic", ecmPower: 1),
                    range: 5))
            .Run(() => 1, () => 1);

        Assert.Equal(0, result.ShotsA);
        Assert.Equal(1, result.TrackDeniedTurnsA);
        Assert.Equal(1, result.EcmPowerCommittedB);
    }

    [Fact]
    public void Eccm_cancels_equal_ecm_and_restores_the_firm_solution()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side("kinetic", sensorPower: 1, eccmPower: 1),
                    Side("kinetic", ecmPower: 1),
                    range: 5))
            .Run(() => 1, () => 100);

        Assert.Equal(1, result.ShotsA);
        Assert.Equal(1, result.FirmTrackTurnsA);
        Assert.Equal(1, result.EccmPowerCommittedA);
    }

    [Fact]
    public void Ecm_does_not_add_a_second_accuracy_penalty_after_firm_exists()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side("kinetic", sensorPower: 1),
                    Side("kinetic", ecmPower: 1),
                    range: 4))
            .Run(() => 60, () => 100);

        Assert.Equal(1, result.ShotsA);
        Assert.Equal(1, result.HitsA);
    }

    [Fact]
    public void Shield_hardener_resists_spen_without_deleting_ordinary_damage()
    {
        Tl1WeaponMatrixResult hardened = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side("kinetic", hardenerPower: 1),
                    Side("kinetic"),
                    range: 0,
                    shieldCapacity: 4))
            .Run(CriticalMissRoll, CriticalHitRoll);
        Tl1WeaponMatrixResult control = new Tl1WeaponMatrixSimulator(
                Profile(Side("kinetic"), Side("kinetic"), range: 0, shieldCapacity: 4))
            .Run(CriticalMissRoll, CriticalHitRoll);

        Assert.Equal(0, hardened.HitsA);
        Assert.Equal(1, hardened.HitsB);
        Assert.Equal(0, hardened.SideA.Defense.CurrentShieldCapacity);
        Assert.Equal(1, control.SideA.Defense.CurrentShieldCapacity);
        Assert.Equal(1, hardened.SideA.Defense.ShieldArmor);
        Assert.Equal(4, hardened.SideA.Defense.ArmorLayers.Single().CurrentIntegrity);
        Assert.Equal(3, control.SideA.Defense.ArmorLayers.Single().CurrentIntegrity);
        Assert.Equal(1, hardened.ShieldHardenerPowerCommittedA);
    }

    [Fact]
    public void Tactical_recharge_uses_only_missing_capacity_after_base_recharge()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side("kinetic", rechargePower: 2),
                    Side("kinetic"),
                    range: 0,
                    turnCap: 2))
            .Run(CriticalMissRoll, CriticalHitRoll);

        Assert.Equal(0, result.HitsA);
        Assert.Equal(2, result.HitsB);
        Assert.Equal(1, result.ShieldRechargePowerSpentA);
    }

    [Fact]
    public void Shield_battery_uses_one_charge_on_the_next_turn_after_collapse()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(
                    Side(
                        "kinetic",
                        batteryCharges: 3,
                        batteryRestore: 3),
                    Side("kinetic"),
                    range: 0,
                    turnCap: 2))
            .Run(CriticalMissRoll, CriticalHitRoll);

        Assert.Equal(0, result.HitsA);
        Assert.Equal(2, result.HitsB);
        Assert.Equal(1, result.ShieldBatteryChargesUsedA);
    }

    [Fact]
    public void Powered_defenses_commit_before_standard_energy_weapon_fire()
    {
        Tl1WeaponMatrixSideProfile defender = Side(
            "energy",
            reactorOutput: 5,
            ecmPower: 1,
            hardenerPower: 1,
            pdsFamily: "energy",
            pdsPowerCost: 2,
            pdsChance: 40,
            pdsUnlimited: true);
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(defender, Side("kinetic"), range: 0))
            .Run(() => 1, () => 100);

        Assert.Equal(2, result.PdsPowerCommittedA);
        Assert.Equal(1, result.EcmPowerCommittedA);
        Assert.Equal(1, result.ShieldHardenerPowerCommittedA);
        Assert.Equal(0, result.ShotsA);
    }

    [Fact]
    public void Main_missile_magazine_starts_ready_and_reloads_from_twenty_four_reserve()
    {
        Tl1WeaponMatrixResult result = new Tl1WeaponMatrixSimulator(
                Profile(Side("kinetic"), Side("missile"), range: 0))
            .Run(() => 100, () => 100);

        Assert.Equal(1, result.LaunchesB);
        Assert.Equal(24, result.AmmunitionB);
        Assert.Equal(1, result.ReadyAmmunitionB);
        Assert.Equal(23, result.ReserveAmmunitionB);
    }
}
