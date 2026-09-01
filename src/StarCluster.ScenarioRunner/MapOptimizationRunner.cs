using System.Globalization;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Maps;

namespace StarCluster.ScenarioRunner;

public sealed class MapAllocationSweepDocument
{
    public int Radius { get; init; }
    public long CellCount { get; init; }
    public int MeasurementCount { get; init; }
    public long MinimumAllocatedBytes { get; init; }
    public long MaximumAllocatedBytes { get; init; }
    public double AverageAllocatedBytes { get; init; }
    public double AverageBytesPerCell { get; init; }
}

public sealed class MapVariantProofDocument
{
    public required string VariantId { get; init; }
    public required string ProfileId { get; init; }
    public int MissileTechnologyLevel { get; init; }
    public int TargetPropulsionTechnologyLevel { get; init; }
    public required string TargetMovementPolicy { get; init; }
    public required string DatalinkCondition { get; init; }
    public int OptimizedRadius { get; init; }
    public int RequiredExplicitCoordinateRadius { get; init; }
    public int SafetyMargin { get; init; }
    public long OptimizedCellCount { get; init; }
    public long ReferenceCellCount { get; init; }
    public double CellRetentionRatio { get; init; }
    public bool ExplicitCoordinatesFit { get; init; }
    public bool CanonicalParityMatched { get; init; }
    public string? Failure { get; init; }
}

public sealed class MapOptimizationSummaryDocument
{
    public int SchemaVersion { get; init; } = 1;
    public required string StudyId { get; init; }
    public int VariantCount { get; init; }
    public int ReferenceRadius { get; init; }
    public int MinimumOptimizedRadius { get; init; }
    public int MaximumOptimizedRadius { get; init; }
    public double AverageOptimizedRadius { get; init; }
    public long ReferenceCellCount { get; init; }
    public double AverageOptimizedCellCount { get; init; }
    public double AverageCellRetentionRatio { get; init; }
    public int ExplicitCoordinateFailureCount { get; init; }
    public int ParityTrialsPerVariant { get; init; }
    public int CanonicalParityFailureCount { get; init; }
    public bool AllocationSweepMonotonic { get; init; }
    public bool Passed { get; init; }
    public required IReadOnlyList<MapAllocationSweepDocument> AllocationSweep { get; init; }
    public required IReadOnlyList<MapVariantProofDocument> Variants { get; init; }
}

public sealed class MapOptimizationRunResult
{
    public required MapOptimizationSummaryDocument Summary { get; init; }
    public required string OutputDirectory { get; init; }

    public bool Passed => Summary.Passed;
}

public static class MapOptimizationRunner
{
    private static readonly int[] SweepRadii = { 5, 28, 64, 100, 192 };

    public static MapOptimizationRunResult Run(
        FullFlightCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        int parityTrialsPerVariant,
        int mapMeasurementsPerRadius,
        string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(study);
        ArgumentNullException.ThrowIfNull(catalog);
        if (parityTrialsPerVariant <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(parityTrialsPerVariant));
        }
        if (mapMeasurementsPerRadius <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(mapMeasurementsPerRadius));
        }

        FullFlightCalibrationModel.Validate(study, catalog);
        IReadOnlyList<PreparedFullFlightCalibrationVariant> optimized =
            FullFlightCalibrationModel.PrepareVariants(
                study,
                catalog,
                FullFlightMapSizingMode.OptimizedVariant);
        IReadOnlyList<PreparedFullFlightCalibrationVariant> reference =
            FullFlightCalibrationModel.PrepareVariants(
                study,
                catalog,
                FullFlightMapSizingMode.ReferenceRadius192);
        if (optimized.Count != reference.Count || optimized.Count != 288)
        {
            throw new InvalidOperationException(
                "The map proof requires matching 288-variant optimized and reference corpora.");
        }

        string fullOutputDirectory = Path.GetFullPath(outputDirectory);
        if (Directory.Exists(fullOutputDirectory))
        {
            Directory.Delete(fullOutputDirectory, recursive: true);
        }
        Directory.CreateDirectory(fullOutputDirectory);

        Console.WriteLine(
            $"Map optimization preflight: {optimized.Count} optimized variants and " +
            $"{reference.Count} radius-{FullFlightCalibrationModel.ReferenceMapRadius} " +
            "reference variants passed.");
        Console.WriteLine(
            $"Map parity policy: {parityTrialsPerVariant} compact trial(s) per " +
            "variant with identical common-random-number streams.");

        IReadOnlyList<MapAllocationSweepDocument> sweep = MeasureMapAllocationSweep(
            mapMeasurementsPerRadius);
        bool sweepMonotonic = IsStrictlyIncreasing(
            sweep.Select(item => item.AverageAllocatedBytes));

        ScenarioExecutionPlan[] optimizedPlans = optimized
            .Select(item => ScenarioExecutionPlan.Prepare(item.Scenario))
            .ToArray();
        ScenarioExecutionPlan[] referencePlans = reference
            .Select(item => ScenarioExecutionPlan.Prepare(item.Scenario))
            .ToArray();
        WarmUp(
            optimized[0],
            optimizedPlans[0],
            reference[0],
            referencePlans[0],
            study.MasterSeed);
        ForceFullCollection();

        var variantRows = new List<MapVariantProofDocument>(optimized.Count);
        var parityFailures = new List<string>();
        string seedNamespace = study.Id + "|checkpoint-22c-map-parity-v1";
        for (int index = 0; index < optimized.Count; index++)
        {
            PreparedFullFlightCalibrationVariant optimizedVariant = optimized[index];
            PreparedFullFlightCalibrationVariant referenceVariant = reference[index];
            if (!string.Equals(
                    optimizedVariant.Id,
                    referenceVariant.Id,
                    StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "Optimized and reference variant ordering diverged.");
            }

            ScenarioDocument optimizedScenario = optimizedVariant.Scenario;
            int requiredRadius =
                FullFlightCalibrationModel.CalculateRequiredExplicitCoordinateRadius(
                    optimizedScenario);
            int optimizedRadius = optimizedScenario.Map.Radius;
            bool coordinatesFit = checked(
                requiredRadius + FullFlightCalibrationModel.OptimizedMapSafetyMargin) <=
                optimizedRadius;
            string? failure = coordinatesFit
                ? null
                : $"explicit coordinate radius {requiredRadius} lacks the configured safety margin";
            bool parityMatched = true;
            for (int trialIndex = 0;
                 trialIndex < parityTrialsPerVariant;
                 trialIndex++)
            {
                MonteCarloTrialResult referenceResult = MonteCarloTrialResult.Execute(
                    referencePlans[index],
                    referenceVariant.Id,
                    trialIndex,
                    study.MasterSeed,
                    seedNamespace,
                    MonteCarloTrialExecutionMode.CompactMetrics);
                MonteCarloTrialResult optimizedResult = MonteCarloTrialResult.Execute(
                    optimizedPlans[index],
                    optimizedVariant.Id,
                    trialIndex,
                    study.MasterSeed,
                    seedNamespace,
                    MonteCarloTrialExecutionMode.CompactMetrics);
                string referenceJson = JsonSerializer.Serialize(
                    referenceResult,
                    ScenarioDocumentSerialization.CompactWriteOptions);
                string optimizedJson = JsonSerializer.Serialize(
                    optimizedResult,
                    ScenarioDocumentSerialization.CompactWriteOptions);
                if (!string.IsNullOrWhiteSpace(referenceResult.Error) ||
                    !string.IsNullOrWhiteSpace(optimizedResult.Error))
                {
                    parityMatched = false;
                    failure =
                        $"trial {trialIndex} execution error: reference=" +
                        $"{referenceResult.Error ?? "none"}; optimized=" +
                        $"{optimizedResult.Error ?? "none"}";
                    parityFailures.Add(
                        optimizedVariant.Id + "|" +
                        trialIndex.ToString(CultureInfo.InvariantCulture) +
                        "|execution-error");
                    break;
                }
                if (!string.Equals(
                        referenceJson,
                        optimizedJson,
                        StringComparison.Ordinal))
                {
                    parityMatched = false;
                    failure = $"trial {trialIndex} canonical result mismatch";
                    parityFailures.Add(
                        optimizedVariant.Id + "|" +
                        trialIndex.ToString(CultureInfo.InvariantCulture));
                    break;
                }
            }

            long optimizedCells = FullFlightCalibrationModel.CalculateHexCellCount(
                optimizedRadius);
            long referenceCells = FullFlightCalibrationModel.CalculateHexCellCount(
                FullFlightCalibrationModel.ReferenceMapRadius);
            variantRows.Add(new MapVariantProofDocument
            {
                VariantId = optimizedVariant.Id,
                ProfileId = optimizedVariant.Profile.Id,
                MissileTechnologyLevel =
                    optimizedVariant.MissileTechnology.TechnologyLevel,
                TargetPropulsionTechnologyLevel =
                    optimizedVariant.TargetPropulsionTechnology.TechnologyLevel,
                TargetMovementPolicy = optimizedVariant.TargetMovementPolicy,
                DatalinkCondition = optimizedVariant.DatalinkCondition,
                OptimizedRadius = optimizedRadius,
                RequiredExplicitCoordinateRadius = requiredRadius,
                SafetyMargin = optimizedRadius - requiredRadius,
                OptimizedCellCount = optimizedCells,
                ReferenceCellCount = referenceCells,
                CellRetentionRatio = optimizedCells / (double)referenceCells,
                ExplicitCoordinatesFit = coordinatesFit,
                CanonicalParityMatched = parityMatched,
                Failure = failure,
            });
        }

        int explicitCoordinateFailures = variantRows.Count(item =>
            !item.ExplicitCoordinatesFit);
        int parityFailureCount = variantRows.Count(item =>
            !item.CanonicalParityMatched);
        long referenceCellCount = FullFlightCalibrationModel.CalculateHexCellCount(
            FullFlightCalibrationModel.ReferenceMapRadius);
        double averageCellCount = variantRows.Average(item =>
            (double)item.OptimizedCellCount);
        double averageCellRetention = averageCellCount / referenceCellCount;
        bool passed =
            explicitCoordinateFailures == 0 &&
            parityFailureCount == 0 &&
            sweepMonotonic &&
            variantRows.All(item =>
                item.OptimizedRadius < FullFlightCalibrationModel.ReferenceMapRadius) &&
            averageCellRetention <= 0.05;
        var summary = new MapOptimizationSummaryDocument
        {
            StudyId = study.Id,
            VariantCount = variantRows.Count,
            ReferenceRadius = FullFlightCalibrationModel.ReferenceMapRadius,
            MinimumOptimizedRadius = variantRows.Min(item => item.OptimizedRadius),
            MaximumOptimizedRadius = variantRows.Max(item => item.OptimizedRadius),
            AverageOptimizedRadius = variantRows.Average(item =>
                (double)item.OptimizedRadius),
            ReferenceCellCount = referenceCellCount,
            AverageOptimizedCellCount = averageCellCount,
            AverageCellRetentionRatio = averageCellRetention,
            ExplicitCoordinateFailureCount = explicitCoordinateFailures,
            ParityTrialsPerVariant = parityTrialsPerVariant,
            CanonicalParityFailureCount = parityFailureCount,
            AllocationSweepMonotonic = sweepMonotonic,
            Passed = passed,
            AllocationSweep = sweep,
            Variants = variantRows.AsReadOnly(),
        };

        WriteJson(
            Path.Combine(fullOutputDirectory, "map-optimization-summary.json"),
            summary);
        WriteSweepCsv(
            Path.Combine(fullOutputDirectory, "map-allocation-sweep.csv"),
            sweep);
        WriteVariantCsv(
            Path.Combine(fullOutputDirectory, "map-radius-variants.csv"),
            variantRows);
        WriteFailures(
            Path.Combine(fullOutputDirectory, "map-parity-failures.txt"),
            parityFailures);
        WriteReport(
            Path.Combine(fullOutputDirectory, "map-optimization-report.txt"),
            summary,
            parityTrialsPerVariant);

        Console.WriteLine(
            $"Map allocation sweep: radius 5 {sweep[0].AverageAllocatedBytes:N0} " +
            $"bytes; radius 192 {sweep[^1].AverageAllocatedBytes:N0} bytes; " +
            $"strictly monotonic {sweepMonotonic}.");
        Console.WriteLine(
            $"Optimized map radii: {summary.MinimumOptimizedRadius} to " +
            $"{summary.MaximumOptimizedRadius}; average " +
            $"{summary.AverageOptimizedRadius:N2}; average cell retention " +
            $"{summary.AverageCellRetentionRatio:P1}.");
        Console.WriteLine(
            $"Map canonical parity: {summary.VariantCount - parityFailureCount} " +
            $"matched, {parityFailureCount} failed; explicit-coordinate failures " +
            $"{explicitCoordinateFailures}.");
        Console.WriteLine(
            $"Map optimization proof: {(passed ? "PASS" : "FAIL")}. Output: " +
            fullOutputDirectory);

        return new MapOptimizationRunResult
        {
            Summary = summary,
            OutputDirectory = fullOutputDirectory,
        };
    }

    private static IReadOnlyList<MapAllocationSweepDocument>
        MeasureMapAllocationSweep(int measurementCount)
    {
        var rows = new List<MapAllocationSweepDocument>(SweepRadii.Length);
        foreach (int radius in SweepRadii)
        {
            SystemMap warmup = SystemMap.Create(
                radius,
                MapObject.CreateStar("sweep-star", "Sweep Star"));
            GC.KeepAlive(warmup);
            ForceFullCollection();

            var samples = new long[measurementCount];
            for (int measurement = 0;
                 measurement < measurementCount;
                 measurement++)
            {
                long before = GC.GetAllocatedBytesForCurrentThread();
                SystemMap map = SystemMap.Create(
                    radius,
                    MapObject.CreateStar("sweep-star", "Sweep Star"));
                long after = GC.GetAllocatedBytesForCurrentThread();
                samples[measurement] = Math.Max(0, after - before);
                GC.KeepAlive(map);
            }
            long cellCount = FullFlightCalibrationModel.CalculateHexCellCount(radius);
            double average = samples.Average(value => (double)value);
            rows.Add(new MapAllocationSweepDocument
            {
                Radius = radius,
                CellCount = cellCount,
                MeasurementCount = measurementCount,
                MinimumAllocatedBytes = samples.Min(),
                MaximumAllocatedBytes = samples.Max(),
                AverageAllocatedBytes = average,
                AverageBytesPerCell = average / cellCount,
            });
            ForceFullCollection();
        }
        return rows.AsReadOnly();
    }

    private static void WarmUp(
        PreparedFullFlightCalibrationVariant optimizedVariant,
        ScenarioExecutionPlan optimizedPlan,
        PreparedFullFlightCalibrationVariant referenceVariant,
        ScenarioExecutionPlan referencePlan,
        ulong masterSeed)
    {
        const string seedNamespace = "checkpoint-22c-map-warmup";
        _ = MonteCarloTrialResult.Execute(
            optimizedPlan,
            optimizedVariant.Id,
            100000,
            masterSeed,
            seedNamespace,
            MonteCarloTrialExecutionMode.CompactMetrics);
        _ = MonteCarloTrialResult.Execute(
            referencePlan,
            referenceVariant.Id,
            100000,
            masterSeed,
            seedNamespace,
            MonteCarloTrialExecutionMode.CompactMetrics);
    }

    private static bool IsStrictlyIncreasing(IEnumerable<double> values)
    {
        double? previous = null;
        foreach (double value in values)
        {
            if (previous.HasValue && value <= previous.Value)
            {
                return false;
            }
            previous = value;
        }
        return true;
    }

    private static void ForceFullCollection()
    {
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();
    }

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

    private static void WriteSweepCsv(
        string path,
        IEnumerable<MapAllocationSweepDocument> rows)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "radius,cell_count,measurement_count,minimum_allocated_bytes," +
            "maximum_allocated_bytes,average_allocated_bytes,average_bytes_per_cell");
        foreach (MapAllocationSweepDocument row in rows)
        {
            builder.Append(row.Radius.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.CellCount.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.MeasurementCount.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.MinimumAllocatedBytes.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.MaximumAllocatedBytes.ToString(CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.Append(row.AverageAllocatedBytes.ToString(
                "R",
                CultureInfo.InvariantCulture));
            builder.Append(',');
            builder.AppendLine(row.AverageBytesPerCell.ToString(
                "R",
                CultureInfo.InvariantCulture));
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteVariantCsv(
        string path,
        IEnumerable<MapVariantProofDocument> rows)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "variant_id,profile_id,missile_tl,target_propulsion_tl," +
            "target_movement_policy,datalink_condition,optimized_radius," +
            "required_explicit_coordinate_radius,safety_margin," +
            "optimized_cell_count,reference_cell_count,cell_retention_ratio," +
            "explicit_coordinates_fit,canonical_parity_matched,failure");
        foreach (MapVariantProofDocument row in rows)
        {
            AppendCsv(builder, row.VariantId);
            AppendCsv(builder, row.ProfileId);
            AppendCsv(builder, row.MissileTechnologyLevel.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.TargetPropulsionTechnologyLevel.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.TargetMovementPolicy);
            AppendCsv(builder, row.DatalinkCondition);
            AppendCsv(builder, row.OptimizedRadius.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.RequiredExplicitCoordinateRadius.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.SafetyMargin.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.OptimizedCellCount.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.ReferenceCellCount.ToString(
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.CellRetentionRatio.ToString(
                "R",
                CultureInfo.InvariantCulture));
            AppendCsv(builder, row.ExplicitCoordinatesFit ? "true" : "false");
            AppendCsv(builder, row.CanonicalParityMatched ? "true" : "false");
            AppendCsv(builder, row.Failure ?? string.Empty);
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

    private static void WriteFailures(
        string path,
        IReadOnlyCollection<string> failures)
    {
        if (failures.Count == 0)
        {
            File.Delete(path);
            return;
        }
        File.WriteAllLines(path, failures);
    }

    private static void WriteReport(
        string path,
        MapOptimizationSummaryDocument summary,
        int parityTrialsPerVariant)
    {
        var builder = new StringBuilder();
        builder.AppendLine("Checkpoint 22c calibration-map optimization proof");
        builder.AppendLine($"Study: {summary.StudyId}");
        builder.AppendLine($"Variants: {summary.VariantCount}");
        builder.AppendLine($"Reference radius: {summary.ReferenceRadius}");
        builder.AppendLine(
            $"Optimized radius range: {summary.MinimumOptimizedRadius} to " +
            $"{summary.MaximumOptimizedRadius}");
        builder.AppendLine(
            $"Average optimized radius: {summary.AverageOptimizedRadius:N2}");
        builder.AppendLine(
            $"Average optimized cells: {summary.AverageOptimizedCellCount:N2}");
        builder.AppendLine(
            $"Average cell retention: {summary.AverageCellRetentionRatio:P2}");
        builder.AppendLine(
            $"Parity trials per variant: {parityTrialsPerVariant}");
        builder.AppendLine(
            $"Canonical parity failures: {summary.CanonicalParityFailureCount}");
        builder.AppendLine(
            $"Explicit-coordinate failures: {summary.ExplicitCoordinateFailureCount}");
        builder.AppendLine(
            $"Allocation sweep monotonic: {summary.AllocationSweepMonotonic}");
        builder.AppendLine($"Passed: {summary.Passed}");
        builder.AppendLine();
        builder.AppendLine("Allocation sweep:");
        foreach (MapAllocationSweepDocument row in summary.AllocationSweep)
        {
            builder.AppendLine(
                $"  radius {row.Radius}: {row.CellCount:N0} cells; " +
                $"{row.AverageAllocatedBytes:N0} bytes; " +
                $"{row.AverageBytesPerCell:N2} bytes/cell");
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }
}
