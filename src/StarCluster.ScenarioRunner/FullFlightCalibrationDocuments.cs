namespace StarCluster.ScenarioRunner;

public sealed class FullFlightCalibrationStudyDocument
{
    public int SchemaVersion { get; set; } = 2;
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string ProfileCatalog { get; set; } = string.Empty;
    public int TrialsPerVariant { get; set; } = 1_000;
    public ulong MasterSeed { get; set; } = 210100UL;
    public int MinimumSafetyTurns { get; set; } = 8;
    public int SafetyTurnBuffer { get; set; } = 4;
    public int FixedPdsTechnologyLevel { get; set; } = 4;
    public int FixedTargetEcmTechnologyLevel { get; set; } = 4;
    public double MinimumPracticalMarginalDelta { get; set; } = 0.01;
    public double MarginalFamilywiseAlpha { get; set; } = 0.05;
    public List<string> MissileProfiles { get; set; } = new();
    public List<int> MissileTechnologyLevels { get; set; } = new();
    public List<int> TargetPropulsionTechnologyLevels { get; set; } = new();
    public List<string> TargetMovementPolicies { get; set; } = new();
    public List<string> DatalinkConditions { get; set; } = new();
}

public sealed class FullFlightCalibrationVariantResult
{
    public string Id { get; init; } = string.Empty;
    public string ProfileId { get; init; } = string.Empty;
    public string ProfileName { get; init; } = string.Empty;
    public int MissileTechnologyLevel { get; init; }
    public int TargetPropulsionTechnologyLevel { get; init; }
    public int MissileSpeedHexesPerTurn { get; init; }
    public int TargetSpeedHexesPerTurn { get; init; }
    public int MissileMaximumRangeHexes { get; init; }
    public int SafetyTurnCap { get; init; }
    public int FixedPdsTechnologyLevel { get; init; }
    public int FixedTargetEcmTechnologyLevel { get; init; }
    public int PdsInterceptionChancePercent { get; init; }
    public string TargetMovementPolicy { get; init; } = string.Empty;
    public string DatalinkCondition { get; init; } = string.Empty;
    public string RelativeSpeedClass { get; init; } = string.Empty;
    public int Trials { get; init; }
    public double TerminalOpportunityProbability { get; init; }
    public double TerminalOpportunityConfidence95Low { get; init; }
    public double TerminalOpportunityConfidence95High { get; init; }
    public double MissileEnteredTargetHexOpportunityProbability { get; init; }
    public double TargetEnteredMissileHexOpportunityProbability { get; init; }
    public double ActionBeganColocatedOpportunityProbability { get; init; }
    public double StationarySearchRetryOpportunityProbability { get; init; }
    public double TerminalOpportunityInvariantFailureProbability { get; init; }
    public double EffectiveHitPerLaunch { get; init; }
    public double EffectiveHitConfidence95Low { get; init; }
    public double EffectiveHitConfidence95High { get; init; }
    public double InterceptionProbability { get; init; }
    public double RangeExhaustionProbability { get; init; }
    public double SelfDestructedProbability { get; init; }
    public double TerminalMissProbability { get; init; }
    public double DudProbability { get; init; }
    public double SearchProbability { get; init; }
    public double OperationalTimeoutProbability { get; init; }
    public double UnexplainedUnresolvedProbability { get; init; }
    public double UnresolvedAtHorizonProbability { get; init; }
    public double DatalinkUpdateAttemptedProbability { get; init; }
    public double DatalinkBlockedObservedProbability { get; init; }
    public double DatalinkLiveObservedProbability { get; init; }
    public double DatalinkSemanticContractFailureProbability { get; init; }
    public double RetainedReportExpiredProbability { get; init; }
    public double FreshDatalinkGuidanceProbability { get; init; }
    public double RetainedDatalinkGuidanceProbability { get; init; }
    public double LocalSensorGuidanceProbability { get; init; }
    public double ActiveSensorUseProbability { get; init; }
    public double AverageTurnsElapsed { get; init; }
    public double AverageMissileActions { get; init; }
    public double AverageReplanCount { get; init; }
    public double AverageDistanceTraveled { get; init; }
    public double AverageTotalFuelSpent { get; init; }
    public double AverageStationarySearchFuelSpent { get; init; }
    public int TrialErrorCount { get; init; }
    public int DatalinkContractFailureCount { get; init; }
    public int TerminalOpportunityInvariantFailureCount { get; init; }
    public int UnexplainedUnresolvedCount { get; init; }
    public IReadOnlyList<string> FailureReasons { get; init; } = Array.Empty<string>();
    public string ScenarioSha256 { get; init; } = string.Empty;
    public string ResultsSha256 { get; init; } = string.Empty;
    public bool Passed { get; init; }
}

public sealed class FullFlightCalibrationMarginalResult
{
    public string Metric { get; init; } = string.Empty;
    public string Axis { get; init; } = string.Empty;
    public string ProfileId { get; init; } = string.Empty;
    public int MissileTechnologyLevel { get; init; }
    public int TargetPropulsionTechnologyLevel { get; init; }
    public string TargetMovementPolicy { get; init; } = string.Empty;
    public string DatalinkCondition { get; init; } = string.Empty;
    public string FromValue { get; init; } = string.Empty;
    public string ToValue { get; init; } = string.Empty;
    public string ExpectedDirection { get; init; } = string.Empty;
    public int TrialCount { get; init; }
    public int NeitherTrue { get; init; }
    public int FromOnlyTrue { get; init; }
    public int ToOnlyTrue { get; init; }
    public int BothTrue { get; init; }
    public double ObservedDelta { get; init; }
    public double PairedDeltaConfidence95Low { get; init; }
    public double PairedDeltaConfidence95High { get; init; }
    public double RawPValue { get; init; }
    public double HolmAdjustedPValue { get; set; }
    public double MinimumPracticalMarginalDelta { get; init; }
    public double MarginalFamilywiseAlpha { get; init; }
    public string PairingFingerprintSha256 { get; init; } = string.Empty;
    public bool CommonRandomNumbersVerified { get; init; }
    public bool StatisticalGateApplied { get; init; }
    public bool StatisticallyContradictory { get; set; }
}

public sealed class FullFlightCalibrationResultsDocument
{
    public int SchemaVersion { get; init; } = 3;
    public string RunMode { get; init; } = "calibration";
    public bool StatisticalGatesApplied { get; init; }
    public bool CommonRandomNumbersVerified { get; init; }
    public string StudyId { get; init; } = string.Empty;
    public string StudyName { get; init; } = string.Empty;
    public string StudySha256 { get; init; } = string.Empty;
    public string ProfileCatalogSha256 { get; init; } = string.Empty;
    public string RunnerAssemblySha256 { get; init; } = string.Empty;
    public string CoreAssemblySha256 { get; init; } = string.Empty;
    public int TrialsPerVariant { get; init; }
    public int VariantCount { get; init; }
    public int MarginalCount { get; init; }
    public int InferentialMarginalCount { get; init; }
    public int DescriptiveMarginalCount { get; init; }
    public int ContradictoryMarginalCount { get; init; }
    public int FailedVariantCount { get; init; }
    public int TrialErrorCount { get; init; }
    public int DatalinkContractFailureCount { get; init; }
    public int TerminalOpportunityInvariantFailureCount { get; init; }
    public int UnexplainedUnresolvedCount { get; init; }
    public int MinimumSafetyTurns { get; init; }
    public int SafetyTurnBuffer { get; init; }
    public int MinimumDerivedSafetyTurnCap { get; init; }
    public int MaximumDerivedSafetyTurnCap { get; init; }
    public string RandomSeedNamespace { get; init; } = string.Empty;
    public double MinimumPracticalMarginalDelta { get; init; }
    public double MarginalFamilywiseAlpha { get; init; }
    public bool Passed { get; init; }
    public IReadOnlyList<FullFlightCalibrationVariantResult> Variants { get; init; } =
        Array.Empty<FullFlightCalibrationVariantResult>();
    public IReadOnlyList<FullFlightCalibrationMarginalResult> Marginals { get; init; } =
        Array.Empty<FullFlightCalibrationMarginalResult>();
}

public sealed class FullFlightVariantExecutionRecord
{
    public string VariantId { get; init; } = string.Empty;
    public int TrialCount { get; init; }
    public int BlockCount { get; init; }
    public long ComputeMilliseconds { get; init; }
}

public sealed class FullFlightExecutionDocument
{
    public int SchemaVersion { get; init; } = 4;
    public string RunMode { get; init; } = "calibration";
    public string SchedulingStrategy { get; init; } = "global-trial-block-workers";
    public string TrialExecutionMode { get; init; } = "CompactMetrics";
    public int RequestedWorkers { get; init; }
    public int WorkerLimit { get; init; }
    public int PeakActiveWorkers { get; init; }
    public int InnerTrialWorkersPerVariant { get; init; }
    public int VariantCount { get; init; }
    public int TrialsPerVariant { get; init; }
    public long TotalTrials { get; init; }
    public int TrialBlockSize { get; init; }
    public int TrialBlockCount { get; init; }
    public int CompletedTrialBlockCount { get; init; }
    public long ComputeElapsedMilliseconds { get; init; }
    public long OutputFinalizationMilliseconds { get; init; }
    public long ElapsedMilliseconds { get; init; }
    public double VariantsPerSecond { get; init; }
    public double TrialsPerSecond { get; init; }
    public double ComputeTrialsPerSecond { get; init; }
    public long ProcessCpuMilliseconds { get; init; }
    public double EffectiveProcessorCores { get; init; }
    public double NormalizedCpuUtilizationPercent { get; init; }
    public int EnvironmentProcessorCount { get; init; }
    public int ProcessAffinityProcessorCount { get; init; }
    public bool ServerGarbageCollection { get; init; }
    public long AllocatedBytes { get; init; }
    public double AllocatedBytesPerTrial { get; init; }
    public int Gen0Collections { get; init; }
    public int Gen1Collections { get; init; }
    public int Gen2Collections { get; init; }
    public DateTimeOffset CompletedUtc { get; init; }
    public IReadOnlyList<FullFlightVariantExecutionRecord> Variants { get; init; } =
        Array.Empty<FullFlightVariantExecutionRecord>();
}

public sealed class FullFlightCalibrationRunResult
{
    public required FullFlightCalibrationResultsDocument Results { get; init; }
    public required FullFlightExecutionDocument Execution { get; init; }
    public required string ResultsSha256 { get; init; }
    public required string OutputDirectory { get; init; }
    public bool Passed => Results.Passed;
}
