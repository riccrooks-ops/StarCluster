namespace StarCluster.Core.Combat.Tactics;

public enum RangeOrderResolutionStatus
{
    Executed,
    NoMovementRequired,
    Throttled,
    StlUnavailable,
    NoMovementResolved,
}

public sealed record RangeOrderSideResolution(
    RangeOrder RequestedOrder,
    RangeOrder ResolvedOrder,
    RangeMovementDirection MovementDirection,
    int AvailableMovementHexes,
    int MovementHexes,
    RangeOrderResolutionStatus Status,
    string ResolutionReason);

public sealed record RangeOrderResolution(
    int InitialRangeHexes,
    int FinalRangeHexes,
    int NetRangeChange,
    int SideADisplacement,
    int SideBDisplacement,
    RangeOrderSideResolution SideA,
    RangeOrderSideResolution SideB)
{
    public bool RangeChanged => InitialRangeHexes != FinalRangeHexes;
}

public static class RangeOrderResolver
{
    public static RangeOrderResolution Resolve(
        int currentRangeHexes,
        TacticalShipDecisionSnapshot sideA,
        TacticalOrderPlan planA,
        TacticalShipDecisionSnapshot sideB,
        TacticalOrderPlan planB)
    {
        if (currentRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(currentRangeHexes));
        }
        ArgumentNullException.ThrowIfNull(sideA);
        ArgumentNullException.ThrowIfNull(planA);
        ArgumentNullException.ThrowIfNull(sideB);
        ArgumentNullException.ThrowIfNull(planB);

        int availableA = sideA.AvailableStlMovement;
        int availableB = sideB.AvailableStlMovement;
        RangeMovementDirection directionA = ResolveDirection(
            planA.RangeOrder,
            planB.RangeOrder);
        RangeMovementDirection directionB = ResolveDirection(
            planB.RangeOrder,
            planA.RangeOrder);
        int requestedA = RequestedMovement(
            currentRangeHexes,
            planA,
            directionA,
            availableA);
        int requestedB = RequestedMovement(
            currentRangeHexes,
            planB,
            directionB,
            availableB);
        MatchMaintainMovement(
            planA.RangeOrder,
            availableA,
            planB.RangeOrder,
            availableB,
            ref requestedA,
            ref requestedB);

        int displacementA = SignedDisplacement("A", directionA, requestedA);
        int displacementB = SignedDisplacement("B", directionB, requestedB);
        LimitSharedDesiredRange(
            currentRangeHexes,
            planA,
            directionA,
            planB,
            directionB,
            ref displacementA,
            ref displacementB);
        LimitCrossing(
            currentRangeHexes,
            ref displacementA,
            ref displacementB);

        int finalRange = checked(
            currentRangeHexes + displacementB - displacementA);
        if (finalRange < 0)
        {
            throw new InvalidOperationException(
                "Range-order resolution permitted the ships to cross.");
        }

        int movedA = Math.Abs(displacementA);
        int movedB = Math.Abs(displacementB);
        RangeOrderSideResolution resolutionA = BuildSideResolution(
            planA.RangeOrder,
            directionA,
            availableA,
            movedA);
        RangeOrderSideResolution resolutionB = BuildSideResolution(
            planB.RangeOrder,
            directionB,
            availableB,
            movedB);
        return new RangeOrderResolution(
            currentRangeHexes,
            finalRange,
            finalRange - currentRangeHexes,
            displacementA,
            displacementB,
            resolutionA,
            resolutionB);
    }

    private static RangeMovementDirection ResolveDirection(
        RangeOrder ownOrder,
        RangeOrder opponentOrder) => ownOrder switch
        {
            RangeOrder.Hold => RangeMovementDirection.None,
            RangeOrder.Close => RangeMovementDirection.Close,
            RangeOrder.Open => RangeMovementDirection.Open,
            RangeOrder.MaintainPreferredRange => opponentOrder switch
            {
                RangeOrder.Close => RangeMovementDirection.Open,
                RangeOrder.Open => RangeMovementDirection.Close,
                _ => RangeMovementDirection.None,
            },
            _ => throw new ArgumentOutOfRangeException(nameof(ownOrder)),
        };

    private static void MatchMaintainMovement(
        RangeOrder orderA,
        int availableA,
        RangeOrder orderB,
        int availableB,
        ref int requestedA,
        ref int requestedB)
    {
        int originalA = requestedA;
        int originalB = requestedB;
        if (orderA == RangeOrder.MaintainPreferredRange &&
            orderB != RangeOrder.MaintainPreferredRange)
        {
            requestedA = Math.Min(availableA, originalB);
        }
        if (orderB == RangeOrder.MaintainPreferredRange &&
            orderA != RangeOrder.MaintainPreferredRange)
        {
            requestedB = Math.Min(availableB, originalA);
        }
    }

    private static int RequestedMovement(
        int currentRange,
        TacticalOrderPlan plan,
        RangeMovementDirection direction,
        int availableMovement)
    {
        if (direction == RangeMovementDirection.None || availableMovement == 0)
        {
            return 0;
        }
        if (plan.RangeOrder == RangeOrder.MaintainPreferredRange ||
            plan.DesiredRangeHexes is not int desired)
        {
            return availableMovement;
        }
        int needed = direction == RangeMovementDirection.Close
            ? Math.Max(0, currentRange - desired)
            : Math.Max(0, desired - currentRange);
        return Math.Min(availableMovement, needed);
    }

    private static void LimitSharedDesiredRange(
        int currentRange,
        TacticalOrderPlan planA,
        RangeMovementDirection directionA,
        TacticalOrderPlan planB,
        RangeMovementDirection directionB,
        ref int displacementA,
        ref int displacementB)
    {
        if (directionA == RangeMovementDirection.Close &&
            directionB == RangeMovementDirection.Close &&
            planA.DesiredRangeHexes is int desiredA &&
            planB.DesiredRangeHexes is int desiredB)
        {
            int targetRange = Math.Max(desiredA, desiredB);
            int rawRange = currentRange + displacementB - displacementA;
            if (rawRange < targetRange)
            {
                ReduceClosing(
                    targetRange - rawRange,
                    ref displacementA,
                    ref displacementB);
            }
        }
        else if (directionA == RangeMovementDirection.Open &&
            directionB == RangeMovementDirection.Open &&
            planA.DesiredRangeHexes is int openDesiredA &&
            planB.DesiredRangeHexes is int openDesiredB)
        {
            int targetRange = Math.Min(openDesiredA, openDesiredB);
            int rawRange = currentRange + displacementB - displacementA;
            if (rawRange > targetRange)
            {
                ReduceOpening(
                    rawRange - targetRange,
                    ref displacementA,
                    ref displacementB);
            }
        }
    }

    private static void ReduceClosing(
        int reduction,
        ref int displacementA,
        ref int displacementB)
    {
        int closingA = Math.Max(0, displacementA);
        int closingB = Math.Max(0, -displacementB);
        int total = closingA + closingB;
        if (reduction <= 0 || total == 0)
        {
            return;
        }
        int reduceA = (int)Math.Floor((double)reduction * closingA / total);
        int reduceB = reduction - reduceA;
        displacementA -= Math.Min(closingA, reduceA);
        displacementB += Math.Min(closingB, reduceB);
        ApplyRemainingClosingReduction(
            reduction - Math.Min(closingA, reduceA) - Math.Min(closingB, reduceB),
            ref displacementA,
            ref displacementB);
    }

    private static void ApplyRemainingClosingReduction(
        int remaining,
        ref int displacementA,
        ref int displacementB)
    {
        if (remaining <= 0)
        {
            return;
        }
        int extraA = Math.Min(Math.Max(0, displacementA), remaining);
        displacementA -= extraA;
        remaining -= extraA;
        if (remaining > 0)
        {
            int extraB = Math.Min(Math.Max(0, -displacementB), remaining);
            displacementB += extraB;
        }
    }

    private static void ReduceOpening(
        int reduction,
        ref int displacementA,
        ref int displacementB)
    {
        int openingA = Math.Max(0, -displacementA);
        int openingB = Math.Max(0, displacementB);
        int total = openingA + openingB;
        if (reduction <= 0 || total == 0)
        {
            return;
        }
        int reduceA = (int)Math.Floor((double)reduction * openingA / total);
        int reduceB = reduction - reduceA;
        displacementA += Math.Min(openingA, reduceA);
        displacementB -= Math.Min(openingB, reduceB);
        ApplyRemainingOpeningReduction(
            reduction - Math.Min(openingA, reduceA) - Math.Min(openingB, reduceB),
            ref displacementA,
            ref displacementB);
    }

    private static void ApplyRemainingOpeningReduction(
        int remaining,
        ref int displacementA,
        ref int displacementB)
    {
        if (remaining <= 0)
        {
            return;
        }
        int extraA = Math.Min(Math.Max(0, -displacementA), remaining);
        displacementA += extraA;
        remaining -= extraA;
        if (remaining > 0)
        {
            int extraB = Math.Min(Math.Max(0, displacementB), remaining);
            displacementB -= extraB;
        }
    }

    private static int SignedDisplacement(
        string side,
        RangeMovementDirection direction,
        int movement) => (side, direction) switch
        {
            (_, RangeMovementDirection.None) => 0,
            ("A", RangeMovementDirection.Close) => movement,
            ("A", RangeMovementDirection.Open) => -movement,
            ("B", RangeMovementDirection.Close) => -movement,
            ("B", RangeMovementDirection.Open) => movement,
            _ => throw new ArgumentOutOfRangeException(nameof(direction)),
        };

    private static void LimitCrossing(
        int currentRange,
        ref int displacementA,
        ref int displacementB)
    {
        int finalRange = currentRange + displacementB - displacementA;
        if (finalRange >= 0)
        {
            return;
        }

        int excessClosing = -finalRange;
        int closingA = Math.Max(0, displacementA);
        int closingB = Math.Max(0, -displacementB);
        int totalClosing = closingA + closingB;
        if (totalClosing <= 0)
        {
            throw new InvalidOperationException(
                "Negative range occurred without closing movement.");
        }

        int reduceA = (int)Math.Floor(
            (double)excessClosing * closingA / totalClosing);
        int reduceB = excessClosing - reduceA;
        displacementA -= Math.Min(closingA, reduceA);
        displacementB += Math.Min(closingB, reduceB);

        int remaining = -(currentRange + displacementB - displacementA);
        if (remaining > 0)
        {
            int extraA = Math.Min(Math.Max(0, displacementA), remaining);
            displacementA -= extraA;
            remaining -= extraA;
        }
        if (remaining > 0)
        {
            int extraB = Math.Min(Math.Max(0, -displacementB), remaining);
            displacementB += extraB;
            remaining -= extraB;
        }
        if (remaining != 0)
        {
            throw new InvalidOperationException(
                "Unable to clamp simultaneous movement at range zero.");
        }
    }

    private static RangeOrderSideResolution BuildSideResolution(
        RangeOrder requested,
        RangeMovementDirection direction,
        int available,
        int moved)
    {
        if (available == 0 && requested != RangeOrder.Hold)
        {
            return new RangeOrderSideResolution(
                requested,
                RangeOrder.Hold,
                RangeMovementDirection.None,
                0,
                0,
                RangeOrderResolutionStatus.StlUnavailable,
                "Requested movement was coerced to Hold because STL movement is unavailable.");
        }
        if (direction == RangeMovementDirection.None || moved == 0)
        {
            bool noMovementRequired = requested is
                RangeOrder.Hold or RangeOrder.MaintainPreferredRange;
            return new RangeOrderSideResolution(
                requested,
                RangeOrder.Hold,
                RangeMovementDirection.None,
                available,
                0,
                noMovementRequired
                    ? RangeOrderResolutionStatus.NoMovementRequired
                    : RangeOrderResolutionStatus.NoMovementResolved,
                requested == RangeOrder.MaintainPreferredRange
                    ? "No counter-movement was required to maintain range."
                    : requested == RangeOrder.Hold
                        ? "The requested Hold order required no movement."
                        : "The resolved order produced no movement.");
        }
        return new RangeOrderSideResolution(
            requested,
            requested,
            direction,
            available,
            moved,
            moved < available
                ? RangeOrderResolutionStatus.Throttled
                : RangeOrderResolutionStatus.Executed,
            moved < available
                ? "Movement was throttled by the desired separation or range-zero boundary."
                : "The requested range order used the available STL movement.");
    }
}
