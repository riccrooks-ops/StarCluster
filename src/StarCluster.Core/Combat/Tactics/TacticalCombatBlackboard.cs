using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Tracking;

namespace StarCluster.Core.Combat.Tactics;

/// <summary>
/// Target-specific memory for observations that a player could legitimately
/// retain during the current tactical engagement. It intentionally stores no
/// hidden opponent component ratings, technology levels, jamming margin, or
/// future outcome information.
/// </summary>
public sealed class TacticalCombatBlackboard
{
    private readonly Dictionary<TacticalEscalationKind, TacticalOverloadFailure> _overloadFailures = new();
    private readonly HashSet<TacticalEscalationKind> _safeStrainExhausted = new();

    public TacticalCombatBlackboard(string targetId)
    {
        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException("A target identifier is required.", nameof(targetId));
        }
        TargetId = targetId;
    }

    public string TargetId { get; }

    public bool ContactEstablished { get; private set; }

    public int? ContactEstablishedTurn { get; private set; }

    public TacticalTrackQuality? LastTrackQuality { get; private set; }

    public int? LastTrackRangeHexes { get; private set; }

    public int? ClosestOrdinaryTrackFailureRangeHexes { get; private set; }

    public int? MaximumOwnAttackRangeHexes { get; private set; }

    public int? MaximumObservedOpponentAttackRangeHexes { get; private set; }

    public bool LastOpponentEcmEmissionObserved { get; private set; }

    public bool LastOpponentActiveSensorEmissionObserved { get; private set; }

    public bool LastFirmTrackDegradedByObservedEcm { get; private set; }

    public void EstablishContact(int turnNumber)
    {
        if (turnNumber <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(turnNumber));
        }
        ContactEstablished = true;
        ContactEstablishedTurn ??= turnNumber;
    }

    public void RecordTrackObservation(
        int rangeHexes,
        TacticalTrackQuality quality,
        bool opponentEcmEmissionObserved,
        bool opponentActiveSensorEmissionObserved,
        bool firmTrackDegradedByObservedEcm)
    {
        if (rangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(rangeHexes));
        }

        LastTrackRangeHexes = rangeHexes;
        LastTrackQuality = quality;
        LastOpponentEcmEmissionObserved = opponentEcmEmissionObserved;
        LastOpponentActiveSensorEmissionObserved = opponentActiveSensorEmissionObserved;
        LastFirmTrackDegradedByObservedEcm = firmTrackDegradedByObservedEcm;

        if (quality != TacticalTrackQuality.Firm)
        {
            ClosestOrdinaryTrackFailureRangeHexes = ClosestOrdinaryTrackFailureRangeHexes is int prior
                ? Math.Min(prior, rangeHexes)
                : rangeHexes;
        }
    }

    public void RecordOwnAttack(int rangeHexes)
    {
        ValidateRange(rangeHexes);
        MaximumOwnAttackRangeHexes = MaximumOwnAttackRangeHexes is int prior
            ? Math.Max(prior, rangeHexes)
            : rangeHexes;
    }

    public void RecordObservedOpponentAttack(int rangeHexes)
    {
        ValidateRange(rangeHexes);
        MaximumObservedOpponentAttackRangeHexes = MaximumObservedOpponentAttackRangeHexes is int prior
            ? Math.Max(prior, rangeHexes)
            : rangeHexes;
    }

    public void RecordOverloadFailure(
        TacticalEscalationKind kind,
        int rangeHexes,
        TacticalObservableStateSignature observableState)
    {
        ValidateRange(rangeHexes);
        ArgumentNullException.ThrowIfNull(observableState);
        _overloadFailures[kind] = new TacticalOverloadFailure(rangeHexes, observableState);
    }

    public bool HasOverloadFailure(TacticalEscalationKind kind) =>
        _overloadFailures.ContainsKey(kind);

    /// <summary>
    /// Records that this ship has exhausted the currently safe Strain envelope
    /// for an escalation. Under the current combat rules Strain does not recover
    /// during an engagement, so closer range or changed opponent emissions do not
    /// make another safe request legal. A future in-combat Strain-recovery mechanic
    /// must explicitly clear this state when it actually restores capability.
    /// </summary>
    public void RecordSafeStrainExhausted(TacticalEscalationKind kind) =>
        _safeStrainExhausted.Add(kind);

    public bool IsSafeStrainExhausted(TacticalEscalationKind kind) =>
        _safeStrainExhausted.Contains(kind);

    public int? OverloadFailureRange(TacticalEscalationKind kind) =>
        _overloadFailures.TryGetValue(kind, out TacticalOverloadFailure? failure) && failure is not null
            ? failure.RangeHexes
            : null;

    /// <summary>
    /// A failed overload is not repeated at the same or greater range while
    /// the observable tactical state is unchanged. A closer range or a
    /// materially changed observable state makes a new attempt reasonable.
    /// </summary>
    public bool CanAttemptOverload(
        TacticalEscalationKind kind,
        int currentRangeHexes,
        TacticalObservableStateSignature observableState)
    {
        ValidateRange(currentRangeHexes);
        ArgumentNullException.ThrowIfNull(observableState);
        if (IsSafeStrainExhausted(kind))
        {
            return false;
        }
        if (!_overloadFailures.TryGetValue(kind, out TacticalOverloadFailure? failure) || failure is null)
        {
            return true;
        }
        return currentRangeHexes < failure.RangeHexes ||
            failure.ObservableState != observableState;
    }

    private static void ValidateRange(int rangeHexes)
    {
        if (rangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(rangeHexes));
        }
    }
}

public enum TacticalEscalationKind
{
    EccmOverload,
    ActiveSensorOverload,
}

/// <summary>
/// Only observable opponent emissions plus the condition of the observer's
/// own relevant equipment are included. Exact opponent ratings are excluded.
/// </summary>
public sealed record TacticalObservableStateSignature(
    bool OpponentEcmEmissionObserved,
    bool OpponentActiveSensorEmissionObserved,
    ComponentCondition OwnEccmCondition,
    ComponentCondition OwnActiveSensorCondition);

public sealed record TacticalOverloadFailure(
    int RangeHexes,
    TacticalObservableStateSignature ObservableState);
