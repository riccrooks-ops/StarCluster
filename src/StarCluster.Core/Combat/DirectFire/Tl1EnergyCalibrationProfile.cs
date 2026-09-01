namespace StarCluster.Core.Combat.DirectFire;

public sealed record Tl1EnergySideProfile(
    string Family,
    string Doctrine,
    int Accuracy,
    int ComputerBonus,
    bool Evasive,
    int ReactorOutput,
    int TacticalShieldRecharge,
    int Ammunition);

public sealed record Tl1EnergyCalibrationProfile(
    int ShieldCapacity,
    int ShieldArmor,
    int BaseShieldRecharge,
    int ArmorProtection,
    int ArmorIntegrity,
    int Hull,
    int RangeHexes,
    int RangePenaltyPerHex,
    int TurnCap,
    Tl1EnergySideProfile SideA,
    Tl1EnergySideProfile SideB)
{
    public static Tl1EnergyCalibrationProfile EnergyMirror(string doctrine = "standard", int rangeHexes = 2) => new(
        2, 0, 1, 0, 4, 12, rangeHexes, 5, 60,
        new Tl1EnergySideProfile("energy", doctrine, 25, 10, false, 5, 0, 0),
        new Tl1EnergySideProfile("energy", doctrine, 25, 10, false, 5, 0, 0));
}
