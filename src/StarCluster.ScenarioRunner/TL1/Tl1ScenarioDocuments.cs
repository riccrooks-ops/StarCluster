using System.Text.Json;

namespace StarCluster.ScenarioRunner.TL1;

public sealed class Tl1MechanicsScenarioDocument
{
    public string SchemaVersion { get; set; } = "star-cluster-tl1-phase-a-v1";

    public string Id { get; set; } = string.Empty;

    public string MatrixScenarioId { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string BaselineVersion { get; set; } = string.Empty;

    public string BaselineSha256 { get; set; } = string.Empty;

    public List<Tl1MechanicsCaseDocument> Cases { get; set; } = new();
}

public sealed class Tl1MechanicsCaseDocument
{
    public string Id { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string Operation { get; set; } = string.Empty;

    public JsonElement Input { get; set; }

    public JsonElement Expected { get; set; }
}

public sealed record Tl1CaseRunResult(
    string Id,
    string Name,
    string Operation,
    bool Passed,
    IReadOnlyList<string> Failures,
    JsonElement Actual,
    IReadOnlyList<string> Events);

public sealed record Tl1ScenarioRunResult(
    Tl1MechanicsScenarioDocument Document,
    IReadOnlyList<Tl1CaseRunResult> Cases)
{
    public bool Passed => Cases.All(item => item.Passed);

    public IReadOnlyList<string> Failures => Cases
        .SelectMany(item => item.Failures.Select(failure => $"{item.Id}: {failure}"))
        .ToArray();
}
