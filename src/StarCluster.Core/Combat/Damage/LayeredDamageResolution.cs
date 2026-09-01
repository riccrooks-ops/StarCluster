namespace StarCluster.Core.Combat.Damage;

/// <summary>
/// Resolution for one armor layer under the canonical penetration-hardening model.
/// Armor Integrity is the layer's durability pool. Armor Protection is a
/// non-consumable hardening rating that reduces APEN while Integrity remains.
/// The legacy-named EffectiveProtection/DamagePrevented/NetDamage/
/// ProtectionDamage fields are retained for older diagnostics; new consumers
/// should prefer the explicit penetration fields appended to this record.
/// </summary>
public sealed record ArmorLayerDamageResolution(
    string LayerId,
    int IncomingDamage,
    int EffectiveProtection,
    int DamagePrevented,
    int NetDamage,
    int IntegrityDamage,
    int ProtectionDamage,
    int OverflowDamage,
    int FinalIntegrity,
    int FinalProtection,
    int ArmorHardening,
    int EffectiveArmorPenetration,
    int ArmorPenetrationResisted,
    int ArmorBypass,
    int ArmorFacingDamage);

/// <summary>
/// Deterministic SC/SA -> armor-layer -> Hull resolution. Shield Capacity and
/// Armor Integrity are durability pools. Shield Armor and Armor Protection are
/// penetration hardening only and do not delete ordinary damage.
/// </summary>
public sealed record LayeredDamageResolution(
    int IncomingDamage,
    int ShieldBypass,
    int ShieldFacingDamage,
    int ShieldArmorPrevented,
    int PostShieldArmorDamage,
    int ShieldAbsorption,
    int ShieldOverflow,
    int DamageToArmor,
    IReadOnlyList<ArmorLayerDamageResolution> ArmorLayers,
    int HullDamage,
    int OverkillDamage,
    int FinalShieldCapacity,
    int FinalHull,
    int EffectiveShieldPenetration,
    int ShieldPenetrationResisted);
