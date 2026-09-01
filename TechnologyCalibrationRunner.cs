using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public static class TechnologyCalibrationRunner
{
    private sealed class CalibrationOutcomeVector
    {
        public required bool[] EffectiveHits { get; init; }
        public required string PairingFingerprintSha256 { get; init; }
    }

    public static TechnologyCalibrationRunResult Run(
        TechnologyCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        string studyPath,
        int jobs,
        int? trialsOverride,
        bool keepTrialJournals,
        string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(study);
        ArgumentNullException.ThrowIfNull(catalog);
        if (string.IsNullOrWhiteSpace(studyPath))
        {
            throw new ArgumentException("A calibration study path is required.", nameof(studyPath));
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

        string fullStudyPath = Path.GetFullPath(studyPath);
        string studyDirectory = Path.GetDirectoryName(fullStudyPath) ??
            throw new InvalidOperationException("Calibration study directory could not be resolved.");
        string baseScenarioPath = Path.GetFullPath(
            Path.Combine(studyDirectory, study.BaseScenario));
        string catalogPath = Path.GetFullPath(
            Path.Combine(studyDirectory, study.ProfileCatalog));
        ScenarioDocument baseScenario =
            ScenarioDocumentSerialization.ReadScenario(baseScenarioPath);
        TechnologyCalibrationModel.Validate(study, catalog, baseScenario);
        IReadOnlyList<PreparedTechnologyCalibrationVariant> prepared =
            TechnologyCalibrationModel.PrepareVariants(study, catalog, baseScenario);

        string fullOutputDirectory = Path.GetFullPath(outputDirectory);
        if (Directory.Exists(fullOutputDirectory))
        {
            Directory.Delete(fullOutputDirectory, recursive: true);
        }
        Directory.CreateDirectory(fullOutputDirectory);

        string studySha256 = RunnerHashUtility.ComputeFileSha256(fullStudyPath);
        string catalogSha256 = RunnerHashUtility.ComputeFileSha256(catalogPath);
        string baseScenarioSha256 = RunnerHashUtility.ComputeFileSha256(baseScenarioPath);
        var results = new List<TechnologyCalibrationVariantResult>(prepared.Count);
        var outcomesByVariant = new Dictionary<string, CalibrationOutcomeVector>(
            StringComparer.Ordinal);
        string randomSeedNamespace = study.Id + "|common-random-numbers-v1";

        Console.WriteLine(
            $"Calibration preflight: {prepared.Count} variants across " +
            $"{study.MissileProfiles.Count} missile profiles passed.");
        foreach (IGrouping<string, PreparedTechnologyCalibrationVariant> profileGroup in
                 prepared.GroupBy(item => item.Profile.Id, StringComparer.Ordinal))
        {
            Console.WriteLine(
                $"Running {profileGroup.Key}: {profileGroup.Count()} variants at " +
                $"{trials} trials each with jobs={jobs}.");
            foreach (PreparedTechnologyCalibrationVariant item in profileGroup)
            {
                string variantDirectory = Path.Combine(
                    fullOutputDirectory,
                    "variants",
                    item.Id);
                MonteCarloBatchRunResult batch = MonteCarloBatchRunner.Run(
                    item.Scenario,
                    item.Id,
                    new MonteCarloBatchOptions
                    {
                        Trials = trials,
                        MasterSeed = study.MasterSeed,
                        Jobs = jobs,
                        Resume = false,
                        CheckpointEvery = 256,
                        TraceSamples = 0,
                        KeepTrialJournal = keepTrialJournals,
                        RandomSeedNamespace = randomSeedNamespace,
                    },
                    variantDirectory);
                results.Add(CreateVariantResult(
                    study,
                    item,
                    batch,
                    trials));
                outcomesByVariant.Add(
                    item.Id,
                    CreateOutcomeVector(batch.Trials));
            }
        }

        TechnologyCalibrationVariantResult[] orderedResults = results
            .OrderBy(item => item.Id, StringComparer.Ordinal)
            .ToArray();
        TechnologyCalibrationMarginalResult[] marginals =
            CreateMarginals(orderedResults, outcomesByVariant, study);
        int contradictoryMarginals = marginals.Count(item => item.StatisticallyContradictory);
        bool passed =
            orderedResults.All(item => item.Passed) &&
            contradictoryMarginals == 0 &&
            marginals.All(item => item.CommonRandomNumbersVerified);
        var document = new TechnologyCalibrationResultsDocument
        {
            StudyId = study.Id,
            StudyName = study.Name,
            StudySha256 = studySha256,
            ProfileCatalogSha256 = catalogSha256,
            BaseScenarioSha256 = baseScenarioSha256,
            RunnerAssemblySha256 = RunnerHashUtility.RunnerAssemblySha256,
            CoreAssemblySha256 = RunnerHashUtility.CoreAssemblySha256,
            TrialsPerVariant = trials,
            VariantCount = orderedResults.Length,
            RandomSeedNamespace = randomSeedNamespace,
            MinimumPracticalMarginalDelta = study.MinimumPracticalMarginalDelta,
            MarginalFamilywiseAlpha = study.MarginalFamilywiseAlpha,
            ContradictoryMarginalCount = contradictoryMarginals,
            Passed = passed,
            Variants = Array.AsReadOnly(orderedResults),
            Marginals = Array.AsReadOnly(marginals),
        };

        string resultsPath = Path.Combine(
            fullOutputDirectory,
            "calibration-summary.json");
        WriteJsonAtomic(resultsPath, document);
        WriteSummaryCsv(
            Path.Combine(fullOutputDirectory, "calibration-summary.csv"),
            orderedResults);
        WriteMarginalsCsv(
            Path.Combine(fullOutputDirectory, "calibration-marginals.csv"),
            marginals);
        string resultsSha256 = RunnerHashUtility.ComputeFileSha256(resultsPath);
        File.WriteAllText(
            Path.Combine(fullOutputDirectory, "calibration-result.sha256"),
            resultsSha256 + Environment.NewLine,
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));

        int failedVariants = orderedResults.Count(item => !item.Passed);
        Console.WriteLine(
            $"Calibration: {orderedResults.Length - failedVariants} variants passed, " +
            $"{failedVariants} failed; {contradictoryMarginals} statistically " +
            $"contradictory marginals after Holm correction. Hash: {resultsSha256}. " +
            $"Output: {fullOutputDirectory}");
        return new TechnologyCalibrationRunResult
        {
            Results = document,
            ResultsSha256 = resultsSha256,
            OutputDirectory = fullOutputDirectory,
        };
    }

    private static TechnologyCalibrationVariantResult CreateVariantResult(
        TechnologyCalibrationStudyDocument study,
        PreparedTechnologyCalibrationVariant item,
        MonteCarloBatchRunResult batch,
        int trials)
    {
        ProbabilityMetricSummary entry = GetMetric(
            batch.Results,
            "stage.TerminalEntryIntercepted");
        ProbabilityMetricSummary preAttack = GetMetric(
            batch.Results,
            "stage.PreTerminalAttackIntercepted");
        ProbabilityMetricSummary acquisition = GetMetric(
            batch.Results,
            "process.acquisitionSucceeded");
        ProbabilityMetricSummary attack = GetMetric(
            batch.Results,
            "process.attackResolved");
        ProbabilityMetricSummary effectiveHit = GetMetric(
            batch.Results,
            "effect.effectiveHit");
        double pds = item.PdsInterceptionChancePercent / 100.0;
        double expectedAcquisition =
            (1.0 - pds) * item.AcquisitionSuccessProbability;

        var errors = new Dictionary<string, double>(StringComparer.Ordinal)
        {
            ["stage.TerminalEntryIntercepted"] = Math.Abs(
                entry.Proportion - item.ExpectedTerminalEntryInterception),
            ["stage.PreTerminalAttackIntercepted"] = Math.Abs(
                preAttack.Proportion - item.ExpectedPreTerminalAttackInterception),
            ["process.acquisitionSucceeded"] = Math.Abs(
                acquisition.Proportion - expectedAcquisition),
            ["process.attackResolved"] = Math.Abs(
                attack.Proportion - item.ExpectedAttackResolution),
            ["effect.effectiveHit"] = Math.Abs(
                effectiveHit.Proportion - item.ExpectedEffectiveHit),
        };
        KeyValuePair<string, double> worst = errors
            .OrderByDescending(pair => pair.Value)
            .ThenBy(pair => pair.Key, StringComparer.Ordinal)
            .First();

        return new TechnologyCalibrationVariantResult
        {
            Id = item.Id,
            ProfileId = item.Profile.Id,
            ProfileName = item.Profile.Name,
            MissileTechnologyLevel = item.MissileTechnology.TechnologyLevel,
            PdsTechnologyLevel = item.PdsTechnologyLevel,
            TargetEcmTechnologyLevel = item.TargetEcmTechnology.TechnologyLevel,
            Trials = trials,
            PdsInterceptionChancePercent = item.PdsInterceptionChancePercent,
            GuidanceBaseHitChancePercent =
                item.MissileTechnology.GuidanceBaseHitChancePercent,
            SeekerBaseAcquisitionChancePercent =
                item.MissileTechnology.SeekerBaseAcquisitionChancePercent,
            SeekerEccmStrength = item.MissileTechnology.SeekerEccmStrength,
            SeekerAccuracyBonusPercent =
                item.MissileTechnology.SeekerAccuracyBonusPercent,
            EffectiveAttackChancePercent = item.EffectiveAttackChancePercent,
            TargetTerminalEcmStrength = item.TargetEcmTechnology.TerminalEcmStrength,
            ExpectedTerminalEntryInterception = item.ExpectedTerminalEntryInterception,
            ExpectedPreTerminalAttackInterception =
                item.ExpectedPreTerminalAttackInterception,
            ExpectedAcquisitionSuccess = expectedAcquisition,
            ExpectedAttackResolution = item.ExpectedAttackResolution,
            ExpectedEffectiveHit = item.ExpectedEffectiveHit,
            ObservedTerminalEntryInterception = entry.Proportion,
            ObservedPreTerminalAttackInterception = preAttack.Proportion,
            ObservedAcquisitionSuccess = acquisition.Proportion,
            ObservedAttackResolution = attack.Proportion,
            ObservedEffectiveHit = effectiveHit.Proportion,
            EffectiveHitConfidence95Low = effectiveHit.Confidence95Low,
            EffectiveHitConfidence95High = effectiveHit.Confidence95High,
            EffectiveHitAbsoluteError = errors["effect.effectiveHit"],
            MaximumMetricAbsoluteError = worst.Value,
            WorstMetric = worst.Key,
            MaximumAbsoluteError = study.MaximumAbsoluteError,
            AverageDistanceTraveled = batch.Results.AverageDistanceTraveled,
            AverageTotalFuelSpent = batch.Results.AverageTotalFuelSpent,
            AverageStationarySearchFuelSpent =
                batch.Results.AverageStationarySearchFuelSpent,
            ScenarioSha256 = batch.Results.ScenarioSha256,
            ResultsSha256 = batch.ResultsSha256,
            Passed = batch.Passed && worst.Value <= study.MaximumAbsoluteError,
        };
    }

    private static ProbabilityMetricSummary GetMetric(
        MonteCarloResultsDocument results,
        string key) =>
        results.Metrics.FirstOrDefault(item => string.Equals(
            item.Key,
            key,
            StringComparison.Ordinal)) ??
        throw new InvalidOperationException(
            $"Calibration metric '{key}' was not present for variant '{results.VariantId}'.");

    private static TechnologyCalibrationMarginalResult[] CreateMarginals(
        IReadOnlyList<TechnologyCalibrationVariantResult> variants,
        IReadOnlyDictionary<string, CalibrationOutcomeVector> outcomesByVariant,
        TechnologyCalibrationStudyDocument study)
    {
        var output = new List<TechnologyCalibrationMarginalResult>();
        AddAxisMarginals(
            output,
            variants,
            outcomesByVariant,
            study,
            "missileTl",
            item => item.MissileTechnologyLevel,
            item => $"{item.ProfileId}|p{item.PdsTechnologyLevel}|e{item.TargetEcmTechnologyLevel}");
        AddAxisMarginals(
            output,
            variants,
            outcomesByVariant,
            study,
            "pdsTl",
            item => item.PdsTechnologyLevel,
            item => $"{item.ProfileId}|m{item.MissileTechnologyLevel}|e{item.TargetEcmTechnologyLevel}");
        AddAxisMarginals(
            output,
            variants,
            outcomesByVariant,
            study,
            "targetEcmTl",
            item => item.TargetEcmTechnologyLevel,
            item => $"{item.ProfileId}|m{item.MissileTechnologyLevel}|p{item.PdsTechnologyLevel}");

        TechnologyCalibrationMarginalResult[] ordered = output
            .OrderBy(item => item.Axis, StringComparer.Ordinal)
            .ThenBy(item => item.ProfileId, StringComparer.Ordinal)
            .ThenBy(item => item.MissileTechnologyLevel)
            .ThenBy(item => item.PdsTechnologyLevel)
            .ThenBy(item => item.TargetEcmTechnologyLevel)
            .ThenBy(item => item.FromTechnologyLevel)
            .ToArray();
        double[] adjusted = PairedMarginalStatistics.AdjustHolm(
            ordered.Select(item => item.RawPValue).ToArray());
        for (int index = 0; index < ordered.Length; index++)
        {
            ordered[index].HolmAdjustedPValue = adjusted[index];
            ordered[index].StatisticallyContradictory =
                PairedMarginalStatistics.IsStatisticallyContradictory(
                    ordered[index].ExpectedDirection,
                    ordered[index].ObservedDelta,
                    adjusted[index],
                    study.MinimumPracticalMarginalDelta,
                    study.MarginalFamilywiseAlpha);
        }

        return ordered;
    }

    private static void AddAxisMarginals(
        ICollection<TechnologyCalibrationMarginalResult> output,
        IReadOnlyList<TechnologyCalibrationVariantResult> variants,
        IReadOnlyDictionary<string, CalibrationOutcomeVector> outcomesByVariant,
        TechnologyCalibrationStudyDocument study,
        string axis,
        Func<TechnologyCalibrationVariantResult, int> levelSelector,
        Func<TechnologyCalibrationVariantResult, string> groupSelector)
    {
        foreach (IGrouping<string, TechnologyCalibrationVariantResult> group in
                 variants.GroupBy(groupSelector, StringComparer.Ordinal))
        {
            TechnologyCalibrationVariantResult[] ordered = group
                .OrderBy(levelSelector)
                .ToArray();
            for (int index = 1; index < ordered.Length; index++)
            {
                TechnologyCalibrationVariantResult from = ordered[index - 1];
                TechnologyCalibrationVariantResult to = ordered[index];
                double expectedDelta =
                    to.ExpectedEffectiveHit - from.ExpectedEffectiveHit;
                string expectedDirection = expectedDelta > 1e-12
                    ? "nondecreasing"
                    : expectedDelta < -1e-12
                        ? "nonincreasing"
                        : "flat";
                CalibrationOutcomeVector fromOutcomes = outcomesByVariant[from.Id];
                CalibrationOutcomeVector toOutcomes = outcomesByVariant[to.Id];
                bool commonRandomNumbersVerified = string.Equals(
                    fromOutcomes.PairingFingerprintSha256,
                    toOutcomes.PairingFingerprintSha256,
                    StringComparison.Ordinal);
                if (!commonRandomNumbersVerified)
                {
                    throw new InvalidOperationException(
                        $"Calibration variants '{from.Id}' and '{to.Id}' did not " +
                        "share the same trial random streams.");
                }
                PairedBinaryDifferenceSummary paired = PairedMarginalStatistics.Compare(
                    fromOutcomes.EffectiveHits,
                    toOutcomes.EffectiveHits,
                    expectedDirection);
                double aggregateDelta =
                    to.ObservedEffectiveHit - from.ObservedEffectiveHit;
                if (Math.Abs(paired.ObservedDelta - aggregateDelta) > 1e-12)
                {
                    throw new InvalidOperationException(
                        $"Paired delta for '{from.Id}' -> '{to.Id}' did not match " +
                        "the aggregate effective-hit delta.");
                }

                output.Add(new TechnologyCalibrationMarginalResult
                {
                    Axis = axis,
                    ProfileId = from.ProfileId,
                    MissileTechnologyLevel = axis == "missileTl"
                        ? to.MissileTechnologyLevel
                        : from.MissileTechnologyLevel,
                    PdsTechnologyLevel = axis == "pdsTl"
                        ? to.PdsTechnologyLevel
                        : from.PdsTechnologyLevel,
                    TargetEcmTechnologyLevel = axis == "targetEcmTl"
                        ? to.TargetEcmTechnologyLevel
                        : from.TargetEcmTechnologyLevel,
                    FromTechnologyLevel = levelSelector(from),
                    ToTechnologyLevel = levelSelector(to),
                    ExpectedDirection = expectedDirection,
                    FromExpectedEffectiveHit = from.ExpectedEffectiveHit,
                    ToExpectedEffectiveHit = to.ExpectedEffectiveHit,
                    ExpectedDelta = expectedDelta,
                    FromObservedEffectiveHit = from.ObservedEffectiveHit,
                    ToObservedEffectiveHit = to.ObservedEffectiveHit,
                    ObservedDelta = paired.ObservedDelta,
                    TrialCount = paired.TrialCount,
                    NeitherEffectiveHit = paired.NeitherTrue,
                    FromOnlyEffectiveHit = paired.FromOnlyTrue,
                    ToOnlyEffectiveHit = paired.ToOnlyTrue,
                    BothEffectiveHit = paired.BothTrue,
                    PairedDeltaConfidence95Low = paired.Confidence95Low,
                    PairedDeltaConfidence95High = paired.Confidence95High,
                    RawPValue = paired.RawPValue,
                    MinimumPracticalMarginalDelta =
                        study.MinimumPracticalMarginalDelta,
                    MarginalFamilywiseAlpha = study.MarginalFamilywiseAlpha,
                    PairingFingerprintSha256 =
                        fromOutcomes.PairingFingerprintSha256,
                    CommonRandomNumbersVerified = commonRandomNumbersVerified,
                });
            }
        }
    }

    private static void WriteSummaryCsv(
        string path,
        IEnumerable<TechnologyCalibrationVariantResult> variants)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "id,profileId,missileTl,pdsTl,targetEcmTl,trials,pdsChancePercent," +
            "guidanceBaseHitPercent,seekerBaseAcquisitionPercent,seekerEccm," +
            "seekerAccuracyBonusPercent,effectiveAttackChancePercent," +
            "targetTerminalEcmStrength,expectedEntryIntercept,observedEntryIntercept," +
            "expectedPreAttackIntercept,observedPreAttackIntercept," +
            "expectedAcquisitionSuccess,observedAcquisitionSuccess," +
            "expectedAttackResolution,observedAttackResolution," +
            "expectedEffectiveHit,observedEffectiveHit,effectiveHitCi95Low," +
            "effectiveHitCi95High,maximumMetricAbsoluteError,worstMetric,passed");
        foreach (TechnologyCalibrationVariantResult item in variants)
        {
            builder.Append(Csv(item.Id)).Append(',')
                .Append(Csv(item.ProfileId)).Append(',')
                .Append(item.MissileTechnologyLevel).Append(',')
                .Append(item.PdsTechnologyLevel).Append(',')
                .Append(item.TargetEcmTechnologyLevel).Append(',')
                .Append(item.Trials).Append(',')
                .Append(item.PdsInterceptionChancePercent).Append(',')
                .Append(item.GuidanceBaseHitChancePercent).Append(',')
                .Append(item.SeekerBaseAcquisitionChancePercent).Append(',')
                .Append(item.SeekerEccmStrength).Append(',')
                .Append(item.SeekerAccuracyBonusPercent).Append(',')
                .Append(item.EffectiveAttackChancePercent).Append(',')
                .Append(item.TargetTerminalEcmStrength).Append(',')
                .Append(Number(item.ExpectedTerminalEntryInterception)).Append(',')
                .Append(Number(item.ObservedTerminalEntryInterception)).Append(',')
                .Append(Number(item.ExpectedPreTerminalAttackInterception)).Append(',')
                .Append(Number(item.ObservedPreTerminalAttackInterception)).Append(',')
                .Append(Number(item.ExpectedAcquisitionSuccess)).Append(',')
                .Append(Number(item.ObservedAcquisitionSuccess)).Append(',')
                .Append(Number(item.ExpectedAttackResolution)).Append(',')
                .Append(Number(item.ObservedAttackResolution)).Append(',')
                .Append(Number(item.ExpectedEffectiveHit)).Append(',')
                .Append(Number(item.ObservedEffectiveHit)).Append(',')
                .Append(Number(item.EffectiveHitConfidence95Low)).Append(',')
                .Append(Number(item.EffectiveHitConfidence95High)).Append(',')
                .Append(Number(item.MaximumMetricAbsoluteError)).Append(',')
                .Append(Csv(item.WorstMetric)).Append(',')
                .Append(item.Passed ? "true" : "false")
                .AppendLine();
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static void WriteMarginalsCsv(
        string path,
        IEnumerable<TechnologyCalibrationMarginalResult> marginals)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "axis,profileId,missileTl,pdsTl,targetEcmTl,fromTl,toTl," +
            "expectedDirection,fromExpectedEffectiveHit,toExpectedEffectiveHit," +
            "expectedDelta,fromObservedEffectiveHit,toObservedEffectiveHit," +
            "observedDelta,trialCount,neitherEffectiveHit,fromOnlyEffectiveHit," +
            "toOnlyEffectiveHit,bothEffectiveHit,pairedDeltaCi95Low," +
            "pairedDeltaCi95High,rawPValue,holmAdjustedPValue," +
            "minimumPracticalMarginalDelta,marginalFamilywiseAlpha," +
            "pairingFingerprintSha256,commonRandomNumbersVerified," +
            "statisticallyContradictory");
        foreach (TechnologyCalibrationMarginalResult item in marginals)
        {
            builder.Append(Csv(item.Axis)).Append(',')
                .Append(Csv(item.ProfileId)).Append(',')
                .Append(item.MissileTechnologyLevel).Append(',')
                .Append(item.PdsTechnologyLevel).Append(',')
                .Append(item.TargetEcmTechnologyLevel).Append(',')
                .Append(item.FromTechnologyLevel).Append(',')
                .Append(item.ToTechnologyLevel).Append(',')
                .Append(Csv(item.ExpectedDirection)).Append(',')
                .Append(Number(item.FromExpectedEffectiveHit)).Append(',')
                .Append(Number(item.ToExpectedEffectiveHit)).Append(',')
                .Append(Number(item.ExpectedDelta)).Append(',')
                .Append(Number(item.FromObservedEffectiveHit)).Append(',')
                .Append(Number(item.ToObservedEffectiveHit)).Append(',')
                .Append(Number(item.ObservedDelta)).Append(',')
                .Append(item.TrialCount).Append(',')
                .Append(item.NeitherEffectiveHit).Append(',')
                .Append(item.FromOnlyEffectiveHit).Append(',')
                .Append(item.ToOnlyEffectiveHit).Append(',')
                .Append(item.BothEffectiveHit).Append(',')
                .Append(Number(item.PairedDeltaConfidence95Low)).Append(',')
                .Append(Number(item.PairedDeltaConfidence95High)).Append(',')
                .Append(Number(item.RawPValue)).Append(',')
                .Append(Number(item.HolmAdjustedPValue)).Append(',')
                .Append(Number(item.MinimumPracticalMarginalDelta)).Append(',')
                .Append(Number(item.MarginalFamilywiseAlpha)).Append(',')
                .Append(Csv(item.PairingFingerprintSha256)).Append(',')
                .Append(item.CommonRandomNumbersVerified ? "true" : "false").Append(',')
                .Append(item.StatisticallyContradictory ? "true" : "false")
                .AppendLine();
        }
        File.WriteAllText(
            path,
            builder.ToString(),
            new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    private static CalibrationOutcomeVector CreateOutcomeVector(
        IReadOnlyList<MonteCarloTrialResult> trials)
    {
        MonteCarloTrialResult[] ordered = trials
            .OrderBy(item => item.TrialIndex)
            .ToArray();
        bool[] effectiveHits = ordered
            .Select(item =>
                item.FinalOutcome == nameof(MissileTerminalOutcome.Hit) ||
                item.FinalOutcome == nameof(MissileTerminalOutcome.CriticalHit))
            .ToArray();
        using IncrementalHash hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (MonteCarloTrialResult trial in ordered)
        {
            string seedRecord =
                $"{trial.TrialIndex}|{trial.TrialSeedHex}|" +
                $"{trial.InterceptionSeedHex}|{trial.TerminalSeedHex}\n";
            hash.AppendData(Encoding.UTF8.GetBytes(seedRecord));
        }
        string fingerprint = Convert.ToHexString(hash.GetHashAndReset())
            .ToLowerInvariant();
        return new CalibrationOutcomeVector
        {
            EffectiveHits = effectiveHits,
            PairingFingerprintSha256 = fingerprint,
        };
    }

    private static string Number(double value) =>
        value.ToString("R", CultureInfo.InvariantCulture);

    private static string Csv(string value) =>
        "\"" + value.Replace("\"", "\"\"") + "\"";

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
