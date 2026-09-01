using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.ScenarioRunner;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1PowerEnvelopeCalibrationRunner
{
    private const string SchemaVersion =
        "star-cluster-tl1-power-envelope-calibration-v2";
    private const int RequiredVariantCount = 294;

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1PowerEnvelopeCalibrationStudyDocument study =
            JsonSerializer.Deserialize<Tl1PowerEnvelopeCalibrationStudyDocument>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                "TL1 power-envelope study could not be read.");

        string baselineHash = Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselinePath)))
            .ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine(
            $"TL1 Power Correction preflight: {study.Variants.Count} variants, " +
            "focused reactor outputs 3-6, 1-TP Kinetic fire, zero-TP Missile " +
            "launches, 1-TP Auxiliary Reactors, revised Shield overcapacity, " +
            "Held Main before PDS, and exact reciprocal pairs verified; passed.");

        if (preflightOnly)
        {
            return 0;
        }

        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new InvalidOperationException(
                "TL1 power-envelope calibration trials must be positive.");
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
                        "tl1-power-common-direct-terminal",
                        index,
                        1UL);
                    var rngB = NewStream(
                        study.MasterSeed,
                        "tl1-power-common-direct-terminal",
                        index,
                        2UL);
                    var pdsRngA = NewStream(
                        study.MasterSeed,
                        "tl1-power-common-pds",
                        index,
                        1UL);
                    var pdsRngB = NewStream(
                        study.MasterSeed,
                        "tl1-power-common-pds",
                        index,
                        2UL);
                    var heldRngA = NewStream(
                        study.MasterSeed,
                        "tl1-power-common-held",
                        index,
                        1UL);
                    var heldRngB = NewStream(
                        study.MasterSeed,
                        "tl1-power-common-held",
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
                $"{summary.MeanTurns:F2}, package A/B " +
                $"{summary.MeanFullPackageRateA:P1}/" +
                $"{summary.MeanFullPackageRateB:P1}, envelope A/B " +
                $"{summary.MeanEnvelopePerTurnA:F1}/" +
                $"{summary.MeanEnvelopePerTurnB:F1}, unused A/B " +
                $"{summary.MeanUnusedPerTurnA:F1}/" +
                $"{summary.MeanUnusedPerTurnB:F1}");
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
            $"TL1 Power Correction Calibration: {summaries.Count} variants, " +
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
        Tl1PowerEnvelopeCalibrationStudyDocument study,
        string baselineHash)
    {
        if (study.SchemaVersion != SchemaVersion)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 power-envelope calibration schema.");
        }
        if (!string.Equals(
                study.BaselineSha256,
                baselineHash,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "TL1 power-envelope calibration baseline hash mismatch.");
        }
        if (study.Variants.Count != RequiredVariantCount)
        {
            throw new InvalidOperationException(
                $"TL1 power-envelope calibration requires exactly " +
                $"{RequiredVariantCount} variants; found {study.Variants.Count}.");
        }
        if (study.Variants
                .Select(variant => variant.Id)
                .Distinct(StringComparer.Ordinal)
                .Count() != study.Variants.Count)
        {
            throw new InvalidOperationException(
                "TL1 power-envelope variant IDs must be unique.");
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
                        StringComparison.Ordinal))
                {
                    throw new InvalidOperationException(
                        $"Variant {variant.Id} does not have a reciprocal pair.");
                }
                if (!ExactSideSwap(variant, partner))
                {
                    throw new InvalidOperationException(
                        $"Variant {variant.Id} and {partner.Id} are not exact " +
                        "side swaps.");
                }
            }
        }

        RequireCategoryCount(study, "accepted-control", 6);
        RequireCategoryCount(study, "reactor-sweep", 40);
        RequireCategoryCount(study, "single-consumer", 64);
        RequireCategoryCount(study, "layered-sweep", 64);
        RequireCategoryCount(study, "power-source-overlay", 60);
        RequireCategoryCount(study, "overload-boundary", 30);
        RequireCategoryCount(study, "held-interception", 30);

        int[] outputs = study.Variants
            .Where(variant => variant.Category == "reactor-sweep")
            .SelectMany(variant => new[]
            {
                variant.SideA.ReactorOutput,
                variant.SideB.ReactorOutput,
            })
            .Distinct()
            .OrderBy(value => value)
            .ToArray();
        if (!outputs.SequenceEqual(Enumerable.Range(3, 4)))
        {
            throw new InvalidOperationException(
                "The correction reactor sweep must cover every integer output from 3 through 6.");
        }

        int[] auxiliaryOutputs = study.Variants
            .SelectMany(variant => new[]
            {
                variant.SideA.AuxiliaryReactorOutput,
                variant.SideB.AuxiliaryReactorOutput,
            })
            .Where(value => value > 0)
            .Distinct()
            .OrderBy(value => value)
            .ToArray();
        if (!auxiliaryOutputs.SequenceEqual(new[] { 1 }))
        {
            throw new InvalidOperationException(
                "The TL1 Auxiliary Reactor overlay must contribute exactly 1 TP.");
        }

        RequireVariant(study, "pe-reactor-energy-standard-r2-p3");
        RequireVariant(study, "pe-single-energy-epds-r2-p5");
        RequireVariant(study, "pe-layer-energy-full-defense-r2-p5");
        RequireVariant(study, "pe-overlay-cap-full-a-r2-p3");
        RequireVariant(study, "pe-overlay-aux-a-r2-p4");
        RequireVariant(study, "pe-overload-sensor-r6-p4");
        RequireVariant(study, "pe-held-energy-standard-r2-p2");
        RequireVariant(study, "pe-held-kinetic-standard-r2-p1");
        RequireVariant(study, "pe-held-pds-saturation-r2-p5");
    }

    private static bool ExactSideSwap(
        Tl1PowerEnvelopeVariantDocument first,
        Tl1PowerEnvelopeVariantDocument second) =>
        first.ShieldCapacity == second.ShieldCapacity &&
        first.ShieldArmor == second.ShieldArmor &&
        first.BaseShieldRecharge == second.BaseShieldRecharge &&
        first.ArmorProtection == second.ArmorProtection &&
        first.ArmorIntegrity == second.ArmorIntegrity &&
        first.Hull == second.Hull &&
        first.RangeHexes == second.RangeHexes &&
        first.RangePenaltyPerHex == second.RangePenaltyPerHex &&
        first.TurnCap == second.TurnCap &&
        JsonSerializer.Serialize(first.SideA) ==
            JsonSerializer.Serialize(second.SideB) &&
        JsonSerializer.Serialize(first.SideB) ==
            JsonSerializer.Serialize(second.SideA);

    private static void RequireCategoryCount(
        Tl1PowerEnvelopeCalibrationStudyDocument study,
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
                $"TL1 power-envelope category {category} requires " +
                $"{expected} variants; found {actual}.");
        }
    }

    private static void RequireVariant(
        Tl1PowerEnvelopeCalibrationStudyDocument study,
        string id)
    {
        if (!study.Variants.Any(
                variant => string.Equals(
                    variant.Id,
                    id,
                    StringComparison.Ordinal)))
        {
            throw new InvalidOperationException(
                $"TL1 power-envelope study is missing required variant {id}.");
        }
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
            ShieldOvercapacitySafeOverload = side.ShieldOvercapacitySafeOverload,
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
        Tl1PowerEnvelopeCalibrationStudyDocument study,
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
                    $"{summary.Variant.Id}:mirror-package-bias",
                    Math.Abs(
                        summary.MeanFullPackageRateA -
                        summary.MeanFullPackageRateB),
                    0.03);
            }
        }

        var evaluatedPairs = new HashSet<string>(StringComparer.Ordinal);
        foreach (Tl1PowerEnvelopeVariantDocument variant in
                 study.Variants.Where(item => !string.IsNullOrWhiteSpace(item.PairId)))
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
                $"{variant.Id}:side-swap-package",
                Math.Abs(
                    first.MeanFullPackageRateA -
                    second.MeanFullPackageRateB),
                0.03);
            AddGate(
                gates,
                $"{variant.Id}:side-swap-envelope",
                Math.Abs(
                    first.MeanEnvelopePerTurnA -
                    second.MeanEnvelopePerTurnB),
                0.05);
        }
        return gates;
    }

    private static void AddGate(
        ICollection<GateResult> gates,
        string id,
        double observed,
        double limit) => gates.Add(new GateResult(
        id,
        observed <= limit,
        observed,
        limit));

    private static void WriteOutputs(
        Tl1PowerEnvelopeCalibrationStudyDocument study,
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
            "full_package_rate_a,full_package_rate_b," +
            "mean_shots_a,mean_shots_b,mean_hits_a,mean_hits_b," +
            "mean_launches_a,mean_launches_b,mean_missile_hits_a," +
            "mean_missile_hits_b,mean_pds_attempts_a,mean_pds_attempts_b," +
            "mean_pds_intercepts_a,mean_pds_intercepts_b," +
            "mean_held_declarations_a,mean_held_declarations_b," +
            "mean_held_attempts_a,mean_held_attempts_b," +
            "mean_held_intercepts_a,mean_held_intercepts_b," +
            "mean_held_unused_a,mean_held_unused_b," +
            "mean_held_power_earmarked_a,mean_held_power_earmarked_b," +
            "mean_offensive_power_spent_a,mean_offensive_power_spent_b," +
            "mean_offensive_cycles_lost_a,mean_offensive_cycles_lost_b," +
            "mean_envelope_per_turn_a,mean_envelope_per_turn_b," +
            "mean_powered_per_turn_a,mean_powered_per_turn_b," +
            "mean_spent_per_turn_a,mean_spent_per_turn_b," +
            "mean_unused_per_turn_a,mean_unused_per_turn_b," +
            "mean_base_reactor_power_per_turn_a,mean_base_reactor_power_per_turn_b," +
            "mean_aux_power_a,mean_aux_power_b," +
            "mean_reactor_overload_power_a,mean_reactor_overload_power_b," +
            "mean_battery_power_a,mean_battery_power_b," +
            "mean_battery_charges_a,mean_battery_charges_b," +
            "mean_cap_discharge_a,mean_cap_discharge_b," +
            "mean_cap_charge_a,mean_cap_charge_b," +
            "mean_cap_final_a,mean_cap_final_b," +
            "mean_pds_power_per_turn_a,mean_pds_power_per_turn_b," +
            "mean_sensor_power_per_turn_a,mean_sensor_power_per_turn_b," +
            "mean_ecm_power_per_turn_a,mean_ecm_power_per_turn_b," +
            "mean_eccm_power_per_turn_a,mean_eccm_power_per_turn_b," +
            "mean_hardener_power_per_turn_a,mean_hardener_power_per_turn_b," +
            "mean_shield_recharge_power_per_turn_a,mean_shield_recharge_power_per_turn_b," +
            "mean_shield_overcapacity_added_a,mean_shield_overcapacity_added_b," +
            "mean_energy_overload_shots_a,mean_energy_overload_shots_b," +
            "mean_firm_track_rate_a,mean_firm_track_rate_b," +
            "mean_track_denied_rate_a,mean_track_denied_rate_b," +
            "mean_unfunded_pds_a,mean_unfunded_pds_b," +
            "mean_unfunded_sensors_a,mean_unfunded_sensors_b," +
            "mean_unfunded_ecm_a,mean_unfunded_ecm_b," +
            "mean_unfunded_eccm_a,mean_unfunded_eccm_b," +
            "mean_unfunded_hardener_a,mean_unfunded_hardener_b," +
            "mean_unfunded_evm_a,mean_unfunded_evm_b," +
            "mean_unfunded_shield_overload_a,mean_unfunded_shield_overload_b," +
            "mean_unfunded_recharge_a,mean_unfunded_recharge_b," +
            "mean_unfunded_held_a,mean_unfunded_held_b," +
            "mean_unfunded_weapon_a,mean_unfunded_weapon_b," +
            "mean_reactor_strain_a,mean_reactor_strain_b," +
            "mean_energy_strain_a,mean_energy_strain_b," +
            "mean_sensor_strain_a,mean_sensor_strain_b," +
            "mean_ecm_strain_a,mean_ecm_strain_b," +
            "mean_eccm_strain_a,mean_eccm_strain_b," +
            "mean_hardener_strain_a,mean_hardener_strain_b," +
            "mean_shield_strain_a,mean_shield_strain_b," +
            "mean_hull_a,mean_hull_b,mean_ammo_remaining_a," +
            "mean_ammo_remaining_b\n");

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
                .Append(F(summary.MeanFullPackageRateA)).Append(',')
                .Append(F(summary.MeanFullPackageRateB)).Append(',')
                .Append(F(summary.MeanShotsA)).Append(',')
                .Append(F(summary.MeanShotsB)).Append(',')
                .Append(F(summary.MeanHitsA)).Append(',')
                .Append(F(summary.MeanHitsB)).Append(',')
                .Append(F(summary.MeanLaunchesA)).Append(',')
                .Append(F(summary.MeanLaunchesB)).Append(',')
                .Append(F(summary.MeanMissileHitsA)).Append(',')
                .Append(F(summary.MeanMissileHitsB)).Append(',')
                .Append(F(summary.MeanPdsAttemptsA)).Append(',')
                .Append(F(summary.MeanPdsAttemptsB)).Append(',')
                .Append(F(summary.MeanPdsInterceptsA)).Append(',')
                .Append(F(summary.MeanPdsInterceptsB)).Append(',')
                .Append(F(summary.MeanHeldDeclarationsA)).Append(',')
                .Append(F(summary.MeanHeldDeclarationsB)).Append(',')
                .Append(F(summary.MeanHeldAttemptsA)).Append(',')
                .Append(F(summary.MeanHeldAttemptsB)).Append(',')
                .Append(F(summary.MeanHeldInterceptsA)).Append(',')
                .Append(F(summary.MeanHeldInterceptsB)).Append(',')
                .Append(F(summary.MeanHeldUnusedA)).Append(',')
                .Append(F(summary.MeanHeldUnusedB)).Append(',')
                .Append(F(summary.MeanHeldPowerEarmarkedA)).Append(',')
                .Append(F(summary.MeanHeldPowerEarmarkedB)).Append(',')
                .Append(F(summary.MeanOffensivePowerSpentA)).Append(',')
                .Append(F(summary.MeanOffensivePowerSpentB)).Append(',')
                .Append(F(summary.MeanOffensiveCyclesLostA)).Append(',')
                .Append(F(summary.MeanOffensiveCyclesLostB)).Append(',')
                .Append(F(summary.MeanEnvelopePerTurnA)).Append(',')
                .Append(F(summary.MeanEnvelopePerTurnB)).Append(',')
                .Append(F(summary.MeanPoweredPerTurnA)).Append(',')
                .Append(F(summary.MeanPoweredPerTurnB)).Append(',')
                .Append(F(summary.MeanSpentPerTurnA)).Append(',')
                .Append(F(summary.MeanSpentPerTurnB)).Append(',')
                .Append(F(summary.MeanUnusedPerTurnA)).Append(',')
                .Append(F(summary.MeanUnusedPerTurnB)).Append(',')
                .Append(F(summary.MeanBaseReactorPowerPerTurnA)).Append(',')
                .Append(F(summary.MeanBaseReactorPowerPerTurnB)).Append(',')
                .Append(F(summary.MeanAuxiliaryPowerA)).Append(',')
                .Append(F(summary.MeanAuxiliaryPowerB)).Append(',')
                .Append(F(summary.MeanReactorOverloadPowerA)).Append(',')
                .Append(F(summary.MeanReactorOverloadPowerB)).Append(',')
                .Append(F(summary.MeanCombatBatteryPowerA)).Append(',')
                .Append(F(summary.MeanCombatBatteryPowerB)).Append(',')
                .Append(F(summary.MeanCombatBatteryChargesA)).Append(',')
                .Append(F(summary.MeanCombatBatteryChargesB)).Append(',')
                .Append(F(summary.MeanCapacitorDischargedA)).Append(',')
                .Append(F(summary.MeanCapacitorDischargedB)).Append(',')
                .Append(F(summary.MeanCapacitorChargedA)).Append(',')
                .Append(F(summary.MeanCapacitorChargedB)).Append(',')
                .Append(F(summary.MeanCapacitorFinalA)).Append(',')
                .Append(F(summary.MeanCapacitorFinalB)).Append(',')
                .Append(F(summary.MeanPdsPowerPerTurnA)).Append(',')
                .Append(F(summary.MeanPdsPowerPerTurnB)).Append(',')
                .Append(F(summary.MeanSensorPowerPerTurnA)).Append(',')
                .Append(F(summary.MeanSensorPowerPerTurnB)).Append(',')
                .Append(F(summary.MeanEcmPowerPerTurnA)).Append(',')
                .Append(F(summary.MeanEcmPowerPerTurnB)).Append(',')
                .Append(F(summary.MeanEccmPowerPerTurnA)).Append(',')
                .Append(F(summary.MeanEccmPowerPerTurnB)).Append(',')
                .Append(F(summary.MeanHardenerPowerPerTurnA)).Append(',')
                .Append(F(summary.MeanHardenerPowerPerTurnB)).Append(',')
                .Append(F(summary.MeanShieldRechargePowerPerTurnA)).Append(',')
                .Append(F(summary.MeanShieldRechargePowerPerTurnB)).Append(',')
                .Append(F(summary.MeanShieldOvercapacityAddedA)).Append(',')
                .Append(F(summary.MeanShieldOvercapacityAddedB)).Append(',')
                .Append(F(summary.MeanEnergyOverloadShotsA)).Append(',')
                .Append(F(summary.MeanEnergyOverloadShotsB)).Append(',')
                .Append(F(summary.MeanFirmTrackRateA)).Append(',')
                .Append(F(summary.MeanFirmTrackRateB)).Append(',')
                .Append(F(summary.MeanTrackDeniedRateA)).Append(',')
                .Append(F(summary.MeanTrackDeniedRateB)).Append(',')
                .Append(F(summary.MeanUnfundedPdsA)).Append(',')
                .Append(F(summary.MeanUnfundedPdsB)).Append(',')
                .Append(F(summary.MeanUnfundedSensorsA)).Append(',')
                .Append(F(summary.MeanUnfundedSensorsB)).Append(',')
                .Append(F(summary.MeanUnfundedEcmA)).Append(',')
                .Append(F(summary.MeanUnfundedEcmB)).Append(',')
                .Append(F(summary.MeanUnfundedEccmA)).Append(',')
                .Append(F(summary.MeanUnfundedEccmB)).Append(',')
                .Append(F(summary.MeanUnfundedHardenerA)).Append(',')
                .Append(F(summary.MeanUnfundedHardenerB)).Append(',')
                .Append(F(summary.MeanUnfundedEvmA)).Append(',')
                .Append(F(summary.MeanUnfundedEvmB)).Append(',')
                .Append(F(summary.MeanUnfundedShieldOverloadA)).Append(',')
                .Append(F(summary.MeanUnfundedShieldOverloadB)).Append(',')
                .Append(F(summary.MeanUnfundedRechargeA)).Append(',')
                .Append(F(summary.MeanUnfundedRechargeB)).Append(',')
                .Append(F(summary.MeanUnfundedHeldA)).Append(',')
                .Append(F(summary.MeanUnfundedHeldB)).Append(',')
                .Append(F(summary.MeanUnfundedWeaponA)).Append(',')
                .Append(F(summary.MeanUnfundedWeaponB)).Append(',')
                .Append(F(summary.MeanReactorStrainA)).Append(',')
                .Append(F(summary.MeanReactorStrainB)).Append(',')
                .Append(F(summary.MeanEnergyStrainA)).Append(',')
                .Append(F(summary.MeanEnergyStrainB)).Append(',')
                .Append(F(summary.MeanSensorStrainA)).Append(',')
                .Append(F(summary.MeanSensorStrainB)).Append(',')
                .Append(F(summary.MeanEcmStrainA)).Append(',')
                .Append(F(summary.MeanEcmStrainB)).Append(',')
                .Append(F(summary.MeanEccmStrainA)).Append(',')
                .Append(F(summary.MeanEccmStrainB)).Append(',')
                .Append(F(summary.MeanHardenerStrainA)).Append(',')
                .Append(F(summary.MeanHardenerStrainB)).Append(',')
                .Append(F(summary.MeanShieldGeneratorStrainA)).Append(',')
                .Append(F(summary.MeanShieldGeneratorStrainB)).Append(',')
                .Append(F(summary.MeanHullA)).Append(',')
                .Append(F(summary.MeanHullB)).Append(',')
                .Append(F(summary.MeanAmmoRemainingA)).Append(',')
                .Append(F(summary.MeanAmmoRemainingB)).Append('\n');
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

    private sealed record GateResult(
        string Id,
        bool Passed,
        double Observed,
        double Limit);

    private sealed record TrialResult
    {
        public Tl1DuelOutcome Outcome { get; init; }
        public int Turns { get; init; }
        public int ShotsA { get; init; }
        public int ShotsB { get; init; }
        public int HitsA { get; init; }
        public int HitsB { get; init; }
        public int LaunchesA { get; init; }
        public int LaunchesB { get; init; }
        public int MissileHitsA { get; init; }
        public int MissileHitsB { get; init; }
        public int PdsAttemptsA { get; init; }
        public int PdsAttemptsB { get; init; }
        public int PdsInterceptsA { get; init; }
        public int PdsInterceptsB { get; init; }
        public int HeldDeclarationsA { get; init; }
        public int HeldDeclarationsB { get; init; }
        public int HeldAttemptsA { get; init; }
        public int HeldAttemptsB { get; init; }
        public int HeldInterceptsA { get; init; }
        public int HeldInterceptsB { get; init; }
        public int HeldUnusedA { get; init; }
        public int HeldUnusedB { get; init; }
        public int HeldPowerEarmarkedA { get; init; }
        public int HeldPowerEarmarkedB { get; init; }
        public int OffensiveWeaponPowerSpentA { get; init; }
        public int OffensiveWeaponPowerSpentB { get; init; }
        public int OffensiveCyclesLostA { get; init; }
        public int OffensiveCyclesLostB { get; init; }
        public int FullPackageTurnsA { get; init; }
        public int FullPackageTurnsB { get; init; }
        public int PartialPackageTurnsA { get; init; }
        public int PartialPackageTurnsB { get; init; }
        public int TotalEnvelopeA { get; init; }
        public int TotalEnvelopeB { get; init; }
        public int TotalPoweredA { get; init; }
        public int TotalPoweredB { get; init; }
        public int TotalSpentA { get; init; }
        public int TotalSpentB { get; init; }
        public int TotalUnusedA { get; init; }
        public int TotalUnusedB { get; init; }
        public int BaseReactorPowerA { get; init; }
        public int BaseReactorPowerB { get; init; }
        public int AuxiliaryPowerA { get; init; }
        public int AuxiliaryPowerB { get; init; }
        public int ReactorOverloadPowerA { get; init; }
        public int ReactorOverloadPowerB { get; init; }
        public int CombatBatteryPowerA { get; init; }
        public int CombatBatteryPowerB { get; init; }
        public int CombatBatteryChargesA { get; init; }
        public int CombatBatteryChargesB { get; init; }
        public int CapacitorDischargedA { get; init; }
        public int CapacitorDischargedB { get; init; }
        public int CapacitorChargedA { get; init; }
        public int CapacitorChargedB { get; init; }
        public int CapacitorFinalA { get; init; }
        public int CapacitorFinalB { get; init; }
        public int PdsPowerCommittedA { get; init; }
        public int PdsPowerCommittedB { get; init; }
        public int SensorPowerCommittedA { get; init; }
        public int SensorPowerCommittedB { get; init; }
        public int EcmPowerCommittedA { get; init; }
        public int EcmPowerCommittedB { get; init; }
        public int EccmPowerCommittedA { get; init; }
        public int EccmPowerCommittedB { get; init; }
        public int ShieldHardenerPowerCommittedA { get; init; }
        public int ShieldHardenerPowerCommittedB { get; init; }
        public int ShieldRechargePowerSpentA { get; init; }
        public int ShieldRechargePowerSpentB { get; init; }
        public int ShieldOvercapacityAddedA { get; init; }
        public int ShieldOvercapacityAddedB { get; init; }
        public int EnergyOverloadShotsA { get; init; }
        public int EnergyOverloadShotsB { get; init; }
        public int FirmTrackTurnsA { get; init; }
        public int FirmTrackTurnsB { get; init; }
        public int TrackDeniedTurnsA { get; init; }
        public int TrackDeniedTurnsB { get; init; }
        public int UnfundedPdsA { get; init; }
        public int UnfundedPdsB { get; init; }
        public int UnfundedSensorsA { get; init; }
        public int UnfundedSensorsB { get; init; }
        public int UnfundedEcmA { get; init; }
        public int UnfundedEcmB { get; init; }
        public int UnfundedEccmA { get; init; }
        public int UnfundedEccmB { get; init; }
        public int UnfundedHardenerA { get; init; }
        public int UnfundedHardenerB { get; init; }
        public int UnfundedEvmA { get; init; }
        public int UnfundedEvmB { get; init; }
        public int UnfundedShieldOverloadA { get; init; }
        public int UnfundedShieldOverloadB { get; init; }
        public int UnfundedRechargeA { get; init; }
        public int UnfundedRechargeB { get; init; }
        public int UnfundedHeldA { get; init; }
        public int UnfundedHeldB { get; init; }
        public int UnfundedWeaponA { get; init; }
        public int UnfundedWeaponB { get; init; }
        public int ReactorStrainA { get; init; }
        public int ReactorStrainB { get; init; }
        public int EnergyStrainA { get; init; }
        public int EnergyStrainB { get; init; }
        public int SensorStrainA { get; init; }
        public int SensorStrainB { get; init; }
        public int EcmStrainA { get; init; }
        public int EcmStrainB { get; init; }
        public int EccmStrainA { get; init; }
        public int EccmStrainB { get; init; }
        public int HardenerStrainA { get; init; }
        public int HardenerStrainB { get; init; }
        public int ShieldGeneratorStrainA { get; init; }
        public int ShieldGeneratorStrainB { get; init; }
        public int HullA { get; init; }
        public int HullB { get; init; }
        public int AmmoRemainingA { get; init; }
        public int AmmoRemainingB { get; init; }

        public static TrialResult From(Tl1PowerEnvelopeResult duel) => new()
        {
            Outcome = duel.Outcome,
            Turns = duel.Turns,
            ShotsA = duel.ShotsA,
            ShotsB = duel.ShotsB,
            HitsA = duel.HitsA,
            HitsB = duel.HitsB,
            LaunchesA = duel.LaunchesA,
            LaunchesB = duel.LaunchesB,
            MissileHitsA = duel.MissileHitsA,
            MissileHitsB = duel.MissileHitsB,
            PdsAttemptsA = duel.PdsAttemptsA,
            PdsAttemptsB = duel.PdsAttemptsB,
            PdsInterceptsA = duel.PdsInterceptsA,
            PdsInterceptsB = duel.PdsInterceptsB,
            HeldDeclarationsA = duel.HeldDeclarationsA,
            HeldDeclarationsB = duel.HeldDeclarationsB,
            HeldAttemptsA = duel.HeldAttemptsA,
            HeldAttemptsB = duel.HeldAttemptsB,
            HeldInterceptsA = duel.HeldInterceptsA,
            HeldInterceptsB = duel.HeldInterceptsB,
            HeldUnusedA = duel.HeldUnusedA,
            HeldUnusedB = duel.HeldUnusedB,
            HeldPowerEarmarkedA = duel.HeldPowerEarmarkedA,
            HeldPowerEarmarkedB = duel.HeldPowerEarmarkedB,
            OffensiveWeaponPowerSpentA = duel.OffensiveWeaponPowerSpentA,
            OffensiveWeaponPowerSpentB = duel.OffensiveWeaponPowerSpentB,
            OffensiveCyclesLostA = duel.OffensiveCyclesLostA,
            OffensiveCyclesLostB = duel.OffensiveCyclesLostB,
            FullPackageTurnsA = duel.FullPackageTurnsA,
            FullPackageTurnsB = duel.FullPackageTurnsB,
            PartialPackageTurnsA = duel.PartialPackageTurnsA,
            PartialPackageTurnsB = duel.PartialPackageTurnsB,
            TotalEnvelopeA = duel.TotalEnvelopeA,
            TotalEnvelopeB = duel.TotalEnvelopeB,
            TotalPoweredA = duel.TotalPoweredA,
            TotalPoweredB = duel.TotalPoweredB,
            TotalSpentA = duel.TotalSpentA,
            TotalSpentB = duel.TotalSpentB,
            TotalUnusedA = duel.TotalUnusedA,
            TotalUnusedB = duel.TotalUnusedB,
            BaseReactorPowerA = duel.BaseReactorPowerA,
            BaseReactorPowerB = duel.BaseReactorPowerB,
            AuxiliaryPowerA = duel.AuxiliaryPowerA,
            AuxiliaryPowerB = duel.AuxiliaryPowerB,
            ReactorOverloadPowerA = duel.ReactorOverloadPowerA,
            ReactorOverloadPowerB = duel.ReactorOverloadPowerB,
            CombatBatteryPowerA = duel.CombatBatteryPowerA,
            CombatBatteryPowerB = duel.CombatBatteryPowerB,
            CombatBatteryChargesA = duel.CombatBatteryChargesUsedA,
            CombatBatteryChargesB = duel.CombatBatteryChargesUsedB,
            CapacitorDischargedA = duel.CapacitorPowerDischargedA,
            CapacitorDischargedB = duel.CapacitorPowerDischargedB,
            CapacitorChargedA = duel.CapacitorPowerChargedA,
            CapacitorChargedB = duel.CapacitorPowerChargedB,
            CapacitorFinalA = duel.CapacitorChargeA,
            CapacitorFinalB = duel.CapacitorChargeB,
            PdsPowerCommittedA = duel.PdsPowerCommittedA,
            PdsPowerCommittedB = duel.PdsPowerCommittedB,
            SensorPowerCommittedA = duel.SensorPowerCommittedA,
            SensorPowerCommittedB = duel.SensorPowerCommittedB,
            EcmPowerCommittedA = duel.EcmPowerCommittedA,
            EcmPowerCommittedB = duel.EcmPowerCommittedB,
            EccmPowerCommittedA = duel.EccmPowerCommittedA,
            EccmPowerCommittedB = duel.EccmPowerCommittedB,
            ShieldHardenerPowerCommittedA = duel.ShieldHardenerPowerCommittedA,
            ShieldHardenerPowerCommittedB = duel.ShieldHardenerPowerCommittedB,
            ShieldRechargePowerSpentA = duel.ShieldRechargePowerSpentA,
            ShieldRechargePowerSpentB = duel.ShieldRechargePowerSpentB,
            ShieldOvercapacityAddedA = duel.ShieldOvercapacityAddedA,
            ShieldOvercapacityAddedB = duel.ShieldOvercapacityAddedB,
            EnergyOverloadShotsA = duel.EnergyOverloadShotsA,
            EnergyOverloadShotsB = duel.EnergyOverloadShotsB,
            FirmTrackTurnsA = duel.FirmTrackTurnsA,
            FirmTrackTurnsB = duel.FirmTrackTurnsB,
            TrackDeniedTurnsA = duel.TrackDeniedTurnsA,
            TrackDeniedTurnsB = duel.TrackDeniedTurnsB,
            UnfundedPdsA = duel.UnfundedPdsA,
            UnfundedPdsB = duel.UnfundedPdsB,
            UnfundedSensorsA = duel.UnfundedSensorsA,
            UnfundedSensorsB = duel.UnfundedSensorsB,
            UnfundedEcmA = duel.UnfundedEcmA,
            UnfundedEcmB = duel.UnfundedEcmB,
            UnfundedEccmA = duel.UnfundedEccmA,
            UnfundedEccmB = duel.UnfundedEccmB,
            UnfundedHardenerA = duel.UnfundedHardenerA,
            UnfundedHardenerB = duel.UnfundedHardenerB,
            UnfundedEvmA = duel.UnfundedEvmA,
            UnfundedEvmB = duel.UnfundedEvmB,
            UnfundedShieldOverloadA = duel.UnfundedShieldOverloadA,
            UnfundedShieldOverloadB = duel.UnfundedShieldOverloadB,
            UnfundedRechargeA = duel.UnfundedRechargeA,
            UnfundedRechargeB = duel.UnfundedRechargeB,
            UnfundedHeldA = duel.UnfundedHeldA,
            UnfundedHeldB = duel.UnfundedHeldB,
            UnfundedWeaponA = duel.UnfundedWeaponA,
            UnfundedWeaponB = duel.UnfundedWeaponB,
            ReactorStrainA = duel.ReactorStrainA,
            ReactorStrainB = duel.ReactorStrainB,
            EnergyStrainA = duel.EnergyStrainA,
            EnergyStrainB = duel.EnergyStrainB,
            SensorStrainA = duel.SensorStrainA,
            SensorStrainB = duel.SensorStrainB,
            EcmStrainA = duel.EcmStrainA,
            EcmStrainB = duel.EcmStrainB,
            EccmStrainA = duel.EccmStrainA,
            EccmStrainB = duel.EccmStrainB,
            HardenerStrainA = duel.HardenerStrainA,
            HardenerStrainB = duel.HardenerStrainB,
            ShieldGeneratorStrainA = duel.ShieldGeneratorStrainA,
            ShieldGeneratorStrainB = duel.ShieldGeneratorStrainB,
            HullA = duel.SideA.Defense.CurrentHull,
            HullB = duel.SideB.Defense.CurrentHull,
            AmmoRemainingA = duel.AmmunitionA,
            AmmoRemainingB = duel.AmmunitionB,
        };
    }

    private sealed record VariantSummary
    {
        public Tl1PowerEnvelopeVariantDocument Variant { get; init; } = null!;
        public int Trials { get; init; }
        public double SideAWinRate { get; init; }
        public double SideBWinRate { get; init; }
        public double MutualRate { get; init; }
        public double UnresolvedRate { get; init; }
        public double MeanTurns { get; init; }
        public double MeanFullPackageRateA { get; init; }
        public double MeanFullPackageRateB { get; init; }
        public double MeanShotsA { get; init; }
        public double MeanShotsB { get; init; }
        public double MeanHitsA { get; init; }
        public double MeanHitsB { get; init; }
        public double MeanLaunchesA { get; init; }
        public double MeanLaunchesB { get; init; }
        public double MeanMissileHitsA { get; init; }
        public double MeanMissileHitsB { get; init; }
        public double MeanPdsAttemptsA { get; init; }
        public double MeanPdsAttemptsB { get; init; }
        public double MeanPdsInterceptsA { get; init; }
        public double MeanPdsInterceptsB { get; init; }
        public double MeanHeldDeclarationsA { get; init; }
        public double MeanHeldDeclarationsB { get; init; }
        public double MeanHeldAttemptsA { get; init; }
        public double MeanHeldAttemptsB { get; init; }
        public double MeanHeldInterceptsA { get; init; }
        public double MeanHeldInterceptsB { get; init; }
        public double MeanHeldUnusedA { get; init; }
        public double MeanHeldUnusedB { get; init; }
        public double MeanHeldPowerEarmarkedA { get; init; }
        public double MeanHeldPowerEarmarkedB { get; init; }
        public double MeanOffensivePowerSpentA { get; init; }
        public double MeanOffensivePowerSpentB { get; init; }
        public double MeanOffensiveCyclesLostA { get; init; }
        public double MeanOffensiveCyclesLostB { get; init; }
        public double MeanEnvelopePerTurnA { get; init; }
        public double MeanEnvelopePerTurnB { get; init; }
        public double MeanPoweredPerTurnA { get; init; }
        public double MeanPoweredPerTurnB { get; init; }
        public double MeanSpentPerTurnA { get; init; }
        public double MeanSpentPerTurnB { get; init; }
        public double MeanUnusedPerTurnA { get; init; }
        public double MeanUnusedPerTurnB { get; init; }
        public double MeanBaseReactorPowerPerTurnA { get; init; }
        public double MeanBaseReactorPowerPerTurnB { get; init; }
        public double MeanAuxiliaryPowerA { get; init; }
        public double MeanAuxiliaryPowerB { get; init; }
        public double MeanReactorOverloadPowerA { get; init; }
        public double MeanReactorOverloadPowerB { get; init; }
        public double MeanCombatBatteryPowerA { get; init; }
        public double MeanCombatBatteryPowerB { get; init; }
        public double MeanCombatBatteryChargesA { get; init; }
        public double MeanCombatBatteryChargesB { get; init; }
        public double MeanCapacitorDischargedA { get; init; }
        public double MeanCapacitorDischargedB { get; init; }
        public double MeanCapacitorChargedA { get; init; }
        public double MeanCapacitorChargedB { get; init; }
        public double MeanCapacitorFinalA { get; init; }
        public double MeanCapacitorFinalB { get; init; }
        public double MeanPdsPowerPerTurnA { get; init; }
        public double MeanPdsPowerPerTurnB { get; init; }
        public double MeanSensorPowerPerTurnA { get; init; }
        public double MeanSensorPowerPerTurnB { get; init; }
        public double MeanEcmPowerPerTurnA { get; init; }
        public double MeanEcmPowerPerTurnB { get; init; }
        public double MeanEccmPowerPerTurnA { get; init; }
        public double MeanEccmPowerPerTurnB { get; init; }
        public double MeanHardenerPowerPerTurnA { get; init; }
        public double MeanHardenerPowerPerTurnB { get; init; }
        public double MeanShieldRechargePowerPerTurnA { get; init; }
        public double MeanShieldRechargePowerPerTurnB { get; init; }
        public double MeanShieldOvercapacityAddedA { get; init; }
        public double MeanShieldOvercapacityAddedB { get; init; }
        public double MeanEnergyOverloadShotsA { get; init; }
        public double MeanEnergyOverloadShotsB { get; init; }
        public double MeanFirmTrackRateA { get; init; }
        public double MeanFirmTrackRateB { get; init; }
        public double MeanTrackDeniedRateA { get; init; }
        public double MeanTrackDeniedRateB { get; init; }
        public double MeanUnfundedPdsA { get; init; }
        public double MeanUnfundedPdsB { get; init; }
        public double MeanUnfundedSensorsA { get; init; }
        public double MeanUnfundedSensorsB { get; init; }
        public double MeanUnfundedEcmA { get; init; }
        public double MeanUnfundedEcmB { get; init; }
        public double MeanUnfundedEccmA { get; init; }
        public double MeanUnfundedEccmB { get; init; }
        public double MeanUnfundedHardenerA { get; init; }
        public double MeanUnfundedHardenerB { get; init; }
        public double MeanUnfundedEvmA { get; init; }
        public double MeanUnfundedEvmB { get; init; }
        public double MeanUnfundedShieldOverloadA { get; init; }
        public double MeanUnfundedShieldOverloadB { get; init; }
        public double MeanUnfundedRechargeA { get; init; }
        public double MeanUnfundedRechargeB { get; init; }
        public double MeanUnfundedHeldA { get; init; }
        public double MeanUnfundedHeldB { get; init; }
        public double MeanUnfundedWeaponA { get; init; }
        public double MeanUnfundedWeaponB { get; init; }
        public double MeanReactorStrainA { get; init; }
        public double MeanReactorStrainB { get; init; }
        public double MeanEnergyStrainA { get; init; }
        public double MeanEnergyStrainB { get; init; }
        public double MeanSensorStrainA { get; init; }
        public double MeanSensorStrainB { get; init; }
        public double MeanEcmStrainA { get; init; }
        public double MeanEcmStrainB { get; init; }
        public double MeanEccmStrainA { get; init; }
        public double MeanEccmStrainB { get; init; }
        public double MeanHardenerStrainA { get; init; }
        public double MeanHardenerStrainB { get; init; }
        public double MeanShieldGeneratorStrainA { get; init; }
        public double MeanShieldGeneratorStrainB { get; init; }
        public double MeanHullA { get; init; }
        public double MeanHullB { get; init; }
        public double MeanAmmoRemainingA { get; init; }
        public double MeanAmmoRemainingB { get; init; }

        public static VariantSummary Create(
            Tl1PowerEnvelopeVariantDocument variant,
            IReadOnlyList<TrialResult> results) => new()
        {
            Variant = variant,
            Trials = results.Count,
            SideAWinRate = Rate(results, Tl1DuelOutcome.SideAWins),
            SideBWinRate = Rate(results, Tl1DuelOutcome.SideBWins),
            MutualRate = results.Count(result =>
                result.Outcome is Tl1DuelOutcome.MutualDestruction or
                    Tl1DuelOutcome.MixedTerminal) / (double)results.Count,
            UnresolvedRate = Rate(results, Tl1DuelOutcome.Unresolved),
            MeanTurns = Avg(results, result => result.Turns),
            MeanFullPackageRateA = Avg(
                results,
                result => Ratio(
                    result.FullPackageTurnsA,
                    result.FullPackageTurnsA + result.PartialPackageTurnsA)),
            MeanFullPackageRateB = Avg(
                results,
                result => Ratio(
                    result.FullPackageTurnsB,
                    result.FullPackageTurnsB + result.PartialPackageTurnsB)),
            MeanShotsA = Avg(results, result => result.ShotsA),
            MeanShotsB = Avg(results, result => result.ShotsB),
            MeanHitsA = Avg(results, result => result.HitsA),
            MeanHitsB = Avg(results, result => result.HitsB),
            MeanLaunchesA = Avg(results, result => result.LaunchesA),
            MeanLaunchesB = Avg(results, result => result.LaunchesB),
            MeanMissileHitsA = Avg(results, result => result.MissileHitsA),
            MeanMissileHitsB = Avg(results, result => result.MissileHitsB),
            MeanPdsAttemptsA = Avg(results, result => result.PdsAttemptsA),
            MeanPdsAttemptsB = Avg(results, result => result.PdsAttemptsB),
            MeanPdsInterceptsA = Avg(results, result => result.PdsInterceptsA),
            MeanPdsInterceptsB = Avg(results, result => result.PdsInterceptsB),
            MeanHeldDeclarationsA = Avg(results, result => result.HeldDeclarationsA),
            MeanHeldDeclarationsB = Avg(results, result => result.HeldDeclarationsB),
            MeanHeldAttemptsA = Avg(results, result => result.HeldAttemptsA),
            MeanHeldAttemptsB = Avg(results, result => result.HeldAttemptsB),
            MeanHeldInterceptsA = Avg(results, result => result.HeldInterceptsA),
            MeanHeldInterceptsB = Avg(results, result => result.HeldInterceptsB),
            MeanHeldUnusedA = Avg(results, result => result.HeldUnusedA),
            MeanHeldUnusedB = Avg(results, result => result.HeldUnusedB),
            MeanHeldPowerEarmarkedA = Avg(
                results,
                result => Ratio(result.HeldPowerEarmarkedA, result.Turns)),
            MeanHeldPowerEarmarkedB = Avg(
                results,
                result => Ratio(result.HeldPowerEarmarkedB, result.Turns)),
            MeanOffensivePowerSpentA = Avg(
                results,
                result => Ratio(result.OffensiveWeaponPowerSpentA, result.Turns)),
            MeanOffensivePowerSpentB = Avg(
                results,
                result => Ratio(result.OffensiveWeaponPowerSpentB, result.Turns)),
            MeanOffensiveCyclesLostA = Avg(
                results,
                result => result.OffensiveCyclesLostA),
            MeanOffensiveCyclesLostB = Avg(
                results,
                result => result.OffensiveCyclesLostB),
            MeanEnvelopePerTurnA = Avg(
                results,
                result => Ratio(result.TotalEnvelopeA, result.Turns)),
            MeanEnvelopePerTurnB = Avg(
                results,
                result => Ratio(result.TotalEnvelopeB, result.Turns)),
            MeanPoweredPerTurnA = Avg(
                results,
                result => Ratio(result.TotalPoweredA, result.Turns)),
            MeanPoweredPerTurnB = Avg(
                results,
                result => Ratio(result.TotalPoweredB, result.Turns)),
            MeanSpentPerTurnA = Avg(
                results,
                result => Ratio(result.TotalSpentA, result.Turns)),
            MeanSpentPerTurnB = Avg(
                results,
                result => Ratio(result.TotalSpentB, result.Turns)),
            MeanUnusedPerTurnA = Avg(
                results,
                result => Ratio(result.TotalUnusedA, result.Turns)),
            MeanUnusedPerTurnB = Avg(
                results,
                result => Ratio(result.TotalUnusedB, result.Turns)),
            MeanBaseReactorPowerPerTurnA = Avg(
                results,
                result => Ratio(result.BaseReactorPowerA, result.Turns)),
            MeanBaseReactorPowerPerTurnB = Avg(
                results,
                result => Ratio(result.BaseReactorPowerB, result.Turns)),
            MeanAuxiliaryPowerA = Avg(results, result => result.AuxiliaryPowerA),
            MeanAuxiliaryPowerB = Avg(results, result => result.AuxiliaryPowerB),
            MeanReactorOverloadPowerA = Avg(
                results,
                result => result.ReactorOverloadPowerA),
            MeanReactorOverloadPowerB = Avg(
                results,
                result => result.ReactorOverloadPowerB),
            MeanCombatBatteryPowerA = Avg(
                results,
                result => result.CombatBatteryPowerA),
            MeanCombatBatteryPowerB = Avg(
                results,
                result => result.CombatBatteryPowerB),
            MeanCombatBatteryChargesA = Avg(
                results,
                result => result.CombatBatteryChargesA),
            MeanCombatBatteryChargesB = Avg(
                results,
                result => result.CombatBatteryChargesB),
            MeanCapacitorDischargedA = Avg(
                results,
                result => result.CapacitorDischargedA),
            MeanCapacitorDischargedB = Avg(
                results,
                result => result.CapacitorDischargedB),
            MeanCapacitorChargedA = Avg(
                results,
                result => result.CapacitorChargedA),
            MeanCapacitorChargedB = Avg(
                results,
                result => result.CapacitorChargedB),
            MeanCapacitorFinalA = Avg(results, result => result.CapacitorFinalA),
            MeanCapacitorFinalB = Avg(results, result => result.CapacitorFinalB),
            MeanPdsPowerPerTurnA = Avg(
                results,
                result => Ratio(result.PdsPowerCommittedA, result.Turns)),
            MeanPdsPowerPerTurnB = Avg(
                results,
                result => Ratio(result.PdsPowerCommittedB, result.Turns)),
            MeanSensorPowerPerTurnA = Avg(
                results,
                result => Ratio(result.SensorPowerCommittedA, result.Turns)),
            MeanSensorPowerPerTurnB = Avg(
                results,
                result => Ratio(result.SensorPowerCommittedB, result.Turns)),
            MeanEcmPowerPerTurnA = Avg(
                results,
                result => Ratio(result.EcmPowerCommittedA, result.Turns)),
            MeanEcmPowerPerTurnB = Avg(
                results,
                result => Ratio(result.EcmPowerCommittedB, result.Turns)),
            MeanEccmPowerPerTurnA = Avg(
                results,
                result => Ratio(result.EccmPowerCommittedA, result.Turns)),
            MeanEccmPowerPerTurnB = Avg(
                results,
                result => Ratio(result.EccmPowerCommittedB, result.Turns)),
            MeanHardenerPowerPerTurnA = Avg(
                results,
                result => Ratio(result.ShieldHardenerPowerCommittedA, result.Turns)),
            MeanHardenerPowerPerTurnB = Avg(
                results,
                result => Ratio(result.ShieldHardenerPowerCommittedB, result.Turns)),
            MeanShieldRechargePowerPerTurnA = Avg(
                results,
                result => Ratio(result.ShieldRechargePowerSpentA, result.Turns)),
            MeanShieldRechargePowerPerTurnB = Avg(
                results,
                result => Ratio(result.ShieldRechargePowerSpentB, result.Turns)),
            MeanShieldOvercapacityAddedA = Avg(
                results,
                result => result.ShieldOvercapacityAddedA),
            MeanShieldOvercapacityAddedB = Avg(
                results,
                result => result.ShieldOvercapacityAddedB),
            MeanEnergyOverloadShotsA = Avg(
                results,
                result => result.EnergyOverloadShotsA),
            MeanEnergyOverloadShotsB = Avg(
                results,
                result => result.EnergyOverloadShotsB),
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
            MeanUnfundedPdsA = Avg(results, result => result.UnfundedPdsA),
            MeanUnfundedPdsB = Avg(results, result => result.UnfundedPdsB),
            MeanUnfundedSensorsA = Avg(results, result => result.UnfundedSensorsA),
            MeanUnfundedSensorsB = Avg(results, result => result.UnfundedSensorsB),
            MeanUnfundedEcmA = Avg(results, result => result.UnfundedEcmA),
            MeanUnfundedEcmB = Avg(results, result => result.UnfundedEcmB),
            MeanUnfundedEccmA = Avg(results, result => result.UnfundedEccmA),
            MeanUnfundedEccmB = Avg(results, result => result.UnfundedEccmB),
            MeanUnfundedHardenerA = Avg(results, result => result.UnfundedHardenerA),
            MeanUnfundedHardenerB = Avg(results, result => result.UnfundedHardenerB),
            MeanUnfundedEvmA = Avg(results, result => result.UnfundedEvmA),
            MeanUnfundedEvmB = Avg(results, result => result.UnfundedEvmB),
            MeanUnfundedShieldOverloadA = Avg(
                results,
                result => result.UnfundedShieldOverloadA),
            MeanUnfundedShieldOverloadB = Avg(
                results,
                result => result.UnfundedShieldOverloadB),
            MeanUnfundedRechargeA = Avg(results, result => result.UnfundedRechargeA),
            MeanUnfundedRechargeB = Avg(results, result => result.UnfundedRechargeB),
            MeanUnfundedHeldA = Avg(results, result => result.UnfundedHeldA),
            MeanUnfundedHeldB = Avg(results, result => result.UnfundedHeldB),
            MeanUnfundedWeaponA = Avg(results, result => result.UnfundedWeaponA),
            MeanUnfundedWeaponB = Avg(results, result => result.UnfundedWeaponB),
            MeanReactorStrainA = Avg(results, result => result.ReactorStrainA),
            MeanReactorStrainB = Avg(results, result => result.ReactorStrainB),
            MeanEnergyStrainA = Avg(results, result => result.EnergyStrainA),
            MeanEnergyStrainB = Avg(results, result => result.EnergyStrainB),
            MeanSensorStrainA = Avg(results, result => result.SensorStrainA),
            MeanSensorStrainB = Avg(results, result => result.SensorStrainB),
            MeanEcmStrainA = Avg(results, result => result.EcmStrainA),
            MeanEcmStrainB = Avg(results, result => result.EcmStrainB),
            MeanEccmStrainA = Avg(results, result => result.EccmStrainA),
            MeanEccmStrainB = Avg(results, result => result.EccmStrainB),
            MeanHardenerStrainA = Avg(results, result => result.HardenerStrainA),
            MeanHardenerStrainB = Avg(results, result => result.HardenerStrainB),
            MeanShieldGeneratorStrainA = Avg(
                results,
                result => result.ShieldGeneratorStrainA),
            MeanShieldGeneratorStrainB = Avg(
                results,
                result => result.ShieldGeneratorStrainB),
            MeanHullA = Avg(results, result => result.HullA),
            MeanHullB = Avg(results, result => result.HullB),
            MeanAmmoRemainingA = Avg(results, result => result.AmmoRemainingA),
            MeanAmmoRemainingB = Avg(results, result => result.AmmoRemainingB),
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
}
