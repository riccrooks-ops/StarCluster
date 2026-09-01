namespace StarCluster.Core.Combat.Tactics;

public sealed record TacticalOrderPlan
{
    public TacticalOrderPlan(
        RangeOrder rangeOrder,
        string decisionReason,
        int? desiredRangeHexes = null)
    {
        if (string.IsNullOrWhiteSpace(decisionReason))
        {
            throw new ArgumentException(
                "A tactical-order decision reason is required.",
                nameof(decisionReason));
        }
        if (desiredRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(desiredRangeHexes));
        }

        RangeOrder = rangeOrder;
        DecisionReason = decisionReason;
        DesiredRangeHexes = desiredRangeHexes;
    }

    public RangeOrder RangeOrder { get; }

    public string DecisionReason { get; }

    public int? DesiredRangeHexes { get; }
}

public interface ITacticalOrderPolicy
{
    TacticalOrderPlan ChooseOrders(TacticalDecisionContext context);
}

public sealed class ScriptedTacticalOrderPolicy : ITacticalOrderPolicy
{
    private readonly IReadOnlyDictionary<int, RangeOrder> _ordersByTurn;
    private readonly RangeOrder _defaultOrder;

    public ScriptedTacticalOrderPolicy(
        IReadOnlyDictionary<int, RangeOrder> ordersByTurn,
        RangeOrder defaultOrder = RangeOrder.Hold)
    {
        ArgumentNullException.ThrowIfNull(ordersByTurn);
        if (ordersByTurn.Keys.Any(turn => turn <= 0))
        {
            throw new ArgumentOutOfRangeException(
                nameof(ordersByTurn),
                "Scripted turn numbers must be positive.");
        }
        _ordersByTurn = new Dictionary<int, RangeOrder>(ordersByTurn);
        _defaultOrder = defaultOrder;
    }

    public TacticalOrderPlan ChooseOrders(TacticalDecisionContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        RangeOrder order = _ordersByTurn.TryGetValue(
            context.TurnNumber,
            out RangeOrder scripted)
                ? scripted
                : _defaultOrder;
        return new TacticalOrderPlan(
            order,
            $"Scenario-scripted range order for turn {context.TurnNumber}.");
    }
}

public sealed class PreferredRangeTacticalPolicy : ITacticalOrderPolicy
{
    public TacticalOrderPlan ChooseOrders(TacticalDecisionContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        RangeDecisionDoctrine doctrine = context.Doctrine;
        int range = context.CurrentRangeHexes;

        if (context.OwnShip.IsImmobile)
        {
            return new TacticalOrderPlan(
                RangeOrder.Hold,
                "STL movement is unavailable.",
                range);
        }
        if (context.Objective == TacticalObjective.HoldPosition)
        {
            return new TacticalOrderPlan(
                RangeOrder.Hold,
                "The tactical objective requires holding position.",
                range);
        }
        if (context.Objective == TacticalObjective.Withdraw ||
            (doctrine.WithdrawWhenDisarmed &&
                !context.OwnShip.HasUsableOffense))
        {
            return new TacticalOrderPlan(
                RangeOrder.Open,
                "The ship is withdrawing from the engagement.");
        }
        if (range > doctrine.MaximumUsefulWeaponRangeHexes)
        {
            return new TacticalOrderPlan(
                RangeOrder.Close,
                "The target is outside every useful weapon range.",
                doctrine.MaximumUsefulWeaponRangeHexes);
        }
        if (range < doctrine.PreferredMinimumRangeHexes)
        {
            return new TacticalOrderPlan(
                RangeOrder.Open,
                "The target is inside the preferred range band.",
                doctrine.PreferredMinimumRangeHexes);
        }
        if (range > doctrine.PreferredMaximumRangeHexes)
        {
            return new TacticalOrderPlan(
                RangeOrder.Close,
                "The target is beyond the preferred range band.",
                doctrine.PreferredMaximumRangeHexes);
        }

        return new TacticalOrderPlan(
            RangeOrder.MaintainPreferredRange,
            "The target is inside the preferred range band.",
            range);
    }
}


public enum OpponentAwareRangeDecisionBasis
{
    UnknownTargetFallback,
    StandoffAdvantage,
    ShorterRangePressure,
    PeerEnvelope,
}

public sealed record OpponentAwareRangeSelection(
    int DesiredRangeHexes,
    OpponentAwareRangeDecisionBasis Basis,
    string DecisionReason);

public sealed class OpponentAwareRangeTacticalPolicy : ITacticalOrderPolicy
{
    public static OpponentAwareRangeSelection SelectRange(
        RangeDecisionDoctrine ownDoctrine,
        ObservedTargetSnapshot target)
    {
        ArgumentNullException.ThrowIfNull(ownDoctrine);
        ArgumentNullException.ThrowIfNull(target);

        int ownMaximum = ownDoctrine.MaximumUsefulWeaponRangeHexes;
        int targetMaximum = target.MaximumWeaponRangeHexes;
        if (!target.IsKnown || targetMaximum <= 0)
        {
            return new OpponentAwareRangeSelection(
                ownDoctrine.PreferredMaximumRangeHexes,
                OpponentAwareRangeDecisionBasis.UnknownTargetFallback,
                "Opponent weapon reach is unknown; use the established outer preferred range.");
        }
        if (ownMaximum > targetMaximum)
        {
            return new OpponentAwareRangeSelection(
                ownMaximum,
                OpponentAwareRangeDecisionBasis.StandoffAdvantage,
                $"Own useful reach {ownMaximum} exceeds observed opponent reach {targetMaximum}; seek the outer useful envelope.");
        }
        if (ownMaximum < targetMaximum)
        {
            return new OpponentAwareRangeSelection(
                ownDoctrine.PreferredMaximumRangeHexes,
                OpponentAwareRangeDecisionBasis.ShorterRangePressure,
                $"Observed opponent reach {targetMaximum} exceeds own useful reach {ownMaximum}; seek the outer established preferred range while preserving family doctrine.");
        }
        return new OpponentAwareRangeSelection(
            ownDoctrine.PreferredMaximumRangeHexes,
            OpponentAwareRangeDecisionBasis.PeerEnvelope,
            $"Weapon reach is equal at {ownMaximum}; use the outer established preferred range.");
    }

    public TacticalOrderPlan ChooseOrders(TacticalDecisionContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        RangeDecisionDoctrine doctrine = context.Doctrine;
        int range = context.CurrentRangeHexes;

        if (context.OwnShip.IsImmobile)
        {
            return new TacticalOrderPlan(
                RangeOrder.Hold,
                "STL movement is unavailable.",
                range);
        }
        if (context.Objective == TacticalObjective.HoldPosition)
        {
            return new TacticalOrderPlan(
                RangeOrder.Hold,
                "The tactical objective requires holding position.",
                range);
        }
        if (context.Objective == TacticalObjective.Withdraw ||
            (doctrine.WithdrawWhenDisarmed &&
                !context.OwnShip.HasUsableOffense))
        {
            return new TacticalOrderPlan(
                RangeOrder.Open,
                "The ship is withdrawing from the engagement.");
        }

        OpponentAwareRangeSelection selection = SelectRange(
            doctrine,
            context.Target);
        if (range < selection.DesiredRangeHexes)
        {
            return new TacticalOrderPlan(
                RangeOrder.Open,
                selection.DecisionReason,
                selection.DesiredRangeHexes);
        }
        if (range > selection.DesiredRangeHexes)
        {
            return new TacticalOrderPlan(
                RangeOrder.Close,
                selection.DecisionReason,
                selection.DesiredRangeHexes);
        }
        return new TacticalOrderPlan(
            RangeOrder.MaintainPreferredRange,
            selection.DecisionReason,
            selection.DesiredRangeHexes);
    }
}

/// <summary>
/// General Engage policy driven by own capabilities and player-observable
/// combat history. It never requires hidden opponent component or TL data.
/// Pre-contact search movement is handled separately by the encounter layer.
/// </summary>
public sealed class AdaptiveEngageTacticalPolicy : ITacticalOrderPolicy
{
    public TacticalOrderPlan ChooseOrders(TacticalDecisionContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        int range = context.CurrentRangeHexes;
        RangeDecisionDoctrine doctrine = context.Doctrine;

        if (context.OwnShip.IsImmobile)
        {
            return new TacticalOrderPlan(
                RangeOrder.Hold,
                "STL movement is unavailable.",
                range);
        }
        if (context.Objective == TacticalObjective.HoldPosition)
        {
            return new TacticalOrderPlan(
                RangeOrder.Hold,
                "The tactical objective requires holding position.",
                range);
        }
        if (context.Objective == TacticalObjective.Withdraw ||
            (doctrine.WithdrawWhenDisarmed && !context.OwnShip.HasUsableOffense))
        {
            return new TacticalOrderPlan(
                RangeOrder.Open,
                "The ship is withdrawing from the engagement.");
        }
        if (!context.Target.IsKnown)
        {
            return new TacticalOrderPlan(
                RangeOrder.Hold,
                "No target contact is available to the Engage policy.",
                range);
        }

        TacticalCombatBlackboard? memory = context.CombatBlackboard;
        if (memory is not null)
        {
            if (memory.LastTrackQuality is not null &&
                memory.LastTrackQuality != StarCluster.Core.Combat.Tracking.TacticalTrackQuality.Firm &&
                memory.LastTrackRangeHexes is int failedRange)
            {
                int desired = Math.Max(0, Math.Min(range, failedRange) - 1);
                return MoveTowardRange(
                    range,
                    desired,
                    $"The previous attack window did not provide a Firm track at range {failedRange}; close for a better observable solution.");
            }

            int? ownDemonstrated = memory.MaximumOwnAttackRangeHexes;
            int? opponentDemonstrated = memory.MaximumObservedOpponentAttackRangeHexes;
            if (ownDemonstrated is int ownRange &&
                (opponentDemonstrated is null || opponentDemonstrated.Value < ownRange))
            {
                return MoveTowardRange(
                    range,
                    ownRange,
                    "Observed combat supports a one-sided engagement envelope; preserve the demonstrated standoff range.");
            }
        }

        int ownMaximum = Math.Max(0, context.OwnShip.MaximumWeaponRangeHexes);
        if (range > ownMaximum)
        {
            return new TacticalOrderPlan(
                RangeOrder.Close,
                "The target is beyond this ship's own known physical weapon reach; close to the outer usable envelope.",
                ownMaximum);
        }

        return new TacticalOrderPlan(
            RangeOrder.MaintainPreferredRange,
            "The target is inside this ship's own weapon envelope; hold long enough to test the actual track and engagement state.",
            range);
    }

    private static TacticalOrderPlan MoveTowardRange(
        int currentRange,
        int desiredRange,
        string reason)
    {
        if (currentRange < desiredRange)
        {
            return new TacticalOrderPlan(RangeOrder.Open, reason, desiredRange);
        }
        if (currentRange > desiredRange)
        {
            return new TacticalOrderPlan(RangeOrder.Close, reason, desiredRange);
        }
        return new TacticalOrderPlan(
            RangeOrder.MaintainPreferredRange,
            reason,
            desiredRange);
    }
}
