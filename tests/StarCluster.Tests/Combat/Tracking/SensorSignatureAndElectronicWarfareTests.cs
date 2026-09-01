using System;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class SensorSignatureAndElectronicWarfareTests
{
    [Fact]
    public void SensorProfileRejectsNegativeActiveModeBonus()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SensorProfile(
                2,
                3,
                6,
                activeModeRangeBonusHexes: -1));
    }

    [Fact]
    public void SignatureProfileRequiresIdentifier()
    {
        Assert.Throws<ArgumentException>(
            () => new SensorSignatureProfile(string.Empty));
    }

    [Fact]
    public void SignatureProfileRejectsNegativeActiveEmissionModifier()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SensorSignatureProfile("quiet", -1, -1));
    }

    [Fact]
    public void ElectronicWarfareProfileRejectsNegativeTechnologyLevel()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new ElectronicWarfareProfile(-1, 0, 0));
    }

    [Fact]
    public void ElectronicWarfareProfileRejectsNegativeJammingPenalty()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new ElectronicWarfareProfile(2, -1, 0));
    }

    [Fact]
    public void EnvironmentProfileRejectsNegativePenalty()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SensorEnvironmentProfile("nebula", -1));
    }

    [Fact]
    public void NeutralContextMatchesLegacyObservation()
    {
        SystemMap map = CreateMap();
        var observer = new HexCoord(-3, 3);
        var target = new HexCoord(2, 3);
        var sensors = new SensorProfile(3, 6, 10, true, 2);

        TacticalTrackObservation legacy = SensorContactEvaluator.Observe(
            map,
            "target",
            observer,
            target,
            sensors);
        SensorContactEvaluationResult evaluated = SensorContactEvaluator.Evaluate(
            map,
            "target",
            observer,
            target,
            sensors,
            SensorContactEvaluationContext.Neutral);

        Assert.Equal(legacy.Detected, evaluated.Observation.Detected);
        Assert.Equal(legacy.Precise, evaluated.Observation.Precise);
        Assert.Equal(legacy.EstimatedCoordinate, evaluated.Observation.EstimatedCoordinate);
        Assert.Equal(SensorContactEvaluationStatus.Firm, evaluated.Status);
    }

    [Fact]
    public void ActiveSensorsExtendFirmEnvelope()
    {
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-4, 4),
            new HexCoord(4, 1),
            new SensorProfile(3, 6, 10, true, 2),
            new SensorContactEvaluationContext(
                SensorMode.Active,
                SensorSignatureProfile.Neutral));

        Assert.Equal(8, result.DistanceHexes);
        Assert.Equal(8, result.EffectiveFirmRangeHexes);
        Assert.Equal(SensorContactEvaluationStatus.Firm, result.Status);
    }

    [Fact]
    public void TargetActiveEmissionsIncreaseItsSignature()
    {
        var signature = new SensorSignatureProfile(
            "standard-ship",
            baselineRangeModifierHexes: 0,
            activeEmissionRangeModifierHexes: 2);
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-4, 4),
            new HexCoord(4, 1),
            new SensorProfile(3, 6, 10, true, 2),
            new SensorContactEvaluationContext(
                SensorMode.Passive,
                signature,
                targetSensorMode: SensorMode.Active));

        Assert.Equal(2, result.TargetSignatureRangeModifierHexes);
        Assert.Equal(SensorContactEvaluationStatus.Firm, result.Status);
    }

    [Fact]
    public void QuietTargetReducesEffectiveRange()
    {
        var signature = new SensorSignatureProfile(
            "quiet-ship",
            baselineRangeModifierHexes: -2);
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-3, 3),
            new HexCoord(3, 0),
            new SensorProfile(3, 6, 10),
            new SensorContactEvaluationContext(
                SensorMode.Passive,
                signature));

        Assert.Equal(4, result.EffectiveFirmRangeHexes);
        Assert.Equal(8, result.EffectiveApproximateRangeHexes);
        Assert.Equal(SensorContactEvaluationStatus.Approximate, result.Status);
    }

    [Fact]
    public void TargetJammingShrinksBothEffectiveEnvelopes()
    {
        var observerElectronicWarfare = new ElectronicWarfareProfile(3, 0, 1);
        var targetElectronicWarfare = new ElectronicWarfareProfile(3, 3, 0);
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-4, 4),
            new HexCoord(4, 1),
            new SensorProfile(3, 6, 10, true, 2),
            new SensorContactEvaluationContext(
                SensorMode.Active,
                SensorSignatureProfile.Neutral,
                observerElectronicWarfare: observerElectronicWarfare,
                targetElectronicWarfare: targetElectronicWarfare,
                targetJammingEnabled: true));

        Assert.Equal(3, result.RawJammingRangePenaltyHexes);
        Assert.Equal(1, result.CounterJammingStrength);
        Assert.Equal(2, result.NetJammingRangePenaltyHexes);
        Assert.Equal(6, result.EffectiveFirmRangeHexes);
        Assert.Equal(10, result.EffectiveApproximateRangeHexes);
        Assert.Equal(SensorContactEvaluationStatus.Approximate, result.Status);
    }

    [Fact]
    public void CounterJammingOffsetsHostileJamming()
    {
        var observerElectronicWarfare = new ElectronicWarfareProfile(3, 0, 3);
        var targetElectronicWarfare = new ElectronicWarfareProfile(3, 3, 0);
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-4, 4),
            new HexCoord(4, 1),
            new SensorProfile(3, 6, 10, true, 2),
            new SensorContactEvaluationContext(
                SensorMode.Active,
                SensorSignatureProfile.Neutral,
                observerElectronicWarfare: observerElectronicWarfare,
                targetElectronicWarfare: targetElectronicWarfare,
                targetJammingEnabled: true));

        Assert.Equal(0, result.NetJammingRangePenaltyHexes);
        Assert.Equal(8, result.EffectiveFirmRangeHexes);
        Assert.Equal(SensorContactEvaluationStatus.Firm, result.Status);
    }

    [Fact]
    public void DisabledJammerDoesNotApplyItsProfile()
    {
        var targetElectronicWarfare = new ElectronicWarfareProfile(3, 6, 0);
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-3, 3),
            new HexCoord(3, 0),
            new SensorProfile(3, 6, 10),
            new SensorContactEvaluationContext(
                SensorMode.Passive,
                SensorSignatureProfile.Neutral,
                targetElectronicWarfare: targetElectronicWarfare,
                targetJammingEnabled: false));

        Assert.Equal(0, result.RawJammingRangePenaltyHexes);
        Assert.Equal(SensorContactEvaluationStatus.Firm, result.Status);
    }

    [Fact]
    public void EnvironmentAndJammingPenaltiesStackDeterministically()
    {
        var targetElectronicWarfare = new ElectronicWarfareProfile(3, 2, 0);
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-3, 3),
            new HexCoord(3, 0),
            new SensorProfile(3, 6, 10, true, 2),
            new SensorContactEvaluationContext(
                SensorMode.Active,
                SensorSignatureProfile.Neutral,
                targetElectronicWarfare: targetElectronicWarfare,
                targetJammingEnabled: true,
                environment: new SensorEnvironmentProfile("ion-storm", 1)));

        Assert.Equal(5, result.EffectiveFirmRangeHexes);
        Assert.Equal(9, result.EffectiveApproximateRangeHexes);
        Assert.Equal(SensorContactEvaluationStatus.Approximate, result.Status);
    }

    [Fact]
    public void OcclusionRemainsAbsoluteUnderActiveSensors()
    {
        SensorContactEvaluationResult result = SensorContactEvaluator.Evaluate(
            CreateMap(),
            "target",
            new HexCoord(-4, 0),
            new HexCoord(4, 0),
            new SensorProfile(9, 20, 30, true, 20),
            new SensorContactEvaluationContext(
                SensorMode.Active,
                new SensorSignatureProfile("radiant", 20, 20)));

        Assert.False(result.Observation.Detected);
        Assert.Equal(SensorContactEvaluationStatus.MissedOccluded, result.Status);
    }

    [Fact]
    public void SameHexContactIsFirmDespiteRangePenalties()
    {
        var coordinate = new HexCoord(2, -1);
        SensorContactEvaluationResult result = SensorContactEvaluator.Evaluate(
            CreateMap(),
            "target",
            coordinate,
            coordinate,
            new SensorProfile(1, 0, 0),
            new SensorContactEvaluationContext(
                SensorMode.Passive,
                new SensorSignatureProfile("silent", -20),
                targetElectronicWarfare: new ElectronicWarfareProfile(9, 20, 0),
                targetJammingEnabled: true,
                environment: new SensorEnvironmentProfile("storm", 20)));

        Assert.True(result.Observation.Detected);
        Assert.True(result.Observation.Precise);
        Assert.Equal(SensorContactEvaluationStatus.Firm, result.Status);
    }

    [Fact]
    public void ReplaceablePolicyMayForceAMissWithinTheEnvelope()
    {
        SensorContactEvaluationResult result = SensorContactEvaluator.Evaluate(
            CreateMap(),
            "target",
            new HexCoord(-3, 3),
            new HexCoord(2, 3),
            new SensorProfile(3, 6, 10),
            SensorContactEvaluationContext.Neutral,
            new AlwaysMissPolicy());

        Assert.False(result.Observation.Detected);
        Assert.Equal(SensorContactEvaluationStatus.MissedByPolicy, result.Status);
    }

    [Fact]
    public void DeterministicPolicyReportsOutOfRangeMiss()
    {
        SensorContactEvaluationResult result = EvaluateClear(
            new HexCoord(-4, 4),
            new HexCoord(4, 1),
            new SensorProfile(2, 3, 6),
            SensorContactEvaluationContext.Neutral);

        Assert.False(result.Observation.Detected);
        Assert.Equal(SensorContactEvaluationStatus.MissedOutOfRange, result.Status);
    }

    [Fact]
    public void RepeatedSensorStateMissesDoNotAgeTwiceInOneEpoch()
    {
        SystemMap map = CreateMap();
        var repository = new TacticalTrackRepository();
        var computing = new ComputingProfile(3, 3, 1);
        var sensors = new SensorProfile(3, 6, 10, true, 2);
        var observer = new HexCoord(-4, 4);
        var target = new HexCoord(4, 1);

        SensorContactEvaluationResult initial = SensorContactEvaluator.Evaluate(
            map,
            "target",
            observer,
            target,
            sensors,
            new SensorContactEvaluationContext(
                SensorMode.Active,
                SensorSignatureProfile.Neutral));
        TacticalTrackUpdateService.Apply(
            repository,
            "observer",
            initial.Observation,
            computing,
            sequence: 1,
            trigger: TrackUpdateTrigger.SystemEntry,
            observationEpoch: 1);

        var heavyJamming = new SensorContactEvaluationContext(
            SensorMode.Active,
            SensorSignatureProfile.Neutral,
            targetElectronicWarfare: new ElectronicWarfareProfile(4, 5, 0),
            targetJammingEnabled: true);
        TacticalTrackObservation missed = SensorContactEvaluator.Evaluate(
            map,
            "target",
            observer,
            target,
            sensors,
            heavyJamming).Observation;

        TacticalTrackUpdateResult firstMiss = TacticalTrackUpdateService.Apply(
            repository,
            "observer",
            missed,
            computing,
            sequence: 2,
            trigger: TrackUpdateTrigger.SensorStateChanged,
            observationEpoch: 2);
        TacticalTrackUpdateResult repeatedMiss = TacticalTrackUpdateService.Apply(
            repository,
            "observer",
            missed,
            computing,
            sequence: 3,
            trigger: TrackUpdateTrigger.SensorStateChanged,
            observationEpoch: 2);

        Assert.True(firstMiss.AgeAdvanced);
        Assert.False(repeatedMiss.AgeAdvanced);
        Assert.Equal(1, repeatedMiss.Record!.MissedUpdateCount);
        Assert.Equal(TacticalTrackQuality.Stale, repeatedMiss.Record.Quality);
    }

    private static SensorContactEvaluationResult EvaluateClear(
        HexCoord observer,
        HexCoord target,
        SensorProfile sensors,
        SensorContactEvaluationContext context) =>
        SensorContactEvaluator.Evaluate(
            CreateMap(),
            "target",
            observer,
            target,
            sensors,
            context);

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            5,
            MapObject.CreateStar("star-primary", "Primary Star"));

    private sealed class AlwaysMissPolicy : ISensorContactResolutionPolicy
    {
        public SensorContactResolution Resolve(
            SensorContactResolutionContext context)
        {
            ArgumentNullException.ThrowIfNull(context);
            return SensorContactResolution.Missed;
        }
    }
}
