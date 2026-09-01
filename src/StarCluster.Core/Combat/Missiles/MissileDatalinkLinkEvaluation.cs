using System;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Geometric result for one launcher-to-missile datalink check.
/// </summary>
public sealed class MissileDatalinkLinkEvaluation
{
    internal MissileDatalinkLinkEvaluation(
        MissileDatalinkState state,
        HexCoord launcherCoordinate,
        HexCoord missileCoordinate,
        LineOfSightQuality? lineOfSightQuality)
    {
        if (!Enum.IsDefined(state))
        {
            throw new ArgumentOutOfRangeException(nameof(state));
        }

        State = state;
        LauncherCoordinate = launcherCoordinate;
        MissileCoordinate = missileCoordinate;
        LineOfSightQuality = lineOfSightQuality;
    }

    public MissileDatalinkState State { get; }

    public HexCoord LauncherCoordinate { get; }

    public HexCoord MissileCoordinate { get; }

    public LineOfSightQuality? LineOfSightQuality { get; }

    public bool IsLive => State == MissileDatalinkState.Live;
}
