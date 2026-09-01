using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Power;

namespace StarCluster.Core.Combat.InternalDamage;

public sealed record DamageControlProfile
{
    public DamageControlProfile(
        int capacityPerTurn,
        int startingRepairKits,
        int tacticalPowerCost,
        int degradedRepairChancePercent,
        int disabledRepairChancePercent,
        int hullRepairChancePercent)
    {
        if (capacityPerTurn <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(capacityPerTurn));
        }
        if (startingRepairKits < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(startingRepairKits));
        }
        if (tacticalPowerCost <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(tacticalPowerCost));
        }
        ValidateChance(degradedRepairChancePercent, nameof(degradedRepairChancePercent));
        ValidateChance(disabledRepairChancePercent, nameof(disabledRepairChancePercent));
        ValidateChance(hullRepairChancePercent, nameof(hullRepairChancePercent));

        CapacityPerTurn = capacityPerTurn;
        StartingRepairKits = startingRepairKits;
        TacticalPowerCost = tacticalPowerCost;
        DegradedRepairChancePercent = degradedRepairChancePercent;
        DisabledRepairChancePercent = disabledRepairChancePercent;
        HullRepairChancePercent = hullRepairChancePercent;
    }

    public static DamageControlProfile Tl1 { get; } = new(
        capacityPerTurn: 1,
        startingRepairKits: 3,
        tacticalPowerCost: 1,
        degradedRepairChancePercent: 70,
        disabledRepairChancePercent: 50,
        hullRepairChancePercent: 40);

    public static DamageControlProfile Tl1CalibrationFiveKits { get; } = new(
        capacityPerTurn: 1,
        startingRepairKits: 5,
        tacticalPowerCost: 1,
        degradedRepairChancePercent: 70,
        disabledRepairChancePercent: 50,
        hullRepairChancePercent: 40);

    public int CapacityPerTurn { get; }

    public int StartingRepairKits { get; }

    public int TacticalPowerCost { get; }

    public int DegradedRepairChancePercent { get; }

    public int DisabledRepairChancePercent { get; }

    public int HullRepairChancePercent { get; }

    private static void ValidateChance(int chance, string name)
    {
        if (chance is < 0 or > 100)
        {
            throw new ArgumentOutOfRangeException(name);
        }
    }
}

public sealed class DamageControlState
{
    public DamageControlState(DamageControlProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);
        Profile = profile;
        RepairKitsRemaining = profile.StartingRepairKits;
    }

    public DamageControlProfile Profile { get; }

    public int RepairKitsRemaining { get; private set; }

    public int AttemptsThisTurn { get; private set; }

    public bool HasAttemptCapacity => AttemptsThisTurn < Profile.CapacityPerTurn;

    public bool HasRepairKits => RepairKitsRemaining > 0;

    public void BeginTurn() => AttemptsThisTurn = 0;

    internal void RequireAttemptAvailable()
    {
        if (AttemptsThisTurn >= Profile.CapacityPerTurn)
        {
            throw new InvalidOperationException(
                "Damage Control Capacity has been exhausted for this turn.");
        }
        if (RepairKitsRemaining <= 0)
        {
            throw new InvalidOperationException("No Repair Kits remain.");
        }
    }

    internal void ConsumeAttempt()
    {
        RequireAttemptAvailable();
        AttemptsThisTurn++;
        RepairKitsRemaining--;
    }
}

public enum PendingRepairKind
{
    Component,
    Hull,
}

public sealed record PendingRepair(
    PendingRepairKind Kind,
    string? ComponentId);

public sealed record DamageControlAttemptResult(
    PendingRepairKind Kind,
    string? ComponentId,
    int ChancePercent,
    int Roll,
    bool Succeeded,
    int TacticalPowerSpent,
    int RepairKitsRemaining,
    bool ActivatesAtNextTurnRefresh);

public sealed record DamageControlEligibility(
    bool ShipEligible,
    bool HasRepairableComponentDamage,
    bool HasRepairableHullDamage,
    bool HasAttemptCapacity,
    bool HasRepairKit,
    bool HasTacticalPower,
    bool CanAttempt);

public static class DamageControlService
{
    public static bool HasRepairableComponentDamage(ShipDamageState ship)
    {
        ArgumentNullException.ThrowIfNull(ship);
        return ship.Components.Any(component =>
            component.Condition is ComponentCondition.Degraded or
                ComponentCondition.Disabled);
    }

    public static bool HasRepairableHullDamage(ShipDamageState ship)
    {
        ArgumentNullException.ThrowIfNull(ship);
        return ship.Defense.CurrentHull > 0 &&
            ship.Defense.CurrentHull < ship.Defense.PristineHull;
    }

    public static bool HasAnyRepairableDamage(ShipDamageState ship) =>
        HasRepairableComponentDamage(ship) || HasRepairableHullDamage(ship);

    public static DamageControlEligibility EvaluateEligibility(
        ShipDamageState ship,
        TacticalPowerLedger power)
    {
        ArgumentNullException.ThrowIfNull(ship);
        ArgumentNullException.ThrowIfNull(power);
        bool shipEligible = !ship.IsDestroyed &&
            !ship.IsPendingDestruction &&
            ship.Defense.CurrentHull > 0;
        bool componentDamage = HasRepairableComponentDamage(ship);
        bool hullDamage = HasRepairableHullDamage(ship);
        bool capacity = ship.DamageControl.HasAttemptCapacity;
        bool repairKit = ship.DamageControl.HasRepairKits;
        bool tacticalPower = power.SpendablePower >=
            ship.DamageControl.Profile.TacticalPowerCost;
        return new DamageControlEligibility(
            shipEligible,
            componentDamage,
            hullDamage,
            capacity,
            repairKit,
            tacticalPower,
            shipEligible &&
                (componentDamage || hullDamage) &&
                capacity &&
                repairKit &&
                tacticalPower);
    }

    public static bool CanAttemptDamageControl(
        ShipDamageState ship,
        TacticalPowerLedger power) => EvaluateEligibility(ship, power).CanAttempt;

    public static DamageControlAttemptResult AttemptComponentRepair(
        ShipDamageState ship,
        string componentId,
        TacticalPowerLedger power,
        int roll)
    {
        ArgumentNullException.ThrowIfNull(ship);
        ArgumentNullException.ThrowIfNull(power);
        if (string.IsNullOrWhiteSpace(componentId))
        {
            throw new ArgumentException("A component ID is required.", nameof(componentId));
        }
        ValidateRoll(roll);
        ship.RequireDamageControlAvailable();
        ShipComponentState component = ship.GetComponent(componentId);
        int chance = component.Condition switch
        {
            ComponentCondition.Degraded =>
                ship.DamageControl.Profile.DegradedRepairChancePercent,
            ComponentCondition.Disabled =>
                ship.DamageControl.Profile.DisabledRepairChancePercent,
            ComponentCondition.Operational => throw new InvalidOperationException(
                $"Component '{componentId}' does not require repair."),
            ComponentCondition.Destroyed => throw new InvalidOperationException(
                $"Destroyed component '{componentId}' cannot be repaired in combat."),
            _ => throw new ArgumentOutOfRangeException(nameof(component.Condition)),
        };

        ship.DamageControl.RequireAttemptAvailable();
        power.Spend(ship.DamageControl.Profile.TacticalPowerCost);
        ship.DamageControl.ConsumeAttempt();
        bool succeeded = roll <= chance;
        if (succeeded)
        {
            ship.QueueRepair(new PendingRepair(
                PendingRepairKind.Component,
                componentId));
        }

        return new DamageControlAttemptResult(
            PendingRepairKind.Component,
            componentId,
            chance,
            roll,
            succeeded,
            ship.DamageControl.Profile.TacticalPowerCost,
            ship.DamageControl.RepairKitsRemaining,
            succeeded);
    }

    public static DamageControlAttemptResult AttemptHullRepair(
        ShipDamageState ship,
        TacticalPowerLedger power,
        int roll)
    {
        ArgumentNullException.ThrowIfNull(ship);
        ArgumentNullException.ThrowIfNull(power);
        ValidateRoll(roll);
        ship.RequireDamageControlAvailable();
        if (ship.Defense.CurrentHull <= 0 ||
            ship.Defense.CurrentHull >= ship.Defense.PristineHull)
        {
            throw new InvalidOperationException(
                "Hull Damage Control requires a surviving ship with missing Hull.");
        }

        int chance = ship.DamageControl.Profile.HullRepairChancePercent;
        ship.DamageControl.RequireAttemptAvailable();
        power.Spend(ship.DamageControl.Profile.TacticalPowerCost);
        ship.DamageControl.ConsumeAttempt();
        bool succeeded = roll <= chance;
        if (succeeded)
        {
            ship.QueueRepair(new PendingRepair(PendingRepairKind.Hull, null));
        }

        return new DamageControlAttemptResult(
            PendingRepairKind.Hull,
            null,
            chance,
            roll,
            succeeded,
            ship.DamageControl.Profile.TacticalPowerCost,
            ship.DamageControl.RepairKitsRemaining,
            succeeded);
    }

    private static void ValidateRoll(int roll)
    {
        if (roll is < 1 or > 100)
        {
            throw new ArgumentOutOfRangeException(nameof(roll));
        }
    }
}
