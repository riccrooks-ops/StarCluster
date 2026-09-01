using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Immutable report from one interception attempt.
/// </summary>
public sealed class MissileInterceptionAttemptResult
{
    internal MissileInterceptionAttemptResult(
        MissileInterceptionAttempt attempt,
        MissileInterceptionOutcome outcome)
    {
        Attempt = attempt ?? throw new ArgumentNullException(nameof(attempt));

        if (!Enum.IsDefined(outcome))
        {
            throw new ArgumentOutOfRangeException(nameof(outcome), outcome, null);
        }

        Outcome = outcome;
    }

    public MissileInterceptionAttempt Attempt { get; }

    public MissileInterceptionOutcome Outcome { get; }

    public string DefenseSystemId => Attempt.DefenseSystem.Id;

    public string DefenderShipId => Attempt.DefenseSystem.DefenderShipId;

    public string SalvoId => Attempt.Salvo.Id;

    public HexCoord MissileCoordinate => Attempt.MissileCoordinate;

    public int AttemptNumberForSystemThisPhase =>
        Attempt.AttemptNumberForSystemThisPhase;

    public MissileInterceptionOpportunity Opportunity => Attempt.Opportunity;

    public bool IsFinalApproach => Attempt.IsFinalApproach;

    public bool Intercepted => Outcome == MissileInterceptionOutcome.Intercepted;
}
