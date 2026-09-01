using System;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Evaluates launcher-to-missile line of sight, copies fresh launcher reports,
/// and ages a missile's retained report exactly once per guidance phase when no
/// new copy arrives.
/// </summary>
public static class MissileDatalinkService
{
    public static MissileDatalinkLinkEvaluation EvaluateLink(
        SystemMap map,
        MissileDatalinkProfile profile,
        HexCoord launcherCoordinate,
        HexCoord missileCoordinate)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(profile);

        if (!profile.IsInstalled)
        {
            return new MissileDatalinkLinkEvaluation(
                MissileDatalinkState.Unavailable,
                launcherCoordinate,
                missileCoordinate,
                lineOfSightQuality: null);
        }

        if (!profile.RequiresLineOfSight ||
            launcherCoordinate == missileCoordinate)
        {
            return new MissileDatalinkLinkEvaluation(
                MissileDatalinkState.Live,
                launcherCoordinate,
                missileCoordinate,
                lineOfSightQuality: null);
        }

        DirectFireLineOfSightResult lineOfSight =
            DirectFireLineOfSight.Evaluate(
                map,
                launcherCoordinate,
                missileCoordinate);

        return new MissileDatalinkLinkEvaluation(
            lineOfSight.Quality == LineOfSightQuality.Blocked
                ? MissileDatalinkState.Blocked
                : MissileDatalinkState.Live,
            launcherCoordinate,
            missileCoordinate,
            lineOfSight.Quality);
    }

    public static MissileDatalinkLinkEvaluation RefreshLinkState(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileDatalinkProfile profile,
        HexCoord launcherCoordinate)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(profile);

        MissileDatalinkLinkEvaluation evaluation = EvaluateLink(
            map,
            profile,
            launcherCoordinate,
            salvo.CurrentCoordinate);
        salvo.SetDatalinkState(evaluation.State);
        return evaluation;
    }

    public static MissileDatalinkUpdateResult UpdateForGuidancePhase(
        SystemMap map,
        GuidedMissileSalvo salvo,
        MissileDatalinkProfile profile,
        HexCoord launcherCoordinate,
        MissileTargetTrackSnapshot launcherTrack,
        int sourceObservationEpoch)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(launcherTrack);

        if (!string.Equals(
                salvo.TargetId,
                launcherTrack.TargetId,
                StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "The supplied launcher track does not belong to this missile salvo.",
                nameof(launcherTrack));
        }

        if (sourceObservationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(sourceObservationEpoch));
        }

        int guidancePhaseNumber = checked(salvo.GuidancePhaseCount + 1);
        MissileDatalinkLinkEvaluation linkEvaluation = EvaluateLink(
            map,
            profile,
            launcherCoordinate,
            salvo.CurrentCoordinate);

        bool duplicateSamePhase =
            salvo.LastDatalinkEvaluationGuidancePhase == guidancePhaseNumber;
        bool reportDelivered = false;
        bool retainedReportAged = false;
        MissileDatalinkReport? retainedReport =
            salvo.RetainedDatalinkReport;

        if (!duplicateSamePhase &&
            linkEvaluation.IsLive &&
            launcherTrack.HasGuidanceCoordinate)
        {
            retainedReport = MissileDatalinkReport.CopyFrom(
                launcherTrack,
                sourceObservationEpoch,
                guidancePhaseNumber);
            reportDelivered = true;
        }
        else if (!duplicateSamePhase && retainedReport is not null)
        {
            retainedReport = retainedReport.AgeOnePhase();
            retainedReportAged = true;
        }

        salvo.ApplyDatalinkEvaluation(
            guidancePhaseNumber,
            linkEvaluation.State,
            retainedReport);

        MissileTargetTrackSnapshot guidanceSnapshot = retainedReport is null
            ? MissileTargetTrackSnapshot.Lost(salvo.TargetId)
            : retainedReport.CreateGuidanceSnapshot(
                profile.MaximumRetainedReportAgePhases);

        bool retainedReportExpired =
            retainedReport is not null &&
            guidanceSnapshot.Quality == MissileTargetTrackQuality.Lost;
        MissileGuidanceReportSource guidanceSource = reportDelivered
            ? MissileGuidanceReportSource.FreshDatalink
            : guidanceSnapshot.HasGuidanceCoordinate
                ? MissileGuidanceReportSource.RetainedDatalink
                : MissileGuidanceReportSource.None;

        return new MissileDatalinkUpdateResult(
            linkEvaluation,
            guidancePhaseNumber,
            launcherTrack.Quality,
            reportDelivered,
            retainedReportAged,
            retainedReportExpired,
            guidanceSource,
            retainedReport,
            guidanceSnapshot);
    }
}
