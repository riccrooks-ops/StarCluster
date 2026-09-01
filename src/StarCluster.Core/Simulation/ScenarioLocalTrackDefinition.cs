using System;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Simulation;

public sealed class ScenarioLocalTrackDefinition
{
    public ScenarioLocalTrackDefinition(
        MissileTargetTrackQuality quality,
        HexCoord guidanceCoordinate,
        int sourceObservationEpoch = 1,
        int uncertaintyRadiusHexes = 0,
        SensorMode sensorMode = SensorMode.Passive,
        int ageEpochs = 0,
        int? lastAgedObservationEpoch = null)
    {
        if (quality is MissileTargetTrackQuality.Lost || !Enum.IsDefined(quality))
        {
            throw new ArgumentOutOfRangeException(nameof(quality));
        }

        if (sourceObservationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(sourceObservationEpoch));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(uncertaintyRadiusHexes));
        }

        if (!Enum.IsDefined(sensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(sensorMode));
        }

        if (ageEpochs < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(ageEpochs));
        }

        Quality = quality;
        GuidanceCoordinate = guidanceCoordinate;
        SourceObservationEpoch = sourceObservationEpoch;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
        SensorMode = sensorMode;
        AgeEpochs = ageEpochs;
        LastAgedObservationEpoch = lastAgedObservationEpoch;
    }

    public MissileTargetTrackQuality Quality { get; }

    public HexCoord GuidanceCoordinate { get; }

    public int SourceObservationEpoch { get; }

    public int UncertaintyRadiusHexes { get; }

    public SensorMode SensorMode { get; }

    public int AgeEpochs { get; }

    public int? LastAgedObservationEpoch { get; }
}
