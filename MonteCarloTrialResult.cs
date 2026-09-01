using System.Globalization;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public enum MonteCarloTrialExecutionMode
{
    DiagnosticJournal,
    CompactMetrics,
}

public sealed class MonteCarloTrialResult
{
    public int TrialIndex { get; set; }

    [JsonIgnore]
    public ulong TrialSeedValue { get; set; }

    [JsonIgnore]
    public ulong InterceptionSeedValue { get; set; }

    [JsonIgnore]
    public ulong TerminalSeedValue { get; set; }

    public string TrialSeedHex
    {
        get => ToHex(TrialSeedValue);
        set => TrialSeedValue = ParseHex(value);
    }

    public string InterceptionSeedHex
    {
        get => ToHex(InterceptionSeedValue);
        set => InterceptionSeedValue = ParseHex(value);
    }

    public string TerminalSeedHex
    {
        get => ToHex(TerminalSeedValue);
        set => TerminalSeedValue = ParseHex(value);
    }
    public string? Error { get; set; }
    public string FinalStatus { get; set; } = string.Empty;
    public string FinalOutcome { get; set; } = string.Empty;
    public string? InterceptionStage { get; set; }
    public bool TerminalEntryAttempted { get; set; }
    public bool PreTerminalAttackAttempted { get; set; }
    public bool AcquisitionAttempted { get; set; }
    public bool AcquisitionSucceeded { get; set; }
    public bool AttackResolved { get; set; }
    public bool SearchActivated { get; set; }
    public bool TerminalOpportunityReached { get; set; }
    public bool MissileEnteredTargetHexOpportunity { get; set; }
    public bool TargetEnteredMissileHexOpportunity { get; set; }
    public bool ActionBeganColocatedOpportunity { get; set; }
    public bool StationarySearchRetryOpportunity { get; set; }
    public bool TerminalOpportunityInvariantPassed { get; set; }
    public bool OperationalTimeoutReached { get; set; }
    public bool UnexplainedUnresolved { get; set; }
    public string ResolutionClass { get; set; } = string.Empty;
    public bool DatalinkUpdateAttempted { get; set; }
    public bool DatalinkBlockedObserved { get; set; }
    public bool DatalinkLiveObserved { get; set; }
    public bool RetainedReportExpiredObserved { get; set; }
    public bool UsedFreshDatalinkGuidance { get; set; }
    public bool UsedRetainedDatalinkGuidance { get; set; }
    public bool UsedLocalSensorGuidance { get; set; }
    public bool ActiveSensorUsed { get; set; }
    public int MissileActions { get; set; }
    public int ReplanCount { get; set; }
    public int TurnsElapsed { get; set; }
    public int DistanceTraveled { get; set; }
    public int TotalFuelSpent { get; set; }
    public int StationarySearchFuelSpent { get; set; }
    public int? AcquisitionRoll { get; set; }
    public int? AttackRoll { get; set; }

    public static MonteCarloTrialResult Execute(
        ScenarioDocument document,
        string variantId,
        int trialIndex,
        ulong masterSeed,
        string? randomSeedNamespace = null,
        MonteCarloTrialExecutionMode executionMode =
            MonteCarloTrialExecutionMode.DiagnosticJournal,
        ScenarioAllocationProfile? allocationProfile = null) =>
        Execute(
            ScenarioExecutionPlan.Prepare(document),
            variantId,
            trialIndex,
            masterSeed,
            randomSeedNamespace,
            executionMode,
            allocationProfile);

    public static MonteCarloTrialResult Execute(
        ScenarioExecutionPlan executionPlan,
        string variantId,
        int trialIndex,
        ulong masterSeed,
        string? randomSeedNamespace = null,
        MonteCarloTrialExecutionMode executionMode =
            MonteCarloTrialExecutionMode.CompactMetrics,
        ScenarioAllocationProfile? allocationProfile = null)
    {
        ArgumentNullException.ThrowIfNull(executionPlan);
        ScenarioAllocationToken totalToken = allocationProfile?.Start() ?? default;
        ulong trialSeed = 0UL;
        ulong interceptionSeed = 0UL;
        ulong terminalSeed = 0UL;
        try
        {
            ScenarioDocument document = executionPlan.Document;
            ScenarioAllocationToken seedToken = allocationProfile?.Start() ?? default;
            try
            {
                string seedNamespace = string.IsNullOrWhiteSpace(randomSeedNamespace)
                    ? variantId
                    : randomSeedNamespace;
                trialSeed = TrialSeedDeriver.Derive(
                    masterSeed,
                    seedNamespace,
                    trialIndex,
                    streamId: 0UL);
                interceptionSeed = TrialSeedDeriver.Derive(
                    masterSeed,
                    seedNamespace,
                    trialIndex,
                    streamId: 1UL);
                terminalSeed = TrialSeedDeriver.Derive(
                    masterSeed,
                    seedNamespace,
                    trialIndex,
                    streamId: 2UL);
            }
            finally
            {
                allocationProfile?.Stop(
                    ScenarioAllocationStage.SeedDerivation,
                    seedToken);
            }

            try
            {
                ScenarioExecutionOptions options;
                ScenarioAllocationToken setupToken =
                    allocationProfile?.Start() ?? default;
                try
                {
                    bool recordDiagnostics =
                        executionMode ==
                            MonteCarloTrialExecutionMode.DiagnosticJournal;
                    options = new ScenarioExecutionOptions
                    {
                        EvaluateAssertions = false,
                        RecordCompletionEvent = false,
                        RecordDiagnostics = recordDiagnostics,
                        CaptureExecutionMetrics = true,
                        AllocationProfile = allocationProfile,
                        InterceptionResolver =
                            new ProbabilityMissileInterceptionResolver(
                                executionPlan.InterceptionProfile,
                                interceptionSeed),
                        TerminalRandomSource =
                            new DeterministicMissileTerminalRandomSource(
                                terminalSeed),
                    };
                }
                finally
                {
                    allocationProfile?.Stop(
                        ScenarioAllocationStage.TrialSetup,
                        setupToken);
                }

                ScenarioExecutor executor;
                ScenarioAllocationToken constructionToken =
                    allocationProfile?.Start() ?? default;
                try
                {
                    executor = new ScenarioExecutor(executionPlan, options);
                }
                finally
                {
                    allocationProfile?.Stop(
                        ScenarioAllocationStage.ExecutorConstruction,
                        constructionToken);
                }

                ScenarioRunResult result = executor.Execute();
                ScenarioAllocationToken projectionToken =
                    allocationProfile?.Start() ?? default;
                try
                {
                    ScenarioExecutionMetrics metrics = result.ExecutionMetrics ??
                        throw new InvalidOperationException(
                            "Monte Carlo execution metrics were not captured.");
                    GuidedMissileSalvo missile =
                        result.Runtime.MissileEngagement.Salvos
                            .OrderBy(item => item.Id, StringComparer.Ordinal)
                            .FirstOrDefault() ??
                        throw new InvalidOperationException(
                            "Monte Carlo scenarios require at least one Missile Flight.");

                    MissileInterceptionAttemptResult? intercepted =
                        result.InterceptionAttempts
                            .FirstOrDefault(attempt => attempt.Intercepted);
                    MissileTerminalResolution? terminal =
                        missile.LastTerminalResolution;
                    bool terminalOpportunityReached =
                        result.TerminalOpportunities.Count > 0;
                    bool terminalMechanicsOccurred =
                        result.InterceptionAttempts.Any(attempt =>
                            attempt.Opportunity is
                                MissileInterceptionOpportunity.TerminalEntry or
                                MissileInterceptionOpportunity.PreTerminalAttack) ||
                        terminal?.TargetCoLocated == true ||
                        metrics.AcquisitionAttempted ||
                        terminal?.AttackWasResolved == true;
                    bool terminalOpportunityInvariantPassed =
                        (!terminalMechanicsOccurred || terminalOpportunityReached) &&
                        metrics.TerminalOpportunityCount ==
                            result.TerminalOpportunities.Count &&
                        metrics.DiagnosticTerminalOpportunityCount ==
                            result.TerminalOpportunities.Count;
                    if (!terminalOpportunityInvariantPassed)
                    {
                        throw new InvalidOperationException(
                            "Terminal mechanics occurred without a matching authoritative and compact terminal opportunity observation.");
                    }

                    bool terminalStatus = IsTerminalStatus(missile.Status);
                    bool operationalTimeoutReached =
                        !terminalStatus &&
                        document.OperationalTurnLimit is int operationalTurnLimit &&
                        metrics.MissileActions >= operationalTurnLimit;
                    bool unexplainedUnresolved =
                        !terminalStatus &&
                        !operationalTimeoutReached;
                    string resolutionClass = terminalStatus
                        ? "Terminal"
                        : operationalTimeoutReached
                            ? "OperationalTimeout"
                            : "UnexplainedUnresolved";

                    return new MonteCarloTrialResult
                    {
                        TrialIndex = trialIndex,
                        TrialSeedValue = trialSeed,
                        InterceptionSeedValue = interceptionSeed,
                        TerminalSeedValue = terminalSeed,
                        FinalStatus = StatusName(missile.Status),
                        FinalOutcome = OutcomeName(
                            terminal?.Outcome ?? MissileTerminalOutcome.None),
                        InterceptionStage = intercepted is null
                            ? null
                            : OpportunityName(intercepted.Opportunity),
                        TerminalEntryAttempted =
                            result.InterceptionAttempts.Any(attempt =>
                                attempt.Opportunity ==
                                    MissileInterceptionOpportunity.TerminalEntry),
                        PreTerminalAttackAttempted =
                            result.InterceptionAttempts.Any(attempt =>
                                attempt.Opportunity ==
                                    MissileInterceptionOpportunity.PreTerminalAttack),
                        AcquisitionAttempted = metrics.AcquisitionAttempted,
                        AcquisitionSucceeded = terminal?.HasFirmSolution ?? false,
                        AttackResolved = terminal?.AttackWasResolved ?? false,
                        SearchActivated = metrics.SearchActivated,
                        TerminalOpportunityReached = terminalOpportunityReached,
                        MissileEnteredTargetHexOpportunity =
                            metrics.MissileEnteredTargetHexOpportunity,
                        TargetEnteredMissileHexOpportunity =
                            metrics.TargetEnteredMissileHexOpportunity,
                        ActionBeganColocatedOpportunity =
                            metrics.ActionBeganColocatedOpportunity,
                        StationarySearchRetryOpportunity =
                            metrics.StationarySearchRetryOpportunity,
                        TerminalOpportunityInvariantPassed =
                            terminalOpportunityInvariantPassed,
                        OperationalTimeoutReached = operationalTimeoutReached,
                        UnexplainedUnresolved = unexplainedUnresolved,
                        ResolutionClass = resolutionClass,
                        DatalinkUpdateAttempted = metrics.DatalinkUpdateAttempted,
                        DatalinkBlockedObserved = metrics.DatalinkBlockedObserved,
                        DatalinkLiveObserved = metrics.DatalinkLiveObserved,
                        RetainedReportExpiredObserved =
                            metrics.RetainedReportExpiredObserved,
                        UsedFreshDatalinkGuidance =
                            metrics.UsedFreshDatalinkGuidance,
                        UsedRetainedDatalinkGuidance =
                            metrics.UsedRetainedDatalinkGuidance,
                        UsedLocalSensorGuidance =
                            metrics.UsedLocalSensorGuidance,
                        ActiveSensorUsed = metrics.ActiveSensorUsed,
                        MissileActions = metrics.MissileActions,
                        ReplanCount = metrics.ReplanCount,
                        TurnsElapsed = Math.Max(
                            1,
                            metrics.MaximumObservedTurnNumber),
                        DistanceTraveled = missile.DistanceTraveled,
                        TotalFuelSpent = missile.TotalFuelSpent,
                        StationarySearchFuelSpent =
                            missile.StationarySearchFuelSpent,
                        AcquisitionRoll = terminal?.AcquisitionRoll,
                        AttackRoll = terminal?.AttackRoll,
                    };
                }
                finally
                {
                    allocationProfile?.Stop(
                        ScenarioAllocationStage.ResultProjection,
                        projectionToken);
                }
            }
            catch (Exception exception)
            {
                ScenarioAllocationToken projectionToken =
                    allocationProfile?.Start() ?? default;
                try
                {
                    return new MonteCarloTrialResult
                    {
                        TrialIndex = trialIndex,
                        TrialSeedValue = trialSeed,
                        InterceptionSeedValue = interceptionSeed,
                        TerminalSeedValue = terminalSeed,
                        Error = exception.ToString(),
                        FinalStatus = "Error",
                        FinalOutcome = "Error",
                    };
                }
                finally
                {
                    allocationProfile?.Stop(
                        ScenarioAllocationStage.ResultProjection,
                        projectionToken);
                }
            }
        }
        finally
        {
            allocationProfile?.Stop(
                ScenarioAllocationStage.TrialTotal,
                totalToken);
        }
    }

    private static bool IsTerminalStatus(GuidedMissileStatus status) =>
        status is GuidedMissileStatus.Expended or
            GuidedMissileStatus.Dud or
            GuidedMissileStatus.RangeExhausted or
            GuidedMissileStatus.Intercepted or
            GuidedMissileStatus.SelfDestructed or
            GuidedMissileStatus.Destroyed;

    private static string StatusName(GuidedMissileStatus status) => status switch
    {
        GuidedMissileStatus.InFlight => nameof(GuidedMissileStatus.InFlight),
        GuidedMissileStatus.WaitingForRoute => nameof(GuidedMissileStatus.WaitingForRoute),
        GuidedMissileStatus.WaitingForTrack => nameof(GuidedMissileStatus.WaitingForTrack),
        GuidedMissileStatus.Searching => nameof(GuidedMissileStatus.Searching),
        GuidedMissileStatus.Expended => nameof(GuidedMissileStatus.Expended),
        GuidedMissileStatus.Dud => nameof(GuidedMissileStatus.Dud),
        GuidedMissileStatus.RangeExhausted => nameof(GuidedMissileStatus.RangeExhausted),
        GuidedMissileStatus.Intercepted => nameof(GuidedMissileStatus.Intercepted),
        GuidedMissileStatus.SelfDestructed => nameof(GuidedMissileStatus.SelfDestructed),
        GuidedMissileStatus.Destroyed => nameof(GuidedMissileStatus.Destroyed),
        _ => throw new ArgumentOutOfRangeException(nameof(status), status, null),
    };

    private static string OutcomeName(MissileTerminalOutcome outcome) => outcome switch
    {
        MissileTerminalOutcome.None => nameof(MissileTerminalOutcome.None),
        MissileTerminalOutcome.AcquisitionFailed => nameof(MissileTerminalOutcome.AcquisitionFailed),
        MissileTerminalOutcome.Intercepted => nameof(MissileTerminalOutcome.Intercepted),
        MissileTerminalOutcome.Dud => nameof(MissileTerminalOutcome.Dud),
        MissileTerminalOutcome.Miss => nameof(MissileTerminalOutcome.Miss),
        MissileTerminalOutcome.Hit => nameof(MissileTerminalOutcome.Hit),
        MissileTerminalOutcome.CriticalHit => nameof(MissileTerminalOutcome.CriticalHit),
        MissileTerminalOutcome.SelfDestructed => nameof(MissileTerminalOutcome.SelfDestructed),
        _ => throw new ArgumentOutOfRangeException(nameof(outcome), outcome, null),
    };

    private static string OpportunityName(
        MissileInterceptionOpportunity opportunity) => opportunity switch
        {
            MissileInterceptionOpportunity.Transit =>
                nameof(MissileInterceptionOpportunity.Transit),
            MissileInterceptionOpportunity.Stationary =>
                nameof(MissileInterceptionOpportunity.Stationary),
            MissileInterceptionOpportunity.TerminalEntry =>
                nameof(MissileInterceptionOpportunity.TerminalEntry),
            MissileInterceptionOpportunity.PreTerminalAttack =>
                nameof(MissileInterceptionOpportunity.PreTerminalAttack),
            _ => throw new ArgumentOutOfRangeException(
                nameof(opportunity),
                opportunity,
                null),
        };

    private static string ToHex(ulong value) => $"0x{value:x16}";

    private static ulong ParseHex(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return 0UL;
        }
        string digits = value.StartsWith("0x", StringComparison.OrdinalIgnoreCase)
            ? value[2..]
            : value;
        if (!ulong.TryParse(
                digits,
                NumberStyles.AllowHexSpecifier,
                CultureInfo.InvariantCulture,
                out ulong parsed))
        {
            throw new InvalidOperationException(
                $"Invalid 64-bit hexadecimal seed '{value}'.");
        }
        return parsed;
    }
}
