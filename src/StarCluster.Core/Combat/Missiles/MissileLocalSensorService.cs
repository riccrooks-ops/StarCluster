using System;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Evaluates a missile's onboard navigation sensor. Every opportunity begins
/// passive. Active mode is attempted only when passive sensing produced no
/// usable contact and the profile permits active emissions.
/// </summary>
public static class MissileLocalSensorService
{
    public static MissileLocalSensorObservationResult Observe(
        SystemMap map,
        string missileId,
        string targetId,
        HexCoord missileCoordinate,
        HexCoord targetCoordinate,
        MissileSensorProfile profile,
        MissileLocalTrackReport? previousTrack,
        SensorSignatureProfile targetSignature,
        SensorMode targetSensorMode,
        ElectronicWarfareProfile targetElectronicWarfare,
        bool targetJammingEnabled,
        SensorEnvironmentProfile environment,
        int observationEpoch)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(targetSignature);
        ArgumentNullException.ThrowIfNull(targetElectronicWarfare);
        ArgumentNullException.ThrowIfNull(environment);

        if (string.IsNullOrWhiteSpace(missileId))
        {
            throw new ArgumentException(
                "A missile ID is required.",
                nameof(missileId));
        }

        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException(
                "A target ID is required.",
                nameof(targetId));
        }

        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }

        if (!profile.IsInstalled)
        {
            return new MissileLocalSensorObservationResult(
                passiveEvaluation: null,
                finalEvaluation: null,
                SensorMode.Passive,
                activeEscalated: false,
                sameEpochVisibilityLoss: false,
                ageAdvanced: false,
                trackReport: null);
        }

        SensorContactEvaluationResult passive = Evaluate(
            map,
            targetId,
            missileCoordinate,
            targetCoordinate,
            profile,
            SensorMode.Passive,
            targetSignature,
            targetSensorMode,
            targetElectronicWarfare,
            targetJammingEnabled,
            environment);

        bool activeEscalated =
            !passive.Observation.Detected &&
            profile.AllowsActiveMode &&
            profile.Sensor.ActiveModeRangeBonusHexes > 0;
        SensorContactEvaluationResult finalEvaluation = activeEscalated
            ? Evaluate(
                map,
                targetId,
                missileCoordinate,
                targetCoordinate,
                profile,
                SensorMode.Active,
                targetSignature,
                targetSensorMode,
                targetElectronicWarfare,
                targetJammingEnabled,
                environment)
            : passive;
        SensorMode mode = activeEscalated
            ? SensorMode.Active
            : SensorMode.Passive;

        bool sameEpochVisibilityLoss = false;
        bool ageAdvanced = false;
        MissileLocalTrackReport? track;
        TacticalTrackObservation observation = finalEvaluation.Observation;
        if (observation.Detected && observation.EstimatedCoordinate.HasValue)
        {
            track = new MissileLocalTrackReport(
                targetId,
                observation.Precise
                    ? MissileTargetTrackQuality.Current
                    : MissileTargetTrackQuality.Approximate,
                observation.EstimatedCoordinate.Value,
                observationEpoch,
                observation.UncertaintyRadiusHexes,
                mode,
                ageEpochs: 0,
                lastAgedObservationEpoch: null);
        }
        else if (previousTrack is null)
        {
            track = null;
        }
        else if (previousTrack.SourceObservationEpoch == observationEpoch)
        {
            sameEpochVisibilityLoss = true;
            track = new MissileLocalTrackReport(
                targetId,
                MissileTargetTrackQuality.Stale,
                previousTrack.GuidanceCoordinate,
                previousTrack.SourceObservationEpoch,
                Math.Max(1, previousTrack.UncertaintyRadiusHexes),
                previousTrack.SensorMode,
                previousTrack.AgeEpochs,
                previousTrack.LastAgedObservationEpoch);
        }
        else if (previousTrack.LastAgedObservationEpoch == observationEpoch)
        {
            track = previousTrack;
        }
        else
        {
            int newAge = checked(previousTrack.AgeEpochs + 1);
            ageAdvanced = true;
            track = newAge > profile.MaximumLocalTrackAgeEpochs
                ? null
                : new MissileLocalTrackReport(
                    targetId,
                    MissileTargetTrackQuality.Stale,
                    previousTrack.GuidanceCoordinate,
                    previousTrack.SourceObservationEpoch,
                    Math.Max(
                        1,
                        checked(
                            previousTrack.UncertaintyRadiusHexes + 1)),
                    previousTrack.SensorMode,
                    newAge,
                    observationEpoch);
        }

        return new MissileLocalSensorObservationResult(
            passive,
            finalEvaluation,
            mode,
            activeEscalated,
            sameEpochVisibilityLoss,
            ageAdvanced,
            track);
    }

    private static SensorContactEvaluationResult Evaluate(
        SystemMap map,
        string targetId,
        HexCoord missileCoordinate,
        HexCoord targetCoordinate,
        MissileSensorProfile profile,
        SensorMode observerMode,
        SensorSignatureProfile targetSignature,
        SensorMode targetSensorMode,
        ElectronicWarfareProfile targetElectronicWarfare,
        bool targetJammingEnabled,
        SensorEnvironmentProfile environment) =>
        SensorContactEvaluator.Evaluate(
            map,
            targetId,
            missileCoordinate,
            targetCoordinate,
            profile.Sensor,
            new SensorContactEvaluationContext(
                observerMode,
                targetSignature,
                targetSensorMode,
                ElectronicWarfareProfile.None,
                targetElectronicWarfare,
                targetJammingEnabled,
                environment),
            sourceType: TacticalTrackSourceType.MissileOnboardSensor);
}
