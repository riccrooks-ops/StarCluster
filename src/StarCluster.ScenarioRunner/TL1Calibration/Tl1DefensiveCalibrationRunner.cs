using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.ScenarioRunner;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1DefensiveCalibrationRunner
{
    private const string SchemaVersion =
        "star-cluster-tl1-defensive-calibration-v1";
    private const int RequiredVariantCount = 171;

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1DefensiveCalibrationStudyDocument study =
            JsonSerializer.Deserialize<Tl1DefensiveCalibrationStudyDocument>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                    "TL1 defensive calibration study could not be read.");

        string baselineHash = Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselinePath)))
            .ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine(
            $"TL1 Defensive Calibration preflight: {study.Variants.Count} " +
            "variants, baseline hash, ready-package, PDS, sensor/EW, and " +
            "shield-defense contracts verified; passed.");

        if (preflightOnly)
        {
            return 0;
        }

        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new InvalidOperationException(
                "TL1 defensive calibration trials must be positive.");
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
                            "tl1-defense-common-direct-terminal",
                            index,
                            1UL));
                    var rngB = new DeterministicRandomStream(
                        TrialSeedDeriver.Derive(
                            study.MasterSeed,
                            "tl1-defense-common-direct-terminal",
                            index,
                            2UL));
                    var pdsRngA = new DeterministicRandomStream(
                        TrialSeedDeriver.Derive(
                            study.MasterSeed,
                            "tl1-defense-common-interception",
                            index,
                            1UL));
                    var pdsRngB = new DeterministicRandomStream(
                        TrialSeedDeriver.Derive(
                            study.MasterSeed,
                            "tl1-defense-common-interception",
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
                $"B {summary.SideBWinRate:P2}, mutual " +
                $"{summary.MutualRate:P2}, unresolved " +
                $"{summary.UnresolvedRate:P2}, turns " +
                $"{summary.MeanTurns:F2}, Firm/denied A " +
                $"{summary.MeanFirmTrackTurnsA:F1}/" +
                $"{summary.MeanTrackDeniedTurnsA:F1}, PDS A " +
                $"{summary.MeanPdsInterceptsA:F1}/" +
                $"{summary.MeanPdsAttemptsA:F1}");
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
            $"TL1 Defensive Calibration: {summaries.Count} variants, " +
            $"{trials} trials each, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static void Validate(
        Tl1DefensiveCalibrationStudyDocument study,
        string baselineHash)
    {
        if (study.SchemaVersion != SchemaVersion)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 defensive calibration schema.");
        }
        if (!string.Equals(
                study.BaselineSha256,
                baselineHash,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "TL1 defensive calibration baseline hash mismatch.");
        }
        if (study.Variants.Count != RequiredVariantCount)
        {
            throw new InvalidOperationException(
                $"TL1 defensive calibration requires exactly " +
                $"{RequiredVariantCount} variants; found " +
                $"{study.Variants.Count}.");
        }
        if (study.Variants
                .Select(variant => variant.Id)
                .Distinct(StringComparer.Ordinal)
                .Count() != study.Variants.Count)
        {
            throw new InvalidOperationException(
                "TL1 defensive calibration variant IDs must be unique.");
        }

        var ids = study.Variants
            .Select(variant => variant.Id)
            .ToHashSet(StringComparer.Ordinal);
        foreach (Tl1WeaponMatrixVariantDocument variant in study.Variants)
        {
            _ = ToProfile(variant);
            if (string.IsNullOrWhiteSpace(variant.Category))
            {
                throw new InvalidOperationException(
                    $"Variant {variant.Id} requires a category.");
            }
            if (!string.IsNullOrWhiteSpace(variant.PairId))
            {
                if (!ids.Contains(variant.PairId))
                {
                    throw new InvalidOperationException(
                        $"Variant {variant.Id} references missing pair " +
                        $"{variant.PairId}.");
                }
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

        RequireCategoryCount(study, "accepted-control", 6);
        RequireCategoryCount(study, "pds-rule-correction", 36);
        RequireCategoryCount(study, "sensor-ew-boundary", 57);
        RequireCategoryCount(study, "shield-defense", 36);
        RequireCategoryCount(study, "layered-defense", 36);

        RequireVariant(study, "ds-pds-amm-tc10-evm-r2");
        RequireVariant(study, "ds-pds-kinetic-tc0-steady-r2");
        RequireVariant(study, "ds-ew-missile-active1-ecm-denied-r5");
        RequireVariant(study, "ds-ew-missile-active1-eccm-restored-r5");
        RequireVariant(study, "ds-shield-hardener-v-missile-r2");
        RequireVariant(study, "ds-shield-battery-v-energy-r2");
        RequireVariant(study, "ds-layer-energy-full-package-r2");
        RequireVariant(study, "ds-layer-amm-saturation-r2");
    }

    private static void RequireCategoryCount(
        Tl1DefensiveCalibrationStudyDocument study,
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
                $"TL1 defensive calibration category {category} requires " +
                $"{expected} variants; found {actual}.");
        }
    }

    private static void RequireVariant(
        Tl1DefensiveCalibrationStudyDocument study,
        string id)
    {
        if (!study.Variants.Any(
                variant => string.Equals(
                    variant.Id,
                    id,
                    StringComparison.Ordinal)))
        {
            throw new InvalidOperationException(
                $"TL1 defensive calibration is missing required variant {id}.");
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
        Tl1DefensiveCalibrationStudyDocument study,
        IReadOnlyList<VariantSummary> summaries)
    {
        var gates = new List<GateResult>();
        foreach (VariantSummary summary in summaries)
        {
            bool mirror = JsonSerializer.Serialize(summary.Variant.SideA) ==
                JsonSerializer.Serialize(summary.Variant.SideB);
            if (mirror)
            {
                AddGate(
                    gates,
                    $"{summary.Variant.Id}:mirror-side-bias",
                    Math.Abs(summary.SideAWinRate - summary.SideBWinRate),
                    0.03);
                AddGate(
                    gates,
                    $"{summary.Variant.Id}:mirror-track-bias",
                    Math.Abs(
                        summary.MeanFirmTrackTurnsA -
                        summary.MeanFirmTrackTurnsB),
                    0.25);
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
            AddGate(
                gates,
                $"{variant.Id}:side-swap-win",
                Math.Abs(first.SideAWinRate - second.SideBWinRate),
                0.03);
            AddGate(
                gates,
                $"{variant.Id}:side-swap-pds",
                Math.Abs(
                    first.MeanPdsInterceptsA -
                    second.MeanPdsInterceptsB),
                0.15);
            AddGate(
                gates,
                $"{variant.Id}:side-swap-track",
                Math.Abs(
                    first.MeanTrackDeniedTurnsA -
                    second.MeanTrackDeniedTurnsB),
                0.25);
        }
        return gates;
    }

    private static void AddGate(
        ICollection<GateResult> gates,
        string id,
        double observed,
        double limit) =>
        gates.Add(new GateResult(id, observed <= limit, observed, limit));

    private static void WriteOutputs(
        Tl1DefensiveCalibrationStudyDocument study,
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
            "variant_id,label,category,trials,side_a_win_rate," +
            "side_b_win_rate,mutual_rate,unresolved_rate,mean_turns," +
            "mean_direct_hits_a,mean_direct_hits_b,mean_launches_a," +
            "mean_launches_b,mean_missile_hits_a,mean_missile_hits_b," +
            "mean_terminal_attacks_a,mean_terminal_attacks_b," +
            "mean_pds_attempts_a,mean_pds_attempts_b," +
            "mean_pds_intercepts_a,mean_pds_intercepts_b," +
            "mean_pds_ammo_used_a,mean_pds_ammo_used_b," +
            "mean_firm_turns_a,mean_firm_turns_b," +
            "mean_denied_turns_a,mean_denied_turns_b," +
            "mean_sensor_power_a,mean_sensor_power_b," +
            "mean_ecm_power_a,mean_ecm_power_b," +
            "mean_eccm_power_a,mean_eccm_power_b," +
            "mean_hardener_power_a,mean_hardener_power_b," +
            "mean_recharge_power_a,mean_recharge_power_b," +
            "mean_battery_charges_a,mean_battery_charges_b," +
            "mean_hull_a,mean_hull_b,mean_ammo_remaining_a," +
            "mean_ammo_remaining_b,mean_pds_ammo_remaining_a," +
            "mean_pds_ammo_remaining_b\n");

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
                .Append(F(summary.MeanDirectHitsA)).Append(',')
                .Append(F(summary.MeanDirectHitsB)).Append(',')
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
                .Append(F(summary.MeanPdsAmmoUsedA)).Append(',')
                .Append(F(summary.MeanPdsAmmoUsedB)).Append(',')
                .Append(F(summary.MeanFirmTrackTurnsA)).Append(',')
                .Append(F(summary.MeanFirmTrackTurnsB)).Append(',')
                .Append(F(summary.MeanTrackDeniedTurnsA)).Append(',')
                .Append(F(summary.MeanTrackDeniedTurnsB)).Append(',')
                .Append(F(summary.MeanSensorPowerA)).Append(',')
                .Append(F(summary.MeanSensorPowerB)).Append(',')
                .Append(F(summary.MeanEcmPowerA)).Append(',')
                .Append(F(summary.MeanEcmPowerB)).Append(',')
                .Append(F(summary.MeanEccmPowerA)).Append(',')
                .Append(F(summary.MeanEccmPowerB)).Append(',')
                .Append(F(summary.MeanHardenerPowerA)).Append(',')
                .Append(F(summary.MeanHardenerPowerB)).Append(',')
                .Append(F(summary.MeanRechargePowerA)).Append(',')
                .Append(F(summary.MeanRechargePowerB)).Append(',')
                .Append(F(summary.MeanBatteryChargesA)).Append(',')
                .Append(F(summary.MeanBatteryChargesB)).Append(',')
                .Append(F(summary.MeanHullA)).Append(',')
                .Append(F(summary.MeanHullB)).Append(',')
                .Append(F(summary.MeanAmmoRemainingA)).Append(',')
                .Append(F(summary.MeanAmmoRemainingB)).Append(',')
                .Append(F(summary.MeanPdsAmmoRemainingA)).Append(',')
                .Append(F(summary.MeanPdsAmmoRemainingB)).Append('\n');
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
        int DirectHitsA,
        int DirectHitsB,
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
        int PdsAmmoUsedA,
        int PdsAmmoUsedB,
        int FirmTrackTurnsA,
        int FirmTrackTurnsB,
        int TrackDeniedTurnsA,
        int TrackDeniedTurnsB,
        int SensorPowerA,
        int SensorPowerB,
        int EcmPowerA,
        int EcmPowerB,
        int EccmPowerA,
        int EccmPowerB,
        int HardenerPowerA,
        int HardenerPowerB,
        int RechargePowerA,
        int RechargePowerB,
        int BatteryChargesA,
        int BatteryChargesB,
        int HullA,
        int HullB,
        int AmmoRemainingA,
        int AmmoRemainingB,
        int PdsAmmoRemainingA,
        int PdsAmmoRemainingB)
    {
        public static TrialResult From(
            Tl1WeaponMatrixResult duel,
            Tl1WeaponMatrixVariantDocument variant) =>
            new(
                duel.Outcome,
                duel.Turns,
                duel.HitsA,
                duel.HitsB,
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
                PdsAmmoUsed(variant.SideA, duel.PdsAmmunitionA),
                PdsAmmoUsed(variant.SideB, duel.PdsAmmunitionB),
                duel.FirmTrackTurnsA,
                duel.FirmTrackTurnsB,
                duel.TrackDeniedTurnsA,
                duel.TrackDeniedTurnsB,
                duel.SensorPowerCommittedA,
                duel.SensorPowerCommittedB,
                duel.EcmPowerCommittedA,
                duel.EcmPowerCommittedB,
                duel.EccmPowerCommittedA,
                duel.EccmPowerCommittedB,
                duel.ShieldHardenerPowerCommittedA,
                duel.ShieldHardenerPowerCommittedB,
                duel.ShieldRechargePowerSpentA,
                duel.ShieldRechargePowerSpentB,
                duel.ShieldBatteryChargesUsedA,
                duel.ShieldBatteryChargesUsedB,
                duel.SideA.Defense.CurrentHull,
                duel.SideB.Defense.CurrentHull,
                duel.AmmunitionA,
                duel.AmmunitionB,
                duel.PdsAmmunitionA,
                duel.PdsAmmunitionB);

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
        double MeanDirectHitsA,
        double MeanDirectHitsB,
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
        double MeanPdsAmmoUsedA,
        double MeanPdsAmmoUsedB,
        double MeanFirmTrackTurnsA,
        double MeanFirmTrackTurnsB,
        double MeanTrackDeniedTurnsA,
        double MeanTrackDeniedTurnsB,
        double MeanSensorPowerA,
        double MeanSensorPowerB,
        double MeanEcmPowerA,
        double MeanEcmPowerB,
        double MeanEccmPowerA,
        double MeanEccmPowerB,
        double MeanHardenerPowerA,
        double MeanHardenerPowerB,
        double MeanRechargePowerA,
        double MeanRechargePowerB,
        double MeanBatteryChargesA,
        double MeanBatteryChargesB,
        double MeanHullA,
        double MeanHullB,
        double MeanAmmoRemainingA,
        double MeanAmmoRemainingB,
        double MeanPdsAmmoRemainingA,
        double MeanPdsAmmoRemainingB)
    {
        public static VariantSummary Create(
            Tl1WeaponMatrixVariantDocument variant,
            TrialResult[] results)
        {
            int count = results.Length;
            return new VariantSummary(
                variant,
                count,
                Rate(results, Tl1DuelOutcome.SideAWins),
                Rate(results, Tl1DuelOutcome.SideBWins),
                Rate(results, Tl1DuelOutcome.MutualDestruction),
                Rate(results, Tl1DuelOutcome.Unresolved),
                results.Average(result => result.Turns),
                results.Average(result => result.DirectHitsA),
                results.Average(result => result.DirectHitsB),
                results.Average(result => result.LaunchesA),
                results.Average(result => result.LaunchesB),
                results.Average(result => result.MissileHitsA),
                results.Average(result => result.MissileHitsB),
                results.Average(result => result.TerminalAttacksA),
                results.Average(result => result.TerminalAttacksB),
                results.Average(result => result.PdsAttemptsA),
                results.Average(result => result.PdsAttemptsB),
                results.Average(result => result.PdsInterceptsA),
                results.Average(result => result.PdsInterceptsB),
                results.Average(result => result.PdsAmmoUsedA),
                results.Average(result => result.PdsAmmoUsedB),
                results.Average(result => result.FirmTrackTurnsA),
                results.Average(result => result.FirmTrackTurnsB),
                results.Average(result => result.TrackDeniedTurnsA),
                results.Average(result => result.TrackDeniedTurnsB),
                results.Average(result => result.SensorPowerA),
                results.Average(result => result.SensorPowerB),
                results.Average(result => result.EcmPowerA),
                results.Average(result => result.EcmPowerB),
                results.Average(result => result.EccmPowerA),
                results.Average(result => result.EccmPowerB),
                results.Average(result => result.HardenerPowerA),
                results.Average(result => result.HardenerPowerB),
                results.Average(result => result.RechargePowerA),
                results.Average(result => result.RechargePowerB),
                results.Average(result => result.BatteryChargesA),
                results.Average(result => result.BatteryChargesB),
                results.Average(result => result.HullA),
                results.Average(result => result.HullB),
                results.Average(result => result.AmmoRemainingA),
                results.Average(result => result.AmmoRemainingB),
                results.Average(result => result.PdsAmmoRemainingA),
                results.Average(result => result.PdsAmmoRemainingB));
        }

        private static double Rate(
            IEnumerable<TrialResult> results,
            Tl1DuelOutcome outcome)
        {
            TrialResult[] array = results as TrialResult[] ?? results.ToArray();
            return array.Count(result => result.Outcome == outcome) /
                (double)array.Length;
        }
    }

    private sealed record GateResult(
        string Id,
        bool Passed,
        double Observed,
        double Limit);
}
