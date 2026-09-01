using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// One coordinate that an observer actually confirmed. Segment identity is
/// explicit so a loss and reacquisition during the same tactical turn can never
/// be rendered as continuous movement.
/// </summary>
public sealed record ObservedTrackSample(
    HexCoord Coordinate,
    int ObservationEpoch,
    int SegmentId = 0,
    long ObservationSequence = 0);
