using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class StlDriveOverloadServiceTests
{
    [Fact]
    public void SafeTl1OverloadMatchesTl1MissileSpeed()
    {
        StlDriveOverloadResult result = Resolve(currentStrain: 0);

        Assert.Equal(StlDriveOverloadOutcome.SafeSuccess, result.Outcome);
        Assert.True(result.BenefitApplied);
        Assert.Equal(2, result.EffectiveMovement);
        Assert.Equal(TechnologyMovementRules.MissileMovement(1), result.EffectiveMovement);
        Assert.Equal(1, result.StrainApplied);
    }

    [Fact]
    public void SecondSafeOverloadReachesStrainLimit()
    {
        StlDriveOverloadResult result = Resolve(currentStrain: 1);

        Assert.Equal(StlDriveOverloadOutcome.SafeSuccess, result.Outcome);
        Assert.Equal(1, result.StrainApplied);
    }

    [Fact]
    public void OverloadBeyondLimitRequiresRoll()
    {
        Assert.Throws<InvalidOperationException>(() => Resolve(currentStrain: 2));
    }

    [Fact]
    public void ForcedSuccessAppliesEmergencyMovement()
    {
        StlDriveOverloadResult result = Resolve(currentStrain: 2, roll: 60);

        Assert.Equal(StlDriveOverloadOutcome.ForcedSuccess, result.Outcome);
        Assert.Equal(2, result.EffectiveMovement);
        Assert.Equal(1, result.StrainApplied);
    }

    [Fact]
    public void ForcedFailureAppliesStrainWithoutMovementBonus()
    {
        StlDriveOverloadResult result = Resolve(currentStrain: 2, roll: 61);

        Assert.Equal(StlDriveOverloadOutcome.ForcedFailure, result.Outcome);
        Assert.False(result.BenefitApplied);
        Assert.Equal(1, result.EffectiveMovement);
        Assert.Equal(1, result.StrainApplied);
    }

    [Fact]
    public void CriticalSuccessRemovesOneStrainFromAttempt()
    {
        StlDriveOverloadResult result = Resolve(currentStrain: 2, roll: 100);

        Assert.Equal(StlDriveOverloadOutcome.CriticalSuccess, result.Outcome);
        Assert.Equal(0, result.StrainApplied);
        Assert.Equal(2, result.EffectiveMovement);
    }

    [Fact]
    public void CriticalFailureRequiresConditionStep()
    {
        StlDriveOverloadResult result = Resolve(currentStrain: 2, roll: 1);

        Assert.Equal(StlDriveOverloadOutcome.CriticalFailure, result.Outcome);
        Assert.True(result.ConditionStepRequired);
        Assert.Equal(1, result.EffectiveMovement);
    }

    [Fact]
    public void DisabledDriveCannotOverloadOrConsumeResources()
    {
        StlDriveOverloadResult result = StlDriveOverloadService.Resolve(
            StlDriveOverloadProfile.Tl1,
            ComponentCondition.Disabled,
            currentStrain: 0,
            availableTacticalPower: 5,
            availableFuel: 24);

        Assert.Equal(StlDriveOverloadOutcome.Ineligible, result.Outcome);
        Assert.Equal(0, result.TacticalPowerCost);
        Assert.Equal(0, result.ExtraFuelCost);
        Assert.Equal(0, result.StrainApplied);
    }

    [Fact]
    public void DegradedDriveCannotOverloadOrConsumeResources()
    {
        StlDriveOverloadResult result = StlDriveOverloadService.Resolve(
            StlDriveOverloadProfile.Tl1,
            ComponentCondition.Degraded,
            currentStrain: 0,
            availableTacticalPower: 5,
            availableFuel: 24);

        Assert.Equal(StlDriveOverloadOutcome.Ineligible, result.Outcome);
        Assert.Equal(0, result.TacticalPowerCost);
        Assert.Equal(0, result.ExtraFuelCost);
        Assert.Equal(0, result.StrainApplied);
    }

    [Fact]
    public void InsufficientPowerPreventsOverload()
    {
        StlDriveOverloadResult result = StlDriveOverloadService.Resolve(
            StlDriveOverloadProfile.Tl1,
            ComponentCondition.Operational,
            currentStrain: 0,
            availableTacticalPower: 0,
            availableFuel: 24);

        Assert.Equal(StlDriveOverloadOutcome.Ineligible, result.Outcome);
    }

    [Fact]
    public void InsufficientFuelPreventsOverload()
    {
        StlDriveOverloadResult result = StlDriveOverloadService.Resolve(
            StlDriveOverloadProfile.Tl1,
            ComponentCondition.Operational,
            currentStrain: 0,
            availableTacticalPower: 5,
            availableFuel: 1);

        Assert.Equal(StlDriveOverloadOutcome.Ineligible, result.Outcome);
    }

    private static StlDriveOverloadResult Resolve(int currentStrain, int? roll = null) =>
        StlDriveOverloadService.Resolve(
            StlDriveOverloadProfile.Tl1,
            ComponentCondition.Operational,
            currentStrain,
            availableTacticalPower: 5,
            availableFuel: 24,
            forcedRoll: roll);
}
