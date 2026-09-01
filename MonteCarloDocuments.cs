using System.Text.Json;

namespace StarCluster.ScenarioRunner;

public sealed class SweepDocument
{
    public int SchemaVersion { get; set; } = 1;
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string BaseScenario { get; set; } = string.Empty;
    public int TrialsPerVariant { get; set; } = 10_000;
    public ulong MasterSeed { get; set; } = 190100UL;
    public List<SweepVariantDocument> Variants { get; set; } = new();
}

public sealed class SweepVariantDocument
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public int? Trials { get; set; }
    public ulong? MasterSeed { get; set; }
    public List<ScenarioOverrideDocument> Overrides { get; set; } = new();
    public Dictionary<string, double> ExpectedProbabilities { get; set; } =
        new(StringComparer.Ordinal);
    public double MaximumAbsoluteError { get; set; } = 0.03;
}

public sealed class ScenarioOverrideDocument
{
    public string Path { get; set; } = string.Empty;
    public JsonElement Value { get; set; }
}

public sealed class MonteCarloBatchOptions
{
    public int Trials { get; init; }
    public ulong MasterSeed { get; init; }
    public int Jobs { get; init; } = 1;
    public bool Resume { get; init; }
    public int CheckpointEvery { get; init; } = 256;
    public int TraceSamples { get; init; }
    public bool KeepTrialJournal { get; init; } = true;
    public string? RandomSeedNamespace { get; init; }
}
