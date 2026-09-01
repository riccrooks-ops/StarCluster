using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Immutable result of attempting one datalink update for the next missile
/// guidance phase.
/// </summary>
public sealed class MissileDatalinkUpdateResult
{
    internal MissileDatalinkUpdateResult(
        MissileDatalinkLinkEvaluation linkEvaluation,
        int guidancePhaseNumber,
        MissileTargetTrackQuality launcherTrackQuality,
        bool reportDelivered,
        bool retainedReportAged,
        bool retainedReportExpired,
        MissileGuidanceReportSource guidanceSource,
        MissileDatalinkReport? retainedReport,
        MissileTargetTrackSnapshot guidanceSnapshot)
    {
        LinkEvaluation = linkEvaluation ??
            throw new ArgumentNullException(nameof(linkEvaluation));

        if (guidancePhaseNumber <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(guidancePhaseNumber));
        }

        if (!Enum.IsDefined(launcherTrackQuality))
        {
            throw new ArgumentOutOfRangeException(
                nameof(launcherTrackQuality));
        }

        if (!Enum.IsDefined(guidanceSource))
        {
            throw new ArgumentOutOfRangeException(nameof(guidanceSource));
        }

        GuidancePhaseNumber = guidancePhaseNumber;
        LauncherTrackQuality = launcherTrackQuality;
        ReportDelivered = reportDelivered;
        RetainedReportAged = retainedReportAged;
        RetainedReportExpired = retainedReportExpired;
        GuidanceSource = guidanceSource;
        RetainedReport = retainedReport;
        GuidanceSnapshot = guidanceSnapshot ??
            throw new ArgumentNullException(nameof(guidanceSnapshot));
    }

    public MissileDatalinkLinkEvaluation LinkEvaluation { get; }

    public MissileDatalinkState State => LinkEvaluation.State;

    public int GuidancePhaseNumber { get; }

    public MissileTargetTrackQuality LauncherTrackQuality { get; }

    public bool ReportDelivered { get; }

    public bool RetainedReportAged { get; }

    public bool RetainedReportExpired { get; }

    public MissileGuidanceReportSource GuidanceSource { get; }

    public MissileDatalinkReport? RetainedReport { get; }

    public MissileTargetTrackSnapshot GuidanceSnapshot { get; }
}
