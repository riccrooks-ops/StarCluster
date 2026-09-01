namespace StarCluster.Core.Combat.Damage;

/// <summary>
/// Canonical damage-domain unit scale introduced by Checkpoint 122.
/// One legacy damage-domain point is represented by two canonical points.
/// </summary>
public static class DamagePointScale
{
    public const int Legacy = 1;
    public const int Current = 2;

    public static int ToCanonical(int legacyPoints)
    {
        ValidatePoints(legacyPoints, nameof(legacyPoints));
        return checked(legacyPoints * Current);
    }

    /// <summary>
    /// Applies the legacy "half, round up" degraded-damage rule while
    /// preserving the active damage-point unit.  At the canonical x2 scale,
    /// D6 therefore degrades to D4 (the canonical equivalent of legacy
    /// D3 -> D2), rather than to D3.
    /// </summary>
    public static int HalfDamageRoundedUp(int damage, int damagePointScale = Current)
    {
        ValidatePoints(damage, nameof(damage));
        if (damagePointScale <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(damagePointScale));
        }

        int halfRoundedUp = (damage + 1) / 2;
        int remainder = halfRoundedUp % damagePointScale;
        int scaled = remainder == 0
            ? halfRoundedUp
            : checked(halfRoundedUp + damagePointScale - remainder);
        return Math.Min(damage, scaled);
    }

    private static void ValidatePoints(int value, string name)
    {
        if (value < 0)
        {
            throw new ArgumentOutOfRangeException(name);
        }
    }
}
