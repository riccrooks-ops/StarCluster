using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;

namespace StarCluster.Core.Combat.DirectFire;

public static class DirectFireAccuracyCalculator
{
    public static DirectFireAccuracyResult Calculate(
        DirectFireAccuracyProfile profile,
        int rangeHexes,
        bool targetEvasive,
        bool shooterEvasive,
        int otherModifiers = 0,
        ComponentCondition targetStlCondition = ComponentCondition.Operational)
    {
        ArgumentNullException.ThrowIfNull(profile);
        if (rangeHexes < 0) throw new ArgumentOutOfRangeException(nameof(rangeHexes));
        int rangePenalty = checked(rangeHexes * profile.RangePenaltyPerHex);
        int targetPenalty = targetEvasive ? profile.TargetEvasivePenalty : 0;
        int shooterPenalty = shooterEvasive ? profile.ShooterEvasivePenalty : 0;
        int targetMobilityBonus =
            ComponentPerformance.TargetMobilityAccuracyBonus(targetStlCondition);
        int unbounded = checked(profile.BaseChance + profile.WeaponAccuracy +
            profile.TargetingComputerBonus - rangePenalty - targetPenalty -
            shooterPenalty + targetMobilityBonus + otherModifiers);
        int finalChance = Math.Clamp(unbounded, profile.MinimumChance, profile.MaximumChance);
        return new DirectFireAccuracyResult(
            profile.BaseChance,
            profile.WeaponAccuracy,
            profile.TargetingComputerBonus,
            rangePenalty,
            targetPenalty,
            shooterPenalty,
            targetMobilityBonus,
            otherModifiers,
            unbounded,
            finalChance);
    }
}
