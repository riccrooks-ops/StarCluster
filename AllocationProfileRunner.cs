using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.Json;

namespace StarCluster.ScenarioRunner;

public sealed class AllocationProfileStageDocument
{
    public required string Mode { get; init; }
    public required string Stage { get; init; }
    public string? ParentStage { get; init; }
    public required string Level { get; init; }
    public bool IsDerived { get; init; }
    public long InvocationCount { get; init; }
    public long AllocatedBytes { get; init; }
    public double BytesPerTrial { get; init; }
    public double PercentOfTrialTotal { get; init; }
    public long ElapsedTicks { get; init; }
    public double ElapsedMilliseconds { get; init; }
    public double MillisecondsPerTrial { get; init; }
}

public sealed class AllocationProfileModeDocument
{
    public required string Mode { get; init; }
    public int TrialCount { get; init; }
    public int ErrorCount { get; init; }
    public long GlobalAllocatedBytes { get; init; }
    public double GlobalBytesPerTrial { get; init; }
    public long ProfiledThreadAllocatedBytes { get; init; }
    public double ProfiledThreadBytesPerTrial { get; init; }
    public double ProfiledToGlobalAllocationRatio { get; init; }
    public long ElapsedMilliseconds { get; init; }
    public double TrialsPerSecond { get; init; }
    public long TopLevelAttributedBytes { get; init; }
    public double TopLevelAttributionCoverage { get; init; }
    public bool HierarchyValid { get; init; }
    public required IReadOnlyList<AllocationProfileStageDocument> Stages { get; init; }
}

public sealed class AllocationProfileSummaryDocument
{
    public int SchemaVersion { get; init; } = 2;
    public required string StudyId { get; init; }
    public int VariantCount { get; init; }
    public int WarmupTrialsPerVariant { get; init; }
    public int MeasuredTrialsPerVariant { get; init; }
    public int MeasuredTrialsPerMode { get; init; }
    public int ParityFailureCount { get; init; }
    public bool Passed { get; init; }
    public required IReadOnlyList<AllocationProfileModeDocument> Modes { get; init; }
}

public sealed class AllocationProfileRunResult
{
    public required AllocationProfileSummaryDocument Summary { get; init; }
    public required string OutputDirectory { get; init; }

    public bool Passed => Summary.Passed;
}

public static class AllocationProfileRunner
{
    private static readonly ScenarioAllocationStage[] AllStages =
        Enum.GetValues<ScenarioAllocationStage>();

    private static readonly ScenarioAllocationStage[] TopLevelStages =
    {
        ScenarioAllocationStage.SeedDerivation,
        ScenarioAllocationStage.TrialSetup,
        ScenarioAllocationStage.ExecutorConstruction,
        ScenarioAllocationStage.ShipMovement,
        ScenarioAllocationStage.MissileAdvancement,
        ScenarioAllocationStage.PhaseAdvancement,
        ScenarioAllocationStage.ScenarioFinalization,
        ScenarioAllocationStage.ResultProjection,
    };

    private static readonly ScenarioAllocationStage[] InitializationStages =
    {
        ScenarioAllocationStage.InitializationMapCreation,
        ScenarioAllocationStage.InitializationStaticObjectPlacement,
        ScenarioAllocationStage.InitializationShipStateCreation,
        ScenarioAllocationStage.InitializationPriorTrackSeeding,
        ScenarioAllocationStage.InitializationMissileStateCreation,
        ScenarioAllocationStage.InitializationTurnAndJournalCreation,
        ScenarioAllocationStage.InitializationInitialTrackRefresh,
        ScenarioAllocationStage.InitializationDiagnostics,
        ScenarioAllocationStage.InitializationResultConstruction,
    };

    private sealed class StageAccumulator
    {
        public long AllocatedBytes;
        public long ElapsedTicks;
        public long InvocationCount;

        public void Add(ScenarioAllocationMeasurement measurement)
        {
            AllocatedBytes += measurement.AllocatedBytes;
            ElapsedTicks += measurement.ElapsedTicks;
            InvocationCount += measurement.InvocationCount;
        }
    }

    private sealed class TrialSample
    {
        public required MonteCarloTrialExecutionMode Mode { get; init; }
        public required string VariantId { get; init; }
        public required string ProfileId { get; init; }
        public int MissileTechnologyLevel { get; init; }
        public int TargetPropulsionTechnologyLevel { get; init; }
        public required string TargetMovementPolicy { get; init; }
        public required string DatalinkCondition { get; init; }
        public int TrialIndex { get; init; }
        public bool HadError { get; init; }
        public required string FinalStatus { get; init; }
        public int MissileActions { get; init; }
        public int TurnsElapsed { get; init; }
        public int DistanceTraveled { get; init; }
        public long GlobalAllocatedBytes { get; init; }
        public required long[] StageAllocatedBytes { get; init; }
    }

    private sealed class ModeAccumulator
    {
        public required MonteCarloTrialExecutionMode Mode { get; init; }
        public required StageAccumulator[] Stages { get; init; }
        public required List<TrialSample> Samples { get; init; }
        public int TrialCount;
        public int ErrorCount;
        public long GlobalAllocatedBytes;
        public long ElapsedMilliseconds;
    }

    public static AllocationProfileRunResult Run(
        FullFlightCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        int measuredTrialsPerVariant,
        int warmupTrialsPerVariant,
        string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(study);
        ArgumentNullException.ThrowIfNull(catalog);
        if (measuredTrialsPerVariant <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(measuredTrialsPerVariant));
        }
        if (warmupTrialsPerVariant < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(warmupTrialsPerVariant));
        }

        FullFlightCalibrationModel.Validate(study, catalog);
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareSchedulerProofVariants(study, catalog);
        ScenarioExecutionPlan[] plans = variants
            .Select(item => ScenarioExecutionPlan.Prepare(item.Scenario))
            .ToArray();
        string fullOutputDirectory = Path.GetFullPath(outputDirectory);
        if (Directory.Exists(fullOutputDirectory))
        {
            Directory.Delete(fullOutputDirectory, recursive: true);
        }
        Directory.CreateDirectory(fullOutputDirectory);

        string randomSeedNamespace =
            study.Id + "|allocation-profile-v1";
        Console.WriteLine(
            $"Allocation profile preflight: {variants.Count} scheduler-proof variants " +
            $"across {study.MissileProfiles.Count} missile profiles passed.");
        Console.WriteLine(
            $"Allocation profile policy: one worker; {warmupTrialsPerVariant} warmup " +
            $"and {measuredTrialsPerVariant} measured trials per variant per mode.");

        WarmUp(
            variants,
            plans,
            study.MasterSeed,
            randomSeedNamespace,
            warmupTrialsPerVariant);
        ForceFullCollection();

        var diagnosticFingerprints = new Dictionary<string, string>(
            StringComparer.Ordinal);
        var parityFailures = new List<string>();
        ModeAccumulator diagnostic = MeasureMode(
            variants,
            plans,
            study.MasterSeed,
            randomSeedNamespace,
            measuredTrialsPerVariant,
            MonteCarloTrialExecutionMode.DiagnosticJournal,
            diagnosticFingerprints,
            parityFailures);
        ForceFullCollection();
        ModeAccumulator compact = MeasureMode(
            variants,
            plans,
            study.MasterSeed,
            randomSeedNamespace,
            measuredTrialsPerVariant,
            MonteCarloTrialExecutionMode.CompactMetrics,
            diagnosticFingerprints,
            parityFailures);

        AllocationProfileModeDocument diagnosticDocument =
            CreateModeDocument(diagnostic);
        AllocationProfileModeDocument compactDocument =
            CreateModeDocument(compact);
        bool passed =
            diagnostic.ErrorCount == 0 &&
            compact.ErrorCount == 0 &&
            parityFailures.Count == 0 &&
            diagnosticDocument.HierarchyValid &&
            compactDocument.HierarchyValid &&
            diagnosticDocument.TopLevelAttributionCoverage >= 0.90 &&
            compactDocument.TopLevelAttributionCoverage >= 0.90 &&
            IsPlausibleGlobalRatio(
                diagnosticDocument.ProfiledToGlobalAllocationRatio) &&
            IsPlausibleGlobalRatio(
                compactDocument.ProfiledToGlobalAllocationRatio);
        var summary = new AllocationProfileSummaryDocument
        {
            StudyId = study.Id,
            VariantCount = variants.Count,
            WarmupTrialsPerVariant = warmupTrialsPerVariant,
            MeasuredTrialsPerVariant = measuredTrialsPerVariant,
            MeasuredTrialsPerMode = variants.Count * measuredTrialsPerVariant,
            ParityFailureCount = parityFailures.Count,
            Passed = passed,
            Modes = new[] { diagnosticDocument, compactDocument },
        };

        WriteJson(
            Path.Combine(fullOutputDirectory, "allocation-profile-summary.json"),
            summary);
        WriteStageCsv(
            Path.Combine(fullOutputDirectory, "allocation-stages.csv"),
            summary.Modes.SelectMany(item => item.Stages));
        WriteTrialCsv(
            Path.Combine(fullOutputDirectory, "allocation-trials.csv"),
            diagnostic.Samples.Concat(compact.Samples));
        WriteParityFailures(
            Path.Combine(fullOutputDirectory, "parity-failures.txt"),
            parityFailures);
        WriteTextReport(
            Path.Combine(fullOutputDirectory, "allocation-profile-report.txt"),
            summary);

        PrintModeSummary(diagnosticDocument);
        PrintModeSummary(compactDocument);
        Console.WriteLine(
            $"Allocation profile parity: {summary.MeasuredTrialsPerMode - parityFailures.Count} " +
            $"matched, {parityFailures.Count} failed.");
        Console.WriteLine(
            $"Allocation profile: {(passed ? "PASS" : "FAIL")}. Output: " +
            fullOutputDirectory);

        return new AllocationProfileRunResult
        {
            Summary = summary,
            OutputDirectory = fullOutputDirectory,
        };
    }

    private static void ForceFullCollection()
    {
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();
    }

    private static void WarmUp(
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants,
        IReadOnlyList<ScenarioExecutionPlan> plans,
        ulong masterSeed,
        string randomSeedNamespace,
        int warmupTrialsPerVariant)
    {
        if (warmupTrialsPerVariant == 0)
        {
            return;
        }

        var profile = new ScenarioAllocationProfile();
        foreach (MonteCarloTrialExecutionMode mode in new[]
                 {
                     MonteCarloTrialExecutionMode.DiagnosticJournal,
                     MonteCarloTrialExecutionMode.CompactMetrics,
                 })
        {
            for (int variantIndex = 0; variantIndex < variants.Count; variantIndex++)
            {
                for (int warmupIndex = 0;
                     warmupIndex < warmupTrialsPerVariant;
                     warmupIndex++)
                {
                    int trialIndex = 100000 + warmupIndex;
                    profile.Reset();
                    MonteCarloTrialResult result = MonteCarloTrialResult.Execute(
                        plans[variantIndex],
                        variants[variantIndex].Id,
                        trialIndex,
                        masterSeed,
                        randomSeedNamespace,
                        mode,
                        profile);
                    _ = JsonSerializer.Serialize(
                        result,
                        ScenarioDocumentSerialization.CompactWriteOptions);
                }
            }
        }
    }

    private static ModeAccumulator MeasureMode(
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants,
        IReadOnlyList<ScenarioExecutionPlan> plans,
        ulong masterSeed,
        string randomSeedNamespace,
        int measuredTrialsPerVariant,
        MonteCarloTrialExecutionMode mode,
        IDictionary<string, string> diagnosticFingerprints,
        ICollection<string> parityFailures)
    {
        var accumulator = new ModeAccumulator
        {
            Mode = mode,
            Stages = AllStages.Select(_ => new StageAccumulator()).ToArray(),
            Samples = new List<TrialSample>(
                variants.Count * measuredTrialsPerVariant),
        };
        var profile = new ScenarioAllocationProfile();
        for (int variantIndex = 0; variantIndex < variants.Count; variantIndex++)
        {
            PreparedFullFlightCalibrationVariant variant = variants[variantIndex];
            for (int trialIndex = 0;
                 trialIndex < measuredTrialsPerVariant;
                 trialIndex++)
            {
                profile.Reset();
                long globalBefore = GC.GetTotalAllocatedBytes(precise: true);
                MonteCarloTrialResult result = MonteCarloTrialResult.Execute(
                    plans[variantIndex],
                    variant.Id,
                    trialIndex,
                    masterSeed,
                    randomSeedNamespace,
                    mode,
                    profile);
                long globalAfter = GC.GetTotalAllocatedBytes(precise: true);
                long globalAllocatedBytes = Math.Max(
                    0,
                    globalAfter - globalBefore);
                accumulator.GlobalAllocatedBytes += globalAllocatedBytes;
                accumulator.TrialCount++;
                if (!string.IsNullOrWhiteSpace(result.Error))
                {
                    accumulator.ErrorCount++;
                }

                var stageAllocatedBytes = new long[AllStages.Length];
                foreach (ScenarioAllocationStage stage in AllStages)
                {
                    ScenarioAllocationMeasurement measurement = profile.Get(stage);
                    accumulator.Stages[(int)stage].Add(measurement);
                    stageAllocatedBytes[(int)stage] = measurement.AllocatedBytes;
                }
                accumulator.Samples.Add(new TrialSample
                {
                    Mode = mode,
                    VariantId = variant.Id,
                    ProfileId = variant.Profile.Id,
                    MissileTechnologyLevel =
                        variant.MissileTechnology.TechnologyLevel,
                    TargetPropulsionTechnologyLevel =
                        variant.TargetPropulsionTechnology.TechnologyLevel,
                    TargetMovementPolicy = variant.TargetMovementPolicy,
                    DatalinkCondition = variant.DatalinkCondition,
                    TrialIndex = trialIndex,
                    HadError = !string.IsNullOrWhiteSpace(result.Error),
                    FinalStatus = result.FinalStatus,
                    MissileActions = result.MissileActions,
                    TurnsElapsed = result.TurnsElapsed,
                    DistanceTraveled = result.DistanceTraveled,
                    GlobalAllocatedBytes = globalAllocatedBytes,
                    StageAllocatedBytes = stageAllocatedBytes,
                });

                string key = variant.Id + "|" + trialIndex.ToString(
                    CultureInfo.InvariantCulture);
                string fingerprint = JsonSerializer.Serialize(
                    result,
                    ScenarioDocumentSerialization.CompactWriteOptions);
                if (mode == MonteCarloTrialExecutionMode.DiagnosticJournal)
                {
                    diagnosticFingerprints[key] = fingerprint;
                }
                else if (!diagnosticFingerprints.TryGetValue(
                             key,
                             out string? diagnosticFingerprint) ||
                         !string.Equals(
                             diagnosticFingerprint,
                             fingerprint,
                             StringComparison.Ordinal))
                {
                    parityFailures.Add(key);
                }
            }
        }
        long trialElapsedTicks = accumulator.Stages[
            (int)ScenarioAllocationStage.TrialTotal].ElapsedTicks;
        accumulator.ElapsedMilliseconds = Math.Max(
            1,
            (long)Math.Ceiling(
                1000.0 * trialElapsedTicks / Stopwatch.Frequency));
        return accumulator;
    }

    private static AllocationProfileModeDocument CreateModeDocument(
        ModeAccumulator accumulator)
    {
        long totalBytes = accumulator.Stages[
            (int)ScenarioAllocationStage.TrialTotal].AllocatedBytes;
        long totalTicks = accumulator.Stages[
            (int)ScenarioAllocationStage.TrialTotal].ElapsedTicks;
        long topLevelBytes = TopLevelStages.Sum(
            stage => accumulator.Stages[(int)stage].AllocatedBytes);
        long topLevelTicks = TopLevelStages.Sum(
            stage => accumulator.Stages[(int)stage].ElapsedTicks);
        bool hierarchyValid = topLevelBytes <= totalBytes;
        var rows = new List<AllocationProfileStageDocument>();
        foreach (ScenarioAllocationStage stage in AllStages)
        {
            StageAccumulator measurement = accumulator.Stages[(int)stage];
            rows.Add(CreateStageDocument(
                accumulator.Mode,
                stage.ToString(),
                ParentOf(stage)?.ToString(),
                LevelOf(stage),
                isDerived: false,
                measurement.InvocationCount,
                measurement.AllocatedBytes,
                measurement.ElapsedTicks,
                accumulator.TrialCount,
                totalBytes));
        }

        hierarchyValid &= AddResidual(
            rows,
            accumulator,
            "TopLevelResidual",
            ScenarioAllocationStage.TrialTotal,
            TopLevelStages,
            accumulator.TrialCount,
            totalBytes);
        hierarchyValid &= AddResidual(
            rows,
            accumulator,
            "ExecutorConstructionResidual",
            ScenarioAllocationStage.ExecutorConstruction,
            new[] { ScenarioAllocationStage.RuntimeInitialization },
            accumulator.TrialCount,
            totalBytes);
        hierarchyValid &= AddResidual(
            rows,
            accumulator,
            "RuntimeInitializationResidual",
            ScenarioAllocationStage.RuntimeInitialization,
            InitializationStages,
            accumulator.TrialCount,
            totalBytes);
        hierarchyValid &= AddResidual(
            rows,
            accumulator,
            "ShipMovementResidual",
            ScenarioAllocationStage.ShipMovement,
            new[]
            {
                ScenarioAllocationStage.ShipMovementPlanning,
                ScenarioAllocationStage.ShipMovementStepExecution,
                ScenarioAllocationStage.TargetMovementObservation,
                ScenarioAllocationStage.TrackRefreshAfterShipMovement,
            },
            accumulator.TrialCount,
            totalBytes);
        hierarchyValid &= AddResidual(
            rows,
            accumulator,
            "MissileAdvancementResidual",
            ScenarioAllocationStage.MissileAdvancement,
            new[]
            {
                ScenarioAllocationStage.MissileInterceptionContext,
                ScenarioAllocationStage.MissileDatalinkUpdate,
                ScenarioAllocationStage.MissileGuidanceAdvance,
                ScenarioAllocationStage.MissileOutcomeCapture,
                ScenarioAllocationStage.TrackRefreshAfterMissileMovement,
            },
            accumulator.TrialCount,
            totalBytes);

        return new AllocationProfileModeDocument
        {
            Mode = accumulator.Mode.ToString(),
            TrialCount = accumulator.TrialCount,
            ErrorCount = accumulator.ErrorCount,
            GlobalAllocatedBytes = accumulator.GlobalAllocatedBytes,
            GlobalBytesPerTrial = Divide(
                accumulator.GlobalAllocatedBytes,
                accumulator.TrialCount),
            ProfiledThreadAllocatedBytes = totalBytes,
            ProfiledThreadBytesPerTrial = Divide(totalBytes, accumulator.TrialCount),
            ProfiledToGlobalAllocationRatio =
                accumulator.GlobalAllocatedBytes == 0
                    ? 0.0
                    : totalBytes / (double)accumulator.GlobalAllocatedBytes,
            ElapsedMilliseconds = accumulator.ElapsedMilliseconds,
            TrialsPerSecond = 1000.0 * accumulator.TrialCount /
                accumulator.ElapsedMilliseconds,
            TopLevelAttributedBytes = topLevelBytes,
            TopLevelAttributionCoverage =
                totalBytes == 0 ? 0.0 : topLevelBytes / (double)totalBytes,
            HierarchyValid = hierarchyValid && topLevelTicks <= totalTicks,
            Stages = rows.AsReadOnly(),
        };
    }

    private static bool AddResidual(
        ICollection<AllocationProfileStageDocument> rows,
        ModeAccumulator accumulator,
        string name,
        ScenarioAllocationStage parent,
        IReadOnlyList<ScenarioAllocationStage> children,
        int trialCount,
        long trialTotalBytes)
    {
        StageAccumulator parentMeasurement = accumulator.Stages[(int)parent];
        long childBytes = children.Sum(
            child => accumulator.Stages[(int)child].AllocatedBytes);
        long childTicks = children.Sum(
            child => accumulator.Stages[(int)child].ElapsedTicks);
        long residualBytes = parentMeasurement.AllocatedBytes - childBytes;
        long residualTicks = parentMeasurement.ElapsedTicks - childTicks;
        bool valid = residualBytes >= 0 && residualTicks >= 0;
        rows.Add(CreateStageDocument(
            accumulator.Mode,
            name,
            parent.ToString(),
            "Residual",
            isDerived: true,
            parentMeasurement.InvocationCount,
            Math.Max(0, residualBytes),
            Math.Max(0, residualTicks),
            trialCount,
            trialTotalBytes));
        return valid;
    }

    private static AllocationProfileStageDocument CreateStageDocument(
        MonteCarloTrialExecutionMode mode,
        string stage,
        string? parentStage,
        string level,
        bool isDerived,
        long invocationCount,
        long allocatedBytes,
        long elapsedTicks,
        int trialCount,
        long trialTotalBytes) => new()
        {
            Mode = mode.ToString(),
            Stage = stage,
            ParentStage = parentStage,
            Level = level,
            IsDerived = isDerived,
            InvocationCount = invocationCount,
            AllocatedBytes = allocatedBytes,
            BytesPerTrial = Divide(allocatedBytes, trialCount),
            PercentOfTrialTotal = trialTotalBytes == 0
                ? 0.0
                : allocatedBytes / (double)trialTotalBytes,
            ElapsedTicks = elapsedTicks,
            ElapsedMilliseconds = 1000.0 * elapsedTicks / Stopwatch.Frequency,
            MillisecondsPerTrial = trialCount == 0
                ? 0.0
                : 1000.0 * elapsedTicks / Stopwatch.Frequency / trialCount,
        };

    private static ScenarioAllocationStage? ParentOf(
        ScenarioAllocationStage stage) => stage switch
        {
            ScenarioAllocationStage.TrialTotal => null,
            ScenarioAllocationStage.RuntimeInitialization =>
                ScenarioAllocationStage.ExecutorConstruction,
            ScenarioAllocationStage.InitializationMapCreation or
            ScenarioAllocationStage.InitializationStaticObjectPlacement or
            ScenarioAllocationStage.InitializationShipStateCreation or
            ScenarioAllocationStage.InitializationPriorTrackSeeding or
            ScenarioAllocationStage.InitializationMissileStateCreation or
            ScenarioAllocationStage.InitializationTurnAndJournalCreation or
            ScenarioAllocationStage.InitializationInitialTrackRefresh or
            ScenarioAllocationStage.InitializationDiagnostics or
            ScenarioAllocationStage.InitializationResultConstruction =>
                ScenarioAllocationStage.RuntimeInitialization,
            ScenarioAllocationStage.ShipMovementPlanning or
            ScenarioAllocationStage.ShipMovementStepExecution or
            ScenarioAllocationStage.TargetMovementObservation or
            ScenarioAllocationStage.TrackRefreshAfterShipMovement =>
                ScenarioAllocationStage.ShipMovement,
            ScenarioAllocationStage.MissileInterceptionContext or
            ScenarioAllocationStage.MissileDatalinkUpdate or
            ScenarioAllocationStage.MissileGuidanceAdvance or
            ScenarioAllocationStage.MissileOutcomeCapture or
            ScenarioAllocationStage.TrackRefreshAfterMissileMovement =>
                ScenarioAllocationStage.MissileAdvancement,
            _ => ScenarioAllocationStage.TrialTotal,
        };

    private static string LevelOf(ScenarioAllocationStage stage)
    {
        if (stage == ScenarioAllocationStage.TrialTotal)
        {
            return "Total";
        }
        return ParentOf(stage) == ScenarioAllocationStage.TrialTotal
            ? "TopLevel"
            : "Detail";
    }

    private static bool IsPlausibleGlobalRatio(double value) =>
        value is >= 0.75 and <= 1.25;

    private static double Divide(long numerator, int denominator) =>
        denominator == 0 ? 0.0 : numerator / (double)denominator;

    private static void WriteJson(string path, object value)
    {
        string json = JsonSerializer.Serialize(
            value,
            ScenarioDocumentSerialization.IndentedWriteOptions);
        File.WriteAllText(
            path,
            json + Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteStageCsv(
        string path,
        IEnumerable<AllocationProfileStageDocument> rows)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "mode,stage,parent_stage,level,is_derived,invocation_count," +
            "allocated_bytes,bytes_per_trial,percent_of_trial_total," +
            "elapsed_ticks,elapsed_milliseconds,milliseconds_per_trial");
        foreach (AllocationProfileStageDocument row in rows)
        {
            builder.Append(row.Mode);
            builder.Append(',');
            builder.Append(row.Stage);
            builder.Append(',');
            builder.Append(row.ParentStage ?? string.Empty);
            builder.Append(',');
            builder.Append(row.Level);
            builder.Append(',');
            builder.Append(row.IsDerived ? "true" : "false");
            builder.Append(',');
            builder.Append(row.InvocationCount.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.AllocatedBytes.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.BytesPerTrial.ToString("R", CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.PercentOfTrialTotal.ToString("R", CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.ElapsedTicks.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.ElapsedMilliseconds.ToString("R", CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.AppendLine(row.MillisecondsPerTrial.ToString(
                "R",
                CultureInfo.InvariantCulture));
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteTrialCsv(
        string path,
        IEnumerable<TrialSample> samples)
    {
        var builder = new StringBuilder();
        builder.Append(
            "mode,variant_id,profile_id,missile_tl,target_propulsion_tl," +
            "target_movement_policy,datalink_condition,trial_index,had_error," +
            "final_status,missile_actions,turns_elapsed,distance_traveled," +
            "global_allocated_bytes");
        foreach (ScenarioAllocationStage stage in AllStages)
        {
            builder.Append(',');
            builder.Append(stage);
            builder.Append("_bytes");
        }
        builder.AppendLine();

        foreach (TrialSample sample in samples)
        {
            AppendCsv(builder, sample.Mode.ToString());
            AppendCsv(builder, sample.VariantId);
            AppendCsv(builder, sample.ProfileId);
            AppendCsv(builder, sample.MissileTechnologyLevel.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, sample.TargetPropulsionTechnologyLevel.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, sample.TargetMovementPolicy);
            AppendCsv(builder, sample.DatalinkCondition);
            AppendCsv(builder, sample.TrialIndex.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, sample.HadError ? "true" : "false");
            AppendCsv(builder, sample.FinalStatus);
            AppendCsv(builder, sample.MissileActions.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, sample.TurnsElapsed.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, sample.DistanceTraveled.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, sample.GlobalAllocatedBytes.ToString(
                CultureInfo.InvariantCulture));
            foreach (ScenarioAllocationStage stage in AllStages)
            {
                AppendCsv(builder, sample.StageAllocatedBytes[(int)stage].ToString(
                    CultureInfo.InvariantCulture));
            }
            builder.AppendLine();
        }

        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void AppendCsv(StringBuilder builder, string value)
    {
        if (builder.Length > 0 && builder[^1] != '\n')
        {
            builder.Append(',');
        }
        bool quote = value.IndexOfAny(new[] { ',', '"', '\r', '\n' }) >= 0;
        if (!quote)
        {
            builder.Append(value);
            return;
        }
        builder.Append('"');
        builder.Append(value.Replace("\"", "\"\"", StringComparison.Ordinal));
        builder.Append('"');
    }

    private static void WriteParityFailures(
        string path,
        IReadOnlyCollection<string> parityFailures)
    {
        if (parityFailures.Count == 0)
        {
            File.Delete(path);
            return;
        }
        File.WriteAllLines(path, parityFailures);
    }

    private static void WriteTextReport(
        string path,
        AllocationProfileSummaryDocument summary)
    {
        var builder = new StringBuilder();
        builder.AppendLine("Checkpoint 22c allocation attribution report");
        builder.AppendLine($"Study: {summary.StudyId}");
        builder.AppendLine($"Variants: {summary.VariantCount}");
        builder.AppendLine(
            $"Measured trials per mode: {summary.MeasuredTrialsPerMode}");
        builder.AppendLine($"Parity failures: {summary.ParityFailureCount}");
        builder.AppendLine($"Passed: {summary.Passed}");
        foreach (AllocationProfileModeDocument mode in summary.Modes)
        {
            builder.AppendLine();
            builder.AppendLine(mode.Mode);
            builder.AppendLine(
                $"  Global bytes/trial: {mode.GlobalBytesPerTrial:N0}");
            builder.AppendLine(
                $"  Profiled thread bytes/trial: " +
                $"{mode.ProfiledThreadBytesPerTrial:N0}");
            builder.AppendLine(
                $"  Top-level attribution coverage: " +
                $"{mode.TopLevelAttributionCoverage:P2}");
            builder.AppendLine($"  Errors: {mode.ErrorCount}");
            builder.AppendLine("  Top-level stages:");
            foreach (AllocationProfileStageDocument stage in mode.Stages
                         .Where(item => item.Level == "TopLevel")
                         .OrderByDescending(item => item.AllocatedBytes))
            {
                builder.AppendLine(
                    $"    {stage.Stage}: {stage.BytesPerTrial:N0} bytes/trial " +
                    $"({stage.PercentOfTrialTotal:P2})");
            }
            builder.AppendLine("  Detail stages:");
            foreach (AllocationProfileStageDocument stage in mode.Stages
                         .Where(item => item.Level == "Detail")
                         .OrderByDescending(item => item.AllocatedBytes))
            {
                builder.AppendLine(
                    $"    {stage.Stage}: {stage.BytesPerTrial:N0} bytes/trial " +
                    $"({stage.PercentOfTrialTotal:P2})");
            }
            builder.AppendLine("  Residual stages:");
            foreach (AllocationProfileStageDocument stage in mode.Stages
                         .Where(item => item.Level == "Residual")
                         .OrderByDescending(item => item.AllocatedBytes))
            {
                builder.AppendLine(
                    $"    {stage.Stage}: {stage.BytesPerTrial:N0} bytes/trial " +
                    $"({stage.PercentOfTrialTotal:P2})");
            }
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void PrintModeSummary(AllocationProfileModeDocument mode)
    {
        Console.WriteLine(
            $"Allocation profile {mode.Mode}: {mode.TrialCount} trials; " +
            $"{mode.ErrorCount} errors; {mode.GlobalBytesPerTrial:N0} global " +
            $"bytes/trial; {mode.ProfiledThreadBytesPerTrial:N0} attributed " +
            $"bytes/trial; {mode.TopLevelAttributionCoverage:P1} top-level coverage.");
        foreach (AllocationProfileStageDocument stage in mode.Stages
                     .Where(item => item.Level == "TopLevel")
                     .OrderByDescending(item => item.AllocatedBytes)
                     .Take(4))
        {
            Console.WriteLine(
                $"       {stage.Stage}: {stage.BytesPerTrial:N0} bytes/trial " +
                $"({stage.PercentOfTrialTotal:P1}).");
        }
        AllocationProfileStageDocument mapCreation = mode.Stages.Single(item =>
            item.Stage == ScenarioAllocationStage.InitializationMapCreation.ToString() &&
            !item.IsDerived);
        Console.WriteLine(
            $"       InitializationMapCreation: {mapCreation.BytesPerTrial:N0} " +
            $"bytes/trial ({mapCreation.PercentOfTrialTotal:P1}).");
    }
}
