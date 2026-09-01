using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class ElectronicWarfareDoctrineServiceTests
{
    [Fact]
    public void ReactiveEccmStaysOffWhenFirmTrackSurvives()
    {
        var context = Context(power: 4, degraded: false);
        Assert.False(ElectronicWarfareDoctrineService.ShouldActivateEccm(
            EccmActivationHeuristic.ReactiveOnFirmDegradation,
            context));
    }

    [Fact]
    public void ReactiveEccmActivatesWhenFirmTrackWasDegradedAndPowerExists()
    {
        var context = Context(power: 4, degraded: true);
        Assert.True(ElectronicWarfareDoctrineService.ShouldActivateEccm(
            EccmActivationHeuristic.ReactiveOnFirmDegradation,
            context));
    }

    [Fact]
    public void PreserveOffenseEcmKeepsOffensiveAndEccmHeadroom()
    {
        var enough = Context(power: 4, offense: 2, pds: 1);
        var shortByOne = Context(power: 3, offense: 2, pds: 1);
        Assert.True(ElectronicWarfareDoctrineService.ShouldActivateEcm(
            EcmActivationHeuristic.PreserveOffenseAndEccm,
            enough));
        Assert.False(ElectronicWarfareDoctrineService.ShouldActivateEcm(
            EcmActivationHeuristic.PreserveOffenseAndEccm,
            shortByOne));
    }

    [Fact]
    public void CombatPackageEcmAlsoPreservesPlannedPdsPower()
    {
        var context = Context(power: 4, offense: 2, pds: 1);
        Assert.True(ElectronicWarfareDoctrineService.ShouldActivateEcm(
            EcmActivationHeuristic.PreserveOffenseAndEccm,
            context));
        Assert.False(ElectronicWarfareDoctrineService.ShouldActivateEcm(
            EcmActivationHeuristic.PreserveCombatPackageAndEccm,
            context));
    }

    [Fact]
    public void DoctrineNeverUsesHiddenEnemyRatings()
    {
        var context = Context(power: 5, offense: 1, pds: 1);
        Assert.True(ElectronicWarfareDoctrineService.ShouldActivateEcm(
            EcmActivationHeuristic.PreserveCombatPackageAndEccm,
            context));
        Assert.False(ElectronicWarfareDoctrineService.ShouldActivateEccm(
            EccmActivationHeuristic.ReactiveOnFirmDegradation,
            context));
    }

    private static ElectronicWarfareDoctrineContext Context(
        int power,
        int offense = 1,
        int pds = 0,
        bool degraded = false) => new(
            SpendableTacticalPower: power,
            EcmNormalPowerCost: 1,
            EccmNormalPowerCost: 1,
            ReadyOffensivePower: offense,
            PlannedPdsPower: pds,
            EcmAvailable: true,
            EccmAvailable: true,
            FirmTrackWasDegradedByObservedEcm: degraded);
}
