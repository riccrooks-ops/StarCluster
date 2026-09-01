using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Component-defined Active Sensor overload limits. This is deliberately
/// bounded: an overload is a listed mode, not an open-ended conversion of
/// spare Tactical Power into range.
/// </summary>
public sealed record ActiveSensorOverloadProfile(
    int AdditionalTacticalPowerCost,
    int FirmRangeBonus,
    int ApproximateRangeBonus,
    int StrainCost,
    int StrainLimit)
{
    public static ActiveSensorOverloadProfile Tl1 { get; } = new(
        AdditionalTacticalPowerCost: 1,
        FirmRangeBonus: 2,
        ApproximateRangeBonus: 2,
        StrainCost: 1,
        StrainLimit: 2);
}

public sealed record ActiveSensorOverloadResult(
    bool Eligible,
    bool BenefitApplied,
    int AdditionalTacticalPowerCost,
    int FirmRangeBonus,
    int ApproximateRangeBonus,
    int StrainApplied,
    string Reason);

public static class ActiveSensorOverloadService
{
    /// <summary>
    /// Evaluates only the automatically successful, at-or-below-Strain-Limit
    /// overload case. A caller that wants to exceed the limit must use the
    /// future Forced Overload path rather than silently treating it as safe.
    /// </summary>
    public static ActiveSensorOverloadResult ResolveSafe(
        ActiveSensorOverloadProfile profile,
        ComponentCondition sensorCondition,
        int currentStrain,
        int availableAdditionalTacticalPower)
    {
        ArgumentNullException.ThrowIfNull(profile);
        if (currentStrain < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(currentStrain));
        }
        if (availableAdditionalTacticalPower < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(availableAdditionalTacticalPower));
        }
        if (sensorCondition != ComponentCondition.Operational)
        {
            return Ineligible(
                profile,
                "Only an Operational Active Sensor may use the TL1 safe-overload mode.");
        }
        if (currentStrain + profile.StrainCost > profile.StrainLimit)
        {
            return Ineligible(
                profile,
                "The next overload would exceed the Active Sensor Strain Limit and require Forced Overload resolution.");
        }
        if (availableAdditionalTacticalPower < profile.AdditionalTacticalPowerCost)
        {
            return Ineligible(profile, "Insufficient Tactical Power for Active Sensor overload.");
        }

        return new ActiveSensorOverloadResult(
            Eligible: true,
            BenefitApplied: true,
            profile.AdditionalTacticalPowerCost,
            profile.FirmRangeBonus,
            profile.ApproximateRangeBonus,
            profile.StrainCost,
            "The Active Sensor overload remains at or below its Strain Limit and succeeds automatically.");
    }

    private static ActiveSensorOverloadResult Ineligible(
        ActiveSensorOverloadProfile profile,
        string reason) => new(
        Eligible: false,
        BenefitApplied: false,
        AdditionalTacticalPowerCost: 0,
        FirmRangeBonus: 0,
        ApproximateRangeBonus: 0,
        StrainApplied: 0,
        Reason: reason);
}
