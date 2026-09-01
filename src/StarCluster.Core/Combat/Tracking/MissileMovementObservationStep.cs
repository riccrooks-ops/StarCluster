using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Observer-safe result for one launch-origin or entered-hex detection check.
/// It records only what the observer could establish at that coordinate.
/// </summary>
public sealed record MissileMovementObservationStep(
    HexCoord Coordinate,
    bool IsLaunchOrigin,
    bool Detected,
    bool SegmentStarted,
    bool SegmentExtended,
    bool SegmentClosed,
    TacticalTrackQuality? TrackQuality);
