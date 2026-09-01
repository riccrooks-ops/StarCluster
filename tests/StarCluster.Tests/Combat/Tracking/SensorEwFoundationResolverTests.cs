using StarCluster.Core.Combat.Tracking;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class SensorEwFoundationResolverTests
{
    private static readonly SensorEwFoundationProfile Profile = new(
        "candidate",
        passiveFirmRange: 1,
        passiveApproximateRange: 2,
        activeFirmRange: 3,
        activeApproximateRange: 4,
        activePowerCost: 1,
        activeOverloadAdditionalPowerCost: 1,
        activeOverloadFirmBonus: 1,
        activeOverloadApproximateBonus: 1);

    [Fact]
    public void ActiveSensorHasOneNormalEnvelopeAndOverloadExtendsReach()
    {
        SensorEwFoundationEvaluationResult normal = Evaluate(
            4,
            new SensorEwFoundationEvaluationContext(SensorMode.Active));
        SensorEwFoundationEvaluationResult overloaded = Evaluate(
            4,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Active,
                ObserverActiveSensorOverloaded: true));

        Assert.Equal(SensorEwFoundationTrackState.Approximate, normal.FinalTrack);
        Assert.Equal(SensorEwFoundationTrackState.Firm, overloaded.FinalTrack);
    }

    [Fact]
    public void ActiveEmitterMayCreateApproximateContactButNeverFirmByEmissionAlone()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            4,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetActiveSensorsEnabled: true));

        Assert.Equal(SensorEwFoundationTrackState.None, result.BaselineTrack);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, result.FinalTrack);
        Assert.True(result.EmissionSources.HasFlag(SensorEwEmissionSource.ActiveSensors));
    }

    [Fact]
    public void ActiveEmissionContactIsRangeLimited()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            5,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetActiveSensorsEnabled: true));

        Assert.Equal(SensorEwFoundationTrackState.None, result.FinalTrack);
    }

    [Fact]
    public void EcmAnnouncesEmitterButDegradesFirmDiscrimination()
    {
        SensorEwFoundationEvaluationResult close = Evaluate(
            1,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1));
        SensorEwFoundationEvaluationResult distant = Evaluate(
            9,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1));

        Assert.Equal(SensorEwFoundationTrackState.Firm, close.BaselineTrack);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, close.FinalTrack);
        Assert.True(close.EcmDegradedFirm);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, distant.FinalTrack);
        Assert.True(distant.EmissionSources.HasFlag(
            SensorEwEmissionSource.ElectronicCountermeasures));
    }

    [Fact]
    public void MatchingEccmPreservesFirmButDoesNotExtendReach()
    {
        SensorEwFoundationEvaluationResult close = Evaluate(
            3,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Active,
                TargetEcmRating: 1,
                ObserverEccmRating: 1));
        SensorEwFoundationEvaluationResult beyond = Evaluate(
            4,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Active,
                TargetEcmRating: 0,
                ObserverEccmRating: 4));

        Assert.Equal(SensorEwFoundationTrackState.Firm, close.FinalTrack);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, beyond.FinalTrack);
    }

    [Fact]
    public void SensorOverloadDoesNotSubstituteForEccm()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            4,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Active,
                ObserverActiveSensorOverloaded: true,
                TargetEcmRating: 1));

        Assert.Equal(SensorEwFoundationTrackState.Firm, result.BaselineTrack);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, result.FinalTrack);
        Assert.True(result.EcmDegradedFirm);
    }

    [Fact]
    public void OcclusionBlocksSensorAndEmissionContact()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            4,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Active,
                TargetActiveSensorsEnabled: true,
                TargetEcmRating: 2,
                HasLineOfSight: false));

        Assert.Equal(SensorEwFoundationTrackState.None, result.FinalTrack);
        Assert.True(result.LineOfSightBlocked);
    }

    [Fact]
    public void SameHexEcmMayDegradeFirmAndRetainsEmissionProvenance()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            0,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1));

        Assert.Equal(SensorEwFoundationTrackState.Firm, result.BaselineTrack);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, result.FinalTrack);
        Assert.True(result.EcmDegradedFirm);
        Assert.True(result.EmissionSources.HasFlag(
            SensorEwEmissionSource.ElectronicCountermeasures));
        Assert.False(result.LineOfSightBlocked);
    }

    [Fact]
    public void SameHexMatchingEccmPreservesFirmAgainstEcm()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            0,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1,
                ObserverEccmRating: 1));

        Assert.Equal(SensorEwFoundationTrackState.Firm, result.FinalTrack);
        Assert.False(result.EcmDegradedFirm);
    }

    [Fact]
    public void SameHexActiveEmitterRetainsActiveSensorProvenance()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            0,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetActiveSensorsEnabled: true));

        Assert.Equal(SensorEwFoundationTrackState.Firm, result.FinalTrack);
        Assert.True(result.EmissionSources.HasFlag(
            SensorEwEmissionSource.ActiveSensors));
    }

    [Fact]
    public void SameHexLineOfSightCannotBeOccluded()
    {
        SensorEwFoundationEvaluationResult result = Evaluate(
            0,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1,
                HasLineOfSight: false));

        Assert.False(result.LineOfSightBlocked);
        Assert.Equal(SensorEwFoundationTrackState.Approximate, result.FinalTrack);
        Assert.True(result.EmissionSources.HasFlag(
            SensorEwEmissionSource.ElectronicCountermeasures));
    }


    [Fact]
    public void PointBlankBurnThroughPreservesFirmAgainstTl1Ecm()
    {
        SensorEwFoundationProfile profile = new SensorEwFoundationProfile(
            "burnthrough",
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

        SensorEwFoundationEvaluationResult result = SensorEwFoundationResolver.Evaluate(
            0,
            profile,
            profile,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1));

        Assert.Equal(SensorEwFoundationTrackState.Firm, result.FinalTrack);
        Assert.Equal(1, result.BurnThroughResistance);
        Assert.Equal(0, result.EffectiveJammingMargin);
        Assert.False(result.EcmDegradedFirm);
    }

    [Fact]
    public void PointBlankBurnThroughDoesNotDefeatStrongerEcm()
    {
        SensorEwFoundationProfile profile = new(
            "burnthrough",
            1, 3, 3, 4, 1, 1, 1, 1,
            discriminationResistance: 0,
            pointBlankBurnThroughResistance: 1);

        SensorEwFoundationEvaluationResult result = SensorEwFoundationResolver.Evaluate(
            0,
            profile,
            profile,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 2));

        Assert.Equal(SensorEwFoundationTrackState.Approximate, result.FinalTrack);
        Assert.Equal(1, result.EffectiveJammingMargin);
        Assert.True(result.EcmDegradedFirm);
    }

    [Fact]
    public void IntrinsicDiscriminationResistanceCanDefeatLowerEcmWithoutEccm()
    {
        SensorEwFoundationProfile profile = new(
            "resistant",
            1, 3, 3, 4, 1, 1, 1, 1,
            discriminationResistance: 1,
            pointBlankBurnThroughResistance: 0);

        SensorEwFoundationEvaluationResult result = SensorEwFoundationResolver.Evaluate(
            1,
            profile,
            profile,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1));

        Assert.Equal(SensorEwFoundationTrackState.Firm, result.FinalTrack);
        Assert.Equal(1, result.ObserverDiscriminationResistance);
        Assert.Equal(0, result.EffectiveJammingMargin);
        Assert.False(result.EcmDegradedFirm);
    }

    [Fact]
    public void PointBlankBurnThroughDoesNotExtendBeyondSameHex()
    {
        SensorEwFoundationProfile profile = new(
            "burnthrough",
            1, 3, 3, 4, 1, 1, 1, 1,
            discriminationResistance: 0,
            pointBlankBurnThroughResistance: 1);

        SensorEwFoundationEvaluationResult result = SensorEwFoundationResolver.Evaluate(
            1,
            profile,
            profile,
            new SensorEwFoundationEvaluationContext(
                SensorMode.Passive,
                TargetEcmRating: 1));

        Assert.Equal(SensorEwFoundationTrackState.Approximate, result.FinalTrack);
        Assert.Equal(0, result.BurnThroughResistance);
        Assert.Equal(1, result.EffectiveJammingMargin);
        Assert.True(result.EcmDegradedFirm);
    }

    private static SensorEwFoundationEvaluationResult Evaluate(
        int distance,
        SensorEwFoundationEvaluationContext context) =>
        SensorEwFoundationResolver.Evaluate(
            distance,
            Profile,
            Profile,
            context);
}
