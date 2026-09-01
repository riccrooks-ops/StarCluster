using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Tracking;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class ActiveSensorOverloadServiceTests
{
    [Fact]
    public void Tl1ProfileDefinesOneBoundedAdditionalPowerStep()
    {
        ActiveSensorOverloadProfile profile = ActiveSensorOverloadProfile.Tl1;

        Assert.Equal(1, profile.AdditionalTacticalPowerCost);
        Assert.Equal(2, profile.FirmRangeBonus);
        Assert.Equal(2, profile.ApproximateRangeBonus);
        Assert.Equal(1, profile.StrainCost);
        Assert.Equal(2, profile.StrainLimit);
    }

    [Fact]
    public void SecondSafeOverloadMayReachStrainLimit()
    {
        ActiveSensorOverloadResult result = ActiveSensorOverloadService.ResolveSafe(
            ActiveSensorOverloadProfile.Tl1,
            ComponentCondition.Operational,
            currentStrain: 1,
            availableAdditionalTacticalPower: 1);

        Assert.True(result.BenefitApplied);
        Assert.Equal(1, result.StrainApplied);
    }

    [Fact]
    public void ThirdSafeOverloadIsDeclinedRatherThanForcing()
    {
        ActiveSensorOverloadResult result = ActiveSensorOverloadService.ResolveSafe(
            ActiveSensorOverloadProfile.Tl1,
            ComponentCondition.Operational,
            currentStrain: 2,
            availableAdditionalTacticalPower: 1);

        Assert.False(result.BenefitApplied);
        Assert.Equal(0, result.AdditionalTacticalPowerCost);
        Assert.Contains("Forced Overload", result.Reason);
    }

    [Fact]
    public void DegradedSensorCannotUseSafeTl1Overload()
    {
        ActiveSensorOverloadResult result = ActiveSensorOverloadService.ResolveSafe(
            ActiveSensorOverloadProfile.Tl1,
            ComponentCondition.Degraded,
            currentStrain: 0,
            availableAdditionalTacticalPower: 1);

        Assert.False(result.BenefitApplied);
    }

    [Fact]
    public void InsufficientAdditionalPowerPreventsOverload()
    {
        ActiveSensorOverloadResult result = ActiveSensorOverloadService.ResolveSafe(
            ActiveSensorOverloadProfile.Tl1,
            ComponentCondition.Operational,
            currentStrain: 0,
            availableAdditionalTacticalPower: 0);

        Assert.False(result.BenefitApplied);
    }
}
