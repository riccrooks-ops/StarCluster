using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.ScenarioRunner;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1WeaponMatrixRunner
{
    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1WeaponMatrixStudyDocument study = JsonSerializer.Deserialize<Tl1WeaponMatrixStudyDocument>(
            File.ReadAllText(studyPath),
            JsonOptions()) ?? throw new InvalidOperationException("TL1 weapon matrix study could not be read.");

        string baselineHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(baselinePath))).ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine($"TL1 Weapon Matrix preflight: {study.Variants.Count} variants, baseline hash verified; passed.");

        if (preflightOnly)
        {
            return 0;
        }

        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new InvalidOperationException("TL1 weapon matrix trials must be positive.");
        }

        int workers = Math.Clamp(jobs, 1, 24);
        Directory.CreateDirectory(outputDirectory);
        var summaries = new List<VariantSummary>();

        foreach (Tl1WeaponMatrixVariantDocument variant in study.Variants)
        {
            TrialResult[] results = new TrialResult[trials];
            Parallel.For(0, trials, new ParallelOptions { MaxDegreeOfParallelism = workers }, index =>
            {
                ulong seedA = TrialSeedDeriver.Derive(study.MasterSeed, "tl1-weapon-matrix-common", index, 1UL);
                ulong seedB = TrialSeedDeriver.Derive(study.MasterSeed, "tl1-weapon-matrix-common", index, 2UL);
                var rngA = new DeterministicRandomStream(seedA);
                var rngB = new DeterministicRandomStream(seedB);
                Tl1WeaponMatrixResult duel = new Tl1WeaponMatrixSimulator(ToProfile(variant)).Run(rngA.NextD100, rngB.NextD100);
                results[index] = TrialResult.From(duel, variant);
            });

            VariantSummary summary = VariantSummary.Create(variant, results);
            summaries.Add(summary);
            Console.WriteLine(
                $"PASS {variant.Id}: A {summary.SideAWinRate:P2}, B {summary.SideBWinRate:P2}, " +
                $"mutual {summary.MutualRate:P2}, unresolved {summary.UnresolvedRate:P2}, " +
                $"mean turns {summary.MeanTurns:F2}, launches A/B {summary.MeanLaunchesA:F1}/{summary.MeanLaunchesB:F1}");
        }

        IReadOnlyList<GateResult> gates = EvaluateGates(study, summaries);
        WriteOutputs(study, baselineHash, trials, summaries, gates, outputDirectory);
        int failed = gates.Count(gate => !gate.Passed);
        Console.WriteLine(
            $"TL1 Weapon Matrix: {summaries.Count} variants, {trials} trials each, {failed} failed gates. " +
            $"Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static void Validate(Tl1WeaponMatrixStudyDocument study, string baselineHash)
    {
        if (study.SchemaVersion != "star-cluster-tl1-weapon-matrix-v1")
        {
            throw new InvalidOperationException("Unexpected TL1 weapon matrix schema.");
        }

        if (!string.Equals(study.BaselineSha256, baselineHash, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("TL1 weapon matrix baseline hash mismatch.");
        }

        if (study.Variants.Count < 30)
        {
            throw new InvalidOperationException("TL1 weapon matrix requires at least 30 variants.");
        }

        if (study.Variants.Select(variant => variant.Id).Distinct(StringComparer.Ordinal).Count() != study.Variants.Count)
        {
            throw new InvalidOperationException("TL1 weapon matrix variant IDs must be unique.");
        }

        var ids = study.Variants.Select(variant => variant.Id).ToHashSet(StringComparer.Ordinal);
        foreach (Tl1WeaponMatrixVariantDocument variant in study.Variants)
        {
            _ = ToProfile(variant);
            if (!string.IsNullOrWhiteSpace(variant.PairId) && !ids.Contains(variant.PairId))
            {
                throw new InvalidOperationException($"Variant {variant.Id} references missing pair {variant.PairId}.");
            }
        }
    }

    private static Tl1WeaponMatrixProfile ToProfile(Tl1WeaponMatrixVariantDocument variant) => new(
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

    private static Tl1WeaponMatrixSideProfile ToSide(Tl1WeaponMatrixSideDocument side) => new(
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
        Tl1WeaponMatrixStudyDocument study,
        IReadOnlyList<VariantSummary> summaries)
    {
        var gates = new List<GateResult>();
        foreach (VariantSummary summary in summaries)
        {
            bool mirror = JsonSerializer.Serialize(summary.Variant.SideA) == JsonSerializer.Serialize(summary.Variant.SideB);
            if (mirror)
            {
                double delta = Math.Abs(summary.SideAWinRate - summary.SideBWinRate);
                gates.Add(new GateResult($"{summary.Variant.Id}:mirror-side-bias", delta <= 0.03, delta, 0.03));
            }
        }

        var evaluatedPairs = new HashSet<string>(StringComparer.Ordinal);
        foreach (Tl1WeaponMatrixVariantDocument variant in study.Variants.Where(v => !string.IsNullOrWhiteSpace(v.PairId)))
        {
            string pairKey = string.CompareOrdinal(variant.Id, variant.PairId) < 0
                ? $"{variant.Id}|{variant.PairId}"
                : $"{variant.PairId}|{variant.Id}";
            if (!evaluatedPairs.Add(pairKey))
            {
                continue;
            }

            VariantSummary first = summaries.Single(summary => summary.Variant.Id == variant.Id);
            VariantSummary second = summaries.Single(summary => summary.Variant.Id == variant.PairId);
            double delta = Math.Abs(first.SideAWinRate - second.SideBWinRate);
            gates.Add(new GateResult($"{variant.Id}:side-swap", delta <= 0.03, delta, 0.03));
        }

        return gates;
    }

    private static void WriteOutputs(
        Tl1WeaponMatrixStudyDocument study,
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
            JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);

        var csv = new StringBuilder(
            "variant_id,label,trials,side_a_win_rate,side_b_win_rate,mutual_rate,unresolved_rate," +
            "mean_turns,p50_turns,p90_turns,mean_direct_hits_a,mean_direct_hits_b,mean_launches_a,mean_launches_b," +
            "mean_missile_hits_a,mean_missile_hits_b,mean_range_exhausted_a,mean_range_exhausted_b," +
            "mean_hull_a,mean_hull_b,mean_ammo_used_a,mean_ammo_used_b\n");

        foreach (VariantSummary summary in summaries)
        {
            csv.Append(C(summary.Variant.Id)).Append(',').Append(C(summary.Variant.Label)).Append(',').Append(summary.Trials).Append(',')
                .Append(F(summary.SideAWinRate)).Append(',').Append(F(summary.SideBWinRate)).Append(',')
                .Append(F(summary.MutualRate)).Append(',').Append(F(summary.UnresolvedRate)).Append(',')
                .Append(F(summary.MeanTurns)).Append(',').Append(summary.P50Turns).Append(',').Append(summary.P90Turns).Append(',')
                .Append(F(summary.MeanDirectHitsA)).Append(',').Append(F(summary.MeanDirectHitsB)).Append(',')
                .Append(F(summary.MeanLaunchesA)).Append(',').Append(F(summary.MeanLaunchesB)).Append(',')
                .Append(F(summary.MeanMissileHitsA)).Append(',').Append(F(summary.MeanMissileHitsB)).Append(',')
                .Append(F(summary.MeanRangeExhaustedA)).Append(',').Append(F(summary.MeanRangeExhaustedB)).Append(',')
                .Append(F(summary.MeanHullA)).Append(',').Append(F(summary.MeanHullB)).Append(',')
                .Append(F(summary.MeanAmmoUsedA)).Append(',').Append(F(summary.MeanAmmoUsedB)).Append('\n');
        }

        File.WriteAllText(Path.Combine(outputDirectory, "variants.csv"), csv.ToString());
        File.WriteAllText(
            Path.Combine(outputDirectory, "gates.csv"),
            "gate_id,passed,observed,limit\n" +
            string.Join("\n", gates.Select(gate => $"{C(gate.Id)},{gate.Passed},{F(gate.Observed)},{F(gate.Limit)}")) + "\n");
    }

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    };

    private static string F(double value) => value.ToString("R", CultureInfo.InvariantCulture);
    private static string C(string value) => string.Concat("\"", value.Replace("\"", "\"\""), "\"");

    private sealed record TrialResult(
        Tl1DuelOutcome Outcome,
        int Turns,
        int DirectHitsA,
        int DirectHitsB,
        int LaunchesA,
        int LaunchesB,
        int MissileHitsA,
        int MissileHitsB,
        int RangeExhaustedA,
        int RangeExhaustedB,
        int HullA,
        int HullB,
        int AmmoUsedA,
        int AmmoUsedB)
    {
        public static TrialResult From(Tl1WeaponMatrixResult duel, Tl1WeaponMatrixVariantDocument variant) => new(
            duel.Outcome,
            duel.Turns,
            duel.HitsA,
            duel.HitsB,
            duel.LaunchesA,
            duel.LaunchesB,
            duel.MissileHitsA,
            duel.MissileHitsB,
            duel.RangeExhaustedA,
            duel.RangeExhaustedB,
            duel.SideA.Defense.CurrentHull,
            duel.SideB.Defense.CurrentHull,
            variant.SideA.Family.Equals("energy", StringComparison.OrdinalIgnoreCase)
                ? 0
                : Math.Max(0, variant.SideA.Ammunition - duel.AmmunitionA),
            variant.SideB.Family.Equals("energy", StringComparison.OrdinalIgnoreCase)
                ? 0
                : Math.Max(0, variant.SideB.Ammunition - duel.AmmunitionB));
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
        double MeanDirectHitsA,
        double MeanDirectHitsB,
        double MeanLaunchesA,
        double MeanLaunchesB,
        double MeanMissileHitsA,
        double MeanMissileHitsB,
        double MeanRangeExhaustedA,
        double MeanRangeExhaustedB,
        double MeanHullA,
        double MeanHullB,
        double MeanAmmoUsedA,
        double MeanAmmoUsedB)
    {
        public static VariantSummary Create(Tl1WeaponMatrixVariantDocument variant, TrialResult[] results)
        {
            int count = results.Length;
            int[] turns = results.Select(result => result.Turns).OrderBy(turn => turn).ToArray();
            return new VariantSummary(
                variant,
                count,
                results.Count(result => result.Outcome == Tl1DuelOutcome.SideAWins) / (double)count,
                results.Count(result => result.Outcome == Tl1DuelOutcome.SideBWins) / (double)count,
                results.Count(result => result.Outcome == Tl1DuelOutcome.MutualDestruction) / (double)count,
                results.Count(result => result.Outcome == Tl1DuelOutcome.Unresolved) / (double)count,
                results.Average(result => result.Turns),
                turns[(count - 1) / 2],
                turns[(int)Math.Floor((count - 1) * 0.90)],
                results.Average(result => result.DirectHitsA),
                results.Average(result => result.DirectHitsB),
                results.Average(result => result.LaunchesA),
                results.Average(result => result.LaunchesB),
                results.Average(result => result.MissileHitsA),
                results.Average(result => result.MissileHitsB),
                results.Average(result => result.RangeExhaustedA),
                results.Average(result => result.RangeExhaustedB),
                results.Average(result => result.HullA),
                results.Average(result => result.HullB),
                results.Average(result => result.AmmoUsedA),
                results.Average(result => result.AmmoUsedB));
        }
    }

    private sealed record GateResult(string Id, bool Passed, double Observed, double Limit);
}
