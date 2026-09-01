using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1PdsCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-pds-calibration-v1";

    [JsonPropertyName("id")]
    public string Id { get; set; } = "tl1-pds01-interception-study";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 300100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1WeaponMatrixVariantDocument> Variants { get; set; } = new();
}
