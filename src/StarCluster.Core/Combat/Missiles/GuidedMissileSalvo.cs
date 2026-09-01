using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Authoritative lifetime state for an in-flight Missile Flight that may replace
/// its future route as the target track changes. Cumulative movement and
/// stationary-search fuel expenditure never reset when a new route is planned.
/// </summary>
public sealed class GuidedMissileSalvo
{
    private readonly List<HexCoord> _travelHistory = new();
    private readonly IReadOnlyList<HexCoord> _travelHistoryView;

    /// <summary>
    /// Compatibility constructor for pre-ownership callers. New combat code
    /// should provide a concrete tactical side through the ownership overload.
    /// </summary>
    public GuidedMissileSalvo(
        string id,
        string launcherId,
        string targetId,
        HexCoord launchCoordinate,
        MissileFlightProfile profile)
        : this(
            id,
            TacticalSide.Unspecified,
            launcherId,
            targetId,
            launchCoordinate,
            profile,
            MissileTerminalProfile.Prototype)
    {
    }

    public GuidedMissileSalvo(
        string id,
        TacticalSide ownerSide,
        string launcherId,
        string targetId,
        HexCoord launchCoordinate,
        MissileFlightProfile profile)
        : this(
            id,
            ownerSide,
            launcherId,
            targetId,
            launchCoordinate,
            profile,
            MissileTerminalProfile.Prototype)
    {
    }

    public GuidedMissileSalvo(
        string id,
        TacticalSide ownerSide,
        string launcherId,
        string targetId,
        HexCoord launchCoordinate,
        MissileFlightProfile profile,
        MissileTerminalProfile terminalProfile)
    {
        ValidateId(id, nameof(id));
        ValidateId(launcherId, nameof(launcherId));
        ValidateId(targetId, nameof(targetId));
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(terminalProfile);

        if (!Enum.IsDefined(ownerSide))
        {
            throw new ArgumentOutOfRangeException(
                nameof(ownerSide),
                ownerSide,
                null);
        }

        Id = id;
        OwnerSide = ownerSide;
        LauncherId = launcherId;
        TargetId = targetId;
        LaunchCoordinate = launchCoordinate;
        CurrentCoordinate = launchCoordinate;
        Profile = profile;
        TerminalProfile = terminalProfile;
        Status = GuidedMissileStatus.InFlight;
        TerminalState = MissileTerminalState.None;
        DatalinkState = MissileDatalinkState.Unavailable;
        LastGuidanceSource = MissileGuidanceReportSource.None;
        _travelHistory.Add(launchCoordinate);
        _travelHistoryView = _travelHistory.AsReadOnly();
    }

    public string Id { get; }

    public TacticalSide OwnerSide { get; }

    public string LauncherId { get; }

    public string TargetId { get; }

    public HexCoord LaunchCoordinate { get; }

    public HexCoord CurrentCoordinate { get; private set; }

    public MissileFlightProfile Profile { get; }

    public MissileTerminalProfile TerminalProfile { get; }

    public GuidedMissileStatus Status { get; private set; }

    public MissileTerminalState TerminalState { get; private set; }

    public MissileTerminalResolution? LastTerminalResolution { get; private set; }

    public HexCoord? TerminalOpportunityCoordinate { get; private set; }

    public bool TerminalEntryDefenseResolved { get; private set; }

    public int DistanceTraveled { get; private set; }

    public int StationarySearchFuelSpent { get; private set; }

    public int TotalFuelSpent => checked(
        DistanceTraveled + StationarySearchFuelSpent);

    public int RemainingRange => Math.Max(
        0,
        Profile.MaximumRange - TotalFuelSpent);

    public int GuidancePhaseCount { get; private set; }

    public HexCoord? CurrentTrackedTargetCoordinate { get; private set; }

    public HexCoord? LastKnownTargetCoordinate { get; private set; }

    public MissileTargetTrackQuality? LastTrackQuality { get; private set; }

    public MissileRouteResult? LastRoutePlan { get; private set; }

    public MissileDatalinkState DatalinkState { get; private set; }

    public MissileDatalinkReport? RetainedDatalinkReport { get; private set; }

    public MissileLocalTrackReport? LocalSensorTrack { get; private set; }

    public MissileGuidanceReportSource LastGuidanceSource { get; private set; }

    public string LastGuidanceDecisionReason { get; private set; } =
        "No guidance decision has been made.";

    public int? LastDatalinkEvaluationGuidancePhase { get; private set; }

    public IReadOnlyList<HexCoord> TravelHistory => _travelHistoryView;

    public string? InterceptedByDefenseSystemId { get; private set; }

    public bool HasTerminalOpportunity =>
        TerminalOpportunityCoordinate.HasValue;

    public bool IsTerminal => Status is
        GuidedMissileStatus.Expended or
        GuidedMissileStatus.Dud or
        GuidedMissileStatus.RangeExhausted or
        GuidedMissileStatus.Intercepted or
        GuidedMissileStatus.SelfDestructed or
        GuidedMissileStatus.Destroyed;

    public void MarkIntercepted() => MarkIntercepted(defenseSystemId: null);

    public void MarkIntercepted(string? defenseSystemId)
    {
        if (IsTerminal)
        {
            return;
        }

        if (defenseSystemId is not null)
        {
            ValidateId(defenseSystemId, nameof(defenseSystemId));
        }

        InterceptedByDefenseSystemId = defenseSystemId;
        Status = GuidedMissileStatus.Intercepted;
        TerminalState = MissileTerminalState.Resolved;
        if (LastTerminalResolution is not null)
        {
            LastTerminalResolution = LastTerminalResolution.WithOutcome(
                MissileTerminalOutcome.Intercepted,
                "The Missile Flight was intercepted before its terminal attack roll.");
        }
        else if (TerminalOpportunityCoordinate.HasValue)
        {
            LastTerminalResolution = new MissileTerminalResolution(
                TerminalOpportunityCoordinate.Value,
                LastGuidanceSource,
                LastTrackQuality ?? MissileTargetTrackQuality.Lost,
                targetCoLocated: true,
                usedSeekerAcquisition: false,
                acquisitionRoll: null,
                acquisitionChancePercent: null,
                hasFirmSolution: false,
                seekerAccuracyApplied: false,
                attackRoll: null,
                effectiveHitChancePercent: null,
                MissileTerminalOutcome.Intercepted,
                "The Missile Flight was intercepted at terminal entry before acquisition.");
        }
    }

    public void MarkDestroyed()
    {
        if (!IsTerminal)
        {
            Status = GuidedMissileStatus.Destroyed;
            TerminalState = MissileTerminalState.Resolved;
        }
    }

    internal void RestoreGuidancePhaseCount(int guidancePhaseCount)
    {
        if (guidancePhaseCount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(guidancePhaseCount));
        }

        if (guidancePhaseCount < GuidancePhaseCount)
        {
            throw new InvalidOperationException(
                "A restored guidance-phase count cannot move backward.");
        }

        GuidancePhaseCount = guidancePhaseCount;
    }

    internal void BeginGuidancePhase(MissileTargetTrackSnapshot track)
    {
        ArgumentNullException.ThrowIfNull(track);
        GuidancePhaseCount++;
        ApplyGuidanceTrack(track);
    }

    internal void ApplyGuidanceTrack(MissileTargetTrackSnapshot track)
    {
        ArgumentNullException.ThrowIfNull(track);
        LastTrackQuality = track.Quality;

        switch (track.Quality)
        {
            case MissileTargetTrackQuality.Current:
                CurrentTrackedTargetCoordinate = track.CurrentCoordinate;
                LastKnownTargetCoordinate = track.CurrentCoordinate;
                break;
            case MissileTargetTrackQuality.Approximate:
                CurrentTrackedTargetCoordinate = null;
                LastKnownTargetCoordinate = track.EstimatedCoordinate;
                break;
            case MissileTargetTrackQuality.Stale:
                CurrentTrackedTargetCoordinate = null;
                LastKnownTargetCoordinate = track.LastKnownCoordinate;
                break;
            case MissileTargetTrackQuality.Lost:
                CurrentTrackedTargetCoordinate = null;
                break;
        }
    }

    internal void SetLocalSensorTrack(MissileLocalTrackReport? track)
    {
        if (track is not null &&
            !string.Equals(track.TargetId, TargetId, StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "The local sensor track belongs to a different target.",
                nameof(track));
        }

        LocalSensorTrack = track;
    }

    internal void SetGuidanceDecision(MissileGuidanceDecision decision)
    {
        ArgumentNullException.ThrowIfNull(decision);
        if (!string.Equals(decision.TargetId, TargetId, StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "The guidance decision belongs to a different target.",
                nameof(decision));
        }

        LastGuidanceSource = decision.SelectedSource;
        LastGuidanceDecisionReason = decision.Reason;
        ApplyGuidanceTrack(decision.SelectedSnapshot);
    }

    internal void SetRoutePlan(MissileRouteResult? routePlan) =>
        LastRoutePlan = routePlan;

    internal void SetDatalinkState(MissileDatalinkState state)
    {
        if (!Enum.IsDefined(state))
        {
            throw new ArgumentOutOfRangeException(nameof(state));
        }

        DatalinkState = state;
    }

    internal void ApplyDatalinkEvaluation(
        int guidancePhaseNumber,
        MissileDatalinkState state,
        MissileDatalinkReport? retainedReport)
    {
        if (guidancePhaseNumber <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(guidancePhaseNumber));
        }

        if (!Enum.IsDefined(state))
        {
            throw new ArgumentOutOfRangeException(nameof(state));
        }

        if (LastDatalinkEvaluationGuidancePhase.HasValue &&
            guidancePhaseNumber < LastDatalinkEvaluationGuidancePhase.Value)
        {
            throw new InvalidOperationException(
                "Datalink guidance phases cannot move backward.");
        }

        if (retainedReport is not null &&
            !string.Equals(
                retainedReport.TargetId,
                TargetId,
                StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "The retained datalink report belongs to a different target.",
                nameof(retainedReport));
        }

        DatalinkState = state;
        RetainedDatalinkReport = retainedReport;
        LastDatalinkEvaluationGuidancePhase = guidancePhaseNumber;
    }

    internal void MoveThrough(IReadOnlyList<HexCoord> enteredCoordinates)
    {
        ArgumentNullException.ThrowIfNull(enteredCoordinates);

        foreach (HexCoord coordinate in enteredCoordinates)
        {
            if (RemainingRange == 0)
            {
                throw new InvalidOperationException(
                    "A Missile Flight cannot move after exhausting its fuel/range budget.");
            }

            CurrentCoordinate = coordinate;
            DistanceTraveled++;
            _travelHistory.Add(coordinate);

            if (TerminalOpportunityCoordinate.HasValue &&
                TerminalOpportunityCoordinate.Value != coordinate)
            {
                ClearTerminalOpportunity();
            }
        }
    }

    internal bool SpendStationarySearchFuel()
    {
        if (IsTerminal || RemainingRange == 0)
        {
            return false;
        }

        int cost = TerminalProfile.StationarySearchFuelCost;
        int spend = Math.Min(cost, RemainingRange);
        StationarySearchFuelSpent = checked(
            StationarySearchFuelSpent + spend);
        return spend > 0;
    }

    internal bool BeginTerminalOpportunity(HexCoord coordinate)
    {
        bool isNew =
            !TerminalOpportunityCoordinate.HasValue ||
            TerminalOpportunityCoordinate.Value != coordinate ||
            TerminalState == MissileTerminalState.None;
        if (isNew)
        {
            TerminalOpportunityCoordinate = coordinate;
            TerminalEntryDefenseResolved = false;
        }

        TerminalState = MissileTerminalState.Opportunity;
        return isNew;
    }

    internal void MarkTerminalEntryDefenseResolved() =>
        TerminalEntryDefenseResolved = true;

    internal void RecordTerminalAcquisition(
        MissileTerminalResolution resolution)
    {
        ArgumentNullException.ThrowIfNull(resolution);
        LastTerminalResolution = resolution;
        TerminalState = resolution.HasFirmSolution
            ? MissileTerminalState.FirmSolution
            : MissileTerminalState.SearchWait;
        if (!resolution.HasFirmSolution)
        {
            Status = GuidedMissileStatus.Searching;
        }
    }

    internal void RecordTerminalAttack(MissileTerminalResolution resolution)
    {
        ArgumentNullException.ThrowIfNull(resolution);
        LastTerminalResolution = resolution;
        TerminalState = MissileTerminalState.Resolved;
        Status = resolution.Outcome switch
        {
            MissileTerminalOutcome.Dud => GuidedMissileStatus.Dud,
            MissileTerminalOutcome.Miss or
            MissileTerminalOutcome.Hit or
            MissileTerminalOutcome.CriticalHit => GuidedMissileStatus.Expended,
            _ => throw new ArgumentException(
                "The supplied terminal resolution does not contain a final attack outcome.",
                nameof(resolution)),
        };
    }

    internal void EnterSearchWait(MissileTerminalResolution resolution)
    {
        RecordTerminalAcquisition(resolution);
        if (RemainingRange == 0)
        {
            MarkSelfDestructed(
                "No fuel remained after the failed terminal opportunity.");
        }
    }

    internal void MarkSelfDestructed(string reason)
    {
        MissileTerminalResolution baseResolution = LastTerminalResolution ??
            new MissileTerminalResolution(
                CurrentCoordinate,
                LastGuidanceSource,
                LastTrackQuality ?? MissileTargetTrackQuality.Lost,
                targetCoLocated: false,
                usedSeekerAcquisition: false,
                acquisitionRoll: null,
                acquisitionChancePercent: null,
                hasFirmSolution: false,
                seekerAccuracyApplied: false,
                attackRoll: null,
                effectiveHitChancePercent: null,
                MissileTerminalOutcome.AcquisitionFailed,
                "No terminal acquisition was recorded.");
        LastTerminalResolution = baseResolution.WithOutcome(
            MissileTerminalOutcome.SelfDestructed,
            reason);
        Status = GuidedMissileStatus.SelfDestructed;
        TerminalState = MissileTerminalState.Resolved;
    }

    internal void ClearTerminalOpportunity()
    {
        TerminalOpportunityCoordinate = null;
        TerminalEntryDefenseResolved = false;
        TerminalState = MissileTerminalState.None;
        LastTerminalResolution = null;
        if (!IsTerminal && Status == GuidedMissileStatus.Searching)
        {
            Status = GuidedMissileStatus.InFlight;
        }
    }

    internal void SetStatus(GuidedMissileStatus status)
    {
        if (!Enum.IsDefined(status))
        {
            throw new ArgumentOutOfRangeException(nameof(status));
        }

        Status = status;
    }

    private static void ValidateId(string id, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException(
                "A stable non-empty ID is required.",
                parameterName);
        }
    }
}
