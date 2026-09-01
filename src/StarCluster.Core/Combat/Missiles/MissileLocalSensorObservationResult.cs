using System;
using StarCluster.Core.Combat.Tracking;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Complete result of one missile-local sensor opportunity.
/// </summary>
public sealed class MissileLocalSensorObservationResult
{
    internal MissileLocalSensorObservationResult(
        SensorContactEvaluationResult? passiveEvaluation,
        SensorContactEvaluationResult? finalEvaluation,
        SensorMode sensorMode,
        bool activeEscalated,
        bool sameEpochVisibilityLoss,
        bool ageAdvanced,
        MissileLocalTrackReport? trackReport)
    {
        PassiveEvaluation = passiveEvaluation;
        FinalEvaluation = finalEvaluation;
        SensorMode = sensorMode;
        ActiveEscalated = activeEscalated;
        SameEpochVisibilityLoss = sameEpochVisibilityLoss;
        AgeAdvanced = ageAdvanced;
        TrackReport = trackReport;
    }

    public SensorContactEvaluationResult? PassiveEvaluation { get; }

    public SensorContactEvaluationResult? FinalEvaluation { get; }

    public SensorMode SensorMode { get; }

    public bool ActiveEscalated { get; }

    public bool SameEpochVisibilityLoss { get; }

    public bool AgeAdvanced { get; }

    public MissileLocalTrackReport? TrackReport { get; }

    public bool HasUsableTrack => TrackReport is not null;
}
