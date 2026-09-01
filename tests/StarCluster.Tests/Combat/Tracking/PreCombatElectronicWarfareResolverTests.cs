using StarCluster.Core.Combat.Tracking;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class PreCombatElectronicWarfareResolverTests
{
    private static readonly SensorEwFoundationProfile Profile = new(
        "balanced-0",
        passiveFirmRange: 1,
        passiveApproximateRange: 3,
        activeFirmRange: 3,
        activeApproximateRange: 4,
        activePowerCost: 1,
        activeOverloadAdditionalPowerCost: 1,
        activeOverloadFirmBonus: 1,
        activeOverloadApproximateBonus: 1,
        discriminationResistance: 0,
        pointBlankBurnThroughResistance: 1);

    [Fact]
    public void BothEcmDeclarationsResolveBeforeEitherEccmResponse()
    {
        PreCombatElectronicWarfareParticipant sideA = Participant(ecm: 1, eccm: 1);
        PreCombatElectronicWarfareParticipant sideB = Participant(ecm: 1, eccm: 1);

        PreCombatElectronicWarfareTrackPair afterEcm =
            PreCombatElectronicWarfareResolver.ResolveAfterEcmDeclarations(
                2, sideA, sideB);
        PreCombatElectronicWarfareTrackPair final =
            PreCombatElectronicWarfareResolver.ResolveAfterEccmResponses(
                2, sideA, sideB);

        Assert.Equal(SensorEwFoundationTrackState.Approximate, afterEcm.SideA.FinalTrack);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, afterEcm.SideB.FinalTrack);
        Assert.True(afterEcm.SideA.EcmDegradedFirm);
        Assert.True(afterEcm.SideB.EcmDegradedFirm);
        Assert.Equal(SensorEwFoundationTrackState.Firm, final.SideA.FinalTrack);
        Assert.Equal(SensorEwFoundationTrackState.Firm, final.SideB.FinalTrack);
    }

    [Fact]
    public void PointBlankBurnThroughCanMakeEccmResponseUnnecessary()
    {
        PreCombatElectronicWarfareParticipant sideA = Participant(ecm: 0, eccm: 1);
        PreCombatElectronicWarfareParticipant sideB = Participant(ecm: 1, eccm: 0);

        PreCombatElectronicWarfareTrackPair afterEcm =
            PreCombatElectronicWarfareResolver.ResolveAfterEcmDeclarations(
                0, sideA, sideB);

        Assert.Equal(SensorEwFoundationTrackState.Firm, afterEcm.SideA.FinalTrack);
        Assert.False(afterEcm.SideA.EcmDegradedFirm);
        Assert.Equal(0, afterEcm.SideA.EffectiveJammingMargin);
    }

    [Fact]
    public void StrongerPointBlankEcmCanStillCreateAnEccmResponseNeed()
    {
        PreCombatElectronicWarfareParticipant sideA = Participant(ecm: 0, eccm: 1);
        PreCombatElectronicWarfareParticipant sideB = Participant(ecm: 2, eccm: 0);

        PreCombatElectronicWarfareTrackPair afterEcm =
            PreCombatElectronicWarfareResolver.ResolveAfterEcmDeclarations(
                0, sideA, sideB);
        PreCombatElectronicWarfareTrackPair final =
            PreCombatElectronicWarfareResolver.ResolveAfterEccmResponses(
                0, sideA, sideB);

        Assert.Equal(SensorEwFoundationTrackState.Approximate, afterEcm.SideA.FinalTrack);
        Assert.True(afterEcm.SideA.EcmDegradedFirm);
        Assert.Equal(SensorEwFoundationTrackState.Firm, final.SideA.FinalTrack);
    }

    [Fact]
    public void SymmetricEwResolutionDoesNotDependOnAnInitiativeOrder()
    {
        PreCombatElectronicWarfareParticipant sideA = Participant(ecm: 1, eccm: 0);
        PreCombatElectronicWarfareParticipant sideB = Participant(ecm: 1, eccm: 0);

        PreCombatElectronicWarfareTrackPair result =
            PreCombatElectronicWarfareResolver.ResolveAfterEcmDeclarations(
                2, sideA, sideB);

        Assert.Equal(result.SideA.FinalTrack, result.SideB.FinalTrack);
        Assert.Equal(result.SideA.EffectiveJammingMargin, result.SideB.EffectiveJammingMargin);
        Assert.Equal(result.SideA.EcmDegradedFirm, result.SideB.EcmDegradedFirm);
    }

    private static PreCombatElectronicWarfareParticipant Participant(
        int ecm,
        int eccm)
    {
        return new PreCombatElectronicWarfareParticipant(
            Profile,
            SensorMode.Active,
            ActiveSensorOverloaded: false,
            ActiveSensorsEnabled: true,
            EcmRating: ecm,
            EccmRating: eccm);
    }
}
