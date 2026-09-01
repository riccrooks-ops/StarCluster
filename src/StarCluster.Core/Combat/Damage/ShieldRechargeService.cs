using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Power;

namespace StarCluster.Core.Combat.Damage;

public static class ShieldRechargeService
{
    public static ShieldRechargeResult ApplyTurnStart(
        LayeredDefenseState defense,
        ComponentCondition shieldCondition,
        ShieldRechargeProfile profile,
        TacticalPowerLedger power,
        int requestedTacticalPower)
    {
        ArgumentNullException.ThrowIfNull(defense);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(power);
        if (requestedTacticalPower < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(requestedTacticalPower));
        }

        int temporaryCapacityLost = defense.ClearTemporaryShieldOvercapacity();
        int baseRestored = defense.RestoreShields(
            profile.BaseRechargeFor(shieldCondition));
        int missingCapacity =
            defense.EffectiveShieldMaximum - defense.CurrentShieldCapacity;
        int requestedWithinCap = Math.Min(
            requestedTacticalPower,
            profile.TacticalPowerCapFor(shieldCondition));
        int powerNeededForMissingCapacity = CeilingDivide(
            missingCapacity,
            profile.TacticalRechargePerPower);
        int tacticalPowerSpent = Math.Min(
            requestedWithinCap,
            Math.Min(power.SpendablePower, powerNeededForMissingCapacity));
        if (tacticalPowerSpent > 0)
        {
            power.Spend(tacticalPowerSpent);
        }
        int tacticalRestored = defense.RestoreShields(
            checked(tacticalPowerSpent * profile.TacticalRechargePerPower));

        return new ShieldRechargeResult(
            temporaryCapacityLost,
            baseRestored,
            tacticalPowerSpent,
            tacticalRestored,
            defense.CurrentShieldCapacity,
            power.Snapshot());
    }

    private static int CeilingDivide(int numerator, int denominator) =>
        numerator <= 0
            ? 0
            : checked((numerator + denominator - 1) / denominator);
}
