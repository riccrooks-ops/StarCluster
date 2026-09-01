using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Power;

namespace StarCluster.ScenarioRunner.AuxiliaryTechnology;

public static class AuxiliaryResourceEnduranceRunner
{
    private const string ExpectedSchemaVersion =
        "star-cluster-auxiliary-resource-endurance-v1";
    private const string Checkpoint52StudyId =
        "aux-end01-resource-endurance-stress";
    private const string Checkpoint53StudyId =
        "aux-end02-resource-semantics-lock";

    public static int Run(
        string studyPath,
        string outputDirectory,
        bool preflightOnly)
    {
        ResourceEnduranceStudyDocument study = JsonSerializer.Deserialize<
            ResourceEnduranceStudyDocument>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                "Auxiliary resource-endurance study could not be read.");

        ValidateStudy(study);
        ResourceEnduranceEvidence evidence = BuildEvidence(study);
        IReadOnlyList<ResourceGate> gates = BuildGates(study, evidence);
        int failed = gates.Count(gate => !gate.Passed);

        Console.WriteLine(
            $"AUX resource-endurance preflight: " +
            $"{evidence.BatteryRows.Count} battery rows, " +
            $"{evidence.CapacitorRows.Count} capacitor turns, " +
            $"{evidence.AmmRows.Count} AMM rows, " +
            $"{evidence.MagazineRows.Count} magazine rows, " +
            $"{failed} failed gates.");
        if (preflightOnly)
        {
            return failed == 0 ? 0 : 1;
        }

        Directory.CreateDirectory(outputDirectory);
        WriteBatteryEvidence(evidence.BatteryRows, outputDirectory);
        WriteCapacitorEvidence(evidence.CapacitorRows, outputDirectory);
        WriteAmmEvidence(evidence.AmmRows, outputDirectory);
        WriteMagazineEvidence(evidence.MagazineRows, outputDirectory);
        WriteGates(gates, outputDirectory);
        WriteSummary(study, evidence, gates, outputDirectory);
        WriteResultHash(outputDirectory);

        Console.WriteLine(
            $"Auxiliary Resource Endurance: {failed} failed gates. " +
            $"Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static void ValidateStudy(ResourceEnduranceStudyDocument study)
    {
        bool identityValid = string.Equals(
                study.SchemaVersion, ExpectedSchemaVersion, StringComparison.Ordinal) &&
            ((study.Checkpoint == 52 && string.Equals(study.Id, Checkpoint52StudyId, StringComparison.Ordinal)) ||
             (study.Checkpoint == 53 && string.Equals(study.Id, Checkpoint53StudyId, StringComparison.Ordinal))) &&
            !string.IsNullOrWhiteSpace(study.Status) &&
            !string.IsNullOrWhiteSpace(study.Policy);
        if (!identityValid)
        {
            throw new InvalidOperationException(
                "Unexpected auxiliary resource-endurance study identity.");
        }
        if (study.CombatBattery.PowerPerCharge != 1 ||
            study.CombatBattery.CandidateCharges.Count == 0 ||
            study.CombatBattery.CandidateCharges.Any(value => value <= 0) ||
            study.CombatBattery.SurgeDemandPerEncounter.Count == 0 ||
            study.CombatBattery.SurgeDemandPerEncounter.Any(value => value <= 0) ||
            study.CombatBattery.EncounterCounts.Count == 0 ||
            study.CombatBattery.EncounterCounts.Any(value => value <= 0))
        {
            throw new InvalidOperationException(
                "Combat Battery endurance inputs are invalid.");
        }
        if (study.PowerCapacitor.Capacity != 1 ||
            study.PowerCapacitor.ChargeRate != 1 ||
            study.PowerCapacitor.DischargeRate != 1 ||
            study.PowerCapacitor.TurnPatterns.Count == 0 ||
            study.PowerCapacitor.TurnPatterns.Any(pattern =>
                string.IsNullOrWhiteSpace(pattern.Id) ||
                pattern.Operations.Count == 0 ||
                pattern.Operations.Any(operation =>
                    operation != "hold" && operation != "charge" &&
                    operation != "discharge")))
        {
            throw new InvalidOperationException(
                "Power Capacitor endurance inputs are invalid.");
        }
        if (study.Amm.RoundCandidates.Count == 0 ||
            study.Amm.RoundCandidates.Any(value => value <= 0) ||
            study.Amm.PdsAttemptsPerEncounter.Count == 0 ||
            study.Amm.PdsAttemptsPerEncounter.Any(value => value <= 0) ||
            study.Amm.EncounterCounts.Count == 0 ||
            study.Amm.EncounterCounts.Any(value => value <= 0))
        {
            throw new InvalidOperationException("AMM endurance inputs are invalid.");
        }
        ValidateMagazineInput(study.WeaponMagazines.Kinetic, "kinetic");
        ValidateMagazineInput(study.WeaponMagazines.Missile, "missile");
    }

    private static void ValidateMagazineInput(
        MagazineEnduranceInput input,
        string family)
    {
        if (input.BaseReserve <= 0 ||
            input.ExpansionBonusByTl.Count != 2 ||
            !input.ExpansionBonusByTl.ContainsKey("1") ||
            !input.ExpansionBonusByTl.ContainsKey("2") ||
            input.ExpansionBonusByTl.Values.Any(value => value <= 0) ||
            input.PackagesPerEncounter.Count == 0 ||
            input.PackagesPerEncounter.Any(value => value <= 0) ||
            input.EncounterCounts.Count == 0 ||
            input.EncounterCounts.Any(value => value <= 0))
        {
            throw new InvalidOperationException(
                $"{family} magazine endurance inputs are invalid.");
        }
    }

    private static ResourceEnduranceEvidence BuildEvidence(
        ResourceEnduranceStudyDocument study)
    {
        var batteryRows = new List<BatteryEnduranceRow>();
        foreach (int candidateCharges in study.CombatBattery.CandidateCharges)
        {
            foreach (int demandPerEncounter in
                study.CombatBattery.SurgeDemandPerEncounter)
            {
                foreach (int encounterCount in study.CombatBattery.EncounterCounts)
                {
                    var battery = new CombatBatteryState(
                        candidateCharges,
                        study.CombatBattery.PowerPerCharge,
                        dischargeLimitPerTurn: 1);
                    int supported = 0;
                    int requested = checked(demandPerEncounter * encounterCount);
                    for (int surge = 0; surge < requested; surge++)
                    {
                        if (battery.CurrentCharges == 0)
                        {
                            break;
                        }
                        var ledger = new TacticalPowerLedger();
                        ledger.BeginTurn(0);
                        battery.BeginTurn();
                        _ = battery.Discharge(ledger);
                        supported++;
                    }
                    batteryRows.Add(new BatteryEnduranceRow(
                        candidateCharges,
                        study.CombatBattery.PowerPerCharge,
                        demandPerEncounter,
                        encounterCount,
                        requested,
                        supported,
                        battery.CurrentCharges,
                        Percent(supported, requested),
                        supported < requested));
                }
            }
        }

        var capacitorRows = new List<CapacitorTurnRow>();
        foreach (CapacitorTurnPattern pattern in
            study.PowerCapacitor.TurnPatterns)
        {
            var capacitor = new CapacitorBankState(
                study.PowerCapacitor.Capacity,
                study.PowerCapacitor.ChargeRate,
                study.PowerCapacitor.DischargeRate);
            for (int index = 0; index < pattern.Operations.Count; index++)
            {
                string operation = pattern.Operations[index];
                var ledger = new TacticalPowerLedger();
                ledger.BeginTurn(1);
                capacitor.BeginTurn();
                bool succeeded = true;
                string detail = "hold";
                try
                {
                    if (operation == "charge")
                    {
                        int charged = capacitor.Charge(ledger, 1);
                        detail = $"spent {charged} reactor TP to recharge";
                    }
                    else if (operation == "discharge")
                    {
                        int discharged = capacitor.Discharge(ledger, 1);
                        detail = $"released {discharged} stored TP";
                    }
                }
                catch (InvalidOperationException exception)
                {
                    succeeded = false;
                    detail = exception.Message;
                }
                capacitorRows.Add(new CapacitorTurnRow(
                    pattern.Id,
                    index + 1,
                    operation,
                    succeeded,
                    ledger.Envelope - 1,
                    ledger.SpentPower,
                    capacitor.StoredPower,
                    detail));
            }
        }

        var ammRows = new List<AmmEnduranceRow>();
        foreach (int rounds in study.Amm.RoundCandidates)
        {
            foreach (int attemptsPerEncounter in
                study.Amm.PdsAttemptsPerEncounter)
            {
                foreach (int encounterCount in study.Amm.EncounterCounts)
                {
                    int requested = checked(attemptsPerEncounter * encounterCount);
                    int used = Math.Min(rounds, requested);
                    ammRows.Add(new AmmEnduranceRow(
                        rounds,
                        attemptsPerEncounter,
                        encounterCount,
                        requested,
                        used,
                        rounds - used,
                        Percent(used, requested),
                        used == requested));
                }
            }
        }

        var magazineRows = new List<MagazineEnduranceRow>();
        AddMagazineRows(
            magazineRows,
            "kinetic",
            study.WeaponMagazines.Kinetic);
        AddMagazineRows(
            magazineRows,
            "missile",
            study.WeaponMagazines.Missile);

        return new ResourceEnduranceEvidence(
            batteryRows,
            capacitorRows,
            ammRows,
            magazineRows);
    }

    private static void AddMagazineRows(
        ICollection<MagazineEnduranceRow> rows,
        string family,
        MagazineEnduranceInput input)
    {
        foreach (int tl in new[] { 1, 2 })
        {
            int bonus = input.ExpansionBonusByTl[
                tl.ToString(CultureInfo.InvariantCulture)];
            foreach (bool expanded in new[] { false, true })
            {
                int reserve = checked(input.BaseReserve + (expanded ? bonus : 0));
                foreach (int demand in input.PackagesPerEncounter)
                {
                    foreach (int encounters in input.EncounterCounts)
                    {
                        int requested = checked(demand * encounters);
                        int used = Math.Min(reserve, requested);
                        rows.Add(new MagazineEnduranceRow(
                            family,
                            tl,
                            expanded,
                            input.BaseReserve,
                            expanded ? bonus : 0,
                            reserve,
                            demand,
                            encounters,
                            requested,
                            used,
                            reserve - used,
                            Percent(used, requested),
                            used == requested));
                    }
                }
            }
        }
    }

    private static IReadOnlyList<ResourceGate> BuildGates(
        ResourceEnduranceStudyDocument study,
        ResourceEnduranceEvidence evidence)
    {
        var gates = new List<ResourceGate>();
        void Gate(string id, bool passed, string detail) =>
            gates.Add(new ResourceGate(id, passed, detail));

        if (study.Checkpoint == 52)
        {
            Gate(
                "battery-primary-and-fallback-candidates",
                study.CombatBattery.CandidateCharges.Contains(3) &&
                study.CombatBattery.CandidateCharges.Contains(2) &&
                study.CombatBattery.PowerPerCharge == 1,
                "Primary candidate is three +1 TP charges; two charges remains the first fallback diagnostic.");
            Gate(
                "battery-finite-campaign-resource",
                evidence.BatteryRows.All(row =>
                    row.SurgesSupported <= row.CandidateCharges &&
                    row.ChargesRemaining ==
                        row.CandidateCharges - row.SurgesSupported),
                "Combat Battery charges persist downward across the encounter sequence and do not auto-refill in this endurance study.");
            BatteryEnduranceRow? primaryBattery = evidence.BatteryRows.FirstOrDefault(row =>
                row.CandidateCharges == 3 && row.SurgeDemandPerEncounter == 1 &&
                row.EncounterCount == 4);
            Gate(
                "battery-three-charge-example",
                primaryBattery is not null &&
                primaryBattery.SurgesSupported == 3 &&
                primaryBattery.ChargesRemaining == 0 &&
                primaryBattery.DepletedBeforeSequenceEnd,
                primaryBattery is null
                    ? "missing"
                    : $"supported={primaryBattery.SurgesSupported}; remaining={primaryBattery.ChargesRemaining}");

            CapacitorTurnRow[] alternating = evidence.CapacitorRows
                .Where(row => row.PatternId == "alternating-demand")
                .OrderBy(row => row.Turn)
                .ToArray();
            Gate(
                "capacitor-alternating-cycle",
                alternating.Length == 5 && alternating.All(row => row.Succeeded) &&
                alternating.Count(row => row.Operation == "discharge") == 3 &&
                alternating.Count(row => row.Operation == "charge") == 2 &&
                alternating.Where(row => row.Operation == "charge")
                    .All(row => row.ReactorPowerSpent == 1) &&
                alternating.Where(row => row.Operation == "discharge")
                    .All(row => row.GeneratedPower == 1),
                "Discharge +1 TP, spend 1 TP on a later recharge turn, then discharge again.");
            CapacitorTurnRow[] backToBack = evidence.CapacitorRows
                .Where(row => row.PatternId == "back-to-back-demand")
                .OrderBy(row => row.Turn)
                .ToArray();
            Gate(
                "capacitor-no-free-back-to-back-burst",
                backToBack.Length == 4 && backToBack[0].Succeeded &&
                !backToBack[1].Succeeded && backToBack[2].Succeeded &&
                backToBack[3].Succeeded,
                "A second consecutive discharge fails until a later turn spends 1 TP to recharge.");
            Gate(
                "amm-endurance-candidates",
                new[] { 15, 20, 25, 30 }.All(
                    rounds => study.Amm.RoundCandidates.Contains(rounds)),
                string.Join(",", study.Amm.RoundCandidates));
            Gate(
                "amm-single-fight-not-forced-empty",
                evidence.AmmRows.Any(row => row.Rounds == 25 &&
                    row.AttemptsPerEncounter == 10 && row.EncounterCount == 1 &&
                    row.FullySupported && row.RoundsRemaining == 15) &&
                evidence.AmmRows.Any(row => row.Rounds == 30 &&
                    row.AttemptsPerEncounter == 10 && row.EncounterCount == 1 &&
                    row.FullySupported && row.RoundsRemaining == 20),
                "Primary 25/30-round AMM candidates retain meaningful reserve after a representative 10-attempt encounter.");
            Gate(
                "amm-multi-encounter-stress-can-bind",
                evidence.AmmRows.Any(row => row.Rounds == 15 &&
                    row.EncounterCount >= 2 && !row.FullySupported) &&
                evidence.AmmRows.Any(row => row.Rounds == 20 &&
                    row.EncounterCount >= 2 && !row.FullySupported),
                "Lower AMM candidates become meaningful over repeated encounters without requiring first-fight depletion.");
            Gate(
                "magazine-expansions-improve-endurance",
                new[] { "kinetic", "missile" }.All(family =>
                    evidence.MagazineRows.Any(expanded =>
                        expanded.Family == family && expanded.Expanded &&
                        evidence.MagazineRows.Any(baseline =>
                            baseline.Family == family && !baseline.Expanded &&
                            baseline.TechnologyLevel == expanded.TechnologyLevel &&
                            baseline.PackagesPerEncounter ==
                                expanded.PackagesPerEncounter &&
                            baseline.EncounterCount == expanded.EncounterCount &&
                            expanded.CoveragePercent > baseline.CoveragePercent))),
                "Kinetic and missile magazine expansions must create measurable repeated-engagement endurance in at least one stress lane.");
            Gate(
                "diagnostic-only-no-automatic-promotion",
                study.Status.Contains("diagnostic", StringComparison.OrdinalIgnoreCase) &&
                study.Policy.Contains("does not promote", StringComparison.OrdinalIgnoreCase),
                study.Policy);
        }
        else
        {
            Gate(
                "battery-three-charge-primary",
                study.CombatBattery.CandidateCharges.SequenceEqual(new[] { 3 }) &&
                study.CombatBattery.PowerPerCharge == 1,
                "Checkpoint 53 locks the primary Combat Battery at three +1 TP charges.");
            Gate(
                "battery-no-encounter-cap",
                evidence.BatteryRows.Any(row => row.CandidateCharges == 3 &&
                    row.SurgeDemandPerEncounter == 3 && row.EncounterCount == 1 &&
                    row.SurgesSupported == 3 && row.ChargesRemaining == 0),
                "Three distinct tactical turns in one protracted encounter may discharge all three charges; the limit is one discharge per turn, not one per encounter.");
            Gate(
                "battery-finite-campaign-resource",
                evidence.BatteryRows.All(row => row.SurgesSupported <= row.CandidateCharges &&
                    row.ChargesRemaining == row.CandidateCharges - row.SurgesSupported),
                "Expended Combat Battery charges remain expended across encounters until replenished outside this tactical sequence.");
            CapacitorTurnRow[] alternating53 = evidence.CapacitorRows
                .Where(row => row.PatternId == "alternating-demand").OrderBy(row => row.Turn).ToArray();
            Gate(
                "capacitor-alternating-cycle",
                alternating53.Length == 5 && alternating53.All(row => row.Succeeded) &&
                alternating53.Count(row => row.Operation == "discharge") == 3 &&
                alternating53.Count(row => row.Operation == "charge") == 2,
                "The TL2 capacitor shifts one TP between turns and remains reusable when a later turn pays to recharge it.");
            CapacitorTurnRow[] backToBack53 = evidence.CapacitorRows
                .Where(row => row.PatternId == "back-to-back-demand").OrderBy(row => row.Turn).ToArray();
            Gate(
                "capacitor-no-free-back-to-back-burst",
                backToBack53.Length == 4 && backToBack53[0].Succeeded && !backToBack53[1].Succeeded &&
                backToBack53[2].Succeeded && backToBack53[3].Succeeded,
                "A second consecutive discharge still requires a later 1 TP recharge turn.");
            Gate(
                "amm-twenty-five-round-lock",
                study.Amm.RoundCandidates.SequenceEqual(new[] { 25 }),
                "Checkpoint 53 keeps AMM ammunition at 25 rounds while campaign endurance remains observable.");
            Gate(
                "amm-first-fight-reserve",
                evidence.AmmRows.Any(row => row.Rounds == 25 && row.AttemptsPerEncounter == 10 &&
                    row.EncounterCount == 1 && row.FullySupported && row.RoundsRemaining == 15),
                "A representative 10-attempt missile-defense fight leaves a meaningful AMM reserve.");
            Gate(
                "amm-repeated-fights-can-bind",
                evidence.AmmRows.Any(row => row.Rounds == 25 && row.EncounterCount >= 3 && !row.FullySupported),
                "AMM scarcity may matter across repeated missile-heavy fights without forcing depletion in the first fight.");
            Gate(
                "magazine-expansions-improve-endurance",
                new[] { "kinetic", "missile" }.All(family => evidence.MagazineRows.Any(expanded =>
                    expanded.Family == family && expanded.Expanded && evidence.MagazineRows.Any(baseline =>
                        baseline.Family == family && !baseline.Expanded &&
                        baseline.TechnologyLevel == expanded.TechnologyLevel &&
                        baseline.PackagesPerEncounter == expanded.PackagesPerEncounter &&
                        baseline.EncounterCount == expanded.EncounterCount &&
                        expanded.CoveragePercent > baseline.CoveragePercent))),
                "Kinetic and missile magazine expansions retain measurable repeated-engagement endurance value.");
            Gate(
                "diagnostic-only-no-automatic-promotion",
                study.Status.Contains("diagnostic", StringComparison.OrdinalIgnoreCase) &&
                study.Policy.Contains("does not promote", StringComparison.OrdinalIgnoreCase),
                study.Policy);
        }
        return gates.AsReadOnly();
    }

    private static double Percent(int numerator, int denominator) =>
        denominator <= 0 ? 0.0 : 100.0 * numerator / denominator;

    private static void WriteBatteryEvidence(
        IReadOnlyList<BatteryEnduranceRow> rows,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "candidate_charges,power_per_charge,surge_demand_per_encounter,encounter_count,total_surge_demand,surges_supported,charges_remaining,coverage_percent,depleted_before_sequence_end"
        };
        lines.AddRange(rows.Select(row => string.Join(',', new[]
        {
            I(row.CandidateCharges), I(row.PowerPerCharge),
            I(row.SurgeDemandPerEncounter), I(row.EncounterCount),
            I(row.TotalSurgeDemand), I(row.SurgesSupported),
            I(row.ChargesRemaining), D(row.CoveragePercent),
            row.DepletedBeforeSequenceEnd.ToString(CultureInfo.InvariantCulture),
        })));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "combat-battery-endurance.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteCapacitorEvidence(
        IReadOnlyList<CapacitorTurnRow> rows,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "pattern_id,turn,operation,succeeded,generated_power,reactor_power_spent,stored_power_after,detail"
        };
        lines.AddRange(rows.Select(row => string.Join(',', new[]
        {
            Csv(row.PatternId), I(row.Turn), Csv(row.Operation),
            row.Succeeded.ToString(CultureInfo.InvariantCulture),
            I(row.GeneratedPower), I(row.ReactorPowerSpent),
            I(row.StoredPowerAfter), Csv(row.Detail),
        })));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "power-capacitor-cycle.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteAmmEvidence(
        IReadOnlyList<AmmEnduranceRow> rows,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "rounds,attempts_per_encounter,encounter_count,total_attempts_requested,rounds_used,rounds_remaining,coverage_percent,fully_supported"
        };
        lines.AddRange(rows.Select(row => string.Join(',', new[]
        {
            I(row.Rounds), I(row.AttemptsPerEncounter), I(row.EncounterCount),
            I(row.TotalAttemptsRequested), I(row.RoundsUsed),
            I(row.RoundsRemaining), D(row.CoveragePercent),
            row.FullySupported.ToString(CultureInfo.InvariantCulture),
        })));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "amm-endurance.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteMagazineEvidence(
        IReadOnlyList<MagazineEnduranceRow> rows,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "family,technology_level,expanded,base_reserve,expansion_bonus,total_reserve,packages_per_encounter,encounter_count,total_packages_requested,packages_used,packages_remaining,coverage_percent,fully_supported"
        };
        lines.AddRange(rows.Select(row => string.Join(',', new[]
        {
            Csv(row.Family), I(row.TechnologyLevel),
            row.Expanded.ToString(CultureInfo.InvariantCulture),
            I(row.BaseReserve), I(row.ExpansionBonus), I(row.TotalReserve),
            I(row.PackagesPerEncounter), I(row.EncounterCount),
            I(row.TotalPackagesRequested), I(row.PackagesUsed),
            I(row.PackagesRemaining), D(row.CoveragePercent),
            row.FullySupported.ToString(CultureInfo.InvariantCulture),
        })));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "magazine-endurance.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteGates(
        IReadOnlyList<ResourceGate> gates,
        string outputDirectory)
    {
        File.WriteAllLines(
            Path.Combine(outputDirectory, "gates.csv"),
            new[] { "gate_id,passed,detail" }.Concat(gates.Select(gate =>
                string.Join(',', new[]
                {
                    Csv(gate.Id),
                    gate.Passed.ToString(CultureInfo.InvariantCulture),
                    Csv(gate.Detail),
                }))),
            new UTF8Encoding(false));
    }

    private static void WriteSummary(
        ResourceEnduranceStudyDocument study,
        ResourceEnduranceEvidence evidence,
        IReadOnlyList<ResourceGate> gates,
        string outputDirectory)
    {
        object summary = study.Checkpoint == 52
            ? new
            {
                schemaVersion = ExpectedSchemaVersion,
                studyId = study.Id,
                checkpoint = study.Checkpoint,
                status = study.Status,
                policy = study.Policy,
                batteryRowCount = evidence.BatteryRows.Count,
                capacitorTurnRowCount = evidence.CapacitorRows.Count,
                ammRowCount = evidence.AmmRows.Count,
                magazineRowCount = evidence.MagazineRows.Count,
                batteryPrimaryCharges = 3,
                batteryFallbackCharges = 2,
                batteryPowerPerCharge = study.CombatBattery.PowerPerCharge,
                capacitorCapacity = study.PowerCapacitor.Capacity,
                capacitorChargeRate = study.PowerCapacitor.ChargeRate,
                capacitorDischargeRate = study.PowerCapacitor.DischargeRate,
                ammRoundCandidates = study.Amm.RoundCandidates,
                failedGates = gates.Count(gate => !gate.Passed),
                gates,
            }
            : new
            {
                schemaVersion = ExpectedSchemaVersion,
                studyId = study.Id,
                checkpoint = study.Checkpoint,
                status = study.Status,
                policy = study.Policy,
                batteryRowCount = evidence.BatteryRows.Count,
                capacitorTurnRowCount = evidence.CapacitorRows.Count,
                ammRowCount = evidence.AmmRows.Count,
                magazineRowCount = evidence.MagazineRows.Count,
                batteryPrimaryCharges = 3,
                batteryPowerPerCharge = study.CombatBattery.PowerPerCharge,
                batteryDischargeLimitPerTurn = 1,
                batteryEncounterDischargeCap = (int?)null,
                capacitorCapacity = study.PowerCapacitor.Capacity,
                capacitorChargeRate = study.PowerCapacitor.ChargeRate,
                capacitorDischargeRate = study.PowerCapacitor.DischargeRate,
                ammRoundCandidates = study.Amm.RoundCandidates,
                failedGates = gates.Count(gate => !gate.Passed),
                gates,
            };
        string json = JsonSerializer.Serialize(
            summary,
            new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(
            Path.Combine(outputDirectory, "summary.json"),
            json,
            new UTF8Encoding(false));
    }

    private static void WriteResultHash(string outputDirectory)
    {
        string summaryPath = Path.Combine(outputDirectory, "summary.json");
        string hash = Convert.ToHexString(SHA256.HashData(
            File.ReadAllBytes(summaryPath))).ToLowerInvariant();
        File.WriteAllText(
            Path.Combine(outputDirectory, "result.sha256.txt"),
            $"{hash}  summary.json{Environment.NewLine}",
            new UTF8Encoding(false));
    }

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = false,
        Converters = { new JsonStringEnumConverter() },
    };

    private static string I(int value) =>
        value.ToString(CultureInfo.InvariantCulture);

    private static string D(double value) =>
        value.ToString("F6", CultureInfo.InvariantCulture);

    private static string Csv(string value) =>
        '"' + value.Replace("\"", "\"\"") + '"';

    private sealed record ResourceEnduranceEvidence(
        IReadOnlyList<BatteryEnduranceRow> BatteryRows,
        IReadOnlyList<CapacitorTurnRow> CapacitorRows,
        IReadOnlyList<AmmEnduranceRow> AmmRows,
        IReadOnlyList<MagazineEnduranceRow> MagazineRows);

    private sealed record BatteryEnduranceRow(
        int CandidateCharges,
        int PowerPerCharge,
        int SurgeDemandPerEncounter,
        int EncounterCount,
        int TotalSurgeDemand,
        int SurgesSupported,
        int ChargesRemaining,
        double CoveragePercent,
        bool DepletedBeforeSequenceEnd);

    private sealed record CapacitorTurnRow(
        string PatternId,
        int Turn,
        string Operation,
        bool Succeeded,
        int GeneratedPower,
        int ReactorPowerSpent,
        int StoredPowerAfter,
        string Detail);

    private sealed record AmmEnduranceRow(
        int Rounds,
        int AttemptsPerEncounter,
        int EncounterCount,
        int TotalAttemptsRequested,
        int RoundsUsed,
        int RoundsRemaining,
        double CoveragePercent,
        bool FullySupported);

    private sealed record MagazineEnduranceRow(
        string Family,
        int TechnologyLevel,
        bool Expanded,
        int BaseReserve,
        int ExpansionBonus,
        int TotalReserve,
        int PackagesPerEncounter,
        int EncounterCount,
        int TotalPackagesRequested,
        int PackagesUsed,
        int PackagesRemaining,
        double CoveragePercent,
        bool FullySupported);

    private sealed record ResourceGate(string Id, bool Passed, string Detail);
}

internal sealed class ResourceEnduranceStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } = string.Empty;

    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("checkpoint")]
    public int Checkpoint { get; set; }

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("policy")]
    public string Policy { get; set; } = string.Empty;

    [JsonPropertyName("combatBattery")]
    public CombatBatteryEnduranceInput CombatBattery { get; set; } = new();

    [JsonPropertyName("powerCapacitor")]
    public PowerCapacitorEnduranceInput PowerCapacitor { get; set; } = new();

    [JsonPropertyName("amm")]
    public AmmEnduranceInput Amm { get; set; } = new();

    [JsonPropertyName("weaponMagazines")]
    public WeaponMagazineEnduranceInputs WeaponMagazines { get; set; } = new();
}

internal sealed class CombatBatteryEnduranceInput
{
    [JsonPropertyName("powerPerCharge")]
    public int PowerPerCharge { get; set; }

    [JsonPropertyName("candidateCharges")]
    public List<int> CandidateCharges { get; set; } = new();

    [JsonPropertyName("surgeDemandPerEncounter")]
    public List<int> SurgeDemandPerEncounter { get; set; } = new();

    [JsonPropertyName("encounterCounts")]
    public List<int> EncounterCounts { get; set; } = new();
}

internal sealed class PowerCapacitorEnduranceInput
{
    [JsonPropertyName("capacity")]
    public int Capacity { get; set; }

    [JsonPropertyName("chargeRate")]
    public int ChargeRate { get; set; }

    [JsonPropertyName("dischargeRate")]
    public int DischargeRate { get; set; }

    [JsonPropertyName("turnPatterns")]
    public List<CapacitorTurnPattern> TurnPatterns { get; set; } = new();
}

internal sealed class CapacitorTurnPattern
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("operations")]
    public List<string> Operations { get; set; } = new();
}

internal sealed class AmmEnduranceInput
{
    [JsonPropertyName("roundCandidates")]
    public List<int> RoundCandidates { get; set; } = new();

    [JsonPropertyName("pdsAttemptsPerEncounter")]
    public List<int> PdsAttemptsPerEncounter { get; set; } = new();

    [JsonPropertyName("encounterCounts")]
    public List<int> EncounterCounts { get; set; } = new();
}

internal sealed class WeaponMagazineEnduranceInputs
{
    [JsonPropertyName("kinetic")]
    public MagazineEnduranceInput Kinetic { get; set; } = new();

    [JsonPropertyName("missile")]
    public MagazineEnduranceInput Missile { get; set; } = new();
}

internal sealed class MagazineEnduranceInput
{
    [JsonPropertyName("baseReserve")]
    public int BaseReserve { get; set; }

    [JsonPropertyName("expansionBonusByTl")]
    public Dictionary<string, int> ExpansionBonusByTl { get; set; } =
        new(StringComparer.Ordinal);

    [JsonPropertyName("packagesPerEncounter")]
    public List<int> PackagesPerEncounter { get; set; } = new();

    [JsonPropertyName("encounterCounts")]
    public List<int> EncounterCounts { get; set; } = new();
}
