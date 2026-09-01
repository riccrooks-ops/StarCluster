using System.Text;
using System.Text.Json;

namespace StarCluster.ScenarioRunner;

public sealed class SweepExpectationResult
{
    public string Metric { get; init; } = string.Empty;
    public double Expected { get; init; }
    public double Observed { get; init; }
    public double AbsoluteError { get; init; }
    public double MaximumAbsoluteError { get; init; }
    public bool Passed { get; init; }
}

public sealed class SweepVariantResult
{
    public string Id { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public int Trials { get; init; }
    public ulong MasterSeed { get; init; }
    public string ScenarioSha256 { get; init; } = string.Empty;
    public string ResultsSha256 { get; init; } = string.Empty;
    public int ErrorCount { get; init; }
    public bool Passed { get; init; }
    public IReadOnlyList<SweepExpectationResult> Expectations { get; init; } =
        Array.Empty<SweepExpectationResult>();
}

public sealed class SweepResultsDocument
{
    public int SchemaVersion { get; init; } = 1;
    public string SweepId { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public string BaseScenarioSha256 { get; init; } = string.Empty;
    public string RunnerAssemblySha256 { get; init; } = string.Empty;
    public string CoreAssemblySha256 { get; init; } = string.Empty;
    public bool Passed { get; init; }
    public IReadOnlyList<SweepVariantResult> Variants { get; init; } =
        Array.Empty<SweepVariantResult>();
}

public sealed class MonteCarloSweepRunResult
{
    public required SweepResultsDocument Results { get; init; }
    public required string ResultsSha256 { get; init; }
    public required string OutputDirectory { get; init; }
    public bool Passed => Results.Passed;
}

public static class MonteCarloSweepRunner
{
    private sealed record PreparedVariant(
        SweepVariantDocument Definition,
        ScenarioDocument Scenario,
        int Trials,
        ulong MasterSeed);

    public static MonteCarloSweepRunResult Run(
        SweepDocument sweep,
        string sweepPath,
        int jobs,
        bool resume,
        int checkpointEvery,
        int traceSamples,
        string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(sweep);
        if (string.IsNullOrWhiteSpace(sweepPath))
        {
            throw new ArgumentException("A sweep path is required.", nameof(sweepPath));
        }
        if (jobs <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(jobs));
        }
        if (checkpointEvery <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(checkpointEvery));
        }
        if (traceSamples < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(traceSamples));
        }
        ValidateSweepDocument(sweep);

        string baseScenarioPath = Path.GetFullPath(
            Path.Combine(
                Path.GetDirectoryName(Path.GetFullPath(sweepPath))!,
                sweep.BaseScenario));
        ScenarioDocument baseScenario =
            ScenarioDocumentSerialization.ReadScenario(baseScenarioPath);
        string baseScenarioSha256 = ScenarioDocumentSerialization.Sha256Hex(
            ScenarioDocumentSerialization.SerializeCanonical(baseScenario));
        PreparedVariant[] prepared = sweep.Variants
            .Select(variant => PrepareVariant(sweep, baseScenario, variant))
            .ToArray();

        string fullOutputDirectory = Path.GetFullPath(outputDirectory);
        if (!resume && Directory.Exists(fullOutputDirectory))
        {
            Directory.Delete(fullOutputDirectory, recursive: true);
        }
        Directory.CreateDirectory(fullOutputDirectory);

        Console.WriteLine(
            $"Sweep preflight: {prepared.Length} variants passed, 0 failed.");
        var variantResults = new List<SweepVariantResult>();
        foreach (PreparedVariant item in prepared)
        {
            string variantDirectory = Path.Combine(
                fullOutputDirectory,
                item.Definition.Id);
            var options = new MonteCarloBatchOptions
            {
                Trials = item.Trials,
                MasterSeed = item.MasterSeed,
                Jobs = jobs,
                Resume = resume,
                CheckpointEvery = checkpointEvery,
                TraceSamples = traceSamples,
            };
            MonteCarloBatchRunResult batch = MonteCarloBatchRunner.Run(
                item.Scenario,
                item.Definition.Id,
                options,
                variantDirectory);
            SweepExpectationResult[] expectations = EvaluateExpectations(
                item.Definition,
                batch.Results);
            bool passed = batch.Passed && expectations.All(result => result.Passed);
            variantResults.Add(new SweepVariantResult
            {
                Id = item.Definition.Id,
                Name = item.Definition.Name,
                Trials = item.Trials,
                MasterSeed = item.MasterSeed,
                ScenarioSha256 = batch.Results.ScenarioSha256,
                ResultsSha256 = batch.ResultsSha256,
                ErrorCount = batch.Results.ErrorCount,
                Passed = passed,
                Expectations = Array.AsReadOnly(expectations),
            });

            Console.WriteLine(
                $"{(passed ? "PASS" : "FAIL")} {item.Definition.Id} " +
                $"({item.Trials} trials; resumed {batch.ResumedTrials}; " +
                $"executed {batch.ExecutedTrials}; hash {batch.ResultsSha256})");
            foreach (SweepExpectationResult expectation in
                     expectations.Where(result => !result.Passed))
            {
                Console.WriteLine(
                    $"     {expectation.Metric}: expected " +
                    $"{expectation.Expected:R}, observed " +
                    $"{expectation.Observed:R}, absolute error " +
                    $"{expectation.AbsoluteError:R} exceeds " +
                    $"{expectation.MaximumAbsoluteError:R}");
            }
        }

        var results = new SweepResultsDocument
        {
            SweepId = sweep.Id,
            Name = sweep.Name,
            BaseScenarioSha256 = baseScenarioSha256,
            RunnerAssemblySha256 = RunnerHashUtility.RunnerAssemblySha256,
            CoreAssemblySha256 = RunnerHashUtility.CoreAssemblySha256,
            Passed = variantResults.All(result => result.Passed),
            Variants = Array.AsReadOnly(
                variantResults
                    .OrderBy(result => result.Id, StringComparer.Ordinal)
                    .ToArray()),
        };
        string resultsPath = Path.Combine(
            fullOutputDirectory,
            "sweep-summary.json");
        WriteJsonAtomic(resultsPath, results);
        string resultsSha256 = RunnerHashUtility.ComputeFileSha256(resultsPath);
        File.WriteAllText(
            Path.Combine(fullOutputDirectory, "sweep-result.sha256"),
            resultsSha256 + Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));

        Console.WriteLine(
            $"Sweep: {variantResults.Count(result => result.Passed)} passed, " +
            $"{variantResults.Count(result => !result.Passed)} failed, " +
            $"{variantResults.Count} total. Hash: {resultsSha256}. " +
            $"Output: {fullOutputDirectory}");
        return new MonteCarloSweepRunResult
        {
            Results = results,
            ResultsSha256 = resultsSha256,
            OutputDirectory = fullOutputDirectory,
        };
    }

    private static PreparedVariant PrepareVariant(
        SweepDocument sweep,
        ScenarioDocument baseScenario,
        SweepVariantDocument variant)
    {
        if (string.IsNullOrWhiteSpace(variant.Id))
        {
            throw new InvalidOperationException("Every sweep variant requires an ID.");
        }
        if (variant.Id.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            throw new InvalidOperationException(
                $"Sweep variant ID '{variant.Id}' is not safe for output paths.");
        }
        int trials = variant.Trials ?? sweep.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new InvalidOperationException(
                $"Sweep variant '{variant.Id}' requires a positive trial count.");
        }
        if (variant.MaximumAbsoluteError < 0.0 ||
            variant.MaximumAbsoluteError > 1.0)
        {
            throw new InvalidOperationException(
                $"Sweep variant '{variant.Id}' maximumAbsoluteError must be " +
                "from 0 through 1.");
        }
        foreach (var expected in variant.ExpectedProbabilities)
        {
            if (expected.Value < 0.0 || expected.Value > 1.0)
            {
                throw new InvalidOperationException(
                    $"Sweep variant '{variant.Id}' expected probability " +
                    $"'{expected.Key}' must be from 0 through 1.");
            }
        }

        ScenarioDocument scenario = ScenarioOverrideApplier.Apply(
            baseScenario,
            variant.Overrides);
        IReadOnlyList<string> failures = ScenarioPreflightValidator.Validate(scenario);
        if (failures.Count > 0)
        {
            throw new InvalidOperationException(
                $"Sweep variant '{variant.Id}' scenario preflight failed: " +
                string.Join("; ", failures));
        }

        return new PreparedVariant(
            variant,
            scenario,
            trials,
            variant.MasterSeed ?? sweep.MasterSeed);
    }

    private static SweepExpectationResult[] EvaluateExpectations(
        SweepVariantDocument variant,
        MonteCarloResultsDocument results)
    {
        IReadOnlyDictionary<string, double> observed = results.Metrics
            .ToDictionary(
                metric => metric.Key,
                metric => metric.Proportion,
                StringComparer.Ordinal);
        return variant.ExpectedProbabilities
            .OrderBy(item => item.Key, StringComparer.Ordinal)
            .Select(item =>
            {
                double actual = observed.TryGetValue(item.Key, out double value)
                    ? value
                    : 0.0;
                double absoluteError = Math.Abs(actual - item.Value);
                return new SweepExpectationResult
                {
                    Metric = item.Key,
                    Expected = item.Value,
                    Observed = actual,
                    AbsoluteError = absoluteError,
                    MaximumAbsoluteError = variant.MaximumAbsoluteError,
                    Passed = absoluteError <= variant.MaximumAbsoluteError,
                };
            })
            .ToArray();
    }

    private static void ValidateSweepDocument(SweepDocument sweep)
    {
        if (sweep.SchemaVersion != 1)
        {
            throw new InvalidOperationException(
                $"Unsupported sweep schema version {sweep.SchemaVersion}; expected 1.");
        }
        if (string.IsNullOrWhiteSpace(sweep.Id))
        {
            throw new InvalidOperationException("A sweep ID is required.");
        }
        if (string.IsNullOrWhiteSpace(sweep.BaseScenario))
        {
            throw new InvalidOperationException("A baseScenario path is required.");
        }
        if (sweep.TrialsPerVariant <= 0)
        {
            throw new InvalidOperationException(
                "trialsPerVariant must be positive.");
        }
        if (sweep.Variants.Count == 0)
        {
            throw new InvalidOperationException(
                "A sweep requires at least one variant.");
        }
        string[] duplicateIds = sweep.Variants
            .GroupBy(variant => variant.Id, StringComparer.Ordinal)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToArray();
        if (duplicateIds.Length > 0)
        {
            throw new InvalidOperationException(
                "Sweep variant IDs must be unique: " +
                string.Join(", ", duplicateIds));
        }
    }

    private static void WriteJsonAtomic<T>(string path, T value)
    {
        string temporaryPath = path + ".tmp";
        File.WriteAllText(
            temporaryPath,
            JsonSerializer.Serialize(
                value,
                ScenarioDocumentSerialization.IndentedWriteOptions) +
                Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        File.Move(temporaryPath, path, overwrite: true);
    }
}
