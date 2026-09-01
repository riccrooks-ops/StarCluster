using System;
using StarCluster.Core.Combat.Power;

namespace StarCluster.Core.Combat.Damage;

/// <summary>
/// Tactical self-healing for armor profiles that explicitly support it. The
/// current candidate rule restores one Armor Integrity per Tactical Power, up
/// to the profile's per-turn TP cap, pristine Integrity, and the finite
/// in-combat regeneration reserve. Out-of-combat self-healing is a separate
/// recovery process and is not represented by this service.
/// </summary>
public sealed record ArmorTacticalRegenerationResult(
    int TacticalPowerSpent,
    int IntegrityRestored,
    int FinalIntegrity,
    int CombatRegenerationReserveRemaining);

public static class ArmorTacticalRegenerationService
{
    public static ArmorTacticalRegenerationResult Apply(
        ArmorLayerState armor,
        TacticalPowerLedger power,
        int tacticalPowerCap,
        int combatRegenerationReserveAi,
        int integrityPerTacticalPower = 1)
    {
        ArgumentNullException.ThrowIfNull(armor);
        ArgumentNullException.ThrowIfNull(power);
        if (tacticalPowerCap < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(tacticalPowerCap));
        }
        if (combatRegenerationReserveAi < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(combatRegenerationReserveAi));
        }
        if (integrityPerTacticalPower <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(integrityPerTacticalPower));
        }

        int missingIntegrity = armor.PristineIntegrity - armor.CurrentIntegrity;
        if (missingIntegrity <= 0 || tacticalPowerCap == 0 || combatRegenerationReserveAi == 0 || power.SpendablePower <= 0)
        {
            return new ArmorTacticalRegenerationResult(0, 0, armor.CurrentIntegrity, combatRegenerationReserveAi);
        }

        int maximumRestorable = Math.Min(missingIntegrity, combatRegenerationReserveAi);
        int powerNeeded = checked((maximumRestorable + integrityPerTacticalPower - 1) / integrityPerTacticalPower);
        int powerSpent = Math.Min(tacticalPowerCap, Math.Min(power.SpendablePower, powerNeeded));
        int restored = Math.Min(maximumRestorable, checked(powerSpent * integrityPerTacticalPower));
        if (powerSpent > 0)
        {
            power.Spend(powerSpent);
            armor.RestoreIntegrity(restored);
        }
        return new ArmorTacticalRegenerationResult(
            powerSpent,
            restored,
            armor.CurrentIntegrity,
            combatRegenerationReserveAi - restored);
    }
}
