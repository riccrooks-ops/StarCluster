using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1PowerEnvelopeCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-power-envelope-calibration-v2";

    [JsonPropertyName("id")]
    public string Id { get; set; } =
        "tl1-pe02-main-power-interception-correction-study";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 330100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1PowerEnvelopeVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1PowerEnvelopeVariantDocument
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

    [JsonPropertyName("rangeSchedule")]
    public List<Tl1RelativeRangeChangeDocument> RangeSchedule { get; set; } =
        new();

    [JsonPropertyName("sideA")]
    public Tl1PowerEnvelopeSideDocument SideA { get; set; } = new();

    [JsonPropertyName("sideB")]
    public Tl1PowerEnvelopeSideDocument SideB { get; set; } = new();
}

public sealed class Tl1PowerEnvelopeSideDocument
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

    [JsonPropertyName("auxiliaryReactorOutput")]
    public int AuxiliaryReactorOutput { get; set; }

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

    [JsonPropertyName("powerPriority")]
    public string PowerPriority { get; set; } = "defense-first";

    [JsonPropertyName("heldInterception")]
    public bool HeldInterception { get; set; }

    [JsonPropertyName("heldInterceptionMode")]
    public string HeldInterceptionMode { get; set; } = "standard";

    [JsonPropertyName("reactorSafeOverload")]
    public bool ReactorSafeOverload { get; set; }

    [JsonPropertyName("energySafeBurst")]
    public bool EnergySafeBurst { get; set; }

    [JsonPropertyName("sensorSafeOverload")]
    public bool SensorSafeOverload { get; set; }

    [JsonPropertyName("ecmSafeOverload")]
    public bool EcmSafeOverload { get; set; }

    [JsonPropertyName("eccmSafeOverload")]
    public bool EccmSafeOverload { get; set; }

    [JsonPropertyName("shieldHardenerSafeOverload")]
    public bool ShieldHardenerSafeOverload { get; set; }

    [JsonPropertyName("shieldOvercapacitySafeOverload")]
    public bool ShieldOvercapacitySafeOverload { get; set; }

    [JsonPropertyName("shieldRecoverySafeOverload")]
    public bool ShieldRecoverySafeOverload { get; set; }

    [JsonPropertyName("safeOverloadTurnLimit")]
    public int SafeOverloadTurnLimit { get; set; } = 2;

    [JsonPropertyName("combatBatteryCharges")]
    public int CombatBatteryCharges { get; set; }

    [JsonPropertyName("combatBatteryGain")]
    public int CombatBatteryGain { get; set; } = 2;

    [JsonPropertyName("combatBatteryDoctrine")]
    public string CombatBatteryDoctrine { get; set; } = "none";

    [JsonPropertyName("capacitorCapacity")]
    public int CapacitorCapacity { get; set; }

    [JsonPropertyName("capacitorStartingCharge")]
    public int CapacitorStartingCharge { get; set; }

    [JsonPropertyName("capacitorChargeRate")]
    public int CapacitorChargeRate { get; set; } = 1;

    [JsonPropertyName("capacitorDischargeRate")]
    public int CapacitorDischargeRate { get; set; } = 2;

    [JsonPropertyName("capacitorDoctrine")]
    public string CapacitorDoctrine { get; set; } = "none";
}

public sealed class Tl1RelativeRangeChangeDocument
{
    [JsonPropertyName("turn")]
    public int Turn { get; set; }

    [JsonPropertyName("rangeHexes")]
    public int RangeHexes { get; set; }
}
