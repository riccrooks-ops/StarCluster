using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Deterministic sensor/EW foundation that separates physical sensing reach
/// from electronic-warfare discrimination effects.
/// It is intentionally compact: a profile has one passive envelope, one
/// normal active envelope, and one bounded active-overload extension.
/// </summary>
public sealed record SensorEwFoundationProfile
{
    public SensorEwFoundationProfile(
        string id,
        int passiveFirmRange,
        int passiveApproximateRange,
        int activeFirmRange,
        int activeApproximateRange,
        int activePowerCost,
        int activeOverloadAdditionalPowerCost,
        int activeOverloadFirmBonus,
        int activeOverloadApproximateBonus,
        int discriminationResistance = 0,
        int pointBlankBurnThroughResistance = 0)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("A sensor/EW foundation profile ID is required.", nameof(id));
        }
        if (passiveFirmRange < 0 || passiveApproximateRange < passiveFirmRange)
        {
            throw new ArgumentOutOfRangeException(nameof(passiveApproximateRange));
        }
        if (activeFirmRange < passiveFirmRange ||
            activeApproximateRange < activeFirmRange ||
            activeApproximateRange < passiveApproximateRange)
        {
            throw new ArgumentOutOfRangeException(nameof(activeApproximateRange));
        }
        if (activePowerCost <= 0 || activeOverloadAdditionalPowerCost < 0 ||
            activeOverloadFirmBonus < 0 || activeOverloadApproximateBonus < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(activePowerCost));
        }
        if (discriminationResistance < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(discriminationResistance));
        }

        if (pointBlankBurnThroughResistance < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(pointBlankBurnThroughResistance));
        }

        Id = id;
        PassiveFirmRange = passiveFirmRange;
        PassiveApproximateRange = passiveApproximateRange;
        ActiveFirmRange = activeFirmRange;
        ActiveApproximateRange = activeApproximateRange;
        ActivePowerCost = activePowerCost;
        ActiveOverloadAdditionalPowerCost = activeOverloadAdditionalPowerCost;
        ActiveOverloadFirmBonus = activeOverloadFirmBonus;
        ActiveOverloadApproximateBonus = activeOverloadApproximateBonus;
        DiscriminationResistance = discriminationResistance;
        PointBlankBurnThroughResistance = pointBlankBurnThroughResistance;
    }

    public string Id { get; }
    public int PassiveFirmRange { get; }
    public int PassiveApproximateRange { get; }
    public int ActiveFirmRange { get; }
    public int ActiveApproximateRange { get; }
    public int ActivePowerCost { get; }
    public int ActiveOverloadAdditionalPowerCost { get; }
    public int ActiveOverloadFirmBonus { get; }
    public int ActiveOverloadApproximateBonus { get; }
    public int DiscriminationResistance { get; }
    public int PointBlankBurnThroughResistance { get; }
}

public enum SensorEwFoundationTrackState
{
    None,
    Approximate,
    Firm,
}

[Flags]
public enum SensorEwEmissionSource
{
    None = 0,
    ActiveSensors = 1,
    ElectronicCountermeasures = 2,
}

public sealed record SensorEwFoundationEvaluationContext(
    SensorMode ObserverSensorMode,
    bool ObserverActiveSensorOverloaded = false,
    bool TargetActiveSensorsEnabled = false,
    bool TargetActiveSensorOverloaded = false,
    int TargetEcmRating = 0,
    int ObserverEccmRating = 0,
    bool HasLineOfSight = true);

public sealed record SensorEwFoundationEvaluationResult(
    int DistanceHexes,
    SensorEwFoundationTrackState BaselineTrack,
    SensorEwFoundationTrackState EmissionAssistedTrack,
    SensorEwFoundationTrackState FinalTrack,
    SensorEwEmissionSource EmissionSources,
    int ObserverFirmRange,
    int ObserverApproximateRange,
    int ActiveEmissionInterceptRange,
    int TargetEcmRating,
    int ObserverEccmRating,
    int NetEcmRating,
    int ObserverDiscriminationResistance,
    int BurnThroughResistance,
    int EffectiveJammingMargin,
    bool EcmDegradedFirm,
    bool LineOfSightBlocked);

public static class SensorEwFoundationResolver
{
    public static SensorEwFoundationEvaluationResult Evaluate(
        int distanceHexes,
        SensorEwFoundationProfile observerProfile,
        SensorEwFoundationProfile targetProfile,
        SensorEwFoundationEvaluationContext context)
    {
        if (distanceHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(distanceHexes));
        }
        ArgumentNullException.ThrowIfNull(observerProfile);
        ArgumentNullException.ThrowIfNull(targetProfile);
        ArgumentNullException.ThrowIfNull(context);
        if (!Enum.IsDefined(context.ObserverSensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(context.ObserverSensorMode));
        }
        if (context.TargetEcmRating < 0 || context.ObserverEccmRating < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(context.TargetEcmRating));
        }

        (int firmRange, int approximateRange) = ObserverRanges(observerProfile, context);
        int activeEmissionRange = TargetActiveEmissionRange(targetProfile, context);
        int netEcm = Math.Max(0, context.TargetEcmRating - context.ObserverEccmRating);
        int burnThroughResistance = distanceHexes == 0
            ? observerProfile.PointBlankBurnThroughResistance
            : 0;
        int totalDiscriminationResistance = checked(
            observerProfile.DiscriminationResistance + burnThroughResistance);
        int effectiveJammingMargin = Math.Max(
            0, netEcm - totalDiscriminationResistance);

        // Same-hex contacts cannot be occluded, but range zero does not bypass
        // emission provenance or ECM/ECCM discrimination. A sufficiently strong
        // jammer may therefore spoil Firm discrimination even at point-blank
        // tactical range.
        bool hasLineOfSight = distanceHexes == 0 || context.HasLineOfSight;
        if (!hasLineOfSight)
        {
            return new SensorEwFoundationEvaluationResult(
                distanceHexes,
                SensorEwFoundationTrackState.None,
                SensorEwFoundationTrackState.None,
                SensorEwFoundationTrackState.None,
                SensorEwEmissionSource.None,
                firmRange,
                approximateRange,
                activeEmissionRange,
                context.TargetEcmRating,
                context.ObserverEccmRating,
                netEcm,
                observerProfile.DiscriminationResistance,
                burnThroughResistance,
                effectiveJammingMargin,
                EcmDegradedFirm: false,
                LineOfSightBlocked: true);
        }

        SensorEwFoundationTrackState baseline = RangeState(
            distanceHexes,
            firmRange,
            approximateRange);

        SensorEwEmissionSource emissionSources = SensorEwEmissionSource.None;
        if (context.TargetActiveSensorsEnabled && distanceHexes <= activeEmissionRange)
        {
            emissionSources |= SensorEwEmissionSource.ActiveSensors;
        }
        if (context.TargetEcmRating > 0)
        {
            // ECM is intentionally conspicuous on the small tactical map: with
            // unobstructed LOS it establishes an emission contact, not a Firm fix.
            emissionSources |= SensorEwEmissionSource.ElectronicCountermeasures;
        }

        SensorEwFoundationTrackState emissionAssisted = baseline;
        if (emissionSources != SensorEwEmissionSource.None &&
            emissionAssisted == SensorEwFoundationTrackState.None)
        {
            emissionAssisted = SensorEwFoundationTrackState.Approximate;
        }

        bool ecmDegradedFirm = effectiveJammingMargin > 0 &&
            emissionAssisted == SensorEwFoundationTrackState.Firm;
        SensorEwFoundationTrackState final = ecmDegradedFirm
            ? SensorEwFoundationTrackState.Approximate
            : emissionAssisted;

        return new SensorEwFoundationEvaluationResult(
            distanceHexes,
            baseline,
            emissionAssisted,
            final,
            emissionSources,
            firmRange,
            approximateRange,
            activeEmissionRange,
            context.TargetEcmRating,
            context.ObserverEccmRating,
            netEcm,
            observerProfile.DiscriminationResistance,
            burnThroughResistance,
            effectiveJammingMargin,
            ecmDegradedFirm,
            LineOfSightBlocked: false);
    }

    private static (int FirmRange, int ApproximateRange) ObserverRanges(
        SensorEwFoundationProfile profile,
        SensorEwFoundationEvaluationContext context)
    {
        if (context.ObserverSensorMode == SensorMode.Passive)
        {
            return (profile.PassiveFirmRange, profile.PassiveApproximateRange);
        }

        int firm = profile.ActiveFirmRange;
        int approximate = profile.ActiveApproximateRange;
        if (context.ObserverActiveSensorOverloaded)
        {
            firm = checked(firm + profile.ActiveOverloadFirmBonus);
            approximate = checked(
                approximate + profile.ActiveOverloadApproximateBonus);
        }
        return (firm, Math.Max(firm, approximate));
    }

    private static int TargetActiveEmissionRange(
        SensorEwFoundationProfile profile,
        SensorEwFoundationEvaluationContext context)
    {
        if (!context.TargetActiveSensorsEnabled)
        {
            return 0;
        }
        int range = profile.ActiveApproximateRange;
        if (context.TargetActiveSensorOverloaded)
        {
            range = checked(range + profile.ActiveOverloadApproximateBonus);
        }
        return range;
    }

    private static SensorEwFoundationTrackState RangeState(
        int distanceHexes,
        int firmRange,
        int approximateRange)
    {
        if (distanceHexes <= firmRange)
        {
            return SensorEwFoundationTrackState.Firm;
        }
        return distanceHexes <= approximateRange
            ? SensorEwFoundationTrackState.Approximate
            : SensorEwFoundationTrackState.None;
    }
}
