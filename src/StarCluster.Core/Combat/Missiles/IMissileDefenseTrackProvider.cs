using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Supplies acquisition eligibility to defensive systems that require a Firm
/// tactical track. Local PDS acquisition bypasses this tactical-track gate.
/// </summary>
public interface IMissileDefenseTrackProvider
{
    bool HasUsableTrack(
        MissileDefenseSystem defenseSystem,
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate);
}
