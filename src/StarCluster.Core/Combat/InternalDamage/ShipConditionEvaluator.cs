using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.InternalDamage;

public static class ShipConditionEvaluator
{
    public static ShipCapabilitySnapshot Evaluate(ShipDamageState ship)
    {
        ArgumentNullException.ThrowIfNull(ship);
        if (ship.IsDestroyed)
        {
            return Snapshot(ShipCondition.Destroyed, false, false, false,
                false, false, false, false, false);
        }
        if (ship.IsPendingDestruction || ship.Defense.CurrentHull == 0)
        {
            return Snapshot(ShipCondition.PendingDestruction, false, false, false,
                false, false, false, false, false);
        }

        bool offense = HasOffensiveCapability(ship);
        bool stl = HasCapability(
            ship,
            ShipComponentCapability.StandardStlMovement,
            allowDisabled: false);
        bool activeDefense = ship.Defense.CurrentShieldCapacity > 0 ||
            HasCapability(ship, ShipComponentCapability.ActiveDefense, false);
        bool evm = HasCapability(
            ship,
            ShipComponentCapability.EvasiveManeuvers,
            allowDisabled: false);
        bool communications = HasCapability(
            ship,
            ShipComponentCapability.Communications,
            allowDisabled: false);
        bool ftl = HasFtlDeparture(ship);
        bool power = HasUsablePower(ship);
        bool damageControl = ship.DamageControl.HasAttemptCapacity &&
            ship.DamageControl.HasRepairKits &&
            power &&
            DamageControlService.HasAnyRepairableDamage(ship);

        bool fullyOperational =
            ship.Defense.CurrentHull == ship.Defense.PristineHull &&
            ship.Components.All(component =>
                component.Condition == ComponentCondition.Operational);
        ShipCondition condition = fullyOperational
            ? ShipCondition.FullyOperational
            : !offense && !stl
                ? ShipCondition.Disabled
                : ShipCondition.Degraded;
        return Snapshot(
            condition,
            offense,
            stl,
            ftl,
            activeDefense,
            evm,
            communications,
            power,
            damageControl);
    }

    private static bool HasOffensiveCapability(ShipDamageState ship)
    {
        bool usablePower = HasUsablePower(ship);
        foreach (ShipComponentState component in ship.Components.Where(item =>
            item.Definition.Capabilities.HasFlag(ShipComponentCapability.Offense) &&
            (item.Condition is ComponentCondition.Operational or ComponentCondition.Degraded)))
        {
            bool usable = component.Definition.Kind switch
            {
                ShipComponentKind.KineticWeapon => usablePower &&
                    HasUsableAmmunition(ship, ShipComponentKind.KineticMagazine),
                ShipComponentKind.EnergyWeapon => usablePower,
                ShipComponentKind.MissileLauncher =>
                    HasUsableAmmunition(ship, ShipComponentKind.MissileMagazine),
                _ => true,
            };
            if (usable)
            {
                return true;
            }
        }
        return false;
    }

    private static bool HasUsableAmmunition(
        ShipDamageState ship,
        ShipComponentKind magazineKind) => ship.Components.Any(component =>
            component.Definition.Kind == magazineKind &&
            (component.LoadedReadyPackages > 0 ||
             ((component.Condition is ComponentCondition.Operational or ComponentCondition.Degraded) &&
              component.CurrentContents > 0)));

    private static bool HasCapability(
        ShipDamageState ship,
        ShipComponentCapability capability,
        bool allowDisabled) => ship.Components.Any(component =>
            component.Definition.Capabilities.HasFlag(capability) &&
            (component.Condition is ComponentCondition.Operational or
                ComponentCondition.Degraded ||
             allowDisabled && component.Condition == ComponentCondition.Disabled));

    private static bool HasFtlDeparture(ShipDamageState ship)
    {
        ShipComponentState? ftl = ship.Components.FirstOrDefault(component =>
            component.Definition.Kind == ShipComponentKind.FtlDrive);
        return ftl?.Condition switch
        {
            ComponentCondition.Operational or ComponentCondition.Degraded => true,
            ComponentCondition.Disabled => ship.IsPlayerShip,
            _ => false,
        };
    }

    private static bool HasUsablePower(ShipDamageState ship) =>
        ship.Components.Any(component => component.Definition.Kind switch
        {
            ShipComponentKind.MainReactor =>
                component.Condition != ComponentCondition.Destroyed,
            ShipComponentKind.AuxiliaryReactor =>
                component.Condition is ComponentCondition.Operational or
                    ComponentCondition.Degraded,
            ShipComponentKind.PowerCapacitor or ShipComponentKind.CombatBattery =>
                (component.Condition is ComponentCondition.Operational or
                    ComponentCondition.Degraded) && component.CurrentContents > 0,
            _ => false,
        });

    private static ShipCapabilitySnapshot Snapshot(
        ShipCondition condition,
        bool offense,
        bool stl,
        bool ftl,
        bool activeDefense,
        bool evm,
        bool communications,
        bool power,
        bool damageControl)
    {
        var tags = new List<string>();
        if (!offense)
        {
            tags.Add("Disarmed");
        }
        if (!stl)
        {
            tags.Add("Immobile");
        }
        if (!ftl)
        {
            tags.Add("Stranded");
        }
        if (!activeDefense)
        {
            tags.Add("Defenseless");
        }
        if (!power)
        {
            tags.Add("Powerless");
        }
        return new ShipCapabilitySnapshot(
            condition,
            offense,
            stl,
            ftl,
            activeDefense,
            evm,
            communications,
            power,
            damageControl,
            tags.AsReadOnly());
    }
}
