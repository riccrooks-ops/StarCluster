namespace StarCluster.Core.Combat.DirectFire;

public sealed record DirectFireAccuracyProfile
{
    public DirectFireAccuracyProfile(
        int baseChance,
        int weaponAccuracy,
        int targetingComputerBonus,
        int rangePenaltyPerHex,
        int targetEvasivePenalty,
        int shooterEvasivePenalty,
        int minimumChance = 5,
        int maximumChance = 95)
    {
        if (baseChance is < 0 or > 100) throw new ArgumentOutOfRangeException(nameof(baseChance));
        if (rangePenaltyPerHex < 0) throw new ArgumentOutOfRangeException(nameof(rangePenaltyPerHex));
        if (targetEvasivePenalty < 0) throw new ArgumentOutOfRangeException(nameof(targetEvasivePenalty));
        if (shooterEvasivePenalty < 0) throw new ArgumentOutOfRangeException(nameof(shooterEvasivePenalty));
        if (minimumChance is < 0 or > 100) throw new ArgumentOutOfRangeException(nameof(minimumChance));
        if (maximumChance is < 0 or > 100 || maximumChance < minimumChance) throw new ArgumentOutOfRangeException(nameof(maximumChance));
        BaseChance = baseChance;
        WeaponAccuracy = weaponAccuracy;
        TargetingComputerBonus = targetingComputerBonus;
        RangePenaltyPerHex = rangePenaltyPerHex;
        TargetEvasivePenalty = targetEvasivePenalty;
        ShooterEvasivePenalty = shooterEvasivePenalty;
        MinimumChance = minimumChance;
        MaximumChance = maximumChance;
    }

    public int BaseChance { get; }
    public int WeaponAccuracy { get; }
    public int TargetingComputerBonus { get; }
    public int RangePenaltyPerHex { get; }
    public int TargetEvasivePenalty { get; }
    public int ShooterEvasivePenalty { get; }
    public int MinimumChance { get; }
    public int MaximumChance { get; }
}
