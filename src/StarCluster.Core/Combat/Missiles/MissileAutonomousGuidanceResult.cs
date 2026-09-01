using System;
using System.Collections.Generic;
using System.Linq;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Result of one action that combines datalink input, local sensor updates,
/// deterministic arbitration, and per-entered-hex replanning.
/// </summary>
public sealed class MissileAutonomousGuidanceResult
{
    internal MissileAutonomousGuidanceResult(
        GuidedMissileAdvanceResult advanceResult,
        MissileGuidanceDecision initialDecision,
        MissileGuidanceDecision finalDecision,
        IEnumerable<MissileAutonomousGuidanceStep> steps)
    {
        AdvanceResult = advanceResult ??
            throw new ArgumentNullException(nameof(advanceResult));
        InitialDecision = initialDecision ??
            throw new ArgumentNullException(nameof(initialDecision));
        FinalDecision = finalDecision ??
            throw new ArgumentNullException(nameof(finalDecision));
        Steps = Array.AsReadOnly(steps.ToArray());
    }

    public GuidedMissileAdvanceResult AdvanceResult { get; }

    public MissileGuidanceDecision InitialDecision { get; }

    public MissileGuidanceDecision FinalDecision { get; }

    public IReadOnlyList<MissileAutonomousGuidanceStep> Steps { get; }

    public int ReplanCount => Steps.Count(step => step.GuidanceChanged);
}
