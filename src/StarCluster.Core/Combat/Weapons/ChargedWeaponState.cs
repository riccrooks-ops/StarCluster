using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Power;

namespace StarCluster.Core.Combat.Weapons;

public sealed class ChargedWeaponState
{
    private bool _chargePaidThisTurn;
    private bool _retentionPaidThisTurn;

    public ChargedWeaponState(
        int requiredChargeTurns,
        int chargePowerPerTurn,
        bool retentionAllowed,
        int retentionUpkeep,
        int? maximumRetentionTurns = null)
    {
        if (requiredChargeTurns <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(requiredChargeTurns));
        }
        if (chargePowerPerTurn < 0 || retentionUpkeep < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(chargePowerPerTurn),
                "Charge and upkeep power cannot be negative.");
        }
        if (maximumRetentionTurns is <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumRetentionTurns));
        }

        RequiredChargeTurns = requiredChargeTurns;
        ChargePowerPerTurn = chargePowerPerTurn;
        RetentionAllowed = retentionAllowed;
        RetentionUpkeep = retentionUpkeep;
        MaximumRetentionTurns = maximumRetentionTurns;
    }

    public int RequiredChargeTurns { get; }

    public int ChargePowerPerTurn { get; }

    public bool RetentionAllowed { get; }

    public int RetentionUpkeep { get; }

    public int? MaximumRetentionTurns { get; }

    public int ChargeProgress { get; private set; }

    public bool IsReady { get; private set; }

    public int RetentionTurns { get; private set; }

    public bool RequiresRetentionPayment { get; private set; }

    public void BeginTurn()
    {
        if (ChargeProgress > 0 && !IsReady && !_chargePaidThisTurn)
        {
            ClearChargeState();
        }
        else if (IsReady)
        {
            if (!RetentionAllowed)
            {
                ClearChargeState();
            }
            else
            {
                RequiresRetentionPayment = true;
            }
        }

        _chargePaidThisTurn = false;
        _retentionPaidThisTurn = false;
    }

    public void PayCharge(TacticalPowerLedger power)
    {
        ArgumentNullException.ThrowIfNull(power);
        if (IsReady)
        {
            throw new InvalidOperationException("A Ready weapon cannot be charged again.");
        }
        if (_chargePaidThisTurn || _retentionPaidThisTurn)
        {
            throw new InvalidOperationException(
                "A charging weapon may receive only one charge or retention payment per turn.");
        }
        if (ChargePowerPerTurn > 0)
        {
            power.Spend(ChargePowerPerTurn);
        }
        ChargeProgress++;
        _chargePaidThisTurn = true;
        if (ChargeProgress >= RequiredChargeTurns)
        {
            ChargeProgress = RequiredChargeTurns;
            IsReady = true;
            RetentionTurns = 0;
            RequiresRetentionPayment = false;
        }
    }

    public void PayRetention(TacticalPowerLedger power)
    {
        ArgumentNullException.ThrowIfNull(power);
        if (!IsReady)
        {
            throw new InvalidOperationException("Only a Ready weapon can be retained.");
        }
        if (!RetentionAllowed)
        {
            throw new InvalidOperationException("This weapon cannot retain a completed charge.");
        }
        if (!RequiresRetentionPayment)
        {
            throw new InvalidOperationException(
                "This weapon's charge is already powered for the current turn.");
        }
        if (_chargePaidThisTurn || _retentionPaidThisTurn)
        {
            throw new InvalidOperationException(
                "A charging weapon may receive only one charge or retention payment per turn.");
        }
        if (MaximumRetentionTurns is int maximum && RetentionTurns >= maximum)
        {
            throw new InvalidOperationException(
                "This weapon has reached its normal retention limit.");
        }
        if (RetentionUpkeep > 0)
        {
            power.Spend(RetentionUpkeep);
        }
        RetentionTurns++;
        RequiresRetentionPayment = false;
        _retentionPaidThisTurn = true;
    }

    public void Fire()
    {
        if (!IsReady)
        {
            throw new InvalidOperationException("The charged weapon is not Ready.");
        }
        if (RequiresRetentionPayment)
        {
            throw new InvalidOperationException(
                "The Ready weapon must receive its retention upkeep before it can fire this turn.");
        }
        ClearChargeState();
    }

    public void StopRetention() => ClearChargeState();

    public void ApplyCondition(ComponentCondition condition)
    {
        if (condition is ComponentCondition.Disabled or ComponentCondition.Destroyed)
        {
            ClearChargeState();
        }
    }

    public void ResetForFtlTransition()
    {
        ClearChargeState();
        _chargePaidThisTurn = false;
        _retentionPaidThisTurn = false;
    }

    public void LoadState(
        int chargeProgress,
        bool isReady,
        int retentionTurns,
        bool readyPowerPaidThisTurn = false)
    {
        if (chargeProgress < 0 || chargeProgress > RequiredChargeTurns)
        {
            throw new ArgumentOutOfRangeException(nameof(chargeProgress));
        }
        if (retentionTurns < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(retentionTurns));
        }
        if (isReady && chargeProgress != RequiredChargeTurns)
        {
            throw new ArgumentException(
                "A Ready weapon must have complete charging progress.",
                nameof(isReady));
        }
        if (!isReady && retentionTurns != 0)
        {
            throw new ArgumentException(
                "A non-Ready weapon cannot have retention turns.",
                nameof(retentionTurns));
        }
        if (readyPowerPaidThisTurn && !isReady)
        {
            throw new ArgumentException(
                "Only a Ready weapon can have its current-turn power marked as paid.",
                nameof(readyPowerPaidThisTurn));
        }
        if (MaximumRetentionTurns is int maximum && retentionTurns > maximum)
        {
            throw new ArgumentOutOfRangeException(
                nameof(retentionTurns),
                retentionTurns,
                "Retention turns cannot exceed the weapon's normal retention limit.");
        }

        ChargeProgress = chargeProgress;
        IsReady = isReady;
        RetentionTurns = retentionTurns;
        RequiresRetentionPayment = isReady && !readyPowerPaidThisTurn;
        _chargePaidThisTurn = !isReady && chargeProgress > 0;
        _retentionPaidThisTurn = isReady && readyPowerPaidThisTurn && retentionTurns > 0;
    }

    private void ClearChargeState()
    {
        ChargeProgress = 0;
        IsReady = false;
        RetentionTurns = 0;
        RequiresRetentionPayment = false;
    }
}
