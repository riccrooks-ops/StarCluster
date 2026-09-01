using System;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Simulation;

public sealed class ScenarioRetainedDatalinkDefinition
{
    public ScenarioRetainedDatalinkDefinition(
        MissileDatalinkState linkState,
        MissileTargetTrackQuality receivedQuality,
        HexCoord guidanceCoordinate,
        int sourceObservationEpoch = 1,
        int receivedGuidancePhase = 1,
        int uncertaintyRadiusHexes = 0,
        int agePhases = 0)
    {
        if (!Enum.IsDefined(linkState))
        {
            throw new ArgumentOutOfRangeException(nameof(linkState));
        }

        if (receivedQuality is MissileTargetTrackQuality.Lost ||
            !Enum.IsDefined(receivedQuality))
        {
            throw new ArgumentOutOfRangeException(nameof(receivedQuality));
        }

        if (sourceObservationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(sourceObservationEpoch));
        }

        if (receivedGuidancePhase <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(receivedGuidancePhase));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(uncertaintyRadiusHexes));
        }

        if (agePhases < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(agePhases));
        }

        LinkState = linkState;
        ReceivedQuality = receivedQuality;
        GuidanceCoordinate = guidanceCoordinate;
        SourceObservationEpoch = sourceObservationEpoch;
        ReceivedGuidancePhase = receivedGuidancePhase;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
        AgePhases = agePhases;
    }

    public MissileDatalinkState LinkState { get; }

    public MissileTargetTrackQuality ReceivedQuality { get; }

    public HexCoord GuidanceCoordinate { get; }

    public int SourceObservationEpoch { get; }

    public int ReceivedGuidancePhase { get; }

    public int UncertaintyRadiusHexes { get; }

    public int AgePhases { get; }
}
