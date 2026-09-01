using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Combat.Weapons;
using StarCluster.ScenarioRunner.TL1;
using StarCluster.ScenarioRunner.TL1Calibration;
using StarCluster.ScenarioRunner.TL1SensorEw;

namespace StarCluster.ScenarioRunner.CrossTlIntegration;

public static class CrossTlBuildPermutationRunner
{
    private const string SchemaVersionV1 = "star-cluster-cross-tl-build-permutation-v1";
    private const string SchemaVersionV2 = "star-cluster-cross-tl-build-permutation-v2";
    private const string SchemaVersionV3 = "star-cluster-cross-tl-build-permutation-v3";
    private const string SchemaVersionV4 = "star-cluster-cross-tl-build-permutation-v4";
    private const string SchemaVersionV5 = "star-cluster-cross-tl-build-permutation-v5";
    private const string SchemaVersionV6 = "star-cluster-cross-tl-build-permutation-v6";
    private const string SchemaVersionV7 = "star-cluster-cross-tl-build-permutation-v7";

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        bool preflightOnly)
    {
        CrossTlBuildPermutationDocument study = JsonSerializer.Deserialize<CrossTlBuildPermutationDocument>(
            File.ReadAllText(studyPath), JsonOptions()) ?? throw new InvalidOperationException(
                "Cross-TL build-permutation definition could not be read.");
        string baselineHash = Sha256File(baselinePath);
        string studyHash = Sha256File(studyPath);
        CrossTlEnumerationResult enumeration = ValidateAndEnumerate(study);
        CrossTlReadinessContext? readiness = IsMatchedReadinessSchema(study.SchemaVersion)
            ? LoadReadinessContext(study, baselinePath)
            : null;
        bool exactEdgeSelection = study.ExactEdgePairingSelection?.Enabled == true;
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells =
            IsMatchedReadinessSchema(study.SchemaVersion) && !exactEdgeSelection
                ? BuildPopulationCells(study, enumeration.LegalBuilds)
                : new Dictionary<string, CrossTlPopulationCell>(StringComparer.Ordinal);
        IReadOnlyList<CrossTlProgressionEdge> progressionEdges = BuildProgressionLattice(
            study, enumeration.LegalBuilds);

        Directory.CreateDirectory(outputDirectory);
        IReadOnlyList<CrossTlLogicalPairing> pairings = ExpandPairings(
            study, enumeration.LegalBuilds, enumeration.NamedBuilds, readiness, populationCells, progressionEdges);
        Tl1IntegratedTacticalCombatStudyDocument generated = BuildIntegratedStudy(
            study, baselineHash, enumeration.NamedBuilds, pairings);

        if (generated.Variants.Count != study.ExpectedGeneratedVariantCount)
        {
            throw new InvalidOperationException(
                $"Cross-TL generated study expected {study.ExpectedGeneratedVariantCount} variants; found {generated.Variants.Count}.");
        }

        IReadOnlyList<CrossTlFoundationGate> gates = BuildFoundationGates(
            study, enumeration, pairings, progressionEdges, generated);
        IReadOnlyList<CrossTlFoundationGate> failed = gates.Where(gate => !gate.Passed).ToArray();
        WriteFoundationGates(gates, outputDirectory);
        WriteProgressionLatticeSummary(study, progressionEdges, outputDirectory);
        WritePreflightSummary(study, studyHash, baselineHash, enumeration, pairings, generated, failed.Count, outputDirectory);
        if (failed.Count > 0)
        {
            foreach (CrossTlFoundationGate gate in failed)
            {
                Console.Error.WriteLine($"FAILED GATE {gate.Id}: {gate.Detail}");
            }
            return 1;
        }

        if (preflightOnly)
        {
            string latticeText = study.ProgressionLattice is null
                ? string.Empty
                : $" {progressionEdges.Count} legal single-axis progression edges;";
            Console.WriteLine(
                $"Cross-TL build-permutation preflight: {enumeration.LegalBuilds.Count} legal builds;" +
                latticeText +
                $" {enumeration.NamedBuilds.Count} named recipes; {pairings.Count} logical pairings; " +
                $"{generated.Variants.Count} generated combat variants; passed.");
            return 0;
        }

        WriteLegalBuilds(study, enumeration.LegalBuilds, outputDirectory);
        WriteNamedBuilds(study, enumeration.NamedBuilds, outputDirectory);
        WritePairingPlan(pairings, outputDirectory);
        WriteProgressionLatticeEdges(study, progressionEdges, outputDirectory);
        if (IsMatchedReadinessSchema(study.SchemaVersion) && !exactEdgeSelection)
        {
            WritePopulationCoverage(study, populationCells, pairings, outputDirectory);
            if (IsAdaptiveSamplingSchema(study.SchemaVersion))
            {
                WriteSecondaryCoverage(study, populationCells, pairings, outputDirectory);
            }
        }
        if (exactEdgeSelection)
        {
            WriteExactEdgePairingPlan(study, pairings, outputDirectory);
        }
        string generatedStudyPath = Path.Combine(outputDirectory, "generated-integrated-combat-study.json");
        string generatedJson = JsonSerializer.Serialize(generated, OutputJsonOptions());
        File.WriteAllText(generatedStudyPath, generatedJson + Environment.NewLine, new UTF8Encoding(false));
        string generatedStudyHash = Sha256File(generatedStudyPath);
        File.WriteAllText(
            Path.Combine(outputDirectory, "result-sha256.txt"),
            generatedStudyHash + Environment.NewLine,
            new UTF8Encoding(false));
        WriteGenerationSummary(
            study, studyHash, baselineHash, generatedStudyPath, generatedStudyHash,
            enumeration, pairings, generated, outputDirectory);

        Console.WriteLine(
            $"Cross-TL build-permutation generation: {enumeration.LegalBuilds.Count} legal builds; " +
            $"{pairings.Count} logical pairings; {generated.Variants.Count} generated combat variants. " +
            $"Output: {Path.GetFullPath(outputDirectory)}");
        return 0;
    }

    internal static long ComputeCartesianCountForSelfTest(IReadOnlyList<int> optionCounts)
    {
        long count = 1;
        foreach (int value in optionCounts)
        {
            if (value <= 0) throw new InvalidOperationException("Cartesian option counts must be positive.");
            count = checked(count * value);
        }
        return count;
    }

    private static bool IsGeneralizedSchema(string schemaVersion) =>
        string.Equals(schemaVersion, SchemaVersionV3, StringComparison.Ordinal) ||
        string.Equals(schemaVersion, SchemaVersionV4, StringComparison.Ordinal) ||
        string.Equals(schemaVersion, SchemaVersionV5, StringComparison.Ordinal) ||
        string.Equals(schemaVersion, SchemaVersionV6, StringComparison.Ordinal) ||
        string.Equals(schemaVersion, SchemaVersionV7, StringComparison.Ordinal);

    private static bool IsMatchedReadinessSchema(string schemaVersion) =>
        string.Equals(schemaVersion, SchemaVersionV4, StringComparison.Ordinal) ||
        string.Equals(schemaVersion, SchemaVersionV5, StringComparison.Ordinal) ||
        string.Equals(schemaVersion, SchemaVersionV6, StringComparison.Ordinal);

    private static bool IsAdaptiveSamplingSchema(string schemaVersion) =>
        string.Equals(schemaVersion, SchemaVersionV5, StringComparison.Ordinal);

    private static CrossTlEnumerationResult ValidateAndEnumerate(CrossTlBuildPermutationDocument study)
    {
        bool v7 = string.Equals(study.SchemaVersion, SchemaVersionV7, StringComparison.Ordinal);
        bool v6 = string.Equals(study.SchemaVersion, SchemaVersionV6, StringComparison.Ordinal);
        bool v5 = string.Equals(study.SchemaVersion, SchemaVersionV5, StringComparison.Ordinal);
        bool v4 = string.Equals(study.SchemaVersion, SchemaVersionV4, StringComparison.Ordinal);
        bool v3 = string.Equals(study.SchemaVersion, SchemaVersionV3, StringComparison.Ordinal);
        bool generalized = v3 || v4 || v5 || v6 || v7;
        bool v2 = string.Equals(study.SchemaVersion, SchemaVersionV2, StringComparison.Ordinal);
        if (!v7 && !v6 && !v5 && !v4 && !v3 && !v2 && !string.Equals(study.SchemaVersion, SchemaVersionV1, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Unexpected cross-TL build-permutation schema.");
        }
        if (v2 || generalized)
        {
            ValidateConstructionGuardrails(study, generalized);
        }
        if (study.TotalInstallationSpace <= 0 || study.FixedShellSpace < 0 ||
            study.FixedShellSpace > study.TotalInstallationSpace)
        {
            throw new InvalidOperationException("Cross-TL Installation Space envelope is invalid.");
        }
        if (study.Axes.Count == 0 || study.Axes.Select(axis => axis.Id).Distinct(StringComparer.Ordinal).Count() != study.Axes.Count)
        {
            throw new InvalidOperationException("Cross-TL axes must be non-empty and uniquely identified.");
        }
        if (v7)
        {
            string[] requiredAxes =
            {
                "hull", "weapon", "reactor", "computer", "sensor", "shield", "shieldHardener",
                "armor", "ecm", "eccm", "stl", "ftl", "pds",
            };
            if (study.Axes.Count != requiredAxes.Length ||
                requiredAxes.Any(required => study.Axes.All(axis => !string.Equals(axis.Id, required, StringComparison.Ordinal))))
            {
                throw new InvalidOperationException(
                    "Cross-TL v7 studies must declare exactly the hull/weapon/reactor/computer/sensor/shield/shieldHardener/armor/ecm/eccm/stl/ftl/pds axes.");
            }
            if (study.CoverageMode is not "construction_envelope" and not "transition_smoke")
            {
                throw new InvalidOperationException(
                    "Cross-TL v7 studies must declare coverageMode as construction_envelope or transition_smoke.");
            }
        }
        else if (generalized)
        {
            string[] requiredAxes = { "weapon", "reactor", "computer", "sensor", "shield", "armor", "ecm", "eccm", "pds" };
            if (study.Axes.Count != requiredAxes.Length ||
                requiredAxes.Any(required => study.Axes.All(axis => !string.Equals(axis.Id, required, StringComparison.Ordinal))))
            {
                throw new InvalidOperationException(
                    "Cross-TL generalized studies must declare exactly the weapon/reactor/computer/sensor/shield/armor/ecm/eccm/pds axes.");
            }
        }
        foreach (CrossTlTechnologyAxisDocument axis in study.Axes)
        {
            if (string.IsNullOrWhiteSpace(axis.Id) || string.IsNullOrWhiteSpace(axis.Code) || axis.Options.Count == 0 ||
                axis.Options.Select(option => option.Id).Distinct(StringComparer.Ordinal).Count() != axis.Options.Count)
            {
                throw new InvalidOperationException($"Cross-TL axis '{axis.Id}' is malformed or has duplicate options.");
            }
            if (axis.Options.Any(option => option.Space < 0 || option.TechnologyLevel < 1 || option.TechnologyLevel > 9 ||
                option.MainWeaponCount is < 0 || option.ReactorCount is < 0))
            {
                throw new InvalidOperationException($"Cross-TL axis '{axis.Id}' contains invalid Space, TL, or component-count data.");
            }
            if ((v2 || generalized) && axis.Id == "weapon" && axis.Options.Any(option => option.MainWeaponCount is null))
            {
                throw new InvalidOperationException("Cross-TL v2+ weapon options must declare mainWeaponCount explicitly.");
            }
            if ((v2 || generalized) && axis.Id == "reactor" && axis.Options.Any(option => option.ReactorCount is null))
            {
                throw new InvalidOperationException("Cross-TL v2+ reactor options must declare reactorCount explicitly.");
            }
            if (generalized && axis.Id == "weapon" && axis.Options.Any(option => option.MainWeaponCount is < 1 or > 2 || option.ReactorCount is not null))
            {
                throw new InvalidOperationException("Cross-TL generalized weapon options must represent one or two Main Weapons and may not declare Reactor count.");
            }
            if (generalized && axis.Id == "reactor" && axis.Options.Any(option => option.ReactorCount is < 1 or > 2 || option.MainWeaponCount is not null))
            {
                throw new InvalidOperationException("Cross-TL generalized reactor options must represent one or two Main Reactors and may not declare Main Weapon count.");
            }
            if (generalized && axis.Options.Any(option => option.EwRatings.Any(rating => rating < 1 || rating > 4) || option.EwRatings.Count > 2 || option.PdsCount is < 0 or > 1))
            {
                throw new InvalidOperationException($"Cross-TL generalized axis '{axis.Id}' contains invalid EW-rating or PDS multiplicity data.");
            }
            if (generalized && (axis.Id == "ecm" || axis.Id == "eccm") && axis.Options.Any(option =>
                option.EwRating is not null || (option.Installed == false && option.EwRatings.Count != 0) ||
                (option.Installed == true && option.EwRatings.Count == 0)))
            {
                throw new InvalidOperationException($"Cross-TL generalized axis '{axis.Id}' must use explicit non-additive ewRatings arrays consistent with installed state.");
            }
            if (v7 && axis.Id == "hull" && axis.Options.Any(option =>
                option.InstallationSpaceCapacity is null or <= 0 || option.Space != 0))
            {
                throw new InvalidOperationException(
                    "Cross-TL v7 Hull options must declare a positive installationSpaceCapacity and consume zero installed component Space.");
            }
            if (v7 && axis.Id == "shieldHardener" && axis.Options.Any(option =>
                option.Installed == true && (option.ShieldArmorBonus is null or <= 0 || option.SustainedPowerCost is null or <= 0)))
            {
                throw new InvalidOperationException(
                    "Cross-TL v7 installed Shield Hardener options require positive shieldArmorBonus and sustainedPowerCost values.");
            }
            if (v7 && axis.Id == "pds" && axis.Options.Any(option =>
                option.Installed == true && (string.IsNullOrWhiteSpace(option.PdsFamily) ||
                    option.PdsBaseChance is null or < 0 || option.PdsPowerCost is null or < 0 ||
                    option.PdsReactionCapacity is null or < 1 or > 2 ||
                    ((option.PdsFallbackPowerCost is null) != (option.PdsFallbackReactionCapacity is null)) ||
                    option.PdsFallbackPowerCost is < 0 || option.PdsFallbackReactionCapacity is < 1 or > 2 ||
                    (option.PdsFallbackPowerCost is int fallbackPower && option.PdsPowerCost is int primaryPower && fallbackPower >= primaryPower) ||
                    (option.PdsFallbackReactionCapacity is int fallbackRc && option.PdsReactionCapacity is int primaryRc && fallbackRc >= primaryRc))))
            {
                throw new InvalidOperationException(
                    "Cross-TL v7 installed PDS options require family/base-chance/power/reaction-capacity runtime characteristics.");
            }
        }

        long rawCombinationCount = ComputeCartesianCountForSelfTest(study.Axes.Select(axis => axis.Options.Count).ToArray());
        if (generalized && rawCombinationCount != study.ExpectedRawCombinationCount)
        {
            throw new InvalidOperationException(
                $"Cross-TL raw-combination count mismatch: expected {study.ExpectedRawCombinationCount}; observed {rawCombinationCount}.");
        }
        var legalBuilds = new List<CrossTlResolvedBuild>();
        if (v7)
        {
            var selections = new Dictionary<string, CrossTlTechnologyOptionDocument>(StringComparer.Ordinal);
            void VisitAxis(int axisIndex, int installedSpace)
            {
                if (axisIndex == study.Axes.Count)
                {
                    int installationSpaceCapacity = RequireOption(selections, "hull").InstallationSpaceCapacity ??
                        throw new InvalidOperationException("Cross-TL v7 Hull selection is missing installationSpaceCapacity.");
                    int usedSpace = checked(study.FixedShellSpace + installedSpace);
                    if (usedSpace > installationSpaceCapacity || !MeetsMinimumCombatCore(study, selections) ||
                        !MeetsConstructionCompatibility(selections))
                    {
                        return;
                    }
                    legalBuilds.Add(ResolveBuild(study, selections, usedSpace, installationSpaceCapacity));
                    return;
                }

                CrossTlTechnologyAxisDocument axis = study.Axes[axisIndex];
                foreach (CrossTlTechnologyOptionDocument option in axis.Options)
                {
                    selections[axis.Id] = option;
                    int nextSpace = checked(installedSpace + option.Space);
                    int? currentCapacity = selections.TryGetValue("hull", out CrossTlTechnologyOptionDocument? hull)
                        ? hull.InstallationSpaceCapacity
                        : null;
                    if (currentCapacity is null || study.FixedShellSpace + nextSpace <= currentCapacity.Value)
                    {
                        VisitAxis(axisIndex + 1, nextSpace);
                    }
                }
                selections.Remove(axis.Id);
            }
            VisitAxis(0, 0);
        }
        else
        {
            var partials = new List<Dictionary<string, CrossTlTechnologyOptionDocument>>
            {
                new(StringComparer.Ordinal),
            };
            foreach (CrossTlTechnologyAxisDocument axis in study.Axes)
            {
                var next = new List<Dictionary<string, CrossTlTechnologyOptionDocument>>();
                foreach (Dictionary<string, CrossTlTechnologyOptionDocument> partial in partials)
                foreach (CrossTlTechnologyOptionDocument option in axis.Options)
                {
                    var copy = new Dictionary<string, CrossTlTechnologyOptionDocument>(partial, StringComparer.Ordinal)
                    {
                        [axis.Id] = option,
                    };
                    next.Add(copy);
                }
                partials = next;
            }

            foreach (Dictionary<string, CrossTlTechnologyOptionDocument> legacySelections in partials)
            {
                int usedSpace = study.FixedShellSpace + legacySelections.Values.Sum(option => option.Space);
                if (usedSpace > study.TotalInstallationSpace) continue;
                if (!MeetsMinimumCombatCore(study, legacySelections)) continue;
                legalBuilds.Add(ResolveBuild(study, legacySelections, usedSpace, study.TotalInstallationSpace));
            }
        }
        if (legalBuilds.Select(build => build.Id).Distinct(StringComparer.Ordinal).Count() != legalBuilds.Count)
        {
            throw new InvalidOperationException("Cross-TL legal-build IDs are not unique.");
        }
        if (legalBuilds.Count != study.ExpectedLegalBuildCount)
        {
            throw new InvalidOperationException(
                $"Cross-TL legal-build count mismatch: expected {study.ExpectedLegalBuildCount}; observed {legalBuilds.Count} from {rawCombinationCount} raw combinations.");
        }

        if (study.NamedRecipes.Count != study.ExpectedNamedRecipeCount ||
            study.NamedRecipes.Select(recipe => recipe.Id).Distinct(StringComparer.Ordinal).Count() != study.NamedRecipes.Count)
        {
            throw new InvalidOperationException("Cross-TL named-recipe count or identity is invalid.");
        }
        var namedBuilds = new Dictionary<string, CrossTlResolvedBuild>(StringComparer.Ordinal);
        foreach (CrossTlNamedRecipeDocument recipe in study.NamedRecipes)
        {
            foreach (CrossTlTechnologyAxisDocument axis in study.Axes)
            {
                if (!recipe.Selections.TryGetValue(axis.Id, out string? optionId) ||
                    axis.Options.All(option => !string.Equals(option.Id, optionId, StringComparison.Ordinal)))
                {
                    throw new InvalidOperationException(
                        $"Named recipe '{recipe.Id}' is missing a valid selection for axis '{axis.Id}'.");
                }
            }
            CrossTlResolvedBuild[] matches = legalBuilds.Where(build =>
                study.Axes.All(axis => string.Equals(
                    build.Selections[axis.Id], recipe.Selections[axis.Id], StringComparison.Ordinal))).ToArray();
            if (matches.Length != 1)
            {
                throw new InvalidOperationException(
                    $"Named recipe '{recipe.Id}' resolved to {matches.Length} legal builds instead of one.");
            }
            namedBuilds.Add(recipe.Id, matches[0]);
        }

        return new CrossTlEnumerationResult(rawCombinationCount, legalBuilds, namedBuilds);
    }

    private static void ValidateConstructionGuardrails(CrossTlBuildPermutationDocument study, bool generalized)
    {
        CrossTlConstructionGuardrailsDocument guardrails = study.ConstructionGuardrails ??
            throw new InvalidOperationException("Cross-TL v2+ studies must declare constructionGuardrails.");
        if (guardrails.MinimumMainWeaponCount < 1 || guardrails.MinimumReactorCount < 1 ||
            guardrails.MinimumSensorCount < 0 ||
            !guardrails.AdditionalMainWeaponsOptional || !guardrails.AdditionalReactorsOptional ||
            !guardrails.DuplicationMustBeExplicit)
        {
            throw new InvalidOperationException(
                "Cross-TL construction guardrails must require at least one Main Weapon and one Reactor, allow an explicit Sensor minimum, and preserve explicit optional duplication.");
        }
        if (study.ExactEdgePairingSelection?.Enabled == true && guardrails.MinimumSensorCount < 1)
        {
            throw new InvalidOperationException(
                "Exact-edge normal-combat progression studies must require at least one installed Sensor.");
        }
        if (generalized && (!guardrails.RedundantEwInstallationsAllowed ||
            guardrails.EcmSameTypeRatingsAdditive || guardrails.EccmSameTypeRatingsAdditive ||
            !string.Equals(guardrails.EwDuplicateResolution, "highest_applicable_functional_rating", StringComparison.Ordinal) ||
            guardrails.PowerSufficiencyIsConstructionLegalityFilter))
        {
            throw new InvalidOperationException(
                "Cross-TL generalized schemas must allow redundant ECM/ECCM without additive ratings, resolve the highest applicable functional rating, and keep Tactical Power sufficiency out of construction legality.");
        }
    }

    private static bool MeetsMinimumCombatCore(
        CrossTlBuildPermutationDocument study,
        IReadOnlyDictionary<string, CrossTlTechnologyOptionDocument> selected)
    {
        if (study.ConstructionGuardrails is null) return true;
        int mainWeapons = selected.Values.Sum(option => option.MainWeaponCount ?? 0);
        int reactors = selected.Values.Sum(option => option.ReactorCount ?? 0);
        int sensors = selected.TryGetValue("sensor", out CrossTlTechnologyOptionDocument? sensor) &&
            sensor is not null && (sensor.Installed ?? true) ? 1 : 0;
        return MeetsMinimumCombatCoreForSelfTest(
            mainWeapons, reactors, sensors,
            study.ConstructionGuardrails.MinimumMainWeaponCount,
            study.ConstructionGuardrails.MinimumReactorCount,
            study.ConstructionGuardrails.MinimumSensorCount);
    }

    internal static bool MeetsMinimumCombatCoreForSelfTest(
        int mainWeaponCount, int reactorCount, int sensorCount = 0,
        int minimumMainWeaponCount = 1, int minimumReactorCount = 1, int minimumSensorCount = 0) =>
        mainWeaponCount >= minimumMainWeaponCount && reactorCount >= minimumReactorCount &&
        sensorCount >= minimumSensorCount;

    private static bool MeetsConstructionCompatibility(
        IReadOnlyDictionary<string, CrossTlTechnologyOptionDocument> selected)
    {
        bool hardenerInstalled = selected.TryGetValue("shieldHardener", out CrossTlTechnologyOptionDocument? hardener) &&
            hardener is not null && hardener.Installed == true;
        bool shieldInstalled = selected.TryGetValue("shield", out CrossTlTechnologyOptionDocument? shield) &&
            shield is not null && (shield.Installed ?? true);
        return !hardenerInstalled || shieldInstalled;
    }

    internal static bool ShieldHardenerCompatibilityForSelfTest(bool shieldInstalled, bool hardenerInstalled) =>
        !hardenerInstalled || shieldInstalled;

    private static CrossTlResolvedBuild ResolveBuild(
        CrossTlBuildPermutationDocument study,
        IReadOnlyDictionary<string, CrossTlTechnologyOptionDocument> selected,
        int usedSpace,
        int? installationSpaceCapacityOverride = null)
    {
        CrossTlTechnologyOptionDocument weapon = RequireOption(selected, "weapon");
        CrossTlTechnologyOptionDocument reactor = RequireOption(selected, "reactor");
        CrossTlTechnologyOptionDocument computer = RequireOption(selected, "computer");
        CrossTlTechnologyOptionDocument sensor = RequireOption(selected, "sensor");
        CrossTlTechnologyOptionDocument shield = RequireOption(selected, "shield");
        CrossTlTechnologyOptionDocument armor = RequireOption(selected, "armor");
        CrossTlTechnologyOptionDocument ecm = RequireOption(selected, "ecm");
        CrossTlTechnologyOptionDocument eccm = RequireOption(selected, "eccm");
        CrossTlTechnologyOptionDocument? pds = selected.TryGetValue("pds", out CrossTlTechnologyOptionDocument? pdsOption)
            ? pdsOption
            : null;
        CrossTlTechnologyOptionDocument? shieldHardener = selected.TryGetValue("shieldHardener", out CrossTlTechnologyOptionDocument? hardenerOption)
            ? hardenerOption
            : null;
        CrossTlTechnologyOptionDocument? stl = selected.TryGetValue("stl", out CrossTlTechnologyOptionDocument? stlOption)
            ? stlOption
            : null;
        CrossTlTechnologyOptionDocument? ftl = selected.TryGetValue("ftl", out CrossTlTechnologyOptionDocument? ftlOption)
            ? ftlOption
            : null;
        if (!Enum.TryParse(weapon.Family, ignoreCase: false, out WeaponFamily family) || family == WeaponFamily.Hybrid)
        {
            throw new InvalidOperationException($"Unknown cross-TL weapon family '{weapon.Family}'.");
        }
        if (weapon.ShieldPenetration is null || weapon.ArmorPenetration is null ||
            reactor.ReactorOutput is null || computer.TargetingBonus is null ||
            string.IsNullOrWhiteSpace(sensor.SensorEwProfileId) || shield.ShieldCapacity is null ||
            armor.ArmorProtection is null || armor.ArmorIntegrity is null)
        {
            throw new InvalidOperationException("Cross-TL option payload is missing a runtime property required by the current screening shell.");
        }
        List<int> ecmRatings = ResolveEwRatings(ecm);
        List<int> eccmRatings = ResolveEwRatings(eccm);
        string buildId = "b-" + string.Join("_", study.Axes.Select(axis =>
            axis.Code + "-" + selected[axis.Id].Id));
        var selections = study.Axes.ToDictionary(axis => axis.Id, axis => selected[axis.Id].Id, StringComparer.Ordinal);
        int maxTl = selected.Values.Max(option => option.TechnologyLevel);
        int tl2Axes = selected.Values.Count(option => option.TechnologyLevel >= 2);
        int mainWeaponCount = selected.Values.Sum(option => option.MainWeaponCount ?? 0);
        int reactorCount = selected.Values.Sum(option => option.ReactorCount ?? 0);
        if (study.ConstructionGuardrails is null)
        {
            mainWeaponCount = 1;
            reactorCount = 1;
        }
        bool sensorInstalled = sensor.Installed ?? true;
        bool shieldInstalled = shield.Installed ?? true;
        int pdsCount = pds?.PdsCount ?? study.FixedShell.KineticPdsCount;
        int advancedComponents = CountAdvancedComponents(selected, ecmRatings, eccmRatings);
        int informationControlAdvancedComponents = CountInformationControlAdvancedComponents(
            selected, ecmRatings, eccmRatings);
        int installationSpaceCapacity = installationSpaceCapacityOverride ?? study.TotalInstallationSpace;
        string spaceUtilizationClass = SpaceUtilizationClass(
            usedSpace, installationSpaceCapacity, study.StratifiedPairingSelection);
        bool ewRedundancy = ecmRatings.Count > 1 || eccmRatings.Count > 1;
        bool mainOrReactorDuplication = mainWeaponCount > 1 || reactorCount > 1;
        string compositionClass = mainOrReactorDuplication && ewRedundancy
            ? "combined-duplication"
            : mainOrReactorDuplication
                ? "weapon-reactor-duplication"
                : ewRedundancy
                    ? "ew-redundancy"
                    : "single-no-ew-redundancy";
        return new CrossTlResolvedBuild(
            buildId, selections, usedSpace, installationSpaceCapacity - usedSpace, installationSpaceCapacity,
            maxTl, tl2Axes, advancedComponents, mainWeaponCount, reactorCount, family,
            weapon.ShieldPenetration.Value, weapon.ArmorPenetration.Value,
            weapon.Damage, weapon.AccuracyBonus, weapon.PowerCost, weapon.MaximumRange, weapon.Ammunition,
            weapon.PreferredSmokeModeId, weapon.PreferredSmokeModeDamage, weapon.PreferredSmokeModePowerCost,
            weapon.PreferredSmokeModeAccuracyBonus,
            reactor.ReactorOutput.Value, computer.TargetingBonus.Value, computer.EvasiveCompensation ?? 0,
            sensor.SensorEwProfileId!, sensorInstalled, sensor.PassiveFirmRange, sensor.PassiveApproximateRange,
            sensor.ActiveLowFirmRange, sensor.ActiveLowApproximateRange, sensor.ActiveLowPowerCost,
            sensor.ActiveHighFirmRange, sensor.ActiveHighApproximateRange, sensor.ActiveHighPowerCost,
            shieldInstalled, shield.ShieldCapacity.Value,
            shieldHardener?.Installed == true, shieldHardener?.ShieldArmorBonus ?? 0, shieldHardener?.SustainedPowerCost ?? 0,
            armor.ArmorProtection.Value, armor.ArmorIntegrity.Value,
            ecmRatings, ecm.EwNormalPowerCost ?? 1, ecm.EwFullStrengthNormalPowerCost,
            eccmRatings, eccm.EwNormalPowerCost ?? 1, eccm.EwFullStrengthNormalPowerCost,
            pdsCount, pds?.PdsFamily, pds?.PdsBaseChance, pds?.PdsPowerCost, pds?.PdsReactionCapacity,
            pds?.PdsFallbackPowerCost, pds?.PdsFallbackReactionCapacity, pds?.PdsAmmunition,
            stl?.NormalMove, ftl?.StrategicMove, weapon.MissileMove, weapon.StandardOnboardNavigationSensor ?? false,
            ewRedundancy, mainOrReactorDuplication, compositionClass,
            informationControlAdvancedComponents, spaceUtilizationClass);
    }

    private static List<int> ResolveEwRatings(CrossTlTechnologyOptionDocument option)
    {
        if (option.EwRatings.Count > 0)
        {
            return option.EwRatings.ToList();
        }
        return option.EwRating is int rating ? new List<int> { rating } : new List<int>();
    }

    private static int CountAdvancedComponents(
        IReadOnlyDictionary<string, CrossTlTechnologyOptionDocument> selected,
        IReadOnlyList<int> ecmRatings,
        IReadOnlyList<int> eccmRatings)
    {
        int count = 0;
        CrossTlTechnologyOptionDocument weapon = RequireOption(selected, "weapon");
        CrossTlTechnologyOptionDocument reactor = RequireOption(selected, "reactor");
        count += weapon.TechnologyLevel >= 2 ? weapon.MainWeaponCount ?? 1 : 0;
        count += reactor.TechnologyLevel >= 2 ? reactor.ReactorCount ?? 1 : 0;
        foreach (string axisId in new[] { "computer", "sensor", "shield", "armor" })
        {
            CrossTlTechnologyOptionDocument option = RequireOption(selected, axisId);
            if ((option.Installed ?? true) && option.TechnologyLevel >= 2) count++;
        }
        count += ecmRatings.Count(rating => rating >= 2);
        count += eccmRatings.Count(rating => rating >= 2);
        return count;
    }

    private static int CountInformationControlAdvancedComponents(
        IReadOnlyDictionary<string, CrossTlTechnologyOptionDocument> selected,
        IReadOnlyList<int> ecmRatings,
        IReadOnlyList<int> eccmRatings)
    {
        int count = 0;
        CrossTlTechnologyOptionDocument computer = RequireOption(selected, "computer");
        CrossTlTechnologyOptionDocument sensor = RequireOption(selected, "sensor");
        if (computer.TechnologyLevel >= 2) count++;
        if ((sensor.Installed ?? true) && sensor.TechnologyLevel >= 2) count++;
        count += ecmRatings.Count(rating => rating >= 2);
        count += eccmRatings.Count(rating => rating >= 2);
        return count;
    }

    private static string SpaceUtilizationClass(
        int usedSpace,
        int totalSpace,
        CrossTlStratifiedPairingSelectionDocument? selection)
    {
        int nearMinimum = selection?.NearFillMinimumUsedSpace ?? Math.Max(0, totalSpace - 3);
        if (usedSpace == totalSpace) return "exact_fill";
        if (usedSpace >= nearMinimum && usedSpace < totalSpace) return "near_fill";
        return "underfilled";
    }

    internal static string SpaceUtilizationClassForSelfTest(
        int usedSpace, int totalSpace, int nearFillMinimumUsedSpace) =>
        SpaceUtilizationClass(usedSpace, totalSpace, new CrossTlStratifiedPairingSelectionDocument
        {
            NearFillMinimumUsedSpace = nearFillMinimumUsedSpace,
        });

    private static CrossTlTechnologyOptionDocument RequireOption(
        IReadOnlyDictionary<string, CrossTlTechnologyOptionDocument> selected,
        string axisId) => selected.TryGetValue(axisId, out CrossTlTechnologyOptionDocument? option)
            ? option
            : throw new InvalidOperationException($"Cross-TL axis '{axisId}' is required by the current screening shell.");

    private static CrossTlReadinessContext LoadReadinessContext(
        CrossTlBuildPermutationDocument study,
        string baselinePath)
    {
        if (string.IsNullOrWhiteSpace(study.SensorEwProfileCatalog))
        {
            throw new InvalidOperationException("Cross-TL v4 readiness classification requires a Sensor/EW profile catalog.");
        }
        Tl1SensorEwFoundationStudy sensorStudy = DeserializeSensorEwFoundationCatalog(
            File.ReadAllText(study.SensorEwProfileCatalog));
        var profiles = sensorStudy.Candidates.ToDictionary(
            candidate => candidate.Id,
            candidate => new SensorEwFoundationProfile(
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
                candidate.PointBlankBurnThroughResistance),
            StringComparer.Ordinal);
        Tl1BaselineCatalog baseline = Tl1BaselineCatalog.Load(baselinePath);
        return new CrossTlReadinessContext(
            profiles,
            baseline.GetInt("kinetic_range"),
            baseline.GetInt("energy_range"),
            baseline.GetInt("missile_range"));
    }

    private static Tl1SensorEwFoundationStudy DeserializeSensorEwFoundationCatalog(string json)
    {
        JsonSerializerOptions sensorEwCatalogOptions = JsonOptions();
        // Tl1SensorEwFoundationStudy is a positional record whose public property names are
        // PascalCase while the authoritative Sensor/EW catalog JSON is camelCase. Match the
        // already-proven integrated-combat loader contract rather than applying the strict
        // Cross-TL document binding options to this external catalog type.
        sensorEwCatalogOptions.PropertyNameCaseInsensitive = true;
        Tl1SensorEwFoundationStudy sensorStudy = JsonSerializer.Deserialize<Tl1SensorEwFoundationStudy>(
            json, sensorEwCatalogOptions) ?? throw new InvalidOperationException(
                "Cross-TL v4 Sensor/EW profile catalog could not be read.");
        if (sensorStudy.Candidates is null)
        {
            throw new InvalidOperationException(
                "Cross-TL v4 Sensor/EW profile catalog candidates could not be bound.");
        }
        return sensorStudy;
    }

    internal static int SensorEwCatalogCandidateCountForSelfTest(string json) =>
        DeserializeSensorEwFoundationCatalog(json).Candidates.Count;

    private static CrossTlEngagementReadiness EngagementReadiness(
        CrossTlResolvedBuild observer,
        CrossTlResolvedBuild target,
        CrossTlReadinessContext? context,
        int referenceRange = 3)
    {
        if (context is null) return new CrossTlEngagementReadiness("not_classified", -1);
        if (!context.SensorProfiles.TryGetValue(observer.SensorEwProfileId, out SensorEwFoundationProfile? observerProfile) ||
            !context.SensorProfiles.TryGetValue(target.SensorEwProfileId, out SensorEwFoundationProfile? targetProfile))
        {
            throw new InvalidOperationException("Cross-TL readiness classification references an unknown Sensor/EW profile.");
        }
        int physicalRange = observer.Family switch
        {
            WeaponFamily.Kinetic => context.KineticPhysicalRange,
            WeaponFamily.Energy => context.EnergyPhysicalRange,
            WeaponFamily.Missile => context.MissilePhysicalRange,
            _ => 0,
        };
        bool CanEngageAt(int range)
        {
            if (range > physicalRange) return false;
            SensorEwFoundationEvaluationResult result = SensorEwFoundationResolver.Evaluate(
                range,
                observerProfile,
                targetProfile,
                new SensorEwFoundationEvaluationContext(
                    observer.SensorInstalled ? SensorMode.Active : SensorMode.Passive,
                    ObserverActiveSensorOverloaded: false,
                    TargetActiveSensorsEnabled: target.SensorInstalled,
                    TargetActiveSensorOverloaded: false,
                    TargetEcmRating: target.EcmRatings.Count == 0 ? 0 : target.EcmRatings.Max(),
                    ObserverEccmRating: observer.EccmRatings.Count == 0 ? 0 : observer.EccmRatings.Max(),
                    HasLineOfSight: true));
            return result.FinalTrack == SensorEwFoundationTrackState.Firm;
        }

        int maximumReadyRange = -1;
        for (int range = referenceRange; range >= 0; range--)
        {
            if (CanEngageAt(range))
            {
                maximumReadyRange = range;
                break;
            }
        }
        if (maximumReadyRange == referenceRange)
        {
            return new CrossTlEngagementReadiness("reference_ready", maximumReadyRange);
        }
        if (maximumReadyRange >= 0)
        {
            return new CrossTlEngagementReadiness("closing_ready", maximumReadyRange);
        }
        return new CrossTlEngagementReadiness("engagement_denied", -1);
    }

    private static string EngagementReadinessClass(
        CrossTlResolvedBuild observer,
        CrossTlResolvedBuild target,
        CrossTlReadinessContext? context,
        int referenceRange = 3) =>
        EngagementReadiness(observer, target, context, referenceRange).ReadinessClass;

    private static string ProgressionMagnitudeStratum(
        CrossTlResolvedBuild sideA,
        CrossTlResolvedBuild sideB,
        CrossTlStratifiedPairingSelectionDocument? selection)
    {
        int distance = ProgressionDistance(sideA, sideB);
        if (distance == 0)
        {
            int threshold = selection?.EqualLowAdvancedMaximum ?? 3;
            return sideA.AdvancedComponentCount <= threshold ? "equal_low" : "equal_high";
        }
        int nearMaximum = selection?.NearDistanceMaximum ?? 2;
        return distance <= nearMaximum ? "near" : "far";
    }

    internal static string ProgressionMagnitudeStratumForSelfTest(
        int sideAAdvancedComponents,
        int sideBAdvancedComponents,
        int nearDistanceMaximum,
        int equalLowAdvancedMaximum)
    {
        int distance = Math.Abs(sideAAdvancedComponents - sideBAdvancedComponents);
        if (distance == 0)
        {
            return sideAAdvancedComponents <= equalLowAdvancedMaximum ? "equal_low" : "equal_high";
        }
        return distance <= nearDistanceMaximum ? "near" : "far";
    }

    private static int SpaceClassRank(string value) => value switch
    {
        "exact_fill" => 0,
        "near_fill" => 1,
        "underfilled" => 2,
        _ => 99,
    };

    private static string SpacePairStratum(CrossTlResolvedBuild sideA, CrossTlResolvedBuild sideB)
    {
        string a = sideA.SpaceUtilizationClass;
        string b = sideB.SpaceUtilizationClass;
        if (SpaceClassRank(a) > SpaceClassRank(b)) (a, b) = (b, a);
        return a + "-" + b;
    }

    internal static string SpacePairStratumForSelfTest(string a, string b)
    {
        if (SpaceClassRank(a) > SpaceClassRank(b)) (a, b) = (b, a);
        return a + "-" + b;
    }

    private static string WeaponFamilyPair(CrossTlResolvedBuild sideA, CrossTlResolvedBuild sideB)
    {
        string a = sideA.Family.ToString();
        string b = sideB.Family.ToString();
        return string.CompareOrdinal(a, b) <= 0 ? a + "-" + b : b + "-" + a;
    }

    private static string InformationControlDirection(CrossTlResolvedBuild sideA, CrossTlResolvedBuild sideB) =>
        sideA.InformationControlAdvancedCount < sideB.InformationControlAdvancedCount
            ? "side_a_lower"
            : sideA.InformationControlAdvancedCount > sideB.InformationControlAdvancedCount
                ? "side_a_higher"
                : "equal";

    private static string InformationControlDistanceBand(
        CrossTlResolvedBuild sideA,
        CrossTlResolvedBuild sideB,
        CrossTlStratifiedPairingSelectionDocument? selection)
    {
        int distance = Math.Abs(sideA.InformationControlAdvancedCount - sideB.InformationControlAdvancedCount);
        if (distance == 0) return "equal";
        int nearMaximum = selection?.InformationControlNearDistanceMaximum > 0
            ? selection.InformationControlNearDistanceMaximum
            : 2;
        return distance <= nearMaximum ? "near" : "far";
    }

    private static string SecondaryCoverageKey(
        CrossTlResolvedBuild sideA,
        CrossTlResolvedBuild sideB,
        CrossTlStratifiedPairingSelectionDocument? selection) =>
        WeaponFamilyPair(sideA, sideB) + "~" + InformationControlDistanceBand(sideA, sideB, selection);

    internal static string InformationControlDistanceBandForSelfTest(int distance, int nearMaximum) =>
        distance == 0 ? "equal" : distance <= nearMaximum ? "near" : "far";

    private static string PopulationCellKey(
        string compositionClass,
        string progressionMagnitude,
        string spacePairStratum) =>
        compositionClass + "~" + progressionMagnitude + "~" + spacePairStratum;

    internal static string PopulationCellKeyForSelfTest(
        string compositionClass, string progressionMagnitude, string spacePairStratum) =>
        PopulationCellKey(compositionClass, progressionMagnitude, spacePairStratum);

    private static IReadOnlyDictionary<string, CrossTlPopulationCell> BuildPopulationCells(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds)
    {
        CrossTlStratifiedPairingSelectionDocument selection = study.StratifiedPairingSelection ??
            throw new InvalidOperationException("Cross-TL v4 population accounting requires stratified selection settings.");
        var groups = legalBuilds.GroupBy(build => new CrossTlPopulationBucketKey(
                build.HasEwRedundancy,
                build.HasMainOrReactorDuplication,
                build.AdvancedComponentCount,
                build.SpaceUtilizationClass))
            .Select(group => new CrossTlPopulationBucket(group.Key, group.LongCount()))
            .OrderBy(bucket => bucket.Key.HasEwRedundancy)
            .ThenBy(bucket => bucket.Key.HasMainOrReactorDuplication)
            .ThenBy(bucket => bucket.Key.AdvancedComponentCount)
            .ThenBy(bucket => bucket.Key.SpaceUtilizationClass, StringComparer.Ordinal)
            .ToArray();
        var counts = new Dictionary<string, long>(StringComparer.Ordinal);
        for (int i = 0; i < groups.Length; i++)
        for (int j = i; j < groups.Length; j++)
        {
            CrossTlPopulationBucket a = groups[i];
            CrossTlPopulationBucket b = groups[j];
            long pairCount = i == j
                ? checked(a.Count * (a.Count - 1L) / 2L)
                : checked(a.Count * b.Count);
            if (pairCount == 0) continue;
            string composition = CompositionPairClass(
                a.Key.HasEwRedundancy, a.Key.HasMainOrReactorDuplication,
                b.Key.HasEwRedundancy, b.Key.HasMainOrReactorDuplication);
            string progression = ProgressionMagnitudeStratumForSelfTest(
                a.Key.AdvancedComponentCount, b.Key.AdvancedComponentCount,
                selection.NearDistanceMaximum, selection.EqualLowAdvancedMaximum);
            string space = SpacePairStratumForSelfTest(
                a.Key.SpaceUtilizationClass, b.Key.SpaceUtilizationClass);
            string key = PopulationCellKey(composition, progression, space);
            counts[key] = counts.GetValueOrDefault(key) + pairCount;
        }
        long total = checked((long)legalBuilds.Count * (legalBuilds.Count - 1L) / 2L);
        if (counts.Values.Sum() != total)
        {
            throw new InvalidOperationException(
                $"Cross-TL v4 population cell accounting mismatch: expected {total}; observed {counts.Values.Sum()}.");
        }
        var result = new Dictionary<string, CrossTlPopulationCell>(StringComparer.Ordinal);
        foreach (string composition in selection.CompositionClasses)
        foreach (string progression in selection.ProgressionMagnitudeStrata)
        foreach (string space in selection.SpacePairStrata)
        {
            string key = PopulationCellKey(composition, progression, space);
            long count = counts.GetValueOrDefault(key);
            result.Add(key, new CrossTlPopulationCell(
                key, composition, progression, space, count,
                total == 0 ? 0.0 : (double)count / total));
        }
        if (counts.Count != result.Count || counts.Keys.Any(key => !result.ContainsKey(key)))
        {
            string unexpected = string.Join(",", counts.Keys.Where(key => !result.ContainsKey(key)).OrderBy(key => key, StringComparer.Ordinal));
            throw new InvalidOperationException(
                $"Cross-TL v4 population accounting produced cells outside the configured 96-cell matrix: {unexpected}.");
        }
        if (result.Count != selection.CompositionClasses.Count *
            selection.ProgressionMagnitudeStrata.Count * selection.SpacePairStrata.Count ||
            result.Values.Any(cell => cell.PopulationUnorderedDistinctCount <= 0))
        {
            throw new InvalidOperationException(
                "Cross-TL v4 population accounting requires every configured composition/progression/Space cell to have nonzero legal population.");
        }
        return result;
    }

    private static string CompositionPairClass(
        bool sideAEwRedundancy,
        bool sideAMainOrReactorDuplication,
        bool sideBEwRedundancy,
        bool sideBMainOrReactorDuplication)
    {
        bool ew = sideAEwRedundancy || sideBEwRedundancy;
        bool main = sideAMainOrReactorDuplication || sideBMainOrReactorDuplication;
        return main && ew
            ? "combined-duplication"
            : main
                ? "weapon-reactor-duplication"
                : ew
                    ? "ew-redundancy"
                    : "single-no-ew-redundancy";
    }

    private static CrossTlLogicalPairing CreatePairing(
        string id,
        string groupId,
        string sideARecipe,
        string sideBRecipe,
        CrossTlResolvedBuild sideA,
        CrossTlResolvedBuild sideB,
        string source,
        string matchedBundleId,
        string orientation,
        CrossTlStratifiedPairingSelectionDocument? selection,
        CrossTlReadinessContext? readiness,
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells,
        int populationSampleCount = 0,
        string progressionTransitionId = "",
        int expectedAdvancedComponentDelta = 0)
    {
        string composition = CompositionPairClass(sideA, sideB);
        string progressionMagnitude = ProgressionMagnitudeStratum(sideA, sideB, selection);
        string spacePair = SpacePairStratum(sideA, sideB);
        string populationKey = PopulationCellKey(composition, progressionMagnitude, spacePair);
        populationCells.TryGetValue(populationKey, out CrossTlPopulationCell? population);
        CrossTlEngagementReadiness readinessA = EngagementReadiness(sideA, sideB, readiness);
        CrossTlEngagementReadiness readinessB = EngagementReadiness(sideB, sideA, readiness);
        long populationCount = population?.PopulationUnorderedDistinctCount ?? 0L;
        double representativeWeight = populationSampleCount > 0
            ? (double)populationCount / populationSampleCount
            : 0.0;
        int informationDistance = Math.Abs(
            sideA.InformationControlAdvancedCount - sideB.InformationControlAdvancedCount);
        string informationBand = InformationControlDistanceBand(sideA, sideB, selection);
        return new CrossTlLogicalPairing(
            id, groupId, sideARecipe, sideBRecipe, sideA, sideB, source,
            ProgressionDirection(sideA, sideB), ProgressionDistance(sideA, sideB),
            ProgressionStratum(sideA, sideB, selection), composition,
            matchedBundleId, orientation, progressionMagnitude, spacePair,
            sideA.UsedSpace - sideB.UsedSpace,
            Math.Abs(sideA.UsedSpace - sideB.UsedSpace),
            WeaponFamilyPair(sideA, sideB),
            InformationControlDirection(sideA, sideB),
            informationDistance, informationBand,
            readinessA.ReadinessClass, readinessB.ReadinessClass,
            readinessA.MaximumReadyRangeHexes, readinessB.MaximumReadyRangeHexes,
            populationKey, populationCount, populationSampleCount, representativeWeight,
            SecondaryCoverageKey(sideA, sideB, selection),
            progressionTransitionId, expectedAdvancedComponentDelta);
    }

    private static IReadOnlyList<CrossTlLogicalPairing> ExpandPairings(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds,
        IReadOnlyDictionary<string, CrossTlResolvedBuild> namedBuilds,
        CrossTlReadinessContext? readiness,
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells,
        IReadOnlyList<CrossTlProgressionEdge> progressionEdges)
    {
        var result = new List<CrossTlLogicalPairing>();
        var orderedPairs = new HashSet<string>(StringComparer.Ordinal);
        foreach (CrossTlPairingGroupDocument group in study.PairingGroups)
        {
            if (string.IsNullOrWhiteSpace(group.Id) || group.SideARecipes.Count == 0 || group.SideBRecipes.Count == 0)
            {
                throw new InvalidOperationException("Cross-TL pairing groups must identify non-empty recipe sets.");
            }
            foreach (string sideARecipe in group.SideARecipes)
            foreach (string sideBRecipe in group.SideBRecipes)
            {
                if (!namedBuilds.TryGetValue(sideARecipe, out CrossTlResolvedBuild? sideA) ||
                    !namedBuilds.TryGetValue(sideBRecipe, out CrossTlResolvedBuild? sideB))
                {
                    throw new InvalidOperationException(
                        $"Pairing group '{group.Id}' references an unknown named recipe.");
                }
                string pairKey = sideA.Id + "|" + sideB.Id;
                if (!orderedPairs.Add(pairKey))
                {
                    throw new InvalidOperationException(
                        $"Ordered build pairing '{sideARecipe}' vs '{sideBRecipe}' appears more than once.");
                }
                string id = $"{group.Id}-{sideARecipe}-vs-{sideBRecipe}";
                string transitionId = group.ProgressionTransitionId ?? string.Empty;
                if (!string.IsNullOrWhiteSpace(transitionId) &&
                    progressionEdges.All(edge => !string.Equals(edge.TransitionId, transitionId, StringComparison.Ordinal) ||
                        !string.Equals(edge.LowerBuildId, sideA.Id, StringComparison.Ordinal) ||
                        !string.Equals(edge.HigherBuildId, sideB.Id, StringComparison.Ordinal)))
                {
                    throw new InvalidOperationException(
                        $"Named pairing group '{group.Id}' does not correspond to progression transition '{transitionId}' for the selected lower/higher build endpoints.");
                }
                int expectedDelta = string.IsNullOrWhiteSpace(transitionId)
                    ? 0
                    : progressionEdges.First(edge => string.Equals(edge.TransitionId, transitionId, StringComparison.Ordinal) &&
                        string.Equals(edge.LowerBuildId, sideA.Id, StringComparison.Ordinal) &&
                        string.Equals(edge.HigherBuildId, sideB.Id, StringComparison.Ordinal)).ExpectedAdvancedComponentDelta;
                result.Add(CreatePairing(
                    id, group.Id, sideARecipe, sideBRecipe, sideA, sideB,
                    "named", id, "named", study.StratifiedPairingSelection,
                    readiness, populationCells, progressionTransitionId: transitionId,
                    expectedAdvancedComponentDelta: expectedDelta));
            }
        }
        if (study.ExpectedNamedLogicalPairingCount > 0 && result.Count != study.ExpectedNamedLogicalPairingCount)
        {
            throw new InvalidOperationException(
                $"Cross-TL named logical-pairing count mismatch: expected {study.ExpectedNamedLogicalPairingCount}; observed {result.Count}.");
        }
        if (study.ExactEdgePairingSelection?.Enabled == true)
        {
            if (study.StratifiedPairingSelection?.Enabled == true || result.Count != 0 ||
                study.ExpectedNamedLogicalPairingCount != 0)
            {
                throw new InvalidOperationException(
                    "Exact-edge progression sampling must remain isolated from named and broad stratified population sampling.");
            }
            IReadOnlyList<CrossTlLogicalPairing> exact = SelectExactProgressionEdgePairings(
                study, legalBuilds, progressionEdges, readiness);
            result.AddRange(exact);
            if (result.Count != study.ExpectedLogicalPairingCount)
            {
                throw new InvalidOperationException(
                    $"Cross-TL exact-edge logical-pairing count mismatch: expected {study.ExpectedLogicalPairingCount}; observed {result.Count}.");
            }
            return result;
        }
        if (study.StratifiedPairingSelection?.Enabled == true)
        {
            IReadOnlyList<CrossTlLogicalPairing> sampled = IsMatchedReadinessSchema(study.SchemaVersion)
                ? SelectMatchedStratifiedPairings(study, legalBuilds, readiness!, populationCells)
                : SelectLegacyStratifiedPairings(study, legalBuilds, orderedPairs);
            if (study.ExpectedStratifiedLogicalPairingCount > 0 && sampled.Count != study.ExpectedStratifiedLogicalPairingCount)
            {
                throw new InvalidOperationException(
                    $"Cross-TL stratified logical-pairing count mismatch: expected {study.ExpectedStratifiedLogicalPairingCount}; observed {sampled.Count}.");
            }
            result.AddRange(sampled);
        }
        else if (study.ExpectedStratifiedLogicalPairingCount != 0)
        {
            throw new InvalidOperationException("Cross-TL study declares stratified logical pairings but stratified selection is disabled.");
        }
        if (result.Count != study.ExpectedLogicalPairingCount)
        {
            throw new InvalidOperationException(
                $"Cross-TL logical-pairing count mismatch: expected {study.ExpectedLogicalPairingCount}; observed {result.Count}.");
        }
        return result;
    }

    private static IReadOnlyList<CrossTlLogicalPairing> SelectExactProgressionEdgePairings(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds,
        IReadOnlyList<CrossTlProgressionEdge> progressionEdges,
        CrossTlReadinessContext? readiness)
    {
        CrossTlExactEdgePairingSelectionDocument selection = study.ExactEdgePairingSelection ??
            throw new InvalidOperationException("Exact-edge pairing selection is missing.");
        if (selection.RepresentativesPerStratum <= 0 || selection.ExpectedStratumCount <= 0 ||
            selection.ExpectedLogicalPairingCount != selection.RepresentativesPerStratum * selection.ExpectedStratumCount ||
            selection.Strata.Count != 4 ||
            !selection.Strata.SequenceEqual(new[] { "transition", "weaponFamily", "compositionClass", "spaceUtilizationClass" }, StringComparer.Ordinal))
        {
            throw new InvalidOperationException("Exact-edge pairing selection has invalid deterministic stratum accounting.");
        }
        var buildsById = legalBuilds.ToDictionary(build => build.Id, StringComparer.Ordinal);
        string CellKey(CrossTlProgressionEdge edge) => string.Join("|", new[]
        {
            edge.TransitionId, edge.WeaponFamily.ToString(), edge.CompositionClass, edge.SpaceUtilizationClass,
        });
        IGrouping<string, CrossTlProgressionEdge>[] groups = progressionEdges
            .GroupBy(CellKey, StringComparer.Ordinal)
            .OrderBy(group => group.Key, StringComparer.Ordinal)
            .ToArray();
        if (groups.Length != selection.ExpectedStratumCount)
        {
            throw new InvalidOperationException(
                $"Exact-edge progression sampling expected {selection.ExpectedStratumCount} populated strata; observed {groups.Length}.");
        }
        var emptyPopulation = new Dictionary<string, CrossTlPopulationCell>(StringComparer.Ordinal);
        var result = new List<CrossTlLogicalPairing>();
        foreach (IGrouping<string, CrossTlProgressionEdge> group in groups)
        {
            CrossTlProgressionEdge[] candidates = group
                .OrderBy(edge => edge.LowerBuildId, StringComparer.Ordinal)
                .ThenBy(edge => edge.HigherBuildId, StringComparer.Ordinal)
                .ToArray();
            if (candidates.Length < selection.RepresentativesPerStratum)
            {
                throw new InvalidOperationException(
                    $"Exact-edge progression stratum '{group.Key}' contains only {candidates.Length} edges; " +
                    $"{selection.RepresentativesPerStratum} are required.");
            }
            for (int i = 0; i < selection.RepresentativesPerStratum; i++)
            {
                CrossTlProgressionEdge edge = candidates[i];
                CrossTlResolvedBuild lower = buildsById[edge.LowerBuildId];
                CrossTlResolvedBuild higher = buildsById[edge.HigherBuildId];
                string id = $"edge-{edge.TransitionId}-{edge.WeaponFamily}-{edge.CompositionClass}-{edge.SpaceUtilizationClass}-{i + 1:D2}";
                result.Add(CreatePairing(
                    id, "exact-progression-edge", lower.Id, higher.Id, lower, higher,
                    "exact_progression_edge", id, "lower-vs-higher", study.StratifiedPairingSelection,
                    readiness, emptyPopulation, 0, edge.TransitionId, edge.ExpectedAdvancedComponentDelta));
            }
        }
        if (result.Count != selection.ExpectedLogicalPairingCount)
        {
            throw new InvalidOperationException(
                $"Exact-edge progression sampling expected {selection.ExpectedLogicalPairingCount} logical pairs; observed {result.Count}.");
        }
        return result;
    }

    private static IReadOnlyList<CrossTlLogicalPairing> SelectLegacyStratifiedPairings(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds,
        HashSet<string> orderedPairs)
    {
        CrossTlStratifiedPairingSelectionDocument selection = study.StratifiedPairingSelection ??
            throw new InvalidOperationException("Stratified pairing selection is missing.");
        if (selection.TargetPerCell <= 0 || selection.ExpectedSampleCount <= 0 || selection.MaxAttempts <= 0 ||
            selection.CompositionClasses.Count == 0 || selection.ProgressionStrata.Count == 0 ||
            selection.NearDistanceMaximum < 1 || selection.EqualLowAdvancedMaximum < 0 ||
            selection.ExpectedSampleCount != selection.TargetPerCell * selection.CompositionClasses.Count * selection.ProgressionStrata.Count)
        {
            throw new InvalidOperationException("Cross-TL stratified pairing selection has invalid progression-distance cell accounting.");
        }
        CrossTlResolvedBuild[] builds = legalBuilds.OrderBy(build => build.Id, StringComparer.Ordinal).ToArray();
        var counts = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (string composition in selection.CompositionClasses)
        foreach (string stratum in selection.ProgressionStrata)
        {
            counts[composition + "|" + stratum] = 0;
        }
        var result = new List<CrossTlLogicalPairing>();
        ulong state = selection.Seed == 0 ? 0x9e3779b97f4a7c15UL : selection.Seed;
        int attempts = 0;
        while (result.Count < selection.ExpectedSampleCount && attempts < selection.MaxAttempts)
        {
            attempts++;
            int aIndex = (int)(NextDeterministic(ref state) % (ulong)builds.Length);
            int bIndex = (int)(NextDeterministic(ref state) % (ulong)builds.Length);
            if (aIndex == bIndex) continue;
            CrossTlResolvedBuild sideA = builds[aIndex];
            CrossTlResolvedBuild sideB = builds[bIndex];
            string composition = CompositionPairClass(sideA, sideB);
            string direction = ProgressionDirection(sideA, sideB);
            int distance = ProgressionDistance(sideA, sideB);
            string stratum = ProgressionStratum(sideA, sideB, selection);
            string cell = composition + "|" + stratum;
            if (!counts.TryGetValue(cell, out int cellCount) || cellCount >= selection.TargetPerCell) continue;
            string pairKey = sideA.Id + "|" + sideB.Id;
            if (!orderedPairs.Add(pairKey)) continue;
            int ordinal = cellCount + 1;
            counts[cell] = ordinal;
            string id = $"sample-{composition}-{stratum}-{ordinal:D2}";
            result.Add(new CrossTlLogicalPairing(
                id, "stratified-sample", sideA.Id, sideB.Id, sideA, sideB,
                "stratified", direction, distance, stratum, composition,
                id, "legacy", ProgressionMagnitudeStratum(sideA, sideB, selection),
                SpacePairStratum(sideA, sideB), sideA.UsedSpace - sideB.UsedSpace,
                Math.Abs(sideA.UsedSpace - sideB.UsedSpace), WeaponFamilyPair(sideA, sideB),
                InformationControlDirection(sideA, sideB),
                Math.Abs(sideA.InformationControlAdvancedCount - sideB.InformationControlAdvancedCount),
                InformationControlDistanceBand(sideA, sideB, selection),
                "not_classified", "not_classified", -1, -1, string.Empty, 0L, 0, 0.0,
                SecondaryCoverageKey(sideA, sideB, selection)));
        }
        string[] incomplete = counts.Where(pair => pair.Value != selection.TargetPerCell)
            .Select(pair => $"{pair.Key}={pair.Value}").ToArray();
        if (incomplete.Length > 0)
        {
            throw new InvalidOperationException(
                "Cross-TL deterministic stratified sampler could not fill all requested cells: " + string.Join(", ", incomplete));
        }
        return result;
    }

    private static IReadOnlyList<CrossTlLogicalPairing> SelectMatchedStratifiedPairings(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds,
        CrossTlReadinessContext readiness,
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells)
    {
        return IsAdaptiveSamplingSchema(study.SchemaVersion)
            ? SelectAdaptiveMatchedPairings(study, legalBuilds, readiness, populationCells)
            : SelectMatchedStratifiedPairingsV4(study, legalBuilds, readiness, populationCells);
    }

    private static IReadOnlyList<CrossTlLogicalPairing> SelectMatchedStratifiedPairingsV4(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds,
        CrossTlReadinessContext readiness,
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells)
    {
        CrossTlStratifiedPairingSelectionDocument selection = study.StratifiedPairingSelection ??
            throw new InvalidOperationException("Matched stratified pairing selection is missing.");
        int configuredCells = selection.CompositionClasses.Count *
            selection.ProgressionMagnitudeStrata.Count * selection.SpacePairStrata.Count;
        int expectedBasePairs = checked(selection.TargetPerCell * configuredCells);
        if (!selection.MatchedBidirectional || selection.TargetPerCell <= 0 || selection.MaxAttempts <= 0 ||
            selection.CompositionClasses.Count == 0 || selection.ProgressionMagnitudeStrata.Count == 0 ||
            selection.SpaceUtilizationClasses.Count != 3 || selection.SpacePairStrata.Count == 0 ||
            selection.NearDistanceMaximum < 1 || selection.EqualLowAdvancedMaximum < 0 ||
            selection.NearFillMinimumUsedSpace <= 0 ||
            selection.ExpectedBasePairCount != expectedBasePairs ||
            selection.ExpectedSampleCount != checked(expectedBasePairs * 2))
        {
            throw new InvalidOperationException(
                "Cross-TL v4 matched stratified selection has invalid composition/progression/Space cell accounting.");
        }
        string[] requiredSpaceClasses = { "exact_fill", "near_fill", "underfilled" };
        if (!requiredSpaceClasses.SequenceEqual(selection.SpaceUtilizationClasses, StringComparer.Ordinal))
        {
            throw new InvalidOperationException(
                "Cross-TL v4 Space-utilization classes must be exact_fill, near_fill, underfilled in canonical order.");
        }
        CrossTlResolvedBuild[] builds = legalBuilds.OrderBy(build => build.Id, StringComparer.Ordinal).ToArray();
        var counts = populationCells.Keys.ToDictionary(key => key, _ => 0, StringComparer.Ordinal);
        var selectedUnordered = new HashSet<string>(StringComparer.Ordinal);
        var result = new List<CrossTlLogicalPairing>();
        ulong state = selection.Seed == 0 ? 0x9e3779b97f4a7c15UL : selection.Seed;
        int attempts = 0;
        int basePairCount = 0;
        while (basePairCount < selection.ExpectedBasePairCount && attempts < selection.MaxAttempts)
        {
            attempts++;
            int aIndex = (int)(NextDeterministic(ref state) % (ulong)builds.Length);
            int bIndex = (int)(NextDeterministic(ref state) % (ulong)builds.Length);
            if (aIndex == bIndex) continue;
            CrossTlResolvedBuild x = builds[aIndex];
            CrossTlResolvedBuild y = builds[bIndex];
            if (string.CompareOrdinal(x.Id, y.Id) > 0) (x, y) = (y, x);
            string unorderedKey = x.Id + "|" + y.Id;
            if (!selectedUnordered.Add(unorderedKey)) continue;
            string composition = CompositionPairClass(x, y);
            string progression = ProgressionMagnitudeStratum(x, y, selection);
            string space = SpacePairStratum(x, y);
            string cell = PopulationCellKey(composition, progression, space);
            if (!counts.TryGetValue(cell, out int cellCount) || cellCount >= selection.TargetPerCell)
            {
                selectedUnordered.Remove(unorderedKey);
                continue;
            }
            CrossTlPopulationCell population = populationCells[cell];
            if (population.PopulationUnorderedDistinctCount <= 0)
            {
                selectedUnordered.Remove(unorderedKey);
                continue;
            }
            int ordinal = cellCount + 1;
            counts[cell] = ordinal;
            basePairCount++;
            string bundleId = $"matched-{composition}-{progression}-{space}-{ordinal:D2}";
            result.Add(CreatePairing(
                bundleId + "-forward", "matched-stratified-sample", x.Id, y.Id, x, y,
                "stratified", bundleId, "forward", selection, readiness, populationCells, 1));
            result.Add(CreatePairing(
                bundleId + "-reverse", "matched-stratified-sample", y.Id, x.Id, y, x,
                "stratified", bundleId, "reverse", selection, readiness, populationCells, 1));
        }
        string[] incomplete = counts.Where(pair => pair.Value != selection.TargetPerCell)
            .Select(pair => $"{pair.Key}={pair.Value}").ToArray();
        if (incomplete.Length > 0 || basePairCount != selection.ExpectedBasePairCount || result.Count != selection.ExpectedSampleCount)
        {
            throw new InvalidOperationException(
                "Cross-TL deterministic matched sampler could not fill all requested cells: " +
                (incomplete.Length == 0 ? "count mismatch" : string.Join(", ", incomplete)));
        }
        return result;
    }

    private static IReadOnlyDictionary<string, int> AllocateAdaptiveCellQuotas(
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells,
        CrossTlStratifiedPairingSelectionDocument selection)
    {
        if (!selection.AdaptiveAllocationEnabled || selection.TargetBasePairBudget <= 0 ||
            selection.MinimumPerPopulationCell <= 0 || selection.AllocationExponent <= 0.0 ||
            selection.MaximumPerPopulationCell < selection.MinimumPerPopulationCell)
        {
            throw new InvalidOperationException("Cross-TL v5 adaptive allocation settings are invalid.");
        }
        CrossTlPopulationCell[] cells = populationCells.Values
            .OrderBy(cell => cell.Key, StringComparer.Ordinal).ToArray();
        int minimumTotal = checked(selection.MinimumPerPopulationCell * cells.Length);
        int maximumTotal = checked(selection.MaximumPerPopulationCell * cells.Length);
        if (selection.TargetBasePairBudget < minimumTotal || selection.TargetBasePairBudget > maximumTotal)
        {
            throw new InvalidOperationException(
                $"Cross-TL v5 adaptive base-pair budget {selection.TargetBasePairBudget} is outside the configured [{minimumTotal},{maximumTotal}] allocation envelope.");
        }
        var quotas = cells.ToDictionary(
            cell => cell.Key,
            _ => selection.MinimumPerPopulationCell,
            StringComparer.Ordinal);
        int remaining = selection.TargetBasePairBudget - minimumTotal;
        if (remaining == 0) return quotas;

        double[] weights = cells.Select(cell =>
            Math.Pow(cell.PopulationUnorderedDistinctCount, selection.AllocationExponent)).ToArray();
        double totalWeight = weights.Sum();
        if (!(totalWeight > 0.0) || double.IsNaN(totalWeight) || double.IsInfinity(totalWeight))
        {
            throw new InvalidOperationException("Cross-TL v5 adaptive allocation produced an invalid population weight total.");
        }
        var fractional = new List<(string Key, double Remainder, long Population)>();
        int allocated = 0;
        for (int i = 0; i < cells.Length; i++)
        {
            double exactExtra = remaining * weights[i] / totalWeight;
            int floorExtra = Math.Min(
                selection.MaximumPerPopulationCell - selection.MinimumPerPopulationCell,
                (int)Math.Floor(exactExtra));
            quotas[cells[i].Key] += floorExtra;
            allocated += floorExtra;
            fractional.Add((cells[i].Key, exactExtra - Math.Floor(exactExtra), cells[i].PopulationUnorderedDistinctCount));
        }
        int residual = remaining - allocated;
        var order = fractional
            .OrderByDescending(item => item.Remainder)
            .ThenByDescending(item => item.Population)
            .ThenBy(item => item.Key, StringComparer.Ordinal)
            .ToArray();
        while (residual > 0)
        {
            bool progressed = false;
            foreach ((string key, _, _) in order)
            {
                if (quotas[key] >= selection.MaximumPerPopulationCell) continue;
                quotas[key]++;
                residual--;
                progressed = true;
                if (residual == 0) break;
            }
            if (!progressed)
            {
                throw new InvalidOperationException("Cross-TL v5 adaptive allocation could not satisfy the requested base-pair budget within the configured per-cell cap.");
            }
        }
        if (quotas.Values.Sum() != selection.TargetBasePairBudget ||
            quotas.Values.Any(value => value < selection.MinimumPerPopulationCell || value > selection.MaximumPerPopulationCell))
        {
            throw new InvalidOperationException("Cross-TL v5 adaptive allocation failed its quota conservation contract.");
        }
        return quotas;
    }

    internal static int[] AllocateAdaptiveQuotasForSelfTest(
        IReadOnlyList<long> populations,
        int budget,
        int minimum,
        double exponent,
        int maximum)
    {
        var cells = new Dictionary<string, CrossTlPopulationCell>(StringComparer.Ordinal);
        long total = populations.Sum();
        for (int i = 0; i < populations.Count; i++)
        {
            string key = $"c{i:D3}";
            cells[key] = new CrossTlPopulationCell(
                key, "test", "test", "test", populations[i], total <= 0 ? 0.0 : (double)populations[i] / total);
        }
        var selection = new CrossTlStratifiedPairingSelectionDocument
        {
            AdaptiveAllocationEnabled = true,
            TargetBasePairBudget = budget,
            MinimumPerPopulationCell = minimum,
            AllocationExponent = exponent,
            MaximumPerPopulationCell = maximum,
        };
        IReadOnlyDictionary<string, int> quotas = AllocateAdaptiveCellQuotas(cells, selection);
        return quotas.OrderBy(pair => pair.Key, StringComparer.Ordinal).Select(pair => pair.Value).ToArray();
    }

    private static IReadOnlyList<CrossTlLogicalPairing> SelectAdaptiveMatchedPairings(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds,
        CrossTlReadinessContext readiness,
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells)
    {
        CrossTlStratifiedPairingSelectionDocument selection = study.StratifiedPairingSelection ??
            throw new InvalidOperationException("Adaptive matched pairing selection is missing.");
        int configuredCells = selection.CompositionClasses.Count *
            selection.ProgressionMagnitudeStrata.Count * selection.SpacePairStrata.Count;
        if (!selection.MatchedBidirectional || selection.MaxAttempts <= 0 || configuredCells != populationCells.Count ||
            selection.ExpectedBasePairCount != selection.TargetBasePairBudget ||
            selection.ExpectedSampleCount != checked(selection.ExpectedBasePairCount * 2) ||
            selection.ExpectedDiversityBasePairCount != checked(selection.DiversityOverlayTopCellCount * selection.DiversityOverlayPairsPerCell) ||
            selection.ExpectedDiversitySampleCount != checked(selection.ExpectedDiversityBasePairCount * 2) ||
            selection.InformationControlNearDistanceMaximum < 1 ||
            selection.SpaceUtilizationClasses.Count != 3)
        {
            throw new InvalidOperationException("Cross-TL v5 adaptive matched sampling settings are inconsistent.");
        }
        string[] requiredSpaceClasses = { "exact_fill", "near_fill", "underfilled" };
        if (!requiredSpaceClasses.SequenceEqual(selection.SpaceUtilizationClasses, StringComparer.Ordinal))
        {
            throw new InvalidOperationException(
                "Cross-TL v5 Space-utilization classes must be exact_fill, near_fill, underfilled in canonical order.");
        }

        IReadOnlyDictionary<string, int> quotas = AllocateAdaptiveCellQuotas(populationCells, selection);
        CrossTlResolvedBuild[] builds = legalBuilds.OrderBy(build => build.Id, StringComparer.Ordinal).ToArray();
        var counts = populationCells.Keys.ToDictionary(key => key, _ => 0, StringComparer.Ordinal);
        var selectedUnordered = new HashSet<string>(StringComparer.Ordinal);
        var result = new List<CrossTlLogicalPairing>();
        ulong state = selection.Seed == 0 ? 0x9e3779b97f4a7c15UL : selection.Seed;
        int attempts = 0;
        int statisticalBasePairCount = 0;
        while (statisticalBasePairCount < selection.ExpectedBasePairCount && attempts < selection.MaxAttempts)
        {
            attempts++;
            int aIndex = (int)(NextDeterministic(ref state) % (ulong)builds.Length);
            int bIndex = (int)(NextDeterministic(ref state) % (ulong)builds.Length);
            if (aIndex == bIndex) continue;
            CrossTlResolvedBuild x = builds[aIndex];
            CrossTlResolvedBuild y = builds[bIndex];
            if (string.CompareOrdinal(x.Id, y.Id) > 0) (x, y) = (y, x);
            string composition = CompositionPairClass(x, y);
            string progression = ProgressionMagnitudeStratum(x, y, selection);
            string space = SpacePairStratum(x, y);
            string cell = PopulationCellKey(composition, progression, space);
            if (!counts.TryGetValue(cell, out int cellCount) || cellCount >= quotas[cell]) continue;
            string unorderedKey = x.Id + "|" + y.Id;
            if (!selectedUnordered.Add(unorderedKey)) continue;
            int ordinal = cellCount + 1;
            counts[cell] = ordinal;
            statisticalBasePairCount++;
            string bundleId = $"adaptive-{composition}-{progression}-{space}-{ordinal:D2}";
            result.Add(CreatePairing(
                bundleId + "-forward", "adaptive-statistical-sample", x.Id, y.Id, x, y,
                "statistical", bundleId, "forward", selection, readiness, populationCells, quotas[cell]));
            result.Add(CreatePairing(
                bundleId + "-reverse", "adaptive-statistical-sample", y.Id, x.Id, y, x,
                "statistical", bundleId, "reverse", selection, readiness, populationCells, quotas[cell]));
        }
        string[] incomplete = counts.Where(pair => pair.Value != quotas[pair.Key])
            .Select(pair => $"{pair.Key}={pair.Value}/{quotas[pair.Key]}").ToArray();
        if (incomplete.Length > 0 || statisticalBasePairCount != selection.ExpectedBasePairCount ||
            result.Count != selection.ExpectedSampleCount)
        {
            throw new InvalidOperationException(
                "Cross-TL v5 adaptive sampler could not fill all allocated population-cell quotas: " +
                (incomplete.Length == 0 ? "count mismatch" : string.Join(", ", incomplete.Take(12))));
        }

        if (selection.DiversityOverlayEnabled && selection.ExpectedDiversityBasePairCount > 0)
        {
            string[] topCells = populationCells.Values
                .OrderByDescending(cell => cell.PopulationUnorderedDistinctCount)
                .ThenBy(cell => cell.Key, StringComparer.Ordinal)
                .Take(selection.DiversityOverlayTopCellCount)
                .Select(cell => cell.Key).ToArray();
            var topCellSet = new HashSet<string>(topCells, StringComparer.Ordinal);
            var overlayCounts = topCells.ToDictionary(key => key, _ => 0, StringComparer.Ordinal);
            var secondaryCoverage = topCells.ToDictionary(
                key => key,
                key => new HashSet<string>(
                    result.Where(pair => pair.Source == "statistical" && pair.Orientation == "forward" && pair.PopulationCellKey == key)
                        .Select(pair => pair.SecondaryCoverageKey),
                    StringComparer.Ordinal),
                StringComparer.Ordinal);
            ulong overlayState = selection.Seed ^ 0xd1b54a32d192ed03UL;
            int overlayAttempts = 0;
            int overlayBasePairCount = 0;

            void AddOverlayPair(CrossTlResolvedBuild x, CrossTlResolvedBuild y, string cell)
            {
                int ordinal = overlayCounts[cell] + 1;
                overlayCounts[cell] = ordinal;
                overlayBasePairCount++;
                string composition = CompositionPairClass(x, y);
                string progression = ProgressionMagnitudeStratum(x, y, selection);
                string space = SpacePairStratum(x, y);
                string bundleId = $"diversity-{composition}-{progression}-{space}-{ordinal:D2}";
                result.Add(CreatePairing(
                    bundleId + "-forward", "secondary-diversity-overlay", x.Id, y.Id, x, y,
                    "diversity", bundleId, "forward", selection, readiness, populationCells));
                result.Add(CreatePairing(
                    bundleId + "-reverse", "secondary-diversity-overlay", y.Id, x.Id, y, x,
                    "diversity", bundleId, "reverse", selection, readiness, populationCells));
            }

            // First pass prefers family-pair/information-gap combinations not already represented
            // in the statistical sample for each high-population cell.
            while (overlayBasePairCount < selection.ExpectedDiversityBasePairCount &&
                   overlayAttempts < selection.MaxAttempts)
            {
                overlayAttempts++;
                int aIndex = (int)(NextDeterministic(ref overlayState) % (ulong)builds.Length);
                int bIndex = (int)(NextDeterministic(ref overlayState) % (ulong)builds.Length);
                if (aIndex == bIndex) continue;
                CrossTlResolvedBuild x = builds[aIndex];
                CrossTlResolvedBuild y = builds[bIndex];
                if (string.CompareOrdinal(x.Id, y.Id) > 0) (x, y) = (y, x);
                string cell = PopulationCellKey(
                    CompositionPairClass(x, y), ProgressionMagnitudeStratum(x, y, selection), SpacePairStratum(x, y));
                if (!topCellSet.Contains(cell) || overlayCounts[cell] >= selection.DiversityOverlayPairsPerCell) continue;
                string unorderedKey = x.Id + "|" + y.Id;
                if (selectedUnordered.Contains(unorderedKey)) continue;
                string secondaryKey = SecondaryCoverageKey(x, y, selection);
                if (secondaryCoverage[cell].Contains(secondaryKey)) continue;
                selectedUnordered.Add(unorderedKey);
                secondaryCoverage[cell].Add(secondaryKey);
                AddOverlayPair(x, y, cell);
            }

            // If a top cell has fewer distinct secondary combinations than its overlay quota,
            // fill the remaining slots with deterministic unique pairs. These remain diagnostic
            // and carry zero population-inference weight.
            overlayAttempts = 0;
            while (overlayBasePairCount < selection.ExpectedDiversityBasePairCount &&
                   overlayAttempts < selection.MaxAttempts)
            {
                overlayAttempts++;
                int aIndex = (int)(NextDeterministic(ref overlayState) % (ulong)builds.Length);
                int bIndex = (int)(NextDeterministic(ref overlayState) % (ulong)builds.Length);
                if (aIndex == bIndex) continue;
                CrossTlResolvedBuild x = builds[aIndex];
                CrossTlResolvedBuild y = builds[bIndex];
                if (string.CompareOrdinal(x.Id, y.Id) > 0) (x, y) = (y, x);
                string cell = PopulationCellKey(
                    CompositionPairClass(x, y), ProgressionMagnitudeStratum(x, y, selection), SpacePairStratum(x, y));
                if (!topCellSet.Contains(cell) || overlayCounts[cell] >= selection.DiversityOverlayPairsPerCell) continue;
                string unorderedKey = x.Id + "|" + y.Id;
                if (!selectedUnordered.Add(unorderedKey)) continue;
                secondaryCoverage[cell].Add(SecondaryCoverageKey(x, y, selection));
                AddOverlayPair(x, y, cell);
            }
            string[] incompleteOverlay = overlayCounts
                .Where(pair => pair.Value != selection.DiversityOverlayPairsPerCell)
                .Select(pair => $"{pair.Key}={pair.Value}/{selection.DiversityOverlayPairsPerCell}").ToArray();
            if (incompleteOverlay.Length > 0 || overlayBasePairCount != selection.ExpectedDiversityBasePairCount ||
                result.Count != selection.ExpectedSampleCount + selection.ExpectedDiversitySampleCount)
            {
                throw new InvalidOperationException(
                    "Cross-TL v5 diversity overlay could not fill all requested high-population cells: " +
                    (incompleteOverlay.Length == 0 ? "count mismatch" : string.Join(", ", incompleteOverlay)));
            }
        }
        return result;
    }

    private static ulong NextDeterministic(ref ulong state)
    {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        return state;
    }

    private static string ProgressionDirection(CrossTlResolvedBuild sideA, CrossTlResolvedBuild sideB) =>
        sideA.AdvancedComponentCount < sideB.AdvancedComponentCount
            ? "side_a_lower"
            : sideA.AdvancedComponentCount > sideB.AdvancedComponentCount
                ? "side_a_higher"
                : "equal";

    private static int ProgressionDistance(CrossTlResolvedBuild sideA, CrossTlResolvedBuild sideB) =>
        Math.Abs(sideA.AdvancedComponentCount - sideB.AdvancedComponentCount);

    private static string ProgressionStratum(
        CrossTlResolvedBuild sideA,
        CrossTlResolvedBuild sideB,
        CrossTlStratifiedPairingSelectionDocument? selection)
    {
        string direction = ProgressionDirection(sideA, sideB);
        if (selection is null) return direction;
        int distance = ProgressionDistance(sideA, sideB);
        if (direction == "equal")
        {
            return sideA.AdvancedComponentCount <= selection.EqualLowAdvancedMaximum
                ? "equal_low"
                : "equal_high";
        }
        string band = distance <= selection.NearDistanceMaximum ? "near" : "far";
        return direction + "_" + band;
    }

    private static string CompositionPairClass(CrossTlResolvedBuild sideA, CrossTlResolvedBuild sideB) =>
        CompositionPairClass(
            sideA.HasEwRedundancy, sideA.HasMainOrReactorDuplication,
            sideB.HasEwRedundancy, sideB.HasMainOrReactorDuplication);

    internal static string ProgressionDirectionForSelfTest(int sideAAdvancedComponents, int sideBAdvancedComponents) =>
        sideAAdvancedComponents < sideBAdvancedComponents ? "side_a_lower" :
        sideAAdvancedComponents > sideBAdvancedComponents ? "side_a_higher" : "equal";

    internal static string ProgressionStratumForSelfTest(
        int sideAAdvancedComponents, int sideBAdvancedComponents, int nearDistanceMaximum, int equalLowAdvancedMaximum)
    {
        int distance = Math.Abs(sideAAdvancedComponents - sideBAdvancedComponents);
        if (distance == 0) return sideAAdvancedComponents <= equalLowAdvancedMaximum ? "equal_low" : "equal_high";
        string direction = sideAAdvancedComponents < sideBAdvancedComponents ? "side_a_lower" : "side_a_higher";
        return direction + "_" + (distance <= nearDistanceMaximum ? "near" : "far");
    }

    private static int ResolveExpectedAdvancedComponentDelta(
        CrossTlProgressionTransitionDocument transition,
        CrossTlTechnologyOptionDocument from,
        CrossTlTechnologyOptionDocument to)
    {
        int inferred = AdvancedComponentContribution(transition.AxisId, to) -
            AdvancedComponentContribution(transition.AxisId, from);
        if (inferred <= 0)
        {
            throw new InvalidOperationException(
                $"Progression transition '{transition.Id}' does not increase the advanced-component contribution of axis '{transition.AxisId}'.");
        }
        if (transition.HasExplicitExpectedAdvancedComponentDelta &&
            transition.ExpectedAdvancedComponentDelta != inferred)
        {
            throw new InvalidOperationException(
                $"Progression transition '{transition.Id}' explicitly declares advanced-component delta " +
                $"{transition.ExpectedAdvancedComponentDelta}, but its from/to option multiplicity implies {inferred}.");
        }
        transition.ResolveLegacyExpectedAdvancedComponentDelta(inferred);
        return transition.ExpectedAdvancedComponentDelta;
    }

    private static int AdvancedComponentContribution(
        string axisId,
        CrossTlTechnologyOptionDocument option) => axisId switch
    {
        "weapon" => option.TechnologyLevel >= 2 ? option.MainWeaponCount ?? 1 : 0,
        "reactor" => option.TechnologyLevel >= 2 ? option.ReactorCount ?? 1 : 0,
        "computer" or "sensor" or "shield" or "armor" =>
            (option.Installed ?? true) && option.TechnologyLevel >= 2 ? 1 : 0,
        "ecm" or "eccm" => ResolveEwRatings(option).Count(rating => rating >= 2),
        _ => 0,
    };

    private static IReadOnlyList<CrossTlProgressionEdge> BuildProgressionLattice(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> legalBuilds)
    {
        CrossTlProgressionLatticeDocument? lattice = study.ProgressionLattice;
        if (lattice is null || !lattice.Enabled)
        {
            return Array.Empty<CrossTlProgressionEdge>();
        }
        if (lattice.Transitions.Count == 0 ||
            lattice.Transitions.Select(transition => transition.Id)
                .Distinct(StringComparer.Ordinal).Count() != lattice.Transitions.Count)
        {
            throw new InvalidOperationException(
                "Cross-TL progression lattice requires uniquely identified transitions.");
        }

        var axesById = study.Axes.ToDictionary(axis => axis.Id, StringComparer.Ordinal);
        string Signature(IReadOnlyDictionary<string, string> selections) =>
            string.Join("|", study.Axes.Select(axis => axis.Id + "=" + selections[axis.Id]));
        var buildsBySignature = legalBuilds.ToDictionary(
            build => Signature(build.Selections), build => build, StringComparer.Ordinal);
        var edges = new List<CrossTlProgressionEdge>();

        foreach (CrossTlProgressionTransitionDocument transition in lattice.Transitions)
        {
            if (!axesById.TryGetValue(transition.AxisId, out CrossTlTechnologyAxisDocument? axis) ||
                axis is null)
            {
                throw new InvalidOperationException(
                    $"Progression transition '{transition.Id}' references unknown axis '{transition.AxisId}'.");
            }
            CrossTlTechnologyOptionDocument? from = axis.Options.SingleOrDefault(option =>
                string.Equals(option.Id, transition.FromOptionId, StringComparison.Ordinal));
            CrossTlTechnologyOptionDocument? to = axis.Options.SingleOrDefault(option =>
                string.Equals(option.Id, transition.ToOptionId, StringComparison.Ordinal));
            if (from is null || to is null || from.TechnologyLevel >= to.TechnologyLevel)
            {
                throw new InvalidOperationException(
                    $"Progression transition '{transition.Id}' must map an existing lower-TL option to an existing higher-TL option.");
            }
            bool v7 = string.Equals(study.SchemaVersion, SchemaVersionV7, StringComparison.Ordinal);
            if (lattice.RequireSameInstallationSpace && from.Space != to.Space)
            {
                throw new InvalidOperationException(
                    $"Progression transition '{transition.Id}' changes Installation Space despite requireSameInstallationSpace=true.");
            }
            if (v7)
            {
                if (string.IsNullOrWhiteSpace(transition.Kind))
                {
                    throw new InvalidOperationException(
                        $"Cross-TL v7 progression transition '{transition.Id}' must declare kind.");
                }
                int observedOptionSpaceDelta = to.Space - from.Space;
                if (observedOptionSpaceDelta != transition.ExpectedInstallationSpaceDelta)
                {
                    throw new InvalidOperationException(
                        $"Progression transition '{transition.Id}' expected installed-Space delta {transition.ExpectedInstallationSpaceDelta}; observed {observedOptionSpaceDelta}.");
                }
                int observedCapacityDelta = (to.InstallationSpaceCapacity ?? 0) - (from.InstallationSpaceCapacity ?? 0);
                if (observedCapacityDelta != transition.ExpectedCapacityDelta)
                {
                    throw new InvalidOperationException(
                        $"Progression transition '{transition.Id}' expected Hull-capacity delta {transition.ExpectedCapacityDelta}; observed {observedCapacityDelta}.");
                }
            }

            int expectedAdvancedComponentDelta = v7
                ? 0
                : ResolveExpectedAdvancedComponentDelta(transition, from, to);
            int transitionCount = 0;
            int exactFillCount = 0;
            foreach (CrossTlResolvedBuild lower in legalBuilds.Where(build =>
                         string.Equals(build.Selections[transition.AxisId], transition.FromOptionId, StringComparison.Ordinal)))
            {
                var higherSelections = lower.Selections.ToDictionary(
                    pair => pair.Key, pair => pair.Value, StringComparer.Ordinal);
                higherSelections[transition.AxisId] = transition.ToOptionId;
                if (!buildsBySignature.TryGetValue(Signature(higherSelections), out CrossTlResolvedBuild? higher) ||
                    higher is null)
                {
                    continue;
                }
                int advancedComponentDelta = higher.AdvancedComponentCount - lower.AdvancedComponentCount;
                if (!v7 && (advancedComponentDelta != expectedAdvancedComponentDelta || advancedComponentDelta <= 0))
                {
                    throw new InvalidOperationException(
                        $"Progression transition '{transition.Id}' expected advanced-component delta " +
                        $"{expectedAdvancedComponentDelta}; observed {advancedComponentDelta} for '{lower.Id}'.");
                }
                if (v7)
                {
                    int observedInstalledSpaceDelta = higher.UsedSpace - lower.UsedSpace;
                    int observedCapacityDelta = higher.InstallationSpaceCapacity - lower.InstallationSpaceCapacity;
                    if (observedInstalledSpaceDelta != transition.ExpectedInstallationSpaceDelta ||
                        observedCapacityDelta != transition.ExpectedCapacityDelta)
                    {
                        throw new InvalidOperationException(
                            $"Progression transition '{transition.Id}' produced build-level Space/capacity deltas " +
                            $"{observedInstalledSpaceDelta}/{observedCapacityDelta} instead of " +
                            $"{transition.ExpectedInstallationSpaceDelta}/{transition.ExpectedCapacityDelta} for '{lower.Id}'.");
                    }
                }
                transitionCount++;
                if (lower.UsedSpace == lower.InstallationSpaceCapacity &&
                    higher.UsedSpace == higher.InstallationSpaceCapacity)
                {
                    exactFillCount++;
                }
                edges.Add(new CrossTlProgressionEdge(
                    transition.Id,
                    transition.AxisId,
                    transition.FromOptionId,
                    transition.ToOptionId,
                    transition.Kind ?? string.Empty,
                    transition.ExpectedInstallationSpaceDelta,
                    transition.ExpectedCapacityDelta,
                    lower.Id,
                    higher.Id,
                    lower.UsedSpace,
                    higher.UsedSpace,
                    lower.InstallationSpaceCapacity,
                    higher.InstallationSpaceCapacity,
                    lower.AdvancedComponentCount,
                    higher.AdvancedComponentCount,
                    lower.Family,
                    lower.CompositionClass,
                    lower.SpaceUtilizationClass,
                    expectedAdvancedComponentDelta));
            }
            if (transitionCount != transition.ExpectedLegalEdgeCount ||
                exactFillCount != transition.ExpectedExactFillEdgeCount)
            {
                throw new InvalidOperationException(
                    $"Progression transition '{transition.Id}' expected {transition.ExpectedLegalEdgeCount} legal / " +
                    $"{transition.ExpectedExactFillEdgeCount} exact-fill edges; observed {transitionCount} / {exactFillCount}.");
            }
        }
        if (edges.Count != lattice.ExpectedTotalLegalEdgeCount)
        {
            throw new InvalidOperationException(
                $"Cross-TL progression lattice expected {lattice.ExpectedTotalLegalEdgeCount} legal edges; observed {edges.Count}.");
        }
        return edges;
    }

    private static Tl1IntegratedTacticalCombatStudyDocument BuildIntegratedStudy(
        CrossTlBuildPermutationDocument study,
        string baselineHash,
        IReadOnlyDictionary<string, CrossTlResolvedBuild> namedBuilds,
        IReadOnlyList<CrossTlLogicalPairing> pairings)
    {
        if (study.Geometries.Count != study.ExpectedGeometryCount)
        {
            throw new InvalidOperationException(
                $"Cross-TL geometry count mismatch: expected {study.ExpectedGeometryCount}; observed {study.Geometries.Count}.");
        }
        bool generalized = IsGeneralizedSchema(study.SchemaVersion);
        var generated = new Tl1IntegratedTacticalCombatStudyDocument
        {
            Id = study.GeneratedStudyId,
            BaselineSha256 = baselineHash,
            MasterSeed = study.MasterSeed,
            TrialsPerVariant = study.TrialsPerVariant,
            TechnologyProfileCatalog = study.TechnologyProfileCatalog,
            AuxiliaryProfileCatalog = study.AuxiliaryProfileCatalog,
            SensorEwProfileCatalog = study.SensorEwProfileCatalog,
            AiDoctrineCatalog = study.AiDoctrineCatalog,
        };
        if (generalized)
        {
            foreach (CrossTlResolvedBuild build in pairings.SelectMany(pairing => new[] { pairing.SideA, pairing.SideB })
                .GroupBy(build => build.Id, StringComparer.Ordinal)
                .Select(group => group.First())
                .OrderBy(build => build.Id, StringComparer.Ordinal))
            {
                generated.Builds.Add(ToIntegratedBuild(build));
            }
        }
        else
        {
            generated.Builds.Add(new Tl1IntegratedShipBuildDocument
            {
                Id = "cross_tl_exact_fill_shell",
                MainWeaponCount = 1,
                MainReactorCount = 1,
                ActiveSensor = true,
                ShieldGenerator = true,
                KineticPdsCount = study.FixedShell.KineticPdsCount,
                EcmSuite = true,
                EccmSuite = true,
                UsedSpace = study.TotalInstallationSpace,
                FreeSupportSpace = 0,
            });
        }

        int variantOrdinal = 0;
        foreach (CrossTlLogicalPairing pairing in pairings)
        foreach (CrossTlGeometryDocument geometry in study.Geometries)
        {
            if (!Enum.TryParse(geometry.MovementMode, ignoreCase: false, out Tl1IntegratedMovementMode movementMode) ||
                !Enum.TryParse(geometry.MovementOrder, ignoreCase: false, out Tl1IntegratedMovementOrder movementOrder))
            {
                throw new InvalidOperationException($"Cross-TL geometry '{geometry.Id}' contains an unknown movement mode/order.");
            }
            variantOrdinal++;
            generated.Variants.Add(BuildVariant(
                study, pairing, geometry, movementMode, movementOrder, variantOrdinal));
        }
        if (generated.Variants.Select(variant => variant.Id).Distinct(StringComparer.Ordinal).Count() != generated.Variants.Count)
        {
            throw new InvalidOperationException("Generated cross-TL integrated variant IDs are not unique.");
        }
        return generated;
    }

    private static Tl1IntegratedShipBuildDocument ToIntegratedBuild(CrossTlResolvedBuild build) => new()
    {
        Id = build.Id,
        MainWeaponCount = build.MainWeaponCount,
        MainReactorCount = build.ReactorCount,
        ActiveSensor = build.SensorInstalled,
        ShieldGenerator = build.ShieldInstalled,
        KineticPdsCount = build.KineticPdsCount,
        PdsFamily = build.PdsFamily,
        PdsBaseChance = build.PdsBaseChance,
        PdsPowerCost = build.PdsPowerCost,
        PdsReactionCapacity = build.PdsReactionCapacity,
        PdsFallbackPowerCost = build.PdsFallbackPowerCost,
        PdsFallbackReactionCapacity = build.PdsFallbackReactionCapacity,
        PdsAmmunition = build.PdsAmmunition,
        ShieldHardener = build.ShieldHardenerInstalled,
        ShieldHardenerArmor = build.ShieldHardenerArmor,
        ShieldHardenerPowerCost = build.ShieldHardenerPowerCost,
        TacticalComputerEvasiveCompensation = build.EvasiveCompensation,
        StandardOnboardMissileNavigationSensor = build.StandardOnboardNavigationSensor,
        FtlStrategicMove = build.FtlStrategicMove,
        EcmSuite = build.EcmRatings.Count > 0,
        EcmSuiteRatings = build.EcmRatings.ToList(),
        EccmSuite = build.EccmRatings.Count > 0,
        EccmSuiteRatings = build.EccmRatings.ToList(),
        UsedSpace = build.UsedSpace,
        FreeSupportSpace = build.FreeSpace,
        AdvancedComponentCount = build.AdvancedComponentCount,
        CrossTlCompositionClass = build.CompositionClass,
    };

    private static string BuildCrossTlProfileLabel(
        CrossTlBuildPermutationDocument study,
        CrossTlLogicalPairing pairing,
        CrossTlGeometryDocument geometry)
    {
        if (IsMatchedReadinessSchema(study.SchemaVersion))
        {
            return string.Join("|", new[]
            {
                $"source={pairing.Source}",
                $"transition={pairing.ProgressionTransitionId}",
                $"expectedAdvancedDelta={pairing.ExpectedAdvancedComponentDelta}",
                $"bundle={pairing.MatchedBundleId}",
                $"orientation={pairing.Orientation}",
                $"composition={pairing.CompositionClass}",
                $"progression={pairing.ProgressionDirection}",
                $"distance={pairing.ProgressionDistance}",
                $"progressionMagnitude={pairing.ProgressionMagnitudeStratum}",
                $"spacePair={pairing.SpacePairStratum}",
                $"spaceDelta={pairing.UsedSpaceDifference}",
                $"spaceAbsDelta={pairing.AbsoluteUsedSpaceDifference}",
                $"familyPair={pairing.WeaponFamilyPair}",
                $"infoDirection={pairing.InformationControlDirection}",
                $"infoDistance={pairing.InformationControlDistance}",
                $"infoBand={pairing.InformationControlDistanceBand}",
                $"readinessA={pairing.SideAReadiness}",
                $"readinessB={pairing.SideBReadiness}",
                $"readyRangeA={pairing.SideAMaximumReadyRangeHexes}",
                $"readyRangeB={pairing.SideBMaximumReadyRangeHexes}",
                $"populationCell={pairing.PopulationCellKey}",
                $"populationCount={pairing.PopulationUnorderedDistinctCount}",
                $"populationSampleCount={pairing.PopulationSampleCount}",
                $"populationRepresentativeWeight={pairing.PopulationRepresentativeWeight.ToString("R", CultureInfo.InvariantCulture)}",
                $"secondaryKey={pairing.SecondaryCoverageKey}",
                $"geometry={geometry.Id}",
            });
        }
        if (IsGeneralizedSchema(study.SchemaVersion))
        {
            string transition = string.IsNullOrWhiteSpace(pairing.ProgressionTransitionId)
                ? "none"
                : pairing.ProgressionTransitionId;
            return $"source={pairing.Source}|transition={transition}|composition={pairing.CompositionClass}|progression={pairing.ProgressionDirection}|distance={pairing.ProgressionDistance}|stratum={pairing.ProgressionStratum}|spaceA={pairing.SideA.UsedSpace}/{pairing.SideA.InstallationSpaceCapacity}|spaceB={pairing.SideB.UsedSpace}/{pairing.SideB.InstallationSpaceCapacity}|geometry={geometry.Id}";
        }
        return $"{pairing.SideARecipe}-vs-{pairing.SideBRecipe}-{geometry.Id}";
    }

    private static Tl1IntegratedTacticalCombatVariantDocument BuildVariant(
        CrossTlBuildPermutationDocument study,
        CrossTlLogicalPairing pairing,
        CrossTlGeometryDocument geometry,
        Tl1IntegratedMovementMode movementMode,
        Tl1IntegratedMovementOrder movementOrder,
        int ordinal)
    {
        CrossTlResolvedBuild a = pairing.SideA;
        CrossTlResolvedBuild b = pairing.SideB;
        bool generalized = IsGeneralizedSchema(study.SchemaVersion);
        return new Tl1IntegratedTacticalCombatVariantDocument
        {
            Id = $"{study.VariantIdPrefix}-{ordinal:D3}-{geometry.Id}",
            ComparisonGroup = pairing.Id,
            ProfileLabel = BuildCrossTlProfileLabel(study, pairing, geometry),
            SideAEngagementReadinessClass = pairing.SideAReadiness,
            SideBEngagementReadinessClass = pairing.SideBReadiness,
            SideAMaximumReadyRangeHexes = pairing.SideAMaximumReadyRangeHexes,
            SideBMaximumReadyRangeHexes = pairing.SideBMaximumReadyRangeHexes,
            SideABuildId = generalized ? a.Id : "cross_tl_exact_fill_shell",
            SideBBuildId = generalized ? b.Id : "cross_tl_exact_fill_shell",
            SideAProfileId = RuntimeProfileIdForBuild(study, a),
            SideBProfileId = RuntimeProfileIdForBuild(study, b),
            SideAAuxiliaryProfileId = study.AuxiliaryProfileId,
            SideBAuxiliaryProfileId = study.AuxiliaryProfileId,
            SideAAiDoctrineId = study.AiDoctrineId,
            SideBAiDoctrineId = study.AiDoctrineId,
            SideAFamily = a.Family,
            SideBFamily = b.Family,
            SideASecondaryFamily = generalized && a.MainWeaponCount == 2 ? a.Family : null,
            SideBSecondaryFamily = generalized && b.MainWeaponCount == 2 ? b.Family : null,
            MovementMode = movementMode,
            InitialRangeHexes = geometry.InitialRangeHexes,
            MovementOrder = movementOrder,
            TacticalMapRadius = 5,
            StartingFuel = 100,
            MovementFuelPerHex = 2,
            EvasiveManeuverFuelCost = 1,
            ProtectedCompartmentation = false,
            DamageControl = Tl1IntegratedDamageControlMode.ComponentFirstReserveOne,
            SideAStlMovementHexes = a.StlNormalMove ?? 1,
            SideBStlMovementHexes = b.StlNormalMove ?? 1,
            BaseShieldRechargeEnabled = true,
            EvasiveManeuversEnabled = false,
            PdsEnabled = true,
            EscapeDisengagementEnabled = false,
            SideABackgroundTacticalPowerCommitment = 0,
            SideBBackgroundTacticalPowerCommitment = 0,
            SideATacticalPowerDoctrine = Tl1TacticalPowerDoctrine.FullVolleyFirst,
            SideBTacticalPowerDoctrine = Tl1TacticalPowerDoctrine.FullVolleyFirst,
            SideAReactorOutputOverride = a.ReactorOutput,
            SideBReactorOutputOverride = b.ReactorOutput,
            SideATrackPolicy = Tl1OperationalTrackPolicy.AcquisitionFirstAutoActive,
            SideBTrackPolicy = Tl1OperationalTrackPolicy.AcquisitionFirstAutoActive,
            SideANetEwRangePenalty = 0,
            SideBNetEwRangePenalty = 0,
            SideAStlOverloadPolicy = Tl1IntegratedStlOverloadPolicy.None,
            SideBStlOverloadPolicy = Tl1IntegratedStlOverloadPolicy.None,
            SideASensorOverloadPolicy = Tl1IntegratedSensorOverloadPolicy.None,
            SideBSensorOverloadPolicy = Tl1IntegratedSensorOverloadPolicy.None,
            SideAEcmPolicy = Tl1IntegratedEwPowerPolicy.Normal,
            SideBEcmPolicy = Tl1IntegratedEwPowerPolicy.Normal,
            SideAEccmPolicy = Tl1IntegratedEwPowerPolicy.ReactiveNormal,
            SideBEccmPolicy = Tl1IntegratedEwPowerPolicy.ReactiveNormal,
            SideAEcmNormalPowerCostOverride = a.EcmRatings.Count == 0 ? null : a.EcmNormalPowerCost,
            SideBEcmNormalPowerCostOverride = b.EcmRatings.Count == 0 ? null : b.EcmNormalPowerCost,
            SideAEccmNormalPowerCostOverride = a.EccmRatings.Count == 0 ? null : a.EccmNormalPowerCost,
            SideBEccmNormalPowerCostOverride = b.EccmRatings.Count == 0 ? null : b.EccmNormalPowerCost,
            SideAEcmFullStrengthNormalPowerCostOverride = a.EcmRatings.Count == 0 ? null : a.EcmFullStrengthNormalPowerCost,
            SideBEcmFullStrengthNormalPowerCostOverride = b.EcmRatings.Count == 0 ? null : b.EcmFullStrengthNormalPowerCost,
            SideAEccmFullStrengthNormalPowerCostOverride = a.EccmRatings.Count == 0 ? null : a.EccmFullStrengthNormalPowerCost,
            SideBEccmFullStrengthNormalPowerCostOverride = b.EccmRatings.Count == 0 ? null : b.EccmFullStrengthNormalPowerCost,
            SideAEcmNormalRatingOverride = a.EcmRatings.Count == 0 ? null : a.EcmRatings.Max(),
            SideBEcmNormalRatingOverride = b.EcmRatings.Count == 0 ? null : b.EcmRatings.Max(),
            SideAEccmNormalRatingOverride = a.EccmRatings.Count == 0 ? null : a.EccmRatings.Max(),
            SideBEccmNormalRatingOverride = b.EccmRatings.Count == 0 ? null : b.EccmRatings.Max(),
            SideAAllowsApproximateDirectFire = false,
            SideBAllowsApproximateDirectFire = false,
            SideAApproximateDirectFireAccuracyPenalty = 0,
            SideBApproximateDirectFireAccuracyPenalty = 0,
            SideASensorEwProfileId = a.SensorEwProfileId,
            SideBSensorEwProfileId = b.SensorEwProfileId,
            SideATacticalComputerTargetingBonusOverride = a.TargetingBonus,
            SideBTacticalComputerTargetingBonusOverride = b.TargetingBonus,
            SideAShieldCapacityOverride = a.ShieldCapacity,
            SideBShieldCapacityOverride = b.ShieldCapacity,
            SideAPrimaryArmorProtectionOverride = a.ArmorProtection,
            SideAPrimaryArmorIntegrityOverride = a.ArmorIntegrity,
            SideBPrimaryArmorProtectionOverride = b.ArmorProtection,
            SideBPrimaryArmorIntegrityOverride = b.ArmorIntegrity,
            SideAWeaponShieldPenetrationOverride = a.ShieldPenetration,
            SideAWeaponArmorPenetrationOverride = a.ArmorPenetration,
            SideBWeaponShieldPenetrationOverride = b.ShieldPenetration,
            SideBWeaponArmorPenetrationOverride = b.ArmorPenetration,
            SideAPrimaryWeaponDamageOverride = a.PreferredSmokeModeDamage ?? a.WeaponDamage,
            SideBPrimaryWeaponDamageOverride = b.PreferredSmokeModeDamage ?? b.WeaponDamage,
            SideAPrimaryWeaponPowerCostOverride = a.PreferredSmokeModePowerCost ?? a.WeaponPowerCost,
            SideBPrimaryWeaponPowerCostOverride = b.PreferredSmokeModePowerCost ?? b.WeaponPowerCost,
            SideAPrimaryWeaponAccuracyBonusOverride = a.PreferredSmokeModeAccuracyBonus ?? a.WeaponAccuracyBonus,
            SideBPrimaryWeaponAccuracyBonusOverride = b.PreferredSmokeModeAccuracyBonus ?? b.WeaponAccuracyBonus,
            SideASensorPassiveFirmRangeOverride = a.SensorPassiveFirmRange,
            SideASensorPassiveApproximateRangeOverride = a.SensorPassiveApproximateRange,
            SideASensorActiveLowFirmRangeOverride = a.SensorActiveLowFirmRange,
            SideASensorActiveLowApproximateRangeOverride = a.SensorActiveLowApproximateRange,
            SideASensorActiveLowPowerCostOverride = a.SensorActiveLowPowerCost,
            SideASensorActiveHighFirmRangeOverride = a.SensorActiveHighFirmRange,
            SideASensorActiveHighApproximateRangeOverride = a.SensorActiveHighApproximateRange,
            SideASensorActiveHighPowerCostOverride = a.SensorActiveHighPowerCost,
            SideBSensorPassiveFirmRangeOverride = b.SensorPassiveFirmRange,
            SideBSensorPassiveApproximateRangeOverride = b.SensorPassiveApproximateRange,
            SideBSensorActiveLowFirmRangeOverride = b.SensorActiveLowFirmRange,
            SideBSensorActiveLowApproximateRangeOverride = b.SensorActiveLowApproximateRange,
            SideBSensorActiveLowPowerCostOverride = b.SensorActiveLowPowerCost,
            SideBSensorActiveHighFirmRangeOverride = b.SensorActiveHighFirmRange,
            SideBSensorActiveHighApproximateRangeOverride = b.SensorActiveHighApproximateRange,
            SideBSensorActiveHighPowerCostOverride = b.SensorActiveHighPowerCost,
            SideAMissileSpeedHexesPerTurnOverride = a.Family == WeaponFamily.Missile ? a.MissileMove : null,
            SideBMissileSpeedHexesPerTurnOverride = b.Family == WeaponFamily.Missile ? b.MissileMove : null,
        };
    }

    private static string RuntimeProfileIdForBuild(
        CrossTlBuildPermutationDocument study,
        CrossTlResolvedBuild build)
    {
        if (!string.Equals(study.SchemaVersion, SchemaVersionV7, StringComparison.Ordinal))
        {
            return study.BaselineProfileId;
        }
        return build.MaxTechnologyLevel >= 3 ? "tl3-cp102-executable-candidate" : "tl2-cp102-integration-reference";
    }

    private static string CrossTlProfileLabelValue(string? label, string key)
    {
        if (string.IsNullOrWhiteSpace(label)) return string.Empty;
        string prefix = key + "=";
        foreach (string segment in label.Split('|', StringSplitOptions.RemoveEmptyEntries))
        {
            if (segment.StartsWith(prefix, StringComparison.Ordinal))
            {
                return segment[prefix.Length..];
            }
        }
        return string.Empty;
    }

    private static IReadOnlyList<CrossTlFoundationGate> BuildFoundationGates(
        CrossTlBuildPermutationDocument study,
        CrossTlEnumerationResult enumeration,
        IReadOnlyList<CrossTlLogicalPairing> pairings,
        IReadOnlyList<CrossTlProgressionEdge> progressionEdges,
        Tl1IntegratedTacticalCombatStudyDocument generated)
    {
        long unorderedWithSelf = ((long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count + 1L)) / 2L;
        long oriented = (long)enumeration.LegalBuilds.Count * enumeration.LegalBuilds.Count;
        int exactFill = enumeration.LegalBuilds.Count(build => build.UsedSpace == build.InstallationSpaceCapacity);
        int nearFill = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "near_fill");
        int underfilled = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "underfilled");
        long unorderedDistinct = checked((long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count - 1L) / 2L);
        long orientedDistinct = checked((long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count - 1L));
        int oneWeapon = enumeration.LegalBuilds.Count(build => build.MainWeaponCount == 1);
        int twoWeapon = enumeration.LegalBuilds.Count(build => build.MainWeaponCount == 2);
        int oneReactor = enumeration.LegalBuilds.Count(build => build.ReactorCount == 1);
        int twoReactor = enumeration.LegalBuilds.Count(build => build.ReactorCount == 2);
        int duplicateEcm = enumeration.LegalBuilds.Count(build => build.EcmRatings.Count == 2);
        int duplicateEccm = enumeration.LegalBuilds.Count(build => build.EccmRatings.Count == 2);
        bool generalized = IsGeneralizedSchema(study.SchemaVersion);
        var gates = new List<CrossTlFoundationGate>
        {
            new("legal-build-count", enumeration.LegalBuilds.Count == study.ExpectedLegalBuildCount,
                $"Expected {study.ExpectedLegalBuildCount}; observed {enumeration.LegalBuilds.Count}."),
            new("all-legal-builds-space-valid", enumeration.LegalBuilds.All(build =>
                build.UsedSpace <= build.InstallationSpaceCapacity && build.FreeSpace >= 0),
                "Every enumerated build must satisfy its selected Hull Installation Space envelope."),
            new("mandatory-combat-core", enumeration.LegalBuilds.All(build =>
                build.MainWeaponCount >= 1 && build.ReactorCount >= 1 &&
                (study.ConstructionGuardrails?.MinimumSensorCount ?? 0) <= (build.SensorInstalled ? 1 : 0)),
                "Every legal combat build must satisfy the required Main Weapon, Reactor, and Sensor construction core; optional duplication remains an explicit design choice."),
            new("power-overcommit-not-legality-filter", true,
                "Enumeration legality is based on Installation Space/current explicit constraints; simultaneous Tactical Power demand is not used as a construction rejection criterion."),
            new("named-recipe-count", enumeration.NamedBuilds.Count == study.ExpectedNamedRecipeCount,
                $"Expected {study.ExpectedNamedRecipeCount}; observed {enumeration.NamedBuilds.Count}."),
            new("logical-pairing-count", pairings.Count == study.ExpectedLogicalPairingCount,
                $"Expected {study.ExpectedLogicalPairingCount}; observed {pairings.Count}."),
            new("generated-variant-count", generated.Variants.Count == study.ExpectedGeneratedVariantCount,
                $"Expected {study.ExpectedGeneratedVariantCount}; observed {generated.Variants.Count}."),
            new("generated-geometry-binding", study.Geometries.All(geometry =>
            {
                if (!Enum.TryParse(geometry.MovementMode, ignoreCase: false, out Tl1IntegratedMovementMode mode) ||
                    !Enum.TryParse(geometry.MovementOrder, ignoreCase: false, out Tl1IntegratedMovementOrder order))
                {
                    return false;
                }
                Tl1IntegratedTacticalCombatVariantDocument[] variants = generated.Variants.Where(v =>
                    string.Equals(CrossTlProfileLabelValue(v.ProfileLabel, "geometry"), geometry.Id, StringComparison.Ordinal)).ToArray();
                return variants.Length == pairings.Count && variants.All(v =>
                    v.MovementMode == mode && v.MovementOrder == order &&
                    v.InitialRangeHexes == geometry.InitialRangeHexes);
            }),
                "Every generated geometry must bind exactly to the movement mode/order/range declared by the foundation study."),
        };
        if (generalized)
        {
            gates.Add(new("raw-combination-count", enumeration.RawCombinationCount == study.ExpectedRawCombinationCount,
                $"Expected {study.ExpectedRawCombinationCount}; observed {enumeration.RawCombinationCount}."));
            gates.Add(new("exact-fill-build-count", exactFill == study.ExpectedExactFillBuildCount,
                $"Expected {study.ExpectedExactFillBuildCount}; observed {exactFill}."));
            gates.Add(new("cross-tl-envelope-accounted", oriented == study.ExpectedOrientedPairingEnvelope && unorderedWithSelf == study.ExpectedUnorderedWithSelfPairingEnvelope,
                $"Expected {study.ExpectedOrientedPairingEnvelope} oriented / {study.ExpectedUnorderedWithSelfPairingEnvelope} unordered-with-self; observed {oriented} / {unorderedWithSelf}."));
            bool requireEnvelopeCoverage = !string.Equals(study.SchemaVersion, SchemaVersionV7, StringComparison.Ordinal) ||
                string.Equals(study.CoverageMode, "construction_envelope", StringComparison.Ordinal);
            if (requireEnvelopeCoverage)
            {
                gates.Add(new("optional-main-weapon-duplication-represented", oneWeapon > 0 && twoWeapon > 0,
                    $"Legal envelope contains {oneWeapon} one-main and {twoWeapon} two-main builds."));
                gates.Add(new("optional-reactor-duplication-represented", oneReactor > 0 && twoReactor > 0,
                    $"Legal envelope contains {oneReactor} one-reactor and {twoReactor} two-reactor builds."));
                gates.Add(new("redundant-ew-represented", duplicateEcm > 0 && duplicateEccm > 0,
                    $"Legal envelope contains {duplicateEcm} duplicate-ECM and {duplicateEccm} duplicate-ECCM builds."));
            }
            gates.Add(new("space-excludes-two-main-two-reactor-core", enumeration.LegalBuilds.All(build => !(build.MainWeaponCount == 2 && build.ReactorCount == 2)),
                string.Equals(study.SchemaVersion, SchemaVersionV7, StringComparison.Ordinal)
                    ? "No legal TL2/TL3 base build may fit both two full Main Weapons and two full Main Reactors in the current 35/36-Space envelopes."
                    : "No legal 35-Space build may fit both two full Main Weapons and two full Main Reactors in the current footprint envelope."));
            gates.Add(new("non-additive-ew-effective-ratings", enumeration.LegalBuilds.All(build =>
                (build.EcmRatings.Count == 0 || build.EcmRatings.Max() <= 2) &&
                (build.EccmRatings.Count == 0 || build.EccmRatings.Max() <= 2)),
                "Redundant ECM/ECCM installations retain the highest installed rating rather than summing same-type ratings."));
            if (string.Equals(study.SchemaVersion, SchemaVersionV7, StringComparison.Ordinal) &&
                string.Equals(study.CoverageMode, "transition_smoke", StringComparison.Ordinal))
            {
                string[] declaredTransitions = study.ProgressionLattice?.Transitions.Select(t => t.Id)
                    .OrderBy(id => id, StringComparer.Ordinal).ToArray() ?? Array.Empty<string>();
                string[] pairedTransitions = pairings.Where(pair => pair.Source == "named" && !string.IsNullOrWhiteSpace(pair.ProgressionTransitionId))
                    .Select(pair => pair.ProgressionTransitionId).Distinct(StringComparer.Ordinal)
                    .OrderBy(id => id, StringComparer.Ordinal).ToArray();
                gates.Add(new("v7-transition-smoke-covers-declared-transitions",
                    declaredTransitions.Length > 0 && declaredTransitions.SequenceEqual(pairedTransitions, StringComparer.Ordinal),
                    $"Named transition smoke covers {pairedTransitions.Length} of {declaredTransitions.Length} declared v7 progression transitions."));
            }
            CrossTlStratifiedPairingSelectionDocument selection = study.StratifiedPairingSelection ?? new();
            if (study.ExactEdgePairingSelection?.Enabled == true)
            {
                CrossTlExactEdgePairingSelectionDocument exactSelection = study.ExactEdgePairingSelection ??
                    throw new InvalidOperationException("Exact-edge pairing selection is missing during gate construction.");
                IReadOnlyList<CrossTlLogicalPairing> exactPairs = pairings
                    .Where(pair => pair.Source == "exact_progression_edge").ToArray();
                gates.Add(new("mandatory-sensor-installed", enumeration.LegalBuilds.All(build => build.SensorInstalled),
                    "Every ordinary legal CP99 combat build must include an installed Sensor; sensorless states remain diagnostic/runtime damage cases outside this construction population."));
                gates.Add(new("space-utilization-build-counts",
                    nearFill == study.ExpectedNearFillBuildCount && underfilled == study.ExpectedUnderfilledBuildCount,
                    $"Expected exact/near/underfilled {study.ExpectedExactFillBuildCount}/{study.ExpectedNearFillBuildCount}/{study.ExpectedUnderfilledBuildCount}; observed {exactFill}/{nearFill}/{underfilled}."));
                gates.Add(new("distinct-pair-envelope-accounted",
                    unorderedDistinct == study.ExpectedUnorderedDistinctPairingEnvelope &&
                    orientedDistinct == study.ExpectedOrientedDistinctPairingEnvelope,
                    $"Expected {study.ExpectedUnorderedDistinctPairingEnvelope} unordered-distinct / {study.ExpectedOrientedDistinctPairingEnvelope} oriented-distinct; observed {unorderedDistinct} / {orientedDistinct}."));
                gates.Add(new("exact-edge-sample-count", exactPairs.Count == exactSelection.ExpectedLogicalPairingCount,
                    $"Expected {exactSelection.ExpectedLogicalPairingCount} exact-edge logical pairs; observed {exactPairs.Count}."));
                int observedStrata = exactPairs.Select(pair => string.Join("|", new[]
                    { pair.ProgressionTransitionId, pair.SideA.Family.ToString(), pair.SideA.CompositionClass, pair.SideA.SpaceUtilizationClass }))
                    .Distinct(StringComparer.Ordinal).Count();
                bool exactCellsComplete = observedStrata == exactSelection.ExpectedStratumCount &&
                    exactPairs.GroupBy(pair => string.Join("|", new[]
                    { pair.ProgressionTransitionId, pair.SideA.Family.ToString(), pair.SideA.CompositionClass, pair.SideA.SpaceUtilizationClass }), StringComparer.Ordinal)
                    .All(group => group.Count() == exactSelection.RepresentativesPerStratum);
                gates.Add(new("exact-edge-stratum-coverage", exactCellsComplete,
                    $"Expected {exactSelection.ExpectedStratumCount} populated exact-edge strata with {exactSelection.RepresentativesPerStratum} representatives each; observed {observedStrata} strata."));
                gates.Add(new("exact-edge-one-axis-and-space-preserved", exactPairs.All(pair =>
                    pair.SideA.UsedSpace == pair.SideB.UsedSpace &&
                    pair.SideB.AdvancedComponentCount - pair.SideA.AdvancedComponentCount == pair.ExpectedAdvancedComponentDelta &&
                    pair.ExpectedAdvancedComponentDelta is 1 or 2),
                    "Every exact-edge comparison must preserve Installation Space and advance exactly the declared one construction axis; duplicated installations may advance two physical components together."));
                gates.Add(new("readiness-classification-complete", exactPairs.All(pair =>
                    pair.SideAReadiness is "reference_ready" or "closing_ready" or "engagement_denied" &&
                    pair.SideBReadiness is "reference_ready" or "closing_ready" or "engagement_denied"),
                    "Every exact-edge comparison must carry side-specific engagement-readiness classification without invoking broad population weighting."));
            }
            else if (IsAdaptiveSamplingSchema(study.SchemaVersion))
            {
                IReadOnlyList<CrossTlLogicalPairing> statistical = pairings
                    .Where(pair => pair.Source == "statistical").ToArray();
                IReadOnlyList<CrossTlLogicalPairing> diversity = pairings
                    .Where(pair => pair.Source == "diversity").ToArray();
                IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells =
                    BuildPopulationCells(study, enumeration.LegalBuilds);
                IReadOnlyDictionary<string, int> quotas = AllocateAdaptiveCellQuotas(populationCells, selection);

                gates.Add(new("adaptive-statistical-sample-count", statistical.Count == selection.ExpectedSampleCount,
                    $"Expected {selection.ExpectedSampleCount} statistical orientations; observed {statistical.Count}."));
                gates.Add(new("adaptive-diversity-sample-count", diversity.Count == selection.ExpectedDiversitySampleCount,
                    $"Expected {selection.ExpectedDiversitySampleCount} diversity orientations; observed {diversity.Count}."));

                bool MirroredBundles(IReadOnlyList<CrossTlLogicalPairing> sample, int expectedBasePairs) =>
                    sample.GroupBy(pair => pair.MatchedBundleId, StringComparer.Ordinal).Count() == expectedBasePairs &&
                    sample.GroupBy(pair => pair.MatchedBundleId, StringComparer.Ordinal).All(group =>
                    {
                        CrossTlLogicalPairing[] bundle = group.ToArray();
                        return bundle.Length == 2 &&
                            bundle.Select(pair => pair.Orientation).OrderBy(value => value, StringComparer.Ordinal)
                                .SequenceEqual(new[] { "forward", "reverse" }, StringComparer.Ordinal) &&
                            bundle[0].SideA.Id == bundle[1].SideB.Id &&
                            bundle[0].SideB.Id == bundle[1].SideA.Id &&
                            bundle[0].SideAReadiness == bundle[1].SideBReadiness &&
                            bundle[0].SideBReadiness == bundle[1].SideAReadiness &&
                            bundle[0].SideAMaximumReadyRangeHexes == bundle[1].SideBMaximumReadyRangeHexes &&
                            bundle[0].SideBMaximumReadyRangeHexes == bundle[1].SideAMaximumReadyRangeHexes &&
                            bundle[0].PopulationCellKey == bundle[1].PopulationCellKey &&
                            bundle[0].PopulationUnorderedDistinctCount == bundle[1].PopulationUnorderedDistinctCount &&
                            Math.Abs(bundle[0].PopulationRepresentativeWeight - bundle[1].PopulationRepresentativeWeight) < 0.000001;
                    });
                gates.Add(new("adaptive-statistical-mirrored-bundles",
                    MirroredBundles(statistical, selection.ExpectedBasePairCount),
                    $"Expected {selection.ExpectedBasePairCount} statistical unordered base pairs, each emitted in forward and reverse orientations."));
                gates.Add(new("adaptive-diversity-mirrored-bundles",
                    MirroredBundles(diversity, selection.ExpectedDiversityBasePairCount),
                    $"Expected {selection.ExpectedDiversityBasePairCount} diagnostic diversity base pairs, each emitted in forward and reverse orientations."));

                var statisticalForwardCounts = statistical.Where(pair => pair.Orientation == "forward")
                    .GroupBy(pair => pair.PopulationCellKey, StringComparer.Ordinal)
                    .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);
                bool quotaCoverage = quotas.All(pair => statisticalForwardCounts.GetValueOrDefault(pair.Key) == pair.Value) &&
                    statisticalForwardCounts.Count == quotas.Count;
                gates.Add(new("adaptive-population-cell-quota-coverage", quotaCoverage,
                    $"The statistical sample must allocate exactly {selection.ExpectedBasePairCount} unordered base pairs across all {quotas.Count} population cells according to deterministic adaptive quotas."));

                bool statisticalWeightsValid = statistical.All(pair =>
                {
                    if (!quotas.TryGetValue(pair.PopulationCellKey, out int quota) || quota <= 0) return false;
                    if (pair.PopulationSampleCount != quota || pair.PopulationUnorderedDistinctCount <= 0) return false;
                    double expectedWeight = (double)pair.PopulationUnorderedDistinctCount / quota;
                    return Math.Abs(pair.PopulationRepresentativeWeight - expectedWeight) <= 0.000001 * Math.Max(1.0, expectedWeight);
                });
                double representedPopulation = statistical.Where(pair => pair.Orientation == "forward")
                    .Sum(pair => pair.PopulationRepresentativeWeight);
                long totalPopulation = populationCells.Values.Sum(cell => cell.PopulationUnorderedDistinctCount);
                gates.Add(new("adaptive-statistical-population-weight-splitting", statisticalWeightsValid &&
                    Math.Abs(representedPopulation - totalPopulation) <= 0.001,
                    $"Statistical samples must split each cell's unordered-distinct population weight among its allocated representatives; represented {representedPopulation:R} of {totalPopulation}."));
                gates.Add(new("diversity-overlay-zero-inference-weight", diversity.All(pair =>
                    pair.PopulationSampleCount == 0 && Math.Abs(pair.PopulationRepresentativeWeight) <= 0.000001),
                    "Diagnostic diversity-overlay pairs must carry zero population-inference weight."));

                string[] topCells = populationCells.Values
                    .OrderByDescending(cell => cell.PopulationUnorderedDistinctCount)
                    .ThenBy(cell => cell.Key, StringComparer.Ordinal)
                    .Take(selection.DiversityOverlayTopCellCount)
                    .Select(cell => cell.Key).ToArray();
                var topCellSet = new HashSet<string>(topCells, StringComparer.Ordinal);
                var diversityForwardCounts = diversity.Where(pair => pair.Orientation == "forward")
                    .GroupBy(pair => pair.PopulationCellKey, StringComparer.Ordinal)
                    .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);
                bool diversityCoverage = diversityForwardCounts.Count == topCells.Length && topCells.All(cell =>
                    diversityForwardCounts.GetValueOrDefault(cell) == selection.DiversityOverlayPairsPerCell) &&
                    diversity.All(pair => topCellSet.Contains(pair.PopulationCellKey));
                gates.Add(new("secondary-diversity-overlay-coverage", diversityCoverage,
                    $"The diversity overlay must add exactly {selection.DiversityOverlayPairsPerCell} unordered diagnostic pairs to each of the {selection.DiversityOverlayTopCellCount} highest-population cells."));

                bool readinessComplete = statistical.Concat(diversity).All(pair =>
                {
                    static bool Valid(string readiness, int readyRange) => readiness switch
                    {
                        "reference_ready" => readyRange == 3,
                        "closing_ready" => readyRange is >= 0 and <= 2,
                        "engagement_denied" => readyRange == -1,
                        _ => false,
                    };
                    return Valid(pair.SideAReadiness, pair.SideAMaximumReadyRangeHexes) &&
                        Valid(pair.SideBReadiness, pair.SideBMaximumReadyRangeHexes);
                });
                gates.Add(new("ready-range-classification-complete", readinessComplete,
                    "Every statistical/diversity orientation must carry a readiness class consistent with its exact maximum Firm-and-physical-weapon ready range."));
                gates.Add(new("secondary-coverage-key-complete", statistical.Concat(diversity).All(pair =>
                    !string.IsNullOrWhiteSpace(pair.SecondaryCoverageKey) &&
                    !string.IsNullOrWhiteSpace(pair.InformationControlDistanceBand)),
                    "Every statistical/diversity orientation must expose weapon-family/information-control secondary-coverage metadata."));
                gates.Add(new("space-utilization-build-counts",
                    nearFill == study.ExpectedNearFillBuildCount && underfilled == study.ExpectedUnderfilledBuildCount,
                    $"Expected exact/near/underfilled {study.ExpectedExactFillBuildCount}/{study.ExpectedNearFillBuildCount}/{study.ExpectedUnderfilledBuildCount}; observed {exactFill}/{nearFill}/{underfilled}."));
                gates.Add(new("distinct-pair-envelope-accounted",
                    unorderedDistinct == study.ExpectedUnorderedDistinctPairingEnvelope &&
                    orientedDistinct == study.ExpectedOrientedDistinctPairingEnvelope,
                    $"Expected {study.ExpectedUnorderedDistinctPairingEnvelope} unordered-distinct / {study.ExpectedOrientedDistinctPairingEnvelope} oriented-distinct; observed {unorderedDistinct} / {orientedDistinct}."));
            }
            else
            {
                IReadOnlyList<CrossTlLogicalPairing> sampled = pairings.Where(pair => pair.Source == "stratified").ToArray();
                gates.Add(new("stratified-sample-count", sampled.Count == selection.ExpectedSampleCount,
                    $"Expected {selection.ExpectedSampleCount}; observed {sampled.Count}."));
                if (IsMatchedReadinessSchema(study.SchemaVersion))
                {
                    gates.Add(new("space-utilization-build-counts",
                        nearFill == study.ExpectedNearFillBuildCount && underfilled == study.ExpectedUnderfilledBuildCount,
                        $"Expected exact/near/underfilled {study.ExpectedExactFillBuildCount}/{study.ExpectedNearFillBuildCount}/{study.ExpectedUnderfilledBuildCount}; observed {exactFill}/{nearFill}/{underfilled}."));
                    gates.Add(new("distinct-pair-envelope-accounted",
                        unorderedDistinct == study.ExpectedUnorderedDistinctPairingEnvelope &&
                        orientedDistinct == study.ExpectedOrientedDistinctPairingEnvelope,
                        $"Expected {study.ExpectedUnorderedDistinctPairingEnvelope} unordered-distinct / {study.ExpectedOrientedDistinctPairingEnvelope} oriented-distinct; observed {unorderedDistinct} / {orientedDistinct}."));
                    CrossTlLogicalPairing[][] bundles = sampled.GroupBy(pair => pair.MatchedBundleId, StringComparer.Ordinal)
                        .Select(group => group.ToArray()).ToArray();
                    bool mirroredBundles = bundles.Length == selection.ExpectedBasePairCount && bundles.All(bundle =>
                        bundle.Length == 2 &&
                        bundle.Select(pair => pair.Orientation).OrderBy(value => value, StringComparer.Ordinal)
                            .SequenceEqual(new[] { "forward", "reverse" }, StringComparer.Ordinal) &&
                        bundle[0].SideA.Id == bundle[1].SideB.Id &&
                        bundle[0].SideB.Id == bundle[1].SideA.Id &&
                        bundle[0].SideAReadiness == bundle[1].SideBReadiness &&
                        bundle[0].SideBReadiness == bundle[1].SideAReadiness &&
                        bundle[0].CompositionClass == bundle[1].CompositionClass &&
                        bundle[0].ProgressionMagnitudeStratum == bundle[1].ProgressionMagnitudeStratum &&
                        bundle[0].SpacePairStratum == bundle[1].SpacePairStratum &&
                        bundle[0].PopulationCellKey == bundle[1].PopulationCellKey &&
                        bundle[0].PopulationUnorderedDistinctCount == bundle[1].PopulationUnorderedDistinctCount);
                    gates.Add(new("matched-bidirectional-pairing", mirroredBundles,
                        $"Expected {selection.ExpectedBasePairCount} deterministic unordered base pairs, each emitted in forward and reverse orientations."));
                    bool cellsComplete = selection.CompositionClasses.All(composition =>
                        selection.ProgressionMagnitudeStrata.All(progression =>
                            selection.SpacePairStrata.All(space => sampled
                                .Where(pair => pair.Orientation == "forward")
                                .Count(pair => pair.CompositionClass == composition &&
                                    pair.ProgressionMagnitudeStratum == progression &&
                                    pair.SpacePairStratum == space) == selection.TargetPerCell)));
                    gates.Add(new("stratified-sample-cell-coverage", cellsComplete,
                        $"Every composition/progression-magnitude/Space stratum must contain exactly {selection.TargetPerCell} deterministic unordered base pair before mirroring."));
                    gates.Add(new("population-weight-coverage", sampled.All(pair =>
                        pair.PopulationUnorderedDistinctCount > 0 && !string.IsNullOrWhiteSpace(pair.PopulationCellKey)),
                        "Every matched screening pair must carry a nonzero legal unordered-distinct population count and stable population-cell key."));
                    gates.Add(new("readiness-classification-complete", sampled.All(pair =>
                        pair.SideAReadiness is "reference_ready" or "closing_ready" or "engagement_denied" &&
                        pair.SideBReadiness is "reference_ready" or "closing_ready" or "engagement_denied"),
                        "Every matched screening orientation must classify both sides independently as reference-ready, closing-ready, or engagement-denied."));
                }
                else
                {
                    bool cellsComplete = selection.CompositionClasses.All(composition =>
                        selection.ProgressionStrata.All(stratum => sampled.Count(pair =>
                            pair.CompositionClass == composition && pair.ProgressionStratum == stratum) == selection.TargetPerCell));
                    gates.Add(new("stratified-sample-cell-coverage", cellsComplete,
                        $"Every composition/progression-distance stratum must contain exactly {selection.TargetPerCell} deterministic ordered pairings."));
                }
            }
            gates.Add(new("generated-physical-builds-match-referenced-builds",
                generated.Builds.Select(build => build.Id).OrderBy(id => id, StringComparer.Ordinal).SequenceEqual(
                    pairings.SelectMany(pair => new[] { pair.SideA.Id, pair.SideB.Id }).Distinct(StringComparer.Ordinal).OrderBy(id => id, StringComparer.Ordinal)),
                "Generated integrated study must carry the actual physical build document for every referenced legal build."));
            if (IsMatchedReadinessSchema(study.SchemaVersion))
            {
                bool runtimeReadinessMetadata = generated.Variants.All(variant =>
                    !string.IsNullOrWhiteSpace(variant.SideAEngagementReadinessClass) &&
                    !string.IsNullOrWhiteSpace(variant.SideBEngagementReadinessClass) &&
                    variant.SideAMaximumReadyRangeHexes.HasValue &&
                    variant.SideBMaximumReadyRangeHexes.HasValue);
                gates.Add(new("generated-runtime-readiness-metadata-complete", runtimeReadinessMetadata,
                    "Every generated matched-readiness runtime variant must carry explicit side-specific readiness class and maximum ready-range metadata; runtime firing-window telemetry must not depend on parsing profile labels."));
            }
        }
        else
        {
            gates.Add(new("cross-tl-envelope-accounted", oriented == 262144L && unorderedWithSelf == 131328L,
                $"Expected 262144 oriented / 131328 unordered-with-self potential pairings; observed {oriented} / {unorderedWithSelf}."));
        }
        if (study.ProgressionLattice is { Enabled: true } lattice)
        {
            gates.Add(new("progression-lattice-total-edge-count",
                progressionEdges.Count == lattice.ExpectedTotalLegalEdgeCount,
                $"Expected {lattice.ExpectedTotalLegalEdgeCount} legal single-axis progression edges; observed {progressionEdges.Count}."));
            foreach (CrossTlProgressionTransitionDocument transition in lattice.Transitions)
            {
                int count = progressionEdges.Count(edge => edge.TransitionId == transition.Id);
                int transitionExactFill = progressionEdges.Count(edge => edge.TransitionId == transition.Id &&
                    edge.LowerUsedSpace == edge.LowerInstallationSpaceCapacity &&
                    edge.HigherUsedSpace == edge.HigherInstallationSpaceCapacity);
                bool deltasMatch = progressionEdges.Where(edge => edge.TransitionId == transition.Id)
                    .All(edge => edge.ExpectedAdvancedComponentDelta == transition.ExpectedAdvancedComponentDelta);
                gates.Add(new($"progression-lattice-{transition.Id}",
                    count == transition.ExpectedLegalEdgeCount && transitionExactFill == transition.ExpectedExactFillEdgeCount && deltasMatch,
                    $"Expected {transition.ExpectedLegalEdgeCount} legal / {transition.ExpectedExactFillEdgeCount} exact-fill edges with advanced-component delta {transition.ExpectedAdvancedComponentDelta}; observed {count} / {transitionExactFill}."));
            }
        }
        return gates;
    }

    private static void WriteExactEdgePairingPlan(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlLogicalPairing> pairings,
        string outputDirectory)
    {
        if (study.ExactEdgePairingSelection?.Enabled != true) return;
        var lines = new List<string>
        {
            "pairing_id,transition_id,expected_advanced_component_delta,weapon_family,composition_class,space_utilization_class,lower_build_id,higher_build_id,used_space,lower_advanced_components,higher_advanced_components,lower_readiness,higher_readiness,lower_ready_range,higher_ready_range"
        };
        foreach (CrossTlLogicalPairing pair in pairings.OrderBy(pair => pair.Id, StringComparer.Ordinal))
        {
            lines.Add(string.Join(',', new[]
            {
                Csv(pair.Id), Csv(pair.ProgressionTransitionId), I(pair.ExpectedAdvancedComponentDelta),
                pair.SideA.Family.ToString(), Csv(pair.SideA.CompositionClass), Csv(pair.SideA.SpaceUtilizationClass),
                Csv(pair.SideA.Id), Csv(pair.SideB.Id), I(pair.SideA.UsedSpace),
                I(pair.SideA.AdvancedComponentCount), I(pair.SideB.AdvancedComponentCount),
                Csv(pair.SideAReadiness), Csv(pair.SideBReadiness),
                I(pair.SideAMaximumReadyRangeHexes), I(pair.SideBMaximumReadyRangeHexes),
            }));
        }
        File.WriteAllLines(Path.Combine(outputDirectory, "exact-edge-pairing-plan.csv"), lines, new UTF8Encoding(false));
    }

    private static void WriteProgressionLatticeSummary(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlProgressionEdge> edges,
        string outputDirectory)
    {
        if (study.ProgressionLattice is not { Enabled: true } lattice) return;
        var summary = new
        {
            enabled = true,
            expectedTotalLegalEdgeCount = lattice.ExpectedTotalLegalEdgeCount,
            observedTotalLegalEdgeCount = edges.Count,
            requireSameInstallationSpace = lattice.RequireSameInstallationSpace,
            transitions = lattice.Transitions.Select(transition => new
            {
                id = transition.Id,
                axisId = transition.AxisId,
                fromOptionId = transition.FromOptionId,
                toOptionId = transition.ToOptionId,
                kind = transition.Kind,
                expectedInstallationSpaceDelta = transition.ExpectedInstallationSpaceDelta,
                expectedCapacityDelta = transition.ExpectedCapacityDelta,
                expectedLegalEdgeCount = transition.ExpectedLegalEdgeCount,
                observedLegalEdgeCount = edges.Count(edge => edge.TransitionId == transition.Id),
                expectedExactFillEdgeCount = transition.ExpectedExactFillEdgeCount,
                observedExactFillEdgeCount = edges.Count(edge => edge.TransitionId == transition.Id &&
                    edge.LowerUsedSpace == edge.LowerInstallationSpaceCapacity &&
                    edge.HigherUsedSpace == edge.HigherInstallationSpaceCapacity),
            }).ToArray(),
        };
        File.WriteAllText(
            Path.Combine(outputDirectory, "progression-lattice-summary.json"),
            JsonSerializer.Serialize(summary, OutputJsonOptions()) + Environment.NewLine,
            new UTF8Encoding(false));
    }

    private static void WriteProgressionLatticeEdges(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlProgressionEdge> edges,
        string outputDirectory)
    {
        if (study.ProgressionLattice is not { Enabled: true }) return;
        using var writer = new StreamWriter(
            Path.Combine(outputDirectory, "progression-lattice-edges.csv"),
            false, new UTF8Encoding(false));
        writer.WriteLine(
            "transition_id,axis_id,from_option_id,to_option_id,kind,expected_installed_space_delta,expected_capacity_delta,lower_build_id,higher_build_id,lower_used_space,higher_used_space,lower_capacity,higher_capacity,lower_advanced_components,higher_advanced_components,weapon_family,composition_class,space_utilization_class");
        foreach (CrossTlProgressionEdge edge in edges.OrderBy(edge => edge.TransitionId, StringComparer.Ordinal)
            .ThenBy(edge => edge.LowerBuildId, StringComparer.Ordinal))
        {
            writer.WriteLine(string.Join(",", new[]
            {
                Csv(edge.TransitionId), Csv(edge.AxisId), Csv(edge.FromOptionId), Csv(edge.ToOptionId),
                Csv(edge.Kind), I(edge.ExpectedInstallationSpaceDelta), I(edge.ExpectedCapacityDelta),
                Csv(edge.LowerBuildId), Csv(edge.HigherBuildId), I(edge.LowerUsedSpace), I(edge.HigherUsedSpace),
                I(edge.LowerInstallationSpaceCapacity), I(edge.HigherInstallationSpaceCapacity), I(edge.LowerAdvancedComponentCount), I(edge.HigherAdvancedComponentCount),
                Csv(edge.WeaponFamily.ToString()), Csv(edge.CompositionClass), Csv(edge.SpaceUtilizationClass),
            }));
        }
    }

    private static void WriteLegalBuilds(
        CrossTlBuildPermutationDocument study,
        IReadOnlyList<CrossTlResolvedBuild> builds,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "buildId,usedSpace,freeSpace,installationSpaceCapacity,maxTechnologyLevel,tl2AxisCount,advancedComponentCount,mainWeaponCount,reactorCount,weaponFamily,shieldPenetration,armorPenetration,weaponDamage,weaponAccuracyBonus,weaponPowerCost,reactorOutput,targetingBonus,evasiveCompensation,sensorInstalled,sensorProfile,shieldInstalled,shieldCapacity,shieldHardener,armorProtection,armorIntegrity,ecmRatings,ecmPower,eccmRatings,eccmPower,pdsCount,pdsFamily,pdsBaseChance,pdsPower,pdsReactionCapacity,pdsAmmunition,stlMove,ftlMove,standardOnboardMissileNavigationSensor,hasEwRedundancy,hasMainOrReactorDuplication,compositionClass,informationControlAdvancedCount,spaceUtilizationClass," +
            string.Join(",", study.Axes.Select(axis => "selection_" + axis.Id)),
        };
        lines.AddRange(builds.OrderBy(build => build.Id, StringComparer.Ordinal).Select(build => string.Join(",", new[]
        {
            Csv(build.Id), I(build.UsedSpace), I(build.FreeSpace), I(build.InstallationSpaceCapacity), I(build.MaxTechnologyLevel), I(build.Tl2AxisCount), I(build.AdvancedComponentCount),
            I(build.MainWeaponCount), I(build.ReactorCount), Csv(build.Family.ToString()), I(build.ShieldPenetration), I(build.ArmorPenetration), I(build.WeaponDamage ?? 0), I(build.WeaponAccuracyBonus ?? 0), I(build.WeaponPowerCost ?? 0), I(build.ReactorOutput),
            I(build.TargetingBonus), I(build.EvasiveCompensation), build.SensorInstalled.ToString().ToLowerInvariant(), Csv(build.SensorEwProfileId), build.ShieldInstalled.ToString().ToLowerInvariant(),
            I(build.ShieldCapacity), build.ShieldHardenerInstalled.ToString().ToLowerInvariant(), I(build.ArmorProtection), I(build.ArmorIntegrity), Csv(string.Join("+", build.EcmRatings)), I(build.EcmNormalPowerCost), Csv(string.Join("+", build.EccmRatings)), I(build.EccmNormalPowerCost),
            I(build.KineticPdsCount), Csv(build.PdsFamily ?? string.Empty), I(build.PdsBaseChance ?? 0), I(build.PdsPowerCost ?? 0), I(build.PdsReactionCapacity ?? 0), I(build.PdsAmmunition ?? -1), I(build.StlNormalMove ?? 0), I(build.FtlStrategicMove ?? 0), build.StandardOnboardNavigationSensor.ToString().ToLowerInvariant(), build.HasEwRedundancy.ToString().ToLowerInvariant(), build.HasMainOrReactorDuplication.ToString().ToLowerInvariant(), Csv(build.CompositionClass),
            I(build.InformationControlAdvancedCount), Csv(build.SpaceUtilizationClass),
        }.Concat(study.Axes.Select(axis => Csv(build.Selections[axis.Id]))))));
        File.WriteAllLines(Path.Combine(outputDirectory, "legal-builds.csv"), lines, new UTF8Encoding(false));
    }

    private static void WriteNamedBuilds(
        CrossTlBuildPermutationDocument study,
        IReadOnlyDictionary<string, CrossTlResolvedBuild> namedBuilds,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "recipeId,buildId,usedSpace,maxTechnologyLevel,advancedComponentCount,informationControlAdvancedCount,spaceUtilizationClass,mainWeaponCount,reactorCount,weaponFamily,ecmRatings,eccmRatings,pdsCount,compositionClass"
        };
        foreach (CrossTlNamedRecipeDocument recipe in study.NamedRecipes)
        {
            CrossTlResolvedBuild build = namedBuilds[recipe.Id];
            lines.Add(string.Join(",", new[]
            {
                Csv(recipe.Id), Csv(build.Id), I(build.UsedSpace), I(build.MaxTechnologyLevel), I(build.AdvancedComponentCount), I(build.InformationControlAdvancedCount), Csv(build.SpaceUtilizationClass), I(build.MainWeaponCount), I(build.ReactorCount),
                Csv(build.Family.ToString()), Csv(string.Join("+", build.EcmRatings)), Csv(string.Join("+", build.EccmRatings)), I(build.KineticPdsCount), Csv(build.CompositionClass),
            }));
        }
        File.WriteAllLines(Path.Combine(outputDirectory, "named-builds.csv"), lines, new UTF8Encoding(false));
    }

    private static void WritePairingPlan(IReadOnlyList<CrossTlLogicalPairing> pairings, string outputDirectory)
    {
        var lines = new List<string>
        {
            "pairingId,pairingGroup,source,matchedBundleId,orientation,compositionClass,progressionDirection,progressionDistance,progressionStratum,progressionMagnitudeStratum,spacePairStratum,usedSpaceDifference,absoluteUsedSpaceDifference,weaponFamilyPair,informationControlDirection,informationControlDistance,informationControlDistanceBand,sideAReadiness,sideBReadiness,sideAMaximumReadyRangeHexes,sideBMaximumReadyRangeHexes,populationCellKey,populationUnorderedDistinctCount,populationSampleCount,populationRepresentativeWeight,secondaryCoverageKey,sideALabel,sideABuildId,sideAUsedSpace,sideASpaceClass,sideAAdvancedComponents,sideAInformationControlAdvancedComponents,sideBLabel,sideBBuildId,sideBUsedSpace,sideBSpaceClass,sideBAdvancedComponents,sideBInformationControlAdvancedComponents"
        };
        lines.AddRange(pairings.Select(pairing => string.Join(",", new[]
        {
            Csv(pairing.Id), Csv(pairing.GroupId), Csv(pairing.Source), Csv(pairing.MatchedBundleId), Csv(pairing.Orientation),
            Csv(pairing.CompositionClass), Csv(pairing.ProgressionDirection), I(pairing.ProgressionDistance), Csv(pairing.ProgressionStratum),
            Csv(pairing.ProgressionMagnitudeStratum), Csv(pairing.SpacePairStratum), I(pairing.UsedSpaceDifference), I(pairing.AbsoluteUsedSpaceDifference),
            Csv(pairing.WeaponFamilyPair), Csv(pairing.InformationControlDirection), I(pairing.InformationControlDistance),
            Csv(pairing.InformationControlDistanceBand), Csv(pairing.SideAReadiness), Csv(pairing.SideBReadiness),
            I(pairing.SideAMaximumReadyRangeHexes), I(pairing.SideBMaximumReadyRangeHexes), Csv(pairing.PopulationCellKey),
            pairing.PopulationUnorderedDistinctCount.ToString(CultureInfo.InvariantCulture),
            I(pairing.PopulationSampleCount), pairing.PopulationRepresentativeWeight.ToString("R", CultureInfo.InvariantCulture),
            Csv(pairing.SecondaryCoverageKey),
            Csv(pairing.SideARecipe), Csv(pairing.SideA.Id), I(pairing.SideA.UsedSpace), Csv(pairing.SideA.SpaceUtilizationClass),
            I(pairing.SideA.AdvancedComponentCount), I(pairing.SideA.InformationControlAdvancedCount),
            Csv(pairing.SideBRecipe), Csv(pairing.SideB.Id), I(pairing.SideB.UsedSpace), Csv(pairing.SideB.SpaceUtilizationClass),
            I(pairing.SideB.AdvancedComponentCount), I(pairing.SideB.InformationControlAdvancedCount),
        })));
        File.WriteAllLines(Path.Combine(outputDirectory, "pairing-plan.csv"), lines, new UTF8Encoding(false));
    }

    private static void WritePopulationCoverage(
        CrossTlBuildPermutationDocument study,
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells,
        IReadOnlyList<CrossTlLogicalPairing> pairings,
        string outputDirectory)
    {
        bool adaptive = IsAdaptiveSamplingSchema(study.SchemaVersion);
        string inferenceSource = adaptive ? "statistical" : "stratified";
        long totalPopulation = populationCells.Values.Sum(cell => cell.PopulationUnorderedDistinctCount);
        var sampledBaseCounts = pairings.Where(pair => pair.Source == inferenceSource && pair.Orientation == "forward")
            .GroupBy(pair => pair.PopulationCellKey, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);
        var representativeWeight = pairings.Where(pair => pair.Source == inferenceSource && pair.Orientation == "forward")
            .GroupBy(pair => pair.PopulationCellKey, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.Sum(pair => pair.PopulationRepresentativeWeight), StringComparer.Ordinal);
        var diversityBaseCounts = pairings.Where(pair => pair.Source == "diversity" && pair.Orientation == "forward")
            .GroupBy(pair => pair.PopulationCellKey, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.Count(), StringComparer.Ordinal);
        var lines = new List<string>
        {
            "populationCellKey,compositionClass,progressionMagnitudeStratum,spacePairStratum,populationUnorderedDistinctCount,populationWeight,statisticalBasePairs,statisticalOrientations,statisticalRepresentativeWeight,diversityBasePairs,diversityOrientations,inclusionFraction"
        };
        foreach (CrossTlPopulationCell cell in populationCells.Values.OrderBy(cell => cell.Key, StringComparer.Ordinal))
        {
            int sampledBases = sampledBaseCounts.GetValueOrDefault(cell.Key);
            int diversityBases = diversityBaseCounts.GetValueOrDefault(cell.Key);
            lines.Add(string.Join(",", new[]
            {
                Csv(cell.Key), Csv(cell.CompositionClass), Csv(cell.ProgressionMagnitudeStratum), Csv(cell.SpacePairStratum),
                cell.PopulationUnorderedDistinctCount.ToString(CultureInfo.InvariantCulture),
                cell.PopulationWeight.ToString("R", CultureInfo.InvariantCulture),
                sampledBases.ToString(CultureInfo.InvariantCulture),
                (sampledBases * 2).ToString(CultureInfo.InvariantCulture),
                representativeWeight.GetValueOrDefault(cell.Key).ToString("R", CultureInfo.InvariantCulture),
                diversityBases.ToString(CultureInfo.InvariantCulture),
                (diversityBases * 2).ToString(CultureInfo.InvariantCulture),
                cell.PopulationUnorderedDistinctCount == 0 ? "0" :
                    ((double)sampledBases / cell.PopulationUnorderedDistinctCount).ToString("R", CultureInfo.InvariantCulture),
            }));
        }
        File.WriteAllLines(Path.Combine(outputDirectory, "population-coverage.csv"), lines, new UTF8Encoding(false));
        var summary = new
        {
            schemaVersion = adaptive
                ? "star-cluster-cross-tl-population-coverage-v2"
                : "star-cluster-cross-tl-population-coverage-v1",
            studyId = study.Id,
            legalBuildCount = study.ExpectedLegalBuildCount,
            unorderedDistinctPairPopulation = totalPopulation,
            populationCellCount = populationCells.Count,
            statisticalBasePairCount = sampledBaseCounts.Values.Sum(),
            statisticalOrientationCount = pairings.Count(pair => pair.Source == inferenceSource),
            statisticalRepresentativeWeightSum = representativeWeight.Values.Sum(),
            diversityBasePairCount = diversityBaseCounts.Values.Sum(),
            diversityOrientationCount = pairings.Count(pair => pair.Source == "diversity"),
            weightingUnit = "unordered distinct legal build pairs",
            note = adaptive
                ? "Population inference uses only the adaptive statistical sample. Each population cell is split equally among its statistical representatives; diversity-overlay and named diagnostic pairs carry zero population-inference weight."
                : "Population weights describe the legal unordered-distinct pair envelope. Named anchors remain diagnostic and are not included in population-weighted screening estimates.",
        };
        File.WriteAllText(Path.Combine(outputDirectory, "population-coverage-summary.json"),
            JsonSerializer.Serialize(summary, OutputJsonOptions()) + Environment.NewLine, new UTF8Encoding(false));
    }

    private static void WriteSecondaryCoverage(
        CrossTlBuildPermutationDocument study,
        IReadOnlyDictionary<string, CrossTlPopulationCell> populationCells,
        IReadOnlyList<CrossTlLogicalPairing> pairings,
        string outputDirectory)
    {
        var lines = new List<string>
        {
            "populationCellKey,populationUnorderedDistinctCount,statisticalBasePairs,diversityBasePairs,statisticalDistinctFamilyPairs,statisticalDistinctInfoBands,statisticalDistinctSecondaryKeys,totalDistinctSecondaryKeys,diversityAddedSecondaryKeys"
        };
        foreach (CrossTlPopulationCell cell in populationCells.Values
            .OrderByDescending(cell => cell.PopulationUnorderedDistinctCount)
            .ThenBy(cell => cell.Key, StringComparer.Ordinal))
        {
            CrossTlLogicalPairing[] statistical = pairings.Where(pair => pair.Source == "statistical" &&
                pair.Orientation == "forward" && pair.PopulationCellKey == cell.Key).ToArray();
            CrossTlLogicalPairing[] diversity = pairings.Where(pair => pair.Source == "diversity" &&
                pair.Orientation == "forward" && pair.PopulationCellKey == cell.Key).ToArray();
            var statisticalKeys = new HashSet<string>(statistical.Select(pair => pair.SecondaryCoverageKey), StringComparer.Ordinal);
            var totalKeys = new HashSet<string>(statisticalKeys, StringComparer.Ordinal);
            foreach (CrossTlLogicalPairing pair in diversity) totalKeys.Add(pair.SecondaryCoverageKey);
            int diversityAdded = totalKeys.Count - statisticalKeys.Count;
            lines.Add(string.Join(",", new[]
            {
                Csv(cell.Key), cell.PopulationUnorderedDistinctCount.ToString(CultureInfo.InvariantCulture),
                statistical.Length.ToString(CultureInfo.InvariantCulture), diversity.Length.ToString(CultureInfo.InvariantCulture),
                statistical.Select(pair => pair.WeaponFamilyPair).Distinct(StringComparer.Ordinal).Count().ToString(CultureInfo.InvariantCulture),
                statistical.Select(pair => pair.InformationControlDistanceBand).Distinct(StringComparer.Ordinal).Count().ToString(CultureInfo.InvariantCulture),
                statisticalKeys.Count.ToString(CultureInfo.InvariantCulture), totalKeys.Count.ToString(CultureInfo.InvariantCulture),
                diversityAdded.ToString(CultureInfo.InvariantCulture),
            }));
        }
        File.WriteAllLines(Path.Combine(outputDirectory, "secondary-coverage.csv"), lines, new UTF8Encoding(false));
    }

    private static void WriteFoundationGates(IReadOnlyList<CrossTlFoundationGate> gates, string outputDirectory)
    {
        var lines = new List<string> { "gateId,passed,detail" };
        lines.AddRange(gates.Select(gate => $"{Csv(gate.Id)},{gate.Passed.ToString().ToLowerInvariant()},{Csv(gate.Detail)}"));
        File.WriteAllLines(Path.Combine(outputDirectory, "gates.csv"), lines, new UTF8Encoding(false));
    }

    private static void WritePreflightSummary(
        CrossTlBuildPermutationDocument study,
        string studyHash,
        string baselineHash,
        CrossTlEnumerationResult enumeration,
        IReadOnlyList<CrossTlLogicalPairing> pairings,
        Tl1IntegratedTacticalCombatStudyDocument generated,
        int failedGateCount,
        string outputDirectory)
    {
        bool adaptive = IsAdaptiveSamplingSchema(study.SchemaVersion);
        string inferenceSource = adaptive ? "statistical" : "stratified";
        var payload = new
        {
            schemaVersion = adaptive
                ? "star-cluster-cross-tl-build-permutation-preflight-v3"
                : IsMatchedReadinessSchema(study.SchemaVersion)
                    ? "star-cluster-cross-tl-build-permutation-preflight-v2"
                    : "star-cluster-cross-tl-build-permutation-preflight-v1",
            studyId = study.Id,
            studySha256 = studyHash,
            baselineSha256 = baselineHash,
            rawCombinationCount = enumeration.RawCombinationCount,
            legalBuildCount = enumeration.LegalBuilds.Count,
            exactFillBuildCount = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "exact_fill"),
            nearFillBuildCount = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "near_fill"),
            underfilledBuildCount = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "underfilled"),
            unorderedDistinctPairingEnvelope = ((long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count - 1L)) / 2L,
            orientedDistinctPairingEnvelope = (long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count - 1L),
            namedRecipeCount = enumeration.NamedBuilds.Count,
            namedLogicalPairingCount = pairings.Count(pair => pair.Source == "named"),
            statisticalLogicalPairingCount = pairings.Count(pair => pair.Source == inferenceSource),
            statisticalBasePairCount = pairings.Count(pair => pair.Source == inferenceSource && pair.Orientation == "forward"),
            diversityLogicalPairingCount = pairings.Count(pair => pair.Source == "diversity"),
            diversityBasePairCount = pairings.Count(pair => pair.Source == "diversity" && pair.Orientation == "forward"),
            populationCellCount = pairings.Where(pair => pair.Source == inferenceSource)
                .Select(pair => pair.PopulationCellKey).Distinct(StringComparer.Ordinal).Count(),
            logicalPairingCount = pairings.Count,
            geometryCount = study.Geometries.Count,
            generatedVariantCount = generated.Variants.Count,
            failedGateCount,
        };
        File.WriteAllText(Path.Combine(outputDirectory, "preflight-summary.json"),
            JsonSerializer.Serialize(payload, OutputJsonOptions()) + Environment.NewLine, new UTF8Encoding(false));
    }

    private static void WriteGenerationSummary(
        CrossTlBuildPermutationDocument study,
        string studyHash,
        string baselineHash,
        string generatedStudyPath,
        string generatedStudyHash,
        CrossTlEnumerationResult enumeration,
        IReadOnlyList<CrossTlLogicalPairing> pairings,
        Tl1IntegratedTacticalCombatStudyDocument generated,
        string outputDirectory)
    {
        bool adaptive = IsAdaptiveSamplingSchema(study.SchemaVersion);
        string inferenceSource = adaptive ? "statistical" : "stratified";
        string[] notes = adaptive
            ? new[]
            {
                "The complete 22,592-build legal envelope remains deterministic. Population inference uses an adaptive 192-base-pair statistical sample across all 96 population cells, mirrored in both orientations, plus a separate mirrored diversity overlay and retained named diagnostics.",
                "Statistical cell population weight is divided equally among that cell's statistical representatives. Diversity-overlay and named diagnostic pairs carry zero population-inference weight.",
                "The diversity overlay targets the highest-population cells and prefers additional weapon-family/information-control secondary coverage without changing population inference.",
                "Structural engagement readiness records the exact maximum ready range separately from observed runtime activity so movement-doctrine denial can be diagnosed rather than conflated with build incapability.",
                "Both dynamic mover-order bounds remain explicit; downstream review also reports mover-order-neutral estimates and initiative sensitivity.",
                "Power overcommit is not a construction-legality filter, and no gameplay/component/technology candidate is promoted by this screening architecture.",
            }
            : IsMatchedReadinessSchema(study.SchemaVersion)
                ? new[]
                {
                    "The full legal-build envelope is enumerated deterministically; 48 named diagnostics plus one unordered distinct base pair from each of 96 composition/progression-magnitude/Space cells are emitted, with every sampled base pair mirrored in both orientations.",
                    "Structural engagement readiness is classified independently from runtime combat activity; engagement-denied legal builds remain in all-legal ecosystem reporting.",
                    "Population weights describe unordered distinct legal-pair prevalence by sampling cell; one sampled pair does not exhaustively represent within-cell build diversity.",
                    "Power overcommit is not a construction-legality filter.",
                    "Every legal combat build contains at least one Main Weapon and one Reactor; second Main Weapons/Reactors are explicit optional design choices subject to Space.",
                    "Redundant ECM/ECCM installations are allowed but never additive; runtime resolves the highest applicable functional rating.",
                    "Locally validated candidates remain provisional pending broader cross-TL integration and explicit human promotion.",
                }
                : new[]
                {
                    "The full legal-build envelope is enumerated deterministically; named anchors plus a deterministic progression/composition-stratified sample are promoted to Monte Carlo in this checkpoint.",
                    "Power overcommit is not a construction-legality filter.",
                    "Every legal combat build contains at least one Main Weapon and one Reactor; second Main Weapons/Reactors are explicit optional design choices subject to Space.",
                    "Redundant ECM/ECCM installations are allowed but never additive; runtime resolves the highest applicable functional rating.",
                    "Locally validated candidates remain provisional pending broader cross-TL integration.",
                };
        var payload = new
        {
            schemaVersion = adaptive
                ? "star-cluster-cross-tl-build-permutation-summary-v3"
                : IsMatchedReadinessSchema(study.SchemaVersion)
                    ? "star-cluster-cross-tl-build-permutation-summary-v2"
                    : "star-cluster-cross-tl-build-permutation-summary-v1",
            studyId = study.Id,
            generatedStudyId = generated.Id,
            studySha256 = studyHash,
            baselineSha256 = baselineHash,
            generatedStudyPath = Path.GetFullPath(generatedStudyPath),
            generatedStudySha256 = generatedStudyHash,
            rawCombinationCount = enumeration.RawCombinationCount,
            legalBuildCount = enumeration.LegalBuilds.Count,
            exactFillBuildCount = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "exact_fill"),
            nearFillBuildCount = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "near_fill"),
            underfilledBuildCount = enumeration.LegalBuilds.Count(build => build.SpaceUtilizationClass == "underfilled"),
            orientedPairingEnvelope = (long)enumeration.LegalBuilds.Count * enumeration.LegalBuilds.Count,
            unorderedWithSelfPairingEnvelope = ((long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count + 1L)) / 2L,
            orientedDistinctPairingEnvelope = (long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count - 1L),
            unorderedDistinctPairingEnvelope = ((long)enumeration.LegalBuilds.Count * (enumeration.LegalBuilds.Count - 1L)) / 2L,
            namedRecipeCount = enumeration.NamedBuilds.Count,
            namedLogicalPairingCount = pairings.Count(pair => pair.Source == "named"),
            statisticalLogicalPairingCount = pairings.Count(pair => pair.Source == inferenceSource),
            statisticalBasePairCount = pairings.Count(pair => pair.Source == inferenceSource && pair.Orientation == "forward"),
            diversityLogicalPairingCount = pairings.Count(pair => pair.Source == "diversity"),
            diversityBasePairCount = pairings.Count(pair => pair.Source == "diversity" && pair.Orientation == "forward"),
            populationCellCount = pairings.Where(pair => pair.Source == inferenceSource)
                .Select(pair => pair.PopulationCellKey).Distinct(StringComparer.Ordinal).Count(),
            logicalPairingCount = pairings.Count,
            geometryCount = study.Geometries.Count,
            generatedVariantCount = generated.Variants.Count,
            trialsPerVariant = generated.TrialsPerVariant,
            defaultSubstantiveTrials = (long)generated.Variants.Count * generated.TrialsPerVariant,
            notes,
        };
        File.WriteAllText(Path.Combine(outputDirectory, "summary.json"),
            JsonSerializer.Serialize(payload, OutputJsonOptions()) + Environment.NewLine, new UTF8Encoding(false));
    }

    private static string Sha256File(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
    private static string I(int value) => value.ToString(CultureInfo.InvariantCulture);
    private static string Csv(string value)
    {
        string text = value ?? string.Empty;
        return text.IndexOfAny(new[] { ',', '"', '\r', '\n' }) >= 0
            ? "\"" + text.Replace("\"", "\"\"") + "\""
            : text;
    }
    private static JsonSerializerOptions JsonOptions() => new() { PropertyNameCaseInsensitive = false };
    private static JsonSerializerOptions OutputJsonOptions() => new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };
}

public sealed class CrossTlBuildPermutationDocument
{
    [JsonPropertyName("schemaVersion")] public string SchemaVersion { get; set; } = string.Empty;
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("checkpoint")] public string Checkpoint { get; set; } = string.Empty;
    [JsonPropertyName("status")] public string Status { get; set; } = string.Empty;
    [JsonPropertyName("purpose")] public string Purpose { get; set; } = string.Empty;
    [JsonPropertyName("coverageMode")] public string? CoverageMode { get; set; }
    [JsonPropertyName("totalInstallationSpace")] public int TotalInstallationSpace { get; set; }
    [JsonPropertyName("fixedShellSpace")] public int FixedShellSpace { get; set; }
    [JsonPropertyName("fixedShell")] public CrossTlFixedShellDocument FixedShell { get; set; } = new();
    [JsonPropertyName("baselineProfileId")] public string BaselineProfileId { get; set; } = "tl1-production";
    [JsonPropertyName("technologyProfileCatalog")] public string? TechnologyProfileCatalog { get; set; }
    [JsonPropertyName("auxiliaryProfileCatalog")] public string AuxiliaryProfileCatalog { get; set; } = string.Empty;
    [JsonPropertyName("auxiliaryProfileId")] public string AuxiliaryProfileId { get; set; } = string.Empty;
    [JsonPropertyName("sensorEwProfileCatalog")] public string SensorEwProfileCatalog { get; set; } = string.Empty;
    [JsonPropertyName("aiDoctrineCatalog")] public string? AiDoctrineCatalog { get; set; }
    [JsonPropertyName("aiDoctrineId")] public string? AiDoctrineId { get; set; }
    [JsonPropertyName("variantIdPrefix")] public string VariantIdPrefix { get; set; } = "c87";
    [JsonPropertyName("constructionGuardrails")] public CrossTlConstructionGuardrailsDocument? ConstructionGuardrails { get; set; }
    [JsonPropertyName("generatedStudyId")] public string GeneratedStudyId { get; set; } = string.Empty;
    [JsonPropertyName("masterSeed")] public ulong MasterSeed { get; set; }
    [JsonPropertyName("trialsPerVariant")] public int TrialsPerVariant { get; set; }
    [JsonPropertyName("expectedRawCombinationCount")] public long ExpectedRawCombinationCount { get; set; }
    [JsonPropertyName("expectedLegalBuildCount")] public int ExpectedLegalBuildCount { get; set; }
    [JsonPropertyName("expectedExactFillBuildCount")] public int ExpectedExactFillBuildCount { get; set; }
    [JsonPropertyName("expectedNearFillBuildCount")] public int ExpectedNearFillBuildCount { get; set; }
    [JsonPropertyName("expectedUnderfilledBuildCount")] public int ExpectedUnderfilledBuildCount { get; set; }
    [JsonPropertyName("expectedUnorderedDistinctPairingEnvelope")] public long ExpectedUnorderedDistinctPairingEnvelope { get; set; }
    [JsonPropertyName("expectedOrientedDistinctPairingEnvelope")] public long ExpectedOrientedDistinctPairingEnvelope { get; set; }
    [JsonPropertyName("expectedNamedRecipeCount")] public int ExpectedNamedRecipeCount { get; set; }
    [JsonPropertyName("expectedNamedLogicalPairingCount")] public int ExpectedNamedLogicalPairingCount { get; set; }
    [JsonPropertyName("expectedStratifiedLogicalPairingCount")] public int ExpectedStratifiedLogicalPairingCount { get; set; }
    [JsonPropertyName("expectedLogicalPairingCount")] public int ExpectedLogicalPairingCount { get; set; }
    [JsonPropertyName("expectedGeometryCount")] public int ExpectedGeometryCount { get; set; }
    [JsonPropertyName("expectedGeneratedVariantCount")] public int ExpectedGeneratedVariantCount { get; set; }
    [JsonPropertyName("expectedOrientedPairingEnvelope")] public long ExpectedOrientedPairingEnvelope { get; set; }
    [JsonPropertyName("expectedUnorderedWithSelfPairingEnvelope")] public long ExpectedUnorderedWithSelfPairingEnvelope { get; set; }
    [JsonPropertyName("stratifiedPairingSelection")] public CrossTlStratifiedPairingSelectionDocument? StratifiedPairingSelection { get; set; }
    [JsonPropertyName("exactEdgePairingSelection")] public CrossTlExactEdgePairingSelectionDocument? ExactEdgePairingSelection { get; set; }
    [JsonPropertyName("progressionLattice")] public CrossTlProgressionLatticeDocument? ProgressionLattice { get; set; }
    [JsonPropertyName("axes")] public List<CrossTlTechnologyAxisDocument> Axes { get; set; } = new();
    [JsonPropertyName("namedRecipes")] public List<CrossTlNamedRecipeDocument> NamedRecipes { get; set; } = new();
    [JsonPropertyName("pairingGroups")] public List<CrossTlPairingGroupDocument> PairingGroups { get; set; } = new();
    [JsonPropertyName("geometries")] public List<CrossTlGeometryDocument> Geometries { get; set; } = new();
}

public sealed class CrossTlConstructionGuardrailsDocument
{
    [JsonPropertyName("minimumMainWeaponCount")] public int MinimumMainWeaponCount { get; set; } = 1;
    [JsonPropertyName("minimumReactorCount")] public int MinimumReactorCount { get; set; } = 1;
    [JsonPropertyName("minimumSensorCount")] public int MinimumSensorCount { get; set; }
    [JsonPropertyName("sensorlessDiagnosticsAllowedOutsideLegalPopulation")] public bool SensorlessDiagnosticsAllowedOutsideLegalPopulation { get; set; }
    [JsonPropertyName("additionalMainWeaponsOptional")] public bool AdditionalMainWeaponsOptional { get; set; } = true;
    [JsonPropertyName("additionalReactorsOptional")] public bool AdditionalReactorsOptional { get; set; } = true;
    [JsonPropertyName("duplicationMustBeExplicit")] public bool DuplicationMustBeExplicit { get; set; } = true;
    [JsonPropertyName("redundantEwInstallationsAllowed")] public bool RedundantEwInstallationsAllowed { get; set; }
    [JsonPropertyName("ecmSameTypeRatingsAdditive")] public bool EcmSameTypeRatingsAdditive { get; set; }
    [JsonPropertyName("eccmSameTypeRatingsAdditive")] public bool EccmSameTypeRatingsAdditive { get; set; }
    [JsonPropertyName("ewDuplicateResolution")] public string? EwDuplicateResolution { get; set; }
    [JsonPropertyName("powerSufficiencyIsConstructionLegalityFilter")] public bool PowerSufficiencyIsConstructionLegalityFilter { get; set; }
}

public sealed class CrossTlFixedShellDocument
{
    [JsonPropertyName("description")] public string Description { get; set; } = string.Empty;
    [JsonPropertyName("stlDriveSpace")] public int StlDriveSpace { get; set; }
    [JsonPropertyName("ftlDriveSpace")] public int FtlDriveSpace { get; set; }
    [JsonPropertyName("kineticPdsSpace")] public int KineticPdsSpace { get; set; }
    [JsonPropertyName("kineticPdsCount")] public int KineticPdsCount { get; set; }
}

public sealed class CrossTlTechnologyAxisDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("code")] public string Code { get; set; } = string.Empty;
    [JsonPropertyName("options")] public List<CrossTlTechnologyOptionDocument> Options { get; set; } = new();
}

public sealed class CrossTlTechnologyOptionDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("technologyLevel")] public int TechnologyLevel { get; set; }
    [JsonPropertyName("status")] public string Status { get; set; } = string.Empty;
    [JsonPropertyName("space")] public int Space { get; set; }
    [JsonPropertyName("mainWeaponCount")] public int? MainWeaponCount { get; set; }
    [JsonPropertyName("reactorCount")] public int? ReactorCount { get; set; }
    [JsonPropertyName("family")] public string? Family { get; set; }
    [JsonPropertyName("shieldPenetration")] public int? ShieldPenetration { get; set; }
    [JsonPropertyName("armorPenetration")] public int? ArmorPenetration { get; set; }
    [JsonPropertyName("reactorOutput")] public int? ReactorOutput { get; set; }
    [JsonPropertyName("targetingBonus")] public int? TargetingBonus { get; set; }
    [JsonPropertyName("sensorEwProfileId")] public string? SensorEwProfileId { get; set; }
    [JsonPropertyName("shieldCapacity")] public int? ShieldCapacity { get; set; }
    [JsonPropertyName("armorProtection")] public int? ArmorProtection { get; set; }
    [JsonPropertyName("armorIntegrity")] public int? ArmorIntegrity { get; set; }
    [JsonPropertyName("ewRating")] public int? EwRating { get; set; }
    [JsonPropertyName("ewRatings")] public List<int> EwRatings { get; set; } = new();
    [JsonPropertyName("installed")] public bool? Installed { get; set; }
    [JsonPropertyName("pdsCount")] public int? PdsCount { get; set; }
    [JsonPropertyName("installationSpaceCapacity")] public int? InstallationSpaceCapacity { get; set; }
    [JsonPropertyName("damage")] public int? Damage { get; set; }
    [JsonPropertyName("accuracyBonus")] public int? AccuracyBonus { get; set; }
    [JsonPropertyName("powerCost")] public int? PowerCost { get; set; }
    [JsonPropertyName("maximumRange")] public int? MaximumRange { get; set; }
    [JsonPropertyName("ammunition")] public int? Ammunition { get; set; }
    [JsonPropertyName("preferredSmokeModeId")] public string? PreferredSmokeModeId { get; set; }
    [JsonPropertyName("preferredSmokeModeDamage")] public int? PreferredSmokeModeDamage { get; set; }
    [JsonPropertyName("preferredSmokeModePowerCost")] public int? PreferredSmokeModePowerCost { get; set; }
    [JsonPropertyName("preferredSmokeModeAccuracyBonus")] public int? PreferredSmokeModeAccuracyBonus { get; set; }
    [JsonPropertyName("evasiveCompensation")] public int? EvasiveCompensation { get; set; }
    [JsonPropertyName("passiveFirmRange")] public int? PassiveFirmRange { get; set; }
    [JsonPropertyName("passiveApproximateRange")] public int? PassiveApproximateRange { get; set; }
    [JsonPropertyName("activeLowFirmRange")] public int? ActiveLowFirmRange { get; set; }
    [JsonPropertyName("activeLowApproximateRange")] public int? ActiveLowApproximateRange { get; set; }
    [JsonPropertyName("activeLowPowerCost")] public int? ActiveLowPowerCost { get; set; }
    [JsonPropertyName("activeHighFirmRange")] public int? ActiveHighFirmRange { get; set; }
    [JsonPropertyName("activeHighApproximateRange")] public int? ActiveHighApproximateRange { get; set; }
    [JsonPropertyName("activeHighPowerCost")] public int? ActiveHighPowerCost { get; set; }
    [JsonPropertyName("ewNormalPowerCost")] public int? EwNormalPowerCost { get; set; }
    [JsonPropertyName("ewFullStrengthNormalPowerCost")] public int? EwFullStrengthNormalPowerCost { get; set; }
    [JsonPropertyName("shieldArmorBonus")] public int? ShieldArmorBonus { get; set; }
    [JsonPropertyName("sustainedPowerCost")] public int? SustainedPowerCost { get; set; }
    [JsonPropertyName("normalMove")] public int? NormalMove { get; set; }
    [JsonPropertyName("strategicMove")] public int? StrategicMove { get; set; }
    [JsonPropertyName("standardOnboardNavigationSensor")] public bool? StandardOnboardNavigationSensor { get; set; }
    [JsonPropertyName("missileMove")] public int? MissileMove { get; set; }
    [JsonPropertyName("pdsFamily")] public string? PdsFamily { get; set; }
    [JsonPropertyName("pdsBaseChance")] public int? PdsBaseChance { get; set; }
    [JsonPropertyName("pdsPowerCost")] public int? PdsPowerCost { get; set; }
    [JsonPropertyName("pdsReactionCapacity")] public int? PdsReactionCapacity { get; set; }
    [JsonPropertyName("pdsFallbackPowerCost")] public int? PdsFallbackPowerCost { get; set; }
    [JsonPropertyName("pdsFallbackReactionCapacity")] public int? PdsFallbackReactionCapacity { get; set; }
    [JsonPropertyName("pdsAmmunition")] public int? PdsAmmunition { get; set; }
    [JsonPropertyName("note")] public string? Note { get; set; }
}

public sealed class CrossTlProgressionLatticeDocument
{
    [JsonPropertyName("enabled")] public bool Enabled { get; set; }
    [JsonPropertyName("requireSameInstallationSpace")] public bool RequireSameInstallationSpace { get; set; } = true;
    [JsonPropertyName("expectedTotalLegalEdgeCount")] public int ExpectedTotalLegalEdgeCount { get; set; }
    [JsonPropertyName("transitions")] public List<CrossTlProgressionTransitionDocument> Transitions { get; set; } = new();
}

public sealed class CrossTlProgressionTransitionDocument
{
    private int _expectedAdvancedComponentDelta = 1;

    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("axisId")] public string AxisId { get; set; } = string.Empty;
    [JsonPropertyName("fromOptionId")] public string FromOptionId { get; set; } = string.Empty;
    [JsonPropertyName("toOptionId")] public string ToOptionId { get; set; } = string.Empty;
    [JsonPropertyName("expectedLegalEdgeCount")] public int ExpectedLegalEdgeCount { get; set; }
    [JsonPropertyName("expectedExactFillEdgeCount")] public int ExpectedExactFillEdgeCount { get; set; }
    [JsonPropertyName("kind")] public string? Kind { get; set; }
    [JsonPropertyName("expectedInstallationSpaceDelta")] public int ExpectedInstallationSpaceDelta { get; set; }
    [JsonPropertyName("expectedCapacityDelta")] public int ExpectedCapacityDelta { get; set; }
    [JsonIgnore] public bool HasExplicitExpectedAdvancedComponentDelta { get; private set; }
    [JsonPropertyName("expectedAdvancedComponentDelta")]
    public int ExpectedAdvancedComponentDelta
    {
        get => _expectedAdvancedComponentDelta;
        set
        {
            _expectedAdvancedComponentDelta = value;
            HasExplicitExpectedAdvancedComponentDelta = true;
        }
    }

    public void ResolveLegacyExpectedAdvancedComponentDelta(int inferred)
    {
        if (!HasExplicitExpectedAdvancedComponentDelta)
        {
            _expectedAdvancedComponentDelta = inferred;
        }
    }
}

public sealed class CrossTlExactEdgePairingSelectionDocument
{
    [JsonPropertyName("enabled")] public bool Enabled { get; set; }
    [JsonPropertyName("representativesPerStratum")] public int RepresentativesPerStratum { get; set; }
    [JsonPropertyName("expectedStratumCount")] public int ExpectedStratumCount { get; set; }
    [JsonPropertyName("expectedLogicalPairingCount")] public int ExpectedLogicalPairingCount { get; set; }
    [JsonPropertyName("strata")] public List<string> Strata { get; set; } = new();
    [JsonPropertyName("ordering")] public string? Ordering { get; set; }
    [JsonPropertyName("note")] public string? Note { get; set; }
}

public sealed class CrossTlStratifiedPairingSelectionDocument
{
    [JsonPropertyName("enabled")] public bool Enabled { get; set; }
    [JsonPropertyName("seed")] public ulong Seed { get; set; }
    [JsonPropertyName("targetPerCell")] public int TargetPerCell { get; set; }
    [JsonPropertyName("expectedSampleCount")] public int ExpectedSampleCount { get; set; }
    [JsonPropertyName("maxAttempts")] public int MaxAttempts { get; set; }
    [JsonPropertyName("nearDistanceMaximum")] public int NearDistanceMaximum { get; set; }
    [JsonPropertyName("equalLowAdvancedMaximum")] public int EqualLowAdvancedMaximum { get; set; }
    [JsonPropertyName("matchedBidirectional")] public bool MatchedBidirectional { get; set; }
    [JsonPropertyName("expectedBasePairCount")] public int ExpectedBasePairCount { get; set; }
    [JsonPropertyName("nearFillMinimumUsedSpace")] public int NearFillMinimumUsedSpace { get; set; }
    [JsonPropertyName("compositionClasses")] public List<string> CompositionClasses { get; set; } = new();
    [JsonPropertyName("progressionStrata")] public List<string> ProgressionStrata { get; set; } = new();
    [JsonPropertyName("progressionMagnitudeStrata")] public List<string> ProgressionMagnitudeStrata { get; set; } = new();
    [JsonPropertyName("spaceUtilizationClasses")] public List<string> SpaceUtilizationClasses { get; set; } = new();
    [JsonPropertyName("spacePairStrata")] public List<string> SpacePairStrata { get; set; } = new();
    [JsonPropertyName("adaptiveAllocationEnabled")] public bool AdaptiveAllocationEnabled { get; set; }
    [JsonPropertyName("targetBasePairBudget")] public int TargetBasePairBudget { get; set; }
    [JsonPropertyName("minimumPerPopulationCell")] public int MinimumPerPopulationCell { get; set; }
    [JsonPropertyName("allocationExponent")] public double AllocationExponent { get; set; }
    [JsonPropertyName("maximumPerPopulationCell")] public int MaximumPerPopulationCell { get; set; }
    [JsonPropertyName("diversityOverlayEnabled")] public bool DiversityOverlayEnabled { get; set; }
    [JsonPropertyName("diversityOverlayTopCellCount")] public int DiversityOverlayTopCellCount { get; set; }
    [JsonPropertyName("diversityOverlayPairsPerCell")] public int DiversityOverlayPairsPerCell { get; set; }
    [JsonPropertyName("expectedDiversityBasePairCount")] public int ExpectedDiversityBasePairCount { get; set; }
    [JsonPropertyName("expectedDiversitySampleCount")] public int ExpectedDiversitySampleCount { get; set; }
    [JsonPropertyName("informationControlNearDistanceMaximum")] public int InformationControlNearDistanceMaximum { get; set; } = 2;
    [JsonPropertyName("note")] public string? Note { get; set; }
}

public sealed class CrossTlNamedRecipeDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("selections")] public Dictionary<string, string> Selections { get; set; } = new(StringComparer.Ordinal);
}

public sealed class CrossTlPairingGroupDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("progressionTransitionId")] public string? ProgressionTransitionId { get; set; }
    [JsonPropertyName("sideARecipes")] public List<string> SideARecipes { get; set; } = new();
    [JsonPropertyName("sideBRecipes")] public List<string> SideBRecipes { get; set; } = new();
}

public sealed class CrossTlGeometryDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("movementMode")] public string MovementMode { get; set; } = string.Empty;
    [JsonPropertyName("movementOrder")] public string MovementOrder { get; set; } = string.Empty;
    [JsonPropertyName("initialRangeHexes")] public int InitialRangeHexes { get; set; }
}

public sealed record CrossTlResolvedBuild(
    string Id,
    IReadOnlyDictionary<string, string> Selections,
    int UsedSpace,
    int FreeSpace,
    int InstallationSpaceCapacity,
    int MaxTechnologyLevel,
    int Tl2AxisCount,
    int AdvancedComponentCount,
    int MainWeaponCount,
    int ReactorCount,
    WeaponFamily Family,
    int ShieldPenetration,
    int ArmorPenetration,
    int? WeaponDamage,
    int? WeaponAccuracyBonus,
    int? WeaponPowerCost,
    int? WeaponMaximumRange,
    int? WeaponAmmunition,
    string? PreferredSmokeModeId,
    int? PreferredSmokeModeDamage,
    int? PreferredSmokeModePowerCost,
    int? PreferredSmokeModeAccuracyBonus,
    int ReactorOutput,
    int TargetingBonus,
    int EvasiveCompensation,
    string SensorEwProfileId,
    bool SensorInstalled,
    int? SensorPassiveFirmRange,
    int? SensorPassiveApproximateRange,
    int? SensorActiveLowFirmRange,
    int? SensorActiveLowApproximateRange,
    int? SensorActiveLowPowerCost,
    int? SensorActiveHighFirmRange,
    int? SensorActiveHighApproximateRange,
    int? SensorActiveHighPowerCost,
    bool ShieldInstalled,
    int ShieldCapacity,
    bool ShieldHardenerInstalled,
    int ShieldHardenerArmor,
    int ShieldHardenerPowerCost,
    int ArmorProtection,
    int ArmorIntegrity,
    IReadOnlyList<int> EcmRatings,
    int EcmNormalPowerCost,
    int? EcmFullStrengthNormalPowerCost,
    IReadOnlyList<int> EccmRatings,
    int EccmNormalPowerCost,
    int? EccmFullStrengthNormalPowerCost,
    int KineticPdsCount,
    string? PdsFamily,
    int? PdsBaseChance,
    int? PdsPowerCost,
    int? PdsReactionCapacity,
    int? PdsFallbackPowerCost,
    int? PdsFallbackReactionCapacity,
    int? PdsAmmunition,
    int? StlNormalMove,
    int? FtlStrategicMove,
    int? MissileMove,
    bool StandardOnboardNavigationSensor,
    bool HasEwRedundancy,
    bool HasMainOrReactorDuplication,
    string CompositionClass,
    int InformationControlAdvancedCount,
    string SpaceUtilizationClass);

public sealed record CrossTlLogicalPairing(
    string Id,
    string GroupId,
    string SideARecipe,
    string SideBRecipe,
    CrossTlResolvedBuild SideA,
    CrossTlResolvedBuild SideB,
    string Source,
    string ProgressionDirection,
    int ProgressionDistance,
    string ProgressionStratum,
    string CompositionClass,
    string MatchedBundleId,
    string Orientation,
    string ProgressionMagnitudeStratum,
    string SpacePairStratum,
    int UsedSpaceDifference,
    int AbsoluteUsedSpaceDifference,
    string WeaponFamilyPair,
    string InformationControlDirection,
    int InformationControlDistance,
    string InformationControlDistanceBand,
    string SideAReadiness,
    string SideBReadiness,
    int SideAMaximumReadyRangeHexes,
    int SideBMaximumReadyRangeHexes,
    string PopulationCellKey,
    long PopulationUnorderedDistinctCount,
    int PopulationSampleCount,
    double PopulationRepresentativeWeight,
    string SecondaryCoverageKey,
    string ProgressionTransitionId = "",
    int ExpectedAdvancedComponentDelta = 0);

public sealed record CrossTlEngagementReadiness(
    string ReadinessClass,
    int MaximumReadyRangeHexes);

public sealed record CrossTlReadinessContext(
    IReadOnlyDictionary<string, SensorEwFoundationProfile> SensorProfiles,
    int KineticPhysicalRange,
    int EnergyPhysicalRange,
    int MissilePhysicalRange);

public sealed record CrossTlPopulationCell(
    string Key,
    string CompositionClass,
    string ProgressionMagnitudeStratum,
    string SpacePairStratum,
    long PopulationUnorderedDistinctCount,
    double PopulationWeight);

public sealed record CrossTlPopulationBucketKey(
    bool HasEwRedundancy,
    bool HasMainOrReactorDuplication,
    int AdvancedComponentCount,
    string SpaceUtilizationClass);

public sealed record CrossTlProgressionEdge(
    string TransitionId,
    string AxisId,
    string FromOptionId,
    string ToOptionId,
    string Kind,
    int ExpectedInstallationSpaceDelta,
    int ExpectedCapacityDelta,
    string LowerBuildId,
    string HigherBuildId,
    int LowerUsedSpace,
    int HigherUsedSpace,
    int LowerInstallationSpaceCapacity,
    int HigherInstallationSpaceCapacity,
    int LowerAdvancedComponentCount,
    int HigherAdvancedComponentCount,
    WeaponFamily WeaponFamily,
    string CompositionClass,
    string SpaceUtilizationClass,
    int ExpectedAdvancedComponentDelta);

public sealed record CrossTlPopulationBucket(
    CrossTlPopulationBucketKey Key,
    long Count);

public sealed record CrossTlEnumerationResult(
    long RawCombinationCount,
    IReadOnlyList<CrossTlResolvedBuild> LegalBuilds,
    IReadOnlyDictionary<string, CrossTlResolvedBuild> NamedBuilds);

public sealed record CrossTlFoundationGate(string Id, bool Passed, string Detail);
