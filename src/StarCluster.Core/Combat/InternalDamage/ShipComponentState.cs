using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.InternalDamage;

public sealed class ShipComponentState
{
    public ShipComponentState(
        ShipComponentDefinition definition,
        ComponentCondition condition = ComponentCondition.Operational,
        int pristineCapacity = 0,
        int? currentContents = null,
        int loadedReadyPackages = 0)
    {
        ArgumentNullException.ThrowIfNull(definition);
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }
        if (pristineCapacity < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(pristineCapacity));
        }
        int contents = currentContents ?? pristineCapacity;
        if (contents < 0 || contents > pristineCapacity)
        {
            throw new ArgumentOutOfRangeException(nameof(currentContents));
        }
        if (loadedReadyPackages < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(loadedReadyPackages));
        }

        Definition = definition;
        Condition = condition;
        PristineCapacity = pristineCapacity;
        CurrentCapacity = condition == ComponentCondition.Degraded && IsFiniteStorage
            ? HalfRoundedUp(pristineCapacity)
            : condition == ComponentCondition.Destroyed && IsFiniteStorage
                ? 0
                : pristineCapacity;
        CurrentContents = condition == ComponentCondition.Destroyed && IsFiniteStorage
            ? 0
            : Math.Min(contents, CurrentCapacity);
        LoadedReadyPackages = loadedReadyPackages;
    }

    public ShipComponentDefinition Definition { get; }

    public ComponentCondition Condition { get; private set; }

    public int PristineCapacity { get; }

    public int CurrentCapacity { get; private set; }

    public int CurrentContents { get; private set; }

    public int LoadedReadyPackages { get; private set; }

    public bool IsFiniteStorage => Definition.Kind is
        ShipComponentKind.KineticMagazine or
        ShipComponentKind.MissileMagazine or
        ShipComponentKind.SpecialWeaponsMagazine or
        ShipComponentKind.AuxiliaryMagazine or
        ShipComponentKind.CombatBattery or
        ShipComponentKind.ShieldBattery;

    public bool IsPowerCapacitor =>
        Definition.Kind == ShipComponentKind.PowerCapacitor;

    public bool IsDestroyed => Condition == ComponentCondition.Destroyed;

    public ComponentConditionTransition ApplyCriticalHit()
    {
        ComponentCondition previous = Condition;
        int previousCapacity = CurrentCapacity;
        int previousContents = CurrentContents;

        if (IsFiniteStorage)
        {
            if (Condition == ComponentCondition.Operational)
            {
                Condition = ComponentCondition.Degraded;
                CurrentCapacity = HalfRoundedUp(PristineCapacity);
                CurrentContents = Math.Min(
                    CurrentCapacity,
                    HalfRoundedUp(CurrentContents));
            }
            else if (Condition != ComponentCondition.Destroyed)
            {
                Condition = ComponentCondition.Destroyed;
                CurrentCapacity = 0;
                CurrentContents = 0;
            }
        }
        else
        {
            Condition = Condition.WorsenOneStep();
            if (IsPowerCapacitor && Condition == ComponentCondition.Destroyed)
            {
                CurrentCapacity = 0;
                CurrentContents = 0;
            }
        }

        return new ComponentConditionTransition(
            Definition.Id,
            previous,
            Condition,
            previousCapacity,
            CurrentCapacity,
            previousContents,
            CurrentContents,
            previous != Condition ||
                previousCapacity != CurrentCapacity ||
                previousContents != CurrentContents);
    }

    public ComponentConditionTransition ApplyCombatRepair()
    {
        ComponentCondition previous = Condition;
        int previousCapacity = CurrentCapacity;
        int previousContents = CurrentContents;

        if (Condition == ComponentCondition.Destroyed)
        {
            throw new InvalidOperationException(
                $"Destroyed component '{Definition.Id}' cannot be repaired in combat.");
        }
        if (Condition == ComponentCondition.Operational)
        {
            throw new InvalidOperationException(
                $"Component '{Definition.Id}' is already Operational.");
        }

        Condition = Condition == ComponentCondition.Disabled
            ? ComponentCondition.Degraded
            : ComponentCondition.Operational;
        if (IsFiniteStorage && Condition == ComponentCondition.Operational)
        {
            CurrentCapacity = PristineCapacity;
        }

        return new ComponentConditionTransition(
            Definition.Id,
            previous,
            Condition,
            previousCapacity,
            CurrentCapacity,
            previousContents,
            CurrentContents,
            true);
    }

    public void SetConditionForScenario(ComponentCondition condition)
    {
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }
        Condition = condition;
        if (IsPowerCapacitor)
        {
            CurrentCapacity = condition == ComponentCondition.Destroyed
                ? 0
                : PristineCapacity;
            if (condition == ComponentCondition.Destroyed)
            {
                CurrentContents = 0;
            }
            else
            {
                CurrentContents = Math.Min(CurrentContents, CurrentCapacity);
            }
        }
        if (IsFiniteStorage)
        {
            if (condition == ComponentCondition.Degraded)
            {
                CurrentCapacity = HalfRoundedUp(PristineCapacity);
                CurrentContents = Math.Min(CurrentContents, CurrentCapacity);
            }
            else if (condition == ComponentCondition.Destroyed)
            {
                CurrentCapacity = 0;
                CurrentContents = 0;
            }
            else if (condition == ComponentCondition.Operational)
            {
                CurrentCapacity = PristineCapacity;
            }
        }
    }

    public void ConsumeContents(int amount)
    {
        if (amount <= 0 || amount > CurrentContents)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        CurrentContents -= amount;
    }

    public void ConsumeReadyPackage(int amount = 1)
    {
        if (amount <= 0 || amount > LoadedReadyPackages)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        LoadedReadyPackages -= amount;
    }

    private static int HalfRoundedUp(int value) => (value + 1) / 2;
}
