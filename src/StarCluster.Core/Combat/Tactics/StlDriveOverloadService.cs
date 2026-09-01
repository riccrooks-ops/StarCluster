using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;

namespace StarCluster.Core.Combat.Tactics;

public enum StlDriveOverloadOutcome
{
    Ineligible,
    SafeSuccess,
    ForcedSuccess,
    ForcedFailure,
    CriticalSuccess,
    CriticalFailure,
}

public sealed record StlDriveOverloadProfile
{
    public StlDriveOverloadProfile(
        int driveTechnologyLevel,
        int tacticalPowerCost,
        int extraFuelCost,
        int strainCost,
        int strainLimit,
        int forcedSuccessChance)
    {
        _ = TechnologyMovementRules.ShipStlMovement(driveTechnologyLevel);
        if (tacticalPowerCost < 0 || extraFuelCost < 0 || strainCost < 0 ||
            strainLimit < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(tacticalPowerCost),
                "STL overload costs and limits must be non-negative.");
        }
        if (forcedSuccessChance is < 1 or > 99)
        {
            throw new ArgumentOutOfRangeException(nameof(forcedSuccessChance));
        }

        DriveTechnologyLevel = driveTechnologyLevel;
        TacticalPowerCost = tacticalPowerCost;
        ExtraFuelCost = extraFuelCost;
        StrainCost = strainCost;
        StrainLimit = strainLimit;
        ForcedSuccessChance = forcedSuccessChance;
    }

    public int DriveTechnologyLevel { get; }

    public int TacticalPowerCost { get; }

    public int ExtraFuelCost { get; }

    public int StrainCost { get; }

    public int StrainLimit { get; }

    public int ForcedSuccessChance { get; }

    public static StlDriveOverloadProfile Tl1 { get; } = new(
        driveTechnologyLevel: 1,
        tacticalPowerCost: 1,
        extraFuelCost: 2,
        strainCost: 1,
        strainLimit: 2,
        forcedSuccessChance: 60);
}

public sealed record StlDriveOverloadResult(
    StlDriveOverloadOutcome Outcome,
    bool BenefitApplied,
    int BaseMovement,
    int MovementBonus,
    int EffectiveMovement,
    int TacticalPowerCost,
    int ExtraFuelCost,
    int StrainApplied,
    bool ConditionStepRequired,
    string Reason);

public static class StlDriveOverloadService
{
    public static StlDriveOverloadResult Resolve(
        StlDriveOverloadProfile profile,
        ComponentCondition driveCondition,
        int currentStrain,
        int availableTacticalPower,
        int availableFuel,
        int? forcedRoll = null)
    {
        ArgumentNullException.ThrowIfNull(profile);
        if (currentStrain < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(currentStrain));
        }
        if (availableTacticalPower < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(availableTacticalPower));
        }
        if (availableFuel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(availableFuel));
        }
        if (forcedRoll is < 1 or > 100)
        {
            throw new ArgumentOutOfRangeException(nameof(forcedRoll));
        }

        int normalMovement = TechnologyMovementRules.ShipStlMovement(
            profile.DriveTechnologyLevel);
        int baseMovement = ComponentPerformance.StlMovement(
            normalMovement,
            driveCondition);
        if (driveCondition != ComponentCondition.Operational)
        {
            return Ineligible(
                baseMovement,
                profile,
                "Only an Operational STL Drive may use overload movement.");
        }
        if (availableTacticalPower < profile.TacticalPowerCost)
        {
            return Ineligible(baseMovement, profile, "Insufficient Tactical Power.");
        }
        if (availableFuel < profile.ExtraFuelCost)
        {
            return Ineligible(baseMovement, profile, "Insufficient fuel for emergency thrust.");
        }

        int resultingStrain = checked(currentStrain + profile.StrainCost);
        if (resultingStrain <= profile.StrainLimit)
        {
            return Success(
                StlDriveOverloadOutcome.SafeSuccess,
                baseMovement,
                profile,
                profile.StrainCost,
                "The overload remains within the STL Drive Strain Limit.");
        }
        if (forcedRoll is null)
        {
            throw new InvalidOperationException(
                "An STL overload beyond the Strain Limit requires a d100 roll.");
        }
        if (forcedRoll == 100)
        {
            return Success(
                StlDriveOverloadOutcome.CriticalSuccess,
                baseMovement,
                profile,
                Math.Max(0, profile.StrainCost - 1),
                "Critical success applies emergency thrust with reduced Strain.");
        }
        if (forcedRoll == 1)
        {
            return new StlDriveOverloadResult(
                StlDriveOverloadOutcome.CriticalFailure,
                false,
                baseMovement,
                0,
                baseMovement,
                profile.TacticalPowerCost,
                profile.ExtraFuelCost,
                profile.StrainCost,
                true,
                "Critical failure applies Strain and worsens the STL Drive one condition step.");
        }
        if (forcedRoll <= profile.ForcedSuccessChance)
        {
            return Success(
                StlDriveOverloadOutcome.ForcedSuccess,
                baseMovement,
                profile,
                profile.StrainCost,
                "Forced overload succeeded.");
        }

        return new StlDriveOverloadResult(
            StlDriveOverloadOutcome.ForcedFailure,
            false,
            baseMovement,
            0,
            baseMovement,
            profile.TacticalPowerCost,
            profile.ExtraFuelCost,
            profile.StrainCost,
            false,
            "Forced overload failed; declared costs and Strain still apply.");
    }

    private static StlDriveOverloadResult Success(
        StlDriveOverloadOutcome outcome,
        int baseMovement,
        StlDriveOverloadProfile profile,
        int strainApplied,
        string reason)
    {
        int bonus = TechnologyMovementRules.StlOverloadMovementBonus(
            profile.DriveTechnologyLevel);
        return new StlDriveOverloadResult(
            outcome,
            true,
            baseMovement,
            bonus,
            checked(baseMovement + bonus),
            profile.TacticalPowerCost,
            profile.ExtraFuelCost,
            strainApplied,
            false,
            reason);
    }

    private static StlDriveOverloadResult Ineligible(
        int baseMovement,
        StlDriveOverloadProfile profile,
        string reason) => new(
        StlDriveOverloadOutcome.Ineligible,
        false,
        baseMovement,
        0,
        baseMovement,
        0,
        0,
        0,
        false,
        reason);
}
