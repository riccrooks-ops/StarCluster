using System.Collections.Concurrent;
using System.Diagnostics;
using System.Globalization;
using System.Numerics;
using System.Runtime;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public static class FullFlightCalibrationRunner
{
    public readonly record struct TrialBlock(
        int VariantIndex,
        int StartTrialIndex,
        int Count);

    private sealed class OutcomeVector
    {
        public required bool[] EffectiveHits { get; init; }
        public required bool[] TerminalOpportunities { get; init; }
        public required string PairingFingerprintSha256 { get; init; }
    }

    private sealed class SchedulerCounters
    {
        public int ActiveWorkers;
        public int PeakActiveWorkers;
        public int CompletedBlocks;
        public int LastReportedPercent;
    }

    private sealed class TrialScheduleResult
    {
        public required MonteCarloTrialResult?[][] TrialsByVariant { get; init; }
        public required long[] VariantComputeTicks { get; init; }
        public required int[] VariantBlockCounts { get; init; }
        public required int WorkerLimit { get; init; }
        public required int PeakActiveWorkers { get; init; }
        public required int TrialBlockSize { get; init; }
        public required int TrialBlockCount { get; init; }
        public required int CompletedTrialBlockCount { get; init; }
        public required long ComputeElapsedMilliseconds { get; init; }
        public required long ProcessCpuMilliseconds { get; init; }
        public required long AllocatedBytes { get; init; }
        public required int Gen0Collections { get; init; }
        public required int Gen1Collections { get; init; }
        public required int Gen2Collections { get; init; }
        public required int EnvironmentProcessorCount { get; init; }
        public required int ProcessAffinityProcessorCount { get; init; }
        public required bool ServerGarbageCollection { get; init; }
        public required double EffectiveProcessorCores { get; init; }
        public required double NormalizedCpuUtilizationPercent { get; init; }
    }

    public const int MaximumVariantWorkers = 24;

    public static int ResolveVariantWorkerCount(int requestedWorkers, int variantCount)
    {
        if (requestedWorkers <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(requestedWorkers));
        }
        if (variantCount <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(variantCount));
        }

        return Math.Min(Math.Min(requestedWorkers, MaximumVariantWorkers), variantCount);
    }

    public static int ResolveTrialBlockSize(int trialsPerVariant)
    {
        if (trialsPerVariant <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(trialsPerVariant));
        }

        return trialsPerVariant switch
        {
            <= 32 => 4,
            <= 128 => 8,
            _ => 16,
        };
    }

    public static IReadOnlyList<TrialBlock> CreateTrialBlocks(
        int variantCount,
        int trialsPerVariant,
        int blockSize)
    {
        if (variantCount <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(variantCount));
        }
        if (trialsPerVariant <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(trialsPerVariant));
        }
        if (blockSize <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(blockSize));
        }

        var result = new List<TrialBlock>();
        for (int start = 0; start < trialsPerVariant; start += blockSize)
        {
            int count = Math.Min(blockSize, trialsPerVariant - start);
            for (int variantIndex = 0; variantIndex < variantCount; variantIndex++)
            {
                result.Add(new TrialBlock(variantIndex, start, count));
            }
        }

        return result.AsReadOnly();
    }

    public static FullFlightCalibrationRunResult Run(
        FullFlightCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        string studyPath,
        int jobs,
        int? trialsOverride,
        bool keepTrialJournals,
        bool schedulerProof,
        MonteCarloTrialExecutionMode trialExecutionMode,
        string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(study);
        ArgumentNullException.ThrowIfNull(catalog);
        if (string.IsNullOrWhiteSpace(studyPath))
        {
            throw new ArgumentException(
                "A full-flight calibration study path is required.",
                nameof(studyPath));
        }
        if (jobs <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(jobs));
        }
        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(trialsOverride));
        }

        FullFlightCalibrationModel.Validate(study, catalog);
        string runMode = schedulerProof ? "scheduler-proof" : "calibration";
        bool statisticalGatesApplied = !schedulerProof;
        IReadOnlyList<PreparedFullFlightCalibrationVariant> prepared = schedulerProof
            ? FullFlightCalibrationModel.PrepareSchedulerProofVariants(study, catalog)
            : FullFlightCalibrationModel.PrepareVariants(study, catalog);
        ScenarioExecutionPlan[] executionPlans = prepared
            .Select(item => ScenarioExecutionPlan.Prepare(item.Scenario))
            .ToArray();
        string fullStudyPath = Path.GetFullPath(studyPath);
        string studyDirectory = Path.GetDirectoryName(fullStudyPath) ??
            throw new InvalidOperationException(
                "Full-flight study directory could not be resolved.");
        string catalogPath = Path.GetFullPath(
            Path.Combine(studyDirectory, study.ProfileCatalog));
        string fullOutputDirectory = Path.GetFullPath(outputDirectory);
        if (Directory.Exists(fullOutputDirectory))
        {
            Directory.Delete(fullOutputDirectory, recursive: true);
        }
        Directory.CreateDirectory(fullOutputDirectory);

        string randomSeedNamespace =
            study.Id + "|full-flight-common-random-numbers-v3";
        int workerLimit = ResolveVariantWorkerCount(jobs, prepared.Count);
        int trialBlockSize = ResolveTrialBlockSize(trials);
        Console.WriteLine(
            schedulerProof
                ? $"Full-flight scheduler proof preflight: {prepared.Count} variants across " +
                  $"{study.MissileProfiles.Count} missile profiles passed."
                : $"Full-flight preflight: {prepared.Count} variants across " +
                  $"{study.MissileProfiles.Count} missile profiles passed.");
        foreach (IGrouping<string, PreparedFullFlightCalibrationVariant> profileGroup in
                 prepared.GroupBy(item => item.Profile.Id, StringComparer.Ordinal))
        {
            Console.WriteLine(
                $"Prepared {profileGroup.Key}: {profileGroup.Count()} full-flight variants " +
                $"at {trials} trials each.");
        }
        Console.WriteLine(
            $"Full-flight scheduler: {workerLimit} global trial-block workers; " +
            $"block size {trialBlockSize}; maximum worker ceiling 24; " +
            $"trial execution {trialExecutionMode}; " +
            $"server GC {(GCSettings.IsServerGC ? "enabled" : "disabled")}.");

        TrialScheduleResult schedule = ExecuteWithGlobalTrialBlocks(
            prepared,
            executionPlans,
            trials,
            study.MasterSeed,
            randomSeedNamespace,
            workerLimit,
            trialBlockSize,
            trialExecutionMode);

        var resultById = new Dictionary<string, FullFlightCalibrationVariantResult>(
            StringComparer.Ordinal);
        var outcomeById = new Dictionary<string, OutcomeVector>(StringComparer.Ordinal);
        var executionById = new Dictionary<string, FullFlightVariantExecutionRecord>(
            StringComparer.Ordinal);
        var finalizationStopwatch = Stopwatch.StartNew();
        for (int variantIndex = 0; variantIndex < prepared.Count; variantIndex++)
        {
            PreparedFullFlightCalibrationVariant item = prepared[variantIndex];
            MonteCarloTrialResult[] orderedTrials = MaterializeTrials(
                schedule.TrialsByVariant[variantIndex],
                item.Id);
            string variantDirectory = Path.Combine(
                fullOutputDirectory,
                "variants",
                item.Id);
            MonteCarloBatchRunResult batch = FinalizePrecomputedVariant(
                item,
                orderedTrials,
                study,
                randomSeedNamespace,
                keepTrialJournals,
                variantDirectory,
                schedule.VariantComputeTicks[variantIndex],
                schedule.VariantBlockCounts[variantIndex]);
            resultById.Add(item.Id, CreateVariantResult(item, batch));
            outcomeById.Add(item.Id, CreateOutcomeVector(batch.Trials));
            executionById.Add(
                item.Id,
                new FullFlightVariantExecutionRecord
                {
                    VariantId = item.Id,
                    TrialCount = orderedTrials.Length,
                    BlockCount = schedule.VariantBlockCounts[variantIndex],
                    ComputeMilliseconds = StopwatchTicksToMilliseconds(
                        schedule.VariantComputeTicks[variantIndex]),
                });
        }
        finalizationStopwatch.Stop();

        FullFlightCalibrationVariantResult[] orderedResults = prepared
            .Select(item => resultById[item.Id])
            .OrderBy(item => item.Id, StringComparer.Ordinal)
            .ToArray();
        IReadOnlyDictionary<string, OutcomeVector> orderedOutcomes = prepared
            .ToDictionary(item => item.Id, item => outcomeById[item.Id], StringComparer.Ordinal);
        bool commonRandomNumbersVerified = orderedOutcomes.Values
            .Select(item => item.PairingFingerprintSha256)
            .Distinct(StringComparer.Ordinal)
            .Count() == 1;
        FullFlightCalibrationMarginalResult[] marginals = statisticalGatesApplied
            ? CreateMarginals(orderedResults, orderedOutcomes, study)
            : Array.Empty<FullFlightCalibrationMarginalResult>();
        int inferentialMarginals = marginals.Count(item => item.StatisticalGateApplied);
        int descriptiveMarginals = marginals.Length - inferentialMarginals;
        int contradictoryMarginals = marginals.Count(item => item.StatisticallyContradictory);
        int failedVariants = orderedResults.Count(item => !item.Passed);
        int trialErrors = orderedResults.Sum(item => item.TrialErrorCount);
        int datalinkContractFailures = orderedResults.Sum(item =>
            item.DatalinkContractFailureCount);
        int terminalOpportunityInvariantFailures = orderedResults.Sum(item =>
            item.TerminalOpportunityInvariantFailureCount);
        int unexplainedUnresolved = orderedResults.Sum(item =>
            item.UnexplainedUnresolvedCount);
        bool passed =
            failedVariants == 0 &&
            commonRandomNumbersVerified &&
            (!statisticalGatesApplied || contradictoryMarginals == 0);
        var document = new FullFlightCalibrationResultsDocument
        {
            RunMode = runMode,
            StatisticalGatesApplied = statisticalGatesApplied,
            CommonRandomNumbersVerified = commonRandomNumbersVerified,
            StudyId = study.Id,
            StudyName = study.Name,
            StudySha256 = RunnerHashUtility.ComputeFileSha256(fullStudyPath),
            ProfileCatalogSha256 = RunnerHashUtility.ComputeFileSha256(catalogPath),
            RunnerAssemblySha256 = RunnerHashUtility.RunnerAssemblySha256,
            CoreAssemblySha256 = RunnerHashUtility.CoreAssemblySha256,
            TrialsPerVariant = trials,
            VariantCount = orderedResults.Length,
            MarginalCount = marginals.Length,
            InferentialMarginalCount = inferentialMarginals,
            DescriptiveMarginalCount = descriptiveMarginals,
            ContradictoryMarginalCount = contradictoryMarginals,
            FailedVariantCount = failedVariants,
            TrialErrorCount = trialErrors,
            DatalinkContractFailureCount = datalinkContractFailures,
            TerminalOpportunityInvariantFailureCount =
                terminalOpportunityInvariantFailures,
            UnexplainedUnresolvedCount = unexplainedUnresolved,
            MinimumSafetyTurns = study.MinimumSafetyTurns,
            SafetyTurnBuffer = study.SafetyTurnBuffer,
            MinimumDerivedSafetyTurnCap = orderedResults.Min(item => item.SafetyTurnCap),
            MaximumDerivedSafetyTurnCap = orderedResults.Max(item => item.SafetyTurnCap),
            RandomSeedNamespace = randomSeedNamespace,
            MinimumPracticalMarginalDelta = study.MinimumPracticalMarginalDelta,
            MarginalFamilywiseAlpha = study.MarginalFamilywiseAlpha,
            Passed = passed,
            Variants = Array.AsReadOnly(orderedResults),
            Marginals = Array.AsReadOnly(marginals),
        };

        string resultsPath = Path.Combine(
            fullOutputDirectory,
            "full-flight-summary.json");
        WriteJsonAtomic(resultsPath, document);
        WriteSummaryCsv(
            Path.Combine(fullOutputDirectory, "full-flight-summary.csv"),
            orderedResults);
        WriteMarginalsCsv(
            Path.Combine(fullOutputDirectory, "full-flight-marginals.csv"),
            marginals);
        string resultsSha256 = RunnerHashUtility.ComputeFileSha256(resultsPath);
        File.WriteAllText(
            Path.Combine(fullOutputDirectory, "full-flight-result.sha256"),
            resultsSha256 + Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));

        long totalTrials = checked((long)orderedResults.Length * trials);
        long totalElapsedMilliseconds = checked(
            schedule.ComputeElapsedMilliseconds + finalizationStopwatch.ElapsedMilliseconds);
        double totalElapsedSeconds = Math.Max(0.001, totalElapsedMilliseconds / 1000.0);
        double computeElapsedSeconds = Math.Max(
            0.001,
            schedule.ComputeElapsedMilliseconds / 1000.0);
        var execution = new FullFlightExecutionDocument
        {
            RunMode = runMode,
            TrialExecutionMode = trialExecutionMode.ToString(),
            RequestedWorkers = jobs,
            WorkerLimit = workerLimit,
            PeakActiveWorkers = schedule.PeakActiveWorkers,
            VariantCount = orderedResults.Length,
            TrialsPerVariant = trials,
            TotalTrials = totalTrials,
            TrialBlockSize = schedule.TrialBlockSize,
            TrialBlockCount = schedule.TrialBlockCount,
            CompletedTrialBlockCount = schedule.CompletedTrialBlockCount,
            ComputeElapsedMilliseconds = schedule.ComputeElapsedMilliseconds,
            OutputFinalizationMilliseconds = finalizationStopwatch.ElapsedMilliseconds,
            ElapsedMilliseconds = totalElapsedMilliseconds,
            VariantsPerSecond = orderedResults.Length / totalElapsedSeconds,
            TrialsPerSecond = totalTrials / totalElapsedSeconds,
            ComputeTrialsPerSecond = totalTrials / computeElapsedSeconds,
            ProcessCpuMilliseconds = schedule.ProcessCpuMilliseconds,
            EffectiveProcessorCores = schedule.EffectiveProcessorCores,
            NormalizedCpuUtilizationPercent = schedule.NormalizedCpuUtilizationPercent,
            EnvironmentProcessorCount = schedule.EnvironmentProcessorCount,
            ProcessAffinityProcessorCount = schedule.ProcessAffinityProcessorCount,
            ServerGarbageCollection = schedule.ServerGarbageCollection,
            AllocatedBytes = schedule.AllocatedBytes,
            AllocatedBytesPerTrial = totalTrials == 0
                ? 0.0
                : schedule.AllocatedBytes / (double)totalTrials,
            Gen0Collections = schedule.Gen0Collections,
            Gen1Collections = schedule.Gen1Collections,
            Gen2Collections = schedule.Gen2Collections,
            CompletedUtc = DateTimeOffset.UtcNow,
            Variants = Array.AsReadOnly(executionById.Values
                .OrderBy(item => item.VariantId, StringComparer.Ordinal)
                .ToArray()),
        };
        WriteJsonAtomic(
            Path.Combine(fullOutputDirectory, "full-flight-execution.json"),
            execution);
        WriteExecutionCsv(
            Path.Combine(fullOutputDirectory, "full-flight-variant-execution.csv"),
            execution.Variants);

        Console.WriteLine(
            $"Full-flight compute: peak {schedule.PeakActiveWorkers}/{workerLimit} active " +
            $"workers; {totalTrials} trials in {schedule.ComputeElapsedMilliseconds} ms; " +
            $"{execution.ComputeTrialsPerSecond:0.##} trials/second; " +
            $"{schedule.EffectiveProcessorCores:0.##} effective processor cores.");
        Console.WriteLine(
            $"Full-flight runtime: Environment.ProcessorCount " +
            $"{schedule.EnvironmentProcessorCount}; process affinity " +
            $"{schedule.ProcessAffinityProcessorCount}; server GC " +
            $"{schedule.ServerGarbageCollection}; normalized CPU " +
            $"{schedule.NormalizedCpuUtilizationPercent:0.##}%; allocation " +
            $"{execution.AllocatedBytesPerTrial:0.##} bytes/trial.");
        Console.WriteLine(
            $"Full-flight failure categories: trial errors {trialErrors}; datalink " +
            $"contract failures {datalinkContractFailures}; terminal-opportunity " +
            $"invariant failures {terminalOpportunityInvariantFailures}; unexplained " +
            $"unresolved outcomes {unexplainedUnresolved}.");
        if (schedulerProof)
        {
            Console.WriteLine(
                $"Full-flight scheduler proof: {orderedResults.Length - failedVariants} " +
                $"variants passed, {failedVariants} failed; common random numbers " +
                $"{(commonRandomNumbersVerified ? "verified" : "failed")}; statistical " +
                $"gates skipped. Hash: {resultsSha256}. Output: {fullOutputDirectory}");
        }
        else
        {
            Console.WriteLine(
                $"Full-flight calibration: {orderedResults.Length - failedVariants} variants " +
                $"passed, {failedVariants} failed; {contradictoryMarginals} statistically " +
                $"contradictory inferential paired marginals after Holm correction; " +
                $"{descriptiveMarginals} descriptive relative-motion marginals. Hash: " +
                $"{resultsSha256}. Output: {fullOutputDirectory}");
        }
        return new FullFlightCalibrationRunResult
        {
            Results = document,
            Execution = execution,
            ResultsSha256 = resultsSha256,
            OutputDirectory = fullOutputDirectory,
        };
    }

    private static TrialScheduleResult ExecuteWithGlobalTrialBlocks(
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants,
        IReadOnlyList<ScenarioExecutionPlan> executionPlans,
        int trialsPerVariant,
        ulong masterSeed,
        string randomSeedNamespace,
        int workerLimit,
        int blockSize,
        MonteCarloTrialExecutionMode trialExecutionMode)
    {
        ArgumentNullException.ThrowIfNull(variants);
        ArgumentNullException.ThrowIfNull(executionPlans);
        if (executionPlans.Count != variants.Count)
        {
            throw new ArgumentException(
                "Every prepared full-flight variant requires one execution plan.",
                nameof(executionPlans));
        }
        if (variants.Count < workerLimit || workerLimit <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(workerLimit));
        }

        IReadOnlyList<TrialBlock> blocks = CreateTrialBlocks(
            variants.Count,
            trialsPerVariant,
            blockSize);
        var queue = new ConcurrentQueue<TrialBlock>(blocks);
        var exceptions = new ConcurrentQueue<Exception>();
        MonteCarloTrialResult?[][] trialMatrix = Enumerable.Range(0, variants.Count)
            .Select(_ => new MonteCarloTrialResult?[trialsPerVariant])
            .ToArray();
        var variantComputeTicks = new long[variants.Count];
        var variantBlockCounts = new int[variants.Count];
        var counters = new SchedulerCounters();
        using var workersReady = new CountdownEvent(workerLimit);
        using var releaseWorkers = new ManualResetEventSlim(false);
        using var workersActive = new CountdownEvent(workerLimit);

        int environmentProcessorCount = Environment.ProcessorCount;
        int affinityProcessorCount = TryGetProcessAffinityProcessorCount();
        bool serverGarbageCollection = GCSettings.IsServerGC;
        int gen0Before = GC.CollectionCount(0);
        int gen1Before = GC.CollectionCount(1);
        int gen2Before = GC.CollectionCount(2);
        long allocatedBefore = GC.GetTotalAllocatedBytes(precise: false);
        using Process process = Process.GetCurrentProcess();
        process.Refresh();
        TimeSpan cpuBefore = process.TotalProcessorTime;
        var stopwatch = Stopwatch.StartNew();

        Task[] workers = Enumerable.Range(0, workerLimit)
            .Select(_ => Task.Factory.StartNew(
                () =>
                {
                    workersReady.Signal();
                    releaseWorkers.Wait();
                    int nowActive = Interlocked.Increment(ref counters.ActiveWorkers);
                    UpdatePeak(ref counters.PeakActiveWorkers, nowActive);
                    workersActive.Signal();
                    workersActive.Wait();
                    try
                    {
                        while (queue.TryDequeue(out TrialBlock block))
                        {
                            long blockStarted = Stopwatch.GetTimestamp();
                            PreparedFullFlightCalibrationVariant variant =
                                variants[block.VariantIndex];
                            for (int offset = 0; offset < block.Count; offset++)
                            {
                                int trialIndex = block.StartTrialIndex + offset;
                                trialMatrix[block.VariantIndex][trialIndex] =
                                    MonteCarloTrialResult.Execute(
                                        executionPlans[block.VariantIndex],
                                        variant.Id,
                                        trialIndex,
                                        masterSeed,
                                        randomSeedNamespace,
                                        trialExecutionMode);
                            }
                            long blockTicks = Stopwatch.GetTimestamp() - blockStarted;
                            Interlocked.Add(
                                ref variantComputeTicks[block.VariantIndex],
                                blockTicks);
                            Interlocked.Increment(
                                ref variantBlockCounts[block.VariantIndex]);
                            int completed = Interlocked.Increment(
                                ref counters.CompletedBlocks);
                            ReportProgress(counters, completed, blocks.Count, stopwatch);
                        }
                    }
                    catch (Exception exception)
                    {
                        exceptions.Enqueue(exception);
                    }
                    finally
                    {
                        Interlocked.Decrement(ref counters.ActiveWorkers);
                    }
                },
                CancellationToken.None,
                TaskCreationOptions.LongRunning,
                TaskScheduler.Default))
            .ToArray();

        workersReady.Wait();
        releaseWorkers.Set();
        Task.WaitAll(workers);
        stopwatch.Stop();
        process.Refresh();
        TimeSpan cpuAfter = process.TotalProcessorTime;
        if (!exceptions.IsEmpty)
        {
            throw new AggregateException(exceptions);
        }
        if (counters.CompletedBlocks != blocks.Count)
        {
            throw new InvalidOperationException(
                $"The global trial scheduler completed {counters.CompletedBlocks} of " +
                $"{blocks.Count} blocks.");
        }

        long computeElapsedMilliseconds = Math.Max(1, stopwatch.ElapsedMilliseconds);
        long processCpuMilliseconds = Math.Max(
            0,
            (long)(cpuAfter - cpuBefore).TotalMilliseconds);
        double effectiveProcessorCores = processCpuMilliseconds /
            (double)computeElapsedMilliseconds;
        double normalizedCpuUtilizationPercent = environmentProcessorCount <= 0
            ? 0.0
            : 100.0 * effectiveProcessorCores / environmentProcessorCount;

        return new TrialScheduleResult
        {
            TrialsByVariant = trialMatrix,
            VariantComputeTicks = variantComputeTicks,
            VariantBlockCounts = variantBlockCounts,
            WorkerLimit = workerLimit,
            PeakActiveWorkers = counters.PeakActiveWorkers,
            TrialBlockSize = blockSize,
            TrialBlockCount = blocks.Count,
            CompletedTrialBlockCount = counters.CompletedBlocks,
            ComputeElapsedMilliseconds = computeElapsedMilliseconds,
            ProcessCpuMilliseconds = processCpuMilliseconds,
            AllocatedBytes = Math.Max(
                0,
                GC.GetTotalAllocatedBytes(precise: false) - allocatedBefore),
            Gen0Collections = GC.CollectionCount(0) - gen0Before,
            Gen1Collections = GC.CollectionCount(1) - gen1Before,
            Gen2Collections = GC.CollectionCount(2) - gen2Before,
            EnvironmentProcessorCount = environmentProcessorCount,
            ProcessAffinityProcessorCount = affinityProcessorCount,
            ServerGarbageCollection = serverGarbageCollection,
            EffectiveProcessorCores = effectiveProcessorCores,
            NormalizedCpuUtilizationPercent = normalizedCpuUtilizationPercent,
        };
    }

    private static void ReportProgress(
        SchedulerCounters counters,
        int completedBlocks,
        int totalBlocks,
        Stopwatch stopwatch)
    {
        int percent = (int)(100L * completedBlocks / totalBlocks);
        int reportPercent = percent - (percent % 5);
        if (reportPercent <= 0)
        {
            return;
        }

        int observed = Volatile.Read(ref counters.LastReportedPercent);
        while (reportPercent > observed)
        {
            int prior = Interlocked.CompareExchange(
                ref counters.LastReportedPercent,
                reportPercent,
                observed);
            if (prior == observed)
            {
                Console.WriteLine(
                    $"Full-flight progress: {reportPercent}% " +
                    $"({completedBlocks}/{totalBlocks} blocks; " +
                    $"{stopwatch.ElapsedMilliseconds} ms).");
                return;
            }
            observed = prior;
        }
    }

    private static MonteCarloTrialResult[] MaterializeTrials(
        IReadOnlyList<MonteCarloTrialResult?> trials,
        string variantId)
    {
        var result = new MonteCarloTrialResult[trials.Count];
        for (int index = 0; index < trials.Count; index++)
        {
            result[index] = trials[index] ??
                throw new InvalidOperationException(
                    $"Variant '{variantId}' is missing trial {index} after scheduling.");
        }
        return result;
    }

    private static MonteCarloBatchRunResult FinalizePrecomputedVariant(
        PreparedFullFlightCalibrationVariant item,
        MonteCarloTrialResult[] orderedTrials,
        FullFlightCalibrationStudyDocument study,
        string randomSeedNamespace,
        bool keepTrialJournal,
        string outputDirectory,
        long computeTicks,
        int blockCount)
    {
        string scenarioJson = ScenarioDocumentSerialization.SerializeCanonical(item.Scenario);
        string scenarioSha256 = ScenarioDocumentSerialization.Sha256Hex(scenarioJson);
        string runnerHash = RunnerHashUtility.RunnerAssemblySha256;
        string coreHash = RunnerHashUtility.CoreAssemblySha256;
        string runKey = RunnerHashUtility.ComputeRunKey(
            scenarioSha256,
            item.Id,
            randomSeedNamespace,
            study.MasterSeed,
            runnerHash,
            coreHash);
        MonteCarloResultsDocument results = MonteCarloStatistics.Aggregate(
            orderedTrials,
            runKey,
            item.Scenario.Id,
            item.Id,
            study.MasterSeed,
            scenarioSha256,
            runnerHash,
            coreHash);

        Directory.CreateDirectory(outputDirectory);
        WriteJsonAtomic(
            Path.Combine(outputDirectory, "manifest.json"),
            new
            {
                schemaVersion = 2,
                runKey,
                scenarioId = item.Scenario.Id,
                variantId = item.Id,
                randomSeedNamespace,
                masterSeed = study.MasterSeed,
                requestedTrials = orderedTrials.Length,
                scenarioSha256,
                runnerAssemblySha256 = runnerHash,
                coreAssemblySha256 = coreHash,
                executionStrategy = "global-trial-block-workers",
            });
        string resultsPath = Path.Combine(outputDirectory, "results.json");
        WriteJsonAtomic(resultsPath, results);
        WriteProbabilityMetricsCsv(
            Path.Combine(outputDirectory, "metrics.csv"),
            results.Metrics);
        string resultsSha256 = RunnerHashUtility.ComputeFileSha256(resultsPath);
        File.WriteAllText(
            Path.Combine(outputDirectory, "result.sha256"),
            resultsSha256 + Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        WriteJsonAtomic(
            Path.Combine(outputDirectory, "execution.json"),
            new
            {
                schemaVersion = 2,
                executionStrategy = "global-trial-block-workers",
                trials = orderedTrials.Length,
                blockCount,
                computeMilliseconds = StopwatchTicksToMilliseconds(computeTicks),
                keepTrialJournal,
                completedUtc = DateTimeOffset.UtcNow,
            });
        WriteVariantErrorJournal(
            Path.Combine(outputDirectory, "errors.jsonl"),
            orderedTrials);
        if (keepTrialJournal)
        {
            WriteVariantTrialJournal(
                Path.Combine(outputDirectory, "trials.jsonl"),
                orderedTrials);
        }

        return new MonteCarloBatchRunResult
        {
            Results = results,
            ResultsSha256 = resultsSha256,
            OutputDirectory = outputDirectory,
            ResumedTrials = 0,
            ExecutedTrials = orderedTrials.Length,
            Trials = Array.AsReadOnly(orderedTrials),
        };
    }

    private static void WriteProbabilityMetricsCsv(
        string path,
        IEnumerable<ProbabilityMetricSummary> metrics)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "metric,count,trial_count,proportion,confidence_95_low,confidence_95_high");
        foreach (ProbabilityMetricSummary metric in metrics)
        {
            builder.Append(metric.Key);
            builder.Append(',');
            builder.Append(metric.Count.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(metric.TrialCount.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(metric.Proportion.ToString("R", CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(metric.Confidence95Low.ToString("R", CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.AppendLine(
                metric.Confidence95High.ToString("R", CultureInfo.InvariantCulture));
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteVariantErrorJournal(
        string path,
        IEnumerable<MonteCarloTrialResult> trials)
    {
        MonteCarloTrialResult[] errors = trials
            .Where(item => !string.IsNullOrWhiteSpace(item.Error))
            .OrderBy(item => item.TrialIndex)
            .ToArray();
        if (errors.Length == 0)
        {
            File.Delete(path);
            return;
        }
        WriteVariantTrialJournal(path, errors);
    }

    private static void WriteVariantTrialJournal(
        string path,
        IEnumerable<MonteCarloTrialResult> trials)
    {
        using var writer = new StreamWriter(
            path,
            append: false,
            encoding: new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        foreach (MonteCarloTrialResult trial in trials)
        {
            writer.WriteLine(JsonSerializer.Serialize(
                trial,
                ScenarioDocumentSerialization.CompactWriteOptions));
        }
    }

    private static long StopwatchTicksToMilliseconds(long ticks) =>
        Math.Max(0, (long)Math.Round(ticks * 1000.0 / Stopwatch.Frequency));

    private static int TryGetProcessAffinityProcessorCount()
    {
        if (!OperatingSystem.IsWindows())
        {
            return 0;
        }

        try
        {
            using Process process = Process.GetCurrentProcess();
            ulong mask = unchecked((ulong)process.ProcessorAffinity.ToInt64());
            return BitOperations.PopCount(mask);
        }
        catch (Exception)
        {
            return 0;
        }
    }

    private static void UpdatePeak(ref int peak, int candidate)
    {
        int observed = Volatile.Read(ref peak);
        while (candidate > observed)
        {
            int prior = Interlocked.CompareExchange(ref peak, candidate, observed);
            if (prior == observed)
            {
                return;
            }
            observed = prior;
        }
    }

    private static FullFlightCalibrationVariantResult CreateVariantResult(
        PreparedFullFlightCalibrationVariant item,
        MonteCarloBatchRunResult batch)
    {
        IReadOnlyList<MonteCarloTrialResult> trials = batch.Trials;
        ProbabilityMetricSummary terminalOpportunity = Metric(
            "flight.terminalOpportunityReached",
            trials,
            trial => trial.TerminalOpportunityReached);
        ProbabilityMetricSummary missileEntered = Metric(
            "flight.opportunity.missileEnteredTargetHex",
            trials,
            trial => trial.MissileEnteredTargetHexOpportunity);
        ProbabilityMetricSummary targetEntered = Metric(
            "flight.opportunity.targetEnteredMissileHex",
            trials,
            trial => trial.TargetEnteredMissileHexOpportunity);
        ProbabilityMetricSummary actionBeganColocated = Metric(
            "flight.opportunity.actionBeganColocated",
            trials,
            trial => trial.ActionBeganColocatedOpportunity);
        ProbabilityMetricSummary stationarySearchRetry = Metric(
            "flight.opportunity.stationarySearchRetry",
            trials,
            trial => trial.StationarySearchRetryOpportunity);
        ProbabilityMetricSummary invariantFailure = Metric(
            "flight.opportunity.invariantFailure",
            trials,
            trial => trial.Error is null &&
                !trial.TerminalOpportunityInvariantPassed);
        ProbabilityMetricSummary effectiveHit = Metric(
            "effect.effectiveHitPerLaunch",
            trials,
            IsEffectiveHit);
        ProbabilityMetricSummary intercepted = Metric(
            "effect.intercepted",
            trials,
            trial => trial.FinalStatus == nameof(GuidedMissileStatus.Intercepted));
        ProbabilityMetricSummary rangeExhausted = Metric(
            "effect.rangeExhausted",
            trials,
            trial => trial.FinalStatus == nameof(GuidedMissileStatus.RangeExhausted));
        ProbabilityMetricSummary selfDestructed = Metric(
            "effect.selfDestructed",
            trials,
            trial => trial.FinalStatus == nameof(GuidedMissileStatus.SelfDestructed));
        ProbabilityMetricSummary terminalMiss = Metric(
            "outcome.miss",
            trials,
            trial => trial.FinalOutcome == nameof(MissileTerminalOutcome.Miss));
        ProbabilityMetricSummary dud = Metric(
            "outcome.dud",
            trials,
            trial => trial.FinalOutcome == nameof(MissileTerminalOutcome.Dud));
        ProbabilityMetricSummary search = Metric(
            "process.searchActivated",
            trials,
            trial => trial.SearchActivated);
        ProbabilityMetricSummary operationalTimeout = Metric(
            "effect.operationalTimeout",
            trials,
            trial => trial.OperationalTimeoutReached);
        ProbabilityMetricSummary unexplainedUnresolved = Metric(
            "effect.unexplainedUnresolved",
            trials,
            trial => trial.UnexplainedUnresolved);
        ProbabilityMetricSummary unresolved = Metric(
            "effect.unresolvedAtHorizon",
            trials,
            trial => trial.OperationalTimeoutReached || trial.UnexplainedUnresolved);
        ProbabilityMetricSummary datalinkUpdate = Metric(
            "process.datalinkUpdateAttempted",
            trials,
            trial => trial.DatalinkUpdateAttempted);
        ProbabilityMetricSummary blocked = Metric(
            "process.datalinkBlockedObserved",
            trials,
            trial => trial.DatalinkBlockedObserved);
        ProbabilityMetricSummary live = Metric(
            "process.datalinkLiveObserved",
            trials,
            trial => trial.DatalinkLiveObserved);
        ProbabilityMetricSummary datalinkContractFailure = Metric(
            "process.datalinkSemanticContractFailure",
            trials,
            trial => !DatalinkSemanticContractPassed(item, trial));
        ProbabilityMetricSummary expired = Metric(
            "process.retainedReportExpired",
            trials,
            trial => trial.RetainedReportExpiredObserved);
        ProbabilityMetricSummary freshDatalink = Metric(
            "process.freshDatalinkGuidanceUsed",
            trials,
            trial => trial.UsedFreshDatalinkGuidance);
        ProbabilityMetricSummary retainedDatalink = Metric(
            "process.retainedDatalinkGuidanceUsed",
            trials,
            trial => trial.UsedRetainedDatalinkGuidance);
        ProbabilityMetricSummary localSensor = Metric(
            "process.localSensorGuidanceUsed",
            trials,
            trial => trial.UsedLocalSensorGuidance);
        ProbabilityMetricSummary activeSensor = Metric(
            "process.activeSensorUsed",
            trials,
            trial => trial.ActiveSensorUsed);

        int trialErrorCount = trials.Count(trial => trial.Error is not null);
        var failureReasons = new List<string>();
        if (trialErrorCount > 0)
        {
            failureReasons.Add("trial-errors");
        }
        if (datalinkContractFailure.Count > 0)
        {
            failureReasons.Add("datalink-semantic-contract");
        }
        if (invariantFailure.Count > 0)
        {
            failureReasons.Add("terminal-opportunity-invariant");
        }
        if (unexplainedUnresolved.Count > 0)
        {
            failureReasons.Add("unexplained-unresolved");
        }
        bool passed =
            batch.Passed &&
            trials.Count == batch.Results.TrialCount &&
            datalinkContractFailure.Count == 0 &&
            invariantFailure.Count == 0 &&
            unexplainedUnresolved.Count == 0;

        return new FullFlightCalibrationVariantResult
        {
            Id = item.Id,
            ProfileId = item.Profile.Id,
            ProfileName = item.Profile.Name,
            MissileTechnologyLevel = item.MissileTechnology.TechnologyLevel,
            TargetPropulsionTechnologyLevel =
                item.TargetPropulsionTechnology.TechnologyLevel,
            MissileSpeedHexesPerTurn =
                item.MissileTechnology.FlightSpeedHexesPerTurn,
            TargetSpeedHexesPerTurn =
                item.TargetPropulsionTechnology.ShipMovementHexesPerTurn,
            MissileMaximumRangeHexes =
                item.MissileTechnology.MaximumRangeHexes,
            SafetyTurnCap = item.SafetyTurnCap,
            FixedPdsTechnologyLevel = item.FixedPdsTechnologyLevel,
            FixedTargetEcmTechnologyLevel =
                item.TargetEcmTechnology.TechnologyLevel,
            PdsInterceptionChancePercent = item.PdsInterceptionChancePercent,
            TargetMovementPolicy = item.TargetMovementPolicy,
            DatalinkCondition = item.DatalinkCondition,
            RelativeSpeedClass = RelativeSpeedClass(
                item.MissileTechnology.FlightSpeedHexesPerTurn,
                item.TargetPropulsionTechnology.ShipMovementHexesPerTurn),
            Trials = trials.Count,
            TerminalOpportunityProbability = terminalOpportunity.Proportion,
            TerminalOpportunityConfidence95Low =
                terminalOpportunity.Confidence95Low,
            TerminalOpportunityConfidence95High =
                terminalOpportunity.Confidence95High,
            MissileEnteredTargetHexOpportunityProbability = missileEntered.Proportion,
            TargetEnteredMissileHexOpportunityProbability = targetEntered.Proportion,
            ActionBeganColocatedOpportunityProbability = actionBeganColocated.Proportion,
            StationarySearchRetryOpportunityProbability = stationarySearchRetry.Proportion,
            TerminalOpportunityInvariantFailureProbability = invariantFailure.Proportion,
            EffectiveHitPerLaunch = effectiveHit.Proportion,
            EffectiveHitConfidence95Low = effectiveHit.Confidence95Low,
            EffectiveHitConfidence95High = effectiveHit.Confidence95High,
            InterceptionProbability = intercepted.Proportion,
            RangeExhaustionProbability = rangeExhausted.Proportion,
            SelfDestructedProbability = selfDestructed.Proportion,
            TerminalMissProbability = terminalMiss.Proportion,
            DudProbability = dud.Proportion,
            SearchProbability = search.Proportion,
            OperationalTimeoutProbability = operationalTimeout.Proportion,
            UnexplainedUnresolvedProbability = unexplainedUnresolved.Proportion,
            UnresolvedAtHorizonProbability = unresolved.Proportion,
            DatalinkUpdateAttemptedProbability = datalinkUpdate.Proportion,
            DatalinkBlockedObservedProbability = blocked.Proportion,
            DatalinkLiveObservedProbability = live.Proportion,
            DatalinkSemanticContractFailureProbability =
                datalinkContractFailure.Proportion,
            RetainedReportExpiredProbability = expired.Proportion,
            FreshDatalinkGuidanceProbability = freshDatalink.Proportion,
            RetainedDatalinkGuidanceProbability = retainedDatalink.Proportion,
            LocalSensorGuidanceProbability = localSensor.Proportion,
            ActiveSensorUseProbability = activeSensor.Proportion,
            AverageTurnsElapsed = trials.Average(trial => trial.TurnsElapsed),
            AverageMissileActions = trials.Average(trial => trial.MissileActions),
            AverageReplanCount = trials.Average(trial => trial.ReplanCount),
            AverageDistanceTraveled = batch.Results.AverageDistanceTraveled,
            AverageTotalFuelSpent = batch.Results.AverageTotalFuelSpent,
            AverageStationarySearchFuelSpent =
                batch.Results.AverageStationarySearchFuelSpent,
            TrialErrorCount = trialErrorCount,
            DatalinkContractFailureCount = datalinkContractFailure.Count,
            TerminalOpportunityInvariantFailureCount = invariantFailure.Count,
            UnexplainedUnresolvedCount = unexplainedUnresolved.Count,
            FailureReasons = failureReasons.AsReadOnly(),
            ScenarioSha256 = batch.Results.ScenarioSha256,
            ResultsSha256 = batch.ResultsSha256,
            Passed = passed,
        };
    }

    public static bool DatalinkSemanticContractPassed(
        PreparedFullFlightCalibrationVariant item,
        MonteCarloTrialResult trial)
    {
        ArgumentNullException.ThrowIfNull(item);
        ArgumentNullException.ThrowIfNull(trial);
        if (trial.Error is not null || !item.Profile.DatalinkInstalled)
        {
            return true;
        }

        if (item.DatalinkCondition == FullFlightCalibrationModel.OccludedDatalink)
        {
            return !trial.UsedFreshDatalinkGuidance &&
                (!trial.DatalinkUpdateAttempted ||
                 (trial.DatalinkBlockedObserved && !trial.DatalinkLiveObserved));
        }

        if (item.DatalinkCondition == FullFlightCalibrationModel.LiveDatalink)
        {
            return !trial.DatalinkBlockedObserved &&
                (!trial.DatalinkUpdateAttempted || trial.DatalinkLiveObserved);
        }

        throw new InvalidOperationException(
            $"Unsupported datalink condition '{item.DatalinkCondition}'.");
    }

    private static FullFlightCalibrationMarginalResult[] CreateMarginals(
        IReadOnlyList<FullFlightCalibrationVariantResult> variants,
        IReadOnlyDictionary<string, OutcomeVector> outcomes,
        FullFlightCalibrationStudyDocument study)
    {
        var byId = variants.ToDictionary(item => item.Id, StringComparer.Ordinal);
        var marginals = new List<FullFlightCalibrationMarginalResult>();
        int[] missileLevels = study.MissileTechnologyLevels.OrderBy(value => value).ToArray();
        int[] targetLevels = study.TargetPropulsionTechnologyLevels
            .OrderBy(value => value)
            .ToArray();

        foreach (string profile in study.MissileProfiles)
        {
            foreach (int targetTl in targetLevels)
            {
                foreach (string policy in study.TargetMovementPolicies)
                {
                    foreach (string datalink in study.DatalinkConditions)
                    {
                        for (int index = 0; index < missileLevels.Length - 1; index++)
                        {
                            AddMetricPair(
                                marginals,
                                byId,
                                outcomes,
                                study,
                                axis: "missileTechnologyLevel",
                                profile,
                                missileLevels[index],
                                missileLevels[index + 1],
                                targetTl,
                                targetTl,
                                policy,
                                datalink,
                                datalink,
                                expectedDirection: "nondecreasing");
                        }
                    }
                }
            }

            foreach (int missileTl in missileLevels)
            {
                foreach (string policy in study.TargetMovementPolicies)
                {
                    foreach (string datalink in study.DatalinkConditions)
                    {
                        for (int index = 0; index < targetLevels.Length - 1; index++)
                        {
                            string expectedDirection = policy switch
                            {
                                FullFlightCalibrationModel.StationaryPolicy => "flat",
                                FullFlightCalibrationModel.StraightRetreatPolicy => "nonincreasing",
                                _ => string.Empty,
                            };
                            if (expectedDirection.Length == 0)
                            {
                                continue;
                            }
                            AddMetricPair(
                                marginals,
                                byId,
                                outcomes,
                                study,
                                axis: "targetPropulsionTechnologyLevel",
                                profile,
                                missileTl,
                                missileTl,
                                targetLevels[index],
                                targetLevels[index + 1],
                                policy,
                                datalink,
                                datalink,
                                expectedDirection);
                        }
                    }
                }

                foreach (int targetTl in targetLevels)
                {
                    foreach (string policy in study.TargetMovementPolicies)
                    {
                        string expectedDirection =
                            IsInferentialDatalinkPolicy(policy)
                                ? "nondecreasing"
                                : "descriptive";
                        AddMetricPair(
                            marginals,
                            byId,
                            outcomes,
                            study,
                            axis: "datalinkCondition",
                            profile,
                            missileTl,
                            missileTl,
                            targetTl,
                            targetTl,
                            policy,
                            FullFlightCalibrationModel.OccludedDatalink,
                            FullFlightCalibrationModel.LiveDatalink,
                            expectedDirection);
                    }
                }
            }
        }

        int[] inferentialIndexes = marginals
            .Select((item, index) => (Item: item, Index: index))
            .Where(pair => pair.Item.StatisticalGateApplied)
            .Select(pair => pair.Index)
            .ToArray();
        double[] adjusted = PairedMarginalStatistics.AdjustHolm(
            inferentialIndexes
                .Select(index => marginals[index].RawPValue)
                .ToArray());
        for (int rank = 0; rank < inferentialIndexes.Length; rank++)
        {
            FullFlightCalibrationMarginalResult marginal =
                marginals[inferentialIndexes[rank]];
            marginal.HolmAdjustedPValue = adjusted[rank];
            marginal.StatisticallyContradictory =
                !marginal.CommonRandomNumbersVerified ||
                PairedMarginalStatistics.IsStatisticallyContradictory(
                    marginal.ExpectedDirection,
                    marginal.ObservedDelta,
                    marginal.HolmAdjustedPValue,
                    study.MinimumPracticalMarginalDelta,
                    study.MarginalFamilywiseAlpha);
        }
        foreach (FullFlightCalibrationMarginalResult marginal in marginals.Where(item =>
                     !item.StatisticalGateApplied))
        {
            marginal.HolmAdjustedPValue = 1.0;
            marginal.StatisticallyContradictory = false;
        }

        return marginals
            .OrderBy(item => item.Metric, StringComparer.Ordinal)
            .ThenBy(item => item.Axis, StringComparer.Ordinal)
            .ThenBy(item => item.ProfileId, StringComparer.Ordinal)
            .ThenBy(item => item.MissileTechnologyLevel)
            .ThenBy(item => item.TargetPropulsionTechnologyLevel)
            .ThenBy(item => item.TargetMovementPolicy, StringComparer.Ordinal)
            .ThenBy(item => item.DatalinkCondition, StringComparer.Ordinal)
            .ThenBy(item => item.FromValue, StringComparer.Ordinal)
            .ToArray();
    }

    public static bool IsInferentialDatalinkPolicy(string policy) =>
        policy is FullFlightCalibrationModel.StationaryPolicy or
            FullFlightCalibrationModel.StraightRetreatPolicy;

    private static void AddMetricPair(
        ICollection<FullFlightCalibrationMarginalResult> marginals,
        IReadOnlyDictionary<string, FullFlightCalibrationVariantResult> variants,
        IReadOnlyDictionary<string, OutcomeVector> outcomes,
        FullFlightCalibrationStudyDocument study,
        string axis,
        string profile,
        int fromMissileTl,
        int toMissileTl,
        int fromTargetTl,
        int toTargetTl,
        string policy,
        string fromDatalink,
        string toDatalink,
        string expectedDirection)
    {
        string fromId = FullFlightCalibrationModel.CreateVariantId(
            profile,
            fromMissileTl,
            fromTargetTl,
            policy,
            fromDatalink);
        string toId = FullFlightCalibrationModel.CreateVariantId(
            profile,
            toMissileTl,
            toTargetTl,
            policy,
            toDatalink);
        FullFlightCalibrationVariantResult from = variants[fromId];
        FullFlightCalibrationVariantResult to = variants[toId];
        OutcomeVector fromOutcomes = outcomes[fromId];
        OutcomeVector toOutcomes = outcomes[toId];
        bool commonRandomNumbersVerified = string.Equals(
            fromOutcomes.PairingFingerprintSha256,
            toOutcomes.PairingFingerprintSha256,
            StringComparison.Ordinal);

        AddMetric(
            marginals,
            study,
            axis,
            "terminalOpportunity",
            from,
            to,
            fromOutcomes.TerminalOpportunities,
            toOutcomes.TerminalOpportunities,
            expectedDirection,
            commonRandomNumbersVerified,
            fromOutcomes.PairingFingerprintSha256);
        AddMetric(
            marginals,
            study,
            axis,
            "effectiveHitPerLaunch",
            from,
            to,
            fromOutcomes.EffectiveHits,
            toOutcomes.EffectiveHits,
            expectedDirection,
            commonRandomNumbersVerified,
            fromOutcomes.PairingFingerprintSha256);
    }

    private static void AddMetric(
        ICollection<FullFlightCalibrationMarginalResult> marginals,
        FullFlightCalibrationStudyDocument study,
        string axis,
        string metric,
        FullFlightCalibrationVariantResult from,
        FullFlightCalibrationVariantResult to,
        IReadOnlyList<bool> fromOutcomes,
        IReadOnlyList<bool> toOutcomes,
        string expectedDirection,
        bool commonRandomNumbersVerified,
        string pairingFingerprintSha256)
    {
        PairedBinaryDifferenceSummary paired = PairedMarginalStatistics.Compare(
            fromOutcomes,
            toOutcomes,
            expectedDirection);
        string fromValue = axis switch
        {
            "missileTechnologyLevel" => from.MissileTechnologyLevel.ToString(CultureInfo.InvariantCulture),
            "targetPropulsionTechnologyLevel" => from.TargetPropulsionTechnologyLevel.ToString(CultureInfo.InvariantCulture),
            _ => from.DatalinkCondition,
        };
        string toValue = axis switch
        {
            "missileTechnologyLevel" => to.MissileTechnologyLevel.ToString(CultureInfo.InvariantCulture),
            "targetPropulsionTechnologyLevel" => to.TargetPropulsionTechnologyLevel.ToString(CultureInfo.InvariantCulture),
            _ => to.DatalinkCondition,
        };
        marginals.Add(new FullFlightCalibrationMarginalResult
        {
            Metric = metric,
            Axis = axis,
            ProfileId = from.ProfileId,
            MissileTechnologyLevel = axis == "missileTechnologyLevel"
                ? from.MissileTechnologyLevel
                : to.MissileTechnologyLevel,
            TargetPropulsionTechnologyLevel =
                axis == "targetPropulsionTechnologyLevel"
                    ? from.TargetPropulsionTechnologyLevel
                    : to.TargetPropulsionTechnologyLevel,
            TargetMovementPolicy = from.TargetMovementPolicy,
            DatalinkCondition = axis == "datalinkCondition"
                ? from.DatalinkCondition + "->" + to.DatalinkCondition
                : from.DatalinkCondition,
            FromValue = fromValue,
            ToValue = toValue,
            ExpectedDirection = expectedDirection,
            TrialCount = paired.TrialCount,
            NeitherTrue = paired.NeitherTrue,
            FromOnlyTrue = paired.FromOnlyTrue,
            ToOnlyTrue = paired.ToOnlyTrue,
            BothTrue = paired.BothTrue,
            ObservedDelta = paired.ObservedDelta,
            PairedDeltaConfidence95Low = paired.Confidence95Low,
            PairedDeltaConfidence95High = paired.Confidence95High,
            RawPValue = paired.RawPValue,
            MinimumPracticalMarginalDelta = study.MinimumPracticalMarginalDelta,
            MarginalFamilywiseAlpha = study.MarginalFamilywiseAlpha,
            PairingFingerprintSha256 = commonRandomNumbersVerified
                ? pairingFingerprintSha256
                : string.Empty,
            CommonRandomNumbersVerified = commonRandomNumbersVerified,
            StatisticalGateApplied = expectedDirection != "descriptive",
        });
    }

    private static OutcomeVector CreateOutcomeVector(
        IReadOnlyList<MonteCarloTrialResult> trials)
    {
        MonteCarloTrialResult[] ordered = trials
            .OrderBy(item => item.TrialIndex)
            .ToArray();
        string seedText = string.Join(
            "\n",
            ordered.Select(item =>
                $"{item.TrialIndex}|{item.TrialSeedHex}|{item.InterceptionSeedHex}|{item.TerminalSeedHex}"));
        return new OutcomeVector
        {
            EffectiveHits = ordered.Select(IsEffectiveHit).ToArray(),
            TerminalOpportunities = ordered
                .Select(item => item.TerminalOpportunityReached)
                .ToArray(),
            PairingFingerprintSha256 = Sha256(seedText),
        };
    }

    private static ProbabilityMetricSummary Metric(
        string key,
        IReadOnlyList<MonteCarloTrialResult> trials,
        Func<MonteCarloTrialResult, bool> predicate)
    {
        int count = trials.Count(predicate);
        return MonteCarloStatistics.CreateMetric(key, count, trials.Count);
    }

    private static bool IsEffectiveHit(MonteCarloTrialResult trial) =>
        trial.FinalOutcome is nameof(MissileTerminalOutcome.Hit) or
            nameof(MissileTerminalOutcome.CriticalHit);

    private static bool IsTerminalStatus(string status) =>
        status is nameof(GuidedMissileStatus.Expended) or
            nameof(GuidedMissileStatus.Dud) or
            nameof(GuidedMissileStatus.RangeExhausted) or
            nameof(GuidedMissileStatus.Intercepted) or
            nameof(GuidedMissileStatus.SelfDestructed) or
            nameof(GuidedMissileStatus.Destroyed);

    private static string RelativeSpeedClass(int missileSpeed, int targetSpeed) =>
        missileSpeed > targetSpeed
            ? "MissileFaster"
            : missileSpeed < targetSpeed
                ? "TargetFaster"
                : "EqualSpeed";


    private static string Sha256(string value) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value)))
            .ToLowerInvariant();

    private static void WriteSummaryCsv(
        string path,
        IEnumerable<FullFlightCalibrationVariantResult> variants)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "id,profileId,missileTl,targetPropulsionTl,missileSpeed,targetSpeed," +
            "maximumRange,safetyTurnCap,pdsTl,targetEcmTl,pdsChancePercent," +
            "movementPolicy,datalinkCondition,relativeSpeedClass,trials," +
            "terminalOpportunity,missileEnteredTargetHex,targetEnteredMissileHex," +
            "actionBeganColocated,stationarySearchRetry,opportunityInvariantFailure," +
            "effectiveHitPerLaunch,intercepted,rangeExhausted,selfDestructed," +
            "terminalMiss,dud,search,operationalTimeout,unexplainedUnresolved," +
            "unresolvedAtHorizon,datalinkUpdateAttempted,datalinkBlocked," +
            "datalinkLive,datalinkSemanticContractFailure,retainedExpired," +
            "freshDatalinkGuidance,retainedDatalinkGuidance,localSensorGuidance," +
            "activeSensor,averageTurns,averageMissileActions,averageReplans," +
            "averageDistance,averageFuel,averageSearchFuel,trialErrors," +
            "datalinkContractFailures,opportunityInvariantFailures," +
            "unexplainedUnresolvedCount,failureReasons,passed");
        foreach (FullFlightCalibrationVariantResult item in variants)
        {
            builder.AppendLine(string.Join(",", new[]
            {
                Csv(item.Id),
                Csv(item.ProfileId),
                item.MissileTechnologyLevel.ToString(CultureInfo.InvariantCulture),
                item.TargetPropulsionTechnologyLevel.ToString(CultureInfo.InvariantCulture),
                item.MissileSpeedHexesPerTurn.ToString(CultureInfo.InvariantCulture),
                item.TargetSpeedHexesPerTurn.ToString(CultureInfo.InvariantCulture),
                item.MissileMaximumRangeHexes.ToString(CultureInfo.InvariantCulture),
                item.SafetyTurnCap.ToString(CultureInfo.InvariantCulture),
                item.FixedPdsTechnologyLevel.ToString(CultureInfo.InvariantCulture),
                item.FixedTargetEcmTechnologyLevel.ToString(CultureInfo.InvariantCulture),
                item.PdsInterceptionChancePercent.ToString(CultureInfo.InvariantCulture),
                Csv(item.TargetMovementPolicy),
                Csv(item.DatalinkCondition),
                Csv(item.RelativeSpeedClass),
                item.Trials.ToString(CultureInfo.InvariantCulture),
                F(item.TerminalOpportunityProbability),
                F(item.MissileEnteredTargetHexOpportunityProbability),
                F(item.TargetEnteredMissileHexOpportunityProbability),
                F(item.ActionBeganColocatedOpportunityProbability),
                F(item.StationarySearchRetryOpportunityProbability),
                F(item.TerminalOpportunityInvariantFailureProbability),
                F(item.EffectiveHitPerLaunch),
                F(item.InterceptionProbability),
                F(item.RangeExhaustionProbability),
                F(item.SelfDestructedProbability),
                F(item.TerminalMissProbability),
                F(item.DudProbability),
                F(item.SearchProbability),
                F(item.OperationalTimeoutProbability),
                F(item.UnexplainedUnresolvedProbability),
                F(item.UnresolvedAtHorizonProbability),
                F(item.DatalinkUpdateAttemptedProbability),
                F(item.DatalinkBlockedObservedProbability),
                F(item.DatalinkLiveObservedProbability),
                F(item.DatalinkSemanticContractFailureProbability),
                F(item.RetainedReportExpiredProbability),
                F(item.FreshDatalinkGuidanceProbability),
                F(item.RetainedDatalinkGuidanceProbability),
                F(item.LocalSensorGuidanceProbability),
                F(item.ActiveSensorUseProbability),
                F(item.AverageTurnsElapsed),
                F(item.AverageMissileActions),
                F(item.AverageReplanCount),
                F(item.AverageDistanceTraveled),
                F(item.AverageTotalFuelSpent),
                F(item.AverageStationarySearchFuelSpent),
                item.TrialErrorCount.ToString(CultureInfo.InvariantCulture),
                item.DatalinkContractFailureCount.ToString(CultureInfo.InvariantCulture),
                item.TerminalOpportunityInvariantFailureCount.ToString(CultureInfo.InvariantCulture),
                item.UnexplainedUnresolvedCount.ToString(CultureInfo.InvariantCulture),
                Csv(string.Join(";", item.FailureReasons)),
                item.Passed ? "true" : "false",
            }));
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteMarginalsCsv(
        string path,
        IEnumerable<FullFlightCalibrationMarginalResult> marginals)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "metric,axis,profileId,missileTl,targetPropulsionTl,movementPolicy," +
            "datalinkCondition,fromValue,toValue,expectedDirection,trialCount," +
            "neitherTrue,fromOnlyTrue,toOnlyTrue,bothTrue,observedDelta," +
            "confidenceLow,confidenceHigh,rawPValue,holmAdjustedPValue," +
            "commonRandomNumbersVerified,statisticalGateApplied," +
            "statisticallyContradictory");
        foreach (FullFlightCalibrationMarginalResult item in marginals)
        {
            builder.AppendLine(string.Join(",", new[]
            {
                Csv(item.Metric),
                Csv(item.Axis),
                Csv(item.ProfileId),
                item.MissileTechnologyLevel.ToString(CultureInfo.InvariantCulture),
                item.TargetPropulsionTechnologyLevel.ToString(CultureInfo.InvariantCulture),
                Csv(item.TargetMovementPolicy),
                Csv(item.DatalinkCondition),
                Csv(item.FromValue),
                Csv(item.ToValue),
                Csv(item.ExpectedDirection),
                item.TrialCount.ToString(CultureInfo.InvariantCulture),
                item.NeitherTrue.ToString(CultureInfo.InvariantCulture),
                item.FromOnlyTrue.ToString(CultureInfo.InvariantCulture),
                item.ToOnlyTrue.ToString(CultureInfo.InvariantCulture),
                item.BothTrue.ToString(CultureInfo.InvariantCulture),
                F(item.ObservedDelta),
                F(item.PairedDeltaConfidence95Low),
                F(item.PairedDeltaConfidence95High),
                F(item.RawPValue),
                F(item.HolmAdjustedPValue),
                item.CommonRandomNumbersVerified ? "true" : "false",
                item.StatisticalGateApplied ? "true" : "false",
                item.StatisticallyContradictory ? "true" : "false",
            }));
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteExecutionCsv(
        string path,
        IEnumerable<FullFlightVariantExecutionRecord> variants)
    {
        var builder = new StringBuilder();
        builder.AppendLine("variantId,trialCount,blockCount,computeMilliseconds");
        foreach (FullFlightVariantExecutionRecord item in variants)
        {
            builder.AppendLine(string.Join(",", new[]
            {
                Csv(item.VariantId),
                item.TrialCount.ToString(CultureInfo.InvariantCulture),
                item.BlockCount.ToString(CultureInfo.InvariantCulture),
                item.ComputeMilliseconds.ToString(CultureInfo.InvariantCulture),
            }));
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteJsonAtomic<T>(string path, T value)
    {
        string temporary = path + ".tmp";
        File.WriteAllText(
            temporary,
            JsonSerializer.Serialize(
                value,
                ScenarioDocumentSerialization.IndentedWriteOptions),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        File.Move(temporary, path, overwrite: true);
    }

    private static string F(double value) =>
        value.ToString("0.#################", CultureInfo.InvariantCulture);

    private static string Csv(string value) =>
        "\"" + value.Replace("\"", "\"\"") + "\"";
}
