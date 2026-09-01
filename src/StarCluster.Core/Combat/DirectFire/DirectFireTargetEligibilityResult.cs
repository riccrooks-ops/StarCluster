using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// Engine-independent result used by both command validation and presentation.
/// AccuracyModifier contains the universal track/range modifier for the current
/// ship attack: -25 pp for Approximate track, -10 pp for extended range, and
/// -35 pp when both apply. Firm fire within Standard Range is zero.
/// </summary>
public sealed record DirectFireTargetEligibilityResult(
    DirectFireTargetEligibilityStatus Status,
    HexCoord? TargetCoordinate,
    int? DistanceHexes,
    bool UsesApproximateTrackFire = false,
    int AccuracyModifier = 0,
    bool UsesExtendedRangeFire = false)
{
    public bool CanCommitNow =>
        Status == DirectFireTargetEligibilityStatus.EligibleNow;

    public bool CanCommitSpecificMissileOrder =>
        Status == DirectFireTargetEligibilityStatus.EligibleNow ||
        Status == DirectFireTargetEligibilityStatus.EligibleForSpecificMissileReserve;

    public bool IsReserveOnly =>
        Status == DirectFireTargetEligibilityStatus.EligibleForSpecificMissileReserve;
}
