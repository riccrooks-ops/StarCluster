using System.Collections.Concurrent;
using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public sealed class MonteCarloBatchRunResult
{
    public required MonteCarloResultsDocument Results { get; init; }
    public required string ResultsSha256 { get; init; }
    public required string OutputDirectory { get; init; }
    public int ResumedTrials { get; init; }
    public int ExecutedTrials { get; init; }
    public IReadOnlyList<MonteCarloTrialResult> Trials { get; init; } =
        Array.Empty<MonteCarloTrialResult>();
    public bool Passed => Results.ErrorCount == 0;
}

public static class MonteCarloBatchRunner
{
    private sealed class RunManifest
    {
        public int SchemaVersion { get; set; } = 1;
        public string RunKey { get; set; } = string.Empty;
        public string ScenarioId { get; set; } = string.Empty;
        public string VariantId { get; set; } = string.Empty;
        public string RandomSeedNamespace { get; set; } = string.Empty;
        public ulong MasterSeed { get; set; }
        public int RequestedTrials { get; set; }
        public string ScenarioSha256 { get; set; } = string.Empty;
        public string RunnerAssemblySha256 { get; set; } = string.Empty;
        public string CoreAssemblySha256 { get; set; } = string.Empty;
    }

    public static MonteCarloBatchRunResult Run(
        ScenarioDocument document,
        string variantId,
        MonteCarloBatchOptions options,
        string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(options);
        Validate(document, variantId, options, outputDirectory);

        string scenarioJson = ScenarioDocumentSerialization.SerializeCanonical(document);
        string scenarioSha256 = ScenarioDocumentSerialization.Sha256Hex(scenarioJson);
        string runnerHash = RunnerHashUtility.RunnerAssemblySha256;
        string coreHash = RunnerHashUtility.CoreAssemblySha256;
        string randomSeedNamespace = string.IsNullOrWhiteSpace(options.RandomSeedNamespace)
            ? variantId
            : options.RandomSeedNamespace;
        string runKey = RunnerHashUtility.ComputeRunKey(
            scenarioSha256,
            variantId,
            randomSeedNamespace,
            options.MasterSeed,
            runnerHash,
            coreHash);

        string fullOutputDirectory = Path.GetFullPath(outputDirectory);
        PrepareOutputDirectory(fullOutputDirectory, options.Resume);
        string manifestPath = Path.Combine(fullOutputDirectory, "manifest.json");
        string trialsPath = Path.Combine(fullOutputDirectory, "trials.jsonl");
        RunManifest manifest = PrepareManifest(
            manifestPath,
            document,
            variantId,
            options,
            scenarioSha256,
            runnerHash,
            coreHash,
            runKey,
            randomSeedNamespace);

        var trialByIndex = LoadExistingTrials(
            trialsPath,
            manifest,
            options.Trials,
            options.Resume);
        int resumedTrials = trialByIndex.Count;
        var stopwatch = Stopwatch.StartNew();
        int executedTrials = ExecuteMissingTrials(
            document,
            variantId,
            options,
            trialsPath,
            trialByIndex,
            randomSeedNamespace);
        stopwatch.Stop();

        MonteCarloTrialResult[] orderedTrials = Enumerable.Range(0, options.Trials)
            .Select(index => GetRequiredTrial(trialByIndex, index))
            .ToArray();
        MonteCarloResultsDocument results = MonteCarloStatistics.Aggregate(
            orderedTrials,
            runKey,
            document.Id,
            variantId,
            options.MasterSeed,
            scenarioSha256,
            runnerHash,
            coreHash);

        string resultsPath = Path.Combine(fullOutputDirectory, "results.json");
        WriteJsonAtomic(resultsPath, results);
        WriteMetricsCsv(
            Path.Combine(fullOutputDirectory, "metrics.csv"),
            results.Metrics);
        string resultsSha256 = RunnerHashUtility.ComputeFileSha256(resultsPath);
        File.WriteAllText(
            Path.Combine(fullOutputDirectory, "result.sha256"),
            resultsSha256 + Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        var executionRecord = new
        {
            schemaVersion = 1,
            jobs = options.Jobs,
            resumeRequested = options.Resume,
            resumedTrials,
            executedTrials,
            requestedTrials = options.Trials,
            checkpointEvery = options.CheckpointEvery,
            keepTrialJournal = options.KeepTrialJournal,
            randomSeedNamespace,
            elapsedMilliseconds = stopwatch.ElapsedMilliseconds,
            completedUtc = DateTimeOffset.UtcNow,
        };
        WriteJsonAtomic(
            Path.Combine(fullOutputDirectory, "execution.json"),
            executionRecord);
        AppendJsonLine(
            Path.Combine(fullOutputDirectory, "execution-history.jsonl"),
            executionRecord);

        WriteErrorJournal(
            Path.Combine(fullOutputDirectory, "errors.jsonl"),
            orderedTrials);

        if (options.TraceSamples > 0)
        {
            WriteTraceSamples(
                document,
                variantId,
                options,
                orderedTrials,
                fullOutputDirectory,
                randomSeedNamespace);
        }

        if (!options.KeepTrialJournal)
        {
            File.Delete(trialsPath);
        }

        return new MonteCarloBatchRunResult
        {
            Results = results,
            ResultsSha256 = resultsSha256,
            OutputDirectory = fullOutputDirectory,
            ResumedTrials = resumedTrials,
            ExecutedTrials = executedTrials,
            Trials = Array.AsReadOnly(orderedTrials),
        };
    }


    private static MonteCarloTrialResult GetRequiredTrial(
        IReadOnlyDictionary<int, MonteCarloTrialResult> trialByIndex,
        int trialIndex)
    {
        if (!trialByIndex.TryGetValue(
                trialIndex,
                out MonteCarloTrialResult? trial) ||
            trial is null)
        {
            throw new InvalidOperationException(
                $"Trial {trialIndex} was not present after batch execution.");
        }

        return trial;
    }

    private static void Validate(
        ScenarioDocument document,
        string variantId,
        MonteCarloBatchOptions options,
        string outputDirectory)
    {
        if (string.IsNullOrWhiteSpace(variantId))
        {
            throw new ArgumentException("A variant ID is required.", nameof(variantId));
        }
        if (variantId.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            throw new ArgumentException(
                $"Variant ID '{variantId}' is not safe for output paths.",
                nameof(variantId));
        }
        if (options.Trials <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(options),
                "Monte Carlo trial count must be positive.");
        }
        if (options.Jobs <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(options),
                "Worker count must be positive.");
        }
        if (options.CheckpointEvery <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(options),
                "Checkpoint interval must be positive.");
        }
        if (options.TraceSamples < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(options),
                "Trace sample count cannot be negative.");
        }
        if (options.RandomSeedNamespace is not null &&
            string.IsNullOrWhiteSpace(options.RandomSeedNamespace))
        {
            throw new ArgumentException(
                "A configured random-seed namespace cannot be blank.",
                nameof(options));
        }
        if (string.IsNullOrWhiteSpace(outputDirectory))
        {
            throw new ArgumentException(
                "An output directory is required.",
                nameof(outputDirectory));
        }

        if (document.Missiles.Count != 1)
        {
            throw new InvalidOperationException(
                "Checkpoint 19 Monte Carlo batches require exactly one primary " +
                "Missile Flight per scenario; multi-flight aggregation is deferred.");
        }

        IReadOnlyList<string> preflight = ScenarioPreflightValidator.Validate(document);
        if (preflight.Count > 0)
        {
            throw new InvalidOperationException(
                "Monte Carlo scenario preflight failed: " +
                string.Join("; ", preflight));
        }
        foreach (DefenseDocument defense in document.Defenses)
        {
            if (defense.InterceptionChancePercent is < 0 or > 100)
            {
                throw new InvalidOperationException(
                    $"Defense '{defense.Id}' interceptionChancePercent must be " +
                    "from 0 through 100.");
            }
        }
    }

    private static void PrepareOutputDirectory(string directory, bool resume)
    {
        if (!resume && Directory.Exists(directory))
        {
            Directory.Delete(directory, recursive: true);
        }
        Directory.CreateDirectory(directory);
    }

    private static RunManifest PrepareManifest(
        string path,
        ScenarioDocument document,
        string variantId,
        MonteCarloBatchOptions options,
        string scenarioSha256,
        string runnerHash,
        string coreHash,
        string runKey,
        string randomSeedNamespace)
    {
        if (options.Resume && File.Exists(path))
        {
            RunManifest existing = JsonSerializer.Deserialize<RunManifest>(
                    File.ReadAllText(path),
                    ScenarioDocumentSerialization.ReadOptions) ??
                throw new InvalidOperationException(
                    $"Resume manifest '{path}' could not be read.");
            if (!string.Equals(existing.RunKey, runKey, StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "Resume manifest does not match the scenario, seed, variant, " +
                    "or current runner/Core assemblies.");
            }
            existing.RequestedTrials = options.Trials;
            WriteJsonAtomic(path, existing);
            return existing;
        }

        if (options.Resume && Directory.EnumerateFileSystemEntries(
                Path.GetDirectoryName(path)!).Any())
        {
            throw new InvalidOperationException(
                "Resume was requested for a non-empty output directory without " +
                "a compatible manifest.json.");
        }

        var manifest = new RunManifest
        {
            RunKey = runKey,
            ScenarioId = document.Id,
            VariantId = variantId,
            RandomSeedNamespace = randomSeedNamespace,
            MasterSeed = options.MasterSeed,
            RequestedTrials = options.Trials,
            ScenarioSha256 = scenarioSha256,
            RunnerAssemblySha256 = runnerHash,
            CoreAssemblySha256 = coreHash,
        };
        WriteJsonAtomic(path, manifest);
        return manifest;
    }

    private static Dictionary<int, MonteCarloTrialResult> LoadExistingTrials(
        string path,
        RunManifest manifest,
        int requestedTrials,
        bool resume)
    {
        var result = new Dictionary<int, MonteCarloTrialResult>();
        if (!resume || !File.Exists(path))
        {
            return result;
        }

        int lineNumber = 0;
        foreach (string line in File.ReadLines(path))
        {
            lineNumber++;
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }
            MonteCarloTrialResult trial = JsonSerializer.Deserialize<MonteCarloTrialResult>(
                    line,
                    ScenarioDocumentSerialization.ReadOptions) ??
                throw new InvalidOperationException(
                    $"Could not read trial line {lineNumber} from '{path}'.");
            if (trial.TrialIndex < 0 || trial.TrialIndex >= requestedTrials)
            {
                throw new InvalidOperationException(
                    $"Resume trial index {trial.TrialIndex} is outside the requested " +
                    $"range 0..{requestedTrials - 1}.");
            }
            string expectedSeed = $"0x{TrialSeedDeriver.Derive(
                manifest.MasterSeed,
                manifest.RandomSeedNamespace,
                trial.TrialIndex,
                streamId: 0UL):x16}";
            if (!string.Equals(
                    trial.TrialSeedHex,
                    expectedSeed,
                    StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    $"Resume trial {trial.TrialIndex} has seed {trial.TrialSeedHex}, " +
                    $"expected {expectedSeed}.");
            }
            if (!result.TryAdd(trial.TrialIndex, trial))
            {
                throw new InvalidOperationException(
                    $"Resume trial file contains duplicate index {trial.TrialIndex}.");
            }
        }

        return result;
    }

    private static int ExecuteMissingTrials(
        ScenarioDocument document,
        string variantId,
        MonteCarloBatchOptions options,
        string trialsPath,
        IDictionary<int, MonteCarloTrialResult> trialByIndex,
        string randomSeedNamespace)
    {
        int executed = 0;
        for (int start = 0; start < options.Trials; start += options.CheckpointEvery)
        {
            int endExclusive = Math.Min(
                options.Trials,
                start + options.CheckpointEvery);
            int[] missing = Enumerable.Range(start, endExclusive - start)
                .Where(index => !trialByIndex.ContainsKey(index))
                .ToArray();
            if (missing.Length == 0)
            {
                continue;
            }

            var completed = new ConcurrentDictionary<int, MonteCarloTrialResult>();
            if (options.Jobs == 1)
            {
                foreach (int index in missing)
                {
                    completed[index] = MonteCarloTrialResult.Execute(
                        document,
                        variantId,
                        index,
                        options.MasterSeed,
                        randomSeedNamespace);
                }
            }
            else
            {
                Parallel.ForEach(
                    missing,
                    new ParallelOptions
                    {
                        MaxDegreeOfParallelism = options.Jobs,
                    },
                    index =>
                    {
                        completed[index] = MonteCarloTrialResult.Execute(
                            document,
                            variantId,
                            index,
                            options.MasterSeed,
                            randomSeedNamespace);
                    });
            }

            MonteCarloTrialResult[] ordered = missing
                .OrderBy(index => index)
                .Select(index => completed[index])
                .ToArray();
            if (options.KeepTrialJournal || options.Resume)
            {
                AppendTrials(trialsPath, ordered);
            }
            foreach (MonteCarloTrialResult trial in ordered)
            {
                trialByIndex.Add(trial.TrialIndex, trial);
            }
            executed += ordered.Length;
        }

        return executed;
    }

    private static void AppendTrials(
        string path,
        IEnumerable<MonteCarloTrialResult> trials)
    {
        using var writer = new StreamWriter(
            path,
            append: true,
            encoding: new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        foreach (MonteCarloTrialResult trial in trials)
        {
            writer.WriteLine(JsonSerializer.Serialize(
                trial,
                ScenarioDocumentSerialization.CompactWriteOptions));
        }
    }

    private static void WriteErrorJournal(
        string path,
        IEnumerable<MonteCarloTrialResult> trials)
    {
        MonteCarloTrialResult[] errors = trials
            .Where(trial => !string.IsNullOrWhiteSpace(trial.Error))
            .OrderBy(trial => trial.TrialIndex)
            .ToArray();
        if (errors.Length == 0)
        {
            File.Delete(path);
            return;
        }

        using var writer = new StreamWriter(
            path,
            append: false,
            encoding: new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        foreach (MonteCarloTrialResult trial in errors)
        {
            writer.WriteLine(JsonSerializer.Serialize(
                trial,
                ScenarioDocumentSerialization.CompactWriteOptions));
        }
    }

    private static void WriteMetricsCsv(
        string path,
        IEnumerable<ProbabilityMetricSummary> metrics)
    {
        using var writer = new StreamWriter(
            path,
            append: false,
            encoding: new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        writer.WriteLine(
            "metric,count,trial_count,proportion,confidence_95_low,confidence_95_high");
        foreach (ProbabilityMetricSummary metric in metrics)
        {
            writer.Write(metric.Key);
            writer.Write(',');
            writer.Write(metric.Count.ToString(CultureInfo.InvariantCulture));
            writer.Write(',');
            writer.Write(metric.TrialCount.ToString(CultureInfo.InvariantCulture));
            writer.Write(',');
            writer.Write(metric.Proportion.ToString("R", CultureInfo.InvariantCulture));
            writer.Write(',');
            writer.Write(metric.Confidence95Low.ToString("R", CultureInfo.InvariantCulture));
            writer.Write(',');
            writer.WriteLine(metric.Confidence95High.ToString("R", CultureInfo.InvariantCulture));
        }
    }

    private static void WriteTraceSamples(
        ScenarioDocument document,
        string variantId,
        MonteCarloBatchOptions options,
        IReadOnlyList<MonteCarloTrialResult> trials,
        string outputDirectory,
        string randomSeedNamespace)
    {
        MonteCarloTrialResult[] samples = trials
            .Where(trial => trial.Error is null)
            .GroupBy(
                trial => $"{trial.InterceptionStage ?? "none"}|{trial.FinalOutcome}",
                StringComparer.Ordinal)
            .Select(group => group.OrderBy(trial => trial.TrialIndex).First())
            .OrderBy(trial => trial.TrialIndex)
            .Take(options.TraceSamples)
            .ToArray();

        foreach (MonteCarloTrialResult sample in samples)
        {
            ulong interceptionSeed = TrialSeedDeriver.Derive(
                options.MasterSeed,
                randomSeedNamespace,
                sample.TrialIndex,
                streamId: 1UL);
            ulong terminalSeed = TrialSeedDeriver.Derive(
                options.MasterSeed,
                randomSeedNamespace,
                sample.TrialIndex,
                streamId: 2UL);
            var executionOptions = new ScenarioExecutionOptions
            {
                EvaluateAssertions = false,
                InterceptionResolver = new ProbabilityMissileInterceptionResolver(
                    document.Defenses,
                    interceptionSeed),
                TerminalRandomSource = new DeterministicMissileTerminalRandomSource(
                    terminalSeed),
            };
            ScenarioRunResult trace = new ScenarioExecutor(
                document,
                executionOptions).Execute();
            string traceRoot = Path.Combine(
                outputDirectory,
                "traces",
                $"trial-{sample.TrialIndex:D8}-{sample.FinalOutcome}");
            ScenarioOutputWriter.Write(trace, traceRoot);
        }
    }

    private static void AppendJsonLine<T>(string path, T value)
    {
        string json = JsonSerializer.Serialize(
            value,
            ScenarioDocumentSerialization.CompactWriteOptions);
        File.AppendAllText(
            path,
            json + Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
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
