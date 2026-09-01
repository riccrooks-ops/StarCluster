using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1KineticCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")] public string SchemaVersion { get; set; } = "star-cluster-tl1-kinetic-calibration-v1";
    [JsonPropertyName("id")] public string Id { get; set; } = "tl1-kc01-kinetic-interaction-study";
    [JsonPropertyName("baselineSha256")] public string BaselineSha256 { get; set; } = string.Empty;
    [JsonPropertyName("masterSeed")] public ulong MasterSeed { get; set; } = 270100UL;
    [JsonPropertyName("trialsPerVariant")] public int TrialsPerVariant { get; set; } = 10000;
    [JsonPropertyName("variants")] public List<Tl1KineticCalibrationVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1KineticCalibrationVariantDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("label")] public string Label { get; set; } = string.Empty;
    [JsonPropertyName("pairId")] public string? PairId { get; set; }
    [JsonPropertyName("shieldCapacity")] public int ShieldCapacity { get; set; } = 2;
    [JsonPropertyName("shieldArmor")] public int ShieldArmor { get; set; }
    [JsonPropertyName("shieldRecharge")] public int ShieldRecharge { get; set; } = 1;
    [JsonPropertyName("armorProtection")] public int ArmorProtection { get; set; }
    [JsonPropertyName("armorIntegrity")] public int ArmorIntegrity { get; set; } = 4;
    [JsonPropertyName("hull")] public int Hull { get; set; } = 12;
    [JsonPropertyName("weaponDamage")] public int WeaponDamage { get; set; } = 4;
    [JsonPropertyName("shieldPenetration")] public int ShieldPenetration { get; set; } = 1;
    [JsonPropertyName("armorPenetration")] public int ArmorPenetration { get; set; }
    [JsonPropertyName("ammunition")] public int Ammunition { get; set; } = 100;
    [JsonPropertyName("rangeHexes")] public int RangeHexes { get; set; } = 2;
    [JsonPropertyName("sideAEvasive")] public bool SideAEvasive { get; set; }
    [JsonPropertyName("sideBEvasive")] public bool SideBEvasive { get; set; }
    [JsonPropertyName("sideAComputerBonus")] public int SideAComputerBonus { get; set; } = 10;
    [JsonPropertyName("sideBComputerBonus")] public int SideBComputerBonus { get; set; } = 10;
    [JsonPropertyName("turnCap")] public int TurnCap { get; set; } = 60;
}
