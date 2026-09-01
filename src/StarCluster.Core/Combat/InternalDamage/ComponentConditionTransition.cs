using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.InternalDamage;

public sealed record ComponentConditionTransition(
    string ComponentId,
    ComponentCondition PreviousCondition,
    ComponentCondition NewCondition,
    int PreviousCapacity,
    int NewCapacity,
    int PreviousContents,
    int NewContents,
    bool Changed);
