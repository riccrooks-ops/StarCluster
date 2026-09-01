namespace StarCluster.Core.Combat;

/// <summary>
/// Minimal engine-independent turn and phase cursor for tactical combat.
/// </summary>
public sealed class TacticalTurnState
{
    public int TurnNumber { get; private set; } = 1;

    public TacticalTurnPhase Phase { get; private set; } = TacticalTurnPhase.Movement;

    public bool IsMovementPhase => Phase == TacticalTurnPhase.Movement;

    public void AdvancePhase()
    {
        switch (Phase)
        {
            case TacticalTurnPhase.Movement:
                Phase = TacticalTurnPhase.ElectronicWarfare;
                break;
            case TacticalTurnPhase.ElectronicWarfare:
                Phase = TacticalTurnPhase.DirectFire;
                break;
            case TacticalTurnPhase.DirectFire:
                Phase = TacticalTurnPhase.MissileAndInterception;
                break;
            case TacticalTurnPhase.MissileAndInterception:
                Phase = TacticalTurnPhase.Damage;
                break;
            case TacticalTurnPhase.Damage:
                Phase = TacticalTurnPhase.DamageControl;
                break;
            case TacticalTurnPhase.DamageControl:
                TurnNumber++;
                Phase = TacticalTurnPhase.Movement;
                break;
        }
    }
}
