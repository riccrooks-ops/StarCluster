namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Player-facing quality of one observer's information about one contact.
/// An unknown contact has no track record at all.
/// </summary>
public enum TacticalTrackQuality
{
    Firm,
    Approximate,
    Stale,
    Lost,
}
