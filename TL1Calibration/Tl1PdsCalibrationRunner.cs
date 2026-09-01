using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.ScenarioRunner;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1PdsCalibrationRunner
{
    private const string SchemaVersion = "star-cluster-tl1-pds-calibration-v1";

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1PdsCalibrationStudyDocument study =
            JsonSerializer.Deserialize<Tl1PdsCalibrationStudyDocument>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                    "TL1 PDS calibration study could not be read.");

        string baselineHash = Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselinePath)))
            .ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine(
            $"TL1 PDS Calibration preflight: {study.Variants.Count} variants, " +
            "baseline hash and PDS contracts verified; passed.");

        if (preflightOnly)
        {
            return 0;
        }

        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new InvalidOperationException(
                "TL1 PDS calibration trials must be positive.");
        }

        int workers = Math.Clamp(jobs, 1, 24);
        Directory.CreateDirectory(outputDirectory);
        var summaries = new List<VariantSummary>();

        foreach (Tl1WeaponMatrixVariantDocument variant in study.Variants)
        {
            TrialResult[] results = new TrialResult[trials];
            Parallel.For(
                0,
                trials,
                new ParallelOptions { MaxDegreeOfParallelism = workers },
                index =>
                {
                    var rngA = new DeterministicRandomStream(
                        TrialSeedDeriver.Derive(
                            study.MasterSeed,
                            "tl1-pds-common-direct-terminal",
                            index,
                            1UL));
                    var rngB = new DeterministicRandomStream(
                        TrialSeedDeriver.Derive(
                            study.MasterSeed,
                            "tl1-pds-common-direct-terminal",
                            index,
                            2UL));
                    var pdsRngA = new DeterministicRandomStream(
                        TrialSeedDeriver.Derive(
                            study.MasterSeed,
                            "tl1-pds-common-interception",
                            index,
                            1UL));
                    var pdsRngB = new DeterministicRandomStream(
                        TrialSeedDeriver.Derive(
                            study.MasterSeed,
                            "tl1-pds-common-interception",
                            index,
                            2UL));

                    Tl1WeaponMatrixResult duel =
                        new Tl1WeaponMatrixSimulator(ToProfile(variant)).Run(
                            rngA.NextD100,
                            rngB.NextD100,
                            pdsRngA.NextD100,
                            pdsRngB.NextD100);
                    results[index] = TrialResult.From(duel, variant);
                });

            VariantSummary summary = VariantSummary.Create(variant, results);
            summaries.Add(summary);
            Console.WriteLine(
                $"PASS {variant.Id}: A {summary.SideAWinRate:P2}, " +
                $"B {summary.SideBWinRate:P2}, mutual {summary.MutualRate:P2}, " +
                $"unresolved {summary.UnresolvedRate:P2}, " +
                $"mean turns {summary.MeanTurns:F2}, " +
                $"PDS attempts A/B {summary.MeanPdsAttemptsA:F1}/" +
                $"{summary.MeanPdsAttemptsB:F1}, intercepts A/B " +
                $"{summary.MeanPdsInterceptsA:F1}/" +
                $"{summary.MeanPdsInterceptsB:F1}");
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
            $"TL1 PDS Calibration: {summaries.Count} variants, {trials} trials " +
            $"each, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static void Validate(
        Tl1PdsCalibrationStudyDocument study,
        string baselineHash)
    {
        if (study.SchemaVersion != SchemaVersion)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 PDS calibration schema.");
        }

        if (!string.Equals(
                study.BaselineSha256,
                baselineHash,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "TL1 PDS calibration baseline hash mismatch.");
        }

        if (study.Variants.Count != 59)
        {
            throw new InvalidOperationException(
                $"TL1 PDS calibration requires exactly 59 variants; found " +
                $"{study.Variants.Count}.");
        }

        if (study.Variants
                .Select(variant => variant.Id)
                .Distinct(StringComparer.Ordinal)
                .Count() != study.Variants.Count)
        {
            throw new InvalidOperationException(
                "TL1 PDS calibration variant IDs must be unique.");
        }

        var ids = study.Variants
            .Select(variant => variant.Id)
            .ToHashSet(StringComparer.Ordinal);
        foreach (Tl1WeaponMatrixVariantDocument variant in study.Variants)
        {
            _ = ToProfile(variant);
            if (!string.IsNullOrWhiteSpace(variant.PairId) &&
                !ids.Contains(variant.PairId))
            {
                throw new InvalidOperationException(
                    $"Variant {variant.Id} references missing pair " +
                    $"{variant.PairId}.");
            }

            if (!string.IsNullOrWhiteSpace(variant.PairId))
            {
                Tl1WeaponMatrixVariantDocument partner = study.Variants.Single(
                    candidate => candidate.Id == variant.PairId);
                if (!string.Equals(
                        partner.PairId,
                        variant.Id,
                        StringComparison.Ordinal))
                {
                    throw new InvalidOperationException(
                        $"Variant {variant.Id} does not have a reciprocal pair.");
                }
            }
        }

        RequireVariant(study, "pds-e-v-m-control-r2");
        RequireVariant(study, "pds-k-v-saturation-r2");
        RequireVariant(study, "pds-kpds-v-m-r2");
        RequireVariant(study, "pds-ammpds-v-m-r2");
        RequireVariant(study, "pds-epds-v-m-r2");
        RequireVariant(study, "pds-kpds-v-saturation-r2");
        RequireVariant(study, "pds-kpds-reaction2-r2");
        RequireVariant(study, "pds-kpds-unpowered-r2");
        RequireVariant(study, "pds-mm-both-kpds-r2");
    }

    private static void RequireVariant(
        Tl1PdsCalibrationStudyDocument study,
        string id)
    {
        if (!study.Variants.Any(
                variant => string.Equals(
                    variant.Id,
                    id,
                    StringComparison.Ordinal)))
        {
            throw new InvalidOperationException(
                $"TL1 PDS calibration is missing required variant {id}.");
        }
    }

    private static Tl1WeaponMatrixProfile ToProfile(
        Tl1WeaponMatrixVariantDocument variant) =>
        new(
            variant.ShieldCapacity,
            variant.ShieldArmor,
            variant.BaseShieldRecharge,
            variant.ArmorProtection,
            variant.ArmorIntegrity,
            variant.Hull,
            variant.RangeHexes,
            variant.RangePenaltyPerHex,
            variant.TurnCap,
            ToSide(variant.SideA),
            ToSide(variant.SideB));

    private static Tl1WeaponMatrixSideProfile ToSide(
        Tl1WeaponMatrixSideDocument side) =>
        new(
            side.Family,
            side.Doctrine,
            side.Accuracy,
            side.ComputerBonus,
            side.Evasive,
            side.ReactorOutput,
            side.Ammunition,
            side.MissileGuidance,
            side.MissileDamage,
            side.MissileShieldPenetration,
            side.MissileArmorPenetration,
            side.MissileSpeed,
            side.MissileRange,
            side.TargetMovePerTurn,
            side.MissileLaunchesPerTurn,
            side.PdsFamily,
            side.PdsPowerCost,
            side.PdsReactionCapacity,
            side.PdsInterceptionChance,
            side.PdsAmmunition,
            side.PdsUnlimitedAmmunition,
            side.SensorTrackGateEnabled,
            side.PassiveFirmRange,
            side.ActiveFirmRangeAtOnePower,
            side.ActiveFirmRangeAtTwoPower,
            side.SensorPower,
            side.EcmPower,
            side.EccmPower,
            side.ShieldHardenerPower,
            side.TacticalShieldRechargePower,
            side.ShieldBatteryCharges,
            side.ShieldBatteryRestore);

    private static IReadOnlyList<GateResult> EvaluateGates(
        Tl1PdsCalibrationStudyDocument study,
        IReadOnlyList<VariantSummary> summaries)
    {
        var gates = new List<GateResult>();
        foreach (VariantSummary summary in summaries)
        {
            bool mirror = JsonSerializer.Serialize(summary.Variant.SideA) ==
                JsonSerializer.Serialize(summary.Variant.SideB);
            if (mirror)
            {
                double delta = Math.Abs(
                    summary.SideAWinRate - summary.SideBWinRate);
                gates.Add(new GateResult(
                    $"{summary.Variant.Id}:mirror-side-bias",
                    delta <= 0.03,
                    delta,
                    0.03));
            }
        }

        var evaluatedPairs = new HashSet<string>(StringComparer.Ordinal);
        foreach (Tl1WeaponMatrixVariantDocument variant in
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
            double winDelta = Math.Abs(
                first.SideAWinRate - second.SideBWinRate);
            double interceptDelta = Math.Abs(
                first.MeanPdsInterceptsA - second.MeanPdsInterceptsB);
            gates.Add(new GateResult(
                $"{variant.Id}:side-swap-win",
                winDelta <= 0.03,
                winDelta,
                0.03));
            gates.Add(new GateResult(
                $"{variant.Id}:side-swap-intercepts",
                interceptDelta <= 0.15,
                interceptDelta,
                0.15));
        }

        return gates;
    }

    private static void WriteOutputs(
        Tl1PdsCalibrationStudyDocument study,
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
            "variant_id,label,trials,side_a_win_rate,side_b_win_rate," +
            "mutual_rate,unresolved_rate,mean_turns,p50_turns,p90_turns," +
            "mean_launches_a,mean_launches_b,mean_missile_hits_a," +
            "mean_missile_hits_b,mean_terminal_attacks_a," +
            "mean_terminal_attacks_b,mean_pds_attempts_a," +
            "mean_pds_attempts_b,mean_pds_intercepts_a," +
            "mean_pds_intercepts_b,mean_pds_entry_attempts_a," +
            "mean_pds_entry_attempts_b,mean_pds_preattack_attempts_a," +
            "mean_pds_preattack_attempts_b,mean_pds_ammo_used_a," +
            "mean_pds_ammo_used_b,mean_pds_power_a,mean_pds_power_b," +
            "mean_hull_a,mean_hull_b\n");

        foreach (VariantSummary summary in summaries)
        {
            csv.Append(C(summary.Variant.Id)).Append(',')
                .Append(C(summary.Variant.Label)).Append(',')
                .Append(summary.Trials).Append(',')
                .Append(F(summary.SideAWinRate)).Append(',')
                .Append(F(summary.SideBWinRate)).Append(',')
                .Append(F(summary.MutualRate)).Append(',')
                .Append(F(summary.UnresolvedRate)).Append(',')
                .Append(F(summary.MeanTurns)).Append(',')
                .Append(summary.P50Turns).Append(',')
                .Append(summary.P90Turns).Append(',')
                .Append(F(summary.MeanLaunchesA)).Append(',')
                .Append(F(summary.MeanLaunchesB)).Append(',')
                .Append(F(summary.MeanMissileHitsA)).Append(',')
                .Append(F(summary.MeanMissileHitsB)).Append(',')
                .Append(F(summary.MeanTerminalAttacksA)).Append(',')
                .Append(F(summary.MeanTerminalAttacksB)).Append(',')
                .Append(F(summary.MeanPdsAttemptsA)).Append(',')
                .Append(F(summary.MeanPdsAttemptsB)).Append(',')
                .Append(F(summary.MeanPdsInterceptsA)).Append(',')
                .Append(F(summary.MeanPdsInterceptsB)).Append(',')
                .Append(F(summary.MeanPdsEntryAttemptsA)).Append(',')
                .Append(F(summary.MeanPdsEntryAttemptsB)).Append(',')
                .Append(F(summary.MeanPdsPreAttackAttemptsA)).Append(',')
                .Append(F(summary.MeanPdsPreAttackAttemptsB)).Append(',')
                .Append(F(summary.MeanPdsAmmoUsedA)).Append(',')
                .Append(F(summary.MeanPdsAmmoUsedB)).Append(',')
                .Append(F(summary.MeanPdsPowerA)).Append(',')
                .Append(F(summary.MeanPdsPowerB)).Append(',')
                .Append(F(summary.MeanHullA)).Append(',')
                .Append(F(summary.MeanHullB)).Append('\n');
        }

        File.WriteAllText(
            Path.Combine(outputDirectory, "variants.csv"),
            csv.ToString());
        File.WriteAllText(
            Path.Combine(outputDirectory, "gates.csv"),
            "gate_id,passed,observed,limit\n" +
            string.Join(
                "\n",
                gates.Select(
                    gate => $"{C(gate.Id)},{gate.Passed}," +
                    $"{F(gate.Observed)},{F(gate.Limit)}")) +
            "\n");
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
        int TerminalAttacksA,
        int TerminalAttacksB,
        int PdsAttemptsA,
        int PdsAttemptsB,
        int PdsInterceptsA,
        int PdsInterceptsB,
        int PdsEntryAttemptsA,
        int PdsEntryAttemptsB,
        int PdsPreAttackAttemptsA,
        int PdsPreAttackAttemptsB,
        int PdsAmmoUsedA,
        int PdsAmmoUsedB,
        int PdsPowerA,
        int PdsPowerB,
        int HullA,
        int HullB)
    {
        public static TrialResult From(
            Tl1WeaponMatrixResult duel,
            Tl1WeaponMatrixVariantDocument variant) =>
            new(
                duel.Outcome,
                duel.Turns,
                duel.LaunchesA,
                duel.LaunchesB,
                duel.MissileHitsA,
                duel.MissileHitsB,
                duel.MissilesReachedGuidanceA,
                duel.MissilesReachedGuidanceB,
                duel.PdsAttemptsA,
                duel.PdsAttemptsB,
                duel.PdsInterceptsA,
                duel.PdsInterceptsB,
                duel.PdsEntryAttemptsA,
                duel.PdsEntryAttemptsB,
                duel.PdsPreAttackAttemptsA,
                duel.PdsPreAttackAttemptsB,
                PdsAmmoUsed(variant.SideA, duel.PdsAmmunitionA),
                PdsAmmoUsed(variant.SideB, duel.PdsAmmunitionB),
                duel.PdsPowerCommittedA,
                duel.PdsPowerCommittedB,
                duel.SideA.Defense.CurrentHull,
                duel.SideB.Defense.CurrentHull);

        private static int PdsAmmoUsed(
            Tl1WeaponMatrixSideDocument side,
            int remaining) =>
            side.PdsUnlimitedAmmunition
                ? 0
                : Math.Max(0, side.PdsAmmunition - remaining);
    }

    private sealed record VariantSummary(
        Tl1WeaponMatrixVariantDocument Variant,
        int Trials,
        double SideAWinRate,
        double SideBWinRate,
        double MutualRate,
        double UnresolvedRate,
        double MeanTurns,
        int P50Turns,
        int P90Turns,
        double MeanLaunchesA,
        double MeanLaunchesB,
        double MeanMissileHitsA,
        double MeanMissileHitsB,
        double MeanTerminalAttacksA,
        double MeanTerminalAttacksB,
        double MeanPdsAttemptsA,
        double MeanPdsAttemptsB,
        double MeanPdsInterceptsA,
        double MeanPdsInterceptsB,
        double MeanPdsEntryAttemptsA,
        double MeanPdsEntryAttemptsB,
        double MeanPdsPreAttackAttemptsA,
        double MeanPdsPreAttackAttemptsB,
        double MeanPdsAmmoUsedA,
        double MeanPdsAmmoUsedB,
        double MeanPdsPowerA,
        double MeanPdsPowerB,
        double MeanHullA,
        double MeanHullB)
    {
        public static VariantSummary Create(
            Tl1WeaponMatrixVariantDocument variant,
            TrialResult[] results)
        {
            int count = results.Length;
            int[] turns = results
                .Select(result => result.Turns)
                .OrderBy(turn => turn)
                .ToArray();
            return new VariantSummary(
                Variant: variant,
                Trials: count,
                SideAWinRate: results.Count(
                    result => result.Outcome == Tl1DuelOutcome.SideAWins) /
                    (double)count,
                SideBWinRate: results.Count(
                    result => result.Outcome == Tl1DuelOutcome.SideBWins) /
                    (double)count,
                MutualRate: results.Count(
                    result => result.Outcome ==
                        Tl1DuelOutcome.MutualDestruction) /
                    (double)count,
                UnresolvedRate: results.Count(
                    result => result.Outcome == Tl1DuelOutcome.Unresolved) /
                    (double)count,
                MeanTurns: results.Average(result => result.Turns),
                P50Turns: turns[(count - 1) / 2],
                P90Turns: turns[(int)Math.Floor((count - 1) * 0.90)],
                MeanLaunchesA: results.Average(result => result.LaunchesA),
                MeanLaunchesB: results.Average(result => result.LaunchesB),
                MeanMissileHitsA: results.Average(result => result.MissileHitsA),
                MeanMissileHitsB: results.Average(result => result.MissileHitsB),
                MeanTerminalAttacksA: results.Average(
                    result => result.TerminalAttacksA),
                MeanTerminalAttacksB: results.Average(
                    result => result.TerminalAttacksB),
                MeanPdsAttemptsA: results.Average(result => result.PdsAttemptsA),
                MeanPdsAttemptsB: results.Average(result => result.PdsAttemptsB),
                MeanPdsInterceptsA: results.Average(
                    result => result.PdsInterceptsA),
                MeanPdsInterceptsB: results.Average(
                    result => result.PdsInterceptsB),
                MeanPdsEntryAttemptsA: results.Average(
                    result => result.PdsEntryAttemptsA),
                MeanPdsEntryAttemptsB: results.Average(
                    result => result.PdsEntryAttemptsB),
                MeanPdsPreAttackAttemptsA: results.Average(
                    result => result.PdsPreAttackAttemptsA),
                MeanPdsPreAttackAttemptsB: results.Average(
                    result => result.PdsPreAttackAttemptsB),
                MeanPdsAmmoUsedA: results.Average(result => result.PdsAmmoUsedA),
                MeanPdsAmmoUsedB: results.Average(result => result.PdsAmmoUsedB),
                MeanPdsPowerA: results.Average(result => result.PdsPowerA),
                MeanPdsPowerB: results.Average(result => result.PdsPowerB),
                MeanHullA: results.Average(result => result.HullA),
                MeanHullB: results.Average(result => result.HullB));
        }
    }

    private sealed record GateResult(
        string Id,
        bool Passed,
        double Observed,
        double Limit);
}
