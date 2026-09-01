using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1DefensiveCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-defensive-calibration-v1";

    [JsonPropertyName("id")]
    public string Id { get; set; } =
        "tl1-ds01-layered-defensive-systems-study";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 310100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1WeaponMatrixVariantDocument> Variants { get; set; } = new();
}
