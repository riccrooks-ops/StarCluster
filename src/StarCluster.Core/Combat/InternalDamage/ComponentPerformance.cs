using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.Core.Combat.InternalDamage;

public sealed record ConditionedWeaponPerformance(
    bool CanFire,
    int Damage,
    int TacticalPowerCost,
    bool RequiresFullRecycleTurnAfterFire,
    bool EnhancedModesAvailable);

public static class ComponentPerformance
{
    public static ConditionedWeaponPerformance Weapon(
        WeaponFamily family,
        ComponentCondition condition,
        int normalDamage,
        int normalPowerCost,
        int damagePointScale = DamagePointScale.Current)
    {
        ValidateNonNegative(normalDamage, nameof(normalDamage));
        ValidateNonNegative(normalPowerCost, nameof(normalPowerCost));
        if (condition is ComponentCondition.Disabled or ComponentCondition.Destroyed)
        {
            return new ConditionedWeaponPerformance(
                false, 0, 0, false, false);
        }
        if (condition == ComponentCondition.Operational)
        {
            return new ConditionedWeaponPerformance(
                true, normalDamage, normalPowerCost, false, true);
        }

        return family switch
        {
            WeaponFamily.Kinetic or WeaponFamily.Missile =>
                new ConditionedWeaponPerformance(
                    true,
                    normalDamage,
                    normalPowerCost,
                    true,
                    false),
            WeaponFamily.Energy => new ConditionedWeaponPerformance(
                true,
                DamagePointScale.HalfDamageRoundedUp(normalDamage, damagePointScale),
                HalfRoundedUp(normalPowerCost),
                false,
                false),
            _ => new ConditionedWeaponPerformance(
                true,
                normalDamage,
                normalPowerCost,
                false,
                false),
        };
    }

    public static int PdsBaseAccuracy(int normalAccuracy, ComponentCondition condition)
    {
        ValidateNonNegative(normalAccuracy, nameof(normalAccuracy));
        return condition switch
        {
            ComponentCondition.Operational => normalAccuracy,
            ComponentCondition.Degraded => HalfRoundedUp(normalAccuracy),
            ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
            _ => throw new ArgumentOutOfRangeException(nameof(condition)),
        };
    }

    public static int ActiveSensorContribution(int normalContribution, ComponentCondition condition) =>
        HalfDownWhenDegraded(normalContribution, condition);

    public static int TargetingComputerBonus(int normalBonus, ComponentCondition condition) =>
        HalfDownWhenDegraded(normalBonus, condition);

    public static int StlMovement(int normalMovement, ComponentCondition condition)
    {
        ValidateNonNegative(normalMovement, nameof(normalMovement));
        return condition switch
        {
            ComponentCondition.Operational => normalMovement,
            ComponentCondition.Degraded => HalfRoundedUp(normalMovement),
            ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
            _ => throw new ArgumentOutOfRangeException(nameof(condition)),
        };
    }

    public const int ImmobileTargetAccuracyBonus = 10;

    public static int TargetMobilityAccuracyBonus(ComponentCondition stlCondition) =>
        stlCondition switch
        {
            ComponentCondition.Operational or ComponentCondition.Degraded => 0,
            ComponentCondition.Disabled or ComponentCondition.Destroyed =>
                ImmobileTargetAccuracyBonus,
            _ => throw new ArgumentOutOfRangeException(nameof(stlCondition)),
        };

    public static int FtlRange(
        int normalRange,
        ComponentCondition condition,
        bool isPlayerShip)
    {
        ValidateNonNegative(normalRange, nameof(normalRange));
        return condition switch
        {
            ComponentCondition.Operational => normalRange,
            ComponentCondition.Degraded => HalfRoundedUp(normalRange),
            ComponentCondition.Disabled => isPlayerShip ? 1 : 0,
            ComponentCondition.Destroyed => 0,
            _ => throw new ArgumentOutOfRangeException(nameof(condition)),
        };
    }

    public static int EvasiveDefenseBonus(int normalBonus, ComponentCondition condition)
    {
        ValidateNonNegative(normalBonus, nameof(normalBonus));
        return condition switch
        {
            ComponentCondition.Operational => normalBonus,
            ComponentCondition.Degraded => normalBonus / 2,
            ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
            _ => throw new ArgumentOutOfRangeException(nameof(condition)),
        };
    }

    public static int EvasiveAttackPenaltyMagnitude(
        int normalPenaltyMagnitude,
        ComponentCondition condition)
    {
        ValidateNonNegative(normalPenaltyMagnitude, nameof(normalPenaltyMagnitude));
        return condition switch
        {
            ComponentCondition.Operational => normalPenaltyMagnitude,
            ComponentCondition.Degraded => HalfRoundedUp(normalPenaltyMagnitude),
            ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
            _ => throw new ArgumentOutOfRangeException(nameof(condition)),
        };
    }

    public static int AdditionalCommittedPower(
        ShipComponentKind kind,
        ComponentCondition condition)
    {
        if (!Enum.IsDefined(kind))
        {
            throw new ArgumentOutOfRangeException(nameof(kind));
        }
        if (!Enum.IsDefined(condition))
        {
            throw new ArgumentOutOfRangeException(nameof(condition));
        }
        bool usesDegradedFullEffectSurcharge = kind is
            ShipComponentKind.ShieldHardener or
            ShipComponentKind.Ecm or
            ShipComponentKind.Eccm;
        return condition == ComponentCondition.Degraded &&
            usesDegradedFullEffectSurcharge
                ? 1
                : 0;
    }

    public static int ShieldRechargePowerCost(
        int normalCost,
        ComponentCondition generatorCondition)
    {
        ValidateNonNegative(normalCost, nameof(normalCost));
        return generatorCondition switch
        {
            ComponentCondition.Operational => normalCost,
            ComponentCondition.Degraded => checked(normalCost * 2),
            ComponentCondition.Disabled or ComponentCondition.Destroyed =>
                throw new InvalidOperationException(
                    "A Disabled or Destroyed Shield Generator cannot recharge shields."),
            _ => throw new ArgumentOutOfRangeException(nameof(generatorCondition)),
        };
    }

    public static bool CommunicationsAvailable(ComponentCondition condition) =>
        condition is ComponentCondition.Operational or ComponentCondition.Degraded;

    public static bool EnhancedModesAvailable(ComponentCondition condition) =>
        condition == ComponentCondition.Operational;

    private static int HalfDownWhenDegraded(
        int normalValue,
        ComponentCondition condition)
    {
        ValidateNonNegative(normalValue, nameof(normalValue));
        return condition switch
        {
            ComponentCondition.Operational => normalValue,
            ComponentCondition.Degraded => normalValue / 2,
            ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
            _ => throw new ArgumentOutOfRangeException(nameof(condition)),
        };
    }

    private static int HalfRoundedUp(int value) => (value + 1) / 2;

    private static void ValidateNonNegative(int value, string name)
    {
        if (value < 0)
        {
            throw new ArgumentOutOfRangeException(name);
        }
    }
}

public sealed class DegradedWeaponRecycleState
{
    private bool _mustRecycleNextTurn;

    public bool IsRecyclingThisTurn { get; private set; }

    public void BeginTurn()
    {
        IsRecyclingThisTurn = _mustRecycleNextTurn;
        _mustRecycleNextTurn = false;
    }

    public bool CanFire(ComponentCondition condition) =>
        (condition is ComponentCondition.Operational or ComponentCondition.Degraded) &&
        !IsRecyclingThisTurn;

    public void RecordFire(ComponentCondition condition)
    {
        if (!CanFire(condition))
        {
            throw new InvalidOperationException(
                "The weapon cannot fire in its current condition or recycle state.");
        }
        if (condition == ComponentCondition.Degraded)
        {
            _mustRecycleNextTurn = true;
        }
    }
}
