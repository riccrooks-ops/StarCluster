using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Tactics;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public sealed class Tl1AiDoctrineRegistryDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } = "star-cluster-ai-doctrine-registry-v1";

    [JsonPropertyName("registryVersion")]
    public string RegistryVersion { get; set; } = string.Empty;

    [JsonPropertyName("dependencies")]
    public List<Tl1AiDoctrineDependencyDocument> Dependencies { get; set; } = new();

    [JsonPropertyName("doctrines")]
    public List<Tl1AiDoctrineDefinitionDocument> Doctrines { get; set; } = new();

    [JsonPropertyName("evidence")]
    public List<Tl1AiDoctrineEvidenceDocument> Evidence { get; set; } = new();
}

public sealed class Tl1AiDoctrineDependencyDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
}

public sealed class Tl1AiDoctrineDefinitionDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("version")]
    public int Version { get; set; }

    [JsonPropertyName("domain")]
    public string Domain { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("ecmHeuristic")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public EcmActivationHeuristic EcmHeuristic { get; set; }

    [JsonPropertyName("eccmHeuristic")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public EccmActivationHeuristic EccmHeuristic { get; set; }

    [JsonPropertyName("acceptedCheckpoint")]
    public string? AcceptedCheckpoint { get; set; }

    [JsonPropertyName("evidenceIds")]
    public List<string> EvidenceIds { get; set; } = new();

    [JsonPropertyName("dependencies")]
    public List<string> Dependencies { get; set; } = new();

    [JsonPropertyName("rationale")]
    public string Rationale { get; set; } = string.Empty;

    [JsonPropertyName("informationPolicy")]
    public Tl1AiDoctrineInformationPolicyDocument InformationPolicy { get; set; } = new();
}

public sealed class Tl1AiDoctrineInformationPolicyDocument
{
    [JsonPropertyName("usesOwnCapabilities")]
    public bool UsesOwnCapabilities { get; set; }

    [JsonPropertyName("usesObservedTrackState")]
    public bool UsesObservedTrackState { get; set; }

    [JsonPropertyName("usesObservedEnemyEmissions")]
    public bool UsesObservedEnemyEmissions { get; set; }

    [JsonPropertyName("usesHiddenEnemyRatings")]
    public bool UsesHiddenEnemyRatings { get; set; }
}

public sealed class Tl1AiDoctrineEvidenceDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("checkpoint")]
    public string Checkpoint { get; set; } = string.Empty;

    [JsonPropertyName("studyId")]
    public string StudyId { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("resultSha256")]
    public string ResultSha256 { get; set; } = string.Empty;

    [JsonPropertyName("conclusion")]
    public string Conclusion { get; set; } = string.Empty;

    [JsonPropertyName("keyMetrics")]
    public Dictionary<string, JsonElement> KeyMetrics { get; set; } = new();

    [JsonPropertyName("dependencyIds")]
    public List<string> DependencyIds { get; set; } = new();

    [JsonPropertyName("revalidateIfChanged")]
    public List<string> RevalidateIfChanged { get; set; } = new();
}

public sealed record LoadedTl1AiDoctrineRegistry(
    string Path,
    string Sha256,
    Tl1AiDoctrineRegistryDocument Document,
    IReadOnlyDictionary<string, Tl1AiDoctrineDefinitionDocument> ById);
