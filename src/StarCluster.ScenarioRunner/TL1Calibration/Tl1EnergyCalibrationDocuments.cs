using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1EnergyCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")] public string SchemaVersion { get; set; } = "star-cluster-tl1-energy-calibration-v1";
    [JsonPropertyName("id")] public string Id { get; set; } = "tl1-ec01-energy-interaction-study";
    [JsonPropertyName("baselineSha256")] public string BaselineSha256 { get; set; } = string.Empty;
    [JsonPropertyName("masterSeed")] public ulong MasterSeed { get; set; } = 280100UL;
    [JsonPropertyName("trialsPerVariant")] public int TrialsPerVariant { get; set; } = 10000;
    [JsonPropertyName("variants")] public List<Tl1EnergyCalibrationVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1EnergyCalibrationVariantDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("label")] public string Label { get; set; } = string.Empty;
    [JsonPropertyName("pairId")] public string? PairId { get; set; }
    [JsonPropertyName("shieldCapacity")] public int ShieldCapacity { get; set; } = 2;
    [JsonPropertyName("shieldArmor")] public int ShieldArmor { get; set; }
    [JsonPropertyName("baseShieldRecharge")] public int BaseShieldRecharge { get; set; } = 1;
    [JsonPropertyName("armorProtection")] public int ArmorProtection { get; set; }
    [JsonPropertyName("armorIntegrity")] public int ArmorIntegrity { get; set; } = 4;
    [JsonPropertyName("hull")] public int Hull { get; set; } = 12;
    [JsonPropertyName("rangeHexes")] public int RangeHexes { get; set; } = 2;
    [JsonPropertyName("rangePenaltyPerHex")] public int RangePenaltyPerHex { get; set; } = 5;
    [JsonPropertyName("turnCap")] public int TurnCap { get; set; } = 80;
    [JsonPropertyName("sideA")] public Tl1EnergySideDocument SideA { get; set; } = new();
    [JsonPropertyName("sideB")] public Tl1EnergySideDocument SideB { get; set; } = new();
}

public sealed class Tl1EnergySideDocument
{
    [JsonPropertyName("family")] public string Family { get; set; } = "energy";
    [JsonPropertyName("doctrine")] public string Doctrine { get; set; } = "standard";
    [JsonPropertyName("accuracy")] public int Accuracy { get; set; } = 25;
    [JsonPropertyName("computerBonus")] public int ComputerBonus { get; set; } = 10;
    [JsonPropertyName("evasive")] public bool Evasive { get; set; }
    [JsonPropertyName("reactorOutput")] public int ReactorOutput { get; set; } = 5;
    [JsonPropertyName("tacticalShieldRecharge")] public int TacticalShieldRecharge { get; set; }
    [JsonPropertyName("ammunition")] public int Ammunition { get; set; } = 100;
}
