using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public sealed class ProbabilityMetricSummary
{
    public string Key { get; init; } = string.Empty;
    public int Count { get; init; }
    public int TrialCount { get; init; }
    public double Proportion { get; init; }
    public double Confidence95Low { get; init; }
    public double Confidence95High { get; init; }
}

public sealed class MonteCarloResultsDocument
{
    public int SchemaVersion { get; init; } = 1;
    public string RunKey { get; init; } = string.Empty;
    public string ScenarioId { get; init; } = string.Empty;
    public string VariantId { get; init; } = string.Empty;
    public ulong MasterSeed { get; init; }
    public int TrialCount { get; init; }
    public string ScenarioSha256 { get; init; } = string.Empty;
    public string RunnerAssemblySha256 { get; init; } = string.Empty;
    public string CoreAssemblySha256 { get; init; } = string.Empty;
    public int ErrorCount { get; init; }
    public double AverageDistanceTraveled { get; init; }
    public double AverageTotalFuelSpent { get; init; }
    public double AverageStationarySearchFuelSpent { get; init; }
    public double AverageTurnsElapsed { get; init; }
    public double AverageMissileActions { get; init; }
    public double AverageReplanCount { get; init; }
    public IReadOnlyList<ProbabilityMetricSummary> Metrics { get; init; } =
        Array.Empty<ProbabilityMetricSummary>();
}

public static class MonteCarloStatistics
{
    private const double Z95 = 1.959963984540054;

    public static MonteCarloResultsDocument Aggregate(
        IReadOnlyList<MonteCarloTrialResult> trials,
        string runKey,
        string scenarioId,
        string variantId,
        ulong masterSeed,
        string scenarioSha256,
        string runnerAssemblySha256,
        string coreAssemblySha256)
    {
        ArgumentNullException.ThrowIfNull(trials);
        if (trials.Count == 0)
        {
            throw new InvalidOperationException(
                "At least one Monte Carlo trial is required for aggregation.");
        }

        Dictionary<string, int> counts = CreateZeroInitializedCounts();
        long distanceSum = 0;
        long fuelSum = 0;
        long searchFuelSum = 0;
        long turnsSum = 0;
        long missileActionsSum = 0;
        long replanCountSum = 0;
        int errorCount = 0;

        foreach (MonteCarloTrialResult trial in trials.OrderBy(item => item.TrialIndex))
        {
            if (trial.Error is not null)
            {
                Increment(counts, "trial.error");
                errorCount++;
                continue;
            }

            Increment(counts, $"status.{trial.FinalStatus}");
            Increment(counts, $"outcome.{trial.FinalOutcome}");
            if (trial.InterceptionStage is not null)
            {
                Increment(counts, $"stage.{trial.InterceptionStage}Intercepted");
            }
            if (trial.TerminalEntryAttempted)
            {
                Increment(counts, "process.terminalEntryAttempted");
            }
            if (trial.PreTerminalAttackAttempted)
            {
                Increment(counts, "process.preTerminalAttackAttempted");
            }
            if (trial.AcquisitionAttempted)
            {
                Increment(counts, "process.acquisitionAttempted");
            }
            if (trial.AcquisitionSucceeded)
            {
                Increment(counts, "process.acquisitionSucceeded");
            }
            if (trial.AttackResolved)
            {
                Increment(counts, "process.attackResolved");
            }
            if (trial.FinalOutcome is nameof(MissileTerminalOutcome.Hit) or
                nameof(MissileTerminalOutcome.CriticalHit))
            {
                Increment(counts, "effect.effectiveHit");
            }
            if (trial.FinalStatus == nameof(GuidedMissileStatus.Intercepted))
            {
                Increment(counts, "effect.intercepted");
            }
            if (trial.SearchActivated)
            {
                Increment(counts, "process.searchActivated");
            }
            if (trial.TerminalOpportunityReached)
            {
                Increment(counts, "flight.terminalOpportunityReached");
            }
            if (trial.DatalinkBlockedObserved)
            {
                Increment(counts, "process.datalinkBlockedObserved");
            }
            if (trial.RetainedReportExpiredObserved)
            {
                Increment(counts, "process.retainedReportExpired");
            }
            if (trial.UsedFreshDatalinkGuidance)
            {
                Increment(counts, "process.freshDatalinkGuidanceUsed");
            }
            if (trial.UsedRetainedDatalinkGuidance)
            {
                Increment(counts, "process.retainedDatalinkGuidanceUsed");
            }
            if (trial.UsedLocalSensorGuidance)
            {
                Increment(counts, "process.localSensorGuidanceUsed");
            }
            if (trial.ActiveSensorUsed)
            {
                Increment(counts, "process.activeSensorUsed");
            }
            if (trial.FinalStatus == nameof(GuidedMissileStatus.RangeExhausted))
            {
                Increment(counts, "effect.rangeExhausted");
            }
            if (!IsTerminalStatus(trial.FinalStatus))
            {
                Increment(counts, "effect.unresolvedAtHorizon");
            }

            distanceSum += trial.DistanceTraveled;
            fuelSum += trial.TotalFuelSpent;
            searchFuelSum += trial.StationarySearchFuelSpent;
            turnsSum += trial.TurnsElapsed;
            missileActionsSum += trial.MissileActions;
            replanCountSum += trial.ReplanCount;
        }

        ProbabilityMetricSummary[] metrics = counts
            .OrderBy(item => item.Key, StringComparer.Ordinal)
            .Select(item => CreateMetric(item.Key, item.Value, trials.Count))
            .ToArray();

        return new MonteCarloResultsDocument
        {
            RunKey = runKey,
            ScenarioId = scenarioId,
            VariantId = variantId,
            MasterSeed = masterSeed,
            TrialCount = trials.Count,
            ScenarioSha256 = scenarioSha256,
            RunnerAssemblySha256 = runnerAssemblySha256,
            CoreAssemblySha256 = coreAssemblySha256,
            ErrorCount = errorCount,
            AverageDistanceTraveled = (double)distanceSum / trials.Count,
            AverageTotalFuelSpent = (double)fuelSum / trials.Count,
            AverageStationarySearchFuelSpent = (double)searchFuelSum / trials.Count,
            AverageTurnsElapsed = (double)turnsSum / trials.Count,
            AverageMissileActions = (double)missileActionsSum / trials.Count,
            AverageReplanCount = (double)replanCountSum / trials.Count,
            Metrics = Array.AsReadOnly(metrics),
        };
    }

    public static ProbabilityMetricSummary CreateMetric(
        string key,
        int count,
        int trialCount)
    {
        if (trialCount <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(trialCount));
        }
        if (count < 0 || count > trialCount)
        {
            throw new ArgumentOutOfRangeException(nameof(count));
        }

        double proportion = (double)count / trialCount;
        double zSquared = Z95 * Z95;
        double denominator = 1.0 + (zSquared / trialCount);
        double center = (proportion + (zSquared / (2.0 * trialCount))) / denominator;
        double margin = Z95 * Math.Sqrt(
            (proportion * (1.0 - proportion) / trialCount) +
            (zSquared / (4.0 * trialCount * trialCount))) / denominator;

        return new ProbabilityMetricSummary
        {
            Key = key,
            Count = count,
            TrialCount = trialCount,
            Proportion = proportion,
            Confidence95Low = Math.Max(0.0, center - margin),
            Confidence95High = Math.Min(1.0, center + margin),
        };
    }

    private static Dictionary<string, int> CreateZeroInitializedCounts()
    {
        var counts = new Dictionary<string, int>(StringComparer.Ordinal)
        {
            ["trial.error"] = 0,
            ["process.terminalEntryAttempted"] = 0,
            ["process.preTerminalAttackAttempted"] = 0,
            ["process.acquisitionAttempted"] = 0,
            ["process.acquisitionSucceeded"] = 0,
            ["process.attackResolved"] = 0,
            ["process.searchActivated"] = 0,
            ["effect.effectiveHit"] = 0,
            ["effect.intercepted"] = 0,
            ["flight.terminalOpportunityReached"] = 0,
            ["process.datalinkBlockedObserved"] = 0,
            ["process.retainedReportExpired"] = 0,
            ["process.freshDatalinkGuidanceUsed"] = 0,
            ["process.retainedDatalinkGuidanceUsed"] = 0,
            ["process.localSensorGuidanceUsed"] = 0,
            ["process.activeSensorUsed"] = 0,
            ["effect.rangeExhausted"] = 0,
            ["effect.unresolvedAtHorizon"] = 0,
        };

        foreach (string status in Enum.GetNames<GuidedMissileStatus>())
        {
            counts[$"status.{status}"] = 0;
        }
        foreach (string outcome in Enum.GetNames<MissileTerminalOutcome>())
        {
            counts[$"outcome.{outcome}"] = 0;
        }
        foreach (string opportunity in Enum.GetNames<MissileInterceptionOpportunity>())
        {
            counts[$"stage.{opportunity}Intercepted"] = 0;
        }

        return counts;
    }

    private static bool IsTerminalStatus(string status) =>
        status is nameof(GuidedMissileStatus.Expended) or
            nameof(GuidedMissileStatus.Dud) or
            nameof(GuidedMissileStatus.RangeExhausted) or
            nameof(GuidedMissileStatus.Intercepted) or
            nameof(GuidedMissileStatus.SelfDestructed) or
            nameof(GuidedMissileStatus.Destroyed);

    private static void Increment(IDictionary<string, int> counts, string key)
    {
        counts[key] = counts.TryGetValue(key, out int current)
            ? current + 1
            : 1;
    }
}
