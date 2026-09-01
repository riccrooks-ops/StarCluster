namespace StarCluster.Core.Combat.Tactics;

public static class TechnologyMovementRules
{
    public const int MinimumTechnologyLevel = 1;
    public const int MaximumTechnologyLevel = 9;

    public static int ShipStlMovement(int driveTechnologyLevel)
    {
        ValidateTechnologyLevel(driveTechnologyLevel);
        return driveTechnologyLevel;
    }

    public static int MissileMovement(int driveTechnologyLevel)
    {
        ValidateTechnologyLevel(driveTechnologyLevel);
        return checked(driveTechnologyLevel + 1);
    }

    public static int StlOverloadMovementBonus(int driveTechnologyLevel) =>
        ShipStlMovement(driveTechnologyLevel);

    public static int ShipStlMovementWithOverload(int driveTechnologyLevel) =>
        checked(
            ShipStlMovement(driveTechnologyLevel) +
            StlOverloadMovementBonus(driveTechnologyLevel));

    private static void ValidateTechnologyLevel(int technologyLevel)
    {
        if (technologyLevel < MinimumTechnologyLevel ||
            technologyLevel > MaximumTechnologyLevel)
        {
            throw new ArgumentOutOfRangeException(
                nameof(technologyLevel),
                technologyLevel,
                $"Technology level must be between {MinimumTechnologyLevel} " +
                $"and {MaximumTechnologyLevel}.");
        }
    }
}
