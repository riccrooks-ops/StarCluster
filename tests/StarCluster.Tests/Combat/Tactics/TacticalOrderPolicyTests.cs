using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class TacticalOrderPolicyTests
{
    [Fact]
    public void ScriptedPolicyUsesNamedTurnOrder()
    {
        var policy = new ScriptedTacticalOrderPolicy(
            new Dictionary<int, RangeOrder> { [2] = RangeOrder.Open },
            RangeOrder.Hold);

        TacticalOrderPlan plan = policy.ChooseOrders(Context(turn: 2));

        Assert.Equal(RangeOrder.Open, plan.RangeOrder);
        Assert.Contains("turn 2", plan.DecisionReason);
    }

    [Fact]
    public void ScriptedPolicyUsesDefaultOrderWhenTurnIsUnspecified()
    {
        var policy = new ScriptedTacticalOrderPolicy(
            new Dictionary<int, RangeOrder>(),
            RangeOrder.Close);

        TacticalOrderPlan plan = policy.ChooseOrders(Context());

        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
    }

    [Fact]
    public void ScriptedPolicyRejectsNonPositiveTurnKeys()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new ScriptedTacticalOrderPolicy(
                new Dictionary<int, RangeOrder> { [0] = RangeOrder.Hold }));
    }

    [Fact]
    public void PreferredPolicyHoldsWhenStlIsDisabled()
    {
        var policy = new PreferredRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            stl: ComponentCondition.Disabled));

        Assert.Equal(RangeOrder.Hold, plan.RangeOrder);
        Assert.Equal(4, plan.DesiredRangeHexes);
    }

    [Fact]
    public void PreferredPolicyOpensForWithdrawalObjective()
    {
        var policy = new PreferredRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            objective: TacticalObjective.Withdraw));

        Assert.Equal(RangeOrder.Open, plan.RangeOrder);
        Assert.Null(plan.DesiredRangeHexes);
    }

    [Fact]
    public void PreferredPolicyWithdrawsWhenDisarmed()
    {
        var policy = new PreferredRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            hasOffense: false));

        Assert.Equal(RangeOrder.Open, plan.RangeOrder);
    }

    [Fact]
    public void PreferredPolicyClosesToMaximumUsefulRange()
    {
        var policy = new PreferredRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(range: 9));

        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
        Assert.Equal(6, plan.DesiredRangeHexes);
    }

    [Fact]
    public void PreferredPolicyOpensToPreferredMinimum()
    {
        var policy = new PreferredRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(range: 0));

        Assert.Equal(RangeOrder.Open, plan.RangeOrder);
        Assert.Equal(1, plan.DesiredRangeHexes);
    }

    [Fact]
    public void PreferredPolicyClosesToPreferredMaximum()
    {
        var policy = new PreferredRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(range: 4));

        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
        Assert.Equal(2, plan.DesiredRangeHexes);
    }

    [Fact]
    public void PreferredPolicyMaintainsCurrentRangeInsideBand()
    {
        var policy = new PreferredRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(range: 2));

        Assert.Equal(RangeOrder.MaintainPreferredRange, plan.RangeOrder);
        Assert.Equal(2, plan.DesiredRangeHexes);
    }

    [Fact]
    public void OpponentAwarePolicyUsesOuterEnvelopeWhenItOutrangesTarget()
    {
        var policy = new OpponentAwareRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 5,
            doctrine: new RangeDecisionDoctrine(3, 4, 5),
            targetMaximumRange: 4));

        Assert.Equal(RangeOrder.MaintainPreferredRange, plan.RangeOrder);
        Assert.Equal(5, plan.DesiredRangeHexes);
        Assert.Contains("exceeds observed opponent reach", plan.DecisionReason);
    }

    [Fact]
    public void OpponentAwarePolicyOpensTowardStandoffAdvantage()
    {
        var policy = new OpponentAwareRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 4,
            doctrine: new RangeDecisionDoctrine(3, 4, 5),
            targetMaximumRange: 4));

        Assert.Equal(RangeOrder.Open, plan.RangeOrder);
        Assert.Equal(5, plan.DesiredRangeHexes);
    }

    [Fact]
    public void OpponentAwarePolicyClosesToOuterPreferredRangeWhenOutranged()
    {
        var policy = new OpponentAwareRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 5,
            doctrine: new RangeDecisionDoctrine(1, 2, 4),
            targetMaximumRange: 5));

        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
        Assert.Equal(2, plan.DesiredRangeHexes);
        Assert.Contains("exceeds own useful reach", plan.DecisionReason);
    }

    [Fact]
    public void OpponentAwareEnergyUsesMiddleBandAgainstLongerRangeMissile()
    {
        var policy = new OpponentAwareRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 6,
            doctrine: new RangeDecisionDoctrine(3, 4, 5),
            targetMaximumRange: 6));

        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
        Assert.Equal(4, plan.DesiredRangeHexes);
    }

    [Fact]
    public void OpponentAwarePolicyFallsBackWhenTargetReachIsUnknown()
    {
        var policy = new OpponentAwareRangeTacticalPolicy();

        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 3,
            doctrine: new RangeDecisionDoctrine(1, 2, 4),
            targetMaximumRange: 0));

        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
        Assert.Equal(2, plan.DesiredRangeHexes);
        Assert.Contains("unknown", plan.DecisionReason);
    }


    [Fact]
    public void AdaptiveEngageClosesAfterObservedTrackFailure()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.EstablishContact(1);
        memory.RecordTrackObservation(2, StarCluster.Core.Combat.Tracking.TacticalTrackQuality.Approximate, true, false, true);
        var policy = new AdaptiveEngageTacticalPolicy();
        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 2,
            doctrine: new RangeDecisionDoctrine(0, 5, 5),
            blackboard: memory));
        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
        Assert.Equal(1, plan.DesiredRangeHexes);
    }

    [Fact]
    public void AdaptiveEngagePreservesObservedStandoffAdvantage()
    {
        var memory = new TacticalCombatBlackboard("B");
        memory.EstablishContact(1);
        memory.RecordOwnAttack(5);
        memory.RecordObservedOpponentAttack(3);
        var policy = new AdaptiveEngageTacticalPolicy();
        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 4,
            doctrine: new RangeDecisionDoctrine(0, 5, 5),
            blackboard: memory));
        Assert.Equal(RangeOrder.Open, plan.RangeOrder);
        Assert.Equal(5, plan.DesiredRangeHexes);
    }

    [Fact]
    public void AdaptiveEngageUsesOnlyOwnReachBeforeCombatEvidence()
    {
        var policy = new AdaptiveEngageTacticalPolicy();
        TacticalOrderPlan plan = policy.ChooseOrders(Context(
            range: 8,
            doctrine: new RangeDecisionDoctrine(0, 5, 5),
            targetMaximumRange: 99,
            blackboard: new TacticalCombatBlackboard("B")));
        Assert.Equal(RangeOrder.Close, plan.RangeOrder);
        Assert.Equal(6, plan.DesiredRangeHexes);
        Assert.DoesNotContain("99", plan.DecisionReason);
    }

    [Fact]
    public void EqualSpeedPursuitPreservesRange()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            4,
            Ship("A"),
            Plan(RangeOrder.Close),
            Ship("B"),
            Plan(RangeOrder.Open));

        Assert.Equal(4, result.FinalRangeHexes);
        Assert.Equal(4, result.SideA.MovementHexes);
        Assert.Equal(4, result.SideB.MovementHexes);
    }

    [Fact]
    public void DegradedPursuerLosesGroundToOperationalRetreat()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            4,
            Ship("A", ComponentCondition.Degraded),
            Plan(RangeOrder.Close),
            Ship("B"),
            Plan(RangeOrder.Open));

        Assert.Equal(6, result.FinalRangeHexes);
        Assert.Equal(2, result.SideA.MovementHexes);
        Assert.Equal(4, result.SideB.MovementHexes);
    }

    [Fact]
    public void DisabledStlCoercesCloseOrderToHold()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            4,
            Ship("A", ComponentCondition.Disabled),
            Plan(RangeOrder.Close),
            Ship("B"),
            Plan(RangeOrder.Hold));

        Assert.Equal(RangeOrder.Hold, result.SideA.ResolvedOrder);
        Assert.Equal(0, result.SideA.MovementHexes);
        Assert.Equal(RangeOrderResolutionStatus.StlUnavailable, result.SideA.Status);
        Assert.Equal(4, result.FinalRangeHexes);
    }

    [Fact]
    public void SharedCloseGoalDoesNotOvershootDesiredRange()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            4,
            Ship("A"),
            Plan(RangeOrder.Close, 2),
            Ship("B"),
            Plan(RangeOrder.Close, 2));

        Assert.Equal(2, result.FinalRangeHexes);
        Assert.Equal(2, result.SideA.MovementHexes + result.SideB.MovementHexes);
    }

    [Fact]
    public void SharedOpenGoalDoesNotOvershootDesiredRange()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            0,
            Ship("A"),
            Plan(RangeOrder.Open, 2),
            Ship("B"),
            Plan(RangeOrder.Open, 2));

        Assert.Equal(2, result.FinalRangeHexes);
        Assert.Equal(2, result.SideA.MovementHexes + result.SideB.MovementHexes);
    }

    [Fact]
    public void HoldOrdersReportNoMovementRequired()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            3,
            Ship("A"),
            Plan(RangeOrder.Hold),
            Ship("B"),
            Plan(RangeOrder.Hold));

        Assert.Equal(RangeOrderResolutionStatus.NoMovementRequired, result.SideA.Status);
        Assert.Equal(RangeOrderResolutionStatus.NoMovementRequired, result.SideB.Status);
    }

    [Fact]
    public void MaintainOrdersInsideBandReportNoMovementRequired()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            3,
            Ship("A"),
            Plan(RangeOrder.MaintainPreferredRange, 3),
            Ship("B"),
            Plan(RangeOrder.MaintainPreferredRange, 3));

        Assert.Equal(3, result.FinalRangeHexes);
        Assert.Equal(RangeOrderResolutionStatus.NoMovementRequired, result.SideA.Status);
        Assert.Equal(RangeOrderResolutionStatus.NoMovementRequired, result.SideB.Status);
    }

    [Fact]
    public void MaintainOrderCountersAnEqualSpeedCloseOrder()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            3,
            Ship("A"),
            Plan(RangeOrder.MaintainPreferredRange, 3),
            Ship("B"),
            Plan(RangeOrder.Close));

        Assert.Equal(3, result.FinalRangeHexes);
        Assert.Equal(
            RangeMovementDirection.Open,
            result.SideA.MovementDirection);
    }

    [Fact]
    public void MaintainOrderMatchesThrottledOpponentMovement()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            3,
            Ship("A"),
            Plan(RangeOrder.MaintainPreferredRange, 3),
            Ship("B"),
            Plan(RangeOrder.Close, 2));

        Assert.Equal(3, result.FinalRangeHexes);
        Assert.Equal(1, result.SideA.MovementHexes);
        Assert.Equal(1, result.SideB.MovementHexes);
    }

    [Fact]
    public void CrossingMovementStopsAtRangeZero()
    {
        RangeOrderResolution result = RangeOrderResolver.Resolve(
            2,
            Ship("A"),
            Plan(RangeOrder.Close),
            Ship("B"),
            Plan(RangeOrder.Close));

        Assert.Equal(0, result.FinalRangeHexes);
        Assert.Equal(2, result.SideA.MovementHexes + result.SideB.MovementHexes);
    }

    [Fact]
    public void TacticalDecisionContextRejectsNegativeRange()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new TacticalDecisionContext(
            1,
            Ship("A"),
            new ObservedTargetSnapshot("B", true, false, true),
            -1,
            Array.Empty<ObservedMissileTrack>(),
            TacticalObjective.Engage,
            new RangeDecisionDoctrine(1, 2, 6),
            TacticalPreviousTurnOutcome.None));
    }

    [Fact]
    public void RangeDoctrineRejectsInvertedPreferredBand()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new RangeDecisionDoctrine(4, 2, 6));
    }

    private static TacticalDecisionContext Context(
        int turn = 1,
        int range = 4,
        ComponentCondition stl = ComponentCondition.Operational,
        bool hasOffense = true,
        TacticalObjective objective = TacticalObjective.Engage,
        RangeDecisionDoctrine? doctrine = null,
        int targetMaximumRange = 0,
        TacticalCombatBlackboard? blackboard = null) => new(
        turn,
        Ship("A", stl, hasOffense),
        new ObservedTargetSnapshot(
            "B",
            true,
            false,
            true,
            MaximumWeaponRangeHexes: targetMaximumRange),
        range,
        Array.Empty<ObservedMissileTrack>(),
        objective,
        doctrine ?? new RangeDecisionDoctrine(1, 2, 6),
        TacticalPreviousTurnOutcome.None,
        blackboard);

    private static TacticalShipDecisionSnapshot Ship(
        string id,
        ComponentCondition condition = ComponentCondition.Operational,
        bool hasOffense = true) => new(
        id,
        condition,
        4,
        hasOffense,
        1,
        6);

    private static TacticalOrderPlan Plan(
        RangeOrder order,
        int? desiredRange = null) => new(
        order,
        $"Test {order} order.",
        desiredRange);
}
