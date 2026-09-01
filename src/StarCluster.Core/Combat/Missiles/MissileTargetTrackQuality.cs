namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Describes the target coordinate supplied to one missile guidance pass.
/// Current is a precise Firm tactical track retained for compatibility.
/// </summary>
public enum MissileTargetTrackQuality
{
    Current,
    Approximate,
    Stale,
    Lost,
}
