namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// Explicit deterministic-duel fixture. Production calibration values are
/// supplied by the ScenarioRunner baseline catalog; Core tests may use the
/// stable MechanicsFixture() profile without tracking balance changes.
/// </summary>
public sealed record Tl1DuelCalibrationProfile(
    int ShieldCapacity,
    int ShieldArmor,
    int ShieldRecharge,
    int ArmorProtection,
    int ArmorIntegrity,
    int Hull,
    int WeaponDamage,
    int ShieldPenetration,
    int ArmorPenetration,
    int WeaponPower,
    int Ammunition,
    int ReactorOutput,
    int BaseChance,
    int WeaponAccuracy,
    int RangePenaltyPerHex,
    int TargetEvasivePenalty,
    int ShooterEvasivePenalty,
    int MinimumChance,
    int MaximumChance,
    int RangeHexes,
    bool SideAEvasive,
    bool SideBEvasive,
    int SideAComputerBonus,
    int SideBComputerBonus,
    int TurnCap)
{
    public static Tl1DuelCalibrationProfile MechanicsFixture(
        int rangeHexes = 2) => new(
        ShieldCapacity: 2,
        ShieldArmor: 0,
        ShieldRecharge: 1,
        ArmorProtection: 0,
        ArmorIntegrity: 4,
        Hull: 12,
        WeaponDamage: 4,
        ShieldPenetration: 1,
        ArmorPenetration: 0,
        WeaponPower: 1,
        Ammunition: 100,
        ReactorOutput: 5,
        BaseChance: 50,
        WeaponAccuracy: 20,
        RangePenaltyPerHex: 5,
        TargetEvasivePenalty: 10,
        ShooterEvasivePenalty: 5,
        MinimumChance: 5,
        MaximumChance: 95,
        RangeHexes: rangeHexes,
        SideAEvasive: false,
        SideBEvasive: false,
        SideAComputerBonus: 10,
        SideBComputerBonus: 10,
        TurnCap: 60);
}
