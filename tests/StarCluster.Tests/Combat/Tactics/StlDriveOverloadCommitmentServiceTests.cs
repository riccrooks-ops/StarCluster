using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class StlDriveOverloadCommitmentServiceTests
{
    [Fact]
    public void PreparedOverloadMayStandDownWithoutHealingStrain()
    {
        StlDriveOverloadCommitment commitment =
            StlDriveOverloadCommitmentService.Prepare(
                StlDriveOverloadProfile.Tl1,
                ComponentCondition.Operational,
                availableTacticalPower: 5);
        StlDriveOverloadStandDownResult result =
            StlDriveOverloadCommitmentService.StandDown(
                commitment,
                currentStrain: 2);

        Assert.True(result.StoodDown);
        Assert.Equal(1, result.TacticalPowerCommitted);
        Assert.Equal(0, result.OverloadFuelSpent);
        Assert.Equal(0, result.StrainApplied);
        Assert.Equal(0, result.StrainRemoved);
    }

    [Fact]
    public void StandDownRequiresAnActualPreparation()
    {
        var commitment = new StlDriveOverloadCommitment(
            Prepared: false,
            TacticalPowerCommitted: 0,
            "not prepared");

        Assert.Throws<InvalidOperationException>(() =>
            StlDriveOverloadCommitmentService.StandDown(commitment, 0));
    }

    [Fact]
    public void PreparationRequiresOperationalDriveAndPower()
    {
        StlDriveOverloadCommitment degraded =
            StlDriveOverloadCommitmentService.Prepare(
                StlDriveOverloadProfile.Tl1,
                ComponentCondition.Degraded,
                availableTacticalPower: 5);
        StlDriveOverloadCommitment noPower =
            StlDriveOverloadCommitmentService.Prepare(
                StlDriveOverloadProfile.Tl1,
                ComponentCondition.Operational,
                availableTacticalPower: 0);

        Assert.False(degraded.Prepared);
        Assert.False(noPower.Prepared);
    }
}
