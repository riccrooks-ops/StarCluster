namespace StarCluster.Core.Combat.Damage;

/// <summary>
/// Canonical deterministic layered-damage resolver.
///
/// SC and AI are the defensive hit-point pools. SA/AP are hardening ratings:
/// while the associated layer has positive capacity/integrity, SA reduces SPEN
/// and AP reduces APEN. Hardening never absorbs ordinary packet damage and is
/// never consumed by damage resolution. Once SC/AI reaches zero, that layer is
/// absent and its hardening provides no benefit until the layer is restored.
/// </summary>
public static class LayeredDamageResolver
{
    public static LayeredDamageResolution Resolve(
        LayeredDefenseState defense,
        AttackPacket packet)
    {
        ArgumentNullException.ThrowIfNull(defense);
        ArgumentNullException.ThrowIfNull(packet);

        int effectiveShieldPenetration;
        int shieldPenetrationResisted;
        int shieldBypass;
        int shieldFacingDamage;
        int shieldAbsorption;
        int shieldOverflow;
        int damageToArmor;

        if (defense.CurrentShieldCapacity > 0)
        {
            effectiveShieldPenetration = Math.Max(
                0,
                packet.ShieldPenetration - defense.ShieldArmor);
            shieldPenetrationResisted =
                packet.ShieldPenetration - effectiveShieldPenetration;
            shieldBypass = Math.Min(packet.Damage, effectiveShieldPenetration);
            shieldFacingDamage = packet.Damage - shieldBypass;
            shieldAbsorption = Math.Min(
                defense.CurrentShieldCapacity,
                shieldFacingDamage);
            defense.ApplyShieldDamage(shieldAbsorption);
            shieldOverflow = shieldFacingDamage - shieldAbsorption;
            damageToArmor = checked(shieldBypass + shieldOverflow);
        }
        else
        {
            // A collapsed/absent shield has nothing to penetrate or harden.
            effectiveShieldPenetration = 0;
            shieldPenetrationResisted = 0;
            shieldBypass = 0;
            shieldFacingDamage = 0;
            shieldAbsorption = 0;
            shieldOverflow = packet.Damage;
            damageToArmor = packet.Damage;
        }

        int remainingDamage = damageToArmor;
        var armorResults = new List<ArmorLayerDamageResolution>();
        for (int layerIndex = 0; layerIndex < defense.ArmorLayers.Count; layerIndex++)
        {
            ArmorLayerState layer = defense.ArmorLayers[layerIndex];
            if (remainingDamage <= 0)
            {
                break;
            }

            int incomingToLayer = remainingDamage;
            int temporaryPrimaryBonus = layerIndex == defense.ArmorLayers.Count - 1
                ? defense.TemporaryPrimaryArmorProtectionBonus
                : 0;

            if (layer.CurrentIntegrity <= 0)
            {
                // The layer is gone. Its AP/hardening is inactive and damage
                // proceeds unchanged to the next layer/Hull.
                armorResults.Add(new ArmorLayerDamageResolution(
                    layer.Id,
                    incomingToLayer,
                    0,
                    0,
                    incomingToLayer,
                    0,
                    0,
                    incomingToLayer,
                    layer.CurrentIntegrity,
                    layer.CurrentProtection,
                    0,
                    0,
                    0,
                    0,
                    0));
                continue;
            }

            int armorHardening = checked(
                layer.CurrentProtection + temporaryPrimaryBonus);
            int effectiveArmorPenetration = Math.Max(
                0,
                packet.ArmorPenetration - armorHardening);
            int armorPenetrationResisted =
                packet.ArmorPenetration - effectiveArmorPenetration;
            int armorBypass = Math.Min(
                incomingToLayer,
                effectiveArmorPenetration);
            int armorFacingDamage = incomingToLayer - armorBypass;
            int integrityDamage = Math.Min(
                layer.CurrentIntegrity,
                armorFacingDamage);
            layer.ApplyIntegrityDamage(integrityDamage);
            int armorOverflow = armorFacingDamage - integrityDamage;
            remainingDamage = checked(armorBypass + armorOverflow);

            armorResults.Add(new ArmorLayerDamageResolution(
                layer.Id,
                incomingToLayer,
                armorHardening, // legacy EffectiveProtection diagnostic alias
                armorPenetrationResisted, // legacy DamagePrevented alias
                incomingToLayer, // no ordinary damage is deleted by AP
                integrityDamage,
                0, // AP is not a destructible durability track
                remainingDamage,
                layer.CurrentIntegrity,
                layer.CurrentProtection,
                armorHardening,
                effectiveArmorPenetration,
                armorPenetrationResisted,
                armorBypass,
                armorFacingDamage));
        }

        int hullDamage = Math.Min(defense.CurrentHull, remainingDamage);
        defense.ApplyHullDamage(hullDamage);
        int overkillDamage = remainingDamage - hullDamage;

        return new LayeredDamageResolution(
            packet.Damage,
            shieldBypass,
            shieldFacingDamage,
            shieldPenetrationResisted, // legacy ShieldArmorPrevented alias
            shieldFacingDamage, // SA no longer removes ordinary facing damage
            shieldAbsorption,
            shieldOverflow,
            damageToArmor,
            armorResults.AsReadOnly(),
            hullDamage,
            overkillDamage,
            defense.CurrentShieldCapacity,
            defense.CurrentHull,
            effectiveShieldPenetration,
            shieldPenetrationResisted);
    }
}
