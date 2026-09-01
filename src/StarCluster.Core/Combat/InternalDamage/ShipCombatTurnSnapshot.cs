using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.InternalDamage;

/// <summary>
/// Captures target mobility at the start of a combat turn. Accuracy procedures
/// use this immutable value for all attacks committed in that turn, so STL
/// damage suffered later in the same simultaneous window does not retroactively
/// grant the Immobile Target bonus.
/// </summary>
public sealed record ShipCombatTurnSnapshot(ComponentCondition StlCondition)
{
    public bool IsImmobile => StlCondition is
        ComponentCondition.Disabled or ComponentCondition.Destroyed;

    public static ShipCombatTurnSnapshot Capture(ShipDamageState ship)
    {
        ArgumentNullException.ThrowIfNull(ship);
        ShipComponentState? stl = ship.Components.FirstOrDefault(component =>
            component.Definition.Kind == ShipComponentKind.StlDrive);
        return new ShipCombatTurnSnapshot(
            stl?.Condition ?? ComponentCondition.Destroyed);
    }
}
