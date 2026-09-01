using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;

namespace StarCluster.Core.Combat.Tactics;

public sealed record TacticalShipDecisionSnapshot(
    string ShipId,
    ComponentCondition StlCondition,
    int NormalStlMovementHexes,
    bool HasUsableOffense,
    int MinimumWeaponRangeHexes,
    int MaximumWeaponRangeHexes)
{
    public int AvailableStlMovement => ComponentPerformance.StlMovement(
        NormalStlMovementHexes,
        StlCondition);

    public bool IsImmobile => AvailableStlMovement == 0;
}

public sealed record ObservedTargetSnapshot(
    string TargetId,
    bool IsKnown,
    bool IsObservedImmobile,
    bool AppearsCombatCapable,
    int MinimumWeaponRangeHexes = 0,
    int MaximumWeaponRangeHexes = 0);

public sealed record ObservedMissileTrack(
    string MissileId,
    string OwnerId,
    int EstimatedRangeHexes,
    bool IsInbound);

public sealed record TacticalPreviousTurnOutcome(
    RangeOrder PreviousRangeOrder,
    int PreviousRangeHexes,
    int RangeChangeHexes)
{
    public static TacticalPreviousTurnOutcome None { get; } = new(
        RangeOrder.Hold,
        0,
        0);
}

public sealed record RangeDecisionDoctrine
{
    public RangeDecisionDoctrine(
        int preferredMinimumRangeHexes,
        int preferredMaximumRangeHexes,
        int maximumUsefulWeaponRangeHexes,
        bool withdrawWhenDisarmed = true)
    {
        if (preferredMinimumRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(preferredMinimumRangeHexes));
        }
        if (preferredMaximumRangeHexes < preferredMinimumRangeHexes)
        {
            throw new ArgumentOutOfRangeException(nameof(preferredMaximumRangeHexes));
        }
        if (maximumUsefulWeaponRangeHexes < preferredMaximumRangeHexes)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumUsefulWeaponRangeHexes));
        }

        PreferredMinimumRangeHexes = preferredMinimumRangeHexes;
        PreferredMaximumRangeHexes = preferredMaximumRangeHexes;
        MaximumUsefulWeaponRangeHexes = maximumUsefulWeaponRangeHexes;
        WithdrawWhenDisarmed = withdrawWhenDisarmed;
    }

    public int PreferredMinimumRangeHexes { get; }

    public int PreferredMaximumRangeHexes { get; }

    public int MaximumUsefulWeaponRangeHexes { get; }

    public bool WithdrawWhenDisarmed { get; }
}

public sealed record TacticalDecisionContext
{
    public TacticalDecisionContext(
        int turnNumber,
        TacticalShipDecisionSnapshot ownShip,
        ObservedTargetSnapshot target,
        int currentRangeHexes,
        IReadOnlyList<ObservedMissileTrack> missileTracks,
        TacticalObjective objective,
        RangeDecisionDoctrine doctrine,
        TacticalPreviousTurnOutcome previousTurn,
        TacticalCombatBlackboard? combatBlackboard = null)
    {
        if (turnNumber <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(turnNumber));
        }
        ArgumentNullException.ThrowIfNull(ownShip);
        ArgumentNullException.ThrowIfNull(target);
        if (currentRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(currentRangeHexes));
        }
        ArgumentNullException.ThrowIfNull(missileTracks);
        ArgumentNullException.ThrowIfNull(doctrine);
        ArgumentNullException.ThrowIfNull(previousTurn);

        TurnNumber = turnNumber;
        OwnShip = ownShip;
        Target = target;
        CurrentRangeHexes = currentRangeHexes;
        MissileTracks = missileTracks;
        Objective = objective;
        Doctrine = doctrine;
        PreviousTurn = previousTurn;
        CombatBlackboard = combatBlackboard;
    }

    public int TurnNumber { get; }

    public TacticalShipDecisionSnapshot OwnShip { get; }

    public ObservedTargetSnapshot Target { get; }

    public int CurrentRangeHexes { get; }

    public IReadOnlyList<ObservedMissileTrack> MissileTracks { get; }

    public TacticalObjective Objective { get; }

    public RangeDecisionDoctrine Doctrine { get; }

    public TacticalPreviousTurnOutcome PreviousTurn { get; }

    public TacticalCombatBlackboard? CombatBlackboard { get; }
}
