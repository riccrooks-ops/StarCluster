using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Complete deterministic evidence for one contact evaluation. The track
/// manager consumes Observation; diagnostics and UI may explain the modifiers
/// without recomputing hidden authoritative state.
/// </summary>
public sealed class SensorContactEvaluationResult
{
    internal SensorContactEvaluationResult(
        TacticalTrackObservation observation,
        SensorContactEvaluationStatus status,
        int distanceHexes,
        int baseFirmRangeHexes,
        int baseApproximateRangeHexes,
        int observerModeRangeModifierHexes,
        int targetSignatureRangeModifierHexes,
        int environmentRangePenaltyHexes,
        int rawJammingRangePenaltyHexes,
        int counterJammingStrength,
        int netJammingRangePenaltyHexes,
        int effectiveFirmRangeHexes,
        int effectiveApproximateRangeHexes,
        SensorContactEvaluationContext context)
    {
        Observation = observation ??
            throw new ArgumentNullException(nameof(observation));
        Context = context ?? throw new ArgumentNullException(nameof(context));
        Status = status;
        DistanceHexes = distanceHexes;
        BaseFirmRangeHexes = baseFirmRangeHexes;
        BaseApproximateRangeHexes = baseApproximateRangeHexes;
        ObserverModeRangeModifierHexes = observerModeRangeModifierHexes;
        TargetSignatureRangeModifierHexes =
            targetSignatureRangeModifierHexes;
        EnvironmentRangePenaltyHexes = environmentRangePenaltyHexes;
        RawJammingRangePenaltyHexes = rawJammingRangePenaltyHexes;
        CounterJammingStrength = counterJammingStrength;
        NetJammingRangePenaltyHexes = netJammingRangePenaltyHexes;
        EffectiveFirmRangeHexes = effectiveFirmRangeHexes;
        EffectiveApproximateRangeHexes = effectiveApproximateRangeHexes;
    }

    public TacticalTrackObservation Observation { get; }

    public SensorContactEvaluationStatus Status { get; }

    public int DistanceHexes { get; }

    public int BaseFirmRangeHexes { get; }

    public int BaseApproximateRangeHexes { get; }

    public int ObserverModeRangeModifierHexes { get; }

    public int TargetSignatureRangeModifierHexes { get; }

    public int EnvironmentRangePenaltyHexes { get; }

    public int RawJammingRangePenaltyHexes { get; }

    public int CounterJammingStrength { get; }

    public int NetJammingRangePenaltyHexes { get; }

    public int EffectiveFirmRangeHexes { get; }

    public int EffectiveApproximateRangeHexes { get; }

    public SensorContactEvaluationContext Context { get; }
}
