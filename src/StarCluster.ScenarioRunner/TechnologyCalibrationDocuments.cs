namespace StarCluster.ScenarioRunner;

public sealed class TechnologyCalibrationStudyDocument
{
    public int SchemaVersion { get; set; } = 1;
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string BaseScenario { get; set; } = string.Empty;
    public string ProfileCatalog { get; set; } = string.Empty;
    public int TrialsPerVariant { get; set; } = 2_000;
    public ulong MasterSeed { get; set; } = 200100UL;
    public double MaximumAbsoluteError { get; set; } = 0.04;
    public double MinimumPracticalMarginalDelta { get; set; } = 0.01;
    public double MarginalFamilywiseAlpha { get; set; } = 0.05;
    public List<string> MissileProfiles { get; set; } = new();
    public List<int> MissileTechnologyLevels { get; set; } = new();
    public List<int> PdsTechnologyLevels { get; set; } = new();
    public List<int> TargetEcmTechnologyLevels { get; set; } = new();
}

public sealed class TechnologyProfileCatalogDocument
{
    public int SchemaVersion { get; set; } = 1;
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public int ControlSensorFirmRange { get; set; } = 20;
    public int ControlSensorApproximateRange { get; set; } = 20;
    public int AcquisitionPenaltyPercentPerNetEcmStrength { get; set; } = 10;
    public int MinimumHitChancePercent { get; set; } = 5;
    public int MaximumHitChancePercent { get; set; } = 95;
    public int MinimumAcquisitionChancePercent { get; set; } = 5;
    public int MaximumAcquisitionChancePercent { get; set; } = 95;
    public List<RepresentativeMissileProfileDocument> MissileProfiles { get; set; } = new();
    public List<TechnologyLevelCalibrationDocument> TechnologyLevels { get; set; } = new();
    public PdsTechnologyCalibrationDocument Pds { get; set; } = new();
}

public sealed class RepresentativeMissileProfileDocument
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public bool DatalinkInstalled { get; set; } = true;
    public bool SensorInstalled { get; set; }
    public bool SeekerInstalled { get; set; }
}

public sealed class TechnologyLevelCalibrationDocument
{
    public int TechnologyLevel { get; set; }
    public int FlightSpeedHexesPerTurn { get; set; }
    public int ShipMovementHexesPerTurn { get; set; } = 1;
    public int MaximumRangeHexes { get; set; }
    public int DatalinkRetainedReportAgePhases { get; set; }
    public int SensorFirmRangeHexes { get; set; }
    public int SensorApproximateRangeHexes { get; set; }
    public int SensorActiveModeBonusHexes { get; set; }
    public int SensorMaximumLocalTrackAgeEpochs { get; set; }
    public int GuidanceBaseHitChancePercent { get; set; }
    public int SeekerBaseAcquisitionChancePercent { get; set; }
    public int SeekerEccmStrength { get; set; }
    public int SeekerAccuracyBonusPercent { get; set; }
    public int TerminalEcmStrength { get; set; }
}

public sealed class PdsTechnologyCalibrationDocument
{
    public int EqualTechnologyInterceptionChancePercent { get; set; } = 35;
    public int InterceptionChancePercentPerTechnologyDelta { get; set; } = 10;
    public int MinimumInterceptionChancePercent { get; set; } = 5;
    public int MaximumInterceptionChancePercent { get; set; } = 95;
    public int RangeHexes { get; set; } = 1;
    public int MaximumAttemptsPerPhase { get; set; } = 2;
}

public sealed class TechnologyCalibrationVariantResult
{
    public string Id { get; init; } = string.Empty;
    public string ProfileId { get; init; } = string.Empty;
    public string ProfileName { get; init; } = string.Empty;
    public int MissileTechnologyLevel { get; init; }
    public int PdsTechnologyLevel { get; init; }
    public int TargetEcmTechnologyLevel { get; init; }
    public int Trials { get; init; }
    public int PdsInterceptionChancePercent { get; init; }
    public int GuidanceBaseHitChancePercent { get; init; }
    public int SeekerBaseAcquisitionChancePercent { get; init; }
    public int SeekerEccmStrength { get; init; }
    public int SeekerAccuracyBonusPercent { get; init; }
    public int EffectiveAttackChancePercent { get; init; }
    public int TargetTerminalEcmStrength { get; init; }
    public double ExpectedTerminalEntryInterception { get; init; }
    public double ExpectedPreTerminalAttackInterception { get; init; }
    public double ExpectedAcquisitionSuccess { get; init; }
    public double ExpectedAttackResolution { get; init; }
    public double ExpectedEffectiveHit { get; init; }
    public double ObservedTerminalEntryInterception { get; init; }
    public double ObservedPreTerminalAttackInterception { get; init; }
    public double ObservedAcquisitionSuccess { get; init; }
    public double ObservedAttackResolution { get; init; }
    public double ObservedEffectiveHit { get; init; }
    public double EffectiveHitConfidence95Low { get; init; }
    public double EffectiveHitConfidence95High { get; init; }
    public double EffectiveHitAbsoluteError { get; init; }
    public double MaximumMetricAbsoluteError { get; init; }
    public string WorstMetric { get; init; } = string.Empty;
    public double MaximumAbsoluteError { get; init; }
    public double AverageDistanceTraveled { get; init; }
    public double AverageTotalFuelSpent { get; init; }
    public double AverageStationarySearchFuelSpent { get; init; }
    public string ScenarioSha256 { get; init; } = string.Empty;
    public string ResultsSha256 { get; init; } = string.Empty;
    public bool Passed { get; init; }
}

public sealed class TechnologyCalibrationMarginalResult
{
    public string Axis { get; init; } = string.Empty;
    public string ProfileId { get; init; } = string.Empty;
    public int MissileTechnologyLevel { get; init; }
    public int PdsTechnologyLevel { get; init; }
    public int TargetEcmTechnologyLevel { get; init; }
    public int FromTechnologyLevel { get; init; }
    public int ToTechnologyLevel { get; init; }
    public string ExpectedDirection { get; init; } = string.Empty;
    public double FromExpectedEffectiveHit { get; init; }
    public double ToExpectedEffectiveHit { get; init; }
    public double ExpectedDelta { get; init; }
    public double FromObservedEffectiveHit { get; init; }
    public double ToObservedEffectiveHit { get; init; }
    public double ObservedDelta { get; init; }
    public int TrialCount { get; init; }
    public int NeitherEffectiveHit { get; init; }
    public int FromOnlyEffectiveHit { get; init; }
    public int ToOnlyEffectiveHit { get; init; }
    public int BothEffectiveHit { get; init; }
    public double PairedDeltaConfidence95Low { get; init; }
    public double PairedDeltaConfidence95High { get; init; }
    public double RawPValue { get; init; }
    public double HolmAdjustedPValue { get; set; }
    public double MinimumPracticalMarginalDelta { get; init; }
    public double MarginalFamilywiseAlpha { get; init; }
    public string PairingFingerprintSha256 { get; init; } = string.Empty;
    public bool CommonRandomNumbersVerified { get; init; }
    public bool StatisticallyContradictory { get; set; }
}

public sealed class TechnologyCalibrationResultsDocument
{
    public int SchemaVersion { get; init; } = 2;
    public string StudyId { get; init; } = string.Empty;
    public string StudyName { get; init; } = string.Empty;
    public string StudySha256 { get; init; } = string.Empty;
    public string ProfileCatalogSha256 { get; init; } = string.Empty;
    public string BaseScenarioSha256 { get; init; } = string.Empty;
    public string RunnerAssemblySha256 { get; init; } = string.Empty;
    public string CoreAssemblySha256 { get; init; } = string.Empty;
    public int TrialsPerVariant { get; init; }
    public int VariantCount { get; init; }
    public string RandomSeedNamespace { get; init; } = string.Empty;
    public double MinimumPracticalMarginalDelta { get; init; }
    public double MarginalFamilywiseAlpha { get; init; }
    public int ContradictoryMarginalCount { get; init; }
    public bool Passed { get; init; }
    public IReadOnlyList<TechnologyCalibrationVariantResult> Variants { get; init; } =
        Array.Empty<TechnologyCalibrationVariantResult>();
    public IReadOnlyList<TechnologyCalibrationMarginalResult> Marginals { get; init; } =
        Array.Empty<TechnologyCalibrationMarginalResult>();
}

public sealed class TechnologyCalibrationRunResult
{
    public required TechnologyCalibrationResultsDocument Results { get; init; }
    public required string ResultsSha256 { get; init; }
    public required string OutputDirectory { get; init; }
    public bool Passed => Results.Passed;
}
