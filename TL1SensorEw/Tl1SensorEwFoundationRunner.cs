using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.Tracking;
using StarCluster.ScenarioRunner.TL1;

namespace StarCluster.ScenarioRunner.TL1SensorEw;

public static class Tl1SensorEwFoundationRunner
{
    private const string ExpectedSchemaVersion =
        "star-cluster-tl1-sensor-ew-foundation-v1";
    private const string Cp68StudyId =
        "tl1-sew01-sensor-ew-foundation-range-sweep";
    private const string Cp69StudyId =
        "tl1-sew02-sensor-ew-foundation-range-sweep";
    private const string Cp71StudyId =
        "tl1-sew03-sensor-ew-discrimination-burnthrough";

    private static readonly SensorEwCase[] Cases =
    {
        new("passive-quiet", SensorMode.Passive, false, false, false, 0, 0, true),
        new("active-quiet", SensorMode.Active, false, false, false, 0, 0, true),
        new("overload-quiet", SensorMode.Active, true, false, false, 0, 0, true),
        new("passive-target-active", SensorMode.Passive, false, true, false, 0, 0, true),
        new("passive-target-active-overload", SensorMode.Passive, false, true, true, 0, 0, true),
        new("passive-target-ecm", SensorMode.Passive, false, false, false, 1, 0, true),
        new("active-target-ecm", SensorMode.Active, false, false, false, 1, 0, true),
        new("overload-target-ecm", SensorMode.Active, true, false, false, 1, 0, true),
        new("active-target-ecm-eccm", SensorMode.Active, false, false, false, 1, 1, true),
        new("overload-target-ecm-eccm", SensorMode.Active, true, false, false, 1, 1, true),
        new("active-target-ecm2-eccm1", SensorMode.Active, false, false, false, 2, 1, true),
        new("passive-target-ecm-occluded", SensorMode.Passive, false, false, false, 1, 0, false),
    };

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        bool preflightOnly)
    {
        Tl1SensorEwFoundationStudy study = JsonSerializer.Deserialize<
            Tl1SensorEwFoundationStudy>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                    "TL1 Sensor/EW foundation study could not be read.");
        Tl1BaselineCatalog baseline = Tl1BaselineCatalog.Load(baselinePath);

        ValidateStudy(study, baseline);
        IReadOnlyList<SensorEwSweepRow> rows = BuildRows(study);
        IReadOnlyList<SensorEwCandidateSummary> summaries =
            BuildSummaries(study, baseline, rows);
        IReadOnlyList<SensorEwFoundationGate> gates =
            BuildGates(study, rows, summaries);
        int failed = gates.Count(gate => !gate.Passed);

        Console.WriteLine(
            "TL1 Sensor/EW foundation preflight: " +
            $"{study.Candidates.Count} profiles, {Cases.Length} contexts, " +
            $"{study.MaxTacticalSeparationHexes + 1} ranges, {rows.Count} rows, " +
            $"{failed} failed gates.");

        if (preflightOnly)
        {
            return failed == 0 ? 0 : 1;
        }

        Directory.CreateDirectory(outputDirectory);
        WriteRows(rows, outputDirectory);
        WriteSummaries(summaries, outputDirectory);
        WriteGates(gates, outputDirectory);
        WriteSummary(study, baseline, summaries, gates, outputDirectory);
        WriteResultHash(outputDirectory);

        Console.WriteLine(
            $"TL1 Sensor/EW Foundation: {failed} failed gates. " +
            $"Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static void ValidateStudy(
        Tl1SensorEwFoundationStudy study,
        Tl1BaselineCatalog baseline)
    {
        if (!string.Equals(study.SchemaVersion, ExpectedSchemaVersion, StringComparison.Ordinal) ||
            study.MaxTacticalSeparationHexes != 10)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 Sensor/EW foundation schema or tactical range.");
        }

        string[] expectedIds;
        if (string.Equals(study.Id, Cp68StudyId, StringComparison.Ordinal) &&
            study.Checkpoint == 68 && study.Candidates.Count == 6)
        {
            expectedIds = new[]
            {
                "legacy-cp67-control",
                "intimate-1",
                "intimate-2",
                "balanced-1",
                "balanced-2",
                "passive-plus",
            };
        }
        else if ((string.Equals(study.Id, Cp69StudyId, StringComparison.Ordinal) &&
                study.Checkpoint == 69 && study.Candidates.Count == 7) ||
            (string.Equals(study.Id, Cp71StudyId, StringComparison.Ordinal) &&
                study.Checkpoint == 71 && study.Candidates.Count == 7))
        {
            expectedIds = new[]
            {
                "legacy-cp67-control",
                "intimate-1",
                "intimate-2",
                "balanced-0",
                "balanced-1",
                "balanced-2",
                "passive-plus",
            };
        }
        else
        {
            throw new InvalidOperationException(
                "Unexpected TL1 Sensor/EW foundation study identity or shape.");
        }
        if (!expectedIds.SequenceEqual(
                study.Candidates.Select(candidate => candidate.Id),
                StringComparer.Ordinal))
        {
            throw new InvalidOperationException(
                "Unexpected TL1 Sensor/EW candidate ordering.");
        }
        if (study.Candidates.Select(candidate => candidate.Id)
            .Distinct(StringComparer.Ordinal).Count() != study.Candidates.Count)
        {
            throw new InvalidOperationException(
                "TL1 Sensor/EW candidate IDs must be unique.");
        }

        foreach (Tl1SensorEwCandidate candidate in study.Candidates)
        {
            _ = ToProfile(candidate);
            if (!candidate.IsHistoricalControl && candidate.ActivePowerCost != 1)
            {
                throw new InvalidOperationException(
                    $"Candidate '{candidate.Id}' must use one 1-TP normal Active mode before overload.");
            }
            if (string.Equals(study.Id, Cp71StudyId, StringComparison.Ordinal) &&
                (candidate.DiscriminationResistance != 0 ||
                 candidate.PointBlankBurnThroughResistance != 1))
            {
                throw new InvalidOperationException(
                    $"Checkpoint 71 candidate '{candidate.Id}' must use TL1 Discrimination Resistance 0 and same-hex Burn-through +1.");
            }
        }

        _ = baseline.GetInt("kinetic_range");
        _ = baseline.GetInt("energy_range");
        _ = baseline.GetInt("missile_range");
    }

    private static IReadOnlyList<SensorEwSweepRow> BuildRows(
        Tl1SensorEwFoundationStudy study)
    {
        var rows = new List<SensorEwSweepRow>();
        foreach (Tl1SensorEwCandidate candidate in study.Candidates)
        {
            SensorEwFoundationProfile profile = ToProfile(candidate);
            foreach (SensorEwCase testCase in Cases)
            {
                for (int range = 0; range <= study.MaxTacticalSeparationHexes; range++)
                {
                    var context = new SensorEwFoundationEvaluationContext(
                        testCase.ObserverMode,
                        testCase.ObserverOverload,
                        testCase.TargetActive,
                        testCase.TargetActiveOverload,
                        testCase.TargetEcmRating,
                        testCase.ObserverEccmRating,
                        testCase.HasLineOfSight);
                    SensorEwFoundationEvaluationResult result =
                        SensorEwFoundationResolver.Evaluate(
                            range,
                            profile,
                            profile,
                            context);
                    rows.Add(new SensorEwSweepRow(
                        candidate.Id,
                        candidate.IsHistoricalControl,
                        testCase.Id,
                        range,
                        result.BaselineTrack.ToString(),
                        result.EmissionAssistedTrack.ToString(),
                        result.FinalTrack.ToString(),
                        result.EmissionSources.ToString(),
                        result.ObserverFirmRange,
                        result.ObserverApproximateRange,
                        result.ActiveEmissionInterceptRange,
                        result.TargetEcmRating,
                        result.ObserverEccmRating,
                        result.NetEcmRating,
                        result.ObserverDiscriminationResistance,
                        result.BurnThroughResistance,
                        result.EffectiveJammingMargin,
                        result.EcmDegradedFirm,
                        result.LineOfSightBlocked));
                }
            }
        }
        return rows;
    }

    private static IReadOnlyList<SensorEwCandidateSummary> BuildSummaries(
        Tl1SensorEwFoundationStudy study,
        Tl1BaselineCatalog baseline,
        IReadOnlyList<SensorEwSweepRow> rows)
    {
        int kineticRange = baseline.GetInt("kinetic_range");
        int energyRange = baseline.GetInt("energy_range");
        int missileRange = baseline.GetInt("missile_range");
        var summaries = new List<SensorEwCandidateSummary>();

        foreach (Tl1SensorEwCandidate candidate in study.Candidates)
        {
            SensorEwFoundationProfile profile = ToProfile(candidate);
            int activeEmissionMax = MaxRange(
                rows,
                candidate.Id,
                "passive-target-active",
                SensorEwFoundationTrackState.Approximate.ToString());
            int ecmEmissionMax = MaxRange(
                rows,
                candidate.Id,
                "passive-target-ecm",
                SensorEwFoundationTrackState.Approximate.ToString());
            summaries.Add(new SensorEwCandidateSummary(
                candidate.Id,
                candidate.IsHistoricalControl,
                profile.PassiveFirmRange,
                profile.PassiveApproximateRange,
                profile.ActiveFirmRange,
                profile.ActiveApproximateRange,
                profile.ActivePowerCost,
                profile.ActiveOverloadAdditionalPowerCost,
                checked(profile.ActiveFirmRange + profile.ActiveOverloadFirmBonus),
                checked(profile.ActiveApproximateRange + profile.ActiveOverloadApproximateBonus),
                activeEmissionMax,
                ecmEmissionMax,
                profile.ActiveFirmRange >= kineticRange,
                profile.ActiveFirmRange >= energyRange,
                profile.ActiveFirmRange >= missileRange,
                checked(profile.ActiveFirmRange + profile.ActiveOverloadFirmBonus) >= kineticRange,
                checked(profile.ActiveFirmRange + profile.ActiveOverloadFirmBonus) >= energyRange,
                checked(profile.ActiveFirmRange + profile.ActiveOverloadFirmBonus) >= missileRange));
        }
        return summaries;
    }

    private static int MaxRange(
        IReadOnlyList<SensorEwSweepRow> rows,
        string candidateId,
        string caseId,
        string finalTrack)
    {
        int[] matches = rows
            .Where(row => string.Equals(row.CandidateId, candidateId, StringComparison.Ordinal) &&
                string.Equals(row.CaseId, caseId, StringComparison.Ordinal) &&
                string.Equals(row.FinalTrack, finalTrack, StringComparison.Ordinal))
            .Select(row => row.RangeHexes)
            .ToArray();
        return matches.Length == 0 ? -1 : matches.Max();
    }

    private static IReadOnlyList<SensorEwFoundationGate> BuildGates(
        Tl1SensorEwFoundationStudy study,
        IReadOnlyList<SensorEwSweepRow> rows,
        IReadOnlyList<SensorEwCandidateSummary> summaries)
    {
        var gates = new List<SensorEwFoundationGate>();
        void Gate(string id, bool passed, string detail) =>
            gates.Add(new SensorEwFoundationGate(id, passed, detail));

        int expectedRows = checked(
            study.Candidates.Count * Cases.Length *
            (study.MaxTacticalSeparationHexes + 1));
        Gate("row-count", rows.Count == expectedRows,
            $"Expected {expectedRows}; observed {rows.Count}.");

        Tl1SensorEwCandidate legacy = study.Candidates[0];
        Gate("legacy-control-frozen",
            legacy.IsHistoricalControl && legacy.PassiveFirmRange == 3 &&
            legacy.PassiveApproximateRange == 5 && legacy.ActiveFirmRange == 6 &&
            legacy.ActiveApproximateRange == 9 && legacy.ActivePowerCost == 2 &&
            legacy.ActiveOverloadFirmBonus == 2 &&
            legacy.ActiveOverloadApproximateBonus == 2,
            "Historical CP67 control must remain 3/5 passive, 6/9 active at 2 TP, +2/+2 overload.");

        Tl1SensorEwCandidate[] candidates = study.Candidates
            .Where(candidate => !candidate.IsHistoricalControl)
            .ToArray();
        Gate("single-normal-active-mode",
            candidates.All(candidate => candidate.ActivePowerCost == 1 &&
                candidate.ActiveOverloadAdditionalPowerCost == 1),
            "Every forward TL1 candidate must have one 1-TP normal Active mode and one +1-TP overload mode.");
        Gate("reduced-normal-active-envelope",
            candidates.All(candidate => candidate.ActiveFirmRange <= 3 &&
                candidate.ActiveApproximateRange <= 4),
            "Forward candidates intentionally test substantially smaller TL1 normal Active envelopes.");
        Gate("higher-tl-room",
            candidates.All(candidate => candidate.ActiveApproximateRange <
                study.MaxTacticalSeparationHexes),
            "No forward TL1 normal Active candidate may cover the full tactical diameter.");

        Gate("active-emission-approx-only",
            rows.Where(row => row.CaseId == "passive-target-active" &&
                    row.BaselineTrack == SensorEwFoundationTrackState.None.ToString())
                .All(row => row.FinalTrack == SensorEwFoundationTrackState.Approximate.ToString() ||
                    row.FinalTrack == SensorEwFoundationTrackState.None.ToString()),
            "Active emissions may establish Approximate from no baseline track but never Firm by emission alone.");
        Gate("active-emission-range-limited",
            summaries.All(summary => summary.ActiveEmissionApproximateMaxRange ==
                summary.ActiveApproximateRange),
            "Normal Active Sensor emissions must be passively detectable only within the emitting sensor's normal detection envelope.");
        Gate("ecm-emission-mapwide",
            summaries.All(summary => summary.EcmEmissionApproximateMaxRange ==
                study.MaxTacticalSeparationHexes),
            "With LOS, active ECM must announce an Approximate emission contact across the tactical map.");
        Gate("ecm-does-not-erase-detection",
            rows.Where(row => row.CaseId == "active-target-ecm")
                .All(row => row.BaselineTrack == SensorEwFoundationTrackState.None.ToString() ||
                    row.FinalTrack != SensorEwFoundationTrackState.None.ToString()),
            "ECM may spoil Firm discrimination but must not erase an otherwise detected contact.");
        Gate("eccm-preserves-firm",
            rows.Where(row => row.CaseId == "active-target-ecm-eccm")
                .All(row => row.FinalTrack == row.BaselineTrack ||
                    row.BaselineTrack == SensorEwFoundationTrackState.None.ToString()),
            "Matching ECCM must cancel TL1 ECM discrimination pressure without extending the underlying sensor envelope.");
        Gate("sensor-overload-not-eccm",
            rows.Any(row => row.CaseId == "overload-target-ecm" &&
                row.BaselineTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                row.FinalTrack == SensorEwFoundationTrackState.Approximate.ToString() &&
                row.EcmDegradedFirm),
            "At least one overloaded-sensor case must still lose Firm to uncancelled ECM, proving overload is not ECCM.");
        Gate("occlusion-blocks-emissions",
            rows.Where(row => row.CaseId == "passive-target-ecm-occluded")
                .All(row => row.RangeHexes == 0 ||
                    row.FinalTrack == SensorEwFoundationTrackState.None.ToString()),
            "Occlusion must block both ordinary and emission-assisted contact outside the same hex.");
        Gate("weapon-range-can-exceed-firm",
            summaries.Where(summary => !summary.IsHistoricalControl)
                .Any(summary => !summary.NormalActiveFirmAtEnergyMaxRange &&
                    !summary.NormalActiveFirmAtMissileMaxRange),
            "The sweep must include candidates where physical weapon reach exceeds normal Active Firm eligibility.");

        if (string.Equals(study.Id, Cp69StudyId, StringComparison.Ordinal))
        {
            Tl1SensorEwCandidate balanced0 = study.Candidates.Single(candidate =>
                string.Equals(candidate.Id, "balanced-0", StringComparison.Ordinal));
            Gate("balanced-0-passive-awareness",
                balanced0.PassiveFirmRange == 1 &&
                balanced0.PassiveApproximateRange == 3 &&
                balanced0.ActiveFirmRange == 3 &&
                balanced0.ActiveApproximateRange == 4 &&
                balanced0.ActiveOverloadFirmBonus == 1 &&
                balanced0.ActiveOverloadApproximateBonus == 1,
                "Balanced-0 must be 1/3 passive, 3/4 Active, and 4/5 overloaded.");

            Gate("same-hex-ecm-discrimination",
                rows.Where(row => row.CaseId == "passive-target-ecm" &&
                        row.RangeHexes == 0)
                    .All(row =>
                        row.BaselineTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        row.FinalTrack == SensorEwFoundationTrackState.Approximate.ToString() &&
                        row.EcmDegradedFirm &&
                        row.EmissionSources.Contains(
                            SensorEwEmissionSource.ElectronicCountermeasures.ToString(),
                            StringComparison.Ordinal)),
                "Same-hex LOS must not bypass ECM discrimination or ECM emission provenance.");

            Gate("same-hex-eccm-counterplay",
                rows.Where(row => row.CaseId == "active-target-ecm-eccm" &&
                        row.RangeHexes == 0)
                    .All(row =>
                        row.BaselineTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        row.FinalTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        !row.EcmDegradedFirm),
                "Matching ECCM must preserve same-hex Firm discrimination against TL1 ECM.");

            Gate("same-hex-active-emission-provenance",
                rows.Where(row => row.CaseId == "passive-target-active" &&
                        row.RangeHexes == 0)
                    .All(row =>
                        row.FinalTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        row.EmissionSources.Contains(
                            SensorEwEmissionSource.ActiveSensors.ToString(),
                            StringComparison.Ordinal)),
                "Same-hex contacts must retain Active Sensor emission provenance.");

            Gate("same-hex-los-unoccludable",
                rows.Where(row => row.CaseId == "passive-target-ecm-occluded" &&
                        row.RangeHexes == 0)
                    .All(row =>
                        !row.LineOfSightBlocked &&
                        row.FinalTrack == SensorEwFoundationTrackState.Approximate.ToString() &&
                        row.EmissionSources.Contains(
                            SensorEwEmissionSource.ElectronicCountermeasures.ToString(),
                            StringComparison.Ordinal)),
                "Same-hex LOS is an explicit unoccludable guardrail while ECM still resolves normally.");
        }


        if (string.Equals(study.Id, Cp71StudyId, StringComparison.Ordinal))
        {
            Tl1SensorEwCandidate balanced0 = study.Candidates.Single(candidate =>
                string.Equals(candidate.Id, "balanced-0", StringComparison.Ordinal));
            Gate("c71-balanced-0-discrimination-profile",
                balanced0.PassiveFirmRange == 1 &&
                balanced0.PassiveApproximateRange == 3 &&
                balanced0.ActiveFirmRange == 3 &&
                balanced0.ActiveApproximateRange == 4 &&
                balanced0.DiscriminationResistance == 0 &&
                balanced0.PointBlankBurnThroughResistance == 1,
                "Checkpoint 71 Balanced-0 must remain 1/3 passive and 3/4 Active, with intrinsic Discrimination Resistance 0 and same-hex Burn-through +1.");

            Gate("c71-same-hex-burnthrough-preserves-firm",
                rows.Where(row => row.CaseId == "passive-target-ecm" &&
                        row.RangeHexes == 0)
                    .All(row =>
                        row.BaselineTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        row.FinalTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        row.NetEcmRating == 1 &&
                        row.ObserverDiscriminationResistance == 0 &&
                        row.BurnThroughResistance == 1 &&
                        row.EffectiveJammingMargin == 0 &&
                        !row.EcmDegradedFirm),
                "TL1 ECM 1 must not degrade an otherwise Firm same-hex observation when +1 burn-through cancels the jamming margin.");

            Gate("c71-burnthrough-is-range-local",
                rows.Where(row => row.CaseId == "passive-target-ecm" &&
                        row.RangeHexes == 1)
                    .All(row =>
                        row.BaselineTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        row.FinalTrack == SensorEwFoundationTrackState.Approximate.ToString() &&
                        row.BurnThroughResistance == 0 &&
                        row.EffectiveJammingMargin == 1 &&
                        row.EcmDegradedFirm),
                "The provisional TL1 burn-through bonus applies only at range zero; ordinary range-one Firm observations remain vulnerable to uncountered ECM 1.");

            Gate("c71-same-hex-los-unoccludable",
                rows.Where(row => row.CaseId == "passive-target-ecm-occluded" &&
                        row.RangeHexes == 0)
                    .All(row =>
                        !row.LineOfSightBlocked &&
                        row.FinalTrack == SensorEwFoundationTrackState.Firm.ToString() &&
                        row.BurnThroughResistance == 1 &&
                        row.EmissionSources.Contains(
                            SensorEwEmissionSource.ElectronicCountermeasures.ToString(),
                            StringComparison.Ordinal)),
                "Same-hex LOS remains unoccludable, ECM emission provenance remains visible, and burn-through affects discrimination rather than LOS.");
        }

        return gates;
    }

    private static SensorEwFoundationProfile ToProfile(
        Tl1SensorEwCandidate candidate) => new(
        candidate.Id,
        candidate.PassiveFirmRange,
        candidate.PassiveApproximateRange,
        candidate.ActiveFirmRange,
        candidate.ActiveApproximateRange,
        candidate.ActivePowerCost,
        candidate.ActiveOverloadAdditionalPowerCost,
        candidate.ActiveOverloadFirmBonus,
        candidate.ActiveOverloadApproximateBonus,
        candidate.DiscriminationResistance,
        candidate.PointBlankBurnThroughResistance);

    private static void WriteRows(
        IReadOnlyList<SensorEwSweepRow> rows,
        string outputDirectory)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "candidate_id,is_historical_control,case_id,range_hexes,baseline_track,emission_assisted_track,final_track,emission_sources,observer_firm_range,observer_approximate_range,active_emission_intercept_range,target_ecm_rating,observer_eccm_rating,net_ecm_rating,observer_discrimination_resistance,burnthrough_resistance,effective_jamming_margin,ecm_degraded_firm,line_of_sight_blocked");
        foreach (SensorEwSweepRow row in rows)
        {
            builder.AppendLine(string.Join(",",
                Csv(row.CandidateId),
                row.IsHistoricalControl ? "true" : "false",
                Csv(row.CaseId),
                row.RangeHexes.ToString(CultureInfo.InvariantCulture),
                row.BaselineTrack,
                row.EmissionAssistedTrack,
                row.FinalTrack,
                Csv(row.EmissionSources),
                row.ObserverFirmRange.ToString(CultureInfo.InvariantCulture),
                row.ObserverApproximateRange.ToString(CultureInfo.InvariantCulture),
                row.ActiveEmissionInterceptRange.ToString(CultureInfo.InvariantCulture),
                row.TargetEcmRating.ToString(CultureInfo.InvariantCulture),
                row.ObserverEccmRating.ToString(CultureInfo.InvariantCulture),
                row.NetEcmRating.ToString(CultureInfo.InvariantCulture),
                row.ObserverDiscriminationResistance.ToString(CultureInfo.InvariantCulture),
                row.BurnThroughResistance.ToString(CultureInfo.InvariantCulture),
                row.EffectiveJammingMargin.ToString(CultureInfo.InvariantCulture),
                row.EcmDegradedFirm ? "true" : "false",
                row.LineOfSightBlocked ? "true" : "false"));
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "range_sweep.csv"),
            builder.ToString());
    }

    private static void WriteSummaries(
        IReadOnlyList<SensorEwCandidateSummary> summaries,
        string outputDirectory)
    {
        File.WriteAllText(
            Path.Combine(outputDirectory, "candidate_summary.json"),
            JsonSerializer.Serialize(summaries, JsonOptions()));
    }

    private static void WriteGates(
        IReadOnlyList<SensorEwFoundationGate> gates,
        string outputDirectory)
    {
        File.WriteAllText(
            Path.Combine(outputDirectory, "gates.json"),
            JsonSerializer.Serialize(gates, JsonOptions()));
    }

    private static void WriteSummary(
        Tl1SensorEwFoundationStudy study,
        Tl1BaselineCatalog baseline,
        IReadOnlyList<SensorEwCandidateSummary> summaries,
        IReadOnlyList<SensorEwFoundationGate> gates,
        string outputDirectory)
    {
        var payload = new
        {
            study.Id,
            study.Checkpoint,
            CandidateCount = study.Candidates.Count,
            ContextCount = Cases.Length,
            RangeCount = study.MaxTacticalSeparationHexes + 1,
            KineticPhysicalRange = baseline.GetInt("kinetic_range"),
            EnergyPhysicalRange = baseline.GetInt("energy_range"),
            MissilePhysicalRange = baseline.GetInt("missile_range"),
            BlockingBalanceTargets = false,
            ProductionSensorRangesChanged = false,
            CandidateSummaries = summaries,
            FailedGates = gates.Count(gate => !gate.Passed),
        };
        File.WriteAllText(
            Path.Combine(outputDirectory, "summary.json"),
            JsonSerializer.Serialize(payload, JsonOptions()));
    }

    private static void WriteResultHash(string outputDirectory)
    {
        string[] files = Directory.GetFiles(outputDirectory)
            .Where(path => !path.EndsWith("result.sha256", StringComparison.OrdinalIgnoreCase))
            .OrderBy(path => Path.GetFileName(path), StringComparer.Ordinal)
            .ToArray();
        using var sha = SHA256.Create();
        foreach (string file in files)
        {
            byte[] name = Encoding.UTF8.GetBytes(Path.GetFileName(file));
            sha.TransformBlock(name, 0, name.Length, null, 0);
            byte[] data = File.ReadAllBytes(file);
            sha.TransformBlock(data, 0, data.Length, null, 0);
        }
        sha.TransformFinalBlock(Array.Empty<byte>(), 0, 0);
        File.WriteAllText(
            Path.Combine(outputDirectory, "result.sha256"),
            Convert.ToHexString(sha.Hash!).ToLowerInvariant() + Environment.NewLine);
    }

    private static string Csv(string value) =>
        '"' + value.Replace("\"", "\"\"") + '"';

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = true,
    };
}

public sealed record Tl1SensorEwFoundationStudy(
    string SchemaVersion,
    string Id,
    int Checkpoint,
    string Status,
    string Policy,
    int MaxTacticalSeparationHexes,
    IReadOnlyList<Tl1SensorEwCandidate> Candidates);

public sealed record Tl1SensorEwCandidate(
    string Id,
    bool IsHistoricalControl,
    int PassiveFirmRange,
    int PassiveApproximateRange,
    int ActiveFirmRange,
    int ActiveApproximateRange,
    int ActivePowerCost,
    int ActiveOverloadAdditionalPowerCost,
    int ActiveOverloadFirmBonus,
    int ActiveOverloadApproximateBonus,
    string Rationale)
{
    public int DiscriminationResistance { get; init; }
    public int PointBlankBurnThroughResistance { get; init; }
}

internal sealed record SensorEwCase(
    string Id,
    SensorMode ObserverMode,
    bool ObserverOverload,
    bool TargetActive,
    bool TargetActiveOverload,
    int TargetEcmRating,
    int ObserverEccmRating,
    bool HasLineOfSight);

public sealed record SensorEwSweepRow(
    string CandidateId,
    bool IsHistoricalControl,
    string CaseId,
    int RangeHexes,
    string BaselineTrack,
    string EmissionAssistedTrack,
    string FinalTrack,
    string EmissionSources,
    int ObserverFirmRange,
    int ObserverApproximateRange,
    int ActiveEmissionInterceptRange,
    int TargetEcmRating,
    int ObserverEccmRating,
    int NetEcmRating,
    int ObserverDiscriminationResistance,
    int BurnThroughResistance,
    int EffectiveJammingMargin,
    bool EcmDegradedFirm,
    bool LineOfSightBlocked);

public sealed record SensorEwCandidateSummary(
    string CandidateId,
    bool IsHistoricalControl,
    int PassiveFirmRange,
    int PassiveApproximateRange,
    int ActiveFirmRange,
    int ActiveApproximateRange,
    int ActivePowerCost,
    int ActiveOverloadAdditionalPowerCost,
    int OverloadedFirmRange,
    int OverloadedApproximateRange,
    int ActiveEmissionApproximateMaxRange,
    int EcmEmissionApproximateMaxRange,
    bool NormalActiveFirmAtKineticMaxRange,
    bool NormalActiveFirmAtEnergyMaxRange,
    bool NormalActiveFirmAtMissileMaxRange,
    bool OverloadedFirmAtKineticMaxRange,
    bool OverloadedFirmAtEnergyMaxRange,
    bool OverloadedFirmAtMissileMaxRange);

public sealed record SensorEwFoundationGate(
    string Id,
    bool Passed,
    string Detail);
