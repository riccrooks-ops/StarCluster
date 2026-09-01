namespace StarCluster.Core.Combat.Components;

public enum ComponentCondition
{
    Operational = 0,
    Degraded = 1,
    Disabled = 2,
    Destroyed = 3,
}

public static class ComponentConditionExtensions
{
    public static ComponentCondition WorsenOneStep(
        this ComponentCondition condition) => condition switch
        {
            ComponentCondition.Operational => ComponentCondition.Degraded,
            ComponentCondition.Degraded => ComponentCondition.Disabled,
            ComponentCondition.Disabled => ComponentCondition.Destroyed,
            ComponentCondition.Destroyed => ComponentCondition.Destroyed,
            _ => throw new ArgumentOutOfRangeException(
                nameof(condition),
                condition,
                "Unknown component condition."),
        };

    public static ComponentCondition ImproveOneStep(
        this ComponentCondition condition) => condition switch
        {
            ComponentCondition.Operational => ComponentCondition.Operational,
            ComponentCondition.Degraded => ComponentCondition.Operational,
            ComponentCondition.Disabled => ComponentCondition.Degraded,
            ComponentCondition.Destroyed => ComponentCondition.Destroyed,
            _ => throw new ArgumentOutOfRangeException(
                nameof(condition),
                condition,
                "Unknown component condition."),
        };
}
