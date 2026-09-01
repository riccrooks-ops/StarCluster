using StarCluster.Core.Combat.Damage;
using Xunit;

namespace StarCluster.Tests.Combat.Damage;

public sealed class LayeredDamageResolverTests
{
    [Fact]
    public void ShieldCapacityAbsorbsOrdinaryDamageBeforeArmor()
    {
        LayeredDefenseState defense = CreateDefense(shield: 6, shieldArmor: 2);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(4, 0, 0));

        Assert.Equal(4, result.ShieldAbsorption);
        Assert.Equal(0, result.ShieldBypass);
        Assert.Equal(0, result.ShieldPenetrationResisted);
        Assert.Equal(2, defense.CurrentShieldCapacity);
        Assert.Equal(6, defense.ArmorLayers[0].CurrentIntegrity);
    }

    [Fact]
    public void ShieldArmorHardensAgainstSpenInsteadOfDeletingOrdinaryDamage()
    {
        LayeredDefenseState defense = CreateDefense(shield: 6, shieldArmor: 1);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(3, 2, 0));

        Assert.Equal(1, result.EffectiveShieldPenetration);
        Assert.Equal(1, result.ShieldPenetrationResisted);
        Assert.Equal(1, result.ShieldBypass);
        Assert.Equal(2, result.ShieldFacingDamage);
        Assert.Equal(2, result.ShieldAbsorption);
        Assert.Equal(4, defense.CurrentShieldCapacity);
        Assert.Equal(5, defense.ArmorLayers[0].CurrentIntegrity);
    }

    [Fact]
    public void ShieldArmorDoesNothingWhenSpenIsZero()
    {
        LayeredDefenseState defense = CreateDefense(shield: 6, shieldArmor: 2);

        LayeredDamageResolver.Resolve(defense, new AttackPacket(3, 0, 0));

        Assert.Equal(3, defense.CurrentShieldCapacity);
    }

    [Fact]
    public void ShieldPenetrationCannotCreateDamage()
    {
        LayeredDefenseState defense = CreateDefense(shield: 6);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(3, 9, 0));

        Assert.Equal(9, result.EffectiveShieldPenetration);
        Assert.Equal(3, result.ShieldBypass);
        Assert.Equal(6, defense.CurrentShieldCapacity);
        Assert.Equal(3, result.DamageToArmor);
    }

    [Fact]
    public void CollapsedShieldHasNoHardeningAndAllDamageProceedsToArmor()
    {
        LayeredDefenseState defense = CreateDefense(shield: 0, shieldArmor: 9);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(4, 4, 0));

        Assert.Equal(0, result.EffectiveShieldPenetration);
        Assert.Equal(0, result.ShieldPenetrationResisted);
        Assert.Equal(0, result.ShieldBypass);
        Assert.Equal(4, result.DamageToArmor);
        Assert.Equal(2, defense.ArmorLayers[0].CurrentIntegrity);
    }

    [Fact]
    public void ShieldOverflowJoinsBypassBeforeArmor()
    {
        LayeredDefenseState defense = CreateDefense(shield: 1);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(4, 1, 0));

        Assert.Equal(1, result.ShieldBypass);
        Assert.Equal(1, result.ShieldAbsorption);
        Assert.Equal(2, result.ShieldOverflow);
        Assert.Equal(3, result.DamageToArmor);
    }

    [Fact]
    public void ArmorProtectionHardensAgainstApenInsteadOfDeletingOrdinaryDamage()
    {
        LayeredDefenseState defense = CreateDefense(shield: 0);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(4, 0, 0));

        ArmorLayerDamageResolution armor = Assert.Single(result.ArmorLayers);
        Assert.Equal(2, armor.ArmorHardening);
        Assert.Equal(0, armor.EffectiveArmorPenetration);
        Assert.Equal(0, armor.ArmorPenetrationResisted);
        Assert.Equal(0, armor.ArmorBypass);
        Assert.Equal(4, armor.IntegrityDamage);
        Assert.Equal(2, defense.ArmorLayers[0].CurrentIntegrity);
        Assert.Equal(2, defense.ArmorLayers[0].CurrentProtection);
    }

    [Fact]
    public void ArmorPenetrationBypassesIntegrityAfterProtectionHardening()
    {
        LayeredDefenseState defense = CreateDefense(shield: 0);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(4, 0, 3));

        ArmorLayerDamageResolution armor = Assert.Single(result.ArmorLayers);
        Assert.Equal(1, armor.EffectiveArmorPenetration);
        Assert.Equal(2, armor.ArmorPenetrationResisted);
        Assert.Equal(1, armor.ArmorBypass);
        Assert.Equal(3, armor.IntegrityDamage);
        Assert.Equal(11, defense.CurrentHull);
        Assert.Equal(2, defense.ArmorLayers[0].CurrentProtection);
    }

    [Fact]
    public void ExhaustingArmorIntegrityDoesNotCreateDestructibleProtectionPool()
    {
        LayeredDefenseState defense = CreateDefense(shield: 0);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(8, 0, 0));

        ArmorLayerDamageResolution armor = Assert.Single(result.ArmorLayers);
        Assert.Equal(6, armor.IntegrityDamage);
        Assert.Equal(0, armor.ProtectionDamage);
        Assert.Equal(2, result.HullDamage);
        Assert.Equal(0, defense.ArmorLayers[0].CurrentIntegrity);
        Assert.Equal(2, defense.ArmorLayers[0].CurrentProtection);
        Assert.Equal(10, defense.CurrentHull);
    }

    [Fact]
    public void ArmorProtectionIsInactiveWhenIntegrityIsAlreadyZero()
    {
        LayeredDefenseState defense = CreateDefense(
            shield: 0,
            armorLayers: new[] { new ArmorLayerState("armor-1", 2, 2, 6, 0) });

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(4, 0, 9));

        ArmorLayerDamageResolution armor = Assert.Single(result.ArmorLayers);
        Assert.Equal(0, armor.ArmorHardening);
        Assert.Equal(0, armor.EffectiveArmorPenetration);
        Assert.Equal(4, result.HullDamage);
        Assert.Equal(2, defense.ArmorLayers[0].CurrentProtection);
    }

    [Fact]
    public void DamageBeyondHullReportsOverkill()
    {
        LayeredDefenseState defense = CreateDefense(
            shield: 0,
            hull: 1,
            armorLayers: new[] { new ArmorLayerState("armor-1", 2, 2, 0, 0) });

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(20, 0, 0));

        Assert.Equal(1, result.HullDamage);
        Assert.Equal(19, result.OverkillDamage);
        Assert.True(defense.IsDestroyed);
    }

    [Fact]
    public void ArmorPenetrationIsReusedUnchangedAcrossActiveLayers()
    {
        var layers = new[]
        {
            new ArmorLayerState("outer", 1, 1, 2, 2),
            new ArmorLayerState("inner", 1, 1, 3, 3),
        };
        LayeredDefenseState defense = CreateDefense(shield: 0, armorLayers: layers);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(8, 0, 2));

        Assert.Equal(2, result.ArmorLayers.Count);
        Assert.All(result.ArmorLayers, layer => Assert.Equal(1, layer.EffectiveArmorPenetration));
        Assert.All(result.ArmorLayers, layer => Assert.Equal(1, layer.ArmorPenetrationResisted));
    }

    [Fact]
    public void TemporaryShieldOvercapacityRaisesCurrentAndMaximum()
    {
        LayeredDefenseState defense = CreateDefense(shield: 6);

        defense.AddTemporaryShieldOvercapacity(2);

        Assert.Equal(8, defense.CurrentShieldCapacity);
        Assert.Equal(8, defense.EffectiveShieldMaximum);
    }

    [Fact]
    public void TurnRefreshClearsOnlyExcessTemporaryShieldCapacity()
    {
        LayeredDefenseState defense = CreateDefense(shield: 6);
        defense.AddTemporaryShieldOvercapacity(2);
        LayeredDamageResolver.Resolve(defense, new AttackPacket(1, 0, 0));

        int lost = defense.ClearTemporaryShieldOvercapacity();

        Assert.Equal(1, lost);
        Assert.Equal(6, defense.CurrentShieldCapacity);
        Assert.Equal(6, defense.EffectiveShieldMaximum);
    }

    [Fact]
    public void TemporaryPrimaryArmorProtectionBonusAddsPenetrationHardening()
    {
        LayeredDefenseState defense = CreateDefense(shield: 0);
        defense.SetTemporaryPrimaryArmorProtectionBonus(1);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(4, 0, 3));

        ArmorLayerDamageResolution armor = Assert.Single(result.ArmorLayers);
        Assert.Equal(3, armor.ArmorHardening);
        Assert.Equal(0, armor.EffectiveArmorPenetration);
        Assert.Equal(4, armor.IntegrityDamage);
        Assert.Equal(2, defense.ArmorLayers[0].CurrentProtection);
    }

    [Fact]
    public void TemporaryPrimaryArmorProtectionBonusDoesNotHardenOuterAblativeLayer()
    {
        var layers = new[]
        {
            new ArmorLayerState("outer", 1, 1, 2, 2),
            new ArmorLayerState("primary", 2, 2, 6, 6),
        };
        LayeredDefenseState defense = CreateDefense(shield: 0, armorLayers: layers);
        defense.SetTemporaryPrimaryArmorProtectionBonus(1);

        LayeredDamageResolution result = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(8, 0, 3));

        Assert.Equal(1, result.ArmorLayers[0].ArmorHardening);
        Assert.Equal(3, result.ArmorLayers[1].ArmorHardening);
    }

    [Fact]
    public void CloneProducesIndependentMutableDefenseState()
    {
        LayeredDefenseState original = CreateDefense(shield: 6);
        LayeredDefenseState clone = original.Clone();

        LayeredDamageResolver.Resolve(clone, new AttackPacket(4, 0, 0));

        Assert.Equal(6, original.CurrentShieldCapacity);
        Assert.Equal(2, clone.CurrentShieldCapacity);
    }

    private static LayeredDefenseState CreateDefense(
        int shield,
        int shieldArmor = 0,
        int hull = 12,
        IEnumerable<ArmorLayerState>? armorLayers = null) => new(
        pristineShieldCapacity: 6,
        currentShieldCapacity: shield,
        shieldArmor: shieldArmor,
        armorLayers: armorLayers ?? new[] { new ArmorLayerState("armor-1", 2, 2, 6, 6) },
        pristineHull: 12,
        currentHull: hull);
}
