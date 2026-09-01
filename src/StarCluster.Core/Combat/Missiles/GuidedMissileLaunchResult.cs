using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Immutable result from creating a guided missile salvo and resolving exactly
/// one launch-phase guidance and movement advance.
/// </summary>
public sealed class GuidedMissileLaunchResult
{
    internal GuidedMissileLaunchResult(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult advanceResult)
        : this(
            salvo,
            advanceResult,
            datalinkUpdateResult: null)
    {
    }

    internal GuidedMissileLaunchResult(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult advanceResult,
        MissileDatalinkUpdateResult? datalinkUpdateResult)
    {
        Salvo = salvo ?? throw new ArgumentNullException(nameof(salvo));
        AdvanceResult = advanceResult ??
            throw new ArgumentNullException(nameof(advanceResult));
        DatalinkUpdateResult = datalinkUpdateResult;
    }

    public GuidedMissileSalvo Salvo { get; }

    public GuidedMissileAdvanceResult AdvanceResult { get; }

    public MissileDatalinkUpdateResult? DatalinkUpdateResult { get; }
}
