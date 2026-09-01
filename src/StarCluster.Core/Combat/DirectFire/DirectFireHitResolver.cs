namespace StarCluster.Core.Combat.DirectFire;

public static class DirectFireHitResolver
{
    public static DirectFireRollOutcome Resolve(int roll, int finalChance)
    {
        if (roll is < 1 or > 100) throw new ArgumentOutOfRangeException(nameof(roll));
        if (finalChance is < 0 or > 100) throw new ArgumentOutOfRangeException(nameof(finalChance));
        if (roll == 1) return DirectFireRollOutcome.CriticalMiss;
        if (roll == 100) return DirectFireRollOutcome.CriticalHit;
        return roll > 100 - finalChance
            ? DirectFireRollOutcome.Hit
            : DirectFireRollOutcome.Miss;
    }

    public static bool IsHit(DirectFireRollOutcome outcome) =>
        outcome is DirectFireRollOutcome.Hit or DirectFireRollOutcome.CriticalHit;
}
