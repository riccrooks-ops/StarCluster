using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.ScenarioRunner.TL1;

public static class Tl1BaselineFactory
{
    public static LayeredDefenseState CreateDefense(
        Tl1BaselineCatalog baseline,
        Tl1DefenseFixture? fixture = null)
    {
        ArgumentNullException.ThrowIfNull(baseline);
        fixture ??= new Tl1DefenseFixture();

        int temporaryOvercapacity = fixture.TemporaryShieldOvercapacity;
        int baselineShield = baseline.GetInt("shield_capacity");
        int requiredPristineShield = Math.Max(
            0,
            (fixture.CurrentShieldCapacity ?? baselineShield) - temporaryOvercapacity);
        int pristineShield = fixture.PristineShieldCapacity ??
            Math.Max(baselineShield, requiredPristineShield);
        int currentShield = fixture.CurrentShieldCapacity ?? pristineShield;
        int pristineHull = fixture.PristineHull ?? baseline.GetInt("hull_points");
        int currentHull = fixture.CurrentHull ?? pristineHull;

        IEnumerable<ArmorLayerState> armorLayers = fixture.ArmorLayers is null
            ? new[]
            {
                new ArmorLayerState(
                    "armor-1",
                    baseline.GetInt("armor_protection"),
                    baseline.GetInt("armor_protection"),
                    baseline.GetInt("armor_integrity"),
                    baseline.GetInt("armor_integrity")),
            }
            : fixture.ArmorLayers.Select(item =>
            {
                int baselineProtection = baseline.GetInt("armor_protection");
                int baselineIntegrity = baseline.GetInt("armor_integrity");
                int pristineProtection = item.PristineProtection ??
                    Math.Max(baselineProtection, item.CurrentProtection ?? baselineProtection);
                int currentProtection = item.CurrentProtection ?? pristineProtection;
                int pristineIntegrity = item.PristineIntegrity ??
                    Math.Max(baselineIntegrity, item.CurrentIntegrity ?? baselineIntegrity);
                int currentIntegrity = item.CurrentIntegrity ?? pristineIntegrity;
                return new ArmorLayerState(
                    item.Id,
                    pristineProtection,
                    currentProtection,
                    pristineIntegrity,
                    currentIntegrity);
            });

        return new LayeredDefenseState(
            pristineShield,
            currentShield,
            fixture.ShieldArmor,
            armorLayers,
            pristineHull,
            currentHull,
            temporaryOvercapacity);
    }

    public static ShieldRechargeProfile CreateShieldRechargeProfile(
        Tl1BaselineCatalog baseline) => new(
        baseline.GetInt("shield_base_recharge"),
        baseline.GetInt("shield_tactical_recharge_rate"),
        baseline.GetInt("shield_tactical_recharge_cap"),
        baseline.GetInt("shield_degraded_base_recharge"),
        baseline.GetInt("shield_degraded_tactical_cap"));

    public static ReactorPowerProfile CreateReactorProfile(
        Tl1BaselineCatalog baseline) => new(
        baseline.GetInt("reactor_output"),
        baseline.GetInt("reactor_degraded_output"),
        baseline.GetInt("reactor_emergency_output"),
        baseline.GetInt("reactor_overload_output"),
        baseline.GetInt("reactor_strain_limit"),
        baseline.GetInt("forced_overload_success"));

    public static ReactorState CreateReactor(
        Tl1BaselineCatalog baseline,
        string condition,
        int strain = 0) => new(
        CreateReactorProfile(baseline),
        ParseCondition(condition),
        strain);

    public static WeaponProfile CreateWeaponProfile(
        Tl1BaselineCatalog baseline,
        string weapon,
        string mode)
    {
        string normalizedWeapon = weapon.Trim().ToLowerInvariant();
        string normalizedMode = mode.Trim().ToLowerInvariant();
        return normalizedWeapon switch
        {
            "kinetic" => new WeaponProfile(
                "tl1-kinetic-cannon",
                WeaponFamily.Kinetic,
                normalizedMode,
                new AttackPacket(
                    baseline.GetInt("kinetic_damage"),
                    baseline.GetInt("kinetic_spen"),
                    baseline.GetInt("kinetic_apen")),
                baseline.GetInt("kinetic_power"),
                ammunitionCost: 1,
                pristineAmmunition: baseline.GetInt("kinetic_ammo")),
            "energy" => CreateEnergyProfile(baseline, normalizedMode),
            "missile" => new WeaponProfile(
                "tl1-missile-launcher",
                WeaponFamily.Missile,
                normalizedMode,
                new AttackPacket(
                    baseline.GetInt("missile_warhead_damage"),
                    baseline.GetInt("missile_warhead_spen"),
                    baseline.GetInt("missile_warhead_apen")),
                baseline.GetInt("missile_launch_power"),
                ammunitionCost: 1,
                pristineAmmunition: baseline.GetInt("missile_ammo")),
            _ => throw new InvalidOperationException(
                $"Unknown TL1 weapon family '{weapon}'."),
        };
    }


    public static Tl1DuelCalibrationProfile CreateKineticDuelProfile(
        Tl1BaselineCatalog baseline,
        int rangeHexes,
        bool sideAEvasive,
        bool sideBEvasive,
        int sideAComputerBonus,
        int sideBComputerBonus,
        int turnCap) => new(
        ShieldCapacity: baseline.GetInt("shield_capacity"),
        ShieldArmor: 0,
        ShieldRecharge: baseline.GetInt("shield_base_recharge"),
        ArmorProtection: baseline.GetInt("armor_protection"),
        ArmorIntegrity: baseline.GetInt("armor_integrity"),
        Hull: baseline.GetInt("hull_points"),
        WeaponDamage: baseline.GetInt("kinetic_damage"),
        ShieldPenetration: baseline.GetInt("kinetic_spen"),
        ArmorPenetration: baseline.GetInt("kinetic_apen"),
        WeaponPower: baseline.GetInt("kinetic_power"),
        Ammunition: baseline.GetInt("kinetic_ammo"),
        ReactorOutput: baseline.GetInt("reactor_output"),
        BaseChance: baseline.GetInt("direct_fire_base_chance"),
        WeaponAccuracy: baseline.GetInt("kinetic_accuracy"),
        RangePenaltyPerHex: baseline.GetInt("direct_fire_range_penalty"),
        TargetEvasivePenalty: baseline.GetInt("target_evasive_penalty"),
        ShooterEvasivePenalty: baseline.GetInt("shooter_evasive_penalty"),
        MinimumChance: baseline.GetInt("direct_fire_minimum_chance"),
        MaximumChance: baseline.GetInt("direct_fire_maximum_chance"),
        RangeHexes: rangeHexes,
        SideAEvasive: sideAEvasive,
        SideBEvasive: sideBEvasive,
        SideAComputerBonus: sideAComputerBonus,
        SideBComputerBonus: sideBComputerBonus,
        TurnCap: turnCap);

    public static ComponentCondition ParseCondition(string value) =>
        value.Trim().ToLowerInvariant() switch
        {
            "operational" => ComponentCondition.Operational,
            "degraded" => ComponentCondition.Degraded,
            "disabled" => ComponentCondition.Disabled,
            "destroyed" => ComponentCondition.Destroyed,
            _ => throw new InvalidOperationException(
                $"Unknown component condition '{value}'."),
        };

    private static WeaponProfile CreateEnergyProfile(
        Tl1BaselineCatalog baseline,
        string mode)
    {
        int power;
        int damage;
        int shieldPenetration;
        int armorPenetration;
        switch (mode)
        {
            case "low":
                power = baseline.GetInt("energy_low_power");
                damage = baseline.GetInt("energy_low_damage");
                shieldPenetration = 0;
                armorPenetration = 0;
                break;
            case "standard":
                power = baseline.GetInt("energy_standard_power");
                damage = baseline.GetInt("energy_standard_damage");
                shieldPenetration = baseline.GetInt("energy_spen");
                armorPenetration = baseline.GetInt("energy_apen");
                break;
            case "overload":
                power = baseline.GetInt("energy_overload_power");
                damage = baseline.GetInt("energy_overload_damage");
                shieldPenetration = baseline.GetInt("energy_spen");
                armorPenetration = baseline.GetInt("energy_apen");
                break;
            default:
                throw new InvalidOperationException(
                    $"Unknown TL1 energy-weapon mode '{mode}'.");
        }

        return new WeaponProfile(
            "tl1-energy-cannon",
            WeaponFamily.Energy,
            mode,
            new AttackPacket(damage, shieldPenetration, armorPenetration),
            power,
            ammunitionCost: 0,
            pristineAmmunition: null);
    }
}
