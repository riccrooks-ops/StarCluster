using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace StarCluster.ScenarioRunner.AuxiliaryTechnology;

public static class AuxiliaryComponentFoundationRunner
{
    private const string ExpectedSchemaVersion =
        "star-cluster-auxiliary-component-catalog-v1";
    private const int ExpectedComponentCount = 27;

    public static int Run(
        string catalogPath,
        string schemaPath,
        string outputDirectory,
        bool preflightOnly)
    {
        using JsonDocument schema = JsonDocument.Parse(File.ReadAllText(schemaPath));
        if (!schema.RootElement.TryGetProperty("$id", out JsonElement schemaId) ||
            !string.Equals(
                schemaId.GetString(),
                ExpectedSchemaVersion,
                StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "Unexpected Auxiliary catalog schema document.");
        }

        AuxiliaryCatalog catalog = JsonSerializer.Deserialize<AuxiliaryCatalog>(
            File.ReadAllText(catalogPath),
            JsonOptions()) ?? throw new InvalidOperationException(
                "Auxiliary component catalog could not be read.");
        IReadOnlyList<GateRow> gates = Validate(catalog);
        int failed = gates.Count(gate => !gate.Passed);

        Console.WriteLine(
            $"AUX foundation preflight: {catalog.InstallationClasses.Count} " +
            $"installation classes, {catalog.Components.Count} candidate families, " +
            $"{failed} failed gates.");
        if (preflightOnly)
        {
            return failed == 0 ? 0 : 1;
        }

        Directory.CreateDirectory(outputDirectory);
        WriteInstallationClasses(catalog, outputDirectory);
        WriteCatalog(catalog, outputDirectory);
        WriteAvailabilityGates(catalog, outputDirectory);
        WriteGates(gates, outputDirectory);
        WriteSummary(catalog, gates, outputDirectory);
        WriteResultHash(outputDirectory);

        Console.WriteLine(
            $"Auxiliary Component Foundation: {catalog.Components.Count} " +
            $"candidate families, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static IReadOnlyList<GateRow> Validate(AuxiliaryCatalog catalog)
    {
        var gates = new List<GateRow>();
        void Gate(string id, bool passed, string detail) =>
            gates.Add(new GateRow(id, passed, detail));

        Gate(
            "schema-version",
            string.Equals(
                catalog.SchemaVersion,
                ExpectedSchemaVersion,
                StringComparison.Ordinal),
            catalog.SchemaVersion);
        Gate("checkpoint-id", catalog.Checkpoint == 43, catalog.Checkpoint.ToString(
            CultureInfo.InvariantCulture));
        Gate(
            "catalog-candidate-only",
            string.Equals(catalog.Status, "candidate_only", StringComparison.Ordinal),
            catalog.Status);

        string[] expectedClasses =
        {
            "dedicated_core",
            "weapon_bay",
            "auxiliary_capacity",
        };
        Gate(
            "three-installation-classes",
            catalog.InstallationClasses.Count == expectedClasses.Length &&
            expectedClasses.All(expected => catalog.InstallationClasses.Any(
                item => string.Equals(item.Id, expected, StringComparison.Ordinal))),
            string.Join(",", catalog.InstallationClasses.Select(item => item.Id)));
        InstallationClassDocument? core = catalog.InstallationClasses.FirstOrDefault(
            item => string.Equals(item.Id, "dedicated_core", StringComparison.Ordinal));
        InstallationClassDocument? aux = catalog.InstallationClasses.FirstOrDefault(
            item => string.Equals(item.Id, "auxiliary_capacity", StringComparison.Ordinal));
        Gate(
            "core-does-not-consume-generic-aux",
            core is not null && !core.ConsumesGenericAuxiliaryCapacity,
            core?.ConsumesGenericAuxiliaryCapacity.ToString() ?? "missing");
        Gate(
            "aux-consumes-generic-aux",
            aux is not null && aux.ConsumesGenericAuxiliaryCapacity,
            aux?.ConsumesGenericAuxiliaryCapacity.ToString() ?? "missing");
        Gate(
            "core-is-not-free",
            !catalog.Foundation.CoreMeansFree &&
            core is not null && core.NotFreeFactors.Count >= 5,
            $"coreMeansFree={catalog.Foundation.CoreMeansFree}; factors=" +
            (core?.NotFreeFactors.Count ?? 0).ToString(CultureInfo.InvariantCulture));
        Gate(
            "no-standard-aux-tree",
            !catalog.Foundation.StandardAuxiliaryResearchTree,
            catalog.Foundation.StandardAuxiliaryResearchTree.ToString());
        Gate(
            "no-mechanics-rewrite",
            !catalog.Foundation.ExistingCombatMechanicsRevisedByThisCheckpoint,
            catalog.Foundation.ExistingCombatMechanicsRevisedByThisCheckpoint.ToString());
        Gate(
            "stripped-fixture-zero-aux-allowed",
            catalog.Foundation.StrippedCalibrationFixtureMayUseZeroAuxiliaryCapacity,
            catalog.Foundation.StrippedCalibrationFixtureMayUseZeroAuxiliaryCapacity.ToString());
        Gate(
            "normal-player-aux-value-not-promoted",
            catalog.Foundation.NormalPlayerHullBaselineAuxiliaryCapacity.Contains(
                "not_promoted", StringComparison.Ordinal),
            catalog.Foundation.NormalPlayerHullBaselineAuxiliaryCapacity);
        Gate(
            "candidate-family-count",
            catalog.Components.Count == ExpectedComponentCount,
            catalog.Components.Count.ToString(CultureInfo.InvariantCulture));
        Gate(
            "unique-family-ids",
            catalog.Components.Select(item => item.Id).Distinct(
                StringComparer.Ordinal).Count() == catalog.Components.Count,
            "IDs must be unique");
        Gate(
            "all-use-auxiliary-capacity",
            catalog.Components.All(item => string.Equals(
                item.InstallationClass,
                "auxiliary_capacity",
                StringComparison.Ordinal)),
            "Every catalog family is an AUX installation");
        Gate(
            "capacity-bounds",
            catalog.Components.All(item => item.CapacityCost is >= 1 and <= 3),
            "Capacity costs must be 1-3");
        Gate(
            "technology-floor-bounds",
            catalog.Components.All(item =>
                item.CandidateFirstStandardItemTl is >= 1 and <= 9 &&
                item.MinimumPrimaryResearchTl is >= 1 and <= 9 &&
                item.MinimumHullTl is >= 1 and <= 9 &&
                item.SupportFloors.All(floor => floor.MinimumTl is >= 1 and <= 9)),
            "All floors must be TL1-9");
        Gate(
            "support-floor-cap",
            catalog.Components.All(item => item.SupportFloors.Count <= 2),
            "No family may depend on more than two support categories");
        Gate(
            "candidate-only-components",
            catalog.Components.All(item =>
                string.Equals(item.AvailabilityStatus, "candidate_only", StringComparison.Ordinal) &&
                string.Equals(item.StandardPlayerAvailability, "not_promoted", StringComparison.Ordinal) &&
                item.FirstStandardItemTlMayOnlyMoveUpUntilPromoted),
            "All component floors remain candidate-only and upward-only");
        Gate(
            "raise-floor-first-policy",
            catalog.Components.All(item => string.Equals(
                item.EntryPolicy,
                "raise_starting_tl_before_reducing_established_mechanical_identity",
                StringComparison.Ordinal)) &&
            catalog.Foundation.BalanceEntryPolicy.Contains(
                "move", StringComparison.OrdinalIgnoreCase),
            catalog.Foundation.BalanceEntryPolicy);
        Gate(
            "high-risk-floor",
            catalog.Components.Where(item => string.Equals(
                item.BalanceRisk.Tier,
                "high",
                StringComparison.Ordinal)).All(item =>
                    item.CandidateFirstStandardItemTl >=
                    catalog.Foundation.HighRiskMinimumCandidateFloor),
            $"minimum={catalog.Foundation.HighRiskMinimumCandidateFloor}");

        var requiredFloors = new Dictionary<string, int>(StringComparer.Ordinal)
        {
            ["aux_energy_pds"] = 2,
            ["aux_auxiliary_reactor"] = 2,
            ["aux_power_capacitor"] = 2,
            ["aux_shield_hardener"] = 3,
            ["aux_energized_armor_controller"] = 3,
            ["aux_evasive_maneuver_system"] = 2,
            ["aux_ecm_suite"] = 2,
            ["aux_eccm_suite"] = 2,
            ["aux_tractor_projector"] = 3,
            ["aux_hangar_bay"] = 3,
        };
        Gate(
            "minimum-risk-floors",
            requiredFloors.All(pair => catalog.Components.Any(item =>
                string.Equals(item.Id, pair.Key, StringComparison.Ordinal) &&
                item.CandidateFirstStandardItemTl >= pair.Value)),
            string.Join(",", requiredFloors.Select(pair => $"{pair.Key}>={pair.Value}")));
        AuxiliaryComponentDocument? ecm = catalog.Components.FirstOrDefault(
            item => string.Equals(item.Id, "aux_ecm_suite", StringComparison.Ordinal));
        AuxiliaryComponentDocument? eccm = catalog.Components.FirstOrDefault(
            item => string.Equals(item.Id, "aux_eccm_suite", StringComparison.Ordinal));
        Gate(
            "ecm-eccm-paired-floor",
            ecm is not null && eccm is not null &&
            ecm.CandidateFirstStandardItemTl == eccm.CandidateFirstStandardItemTl,
            $"ECM={ecm?.CandidateFirstStandardItemTl}; ECCM={eccm?.CandidateFirstStandardItemTl}");
        Gate(
            "no-standard-cloak",
            catalog.Foundation.ExcludedStandardCapabilities.Contains(
                "cloak", StringComparer.OrdinalIgnoreCase) &&
            catalog.Components.All(item =>
                !item.Id.Contains("cloak", StringComparison.OrdinalIgnoreCase) &&
                !item.DisplayName.Contains("cloak", StringComparison.OrdinalIgnoreCase)),
            "Cloak remains rare/alien/Precursor rather than standard player AUX");
        Gate(
            "fixture-evidence-is-not-promotion",
            catalog.Components.All(item =>
                !string.IsNullOrWhiteSpace(item.Tl1FixtureEvidence) &&
                string.Equals(item.StandardPlayerAvailability, "not_promoted", StringComparison.Ordinal)),
            "Fixture evidence is retained separately from availability");

        return gates.AsReadOnly();
    }

    private static void WriteInstallationClasses(
        AuxiliaryCatalog catalog,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "installation_class_id,display_name,consumes_generic_auxiliary_capacity,not_free_factor_count,duplicate_rule,description",
        };
        lines.AddRange(catalog.InstallationClasses.Select(item => string.Join(",",
            Csv(item.Id),
            Csv(item.DisplayName),
            Csv(item.ConsumesGenericAuxiliaryCapacity.ToString().ToLowerInvariant()),
            Csv(item.NotFreeFactors.Count.ToString(CultureInfo.InvariantCulture)),
            Csv(item.DuplicateRule),
            Csv(item.Description))));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "installation-classes.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteCatalog(
        AuxiliaryCatalog catalog,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "auxiliary_family_id,display_name,role,candidate_first_standard_item_tl,primary_research_category,minimum_primary_research_tl,support_floors,minimum_hull_tl,capacity_cost,power_behavior,balance_risk,availability_status",
        };
        lines.AddRange(catalog.Components.OrderBy(item => item.Id, StringComparer.Ordinal).Select(
            item => string.Join(",",
                Csv(item.Id),
                Csv(item.DisplayName),
                Csv(item.Role),
                Csv(item.CandidateFirstStandardItemTl.ToString(CultureInfo.InvariantCulture)),
                Csv(item.PrimaryResearchCategory),
                Csv(item.MinimumPrimaryResearchTl.ToString(CultureInfo.InvariantCulture)),
                Csv(string.Join(";", item.SupportFloors.Select(
                    floor => $"{floor.TechnologyId}>={floor.MinimumTl}"))),
                Csv(item.MinimumHullTl.ToString(CultureInfo.InvariantCulture)),
                Csv(item.CapacityCost.ToString(CultureInfo.InvariantCulture)),
                Csv(item.TacticalPowerBehavior.Mode),
                Csv(item.BalanceRisk.Tier),
                Csv(item.AvailabilityStatus))));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "catalog.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteAvailabilityGates(
        AuxiliaryCatalog catalog,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "auxiliary_family_id,item_floor,primary_floor,maximum_support_floor,minimum_hull_tl,calculated_static_floor,balance_risk,standard_player_availability,entry_policy",
        };
        lines.AddRange(catalog.Components.OrderBy(item => item.Id, StringComparer.Ordinal).Select(
            item =>
            {
                int support = item.SupportFloors.Count == 0
                    ? 1
                    : item.SupportFloors.Max(floor => floor.MinimumTl);
                int calculated = new[]
                {
                    item.CandidateFirstStandardItemTl,
                    item.MinimumPrimaryResearchTl,
                    support,
                    item.MinimumHullTl,
                }.Max();
                return string.Join(",",
                    Csv(item.Id),
                    Csv(item.CandidateFirstStandardItemTl.ToString(CultureInfo.InvariantCulture)),
                    Csv(item.MinimumPrimaryResearchTl.ToString(CultureInfo.InvariantCulture)),
                    Csv(support.ToString(CultureInfo.InvariantCulture)),
                    Csv(item.MinimumHullTl.ToString(CultureInfo.InvariantCulture)),
                    Csv(calculated.ToString(CultureInfo.InvariantCulture)),
                    Csv(item.BalanceRisk.Tier),
                    Csv(item.StandardPlayerAvailability),
                    Csv(item.EntryPolicy));
            }));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "availability-gates.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteGates(
        IReadOnlyList<GateRow> gates,
        string outputDirectory)
    {
        var lines = new List<string> { "gate_id,passed,detail" };
        lines.AddRange(gates.Select(gate => string.Join(",",
            Csv(gate.Id),
            Csv(gate.Passed.ToString().ToLowerInvariant()),
            Csv(gate.Detail))));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "gates.csv"),
            lines,
            new UTF8Encoding(false));
    }

    private static void WriteSummary(
        AuxiliaryCatalog catalog,
        IReadOnlyList<GateRow> gates,
        string outputDirectory)
    {
        object summary = new
        {
            schemaVersion = catalog.SchemaVersion,
            catalogId = catalog.Id,
            checkpoint = catalog.Checkpoint,
            status = catalog.Status,
            installationClassCount = catalog.InstallationClasses.Count,
            auxiliaryFamilyCount = catalog.Components.Count,
            candidateFloorCounts = catalog.Components
                .GroupBy(item => item.CandidateFirstStandardItemTl)
                .OrderBy(group => group.Key)
                .ToDictionary(group => $"tl{group.Key}", group => group.Count()),
            highRiskFamilyCount = catalog.Components.Count(item => string.Equals(
                item.BalanceRisk.Tier,
                "high",
                StringComparison.Ordinal)),
            mechanicsRevised = catalog.Foundation.ExistingCombatMechanicsRevisedByThisCheckpoint,
            standardAuxiliaryResearchTree = catalog.Foundation.StandardAuxiliaryResearchTree,
            coreMeansFree = catalog.Foundation.CoreMeansFree,
            availabilityFormula = catalog.Foundation.AvailabilityFormula,
            balanceEntryPolicy = catalog.Foundation.BalanceEntryPolicy,
            gateCount = gates.Count,
            failedGates = gates.Count(gate => !gate.Passed),
        };
        File.WriteAllText(
            Path.Combine(outputDirectory, "summary.json"),
            JsonSerializer.Serialize(summary, new JsonSerializerOptions
            {
                WriteIndented = true,
            }) + Environment.NewLine,
            new UTF8Encoding(false));
    }

    private static void WriteResultHash(string outputDirectory)
    {
        string[] paths = Directory.GetFiles(outputDirectory)
            .Where(path => !string.Equals(
                Path.GetFileName(path),
                "result.sha256.txt",
                StringComparison.OrdinalIgnoreCase))
            .OrderBy(path => Path.GetFileName(path), StringComparer.Ordinal)
            .ToArray();
        using var stream = new MemoryStream();
        foreach (string path in paths)
        {
            byte[] name = Encoding.UTF8.GetBytes(Path.GetFileName(path) + "\n");
            stream.Write(name, 0, name.Length);
            byte[] data = File.ReadAllBytes(path);
            stream.Write(data, 0, data.Length);
            stream.WriteByte((byte)'\n');
        }
        string hash = Convert.ToHexString(SHA256.HashData(stream.ToArray()))
            .ToLowerInvariant();
        File.WriteAllText(
            Path.Combine(outputDirectory, "result.sha256.txt"),
            hash + Environment.NewLine,
            new UTF8Encoding(false));
    }

    private static string Csv(string value)
    {
        string escaped = value.Replace("\"", "\"\"", StringComparison.Ordinal);
        return $"\"{escaped}\"";
    }

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = true,
    };

    private sealed record GateRow(string Id, bool Passed, string Detail);

    private sealed class AuxiliaryCatalog
    {
        public string SchemaVersion { get; init; } = string.Empty;
        public string Id { get; init; } = string.Empty;
        public string Title { get; init; } = string.Empty;
        public string Status { get; init; } = string.Empty;
        public int Checkpoint { get; init; }
        public List<InstallationClassDocument> InstallationClasses { get; init; } = new();
        public FoundationDocument Foundation { get; init; } = new();
        public List<AuxiliaryComponentDocument> Components { get; init; } = new();
    }

    private sealed class InstallationClassDocument
    {
        public string Id { get; init; } = string.Empty;
        public string DisplayName { get; init; } = string.Empty;
        public string Description { get; init; } = string.Empty;
        public bool ConsumesGenericAuxiliaryCapacity { get; init; }
        public List<string> NotFreeFactors { get; init; } = new();
        public string DuplicateRule { get; init; } = string.Empty;
    }

    private sealed class FoundationDocument
    {
        public bool StandardAuxiliaryResearchTree { get; init; }
        public bool CoreMeansFree { get; init; }
        public bool ExistingCombatMechanicsRevisedByThisCheckpoint { get; init; }
        public bool StrippedCalibrationFixtureMayUseZeroAuxiliaryCapacity { get; init; }
        public string NormalPlayerHullBaselineAuxiliaryCapacity { get; init; } = string.Empty;
        public string HullTlRole { get; init; } = string.Empty;
        public string AvailabilityFormula { get; init; } = string.Empty;
        public string AvailabilityInterpretation { get; init; } = string.Empty;
        public string Tl1FixtureEvidencePolicy { get; init; } = string.Empty;
        public string BalanceEntryPolicy { get; init; } = string.Empty;
        public List<string> HighRiskFunctions { get; init; } = new();
        public int HighRiskMinimumCandidateFloor { get; init; }
        public List<string> ExcludedStandardCapabilities { get; init; } = new();
        public string AlienAndPrecursorPolicy { get; init; } = string.Empty;
    }

    private sealed class AuxiliaryComponentDocument
    {
        public string Id { get; init; } = string.Empty;
        public string DisplayName { get; init; } = string.Empty;
        public string Role { get; init; } = string.Empty;
        public string InstallationClass { get; init; } = string.Empty;
        public int CandidateFirstStandardItemTl { get; init; }
        public string PrimaryResearchCategory { get; init; } = string.Empty;
        public int MinimumPrimaryResearchTl { get; init; }
        public List<SupportFloorDocument> SupportFloors { get; init; } = new();
        public int MinimumHullTl { get; init; }
        public int CapacityCost { get; init; }
        public TacticalPowerBehaviorDocument TacticalPowerBehavior { get; init; } = new();
        public string StackingRule { get; init; } = string.Empty;
        public DamageProfileDocument DamageProfile { get; init; } = new();
        public string Tl1FixtureEvidence { get; init; } = string.Empty;
        public BalanceRiskDocument BalanceRisk { get; init; } = new();
        public List<string> BlockingConcerns { get; init; } = new();
        public string AvailabilityStatus { get; init; } = string.Empty;
        public bool FirstStandardItemTlMayOnlyMoveUpUntilPromoted { get; init; }
        public string StandardPlayerAvailability { get; init; } = string.Empty;
        public string EntryPolicy { get; init; } = string.Empty;
        public string Notes { get; init; } = string.Empty;
    }

    private sealed class SupportFloorDocument
    {
        public string TechnologyId { get; init; } = string.Empty;
        public int MinimumTl { get; init; }
    }

    private sealed class TacticalPowerBehaviorDocument
    {
        public string Mode { get; init; } = string.Empty;
        public string Amount { get; init; } = string.Empty;
        public string Notes { get; init; } = string.Empty;
    }

    private sealed class DamageProfileDocument
    {
        public bool Damageable { get; init; }
        public int CriticalExposure { get; init; }
        public string Notes { get; init; } = string.Empty;
    }

    private sealed class BalanceRiskDocument
    {
        public string Tier { get; init; } = string.Empty;
        public List<string> Flags { get; init; } = new();
    }
}
