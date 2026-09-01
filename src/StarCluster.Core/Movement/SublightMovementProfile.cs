using System;

namespace StarCluster.Core.Movement;

/// <summary>
/// Stores the data-driven performance used for one ship's tactical movement.
/// The final TL-to-allowance progression remains balance data rather than an
/// algorithmic assumption.
/// </summary>
public sealed class SublightMovementProfile
{
    public SublightMovementProfile(int technologyLevel, int maximumHexesPerTurn)
    {
        if (technologyLevel is < 1 or > 9)
        {
            throw new ArgumentOutOfRangeException(
                nameof(technologyLevel),
                technologyLevel,
                "Sublight Propulsion technology level must be from 1 through 9.");
        }

        if (maximumHexesPerTurn < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumHexesPerTurn),
                maximumHexesPerTurn,
                "Maximum movement cannot be negative.");
        }

        TechnologyLevel = technologyLevel;
        MaximumHexesPerTurn = maximumHexesPerTurn;
    }

    public int TechnologyLevel { get; }

    public int MaximumHexesPerTurn { get; }
}
