using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Power;
using Xunit;

namespace StarCluster.Tests.Combat.Power;

public sealed class ReactorStateTests
{
    [Fact]
    public void OutputFollowsConditionAtTurnStart()
    {
        ReactorState reactor = CreateReactor(ComponentCondition.Degraded);

        Assert.Equal(3, reactor.CurrentOutput);
    }

    [Fact]
    public void DisabledReactorUsesEmergencyOutput()
    {
        ReactorState reactor = CreateReactor(ComponentCondition.Disabled);

        Assert.Equal(1, reactor.CurrentOutput);
    }

    [Fact]
    public void DestroyedReactorProducesNoOutput()
    {
        ReactorState reactor = CreateReactor(ComponentCondition.Destroyed);

        Assert.Equal(0, reactor.CurrentOutput);
    }

    [Fact]
    public void SafeOverloadAutomaticallyAddsPowerAndStrain()
    {
        ReactorState reactor = CreateReactor();
        TacticalPowerLedger ledger = CreateLedger(reactor);

        ReactorOverloadResult result = reactor.AttemptOverload(ledger);

        Assert.Equal(ReactorOverloadOutcome.SafeSuccess, result.Outcome);
        Assert.Equal(6, ledger.Envelope);
        Assert.Equal(1, reactor.CurrentStrain);
    }

    [Fact]
    public void OverloadAtLimitIsStillSafe()
    {
        ReactorState reactor = CreateReactor(strain: 1);
        TacticalPowerLedger ledger = CreateLedger(reactor);

        ReactorOverloadResult result = reactor.AttemptOverload(ledger);

        Assert.False(result.WasForced);
        Assert.Equal(2, reactor.CurrentStrain);
    }

    [Fact]
    public void ForcedOverloadSuccessAddsBenefitAfterRoll()
    {
        ReactorState reactor = CreateReactor(strain: 2);
        TacticalPowerLedger ledger = CreateLedger(reactor);

        ReactorOverloadResult result = reactor.AttemptOverload(ledger, 60);

        Assert.Equal(ReactorOverloadOutcome.ForcedSuccess, result.Outcome);
        Assert.Equal(6, ledger.Envelope);
        Assert.Equal(3, reactor.CurrentStrain);
    }

    [Fact]
    public void ForcedOverloadFailureAddsStrainButNoPower()
    {
        ReactorState reactor = CreateReactor(strain: 2);
        TacticalPowerLedger ledger = CreateLedger(reactor);

        ReactorOverloadResult result = reactor.AttemptOverload(ledger, 61);

        Assert.Equal(ReactorOverloadOutcome.Failure, result.Outcome);
        Assert.Equal(5, ledger.Envelope);
        Assert.Equal(3, reactor.CurrentStrain);
    }

    [Fact]
    public void CriticalSuccessAddsPowerWithoutAdditionalStrain()
    {
        ReactorState reactor = CreateReactor(strain: 2);
        TacticalPowerLedger ledger = CreateLedger(reactor);

        ReactorOverloadResult result = reactor.AttemptOverload(ledger, 100);

        Assert.Equal(ReactorOverloadOutcome.CriticalSuccess, result.Outcome);
        Assert.Equal(2, reactor.CurrentStrain);
        Assert.Equal(6, ledger.Envelope);
    }

    [Fact]
    public void CriticalFailureWorsensCondition()
    {
        ReactorState reactor = CreateReactor(strain: 2);
        TacticalPowerLedger ledger = CreateLedger(reactor);

        ReactorOverloadResult result = reactor.AttemptOverload(ledger, 1);

        Assert.Equal(ReactorOverloadOutcome.CriticalFailure, result.Outcome);
        Assert.Equal(ComponentCondition.Degraded, reactor.Condition);
        Assert.Equal(5, ledger.Envelope);
    }

    [Fact]
    public void ReactorCanOverloadOnlyOncePerTurn()
    {
        ReactorState reactor = CreateReactor();
        TacticalPowerLedger ledger = CreateLedger(reactor);
        reactor.AttemptOverload(ledger);

        Assert.Throws<InvalidOperationException>(() =>
            reactor.AttemptOverload(ledger));
    }

    [Fact]
    public void NewTurnRestoresOverloadOpportunityWithoutRemovingStrain()
    {
        ReactorState reactor = CreateReactor();
        TacticalPowerLedger ledger = CreateLedger(reactor);
        reactor.AttemptOverload(ledger);

        reactor.ResetTurn();
        ledger.BeginTurn(reactor.CurrentOutput);
        reactor.AttemptOverload(ledger);

        Assert.Equal(2, reactor.CurrentStrain);
    }

    [Fact]
    public void DisabledAndDestroyedReactorsCannotOverload()
    {
        ReactorState disabled = CreateReactor(ComponentCondition.Disabled);
        ReactorState destroyed = CreateReactor(ComponentCondition.Destroyed);

        Assert.Throws<InvalidOperationException>(() =>
            disabled.AttemptOverload(CreateLedger(disabled)));
        Assert.Throws<InvalidOperationException>(() =>
            destroyed.AttemptOverload(CreateLedger(destroyed)));
    }

    private static ReactorState CreateReactor(
        ComponentCondition condition = ComponentCondition.Operational,
        int strain = 0) => new(
        new ReactorPowerProfile(
            operationalOutput: 5,
            degradedOutput: 3,
            emergencyOutput: 1,
            overloadOutput: 1,
            strainLimit: 2,
            forcedOverloadSuccessPercent: 60),
        condition,
        strain);

    private static TacticalPowerLedger CreateLedger(ReactorState reactor)
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(reactor.CurrentOutput);
        return ledger;
    }
}
