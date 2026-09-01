using System;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Central terminal contract. It validates a co-located Current/Firm solution,
/// optionally uses a seeker to produce one, and resolves exactly one d100
/// terminal attack after defenses have had their pre-attack opportunity.
/// </summary>
public static class MissileTerminalResolutionService
{
    public static MissileTerminalResolution EvaluateAcquisition(
        GuidedMissileSalvo salvo,
        HexCoord actualTargetCoordinate,
        MissileGuidanceReportSource reportSource,
        MissileTargetTrackSnapshot report,
        MissileDatalinkState datalinkState,
        bool onboardNavigationSensorInstalled,
        int targetTerminalEcmStrength,
        IMissileTerminalRandomSource randomSource)
    {
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(report);
        ArgumentNullException.ThrowIfNull(randomSource);
        if (targetTerminalEcmStrength < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(targetTerminalEcmStrength));
        }
        if (!string.Equals(
                salvo.TargetId,
                report.TargetId,
                StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "The terminal report belongs to a different target.",
                nameof(report));
        }

        bool coLocated = salvo.CurrentCoordinate == actualTargetCoordinate;
        if (!coLocated)
        {
            return new MissileTerminalResolution(
                salvo.CurrentCoordinate,
                reportSource,
                report.Quality,
                targetCoLocated: false,
                usedSeekerAcquisition: false,
                acquisitionRoll: null,
                acquisitionChancePercent: null,
                hasFirmSolution: false,
                seekerAccuracyApplied: false,
                attackRoll: null,
                effectiveHitChancePercent: null,
                MissileTerminalOutcome.AcquisitionFailed,
                "The Missile Flight reached a candidate coordinate, but the target was not co-located.");
        }

        bool liveFirmRemote =
            report.Quality == MissileTargetTrackQuality.Current &&
            reportSource == MissileGuidanceReportSource.FreshDatalink &&
            datalinkState == MissileDatalinkState.Live;
        bool liveFirmPeer =
            report.Quality == MissileTargetTrackQuality.Current &&
            reportSource == MissileGuidanceReportSource.PeerGuidance &&
            salvo.TerminalProfile.AllowsPeerTerminalGuidance;
        bool firmLocal =
            report.Quality == MissileTargetTrackQuality.Current &&
            reportSource == MissileGuidanceReportSource.LocalSensor &&
            onboardNavigationSensorInstalled;
        bool hasLegitimateFirmReport =
            liveFirmRemote || liveFirmPeer || firmLocal;

        bool seekerInstalled = salvo.TerminalProfile.Seeker.IsInstalled;
        bool seekerOnly = seekerInstalled && !onboardNavigationSensorInstalled;
        if (hasLegitimateFirmReport && !seekerOnly)
        {
            return new MissileTerminalResolution(
                salvo.CurrentCoordinate,
                reportSource,
                report.Quality,
                targetCoLocated: true,
                usedSeekerAcquisition: false,
                acquisitionRoll: null,
                acquisitionChancePercent: null,
                hasFirmSolution: true,
                seekerAccuracyApplied: false,
                attackRoll: null,
                effectiveHitChancePercent: null,
                MissileTerminalOutcome.None,
                "A legitimate live Current/Firm launcher, explicitly enabled peer, or missile-local report supplied the terminal solution.");
        }

        MissileGuidanceReportSource seekerCueSource = reportSource;
        MissileTargetTrackSnapshot seekerCue = report;
        bool seekerMayAttempt = false;
        if (seekerOnly)
        {
            // A seeker-only architecture has no general navigation sensor. Its
            // co-located seeker performs the local acquisition step from the
            // remote Current/Approximate cue that brought it into the target hex.
            seekerMayAttempt = report.Quality is
                MissileTargetTrackQuality.Current or
                MissileTargetTrackQuality.Approximate;
        }
        else if (seekerInstalled && onboardNavigationSensorInstalled)
        {
            // A sensor-plus-seeker architecture may not turn a merely remote
            // Approximate cue directly into terminal Firm. The seeker refines an
            // existing missile-local navigation track. Prefer the live local
            // report even when arbitration selected a remote report for cruise.
            MissileTargetTrackSnapshot? localCue = reportSource == MissileGuidanceReportSource.LocalSensor
                ? report
                : salvo.LocalSensorTrack?.CreateGuidanceSnapshot();
            if (localCue is not null &&
                localCue.Quality is MissileTargetTrackQuality.Current or MissileTargetTrackQuality.Approximate)
            {
                seekerCueSource = MissileGuidanceReportSource.LocalSensor;
                seekerCue = localCue;
                seekerMayAttempt = true;
            }
        }

        if (!seekerMayAttempt)
        {
            string reason = seekerInstalled && onboardNavigationSensorInstalled
                ? "A sensor-plus-seeker missile requires at least an Approximate missile-local navigation track before the seeker may refine it into terminal Firm."
                : report.Quality is MissileTargetTrackQuality.Stale or MissileTargetTrackQuality.Lost
                    ? "A seeker-only missile requires at least a Current/Firm or Approximate remote cue before co-located terminal acquisition."
                    : "No legitimate live Firm report or eligible local seeker-acquisition path could produce a terminal solution.";
            return new MissileTerminalResolution(
                salvo.CurrentCoordinate,
                reportSource,
                report.Quality,
                targetCoLocated: true,
                usedSeekerAcquisition: false,
                acquisitionRoll: null,
                acquisitionChancePercent: null,
                hasFirmSolution: false,
                seekerAccuracyApplied: false,
                attackRoll: null,
                effectiveHitChancePercent: null,
                MissileTerminalOutcome.AcquisitionFailed,
                reason);
        }

        MissileTerminalSeekerProfile seeker = salvo.TerminalProfile.Seeker;
        int netEcmStrength = Math.Max(
            0,
            targetTerminalEcmStrength - seeker.TerminalEccmStrength);
        int rawChance = checked(
            seeker.BaseAcquisitionChancePercent -
            (netEcmStrength *
             salvo.TerminalProfile.AcquisitionPenaltyPercentPerNetEcmStrength));
        int chance = seeker.ClampAcquisitionChance(rawChance);
        int roll = NextValidatedRoll(randomSource);
        bool acquired = roll <= chance;

        return new MissileTerminalResolution(
            salvo.CurrentCoordinate,
            seekerCueSource,
            seekerCue.Quality,
            targetCoLocated: true,
            usedSeekerAcquisition: true,
            acquisitionRoll: roll,
            acquisitionChancePercent: chance,
            hasFirmSolution: acquired,
            seekerAccuracyApplied: false,
            attackRoll: null,
            effectiveHitChancePercent: null,
            acquired
                ? MissileTerminalOutcome.None
                : MissileTerminalOutcome.AcquisitionFailed,
            acquired
                ? "The co-located seeker converted the available cue into a Firm terminal solution."
                : "The co-located seeker failed to convert the available cue into a Firm terminal solution.");
    }

    public static MissileTerminalResolution ResolveAttack(
        GuidedMissileSalvo salvo,
        MissileTerminalResolution acquisition,
        IMissileTerminalRandomSource randomSource,
        ComponentCondition targetStlCondition = ComponentCondition.Operational)
    {
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(acquisition);
        ArgumentNullException.ThrowIfNull(randomSource);
        if (!acquisition.HasFirmSolution)
        {
            throw new InvalidOperationException(
                "A Missile Flight cannot roll a terminal attack without a Firm solution.");
        }

        bool seekerAccuracyApplied = salvo.TerminalProfile.Seeker.IsInstalled;
        int rawChance = checked(
            salvo.TerminalProfile.GuidanceComputer.BaseHitChancePercent +
            (seekerAccuracyApplied
                ? salvo.TerminalProfile.Seeker.AccuracyBonusPercent
                : 0) +
            ComponentPerformance.TargetMobilityAccuracyBonus(
                targetStlCondition));
        int chance = salvo.TerminalProfile.GuidanceComputer.ClampHitChance(
            rawChance);
        int roll = NextValidatedRoll(randomSource);

        MissileTerminalOutcome outcome;
        string reason;
        if (roll == 1)
        {
            outcome = MissileTerminalOutcome.Dud;
            reason = "Natural 01: terminal fuse or activation failure; an inert recoverable dud remains.";
        }
        else if (roll == 100)
        {
            outcome = MissileTerminalOutcome.CriticalHit;
            reason = "Natural 100: the terminal attack hit and recorded a critical result for later damage resolution.";
        }
        else if (roll <= chance)
        {
            outcome = MissileTerminalOutcome.Hit;
            reason = "The terminal attack roll was within the Guidance Computer's bounded hit chance.";
        }
        else
        {
            outcome = MissileTerminalOutcome.Miss;
            reason = "The terminal attack failed; the Missile Flight was expended in an ineffective detonation.";
        }

        return acquisition.WithAttack(
            seekerAccuracyApplied,
            roll,
            chance,
            outcome,
            reason);
    }

    private static int NextValidatedRoll(
        IMissileTerminalRandomSource randomSource)
    {
        int roll = randomSource.NextD100();
        if (roll is < 1 or > 100)
        {
            throw new InvalidOperationException(
                $"The terminal random source returned invalid d100 roll {roll}.");
        }

        return roll;
    }
}
