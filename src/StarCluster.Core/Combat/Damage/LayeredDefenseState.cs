namespace StarCluster.Core.Combat.Damage;

public sealed class LayeredDefenseState
{
    private readonly List<ArmorLayerState> _armorLayers;

    public LayeredDefenseState(
        int pristineShieldCapacity,
        int currentShieldCapacity,
        int shieldArmor,
        IEnumerable<ArmorLayerState> armorLayers,
        int pristineHull,
        int currentHull,
        int temporaryShieldOvercapacity = 0,
        int temporaryPrimaryArmorProtectionBonus = 0)
    {
        if (pristineShieldCapacity < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(pristineShieldCapacity));
        }
        if (temporaryShieldOvercapacity < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(temporaryShieldOvercapacity));
        }
        if (temporaryPrimaryArmorProtectionBonus < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(temporaryPrimaryArmorProtectionBonus));
        }
        int effectiveShieldMaximum = checked(
            pristineShieldCapacity + temporaryShieldOvercapacity);
        if (currentShieldCapacity < 0 || currentShieldCapacity > effectiveShieldMaximum)
        {
            throw new ArgumentOutOfRangeException(nameof(currentShieldCapacity));
        }
        if (shieldArmor < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(shieldArmor));
        }
        if (pristineHull < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(pristineHull));
        }
        if (currentHull < 0 || currentHull > pristineHull)
        {
            throw new ArgumentOutOfRangeException(nameof(currentHull));
        }

        ArgumentNullException.ThrowIfNull(armorLayers);
        _armorLayers = armorLayers.Select(layer =>
            layer?.Clone() ?? throw new ArgumentException(
                "Armor layers cannot contain null entries.",
                nameof(armorLayers))).ToList();
        if (_armorLayers.Select(layer => layer.Id)
            .Distinct(StringComparer.Ordinal)
            .Count() != _armorLayers.Count)
        {
            throw new ArgumentException(
                "Armor layer IDs must be unique.",
                nameof(armorLayers));
        }

        PristineShieldCapacity = pristineShieldCapacity;
        CurrentShieldCapacity = currentShieldCapacity;
        ShieldArmor = shieldArmor;
        TemporaryShieldOvercapacity = temporaryShieldOvercapacity;
        TemporaryPrimaryArmorProtectionBonus = temporaryPrimaryArmorProtectionBonus;
        PristineHull = pristineHull;
        CurrentHull = currentHull;
    }

    public int PristineShieldCapacity { get; }

    public int TemporaryShieldOvercapacity { get; private set; }

    public int EffectiveShieldMaximum => checked(
        PristineShieldCapacity + TemporaryShieldOvercapacity);

    public int CurrentShieldCapacity { get; private set; }

    public int ShieldArmor { get; set; }

    public int TemporaryPrimaryArmorProtectionBonus { get; private set; }

    public IReadOnlyList<ArmorLayerState> ArmorLayers => _armorLayers;

    public int PristineHull { get; }

    public int CurrentHull { get; private set; }

    public bool IsDestroyed => CurrentHull == 0;

    public bool IsShieldCollapsed => CurrentShieldCapacity == 0;

    public int RestoreShields(int amount)
    {
        if (amount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        int restored = Math.Min(amount, EffectiveShieldMaximum - CurrentShieldCapacity);
        CurrentShieldCapacity += restored;
        return restored;
    }

    public int AddTemporaryShieldOvercapacity(int amount)
    {
        if (amount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        TemporaryShieldOvercapacity = checked(TemporaryShieldOvercapacity + amount);
        CurrentShieldCapacity = checked(CurrentShieldCapacity + amount);
        return amount;
    }

    public int ClearTemporaryShieldOvercapacity()
    {
        int lost = Math.Max(0, CurrentShieldCapacity - PristineShieldCapacity);
        CurrentShieldCapacity = Math.Min(
            CurrentShieldCapacity,
            PristineShieldCapacity);
        TemporaryShieldOvercapacity = 0;
        return lost;
    }

    public void SetTemporaryPrimaryArmorProtectionBonus(int amount)
    {
        if (amount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        TemporaryPrimaryArmorProtectionBonus = amount;
    }

    public void ClearTemporaryPrimaryArmorProtectionBonus() =>
        TemporaryPrimaryArmorProtectionBonus = 0;

    public int CollapseShields()
    {
        int lost = CurrentShieldCapacity;
        CurrentShieldCapacity = 0;
        TemporaryShieldOvercapacity = 0;
        return lost;
    }

    public int RestoreHull(int amount)
    {
        if (amount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        int restored = Math.Min(amount, PristineHull - CurrentHull);
        CurrentHull += restored;
        return restored;
    }

    internal void ApplyShieldDamage(int amount)
    {
        if (amount < 0 || amount > CurrentShieldCapacity)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        CurrentShieldCapacity -= amount;
    }

    internal void ApplyHullDamage(int amount)
    {
        if (amount < 0 || amount > CurrentHull)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        CurrentHull -= amount;
    }

    public LayeredDefenseState Clone() => new(
        PristineShieldCapacity,
        CurrentShieldCapacity,
        ShieldArmor,
        _armorLayers,
        PristineHull,
        CurrentHull,
        TemporaryShieldOvercapacity,
        TemporaryPrimaryArmorProtectionBonus);
}
