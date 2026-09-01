using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Power;

public sealed class CombatBatteryState
{
    public CombatBatteryState(
        int pristineCharges,
        int powerPerCharge,
        int dischargeLimitPerTurn,
        int? currentCharges = null,
        ComponentCondition condition = ComponentCondition.Operational)
    {
        if (pristineCharges < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(pristineCharges));
        }
        if (powerPerCharge <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(powerPerCharge));
        }
        if (dischargeLimitPerTurn <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(dischargeLimitPerTurn));
        }
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }

        int charges = currentCharges ?? pristineCharges;
        if (charges < 0 || charges > pristineCharges)
        {
            throw new ArgumentOutOfRangeException(nameof(currentCharges));
        }

        PristineCharges = pristineCharges;
        CurrentCapacity = condition == ComponentCondition.Degraded
            ? HalfRoundedUp(pristineCharges)
            : condition == ComponentCondition.Destroyed ? 0 : pristineCharges;
        CurrentCharges = condition == ComponentCondition.Destroyed
            ? 0
            : Math.Min(charges, CurrentCapacity);
        PowerPerCharge = powerPerCharge;
        DischargeLimitPerTurn = dischargeLimitPerTurn;
        Condition = condition;
    }

    public int PristineCharges { get; }

    public int CurrentCapacity { get; private set; }

    public int CurrentCharges { get; private set; }

    public int PowerPerCharge { get; }

    public int DischargeLimitPerTurn { get; }

    public ComponentCondition Condition { get; private set; }

    public int DischargesThisTurn { get; private set; }

    public void BeginTurn() => DischargesThisTurn = 0;

    public int Discharge(TacticalPowerLedger ledger)
    {
        ArgumentNullException.ThrowIfNull(ledger);
        if (Condition is ComponentCondition.Disabled or ComponentCondition.Destroyed)
        {
            throw new InvalidOperationException(
                "A Disabled or Destroyed Combat Battery cannot discharge.");
        }
        if (CurrentCharges == 0)
        {
            throw new InvalidOperationException(
                "The Combat Battery has no remaining charges.");
        }
        if (DischargesThisTurn >= DischargeLimitPerTurn)
        {
            throw new InvalidOperationException(
                "The Combat Battery has reached its discharge limit for this turn.");
        }

        CurrentCharges--;
        DischargesThisTurn++;
        ledger.AddGeneratedPower(PowerPerCharge);
        return PowerPerCharge;
    }

    public ComponentCondition ApplyCriticalHit()
    {
        if (Condition == ComponentCondition.Operational)
        {
            Condition = ComponentCondition.Degraded;
            CurrentCapacity = HalfRoundedUp(PristineCharges);
            CurrentCharges = Math.Min(
                CurrentCapacity,
                HalfRoundedUp(CurrentCharges));
        }
        else if (Condition != ComponentCondition.Destroyed)
        {
            Condition = ComponentCondition.Destroyed;
            CurrentCapacity = 0;
            CurrentCharges = 0;
        }
        return Condition;
    }

    public ComponentCondition RepairOneStep()
    {
        if (Condition == ComponentCondition.Destroyed)
        {
            throw new InvalidOperationException(
                "A Destroyed Combat Battery cannot be repaired during combat.");
        }
        if (Condition == ComponentCondition.Degraded)
        {
            Condition = ComponentCondition.Operational;
            CurrentCapacity = PristineCharges;
        }
        return Condition;
    }

    private static int HalfRoundedUp(int value) => (value + 1) / 2;
}
