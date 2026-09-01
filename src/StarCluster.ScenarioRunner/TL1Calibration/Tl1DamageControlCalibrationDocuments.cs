using System.Text.Json.Serialization;
using StarCluster.Core.Combat.InternalDamage;

namespace StarCluster.ScenarioRunner.TL1Calibration;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1DamageControlDoctrine
{
    None,
    ComponentOnly,
    HullHalf,
    HullHalfReserveOne,
}

public sealed class Tl1DamageControlCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-damage-control-calibration-v1";

    [JsonPropertyName("id")]
    public string Id { get; set; } =
        "tl1-dc01-damage-control-doctrine-study";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 370100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1DamageControlVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1DamageControlVariantDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("density")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public InternalCriticalDensity Density { get; set; }

    [JsonPropertyName("protectedCompartmentation")]
    public bool ProtectedCompartmentation { get; set; }

    [JsonPropertyName("doctrine")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1DamageControlDoctrine Doctrine { get; set; }

    [JsonPropertyName("loadout")]
    public string Loadout { get; set; } = "kinetic";

    [JsonPropertyName("damageTempo")]
    public string DamageTempo { get; set; } = "steady";
}
