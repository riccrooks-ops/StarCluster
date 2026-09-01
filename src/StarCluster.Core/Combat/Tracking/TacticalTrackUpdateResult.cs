namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Immutable summary of one observer-target update.
/// </summary>
public sealed class TacticalTrackUpdateResult
{
    internal TacticalTrackUpdateResult(
        string observerId,
        string targetId,
        TrackUpdateTrigger trigger,
        TacticalTrackQuality? previousQuality,
        TacticalTrackRecord? record,
        bool created,
        int observationEpoch,
        bool ageAdvanced)
    {
        ObserverId = observerId;
        TargetId = targetId;
        Trigger = trigger;
        PreviousQuality = previousQuality;
        Record = record;
        Created = created;
        ObservationEpoch = observationEpoch;
        AgeAdvanced = ageAdvanced;
    }

    public string ObserverId { get; }

    public string TargetId { get; }

    public TrackUpdateTrigger Trigger { get; }

    public TacticalTrackQuality? PreviousQuality { get; }

    public TacticalTrackRecord? Record { get; }

    public TacticalTrackQuality? CurrentQuality => Record?.Quality;

    public bool Created { get; }

    /// <summary>
    /// Observation epoch used for this reevaluation. The prototype supplies the
    /// tactical turn number.
    /// </summary>
    public int ObservationEpoch { get; }

    /// <summary>
    /// True only when this missed observation consumed the epoch's one allowed
    /// age step for the observer-target pair.
    /// </summary>
    public bool AgeAdvanced { get; }

    public bool RemainsUnknown => Record is null;
}
