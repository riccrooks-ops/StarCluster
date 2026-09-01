using System.Text.Json.Serialization;
using StarCluster.Core.Combat.InternalDamage;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1InternalDamageCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-internal-damage-calibration-v1";

    [JsonPropertyName("id")]
    public string Id { get; set; } =
        "tl1-id01-internal-damage-and-damage-control-study";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 360100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1InternalDamageVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1InternalDamageVariantDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("density")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public InternalCriticalDensity Density { get; set; }

    [JsonPropertyName("protectedCompartmentation")]
    public bool ProtectedCompartmentation { get; set; }

    [JsonPropertyName("damageControl")]
    public bool DamageControl { get; set; }

    [JsonPropertyName("loadout")]
    public string Loadout { get; set; } = "kinetic";

    [JsonPropertyName("damageTempo")]
    public string DamageTempo { get; set; } = "steady";
}
