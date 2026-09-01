using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;

namespace StarCluster.Core.Combat.InternalDamage;

public sealed class ShipDamageState
{
    private readonly List<ShipComponentState> _components;
    private readonly List<PendingRepair> _pendingRepairs = new();

    public ShipDamageState(
        LayeredDefenseState defense,
        InternalDamageTrack internalTrack,
        IEnumerable<ShipComponentState> components,
        ulong criticalExposureSeed,
        bool isPlayerShip,
        DamageControlProfile? damageControlProfile = null)
    {
        ArgumentNullException.ThrowIfNull(defense);
        ArgumentNullException.ThrowIfNull(internalTrack);
        ArgumentNullException.ThrowIfNull(components);
        _components = components.ToList();
        if (_components.Count == 0)
        {
            throw new ArgumentException(
                "At least one damageable component is required.",
                nameof(components));
        }
        if (_components.Select(component => component.Definition.Id)
            .Distinct(StringComparer.Ordinal).Count() != _components.Count)
        {
            throw new ArgumentException(
                "Component IDs must be unique.",
                nameof(components));
        }

        Defense = defense;
        InternalTrack = internalTrack;
        CriticalExposure = new CriticalExposureTable(_components);
        CriticalExposureSeed = criticalExposureSeed;
        IsPlayerShip = isPlayerShip;
        DamageControl = new DamageControlState(
            damageControlProfile ?? DamageControlProfile.Tl1);
    }

    public LayeredDefenseState Defense { get; }

    public InternalDamageTrack InternalTrack { get; }

    public CriticalExposureTable CriticalExposure { get; }

    public ulong CriticalExposureSeed { get; }

    public bool IsPlayerShip { get; }

    public DamageControlState DamageControl { get; }

    public IReadOnlyList<ShipComponentState> Components => _components;

    public int InternalPositionsCrossed { get; private set; }

    public int CriticalSelectionsResolved { get; private set; }

    public bool IsPendingDestruction { get; private set; }

    public bool IsDestroyed { get; private set; }

    public IReadOnlyList<PendingRepair> PendingRepairs => _pendingRepairs;

    public ShipCapabilitySnapshot CapabilitySnapshot =>
        ShipConditionEvaluator.Evaluate(this);

    public ShipComponentState GetComponent(string componentId) =>
        _components.SingleOrDefault(component => string.Equals(
            component.Definition.Id,
            componentId,
            StringComparison.Ordinal)) ?? throw new KeyNotFoundException(
                $"No installed component has ID '{componentId}'.");

    public void BeginTurn()
    {
        DamageControl.BeginTurn();
    }

    public IReadOnlyList<ComponentConditionTransition> ApplyPendingRepairsAtTurnRefresh()
    {
        var transitions = new List<ComponentConditionTransition>();
        foreach (PendingRepair repair in _pendingRepairs)
        {
            if (repair.Kind == PendingRepairKind.Hull)
            {
                Defense.RestoreHull(1);
                continue;
            }

            ShipComponentState component = GetComponent(
                repair.ComponentId ?? throw new InvalidOperationException(
                    "A component repair is missing its target ID."));
            transitions.Add(component.ApplyCombatRepair());
        }
        _pendingRepairs.Clear();
        return transitions.AsReadOnly();
    }

    internal int AdvanceInternalPosition()
    {
        InternalPositionsCrossed++;
        return InternalPositionsCrossed;
    }

    internal (CriticalExposureSelection Selection, ComponentConditionTransition Transition)
        ApplyCritical(string streamId)
    {
        CriticalExposureSelection selection = CriticalExposure.Select(
            CriticalExposureSeed,
            CriticalSelectionsResolved,
            streamId);
        CriticalSelectionsResolved++;
        ShipComponentState component = GetComponent(selection.ComponentId);
        ComponentConditionTransition transition = component.ApplyCriticalHit();
        if (component.Definition.Kind == ShipComponentKind.ShieldGenerator &&
            transition.NewCondition == ComponentCondition.Destroyed)
        {
            Defense.CollapseShields();
        }
        return (selection, transition);
    }

    internal void MarkPendingDestruction()
    {
        if (!IsDestroyed)
        {
            IsPendingDestruction = true;
        }
    }

    public void CompleteDamagePhase()
    {
        if (IsPendingDestruction)
        {
            IsDestroyed = true;
            IsPendingDestruction = false;
            Defense.CollapseShields();
            _pendingRepairs.Clear();
        }
    }

    internal void QueueRepair(PendingRepair repair)
    {
        ArgumentNullException.ThrowIfNull(repair);
        _pendingRepairs.Add(repair);
    }

    internal void RequireDamageControlAvailable()
    {
        if (IsDestroyed || IsPendingDestruction || Defense.CurrentHull == 0)
        {
            throw new InvalidOperationException(
                "A Destroyed or Pending Destruction ship cannot use Damage Control.");
        }
    }
}
