using System.Text.Json.Serialization;
using StarCluster.Core.Combat.InternalDamage;

namespace StarCluster.ScenarioRunner.TL1Calibration;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1CombatPacingDamageControlMode
{
    None,
    ComponentFirstReserveOne,
}

public sealed class Tl1CombatPacingStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-combat-pacing-v1";

    [JsonPropertyName("id")]
    public string Id { get; set; } =
        "tl1-cp01-critical-density-and-immobile-timing";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 370200UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1CombatPacingVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1CombatPacingVariantDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("density")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public InternalCriticalDensity Density { get; set; }

    [JsonPropertyName("protectedCompartmentation")]
    public bool ProtectedCompartmentation { get; set; }

    [JsonPropertyName("damageControl")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1CombatPacingDamageControlMode DamageControl { get; set; }
}
