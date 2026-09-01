using System.Globalization;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.ScenarioRunner;
using StarCluster.ScenarioRunner.TL1;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1KineticCalibrationRunner
{
    public static int Run(string studyPath, string baselinePath, string outputDirectory, int? trialsOverride, int jobs, bool preflightOnly)
    {
        Tl1KineticCalibrationStudyDocument study = JsonSerializer.Deserialize<Tl1KineticCalibrationStudyDocument>(File.ReadAllText(studyPath), JsonOptions())
            ?? throw new InvalidOperationException("kinetic calibration study could not be read.");
        Tl1BaselineCatalog baseline = Tl1BaselineCatalog.Load(baselinePath);
        string hash = baseline.Sha256;
        Validate(study, baseline);
        Console.WriteLine($"TL1 Kinetic Calibration preflight: {study.Variants.Count} variants, baseline hash verified; passed.");
        if (preflightOnly) return 0;
        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0) throw new InvalidOperationException("Kinetic calibration trials must be positive.");
        int workers = Math.Clamp(jobs, 1, 24);
        Directory.CreateDirectory(outputDirectory);
        var summaries = new List<VariantSummary>();
        foreach (Tl1KineticCalibrationVariantDocument variant in study.Variants)
        {
            Tl1DuelCalibrationProfile profile = ToProfile(variant, baseline);
            TrialResult[] results = new TrialResult[trials];
            var options = new ParallelOptions { MaxDegreeOfParallelism = workers };
            Parallel.For(0, trials, options, index =>
            {
                ulong seedA = TrialSeedDeriver.Derive(study.MasterSeed, "tl1-kinetic-calibration-common", index, 1UL);
                ulong seedB = TrialSeedDeriver.Derive(study.MasterSeed, "tl1-kinetic-calibration-common", index, 2UL);
                var rngA = new DeterministicRandomStream(seedA);
                var rngB = new DeterministicRandomStream(seedB);
                var simulator = new Tl1KineticDuelSimulator(profile);
                Tl1CalibrationDuelResult duel = simulator.Run(rngA.NextD100, rngB.NextD100);
                results[index] = TrialResult.From(duel);
            });
            VariantSummary summary = VariantSummary.Create(variant, results);
            summaries.Add(summary);
            Console.WriteLine($"PASS {variant.Id}: A {summary.SideAWinRate:P2}, B {summary.SideBWinRate:P2}, mutual {summary.MutualRate:P2}, unresolved {summary.UnresolvedRate:P2}, mean turns {summary.MeanTurns:F2}");
        }
        IReadOnlyList<GateResult> gates = EvaluateGates(study, summaries);
        WriteOutputs(study, hash, trials, summaries, gates, outputDirectory);
        int failed = gates.Count(g => !g.Passed);
        Console.WriteLine($"TL1 Kinetic Calibration: {summaries.Count} variants, {trials} trials each, {failed} failed gates. Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static void Validate(
        Tl1KineticCalibrationStudyDocument study,
        Tl1BaselineCatalog baseline)
    {
        if (study.SchemaVersion != "star-cluster-tl1-kinetic-calibration-v1") throw new InvalidOperationException("Unexpected TL1 kinetic calibration schema.");
        if (!string.Equals(study.BaselineSha256, baseline.Sha256, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("Kinetic calibration baseline hash mismatch.");
        if (study.Variants.Count < 20) throw new InvalidOperationException("Kinetic calibration requires at least 20 variants.");
        if (study.Variants.Select(v => v.Id).Distinct(StringComparer.Ordinal).Count() != study.Variants.Count) throw new InvalidOperationException("Kinetic calibration variant IDs must be unique.");
        foreach (Tl1KineticCalibrationVariantDocument v in study.Variants)
        {
            _ = ToProfile(v, baseline);
            if (string.IsNullOrWhiteSpace(v.Id) || string.IsNullOrWhiteSpace(v.Label)) throw new InvalidOperationException("Every kinetic calibration variant requires an ID and label.");
        }
    }

    private static Tl1DuelCalibrationProfile ToProfile(
        Tl1KineticCalibrationVariantDocument v,
        Tl1BaselineCatalog baseline) => new(
        ShieldCapacity: v.ShieldCapacity,
        ShieldArmor: v.ShieldArmor,
        ShieldRecharge: v.ShieldRecharge,
        ArmorProtection: v.ArmorProtection,
        ArmorIntegrity: v.ArmorIntegrity,
        Hull: v.Hull,
        WeaponDamage: v.WeaponDamage,
        ShieldPenetration: v.ShieldPenetration,
        ArmorPenetration: v.ArmorPenetration,
        WeaponPower: baseline.GetInt("kinetic_power"),
        Ammunition: v.Ammunition,
        ReactorOutput: baseline.GetInt("reactor_output"),
        BaseChance: baseline.GetInt("direct_fire_base_chance"),
        WeaponAccuracy: baseline.GetInt("kinetic_accuracy"),
        RangePenaltyPerHex: baseline.GetInt("direct_fire_range_penalty"),
        TargetEvasivePenalty: baseline.GetInt("target_evasive_penalty"),
        ShooterEvasivePenalty: baseline.GetInt("shooter_evasive_penalty"),
        MinimumChance: baseline.GetInt("direct_fire_minimum_chance"),
        MaximumChance: baseline.GetInt("direct_fire_maximum_chance"),
        RangeHexes: v.RangeHexes,
        SideAEvasive: v.SideAEvasive,
        SideBEvasive: v.SideBEvasive,
        SideAComputerBonus: v.SideAComputerBonus,
        SideBComputerBonus: v.SideBComputerBonus,
        TurnCap: v.TurnCap);

    private static IReadOnlyList<GateResult> EvaluateGates(Tl1KineticCalibrationStudyDocument study, IReadOnlyList<VariantSummary> summaries)
    {
        var gates = new List<GateResult>();
        foreach (VariantSummary s in summaries)
        {
            bool mirror = s.Variant.SideAEvasive == s.Variant.SideBEvasive && s.Variant.SideAComputerBonus == s.Variant.SideBComputerBonus;
            if (mirror)
            {
                double delta = Math.Abs(s.SideAWinRate - s.SideBWinRate);
                gates.Add(new GateResult($"{s.Variant.Id}:mirror-side-bias", delta <= 0.03, delta, 0.03));
            }
        }
        foreach (Tl1KineticCalibrationVariantDocument v in study.Variants.Where(x => !string.IsNullOrWhiteSpace(x.PairId)))
        {
            VariantSummary a = summaries.Single(x => x.Variant.Id == v.Id);
            VariantSummary b = summaries.Single(x => x.Variant.Id == v.PairId);
            double delta = Math.Abs(a.SideAWinRate - b.SideBWinRate);
            gates.Add(new GateResult($"{v.Id}:side-swap", delta <= 0.03, delta, 0.03));
        }
        return gates;
    }

    private static void WriteOutputs(Tl1KineticCalibrationStudyDocument study, string hash, int trials, IReadOnlyList<VariantSummary> summaries, IReadOnlyList<GateResult> gates, string outputDirectory)
    {
        var payload = new { study.Id, baselineSha256 = hash, trialsPerVariant = trials, variants = summaries, gates, passed = gates.All(g => g.Passed) };
        File.WriteAllText(Path.Combine(outputDirectory, "summary.json"), JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
        var csv = new StringBuilder("variant_id,label,trials,side_a_win_rate,side_a_win_ci95_low,side_a_win_ci95_high,side_b_win_rate,side_b_win_ci95_low,side_b_win_ci95_high,mutual_rate,mutual_ci95_low,mutual_ci95_high,unresolved_rate,unresolved_ci95_low,unresolved_ci95_high,mean_turns,p50_turns,p90_turns,mean_hits_a,mean_hits_b,mean_shield_a,mean_shield_b,mean_armor_protection_a,mean_armor_protection_b,mean_armor_integrity_a,mean_armor_integrity_b,mean_hull_a,mean_hull_b,hull_damage_rate_a,hull_damage_rate_b,armor_depletion_rate_a,armor_depletion_rate_b,mean_ammo_used_a,mean_ammo_used_b\n");
        foreach (VariantSummary s in summaries)
        {
            csv.Append(C(s.Variant.Id)).Append(',').Append(C(s.Variant.Label)).Append(',').Append(s.Trials).Append(',')
                .Append(F(s.SideAWinRate)).Append(',').Append(F(s.SideAWins.Confidence95Low)).Append(',').Append(F(s.SideAWins.Confidence95High)).Append(',')
                .Append(F(s.SideBWinRate)).Append(',').Append(F(s.SideBWins.Confidence95Low)).Append(',').Append(F(s.SideBWins.Confidence95High)).Append(',')
                .Append(F(s.MutualRate)).Append(',').Append(F(s.MutualDestruction.Confidence95Low)).Append(',').Append(F(s.MutualDestruction.Confidence95High)).Append(',')
                .Append(F(s.UnresolvedRate)).Append(',').Append(F(s.Unresolved.Confidence95Low)).Append(',').Append(F(s.Unresolved.Confidence95High)).Append(',')
                .Append(F(s.MeanTurns)).Append(',').Append(s.P50Turns).Append(',').Append(s.P90Turns).Append(',')
                .Append(F(s.MeanHitsA)).Append(',').Append(F(s.MeanHitsB)).Append(',')
                .Append(F(s.MeanShieldA)).Append(',').Append(F(s.MeanShieldB)).Append(',')
                .Append(F(s.MeanArmorProtectionA)).Append(',').Append(F(s.MeanArmorProtectionB)).Append(',')
                .Append(F(s.MeanArmorIntegrityA)).Append(',').Append(F(s.MeanArmorIntegrityB)).Append(',')
                .Append(F(s.MeanHullA)).Append(',').Append(F(s.MeanHullB)).Append(',')
                .Append(F(s.HullDamageRateA)).Append(',').Append(F(s.HullDamageRateB)).Append(',')
                .Append(F(s.ArmorDepletionRateA)).Append(',').Append(F(s.ArmorDepletionRateB)).Append(',')
                .Append(F(s.MeanAmmoUsedA)).Append(',').Append(F(s.MeanAmmoUsedB)).Append('\n');
        }
        File.WriteAllText(Path.Combine(outputDirectory, "variants.csv"), csv.ToString());
        File.WriteAllText(Path.Combine(outputDirectory, "gates.csv"), "gate_id,passed,observed,limit\n" + string.Join("\n", gates.Select(g => $"{C(g.Id)},{g.Passed},{F(g.Observed)},{F(g.Limit)}")) + "\n");
    }

    private static JsonSerializerOptions JsonOptions() => new() { PropertyNameCaseInsensitive = true, ReadCommentHandling = JsonCommentHandling.Skip };
    private static string F(double value) => value.ToString("R", CultureInfo.InvariantCulture);
    private static string C(string value) => string.Concat("\"", value.Replace("\"", "\"\""), "\"");

    private sealed record TrialResult(
        Tl1DuelOutcome Outcome, int Turns, int HitsA, int HitsB,
        int ShieldA, int ShieldB, int ArmorProtectionA, int ArmorProtectionB,
        int ArmorIntegrityA, int ArmorIntegrityB, int HullA, int HullB,
        int AmmoA, int AmmoB)
    {
        public static TrialResult From(Tl1CalibrationDuelResult d)
        {
            ArmorLayerState armorA = d.SideA.Defense.ArmorLayers.Single();
            ArmorLayerState armorB = d.SideB.Defense.ArmorLayers.Single();
            return new TrialResult(
                d.Outcome, d.Turns, d.HitsA, d.HitsB,
                d.SideA.Defense.CurrentShieldCapacity, d.SideB.Defense.CurrentShieldCapacity,
                armorA.CurrentProtection, armorB.CurrentProtection,
                armorA.CurrentIntegrity, armorB.CurrentIntegrity,
                d.SideA.Defense.CurrentHull, d.SideB.Defense.CurrentHull,
                d.AmmunitionA, d.AmmunitionB);
        }
    }

    private sealed record OutcomeInterval(int Count, double Rate, double Confidence95Low, double Confidence95High);

    private sealed record VariantSummary(
        Tl1KineticCalibrationVariantDocument Variant, int Trials,
        OutcomeInterval SideAWins, OutcomeInterval SideBWins,
        OutcomeInterval MutualDestruction, OutcomeInterval Unresolved,
        double SideAWinRate, double SideBWinRate, double MutualRate, double UnresolvedRate,
        double MeanTurns, int P50Turns, int P90Turns,
        double MeanHitsA, double MeanHitsB,
        double MeanShieldA, double MeanShieldB,
        double MeanArmorProtectionA, double MeanArmorProtectionB,
        double MeanArmorIntegrityA, double MeanArmorIntegrityB,
        double MeanHullA, double MeanHullB,
        double HullDamageRateA, double HullDamageRateB,
        double ArmorDepletionRateA, double ArmorDepletionRateB,
        double MeanAmmoUsedA, double MeanAmmoUsedB)
    {
        public static VariantSummary Create(Tl1KineticCalibrationVariantDocument v, TrialResult[] r)
        {
            int[] turns = r.Select(x => x.Turns).OrderBy(x => x).ToArray();
            int n = r.Length;
            OutcomeInterval aWins = Interval(r.Count(x => x.Outcome == Tl1DuelOutcome.SideAWins), n);
            OutcomeInterval bWins = Interval(r.Count(x => x.Outcome == Tl1DuelOutcome.SideBWins), n);
            OutcomeInterval mutual = Interval(r.Count(x => x.Outcome == Tl1DuelOutcome.MutualDestruction), n);
            OutcomeInterval unresolved = Interval(r.Count(x => x.Outcome == Tl1DuelOutcome.Unresolved), n);
            return new VariantSummary(v, n, aWins, bWins, mutual, unresolved,
                aWins.Rate, bWins.Rate, mutual.Rate, unresolved.Rate,
                r.Average(x => x.Turns), turns[(n - 1) / 2], turns[(int)Math.Floor((n - 1) * 0.90)],
                r.Average(x => x.HitsA), r.Average(x => x.HitsB),
                r.Average(x => x.ShieldA), r.Average(x => x.ShieldB),
                r.Average(x => x.ArmorProtectionA), r.Average(x => x.ArmorProtectionB),
                r.Average(x => x.ArmorIntegrityA), r.Average(x => x.ArmorIntegrityB),
                r.Average(x => x.HullA), r.Average(x => x.HullB),
                r.Count(x => x.HullA < v.Hull) / (double)n, r.Count(x => x.HullB < v.Hull) / (double)n,
                r.Count(x => x.ArmorIntegrityA == 0) / (double)n, r.Count(x => x.ArmorIntegrityB == 0) / (double)n,
                v.Ammunition - r.Average(x => x.AmmoA), v.Ammunition - r.Average(x => x.AmmoB));
        }

        private static OutcomeInterval Interval(int count, int trials)
        {
            ProbabilityMetricSummary metric = MonteCarloStatistics.CreateMetric("outcome", count, trials);
            return new OutcomeInterval(metric.Count, metric.Proportion, metric.Confidence95Low, metric.Confidence95High);
        }
    }

    private sealed record GateResult(string Id, bool Passed, double Observed, double Limit);
}
