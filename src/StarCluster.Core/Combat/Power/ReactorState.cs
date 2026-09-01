using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Power;

public sealed class ReactorState
{
    public ReactorState(
        ReactorPowerProfile profile,
        ComponentCondition condition = ComponentCondition.Operational,
        int currentStrain = 0)
    {
        ArgumentNullException.ThrowIfNull(profile);
        if (currentStrain < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(currentStrain));
        }

        Profile = profile;
        Condition = condition;
        CurrentStrain = currentStrain;
    }

    public ReactorPowerProfile Profile { get; }

    public ComponentCondition Condition { get; private set; }

    public int CurrentStrain { get; private set; }

    public bool OverloadUsedThisTurn { get; private set; }

    public int CurrentOutput => Profile.OutputFor(Condition);

    public void SetCondition(ComponentCondition condition) => Condition = condition;

    public void ResetTurn() => OverloadUsedThisTurn = false;

    public ReactorOverloadResult AttemptOverload(
        TacticalPowerLedger ledger,
        int? forcedRoll = null)
    {
        ArgumentNullException.ThrowIfNull(ledger);
        if (OverloadUsedThisTurn)
        {
            throw new InvalidOperationException(
                "This reactor has already overloaded this turn.");
        }
        if (Condition is ComponentCondition.Disabled or ComponentCondition.Destroyed)
        {
            throw new InvalidOperationException(
                $"A {Condition} reactor cannot overload.");
        }

        OverloadUsedThisTurn = true;
        bool forced = checked(CurrentStrain + 1) > Profile.StrainLimit;
        if (!forced)
        {
            CurrentStrain++;
            ledger.AddGeneratedPower(Profile.OverloadOutput);
            return new ReactorOverloadResult(
                ReactorOverloadOutcome.SafeSuccess,
                false,
                null,
                true,
                Profile.OverloadOutput,
                1,
                CurrentStrain,
                Condition);
        }

        int roll = forcedRoll ?? throw new InvalidOperationException(
            "A forced overload requires one d100 roll.");
        if (roll is < 1 or > 100)
        {
            throw new ArgumentOutOfRangeException(
                nameof(forcedRoll),
                roll,
                "A forced-overload roll must be between 1 and 100.");
        }

        if (roll == 100)
        {
            ledger.AddGeneratedPower(Profile.OverloadOutput);
            return new ReactorOverloadResult(
                ReactorOverloadOutcome.CriticalSuccess,
                true,
                roll,
                true,
                Profile.OverloadOutput,
                0,
                CurrentStrain,
                Condition);
        }

        CurrentStrain++;
        if (roll == 1)
        {
            Condition = Condition.WorsenOneStep();
            return new ReactorOverloadResult(
                ReactorOverloadOutcome.CriticalFailure,
                true,
                roll,
                false,
                0,
                1,
                CurrentStrain,
                Condition);
        }

        if (roll <= Profile.ForcedOverloadSuccessPercent)
        {
            ledger.AddGeneratedPower(Profile.OverloadOutput);
            return new ReactorOverloadResult(
                ReactorOverloadOutcome.ForcedSuccess,
                true,
                roll,
                true,
                Profile.OverloadOutput,
                1,
                CurrentStrain,
                Condition);
        }

        return new ReactorOverloadResult(
            ReactorOverloadOutcome.Failure,
            true,
            roll,
            false,
            0,
            1,
            CurrentStrain,
            Condition);
    }
}
