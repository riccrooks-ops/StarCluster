namespace StarCluster.Core.Combat;

/// <summary>
/// Stable tactical-combat phase order. Contact establishes the encounter;
/// repeatable combat turns begin with Movement. Electronic Warfare resolves
/// after Movement and before either Direct Fire or Missile / Interception.
/// Direct-fire commitments are made before missile movement so held
/// interception orders can react later in the same turn. Damage is revealed
/// only in the later Damage phase.
/// </summary>
public enum TacticalTurnPhase
{
    Movement,
    ElectronicWarfare,
    DirectFire,
    MissileAndInterception,
    Damage,
    DamageControl,
}
