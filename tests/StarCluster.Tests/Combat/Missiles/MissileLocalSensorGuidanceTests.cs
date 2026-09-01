using System;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileLocalSensorGuidanceTests
{
    [Fact]
    public void MissileSensorProfileRejectsNegativeLocalRetention()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new MissileSensorProfile(
                2,
                true,
                2,
                4,
                maximumLocalTrackAgeEpochs: -1));
    }

    [Fact]
    public void PassiveLocalSensorCreatesCurrentTrackInsideFirmRange()
    {
        MissileLocalSensorObservationResult result = Observe(
            missile: new HexCoord(2, 2),
            target: new HexCoord(1, 2),
            SensorProfile(firm: 2, approximate: 3),
            previous: null,
            epoch: 1);

        Assert.Equal(SensorMode.Passive, result.SensorMode);
        Assert.False(result.ActiveEscalated);
        Assert.Equal(MissileTargetTrackQuality.Current, result.TrackReport!.Quality);
        Assert.Equal(new HexCoord(1, 2), result.TrackReport.GuidanceCoordinate);
    }

    [Fact]
    public void ActiveModeEscalatesOnlyAfterPassiveMiss()
    {
        MissileLocalSensorObservationResult result = Observe(
            missile: new HexCoord(3, 2),
            target: new HexCoord(0, 2),
            new MissileSensorProfile(
                2,
                true,
                firmRangeHexes: 1,
                approximateRangeHexes: 2,
                activeModeRangeBonusHexes: 1),
            previous: null,
            epoch: 1);

        Assert.True(result.ActiveEscalated);
        Assert.Equal(SensorMode.Active, result.SensorMode);
        Assert.Equal(MissileTargetTrackQuality.Approximate, result.TrackReport!.Quality);
    }

    [Fact]
    public void SameEpochVisibilityLossBecomesStaleWithoutAging()
    {
        MissileLocalTrackReport current = Observe(
            missile: new HexCoord(-2, 1),
            target: new HexCoord(-3, 1),
            SensorProfile(2, 4),
            previous: null,
            epoch: 2).TrackReport!;

        MissileLocalSensorObservationResult blocked = Observe(
            missile: new HexCoord(2, 0),
            target: new HexCoord(-3, 1),
            SensorProfile(2, 4),
            current,
            epoch: 2);

        Assert.True(blocked.SameEpochVisibilityLoss);
        Assert.False(blocked.AgeAdvanced);
        Assert.Equal(MissileTargetTrackQuality.Stale, blocked.TrackReport!.Quality);
        Assert.Equal(current.GuidanceCoordinate, blocked.TrackReport.GuidanceCoordinate);
    }

    [Fact]
    public void LaterMissAgesLocalTrackAtMostOncePerEpoch()
    {
        MissileLocalTrackReport current = Observe(
            missile: new HexCoord(-2, 1),
            target: new HexCoord(-3, 1),
            SensorProfile(2, 4),
            previous: null,
            epoch: 1).TrackReport!;
        MissileLocalSensorObservationResult firstMiss = Observe(
            missile: new HexCoord(2, 0),
            target: new HexCoord(-3, 1),
            SensorProfile(2, 4),
            current,
            epoch: 2);
        MissileLocalSensorObservationResult repeated = Observe(
            missile: new HexCoord(2, -1),
            target: new HexCoord(-3, 1),
            SensorProfile(2, 4),
            firstMiss.TrackReport,
            epoch: 2);

        Assert.True(firstMiss.AgeAdvanced);
        Assert.False(repeated.AgeAdvanced);
        Assert.Equal(1, repeated.TrackReport!.AgeEpochs);
    }

    [Fact]
    public void LocalCurrentReportBeatsFreshStaleDatalinkAtActionStart()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(2, 2),
            range: 8,
            speed: 1);
        MissileDatalinkUpdateResult datalink = Datalink(
            map,
            salvo,
            launcher: new HexCoord(2, 2),
            MissileTargetTrackSnapshot.Stale(TargetId, new HexCoord(3, 0)),
            epoch: 1);

        MissileAutonomousGuidanceResult result = Advance(
            map,
            salvo,
            datalink,
            target: new HexCoord(1, 2),
            SensorProfile(2, 3),
            epoch: 1);

        Assert.Equal(MissileGuidanceReportSource.LocalSensor, result.InitialDecision.SelectedSource);
        Assert.Equal(GuidedMissileStatus.Expended, result.AdvanceResult.Status);
        Assert.Equal(MissileTerminalOutcome.Hit, result.AdvanceResult.TerminalResolution!.Outcome);
    }

    [Fact]
    public void PerEnteredHexReacquisitionReplansWithoutRefund()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(3, 1),
            range: 8,
            speed: 2);
        MissileDatalinkUpdateResult datalink = Datalink(
            map,
            salvo,
            launcher: new HexCoord(3, 1),
            MissileTargetTrackSnapshot.Stale(TargetId, new HexCoord(0, 1)),
            epoch: 1);

        MissileAutonomousGuidanceResult result = Advance(
            map,
            salvo,
            datalink,
            target: new HexCoord(0, 1),
            SensorProfile(firm: 2, approximate: 2),
            epoch: 1);

        Assert.Equal(2, result.AdvanceResult.DistanceTraveledThisPhase);
        Assert.True(result.ReplanCount >= 1);
        Assert.Equal(MissileGuidanceReportSource.LocalSensor, result.FinalDecision.SelectedSource);
        Assert.Equal(2, salvo.DistanceTraveled);
    }

    [Fact]
    public void BlockedDatalinkCanStillUseLocalSensor()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(-2, 0),
            range: 6,
            speed: 2,
            launcherId: LauncherId);
        MissileDatalinkUpdateResult datalink =
            MissileDatalinkService.UpdateForGuidancePhase(
                map,
                salvo,
                DatalinkProfile(),
                new HexCoord(4, 0),
                MissileTargetTrackSnapshot.Current(
                    TargetId,
                    new HexCoord(-3, 0)),
                sourceObservationEpoch: 1);

        MissileAutonomousGuidanceResult result = Advance(
            map,
            salvo,
            datalink,
            target: new HexCoord(-3, 0),
            SensorProfile(2, 3),
            epoch: 1);

        Assert.Equal(MissileDatalinkState.Blocked, datalink.State);
        Assert.Equal(MissileGuidanceReportSource.LocalSensor, result.InitialDecision.SelectedSource);
        Assert.Equal(GuidedMissileStatus.Expended, result.AdvanceResult.Status);
        Assert.Equal(MissileTerminalOutcome.Hit, result.AdvanceResult.TerminalResolution!.Outcome);
    }

    [Fact]
    public void TargetMovementObservationUpdatesLocalTrackWithoutMovingMissile()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(2, 2),
            range: 6,
            speed: 2);

        MissileAutonomousGuidanceService.ObserveAfterTargetMovement(
            map,
            salvo,
            SensorProfile(3, 4),
            new HexCoord(1, 2),
            SensorSignatureProfile.Neutral,
            SensorMode.Passive,
            ElectronicWarfareProfile.None,
            false,
            SensorEnvironmentProfile.ClearSpace,
            observationEpoch: 1);
        MissileAutonomousGuidanceService.ObserveAfterTargetMovement(
            map,
            salvo,
            SensorProfile(3, 4),
            new HexCoord(0, 2),
            SensorSignatureProfile.Neutral,
            SensorMode.Passive,
            ElectronicWarfareProfile.None,
            false,
            SensorEnvironmentProfile.ClearSpace,
            observationEpoch: 2);

        Assert.Equal(0, salvo.DistanceTraveled);
        Assert.Equal(new HexCoord(0, 2), salvo.LocalSensorTrack!.GuidanceCoordinate);
        Assert.Equal(2, salvo.LocalSensorTrack.SourceObservationEpoch);
    }

    [Fact]
    public void ReplanningNeverRestoresLifetimeRange()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(3, 1),
            range: 1,
            speed: 2);
        MissileDatalinkUpdateResult datalink = Datalink(
            map,
            salvo,
            launcher: new HexCoord(3, 1),
            MissileTargetTrackSnapshot.Stale(TargetId, new HexCoord(0, 1)),
            epoch: 1);

        MissileAutonomousGuidanceResult result = Advance(
            map,
            salvo,
            datalink,
            target: new HexCoord(0, 1),
            SensorProfile(2, 2),
            epoch: 1);

        Assert.Equal(1, result.AdvanceResult.DistanceTraveledThisPhase);
        Assert.Equal(1, salvo.DistanceTraveled);
        Assert.Equal(0, salvo.RemainingRange);
        Assert.Equal(GuidedMissileStatus.RangeExhausted, salvo.Status);
    }

    private static MissileAutonomousGuidanceResult Advance(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileDatalinkUpdateResult datalink,
        HexCoord target,
        MissileSensorProfile sensor,
        int epoch) =>
        MissileAutonomousGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            datalink,
            sensor,
            target,
            SensorSignatureProfile.Neutral,
            SensorMode.Passive,
            ElectronicWarfareProfile.None,
            false,
            SensorEnvironmentProfile.ClearSpace,
            epoch);

    private static MissileLocalSensorObservationResult Observe(
        HexCoord missile,
        HexCoord target,
        MissileSensorProfile profile,
        MissileLocalTrackReport? previous,
        int epoch) =>
        MissileLocalSensorService.Observe(
            CreateMap(),
            MissileId,
            TargetId,
            missile,
            target,
            profile,
            previous,
            SensorSignatureProfile.Neutral,
            SensorMode.Passive,
            ElectronicWarfareProfile.None,
            false,
            SensorEnvironmentProfile.ClearSpace,
            epoch);

    private static MissileDatalinkUpdateResult Datalink(
        SystemMap map,
        GuidedMissileSalvo salvo,
        HexCoord launcher,
        MissileTargetTrackSnapshot track,
        int epoch) =>
        MissileDatalinkService.UpdateForGuidancePhase(
            map,
            salvo,
            new MissileDatalinkProfile(
                2,
                true,
                requiresLineOfSight: false,
                maximumRetainedReportAgePhases: 3),
            launcher,
            track,
            epoch);

    private static GuidedMissileSalvo CreateSalvo(
        HexCoord coordinate,
        int range,
        int speed,
        string launcherId = LauncherId) =>
        new(
            MissileId,
            TacticalSide.Enemy,
            launcherId,
            TargetId,
            coordinate,
            new MissileFlightProfile(2, range, speed));

    private static MissileSensorProfile SensorProfile(
        int firm,
        int approximate) =>
        new(
            2,
            true,
            firm,
            approximate,
            activeModeRangeBonusHexes: 0,
            allowsActiveMode: false,
            maximumLocalTrackAgeEpochs: 2);

    private static MissileDatalinkProfile DatalinkProfile() =>
        new(
            2,
            true,
            requiresLineOfSight: true,
            maximumRetainedReportAgePhases: 3);

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            MapDefaults.SystemRadius,
            MapObject.CreateStar("star", "Primary"));

    private const string MissileId = "missile";
    private const string LauncherId = "launcher";
    private const string TargetId = "target";
}
