namespace StarCluster.Core.Combat.Damage;

/// <summary>
/// CP139 research/parity resolver for the DEF/RES candidate damage model.
/// It has no production caller. The production LayeredDamageResolver remains
/// the penetration-hardening authority until a later checkpoint explicitly promotes otherwise.
/// </summary>
public static class DefResDamageResolver
{
    public const double ShieldDefEffectiveCapPp = 45.0;
    public const double ArmorResEffectiveCapPp = 95.0;

    public static DefResDamageResolution Resolve(
        double shield,
        double armorIntegrity,
        double hull,
        double damage,
        double shieldPenetration,
        double armorPenetration,
        double shieldDefPp,
        double armorResPp,
        int defenseRoll)
    {
        if (shield < 0 || armorIntegrity < 0 || hull < 0 || damage < 0 || shieldPenetration < 0 || armorPenetration < 0 || shieldDefPp < 0 || armorResPp < 0)
            throw new ArgumentOutOfRangeException(nameof(damage));
        if (defenseRoll is < 1 or > 100)
            throw new ArgumentOutOfRangeException(nameof(defenseRoll));

        double effectiveDef = shield > 0
            ? Math.Min(ShieldDefEffectiveCapPp, Math.Max(0.0, shieldDefPp - shieldPenetration))
            : 0.0;
        bool deflected = shield > 0 && defenseRoll <= effectiveDef;
        if (deflected || damage <= 0)
            return new DefResDamageResolution(damage, effectiveDef, deflected, 0, 0, 0, 0, 0, 0, 0, 0, 0, shield, armorIntegrity, hull);

        double shieldAbsorbed = shield > 0 ? Math.Min(shield, damage) : 0.0;
        double finalShield = Math.Max(0.0, shield - shieldAbsorbed);
        double toArmor = damage - shieldAbsorbed;
        double effectiveRes = 0.0;
        double resisted = 0.0;
        double armorDamage = 0.0;
        double overflowRaw = toArmor;
        double finalArmor = armorIntegrity;
        if (armorIntegrity > 0 && toArmor > 0)
        {
            effectiveRes = Math.Min(ArmorResEffectiveCapPp, Math.Max(0.0, armorResPp - armorPenetration));
            double passFraction = 1.0 - effectiveRes / 100.0;
            double rawToCollapse = armorIntegrity / passFraction;
            double rawAgainstArmor = Math.Min(toArmor, rawToCollapse);
            armorDamage = rawAgainstArmor * passFraction;
            resisted = rawAgainstArmor - armorDamage;
            finalArmor = Math.Max(0.0, armorIntegrity - armorDamage);
            overflowRaw = Math.Max(0.0, toArmor - rawAgainstArmor);
        }
        double hullDamage = Math.Min(hull, overflowRaw);
        double finalHull = hull - hullDamage;
        double overkill = overflowRaw - hullDamage;
        return new DefResDamageResolution(damage, effectiveDef, false, shieldAbsorbed, toArmor, effectiveRes, resisted, armorDamage, overflowRaw, hullDamage, overkill, 0, finalShield, finalArmor, finalHull);
    }
}

public sealed record DefResDamageResolution(
    double IncomingDamage,
    double EffectiveDefPp,
    bool Deflected,
    double ShieldAbsorbed,
    double DamageToArmor,
    double EffectiveResPp,
    double ArmorResistedDamage,
    double ArmorDamage,
    double ArmorOverflowRaw,
    double HullDamage,
    double OverkillDamage,
    double Reserved,
    double FinalShield,
    double FinalArmorIntegrity,
    double FinalHull);
