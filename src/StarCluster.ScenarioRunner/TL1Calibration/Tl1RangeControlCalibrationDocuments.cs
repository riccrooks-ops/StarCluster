using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1RangeControlCalibrationStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-range-control-calibration-v1";

    [JsonPropertyName("id")]
    public string Id { get; set; } =
        "tl1-rc01-scripted-relative-range-study";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 350100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("variants")]
    public List<Tl1PowerEnvelopeVariantDocument> Variants { get; set; } = new();
}
