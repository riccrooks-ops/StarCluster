using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Immutable authoritative record of one terminal opportunity. Acquisition and
/// attack rolls remain explicit so diagnostics can distinguish no solution,
/// interception, dud, miss, hit, and critical hit.
/// </summary>
public sealed class MissileTerminalResolution
{
    internal MissileTerminalResolution(
        HexCoord opportunityCoordinate,
        MissileGuidanceReportSource reportSource,
        MissileTargetTrackQuality reportQuality,
        bool targetCoLocated,
        bool usedSeekerAcquisition,
        int? acquisitionRoll,
        int? acquisitionChancePercent,
        bool hasFirmSolution,
        bool seekerAccuracyApplied,
        int? attackRoll,
        int? effectiveHitChancePercent,
        MissileTerminalOutcome outcome,
        string reason)
    {
        if (!Enum.IsDefined(reportSource))
        {
            throw new ArgumentOutOfRangeException(nameof(reportSource));
        }
        if (!Enum.IsDefined(reportQuality))
        {
            throw new ArgumentOutOfRangeException(nameof(reportQuality));
        }
        if (!Enum.IsDefined(outcome))
        {
            throw new ArgumentOutOfRangeException(nameof(outcome));
        }

        OpportunityCoordinate = opportunityCoordinate;
        ReportSource = reportSource;
        ReportQuality = reportQuality;
        TargetCoLocated = targetCoLocated;
        UsedSeekerAcquisition = usedSeekerAcquisition;
        AcquisitionRoll = acquisitionRoll;
        AcquisitionChancePercent = acquisitionChancePercent;
        HasFirmSolution = hasFirmSolution;
        SeekerAccuracyApplied = seekerAccuracyApplied;
        AttackRoll = attackRoll;
        EffectiveHitChancePercent = effectiveHitChancePercent;
        Outcome = outcome;
        Reason = string.IsNullOrWhiteSpace(reason)
            ? "No terminal-resolution reason was supplied."
            : reason;
    }

    public HexCoord OpportunityCoordinate { get; }

    public MissileGuidanceReportSource ReportSource { get; }

    public MissileTargetTrackQuality ReportQuality { get; }

    public bool TargetCoLocated { get; }

    public bool UsedSeekerAcquisition { get; }

    public int? AcquisitionRoll { get; }

    public int? AcquisitionChancePercent { get; }

    public bool HasFirmSolution { get; }

    public bool SeekerAccuracyApplied { get; }

    public int? AttackRoll { get; }

    public int? EffectiveHitChancePercent { get; }

    public MissileTerminalOutcome Outcome { get; }

    public string Reason { get; }

    public bool AttackWasResolved => AttackRoll.HasValue;

    public bool IsHit => Outcome is
        MissileTerminalOutcome.Hit or
        MissileTerminalOutcome.CriticalHit;

    public bool IsCriticalHit => Outcome == MissileTerminalOutcome.CriticalHit;

    public bool IsDud => Outcome == MissileTerminalOutcome.Dud;

    internal MissileTerminalResolution WithOutcome(
        MissileTerminalOutcome outcome,
        string reason) => new(
            OpportunityCoordinate,
            ReportSource,
            ReportQuality,
            TargetCoLocated,
            UsedSeekerAcquisition,
            AcquisitionRoll,
            AcquisitionChancePercent,
            HasFirmSolution,
            SeekerAccuracyApplied,
            AttackRoll,
            EffectiveHitChancePercent,
            outcome,
            reason);

    internal MissileTerminalResolution WithAttack(
        bool seekerAccuracyApplied,
        int attackRoll,
        int effectiveHitChancePercent,
        MissileTerminalOutcome outcome,
        string reason) => new(
            OpportunityCoordinate,
            ReportSource,
            ReportQuality,
            TargetCoLocated,
            UsedSeekerAcquisition,
            AcquisitionRoll,
            AcquisitionChancePercent,
            HasFirmSolution,
            seekerAccuracyApplied,
            attackRoll,
            effectiveHitChancePercent,
            outcome,
            reason);
}
