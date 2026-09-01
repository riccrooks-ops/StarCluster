using System;

namespace StarCluster.Core.Combat.Tactics;

/// <summary>
/// KISS tactical fuel accounting for ship movement. Fuel is a single integer
/// resource; the rule deliberately avoids fractional burn rates.
/// </summary>
public sealed record TacticalFuelRules(
    int StartingFuel,
    int FuelPerTraversedHex,
    int EvasiveManeuverFuelCost)
{
    public static TacticalFuelRules Baseline { get; } = new(100, 2, 1);

    public int MovementCost(int traversedHexes, bool evasiveManeuvers)
    {
        if (traversedHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(traversedHexes));
        }
        return checked(
            (traversedHexes * FuelPerTraversedHex) +
            (evasiveManeuvers ? EvasiveManeuverFuelCost : 0));
    }

    public int AffordableMovementHexes(int fuelAvailable, bool evasiveManeuvers)
    {
        if (fuelAvailable < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(fuelAvailable));
        }
        int movementFuel = Math.Max(
            0,
            fuelAvailable - (evasiveManeuvers ? EvasiveManeuverFuelCost : 0));
        return FuelPerTraversedHex <= 0
            ? int.MaxValue
            : movementFuel / FuelPerTraversedHex;
    }
}
