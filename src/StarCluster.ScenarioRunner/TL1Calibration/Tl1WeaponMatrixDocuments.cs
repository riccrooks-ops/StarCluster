using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1WeaponMatrixStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-weapon-matrix-v1";

    [JsonPropertyName("id")]
    public string Id { get; set; } = "tl1-wm01-complete-weapon-matrix";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 290100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1WeaponMatrixVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1WeaponMatrixVariantDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("label")]
    public string Label { get; set; } = string.Empty;

    [JsonPropertyName("category")]
    public string Category { get; set; } = string.Empty;

    [JsonPropertyName("pairId")]
    public string? PairId { get; set; }

    [JsonPropertyName("shieldCapacity")]
    public int ShieldCapacity { get; set; } = 2;

    [JsonPropertyName("shieldArmor")]
    public int ShieldArmor { get; set; }

    [JsonPropertyName("baseShieldRecharge")]
    public int BaseShieldRecharge { get; set; } = 1;

    [JsonPropertyName("armorProtection")]
    public int ArmorProtection { get; set; }

    [JsonPropertyName("armorIntegrity")]
    public int ArmorIntegrity { get; set; } = 4;

    [JsonPropertyName("hull")]
    public int Hull { get; set; } = 12;

    [JsonPropertyName("rangeHexes")]
    public int RangeHexes { get; set; } = 2;

    [JsonPropertyName("rangePenaltyPerHex")]
    public int RangePenaltyPerHex { get; set; } = 5;

    [JsonPropertyName("turnCap")]
    public int TurnCap { get; set; } = 100;

    [JsonPropertyName("sideA")]
    public Tl1WeaponMatrixSideDocument SideA { get; set; } = new();

    [JsonPropertyName("sideB")]
    public Tl1WeaponMatrixSideDocument SideB { get; set; } = new();
}

public sealed class Tl1WeaponMatrixSideDocument
{
    [JsonPropertyName("family")]
    public string Family { get; set; } = "kinetic";

    [JsonPropertyName("doctrine")]
    public string Doctrine { get; set; } = "standard";

    [JsonPropertyName("accuracy")]
    public int Accuracy { get; set; } = 20;

    [JsonPropertyName("computerBonus")]
    public int ComputerBonus { get; set; } = 10;

    [JsonPropertyName("evasive")]
    public bool Evasive { get; set; }

    [JsonPropertyName("reactorOutput")]
    public int ReactorOutput { get; set; } = 5;

    [JsonPropertyName("ammunition")]
    public int Ammunition { get; set; } = 100;

    [JsonPropertyName("missileGuidance")]
    public int MissileGuidance { get; set; } = 55;

    [JsonPropertyName("missileDamage")]
    public int MissileDamage { get; set; } = 5;

    [JsonPropertyName("missileShieldPenetration")]
    public int MissileShieldPenetration { get; set; } = 1;

    [JsonPropertyName("missileArmorPenetration")]
    public int MissileArmorPenetration { get; set; } = 2;

    [JsonPropertyName("missileSpeed")]
    public int MissileSpeed { get; set; } = 1;

    [JsonPropertyName("missileRange")]
    public int MissileRange { get; set; } = 6;

    [JsonPropertyName("targetMovePerTurn")]
    public int TargetMovePerTurn { get; set; }

    [JsonPropertyName("missileLaunchesPerTurn")]
    public int MissileLaunchesPerTurn { get; set; } = 1;

    [JsonPropertyName("pdsFamily")]
    public string PdsFamily { get; set; } = "none";

    [JsonPropertyName("pdsPowerCost")]
    public int PdsPowerCost { get; set; }

    [JsonPropertyName("pdsReactionCapacity")]
    public int PdsReactionCapacity { get; set; }

    [JsonPropertyName("pdsInterceptionChance")]
    public int PdsInterceptionChance { get; set; }

    [JsonPropertyName("pdsAmmunition")]
    public int PdsAmmunition { get; set; }

    [JsonPropertyName("pdsUnlimitedAmmunition")]
    public bool PdsUnlimitedAmmunition { get; set; }

    [JsonPropertyName("sensorTrackGateEnabled")]
    public bool SensorTrackGateEnabled { get; set; }

    [JsonPropertyName("passiveFirmRange")]
    public int PassiveFirmRange { get; set; } = 3;

    [JsonPropertyName("activeFirmRangeAtOnePower")]
    public int ActiveFirmRangeAtOnePower { get; set; } = 5;

    [JsonPropertyName("activeFirmRangeAtTwoPower")]
    public int ActiveFirmRangeAtTwoPower { get; set; } = 6;

    [JsonPropertyName("sensorPower")]
    public int SensorPower { get; set; }

    [JsonPropertyName("ecmPower")]
    public int EcmPower { get; set; }

    [JsonPropertyName("eccmPower")]
    public int EccmPower { get; set; }

    [JsonPropertyName("shieldHardenerPower")]
    public int ShieldHardenerPower { get; set; }

    [JsonPropertyName("tacticalShieldRechargePower")]
    public int TacticalShieldRechargePower { get; set; }

    [JsonPropertyName("shieldBatteryCharges")]
    public int ShieldBatteryCharges { get; set; }

    [JsonPropertyName("shieldBatteryRestore")]
    public int ShieldBatteryRestore { get; set; }
}
