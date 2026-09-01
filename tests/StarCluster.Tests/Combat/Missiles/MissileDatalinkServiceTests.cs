using System;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileDatalinkServiceTests
{
    [Fact]
    public void ProfileRejectsNegativeTechnologyLevel()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new MissileDatalinkProfile(-1));
    }

    [Fact]
    public void ProfileRejectsNegativeRetentionAge()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new MissileDatalinkProfile(
                2,
                maximumRetainedReportAgePhases: -1));
    }

    [Fact]
    public void MissingReceiverMakesTheLinkUnavailable()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(2, 2));

        MissileDatalinkUpdateResult result =
            MissileDatalinkService.UpdateForGuidancePhase(
                map,
                salvo,
                MissileDatalinkProfile.None,
                new HexCoord(2, 2),
                MissileTargetTrackSnapshot.Current(
                    TargetId,
                    new HexCoord(1, 1)),
                sourceObservationEpoch: 1);

        Assert.Equal(MissileDatalinkState.Unavailable, result.State);
        Assert.Equal(MissileGuidanceReportSource.None, result.GuidanceSource);
        Assert.Equal(MissileTargetTrackQuality.Lost, result.GuidanceSnapshot.Quality);
        Assert.Null(salvo.RetainedDatalinkReport);
    }

    [Fact]
    public void SameHexLauncherAndMissileHaveALiveLink()
    {
        SystemMap map = CreateMap();
        var coordinate = new HexCoord(2, 2);

        MissileDatalinkLinkEvaluation result =
            MissileDatalinkService.EvaluateLink(
                map,
                Profile(),
                coordinate,
                coordinate);

        Assert.True(result.IsLive);
        Assert.Null(result.LineOfSightQuality);
    }

    [Fact]
    public void ClearGeometryKeepsTheLinkLive()
    {
        MissileDatalinkLinkEvaluation result =
            MissileDatalinkService.EvaluateLink(
                CreateMap(),
                Profile(),
                new HexCoord(-3, 3),
                new HexCoord(2, 3));

        Assert.Equal(MissileDatalinkState.Live, result.State);
    }

    [Fact]
    public void CentralStarBlocksTheDatalink()
    {
        MissileDatalinkLinkEvaluation result =
            MissileDatalinkService.EvaluateLink(
                CreateMap(),
                Profile(),
                new HexCoord(-4, 0),
                new HexCoord(4, 0));

        Assert.Equal(MissileDatalinkState.Blocked, result.State);
    }

    [Fact]
    public void LiveLinkCopiesCurrentLauncherReport()
    {
        SystemMap map = CreateMap();
        var missileCoordinate = new HexCoord(2, 2);
        var targetCoordinate = new HexCoord(3, 1);
        GuidedMissileSalvo salvo = CreateSalvo(missileCoordinate);

        MissileDatalinkUpdateResult result = Update(
            map,
            salvo,
            Profile(),
            missileCoordinate,
            MissileTargetTrackSnapshot.Current(TargetId, targetCoordinate));

        Assert.True(result.ReportDelivered);
        Assert.Equal(MissileGuidanceReportSource.FreshDatalink, result.GuidanceSource);
        Assert.Equal(MissileTargetTrackQuality.Current, result.GuidanceSnapshot.Quality);
        Assert.Equal(targetCoordinate, result.GuidanceSnapshot.GuidanceCoordinate!.Value);
        Assert.Equal(0, result.RetainedReport!.AgePhases);
        Assert.Equal(0, result.RetainedReport.ReceivedUncertaintyRadiusHexes);
        Assert.Equal(0, result.RetainedReport.EffectiveUncertaintyRadiusHexes);
        Assert.Equal(1, result.RetainedReport.SourceObservationEpoch);
    }

    [Fact]
    public void LiveLinkCopiesApproximateLauncherReport()
    {
        SystemMap map = CreateMap();
        var missileCoordinate = new HexCoord(2, 2);
        var estimate = new HexCoord(3, 0);
        GuidedMissileSalvo salvo = CreateSalvo(missileCoordinate);

        MissileDatalinkUpdateResult result = Update(
            map,
            salvo,
            Profile(),
            missileCoordinate,
            MissileTargetTrackSnapshot.Approximate(TargetId, estimate));

        Assert.Equal(MissileTargetTrackQuality.Approximate, result.GuidanceSnapshot.Quality);
        Assert.Equal(estimate, result.RetainedReport!.GuidanceCoordinate);
        Assert.Equal(MissileTargetTrackQuality.Approximate, result.RetainedReport.ReceivedQuality);
    }

    [Fact]
    public void BlockedLinkRetainsAndAgesTheLastCopyToStale()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));
        var oldCoordinate = new HexCoord(3, 0);

        Update(
            map,
            salvo,
            NoLineOfSightProfile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Current(TargetId, oldCoordinate));
        CountGuidancePhase(map, salvo);

        MissileDatalinkUpdateResult blocked = Update(
            map,
            salvo,
            Profile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Current(
                TargetId,
                new HexCoord(2, -1)));

        Assert.Equal(MissileDatalinkState.Blocked, blocked.State);
        Assert.False(blocked.ReportDelivered);
        Assert.True(blocked.RetainedReportAged);
        Assert.Equal(1, blocked.RetainedReport!.AgePhases);
        Assert.Equal(1, blocked.RetainedReport.EffectiveUncertaintyRadiusHexes);
        Assert.Equal(MissileTargetTrackQuality.Stale, blocked.GuidanceSnapshot.Quality);
        Assert.Equal(oldCoordinate, blocked.GuidanceSnapshot.GuidanceCoordinate!.Value);
    }

    [Fact]
    public void RetainedCopyDoesNotFollowANewerBlockedLauncherSnapshot()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));
        var copiedCoordinate = new HexCoord(3, 0);
        var hiddenNewCoordinate = new HexCoord(2, -2);

        Update(
            map,
            salvo,
            NoLineOfSightProfile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Current(TargetId, copiedCoordinate));
        CountGuidancePhase(map, salvo);

        MissileDatalinkUpdateResult blocked = Update(
            map,
            salvo,
            Profile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Current(TargetId, hiddenNewCoordinate));

        Assert.Equal(copiedCoordinate, blocked.RetainedReport!.GuidanceCoordinate);
        Assert.NotEqual(hiddenNewCoordinate, blocked.GuidanceSnapshot.GuidanceCoordinate!.Value);
    }

    [Fact]
    public void RepeatedEvaluationInOneGuidancePhaseDoesNotAgeTwice()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));

        Update(
            map,
            salvo,
            NoLineOfSightProfile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Current(
                TargetId,
                new HexCoord(3, 0)));
        CountGuidancePhase(map, salvo);

        MissileDatalinkUpdateResult firstBlocked = Update(
            map,
            salvo,
            Profile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Lost(TargetId));
        MissileDatalinkUpdateResult repeatedBlocked = Update(
            map,
            salvo,
            Profile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Lost(TargetId));

        Assert.Equal(1, firstBlocked.RetainedReport!.AgePhases);
        Assert.False(repeatedBlocked.RetainedReportAged);
        Assert.Equal(1, repeatedBlocked.RetainedReport!.AgePhases);
    }

    [Fact]
    public void RestoredLinkReplacesTheRetainedCopyAndResetsAge()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));

        Update(
            map,
            salvo,
            NoLineOfSightProfile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Current(
                TargetId,
                new HexCoord(3, 0)));
        CountGuidancePhase(map, salvo);
        Update(
            map,
            salvo,
            Profile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Lost(TargetId));
        CountGuidancePhase(map, salvo);

        var reacquiredCoordinate = new HexCoord(2, -1);
        MissileDatalinkUpdateResult restored = Update(
            map,
            salvo,
            Profile(),
            salvo.CurrentCoordinate,
            MissileTargetTrackSnapshot.Current(
                TargetId,
                reacquiredCoordinate),
            sourceObservationEpoch: 3);

        Assert.Equal(MissileDatalinkState.Live, restored.State);
        Assert.True(restored.ReportDelivered);
        Assert.Equal(0, restored.RetainedReport!.AgePhases);
        Assert.Equal(3, restored.RetainedReport.SourceObservationEpoch);
        Assert.Equal(reacquiredCoordinate, restored.GuidanceSnapshot.GuidanceCoordinate!.Value);
    }

    [Fact]
    public void LiveLinkWithNoUsableLauncherCoordinateAgesThePriorCopy()
    {
        SystemMap map = CreateMap();
        var coordinate = new HexCoord(2, 2);
        GuidedMissileSalvo salvo = CreateSalvo(coordinate);

        Update(
            map,
            salvo,
            Profile(),
            coordinate,
            MissileTargetTrackSnapshot.Current(
                TargetId,
                new HexCoord(3, 1)));
        CountGuidancePhase(map, salvo);

        MissileDatalinkUpdateResult result = Update(
            map,
            salvo,
            Profile(),
            coordinate,
            MissileTargetTrackSnapshot.Lost(TargetId));

        Assert.Equal(MissileDatalinkState.Live, result.State);
        Assert.False(result.ReportDelivered);
        Assert.True(result.RetainedReportAged);
        Assert.Equal(MissileGuidanceReportSource.RetainedDatalink, result.GuidanceSource);
    }

    [Fact]
    public void RetainedReportExpiresAfterTheConfiguredAgeLimit()
    {
        SystemMap map = CreateMap();
        var coordinate = new HexCoord(2, 2);
        GuidedMissileSalvo salvo = CreateSalvo(coordinate);
        var profile = new MissileDatalinkProfile(
            technologyLevel: 2,
            maximumRetainedReportAgePhases: 1);

        Update(
            map,
            salvo,
            profile,
            coordinate,
            MissileTargetTrackSnapshot.Current(
                TargetId,
                new HexCoord(3, 1)));
        CountGuidancePhase(map, salvo);
        Update(
            map,
            salvo,
            profile,
            coordinate,
            MissileTargetTrackSnapshot.Lost(TargetId));
        CountGuidancePhase(map, salvo);

        MissileDatalinkUpdateResult expired = Update(
            map,
            salvo,
            profile,
            coordinate,
            MissileTargetTrackSnapshot.Lost(TargetId));

        Assert.True(expired.RetainedReportExpired);
        Assert.Equal(2, expired.RetainedReport!.AgePhases);
        Assert.Equal(MissileGuidanceReportSource.None, expired.GuidanceSource);
        Assert.Equal(MissileTargetTrackQuality.Lost, expired.GuidanceSnapshot.Quality);
    }

    [Fact]
    public void ActionEndLinkRefreshDoesNotAgeTheRetainedReport()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(new HexCoord(4, 0));

        Update(
            map,
            salvo,
            NoLineOfSightProfile(),
            new HexCoord(-4, 0),
            MissileTargetTrackSnapshot.Current(
                TargetId,
                new HexCoord(3, 0)));

        MissileDatalinkLinkEvaluation refreshed =
            MissileDatalinkService.RefreshLinkState(
                map,
                salvo,
                Profile(),
                new HexCoord(-4, 0));

        Assert.Equal(MissileDatalinkState.Blocked, refreshed.State);
        Assert.Equal(0, salvo.RetainedDatalinkReport!.AgePhases);
        Assert.Equal(0, salvo.GuidancePhaseCount);
        Assert.Equal(1, salvo.LastDatalinkEvaluationGuidancePhase!.Value);
    }

    [Fact]
    public void LaunchServiceExposesTheCopiedDatalinkUpdate()
    {
        SystemMap map = CreateMap();
        var launch = new HexCoord(-3, 3);
        var target = new HexCoord(0, 3);

        GuidedMissileLaunchResult result =
            MissileLaunchService.LaunchAndAdvanceOnePhase(
                map,
                "salvo",
                TacticalSide.Player,
                "launcher",
                TargetId,
                launch,
                new MissileFlightProfile(2, 8, 1),
                Profile(),
                MissileTargetTrackSnapshot.Current(TargetId, target),
                sourceObservationEpoch: 1);

        Assert.NotNull(result.DatalinkUpdateResult);
        Assert.True(result.DatalinkUpdateResult!.ReportDelivered);
        Assert.Equal(MissileGuidanceReportSource.FreshDatalink, result.DatalinkUpdateResult.GuidanceSource);
        Assert.Equal(1, result.Salvo.GuidancePhaseCount);
        Assert.Equal(1, result.Salvo.DistanceTraveled);
    }

    private static MissileDatalinkUpdateResult Update(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileDatalinkProfile profile,
        HexCoord launcherCoordinate,
        MissileTargetTrackSnapshot launcherTrack,
        int sourceObservationEpoch = 1) =>
        MissileDatalinkService.UpdateForGuidancePhase(
            map,
            salvo,
            profile,
            launcherCoordinate,
            launcherTrack,
            sourceObservationEpoch);

    private static void CountGuidancePhase(
        SystemMap map,
        GuidedMissileSalvo salvo) =>
        MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Lost(TargetId));

    private static MissileDatalinkProfile Profile() => new(
        technologyLevel: 2,
        maximumRetainedReportAgePhases: 3);

    private static MissileDatalinkProfile NoLineOfSightProfile() => new(
        technologyLevel: 2,
        requiresLineOfSight: false,
        maximumRetainedReportAgePhases: 3);

    private static GuidedMissileSalvo CreateSalvo(HexCoord coordinate) => new(
        "salvo",
        TacticalSide.Player,
        "launcher",
        TargetId,
        coordinate,
        new MissileFlightProfile(2, 12, 1));

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            8,
            MapObject.CreateStar("star", "Primary Star"));

    private const string TargetId = "target";
}
