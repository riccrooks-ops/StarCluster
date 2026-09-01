using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.ScenarioRunner;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1EnergyCalibrationRunner
{
    public static int Run(string studyPath, string baselinePath, string outputDirectory, int? trialsOverride, int jobs, bool preflightOnly)
    {
        Tl1EnergyCalibrationStudyDocument study = JsonSerializer.Deserialize<Tl1EnergyCalibrationStudyDocument>(File.ReadAllText(studyPath), JsonOptions())
            ?? throw new InvalidOperationException("energy calibration study could not be read.");
        string hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(baselinePath))).ToLowerInvariant();
        Validate(study, hash);
        Console.WriteLine($"TL1 Energy Calibration preflight: {study.Variants.Count} variants, baseline hash verified; passed.");
        if (preflightOnly) return 0;
        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0) throw new InvalidOperationException("Energy calibration trials must be positive.");
        int workers = Math.Clamp(jobs, 1, 24);
        Directory.CreateDirectory(outputDirectory);
        var summaries = new List<VariantSummary>();
        foreach (Tl1EnergyCalibrationVariantDocument variant in study.Variants)
        {
            TrialResult[] results = new TrialResult[trials];
            Parallel.For(0, trials, new ParallelOptions { MaxDegreeOfParallelism = workers }, index =>
            {
                ulong seedA = TrialSeedDeriver.Derive(study.MasterSeed, "tl1-energy-calibration-common", index, 1UL);
                ulong seedB = TrialSeedDeriver.Derive(study.MasterSeed, "tl1-energy-calibration-common", index, 2UL);
                var rngA = new DeterministicRandomStream(seedA);
                var rngB = new DeterministicRandomStream(seedB);
                Tl1EnergyDuelResult duel = new Tl1EnergyDuelSimulator(ToProfile(variant)).Run(rngA.NextD100, rngB.NextD100);
                results[index] = TrialResult.From(duel, variant);
            });
            VariantSummary summary = VariantSummary.Create(variant, results);
            summaries.Add(summary);
            Console.WriteLine($"PASS {variant.Id}: A {summary.SideAWinRate:P2}, B {summary.SideBWinRate:P2}, mutual {summary.MutualRate:P2}, unresolved {summary.UnresolvedRate:P2}, mean turns {summary.MeanTurns:F2}, TP A/B {summary.MeanPowerA:F1}/{summary.MeanPowerB:F1}");
        }
        IReadOnlyList<GateResult> gates = EvaluateGates(study, summaries);
        WriteOutputs(study, hash, trials, summaries, gates, outputDirectory);
        int failed = gates.Count(g => !g.Passed);
        Console.WriteLine($"TL1 Energy Calibration: {summaries.Count} variants, {trials} trials each, {failed} failed gates. Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static void Validate(Tl1EnergyCalibrationStudyDocument study, string hash)
    {
        if (study.SchemaVersion != "star-cluster-tl1-energy-calibration-v1") throw new InvalidOperationException("Unexpected TL1 energy calibration schema.");
        if (!string.Equals(study.BaselineSha256, hash, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("Energy calibration baseline hash mismatch.");
        if (study.Variants.Count < 20) throw new InvalidOperationException("Energy calibration requires at least 20 variants.");
        if (study.Variants.Select(v => v.Id).Distinct(StringComparer.Ordinal).Count() != study.Variants.Count) throw new InvalidOperationException("Energy calibration variant IDs must be unique.");
        foreach (Tl1EnergyCalibrationVariantDocument variant in study.Variants) _ = ToProfile(variant);
    }

    private static Tl1EnergyCalibrationProfile ToProfile(Tl1EnergyCalibrationVariantDocument v) => new(
        v.ShieldCapacity, v.ShieldArmor, v.BaseShieldRecharge, v.ArmorProtection, v.ArmorIntegrity, v.Hull,
        v.RangeHexes, v.RangePenaltyPerHex, v.TurnCap, ToSide(v.SideA), ToSide(v.SideB));

    private static Tl1EnergySideProfile ToSide(Tl1EnergySideDocument side) => new(
        side.Family, side.Doctrine, side.Accuracy, side.ComputerBonus, side.Evasive,
        side.ReactorOutput, side.TacticalShieldRecharge, side.Ammunition);

    private static IReadOnlyList<GateResult> EvaluateGates(Tl1EnergyCalibrationStudyDocument study, IReadOnlyList<VariantSummary> summaries)
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
        foreach (Tl1EnergyCalibrationVariantDocument variant in study.Variants.Where(v => !string.IsNullOrWhiteSpace(v.PairId)))
        {
            VariantSummary a = summaries.Single(s => s.Variant.Id == variant.Id);
            VariantSummary b = summaries.Single(s => s.Variant.Id == variant.PairId);
            double delta = Math.Abs(a.SideAWinRate - b.SideBWinRate);
            gates.Add(new GateResult($"{variant.Id}:side-swap", delta <= 0.03, delta, 0.03));
        }
        return gates;
    }

    private static void WriteOutputs(Tl1EnergyCalibrationStudyDocument study, string hash, int trials, IReadOnlyList<VariantSummary> summaries, IReadOnlyList<GateResult> gates, string outputDirectory)
    {
        var payload = new { study.Id, baselineSha256 = hash, trialsPerVariant = trials, variants = summaries, gates, passed = gates.All(g => g.Passed) };
        File.WriteAllText(Path.Combine(outputDirectory, "summary.json"), JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
        var csv = new StringBuilder("variant_id,label,trials,side_a_win_rate,side_b_win_rate,mutual_rate,unresolved_rate,mean_turns,p50_turns,p90_turns,mean_hits_a,mean_hits_b,mean_hull_a,mean_hull_b,mean_power_a,mean_power_b,mean_tactical_shield_a,mean_tactical_shield_b,mean_ammo_used_a,mean_ammo_used_b\n");
        foreach (VariantSummary s in summaries)
        {
            csv.Append(C(s.Variant.Id)).Append(',').Append(C(s.Variant.Label)).Append(',').Append(s.Trials).Append(',')
                .Append(F(s.SideAWinRate)).Append(',').Append(F(s.SideBWinRate)).Append(',').Append(F(s.MutualRate)).Append(',').Append(F(s.UnresolvedRate)).Append(',')
                .Append(F(s.MeanTurns)).Append(',').Append(s.P50Turns).Append(',').Append(s.P90Turns).Append(',')
                .Append(F(s.MeanHitsA)).Append(',').Append(F(s.MeanHitsB)).Append(',').Append(F(s.MeanHullA)).Append(',').Append(F(s.MeanHullB)).Append(',')
                .Append(F(s.MeanPowerA)).Append(',').Append(F(s.MeanPowerB)).Append(',').Append(F(s.MeanTacticalShieldA)).Append(',').Append(F(s.MeanTacticalShieldB)).Append(',')
                .Append(F(s.MeanAmmoUsedA)).Append(',').Append(F(s.MeanAmmoUsedB)).Append('\n');
        }
        File.WriteAllText(Path.Combine(outputDirectory, "variants.csv"), csv.ToString());
        File.WriteAllText(Path.Combine(outputDirectory, "gates.csv"), "gate_id,passed,observed,limit\n" + string.Join("\n", gates.Select(g => $"{C(g.Id)},{g.Passed},{F(g.Observed)},{F(g.Limit)}")) + "\n");
    }

    private static JsonSerializerOptions JsonOptions() => new() { PropertyNameCaseInsensitive = true, ReadCommentHandling = JsonCommentHandling.Skip };
    private static string F(double value) => value.ToString("R", CultureInfo.InvariantCulture);
    private static string C(string value) => string.Concat("\"", value.Replace("\"", "\"\""), "\"");

    private sealed record TrialResult(Tl1DuelOutcome Outcome, int Turns, int HitsA, int HitsB, int HullA, int HullB,
        int PowerA, int PowerB, int TacticalShieldA, int TacticalShieldB, int AmmoUsedA, int AmmoUsedB)
    {
        public static TrialResult From(Tl1EnergyDuelResult d, Tl1EnergyCalibrationVariantDocument v) => new(
            d.Outcome, d.Turns, d.HitsA, d.HitsB, d.SideA.Defense.CurrentHull, d.SideB.Defense.CurrentHull,
            d.TacticalPowerSpentA, d.TacticalPowerSpentB, d.TacticalShieldRestoredA, d.TacticalShieldRestoredB,
            v.SideA.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase) ? v.SideA.Ammunition - d.AmmunitionA : 0,
            v.SideB.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase) ? v.SideB.Ammunition - d.AmmunitionB : 0);
    }

    private sealed record VariantSummary(Tl1EnergyCalibrationVariantDocument Variant, int Trials,
        double SideAWinRate, double SideBWinRate, double MutualRate, double UnresolvedRate,
        double MeanTurns, int P50Turns, int P90Turns, double MeanHitsA, double MeanHitsB,
        double MeanHullA, double MeanHullB, double MeanPowerA, double MeanPowerB,
        double MeanTacticalShieldA, double MeanTacticalShieldB, double MeanAmmoUsedA, double MeanAmmoUsedB)
    {
        public static VariantSummary Create(Tl1EnergyCalibrationVariantDocument v, TrialResult[] r)
        {
            int n = r.Length;
            int[] turns = r.Select(x => x.Turns).OrderBy(x => x).ToArray();
            return new VariantSummary(v, n,
                r.Count(x => x.Outcome == Tl1DuelOutcome.SideAWins) / (double)n,
                r.Count(x => x.Outcome == Tl1DuelOutcome.SideBWins) / (double)n,
                r.Count(x => x.Outcome == Tl1DuelOutcome.MutualDestruction) / (double)n,
                r.Count(x => x.Outcome == Tl1DuelOutcome.Unresolved) / (double)n,
                r.Average(x => x.Turns), turns[(n - 1) / 2], turns[(int)Math.Floor((n - 1) * 0.90)],
                r.Average(x => x.HitsA), r.Average(x => x.HitsB), r.Average(x => x.HullA), r.Average(x => x.HullB),
                r.Average(x => x.PowerA), r.Average(x => x.PowerB), r.Average(x => x.TacticalShieldA), r.Average(x => x.TacticalShieldB),
                r.Average(x => x.AmmoUsedA), r.Average(x => x.AmmoUsedB));
        }
    }

    private sealed record GateResult(string Id, bool Passed, double Observed, double Limit);
}
