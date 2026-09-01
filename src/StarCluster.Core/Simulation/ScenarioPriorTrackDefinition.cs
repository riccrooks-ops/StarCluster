using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Simulation;

/// <summary>
/// Fragmentary pre-encounter intelligence applied before the normal system-entry sensor pass.
/// </summary>
public sealed class ScenarioPriorTrackDefinition
{
    public ScenarioPriorTrackDefinition(
        string observerId,
        string targetId,
        HexCoord lastKnownCoordinate,
        int uncertaintyRadiusHexes = 1)
    {
        if (string.IsNullOrWhiteSpace(observerId))
        {
            throw new ArgumentException("An observer ID is required.", nameof(observerId));
        }

        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException("A target ID is required.", nameof(targetId));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(uncertaintyRadiusHexes));
        }

        ObserverId = observerId;
        TargetId = targetId;
        LastKnownCoordinate = lastKnownCoordinate;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
    }

    public string ObserverId { get; }

    public string TargetId { get; }

    public HexCoord LastKnownCoordinate { get; }

    public int UncertaintyRadiusHexes { get; }
}
