using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.ScenarioRunner;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1RangeControlCalibrationRunner
{
    private const string SchemaVersion =
        "star-cluster-tl1-range-control-calibration-v1";
    private const int RequiredVariantCount = 75;

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1RangeControlCalibrationStudyDocument study =
            JsonSerializer.Deserialize<Tl1RangeControlCalibrationStudyDocument>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                "TL1 range-control study could not be read.");

        string baselineHash = Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselinePath)))
            .ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine(
            $"TL1 Range Control preflight: {study.Variants.Count} variants, " +
            "scripted Turn-2 relative-range changes, 0-10 hex board separation, " +
            "cumulative Missile Flight travel, sensor/EW reacquisition, scalar " +
            "outrun proofs, Held Main before PDS, and exact reciprocal pairs " +
            "verified; passed.");

        if (preflightOnly)
        {
            return 0;
        }

        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new InvalidOperationException(
                "TL1 range-control calibration trials must be positive.");
        }

        int workers = Math.Clamp(jobs, 1, 24);
        Directory.CreateDirectory(outputDirectory);
        var summaries = new List<VariantSummary>();

        foreach (Tl1PowerEnvelopeVariantDocument variant in study.Variants)
        {
            TrialResult[] results = new TrialResult[trials];
            Parallel.For(
                0,
                trials,
                new ParallelOptions { MaxDegreeOfParallelism = workers },
                index =>
                {
                    var rngA = NewStream(
                        study.MasterSeed,
                        "tl1-range-common-direct-terminal",
                        index,
                        1UL);
                    var rngB = NewStream(
                        study.MasterSeed,
                        "tl1-range-common-direct-terminal",
                        index,
                        2UL);
                    var pdsRngA = NewStream(
                        study.MasterSeed,
                        "tl1-range-common-pds",
                        index,
                        1UL);
                    var pdsRngB = NewStream(
                        study.MasterSeed,
                        "tl1-range-common-pds",
                        index,
                        2UL);
                    var heldRngA = NewStream(
                        study.MasterSeed,
                        "tl1-range-common-held",
                        index,
                        1UL);
                    var heldRngB = NewStream(
                        study.MasterSeed,
                        "tl1-range-common-held",
                        index,
                        2UL);

                    Tl1PowerEnvelopeResult duel =
                        new Tl1PowerEnvelopeSimulator(ToProfile(variant)).Run(
                            rngA.NextD100,
                            rngB.NextD100,
                            pdsRngA.NextD100,
                            pdsRngB.NextD100,
                            heldRngA.NextD100,
                            heldRngB.NextD100);
                    results[index] = TrialResult.From(duel);
                });

            VariantSummary summary = VariantSummary.Create(variant, results);
            summaries.Add(summary);
            Console.WriteLine(
                $"PASS {variant.Id}: A {summary.SideAWinRate:P2}, " +
                $"B {summary.SideBWinRate:P2}, mutual {summary.MutualRate:P2}, " +
                $"unresolved {summary.UnresolvedRate:P2}, turns " +
                $"{summary.MeanTurns:F2}, range " +
                $"{summary.InitialRangeHexes:F0}->{summary.FinalRangeHexes:F0}, " +
                $"Firm A/B {summary.MeanFirmTrackRateA:P1}/" +
                $"{summary.MeanFirmTrackRateB:P1}, exhausted A/B " +
                $"{summary.MeanRangeExhaustedA:F2}/" +
                $"{summary.MeanRangeExhaustedB:F2}, reroutes A/B " +
                $"{summary.MeanMissileReroutesA:F2}/" +
                $"{summary.MeanMissileReroutesB:F2}");
        }

        IReadOnlyList<GateResult> gates = EvaluateGates(study, summaries);
        WriteOutputs(
            study,
            baselineHash,
            trials,
            summaries,
            gates,
            outputDirectory);
        int failed = gates.Count(gate => !gate.Passed);
        Console.WriteLine(
            $"TL1 Range Control Calibration: {summaries.Count} variants, " +
            $"{trials} trials each, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static DeterministicRandomStream NewStream(
        ulong masterSeed,
        string streamId,
        int trialIndex,
        ulong sideId) => new(
        TrialSeedDeriver.Derive(masterSeed, streamId, trialIndex, sideId));

    private static void Validate(
        Tl1RangeControlCalibrationStudyDocument study,
        string baselineHash)
    {
        if (study.SchemaVersion != SchemaVersion)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 range-control calibration schema.");
        }
        if (!string.Equals(
                study.BaselineSha256,
                baselineHash,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "TL1 range-control calibration baseline hash mismatch.");
        }
        if (study.Variants.Count != RequiredVariantCount)
        {
            throw new InvalidOperationException(
                $"TL1 range-control calibration requires exactly " +
                $"{RequiredVariantCount} variants; found {study.Variants.Count}.");
        }
        if (study.Variants
                .Select(variant => variant.Id)
                .Distinct(StringComparer.Ordinal)
                .Count() != study.Variants.Count)
        {
            throw new InvalidOperationException(
                "TL1 range-control variant IDs must be unique.");
        }

        var ids = study.Variants
            .Select(variant => variant.Id)
            .ToHashSet(StringComparer.Ordinal);
        foreach (Tl1PowerEnvelopeVariantDocument variant in study.Variants)
        {
            _ = ToProfile(variant);
            if (string.IsNullOrWhiteSpace(variant.Category))
            {
                throw new InvalidOperationException(
                    $"Variant {variant.Id} requires a category.");
            }
            if (variant.RangeSchedule.Count > 0 &&
                variant.RangeSchedule[0].Turn != 2 &&
                !variant.Id.Contains("late-outward", StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    $"Variant {variant.Id} must apply its scripted change on " +
                    "Turn 2 unless it is the explicit late-change proof.");
            }
            if (!string.IsNullOrWhiteSpace(variant.PairId))
            {
                if (!ids.Contains(variant.PairId))
                {
                    throw new InvalidOperationException(
                        $"Variant {variant.Id} references missing pair " +
                        $"{variant.PairId}.");
                }
                Tl1PowerEnvelopeVariantDocument partner = study.Variants.Single(
                    candidate => candidate.Id == variant.PairId);
                if (!string.Equals(
                        partner.PairId,
                        variant.Id,
                        StringComparison.Ordinal) ||
                    !ExactSideSwap(variant, partner))
                {
                    throw new InvalidOperationException(
                        $"Variant {variant.Id} does not have an exact reciprocal " +
                        "side swap.");
                }
            }
        }

        RequireCategoryCount(study, "static-control", 9);
        RequireCategoryCount(study, "scripted-direct", 12);
        RequireCategoryCount(study, "missile-budget", 16);
        RequireCategoryCount(study, "sensor-ew", 20);
        RequireCategoryCount(study, "interception-timing", 12);
        RequireCategoryCount(study, "scalar-outrun", 6);

        RequireVariant(study, "rc-mb-exact-exhaustion");
        RequireVariant(study, "rc-mb-inward-early-arrival");
        RequireVariant(study, "rc-sensor-passive-lost");
        RequireVariant(study, "rc-sensor-eccm-restores-active1");
        RequireVariant(study, "rc-intercept-held-kinetic-plus-pds-delayed");
        RequireVariant(study, "rc-outrun-target-faster");
        RequireVariant(study, "rc-outrun-missile-faster");
    }

    private static void RequireCategoryCount(
        Tl1RangeControlCalibrationStudyDocument study,
        string category,
        int expected)
    {
        int actual = study.Variants.Count(
            variant => string.Equals(
                variant.Category,
                category,
                StringComparison.Ordinal));
        if (actual != expected)
        {
            throw new InvalidOperationException(
                $"TL1 range-control category {category} requires {expected} " +
                $"variants; found {actual}.");
        }
    }

    private static void RequireVariant(
        Tl1RangeControlCalibrationStudyDocument study,
        string id)
    {
        if (!study.Variants.Any(
                variant => string.Equals(
                    variant.Id,
                    id,
                    StringComparison.Ordinal)))
        {
            throw new InvalidOperationException(
                $"TL1 range-control study is missing required variant {id}.");
        }
    }

    private static bool ExactSideSwap(
        Tl1PowerEnvelopeVariantDocument first,
        Tl1PowerEnvelopeVariantDocument second)
    {
        bool sameCommon =
            first.Category == second.Category &&
            first.ShieldCapacity == second.ShieldCapacity &&
            first.ShieldArmor == second.ShieldArmor &&
            first.BaseShieldRecharge == second.BaseShieldRecharge &&
            first.ArmorProtection == second.ArmorProtection &&
            first.ArmorIntegrity == second.ArmorIntegrity &&
            first.Hull == second.Hull &&
            first.RangeHexes == second.RangeHexes &&
            first.RangePenaltyPerHex == second.RangePenaltyPerHex &&
            first.TurnCap == second.TurnCap &&
            JsonSerializer.Serialize(first.RangeSchedule) ==
                JsonSerializer.Serialize(second.RangeSchedule);
        return sameCommon &&
            JsonSerializer.Serialize(first.SideA) ==
                JsonSerializer.Serialize(second.SideB) &&
            JsonSerializer.Serialize(first.SideB) ==
                JsonSerializer.Serialize(second.SideA);
    }

    private static Tl1PowerEnvelopeProfile ToProfile(
        Tl1PowerEnvelopeVariantDocument variant) => new()
        {
            ShieldCapacity = variant.ShieldCapacity,
            ShieldArmor = variant.ShieldArmor,
            BaseShieldRecharge = variant.BaseShieldRecharge,
            ArmorProtection = variant.ArmorProtection,
            ArmorIntegrity = variant.ArmorIntegrity,
            Hull = variant.Hull,
            RangeHexes = variant.RangeHexes,
            RangePenaltyPerHex = variant.RangePenaltyPerHex,
            TurnCap = variant.TurnCap,
            RangeSchedule = variant.RangeSchedule
                .Select(change => new Tl1RelativeRangeChange(
                    change.Turn,
                    change.RangeHexes))
                .ToArray(),
            SideA = ToSide(variant.SideA),
            SideB = ToSide(variant.SideB),
        };

    private static Tl1PowerEnvelopeSideProfile ToSide(
        Tl1PowerEnvelopeSideDocument side) => new()
        {
            Family = side.Family,
            Doctrine = side.Doctrine,
            Accuracy = side.Accuracy,
            ComputerBonus = side.ComputerBonus,
            Evasive = side.Evasive,
            ReactorOutput = side.ReactorOutput,
            AuxiliaryReactorOutput = side.AuxiliaryReactorOutput,
            Ammunition = side.Ammunition,
            MissileGuidance = side.MissileGuidance,
            MissileDamage = side.MissileDamage,
            MissileShieldPenetration = side.MissileShieldPenetration,
            MissileArmorPenetration = side.MissileArmorPenetration,
            MissileSpeed = side.MissileSpeed,
            MissileRange = side.MissileRange,
            TargetMovePerTurn = side.TargetMovePerTurn,
            MissileLaunchesPerTurn = side.MissileLaunchesPerTurn,
            PdsFamily = side.PdsFamily,
            PdsPowerCost = side.PdsPowerCost,
            PdsReactionCapacity = side.PdsReactionCapacity,
            PdsInterceptionChance = side.PdsInterceptionChance,
            PdsAmmunition = side.PdsAmmunition,
            PdsUnlimitedAmmunition = side.PdsUnlimitedAmmunition,
            SensorTrackGateEnabled = side.SensorTrackGateEnabled,
            PassiveFirmRange = side.PassiveFirmRange,
            ActiveFirmRangeAtOnePower = side.ActiveFirmRangeAtOnePower,
            ActiveFirmRangeAtTwoPower = side.ActiveFirmRangeAtTwoPower,
            SensorPower = side.SensorPower,
            EcmPower = side.EcmPower,
            EccmPower = side.EccmPower,
            ShieldHardenerPower = side.ShieldHardenerPower,
            TacticalShieldRechargePower = side.TacticalShieldRechargePower,
            PowerPriority = side.PowerPriority,
            HeldInterception = side.HeldInterception,
            HeldInterceptionMode = side.HeldInterceptionMode,
            ReactorSafeOverload = side.ReactorSafeOverload,
            EnergySafeBurst = side.EnergySafeBurst,
            SensorSafeOverload = side.SensorSafeOverload,
            EcmSafeOverload = side.EcmSafeOverload,
            EccmSafeOverload = side.EccmSafeOverload,
            ShieldHardenerSafeOverload = side.ShieldHardenerSafeOverload,
            ShieldOvercapacitySafeOverload =
                side.ShieldOvercapacitySafeOverload,
            ShieldRecoverySafeOverload = side.ShieldRecoverySafeOverload,
            SafeOverloadTurnLimit = side.SafeOverloadTurnLimit,
            CombatBatteryCharges = side.CombatBatteryCharges,
            CombatBatteryGain = side.CombatBatteryGain,
            CombatBatteryDoctrine = side.CombatBatteryDoctrine,
            CapacitorCapacity = side.CapacitorCapacity,
            CapacitorStartingCharge = side.CapacitorStartingCharge,
            CapacitorChargeRate = side.CapacitorChargeRate,
            CapacitorDischargeRate = side.CapacitorDischargeRate,
            CapacitorDoctrine = side.CapacitorDoctrine,
        };

    private static IReadOnlyList<GateResult> EvaluateGates(
        Tl1RangeControlCalibrationStudyDocument study,
        IReadOnlyList<VariantSummary> summaries)
    {
        var gates = new List<GateResult>();
        foreach (VariantSummary summary in summaries)
        {
            bool mirror = JsonSerializer.Serialize(summary.Variant.SideA) ==
                JsonSerializer.Serialize(summary.Variant.SideB);
            if (mirror)
            {
                AddMaximumGate(
                    gates,
                    $"{summary.Variant.Id}:mirror-side-bias",
                    Math.Abs(summary.SideAWinRate - summary.SideBWinRate),
                    0.03);
            }
        }

        var evaluatedPairs = new HashSet<string>(StringComparer.Ordinal);
        foreach (Tl1PowerEnvelopeVariantDocument variant in
                 study.Variants.Where(
                     item => !string.IsNullOrWhiteSpace(item.PairId)))
        {
            string pairId = variant.PairId!;
            string pairKey = string.CompareOrdinal(variant.Id, pairId) < 0
                ? $"{variant.Id}|{pairId}"
                : $"{pairId}|{variant.Id}";
            if (!evaluatedPairs.Add(pairKey))
            {
                continue;
            }

            VariantSummary first = summaries.Single(
                summary => summary.Variant.Id == variant.Id);
            VariantSummary second = summaries.Single(
                summary => summary.Variant.Id == pairId);
            AddMaximumGate(
                gates,
                $"{variant.Id}:side-swap-win",
                Math.Abs(first.SideAWinRate - second.SideBWinRate),
                0.03);
            AddMaximumGate(
                gates,
                $"{variant.Id}:side-swap-track",
                Math.Abs(
                    first.MeanFirmTrackRateA -
                    second.MeanFirmTrackRateB),
                0.03);
            AddMaximumGate(
                gates,
                $"{variant.Id}:side-swap-reroute",
                Math.Abs(
                    first.MeanMissileReroutesA -
                    second.MeanMissileReroutesB),
                0.10);
        }

        VariantSummary exactExhaustion = Find(
            summaries,
            "rc-mb-exact-exhaustion");
        AddMinimumGate(
            gates,
            "exact-exhaustion:range-budget-consumed",
            exactExhaustion.MeanRangeExhaustedA,
            0.90);
        AddMaximumGate(
            gates,
            "exact-exhaustion:no-impact",
            exactExhaustion.MeanMissileHitsA,
            0.05);

        VariantSummary passiveLost = Find(
            summaries,
            "rc-sensor-passive-lost");
        AddMaximumGate(
            gates,
            "sensor-step:passive-track-lost",
            passiveLost.MeanFirmTrackRateA,
            0.55);

        VariantSummary eccmRestored = Find(
            summaries,
            "rc-sensor-eccm-restores-active1");
        AddMinimumGate(
            gates,
            "sensor-step:eccm-restores-track",
            eccmRestored.MeanFirmTrackRateA,
            0.90);

        VariantSummary targetFaster = Find(
            summaries,
            "rc-outrun-target-faster");
        AddMinimumGate(
            gates,
            "outrun:target-faster-exhausts-flight",
            targetFaster.MeanRangeExhaustedA,
            0.90);
        AddMaximumGate(
            gates,
            "outrun:target-faster-prevents-hit",
            targetFaster.MeanMissileHitsA,
            0.05);

        VariantSummary missileFaster = Find(
            summaries,
            "rc-outrun-missile-faster");
        AddMinimumGate(
            gates,
            "outrun:missile-faster-reaches-target",
            missileFaster.MeanMissileHitsA,
            0.80);

        VariantSummary heldAndPds = Find(
            summaries,
            "rc-intercept-held-kinetic-plus-pds-delayed");
        AddMinimumGate(
            gates,
            "interception:delayed-held-window-used",
            heldAndPds.MeanHeldAttemptsB,
            0.50);
        AddMinimumGate(
            gates,
            "interception:survivors-reach-pds",
            heldAndPds.MeanPdsAttemptsB,
            0.05);

        return gates;
    }

    private static VariantSummary Find(
        IReadOnlyList<VariantSummary> summaries,
        string id) => summaries.Single(
        summary => string.Equals(
            summary.Variant.Id,
            id,
            StringComparison.Ordinal));

    private static void AddMaximumGate(
        ICollection<GateResult> gates,
        string id,
        double observed,
        double maximum) => gates.Add(
        new GateResult(id, observed <= maximum, observed, "maximum", maximum));

    private static void AddMinimumGate(
        ICollection<GateResult> gates,
        string id,
        double observed,
        double minimum) => gates.Add(
        new GateResult(id, observed >= minimum, observed, "minimum", minimum));

    private static void WriteOutputs(
        Tl1RangeControlCalibrationStudyDocument study,
        string baselineHash,
        int trials,
        IReadOnlyList<VariantSummary> summaries,
        IReadOnlyList<GateResult> gates,
        string outputDirectory)
    {
        var payload = new
        {
            study.Id,
            baselineSha256 = baselineHash,
            trialsPerVariant = trials,
            variants = summaries,
            gates,
            passed = gates.All(gate => gate.Passed),
        };
        File.WriteAllText(
            Path.Combine(outputDirectory, "summary.json"),
            JsonSerializer.Serialize(
                payload,
                new JsonSerializerOptions { WriteIndented = true }) +
            Environment.NewLine);

        var csv = new StringBuilder(
            "variant_id,label,category,trials,side_a_win_rate,side_b_win_rate," +
            "mutual_rate,unresolved_rate,mean_turns,initial_range,final_range," +
            "range_changes,firm_track_rate_a,firm_track_rate_b," +
            "track_denied_rate_a,track_denied_rate_b,mean_launches_a," +
            "mean_launches_b,mean_missile_hits_a,mean_missile_hits_b," +
            "mean_range_exhausted_a,mean_range_exhausted_b," +
            "mean_missile_reroutes_a,mean_missile_reroutes_b," +
            "mean_held_attempts_a,mean_held_attempts_b," +
            "mean_held_intercepts_a,mean_held_intercepts_b," +
            "mean_pds_attempts_a,mean_pds_attempts_b," +
            "mean_pds_intercepts_a,mean_pds_intercepts_b," +
            "mean_hull_a,mean_hull_b\n");
        foreach (VariantSummary summary in summaries)
        {
            csv.Append(C(summary.Variant.Id)).Append(',')
                .Append(C(summary.Variant.Label)).Append(',')
                .Append(C(summary.Variant.Category)).Append(',')
                .Append(summary.Trials).Append(',')
                .Append(F(summary.SideAWinRate)).Append(',')
                .Append(F(summary.SideBWinRate)).Append(',')
                .Append(F(summary.MutualRate)).Append(',')
                .Append(F(summary.UnresolvedRate)).Append(',')
                .Append(F(summary.MeanTurns)).Append(',')
                .Append(F(summary.InitialRangeHexes)).Append(',')
                .Append(F(summary.FinalRangeHexes)).Append(',')
                .Append(F(summary.MeanRangeChangesApplied)).Append(',')
                .Append(F(summary.MeanFirmTrackRateA)).Append(',')
                .Append(F(summary.MeanFirmTrackRateB)).Append(',')
                .Append(F(summary.MeanTrackDeniedRateA)).Append(',')
                .Append(F(summary.MeanTrackDeniedRateB)).Append(',')
                .Append(F(summary.MeanLaunchesA)).Append(',')
                .Append(F(summary.MeanLaunchesB)).Append(',')
                .Append(F(summary.MeanMissileHitsA)).Append(',')
                .Append(F(summary.MeanMissileHitsB)).Append(',')
                .Append(F(summary.MeanRangeExhaustedA)).Append(',')
                .Append(F(summary.MeanRangeExhaustedB)).Append(',')
                .Append(F(summary.MeanMissileReroutesA)).Append(',')
                .Append(F(summary.MeanMissileReroutesB)).Append(',')
                .Append(F(summary.MeanHeldAttemptsA)).Append(',')
                .Append(F(summary.MeanHeldAttemptsB)).Append(',')
                .Append(F(summary.MeanHeldInterceptsA)).Append(',')
                .Append(F(summary.MeanHeldInterceptsB)).Append(',')
                .Append(F(summary.MeanPdsAttemptsA)).Append(',')
                .Append(F(summary.MeanPdsAttemptsB)).Append(',')
                .Append(F(summary.MeanPdsInterceptsA)).Append(',')
                .Append(F(summary.MeanPdsInterceptsB)).Append(',')
                .Append(F(summary.MeanHullA)).Append(',')
                .Append(F(summary.MeanHullB)).Append('\n');
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "variants.csv"),
            csv.ToString());

        var gateCsv = new StringBuilder("gate_id,passed,observed,comparison,limit\n");
        foreach (GateResult gate in gates)
        {
            gateCsv.Append(C(gate.Id)).Append(',')
                .Append(gate.Passed).Append(',')
                .Append(F(gate.Observed)).Append(',')
                .Append(gate.Comparison).Append(',')
                .Append(F(gate.Limit)).Append('\n');
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "gates.csv"),
            gateCsv.ToString());
    }

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    };

    private static string F(double value) =>
        value.ToString("R", CultureInfo.InvariantCulture);

    private static string C(string value) =>
        string.Concat("\"", value.Replace("\"", "\"\""), "\"");

    private sealed record TrialResult(
        Tl1DuelOutcome Outcome,
        int Turns,
        int LaunchesA,
        int LaunchesB,
        int MissileHitsA,
        int MissileHitsB,
        int RangeExhaustedA,
        int RangeExhaustedB,
        int InitialRangeHexes,
        int FinalRangeHexes,
        int RangeChangesApplied,
        int MissileReroutesA,
        int MissileReroutesB,
        int FirmTrackTurnsA,
        int FirmTrackTurnsB,
        int TrackDeniedTurnsA,
        int TrackDeniedTurnsB,
        int HeldAttemptsA,
        int HeldAttemptsB,
        int HeldInterceptsA,
        int HeldInterceptsB,
        int PdsAttemptsA,
        int PdsAttemptsB,
        int PdsInterceptsA,
        int PdsInterceptsB,
        int HullA,
        int HullB)
    {
        public static TrialResult From(Tl1PowerEnvelopeResult duel) => new(
            duel.Outcome,
            duel.Turns,
            duel.LaunchesA,
            duel.LaunchesB,
            duel.MissileHitsA,
            duel.MissileHitsB,
            duel.RangeExhaustedA,
            duel.RangeExhaustedB,
            duel.InitialRangeHexes,
            duel.FinalRangeHexes,
            duel.RangeChangesApplied,
            duel.MissileReroutesA,
            duel.MissileReroutesB,
            duel.FirmTrackTurnsA,
            duel.FirmTrackTurnsB,
            duel.TrackDeniedTurnsA,
            duel.TrackDeniedTurnsB,
            duel.HeldAttemptsA,
            duel.HeldAttemptsB,
            duel.HeldInterceptsA,
            duel.HeldInterceptsB,
            duel.PdsAttemptsA,
            duel.PdsAttemptsB,
            duel.PdsInterceptsA,
            duel.PdsInterceptsB,
            duel.SideA.Defense.CurrentHull,
            duel.SideB.Defense.CurrentHull);
    }

    private sealed record VariantSummary
    {
        public required Tl1PowerEnvelopeVariantDocument Variant { get; init; }
        public int Trials { get; init; }
        public double SideAWinRate { get; init; }
        public double SideBWinRate { get; init; }
        public double MutualRate { get; init; }
        public double UnresolvedRate { get; init; }
        public double MeanTurns { get; init; }
        public double InitialRangeHexes { get; init; }
        public double FinalRangeHexes { get; init; }
        public double MeanRangeChangesApplied { get; init; }
        public double MeanFirmTrackRateA { get; init; }
        public double MeanFirmTrackRateB { get; init; }
        public double MeanTrackDeniedRateA { get; init; }
        public double MeanTrackDeniedRateB { get; init; }
        public double MeanLaunchesA { get; init; }
        public double MeanLaunchesB { get; init; }
        public double MeanMissileHitsA { get; init; }
        public double MeanMissileHitsB { get; init; }
        public double MeanRangeExhaustedA { get; init; }
        public double MeanRangeExhaustedB { get; init; }
        public double MeanMissileReroutesA { get; init; }
        public double MeanMissileReroutesB { get; init; }
        public double MeanHeldAttemptsA { get; init; }
        public double MeanHeldAttemptsB { get; init; }
        public double MeanHeldInterceptsA { get; init; }
        public double MeanHeldInterceptsB { get; init; }
        public double MeanPdsAttemptsA { get; init; }
        public double MeanPdsAttemptsB { get; init; }
        public double MeanPdsInterceptsA { get; init; }
        public double MeanPdsInterceptsB { get; init; }
        public double MeanHullA { get; init; }
        public double MeanHullB { get; init; }

        public static VariantSummary Create(
            Tl1PowerEnvelopeVariantDocument variant,
            IReadOnlyList<TrialResult> results) => new()
        {
            Variant = variant,
            Trials = results.Count,
            SideAWinRate = Rate(results, Tl1DuelOutcome.SideAWins),
            SideBWinRate = Rate(results, Tl1DuelOutcome.SideBWins),
            MutualRate = Rate(results, Tl1DuelOutcome.MutualDestruction),
            UnresolvedRate = Rate(results, Tl1DuelOutcome.Unresolved),
            MeanTurns = Avg(results, result => result.Turns),
            InitialRangeHexes = Avg(results, result => result.InitialRangeHexes),
            FinalRangeHexes = Avg(results, result => result.FinalRangeHexes),
            MeanRangeChangesApplied = Avg(
                results,
                result => result.RangeChangesApplied),
            MeanFirmTrackRateA = Avg(
                results,
                result => Ratio(
                    result.FirmTrackTurnsA,
                    result.FirmTrackTurnsA + result.TrackDeniedTurnsA)),
            MeanFirmTrackRateB = Avg(
                results,
                result => Ratio(
                    result.FirmTrackTurnsB,
                    result.FirmTrackTurnsB + result.TrackDeniedTurnsB)),
            MeanTrackDeniedRateA = Avg(
                results,
                result => Ratio(
                    result.TrackDeniedTurnsA,
                    result.FirmTrackTurnsA + result.TrackDeniedTurnsA)),
            MeanTrackDeniedRateB = Avg(
                results,
                result => Ratio(
                    result.TrackDeniedTurnsB,
                    result.FirmTrackTurnsB + result.TrackDeniedTurnsB)),
            MeanLaunchesA = Avg(results, result => result.LaunchesA),
            MeanLaunchesB = Avg(results, result => result.LaunchesB),
            MeanMissileHitsA = Avg(results, result => result.MissileHitsA),
            MeanMissileHitsB = Avg(results, result => result.MissileHitsB),
            MeanRangeExhaustedA = Avg(
                results,
                result => result.RangeExhaustedA),
            MeanRangeExhaustedB = Avg(
                results,
                result => result.RangeExhaustedB),
            MeanMissileReroutesA = Avg(
                results,
                result => result.MissileReroutesA),
            MeanMissileReroutesB = Avg(
                results,
                result => result.MissileReroutesB),
            MeanHeldAttemptsA = Avg(results, result => result.HeldAttemptsA),
            MeanHeldAttemptsB = Avg(results, result => result.HeldAttemptsB),
            MeanHeldInterceptsA = Avg(
                results,
                result => result.HeldInterceptsA),
            MeanHeldInterceptsB = Avg(
                results,
                result => result.HeldInterceptsB),
            MeanPdsAttemptsA = Avg(results, result => result.PdsAttemptsA),
            MeanPdsAttemptsB = Avg(results, result => result.PdsAttemptsB),
            MeanPdsInterceptsA = Avg(results, result => result.PdsInterceptsA),
            MeanPdsInterceptsB = Avg(results, result => result.PdsInterceptsB),
            MeanHullA = Avg(results, result => result.HullA),
            MeanHullB = Avg(results, result => result.HullB),
        };

        private static double Rate(
            IReadOnlyList<TrialResult> results,
            Tl1DuelOutcome outcome) =>
            results.Count(result => result.Outcome == outcome) /
            (double)results.Count;

        private static double Avg(
            IReadOnlyList<TrialResult> results,
            Func<TrialResult, double> selector) => results.Average(selector);

        private static double Ratio(int numerator, int denominator) =>
            denominator <= 0 ? 0.0 : numerator / (double)denominator;
    }

    private sealed record GateResult(
        string Id,
        bool Passed,
        double Observed,
        string Comparison,
        double Limit);
}
