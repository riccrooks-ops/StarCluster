using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Power;

public sealed class AuxiliaryReactorState
{
    private bool _coolingNextTurn;

    public AuxiliaryReactorState(
        int operationalOutput,
        int degradedOutput,
        ComponentCondition condition = ComponentCondition.Operational)
    {
        if (operationalOutput < 0 || degradedOutput < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(operationalOutput));
        }
        if (degradedOutput > operationalOutput)
        {
            throw new ArgumentException(
                "Degraded Auxiliary Reactor output cannot exceed operational output.",
                nameof(degradedOutput));
        }
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }

        OperationalOutput = operationalOutput;
        DegradedOutput = degradedOutput;
        Condition = condition;
    }

    public int OperationalOutput { get; }

    public int DegradedOutput { get; }

    public ComponentCondition Condition { get; private set; }

    public bool CoolingThisTurn { get; private set; }

    public bool ContributedThisTurn { get; private set; }

    public int CurrentOutput => Condition switch
    {
        ComponentCondition.Operational => OperationalOutput,
        ComponentCondition.Degraded => CoolingThisTurn ? 0 : DegradedOutput,
        ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
        _ => throw new ArgumentOutOfRangeException(nameof(Condition)),
    };

    public void BeginTurn()
    {
        CoolingThisTurn = _coolingNextTurn;
        _coolingNextTurn = false;
        ContributedThisTurn = false;
    }

    public void SetCondition(ComponentCondition condition)
    {
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }
        Condition = condition;
        if (condition is ComponentCondition.Disabled or ComponentCondition.Destroyed)
        {
            _coolingNextTurn = false;
            CoolingThisTurn = false;
        }
    }

    public int Contribute(TacticalPowerLedger ledger)
    {
        ArgumentNullException.ThrowIfNull(ledger);
        if (ContributedThisTurn)
        {
            throw new InvalidOperationException(
                "The Auxiliary Reactor has already contributed this turn.");
        }

        int output = CurrentOutput;
        if (output > 0)
        {
            ledger.AddGeneratedPower(output);
            if (Condition == ComponentCondition.Degraded)
            {
                _coolingNextTurn = true;
            }
        }
        ContributedThisTurn = true;
        return output;
    }
}
