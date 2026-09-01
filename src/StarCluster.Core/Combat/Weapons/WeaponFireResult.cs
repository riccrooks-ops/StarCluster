using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;

namespace StarCluster.Core.Combat.Weapons;

public sealed record WeaponFireResult(
    string WeaponId,
    string Mode,
    bool Hit,
    int TacticalPowerSpent,
    int AmmunitionSpent,
    int? RemainingAmmunition,
    TacticalPowerSnapshot Power,
    LayeredDamageResolution? DamageResolution);
