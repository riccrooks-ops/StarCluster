using StarCluster.Core.Combat.Power;

namespace StarCluster.Core.Combat.Damage;

public sealed record ShieldRechargeResult(
    int TemporaryCapacityLost,
    int BaseRestored,
    int TacticalPowerSpent,
    int TacticalRestored,
    int FinalShieldCapacity,
    TacticalPowerSnapshot Power);
