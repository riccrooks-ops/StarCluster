using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

internal sealed class ScenarioMissileDefenseTrackProvider : IMissileDefenseTrackProvider
{
    private readonly ScenarioInitializationResult _runtime;

    public ScenarioMissileDefenseTrackProvider(ScenarioInitializationResult runtime)
    {
        _runtime = runtime ?? throw new ArgumentNullException(nameof(runtime));
    }

    public bool HasUsableTrack(
        MissileDefenseSystem defenseSystem,
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate)
    {
        TacticalTrackRecord? track = _runtime.Tracks.Get(
            defenseSystem.DefenderShipId,
            salvo.Id);
        return track is
        {
            Quality: TacticalTrackQuality.Firm,
            EstimatedCoordinate: { } coordinate,
        } && coordinate == missileCoordinate;
    }
}
