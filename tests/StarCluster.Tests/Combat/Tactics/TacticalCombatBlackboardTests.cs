using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Tactics;
using StarCluster.Core.Combat.Tracking;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class TacticalCombatBlackboardTests
{
    private static readonly TacticalObservableStateSignature StableState = new(
        OpponentEcmEmissionObserved: true,
        OpponentActiveSensorEmissionObserved: false,
        OwnEccmCondition: ComponentCondition.Operational,
        OwnActiveSensorCondition: ComponentCondition.Operational);

    [Fact]
    public void ContactMemoryRetainsFirstDetectionTurn()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.EstablishContact(3);
        memory.EstablishContact(4);
        Assert.True(memory.ContactEstablished);
        Assert.Equal(3, memory.ContactEstablishedTurn);
    }

    [Fact]
    public void OrdinaryTrackFailureRemembersClosestFailedRange()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.RecordTrackObservation(3, TacticalTrackQuality.Approximate, true, false, true);
        memory.RecordTrackObservation(1, TacticalTrackQuality.Approximate, true, false, true);
        Assert.Equal(1, memory.ClosestOrdinaryTrackFailureRangeHexes);
        Assert.Equal(1, memory.LastTrackRangeHexes);
    }

    [Fact]
    public void FailedOverloadIsNotRepeatedAtSameOrGreaterRange()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.RecordOverloadFailure(TacticalEscalationKind.EccmOverload, 2, StableState);
        Assert.False(memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 2, StableState));
        Assert.False(memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 3, StableState));
    }

    [Fact]
    public void FailedOverloadMayBeRetriedAfterClosing()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.RecordOverloadFailure(TacticalEscalationKind.ActiveSensorOverload, 2, StableState);
        Assert.True(memory.CanAttemptOverload(TacticalEscalationKind.ActiveSensorOverload, 1, StableState));
    }

    [Fact]
    public void MaterialObservableStateChangeReenablesOverload()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.RecordOverloadFailure(TacticalEscalationKind.EccmOverload, 1, StableState);
        TacticalObservableStateSignature changed = StableState with
        {
            OpponentEcmEmissionObserved = false,
        };
        Assert.True(memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 1, changed));
    }

    [Fact]
    public void SafeStrainExhaustionSuppressesRetryEvenAfterClosingOrObservableChange()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.RecordSafeStrainExhausted(TacticalEscalationKind.EccmOverload);
        TacticalObservableStateSignature changed = StableState with
        {
            OpponentEcmEmissionObserved = false,
        };

        Assert.True(memory.IsSafeStrainExhausted(TacticalEscalationKind.EccmOverload));
        Assert.False(memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 0, StableState));
        Assert.False(memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 0, changed));
    }

    [Fact]
    public void AttackMemoryTracksOnlyObservedRanges()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.RecordOwnAttack(3);
        memory.RecordOwnAttack(5);
        memory.RecordObservedOpponentAttack(2);
        Assert.Equal(5, memory.MaximumOwnAttackRangeHexes);
        Assert.Equal(2, memory.MaximumObservedOpponentAttackRangeHexes);
    }
}
