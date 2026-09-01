namespace StarCluster.Core.Combat.InternalDamage;

public enum ShipComponentKind
{
    MainReactor,
    AuxiliaryReactor,
    StlDrive,
    FtlDrive,
    ShieldGenerator,
    ShieldHardener,
    KineticWeapon,
    EnergyWeapon,
    MissileLauncher,
    PointDefense,
    KineticMagazine,
    MissileMagazine,
    SpecialWeaponsMagazine,
    AuxiliaryMagazine,
    ActiveSensors,
    TargetingComputer,
    Communications,
    Ecm,
    Eccm,
    PowerCapacitor,
    CombatBattery,
    ShieldBattery,
    EvasiveManeuverSystem,
    GenericDamageableAuxiliary,
}

public enum CriticalExposureGroup
{
    None = 0,
    Electronics = 1,
}

[Flags]
public enum ShipComponentCapability
{
    None = 0,
    Offense = 1 << 0,
    StandardStlMovement = 1 << 1,
    FtlDeparture = 1 << 2,
    ActiveDefense = 1 << 3,
    EvasiveManeuvers = 1 << 4,
    Communications = 1 << 5,
    PowerSource = 1 << 6,
    MissileDatalink = 1 << 7,
}
