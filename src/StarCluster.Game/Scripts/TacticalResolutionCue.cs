using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;

namespace StarCluster.Game;

/// <summary>
/// Short-lived observer-safe map feedback for a resolved tactical outcome.
/// </summary>
public sealed record TacticalResolutionCue(
    HexCoord Coordinate,
    TacticalSide Side,
    string Text);
