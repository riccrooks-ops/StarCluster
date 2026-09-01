using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.DirectFire;

public static class Tl1TargetingComputer
{
    public const int OperationalBonus = 10;
    public const int DegradedBonus = 5;

    public static int Bonus(ComponentCondition condition) => condition switch
    {
        ComponentCondition.Operational => OperationalBonus,
        ComponentCondition.Degraded => DegradedBonus,
        ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
        _ => throw new ArgumentOutOfRangeException(nameof(condition)),
    };
}
