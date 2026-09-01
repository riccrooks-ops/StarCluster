using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Result from launching a sensor-equipped missile and resolving its first
/// autonomous guidance action.
/// </summary>
public sealed class GuidedMissileAutonomousLaunchResult
{
    internal GuidedMissileAutonomousLaunchResult(
        GuidedMissileSalvo salvo,
        MissileDatalinkUpdateResult datalinkUpdateResult,
        MissileAutonomousGuidanceResult autonomousGuidanceResult)
    {
        Salvo = salvo ?? throw new ArgumentNullException(nameof(salvo));
        DatalinkUpdateResult = datalinkUpdateResult ??
            throw new ArgumentNullException(nameof(datalinkUpdateResult));
        AutonomousGuidanceResult = autonomousGuidanceResult ??
            throw new ArgumentNullException(nameof(autonomousGuidanceResult));
    }

    public GuidedMissileSalvo Salvo { get; }

    public MissileDatalinkUpdateResult DatalinkUpdateResult { get; }

    public MissileAutonomousGuidanceResult AutonomousGuidanceResult { get; }

    public GuidedMissileAdvanceResult AdvanceResult =>
        AutonomousGuidanceResult.AdvanceResult;
}
