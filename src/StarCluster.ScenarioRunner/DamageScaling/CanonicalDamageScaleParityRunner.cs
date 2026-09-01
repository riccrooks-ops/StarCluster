using System.Text.Json;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.ScenarioRunner.DamageScaling;

public static class CanonicalDamageScaleParityRunner
{
    public static int Run(string outputDirectory)
    {
        Directory.CreateDirectory(outputDirectory);
        int layeredCases = 0;
        int mismatches = 0;
        var samples = new List<string>();

        int[] shieldCaps = new[] { 0, 1, 2, 3 };
        int[] shieldArmor = new[] { 0, 1, 2 };
        int[] armorProtection = new[] { 0, 1, 2, 3 };
        int[] armorIntegrity = new[] { 0, 2, 4, 6, 8 };
        int[] hullValues = new[] { 4, 8, 12 };

        for (int damage = 0; damage <= 12; damage++)
        for (int spen = 0; spen <= 4; spen++)
        for (int apen = 0; apen <= 4; apen++)
        foreach (int shield in shieldCaps)
        foreach (int sa in shieldArmor)
        foreach (int ap in armorProtection)
        foreach (int ai in armorIntegrity)
        foreach (int hull in hullValues)
        {
            layeredCases++;
            var legacy = Resolve(
                shield, sa, ap, ai, hull, damage, spen, apen, scale: 1);
            var canonical = Resolve(
                shield, sa, ap, ai, hull, damage, spen, apen,
                scale: DamagePointScale.Current);
            if (!Equivalent(legacy, canonical))
            {
                mismatches++;
                if (samples.Count < 20)
                {
                    samples.Add(
                        $"D{damage}/SP{spen}/AP{apen}; S{shield}/SA{sa}/" +
                        $"AP{ap}/AI{ai}/H{hull}");
                }
            }
        }

        int temporaryEffectCases = 0;
        for (int damage = 0; damage <= 12; damage++)
        for (int temporaryShield = 0; temporaryShield <= 2; temporaryShield++)
        for (int temporaryArmor = 0; temporaryArmor <= 2; temporaryArmor++)
        {
            temporaryEffectCases++;
            var legacy = Resolve(
                2, 1, 1, 4, 12, damage, 1, 1, 1,
                temporaryShield, temporaryArmor);
            var canonical = Resolve(
                2, 1, 1, 4, 12, damage, 1, 1,
                DamagePointScale.Current,
                temporaryShield, temporaryArmor);
            if (!Equivalent(legacy, canonical))
            {
                mismatches++;
                if (samples.Count < 20)
                {
                    samples.Add(
                        $"temporary D{damage}; shield+{temporaryShield}; armor+{temporaryArmor}");
                }
            }
        }

        int energyCases = 0;
        for (int legacyDamage = 0; legacyDamage <= 20; legacyDamage++)
        {
            energyCases++;
            int oldDamage = ComponentPerformance.Weapon(
                WeaponFamily.Energy,
                ComponentCondition.Degraded,
                legacyDamage,
                normalPowerCost: 3,
                damagePointScale: DamagePointScale.Legacy).Damage;
            ConditionedWeaponPerformance migrated = ComponentPerformance.Weapon(
                WeaponFamily.Energy,
                ComponentCondition.Degraded,
                legacyDamage * DamagePointScale.Current,
                normalPowerCost: 3,
                damagePointScale: DamagePointScale.Current);
            if (migrated.Damage != oldDamage * DamagePointScale.Current ||
                migrated.TacticalPowerCost != 2)
            {
                mismatches++;
                if (samples.Count < 20)
                {
                    samples.Add($"energy degraded legacy D{legacyDamage}");
                }
            }
        }

        var legacyRepair = new LayeredDefenseState(
            0, 0, 0, Array.Empty<ArmorLayerState>(), 12, 10);
        var parityRepair = new LayeredDefenseState(
            0, 0, 0, Array.Empty<ArmorLayerState>(), 24, 20);
        legacyRepair.RestoreHull(1);
        parityRepair.RestoreHull(2);
        bool repairParityExact =
            parityRepair.CurrentHull == legacyRepair.CurrentHull * 2;
        if (!repairParityExact)
        {
            mismatches++;
            samples.Add("artificial 2-Hull repair parity");
        }

        var summary = new
        {
            schemaVersion = "star-cluster-canonical-damage-scale-parity-v0.1",
            checkpoint = 122,
            damagePointScale = DamagePointScale.Current,
            layeredCases,
            temporaryEffectCases,
            energyDegradedCases = energyCases,
            productionRepairHullPerKit = 1,
            parityOnlyRepairHullPerKit = 2,
            repairParityExact,
            criticalCadenceMigrated = false,
            mismatches,
            mismatchSamples = samples,
            exactParity = mismatches == 0,
        };

        string json = JsonSerializer.Serialize(
            summary,
            new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(
            Path.Combine(outputDirectory, "summary.json"),
            json + Environment.NewLine);

        Console.WriteLine(
            $"CP122 canonical damage-scale parity: {layeredCases:N0} layered + " +
            $"{temporaryEffectCases:N0} temporary-effect + {energyCases:N0} " +
            $"degraded-Energy cases; mismatches={mismatches}; " +
            "production Repair Kit=1 Hull; parity-only Repair Kit=2 Hull; " +
            "critical cadence deferred.");
        return mismatches == 0 ? 0 : 1;
    }

    private static LayeredDamageResolution Resolve(
        int shield,
        int shieldArmor,
        int armorProtection,
        int armorIntegrity,
        int hull,
        int damage,
        int spen,
        int apen,
        int scale,
        int temporaryShield = 0,
        int temporaryArmor = 0)
    {
        int S(int value) => checked(value * scale);
        var armor = new ArmorLayerState(
            "primary",
            S(armorProtection),
            S(armorProtection),
            S(armorIntegrity),
            S(armorIntegrity));
        var defense = new LayeredDefenseState(
            S(shield),
            S(shield + temporaryShield),
            S(shieldArmor),
            new[] { armor },
            S(hull),
            S(hull),
            S(temporaryShield),
            S(temporaryArmor));
        return LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(S(damage), S(spen), S(apen)));
    }

    private static bool Equivalent(
        LayeredDamageResolution legacy,
        LayeredDamageResolution canonical)
    {
        bool E(int oldValue, int newValue) =>
            newValue == oldValue * DamagePointScale.Current;
        if (!E(legacy.IncomingDamage, canonical.IncomingDamage) ||
            !E(legacy.ShieldBypass, canonical.ShieldBypass) ||
            !E(legacy.ShieldFacingDamage, canonical.ShieldFacingDamage) ||
            !E(legacy.ShieldArmorPrevented, canonical.ShieldArmorPrevented) ||
            !E(legacy.PostShieldArmorDamage, canonical.PostShieldArmorDamage) ||
            !E(legacy.ShieldAbsorption, canonical.ShieldAbsorption) ||
            !E(legacy.ShieldOverflow, canonical.ShieldOverflow) ||
            !E(legacy.DamageToArmor, canonical.DamageToArmor) ||
            !E(legacy.HullDamage, canonical.HullDamage) ||
            !E(legacy.OverkillDamage, canonical.OverkillDamage) ||
            !E(legacy.FinalShieldCapacity, canonical.FinalShieldCapacity) ||
            !E(legacy.FinalHull, canonical.FinalHull) ||
            legacy.ArmorLayers.Count != canonical.ArmorLayers.Count)
        {
            return false;
        }

        for (int i = 0; i < legacy.ArmorLayers.Count; i++)
        {
            ArmorLayerDamageResolution a = legacy.ArmorLayers[i];
            ArmorLayerDamageResolution b = canonical.ArmorLayers[i];
            if (a.LayerId != b.LayerId ||
                !E(a.IncomingDamage, b.IncomingDamage) ||
                !E(a.EffectiveProtection, b.EffectiveProtection) ||
                !E(a.DamagePrevented, b.DamagePrevented) ||
                !E(a.NetDamage, b.NetDamage) ||
                !E(a.IntegrityDamage, b.IntegrityDamage) ||
                !E(a.ProtectionDamage, b.ProtectionDamage) ||
                !E(a.OverflowDamage, b.OverflowDamage) ||
                !E(a.FinalIntegrity, b.FinalIntegrity) ||
                !E(a.FinalProtection, b.FinalProtection))
            {
                return false;
            }
        }
        return true;
    }
}
