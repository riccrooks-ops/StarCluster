using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Immutable input supplied to an interception resolver.
/// </summary>
public sealed class MissileInterceptionAttempt
{
    internal MissileInterceptionAttempt(
        MissileDefenseSystem defenseSystem,
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate,
        int attemptNumberForSystemThisPhase,
        MissileInterceptionOpportunity opportunity)
    {
        DefenseSystem = defenseSystem ??
            throw new ArgumentNullException(nameof(defenseSystem));
        Salvo = salvo ?? throw new ArgumentNullException(nameof(salvo));

        if (attemptNumberForSystemThisPhase <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(attemptNumberForSystemThisPhase),
                attemptNumberForSystemThisPhase,
                "Attempt numbers begin at one.");
        }
        if (!Enum.IsDefined(opportunity))
        {
            throw new ArgumentOutOfRangeException(nameof(opportunity));
        }

        MissileCoordinate = missileCoordinate;
        AttemptNumberForSystemThisPhase = attemptNumberForSystemThisPhase;
        Opportunity = opportunity;
    }

    public MissileDefenseSystem DefenseSystem { get; }

    public GuidedMissileSalvo Salvo { get; }

    public HexCoord MissileCoordinate { get; }

    public int AttemptNumberForSystemThisPhase { get; }

    public MissileInterceptionOpportunity Opportunity { get; }

    public bool IsFinalApproach => Opportunity is
        MissileInterceptionOpportunity.TerminalEntry or
        MissileInterceptionOpportunity.PreTerminalAttack;
}
