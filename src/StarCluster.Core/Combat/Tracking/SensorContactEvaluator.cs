using System;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Converts deterministic range, target signature, sensor mode, environment,
/// electronic warfare, and occlusion into a sensor observation. The final
/// quality decision is delegated to a replaceable resolution policy.
/// </summary>
public static class SensorContactEvaluator
{
    /// <summary>
    /// Backward-compatible neutral evaluation. Passive sensors, a neutral
    /// target signature, clear space, and no jamming reproduce the Checkpoint
    /// 13 behavior.
    /// </summary>
    public static TacticalTrackObservation Observe(
        SystemMap map,
        string targetId,
        HexCoord observerCoordinate,
        HexCoord targetCoordinate,
        SensorProfile sensorProfile,
        TacticalTrackSourceType sourceType = TacticalTrackSourceType.TacticalSensors) =>
        Evaluate(
            map,
            targetId,
            observerCoordinate,
            targetCoordinate,
            sensorProfile,
            SensorContactEvaluationContext.Neutral,
            sourceType: sourceType).Observation;

    public static SensorContactEvaluationResult Evaluate(
        SystemMap map,
        string targetId,
        HexCoord observerCoordinate,
        HexCoord targetCoordinate,
        SensorProfile sensorProfile,
        SensorContactEvaluationContext evaluationContext,
        ISensorContactResolutionPolicy? resolutionPolicy = null,
        TacticalTrackSourceType sourceType = TacticalTrackSourceType.TacticalSensors)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(sensorProfile);
        ArgumentNullException.ThrowIfNull(evaluationContext);

        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException("A target ID is required.", nameof(targetId));
        }

        int distance = observerCoordinate.DistanceTo(targetCoordinate);
        int observerModeModifier =
            evaluationContext.ObserverSensorMode == SensorMode.Active
                ? sensorProfile.ActiveModeRangeBonusHexes
                : 0;
        int signatureModifier = evaluationContext.TargetSignature
            .GetRangeModifier(evaluationContext.TargetSensorMode);
        int environmentPenalty =
            evaluationContext.Environment.RangePenaltyHexes;
        int rawJammingPenalty = evaluationContext.TargetJammingEnabled
            ? evaluationContext.TargetElectronicWarfare
                .JammingRangePenaltyHexes
            : 0;
        int counterJamming =
            evaluationContext.ObserverElectronicWarfare.CounterJammingStrength;
        int netJammingPenalty = Math.Max(
            0,
            rawJammingPenalty - counterJamming);
        int totalRangeModifier = checked(
            observerModeModifier +
            signatureModifier -
            environmentPenalty -
            netJammingPenalty);
        int effectiveFirmRange = Math.Max(
            0,
            checked(sensorProfile.FirmRangeHexes + totalRangeModifier));
        int effectiveApproximateRange = Math.Max(
            effectiveFirmRange,
            Math.Max(
                0,
                checked(
                    sensorProfile.ApproximateRangeHexes +
                    totalRangeModifier)));

        // A contact occupying the observer's own hex is necessarily locally
        // acquired. This remains a hard rule even under severe jamming.
        if (distance == 0)
        {
            return CreateResult(
                TacticalTrackObservation.Firm(
                    targetId,
                    targetCoordinate,
                    sourceType),
                SensorContactEvaluationStatus.Firm,
                distance,
                sensorProfile,
                observerModeModifier,
                signatureModifier,
                environmentPenalty,
                rawJammingPenalty,
                counterJamming,
                netJammingPenalty,
                effectiveFirmRange,
                effectiveApproximateRange,
                evaluationContext);
        }

        if (sensorProfile.RequiresLineOfSight)
        {
            DirectFireLineOfSightResult lineOfSight =
                DirectFireLineOfSight.Evaluate(
                    map,
                    observerCoordinate,
                    targetCoordinate);
            if (lineOfSight.Quality == LineOfSightQuality.Blocked)
            {
                return CreateResult(
                    TacticalTrackObservation.Missed(targetId, sourceType),
                    SensorContactEvaluationStatus.MissedOccluded,
                    distance,
                    sensorProfile,
                    observerModeModifier,
                    signatureModifier,
                    environmentPenalty,
                    rawJammingPenalty,
                    counterJamming,
                    netJammingPenalty,
                    effectiveFirmRange,
                    effectiveApproximateRange,
                    evaluationContext);
            }
        }

        ISensorContactResolutionPolicy policy = resolutionPolicy ??
            DeterministicSensorContactResolutionPolicy.Instance;
        SensorContactResolution resolution = policy.Resolve(
            new SensorContactResolutionContext(
                distance,
                effectiveFirmRange,
                effectiveApproximateRange));

        return resolution switch
        {
            SensorContactResolution.Firm => CreateResult(
                TacticalTrackObservation.Firm(
                    targetId,
                    targetCoordinate,
                    sourceType),
                SensorContactEvaluationStatus.Firm,
                distance,
                sensorProfile,
                observerModeModifier,
                signatureModifier,
                environmentPenalty,
                rawJammingPenalty,
                counterJamming,
                netJammingPenalty,
                effectiveFirmRange,
                effectiveApproximateRange,
                evaluationContext),
            SensorContactResolution.Approximate => CreateResult(
                TacticalTrackObservation.Approximate(
                    targetId,
                    targetCoordinate,
                    uncertaintyRadiusHexes: 1,
                    sourceType: sourceType),
                SensorContactEvaluationStatus.Approximate,
                distance,
                sensorProfile,
                observerModeModifier,
                signatureModifier,
                environmentPenalty,
                rawJammingPenalty,
                counterJamming,
                netJammingPenalty,
                effectiveFirmRange,
                effectiveApproximateRange,
                evaluationContext),
            SensorContactResolution.Missed => CreateResult(
                TacticalTrackObservation.Missed(targetId, sourceType),
                distance > effectiveApproximateRange
                    ? SensorContactEvaluationStatus.MissedOutOfRange
                    : SensorContactEvaluationStatus.MissedByPolicy,
                distance,
                sensorProfile,
                observerModeModifier,
                signatureModifier,
                environmentPenalty,
                rawJammingPenalty,
                counterJamming,
                netJammingPenalty,
                effectiveFirmRange,
                effectiveApproximateRange,
                evaluationContext),
            _ => throw new InvalidOperationException(
                $"Unsupported sensor resolution {resolution}."),
        };
    }

    private static SensorContactEvaluationResult CreateResult(
        TacticalTrackObservation observation,
        SensorContactEvaluationStatus status,
        int distance,
        SensorProfile sensorProfile,
        int observerModeModifier,
        int signatureModifier,
        int environmentPenalty,
        int rawJammingPenalty,
        int counterJamming,
        int netJammingPenalty,
        int effectiveFirmRange,
        int effectiveApproximateRange,
        SensorContactEvaluationContext evaluationContext) =>
        new(
            observation,
            status,
            distance,
            sensorProfile.FirmRangeHexes,
            sensorProfile.ApproximateRangeHexes,
            observerModeModifier,
            signatureModifier,
            environmentPenalty,
            rawJammingPenalty,
            counterJamming,
            netJammingPenalty,
            effectiveFirmRange,
            effectiveApproximateRange,
            evaluationContext);
}
