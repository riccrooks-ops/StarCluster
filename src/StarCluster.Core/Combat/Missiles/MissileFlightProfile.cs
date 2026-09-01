using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Stores the route-relevant performance of one missile or torpedo design.
/// </summary>
/// <remarks>
/// Technology level is recorded, but this checkpoint intentionally does not
/// hard-code a TL-to-performance table. Range and speed remain explicit data
/// so later balance passes can revise the progression without changing the
/// routing or salvo algorithms.
/// </remarks>
public sealed record MissileFlightProfile
{
    public MissileFlightProfile(
        int technologyLevel,
        int maximumRange,
        int speedHexesPerTurn)
    {
        if (technologyLevel is < 1 or > 9)
        {
            throw new ArgumentOutOfRangeException(
                nameof(technologyLevel),
                technologyLevel,
                "Missile technology level must be from 1 through 9.");
        }

        if (maximumRange <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumRange),
                maximumRange,
                "Maximum missile range must be positive.");
        }

        if (speedHexesPerTurn <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(speedHexesPerTurn),
                speedHexesPerTurn,
                "Missile speed must be positive.");
        }

        TechnologyLevel = technologyLevel;
        MaximumRange = maximumRange;
        SpeedHexesPerTurn = speedHexesPerTurn;
    }

    public int TechnologyLevel { get; }

    public int MaximumRange { get; }

    public int SpeedHexesPerTurn { get; }

    /// <summary>
    /// Returns the number of missile-movement turns required to traverse the
    /// supplied routed distance.
    /// </summary>
    public int EstimateTravelTurns(int routedDistance)
    {
        if (routedDistance < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(routedDistance),
                routedDistance,
                "Routed distance cannot be negative.");
        }

        return routedDistance == 0
            ? 0
            : ((routedDistance - 1) / SpeedHexesPerTurn) + 1;
    }
}
