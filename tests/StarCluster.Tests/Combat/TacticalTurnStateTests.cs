using StarCluster.Core.Combat;
using Xunit;

namespace StarCluster.Tests.Combat;

public sealed class TacticalTurnStateTests
{
    [Fact]
    public void NewStateBeginsAtTurnOneMovement()
    {
        var state = new TacticalTurnState();

        Assert.Equal(1, state.TurnNumber);
        Assert.Equal(TacticalTurnPhase.Movement, state.Phase);
        Assert.True(state.IsMovementPhase);
    }

    [Fact]
    public void MovementAdvancesToElectronicWarfare()
    {
        var state = new TacticalTurnState();

        state.AdvancePhase();

        Assert.Equal(TacticalTurnPhase.ElectronicWarfare, state.Phase);
    }

    [Fact]
    public void ElectronicWarfareAdvancesToDirectFire()
    {
        var state = new TacticalTurnState();
        state.AdvancePhase();

        state.AdvancePhase();

        Assert.Equal(TacticalTurnPhase.DirectFire, state.Phase);
    }

    [Fact]
    public void DirectFireAdvancesToMissileAndInterception()
    {
        var state = new TacticalTurnState();
        state.AdvancePhase();
        state.AdvancePhase();

        state.AdvancePhase();

        Assert.Equal(TacticalTurnPhase.MissileAndInterception, state.Phase);
    }

    [Fact]
    public void MissileAndDamageAdvanceInOrder()
    {
        var state = new TacticalTurnState();
        state.AdvancePhase();
        state.AdvancePhase();
        state.AdvancePhase();

        state.AdvancePhase();
        Assert.Equal(TacticalTurnPhase.Damage, state.Phase);

        state.AdvancePhase();
        Assert.Equal(TacticalTurnPhase.DamageControl, state.Phase);
    }

    [Fact]
    public void DamageControlCompletesTurnAndReturnsToMovement()
    {
        var state = new TacticalTurnState();
        for (int index = 0; index < 6; index++)
        {
            state.AdvancePhase();
        }

        Assert.Equal(2, state.TurnNumber);
        Assert.Equal(TacticalTurnPhase.Movement, state.Phase);
        Assert.True(state.IsMovementPhase);
    }
}
