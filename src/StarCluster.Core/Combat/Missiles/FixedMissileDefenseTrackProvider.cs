using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Deterministic test provider for tactical interception acquisition.
/// </summary>
public sealed class FixedMissileDefenseTrackProvider : IMissileDefenseTrackProvider
{
    public FixedMissileDefenseTrackProvider(bool hasUsableTrack)
    {
        HasTrack = hasUsableTrack;
    }

    public bool HasTrack { get; }

    public bool HasUsableTrack(
        MissileDefenseSystem defenseSystem,
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate) => HasTrack;
}
