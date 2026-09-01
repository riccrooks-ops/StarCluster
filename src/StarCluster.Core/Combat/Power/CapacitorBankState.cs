using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Power;

public sealed class CapacitorBankState
{
    private bool _blockRechargeNextTurn;

    public CapacitorBankState(
        int capacity,
        int chargeRate,
        int dischargeRate,
        int? storedPower = null,
        ComponentCondition condition = ComponentCondition.Operational)
    {
        if (capacity < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(capacity));
        }
        if (chargeRate <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(chargeRate));
        }
        if (dischargeRate <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(dischargeRate));
        }
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }

        int initial = storedPower ?? capacity;
        if (initial < 0 || initial > capacity)
        {
            throw new ArgumentOutOfRangeException(nameof(storedPower));
        }

        Capacity = capacity;
        ChargeRate = chargeRate;
        DischargeRate = dischargeRate;
        Condition = condition;
        StoredPower = condition == ComponentCondition.Destroyed ? 0 : initial;
    }

    public int Capacity { get; }

    public int ChargeRate { get; }

    public int DischargeRate { get; }

    public ComponentCondition Condition { get; private set; }

    public int StoredPower { get; private set; }

    public bool OperationUsedThisTurn { get; private set; }

    public bool RechargeBlockedThisTurn { get; private set; }

    public void BeginTurn()
    {
        OperationUsedThisTurn = false;
        RechargeBlockedThisTurn = _blockRechargeNextTurn;
        _blockRechargeNextTurn = false;
    }

    public int Charge(TacticalPowerLedger ledger, int requestedPower)
    {
        ArgumentNullException.ThrowIfNull(ledger);
        RequireFunctional();
        RequireOperationAvailable();
        if (RechargeBlockedThisTurn)
        {
            throw new InvalidOperationException(
                "The Degraded Capacitor Bank is in its post-discharge recharge-recovery turn.");
        }
        if (requestedPower <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(requestedPower));
        }

        int amount = Math.Min(
            requestedPower,
            Math.Min(ChargeRate, Capacity - StoredPower));
        if (amount <= 0)
        {
            throw new InvalidOperationException(
                "The Capacitor Bank is already at full capacity.");
        }

        ledger.Spend(amount);
        StoredPower += amount;
        OperationUsedThisTurn = true;
        return amount;
    }

    public int Discharge(TacticalPowerLedger ledger, int requestedPower)
    {
        ArgumentNullException.ThrowIfNull(ledger);
        RequireFunctional();
        RequireOperationAvailable();
        if (requestedPower <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(requestedPower));
        }

        int amount = Math.Min(
            requestedPower,
            Math.Min(DischargeRate, StoredPower));
        if (amount <= 0)
        {
            throw new InvalidOperationException(
                "The Capacitor Bank has no stored Tactical Power.");
        }

        StoredPower -= amount;
        OperationUsedThisTurn = true;
        if (Condition == ComponentCondition.Degraded)
        {
            _blockRechargeNextTurn = true;
        }
        ledger.AddGeneratedPower(amount);
        return amount;
    }

    public void SetCondition(ComponentCondition condition)
    {
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }
        Condition = condition;
        if (condition == ComponentCondition.Destroyed)
        {
            StoredPower = 0;
            _blockRechargeNextTurn = false;
            RechargeBlockedThisTurn = false;
        }
    }

    public ComponentCondition RepairOneStep()
    {
        if (Condition == ComponentCondition.Destroyed)
        {
            throw new InvalidOperationException(
                "A Destroyed Capacitor Bank cannot be repaired during combat.");
        }
        Condition = Condition.ImproveOneStep();
        return Condition;
    }

    public void CompleteFtlTransition()
    {
        if (Condition is ComponentCondition.Operational or ComponentCondition.Degraded)
        {
            StoredPower = Capacity;
        }
        OperationUsedThisTurn = false;
        RechargeBlockedThisTurn = false;
        _blockRechargeNextTurn = false;
    }

    private void RequireFunctional()
    {
        if (Condition is ComponentCondition.Disabled or ComponentCondition.Destroyed)
        {
            throw new InvalidOperationException(
                "A Disabled or Destroyed Capacitor Bank cannot charge or discharge.");
        }
    }

    private void RequireOperationAvailable()
    {
        if (OperationUsedThisTurn)
        {
            throw new InvalidOperationException(
                "The Capacitor Bank may charge or discharge only once per turn.");
        }
    }
}
