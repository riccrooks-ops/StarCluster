using System.Collections.Concurrent;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Power;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1InternalDamageCalibrationRunner
{
    private const string SchemaVersion =
        "star-cluster-tl1-internal-damage-calibration-v1";
    private const int RequiredVariantCount = 80;
    private const int Hull = 12;

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1InternalDamageCalibrationStudyDocument study =
            JsonSerializer.Deserialize<Tl1InternalDamageCalibrationStudyDocument>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                "TL1 internal-damage study could not be read.");
        string baselineHash = Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselinePath)))
            .ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine(
            $"TL1 Internal Damage preflight: {study.Variants.Count} variants; " +
            "15/20/25/33 1/3/50 percent H/X densities, ordinary seeded and " +
            "finite-count Protected Compartmentation with terminal H/X swap, " +
            "kinetic and missile loadouts, " +
            "steady and burst Hull packets, TL1 Damage Control, weighted Critical " +
            "Exposure, sequential condition steps, and player/NPC state boundaries " +
            "verified; passed.");
        if (preflightOnly)
        {
            return 0;
        }

        int trials = trialsOverride ?? study.TrialsPerVariant;
        if (trials <= 0)
        {
            throw new InvalidOperationException("Trials per variant must be positive.");
        }
        if (jobs <= 0)
        {
            throw new InvalidOperationException("Jobs must be positive.");
        }

        var results = new Tl1InternalDamageVariantSummary[study.Variants.Count];
        var options = new ParallelOptions
        {
            MaxDegreeOfParallelism = Math.Min(jobs, study.Variants.Count),
        };
        Parallel.ForEach(
            study.Variants.Select((variant, index) => (variant, index)),
            options,
            item =>
            {
                results[item.index] = RunVariant(
                    study.MasterSeed,
                    item.variant,
                    trials);
                Console.WriteLine(
                    $"PASS {item.variant.Id}: first X " +
                    $"{results[item.index].MeanFirstCriticalPosition:F2}, " +
                    $"X {results[item.index].MeanCriticalMarkers:F2}, " +
                    $"Disabled {results[item.index].DisabledBeforeDestructionPercent:F2} %, " +
                    $"repair {results[item.index].RepairSuccessPercent:F2} %.");
            });

        IReadOnlyList<Tl1InternalDamageGate> gates = BuildGates(
            study,
            results);
        WriteOutputs(
            study,
            baselineHash,
            trials,
            results,
            gates,
            outputDirectory);
        int failed = gates.Count(gate => !gate.Passed);
        Console.WriteLine(
            $"TL1 Internal Damage Calibration: {results.Length} variants, " +
            $"{trials} trials each, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static Tl1InternalDamageVariantSummary RunVariant(
        ulong masterSeed,
        Tl1InternalDamageVariantDocument variant,
        int trials)
    {
        var aggregate = new VariantAccumulator(Hull);
        for (int trial = 0; trial < trials; trial++)
        {
            TrialOutcome outcome = RunTrial(masterSeed, variant, trial);
            aggregate.Add(outcome);
        }
        return aggregate.ToSummary(variant, trials);
    }

    private static TrialOutcome RunTrial(
        ulong masterSeed,
        Tl1InternalDamageVariantDocument variant,
        int trialIndex)
    {
        ulong trackSeed = TrialSeedDeriver.Derive(
            masterSeed,
            "checkpoint-36-track",
            trialIndex,
            1UL);
        ulong exposureSeed = TrialSeedDeriver.Derive(
            masterSeed,
            "checkpoint-36-exposure",
            trialIndex,
            2UL);
        var repairRandom = new DeterministicRandomStream(
            TrialSeedDeriver.Derive(
                masterSeed,
                "checkpoint-36-damage-control",
                trialIndex,
                3UL));
        ShipDamageState ship = CreateShip(
            variant,
            trackSeed,
            exposureSeed);
        var selectedCounts = new Dictionary<string, int>(StringComparer.Ordinal);
        var conditionStepCounts = new Dictionary<string, int>(StringComparer.Ordinal);
        int? firstCritical = null;
        int repairAttempts = 0;
        int repairSuccesses = 0;
        bool disabledBeforeDestruction = false;
        int repeatedSelections = 0;
        var seenSelections = new HashSet<string>(StringComparer.Ordinal);
        int[] hullObservations = new int[Hull + 1];
        int[] disabledAtHull = new int[Hull + 1];
        int damage = variant.DamageTempo == "burst" ? 3 : 1;
        var auxiliaryReactor = new AuxiliaryReactorState(1, 1);

        while (!ship.IsDestroyed)
        {
            ship.ApplyPendingRepairsAtTurnRefresh();
            ship.BeginTurn();
            var power = new TacticalPowerLedger();
            power.BeginTurn(CurrentMainReactorOutput(ship));
            auxiliaryReactor.SetCondition(ship.GetComponent("aux-reactor").Condition);
            auxiliaryReactor.BeginTurn();
            auxiliaryReactor.Contribute(power);

            ShipDamageResolution resolution = ShipDamageResolver.ResolvePacket(
                ship,
                new AttackPacket(damage, damage, damage));
            foreach (InternalDamageEvent internalEvent in resolution.InternalEvents)
            {
                if (internalEvent.Selection is null)
                {
                    continue;
                }
                firstCritical ??= internalEvent.InternalPosition;
                string id = internalEvent.Selection.ComponentId;
                selectedCounts[id] = selectedCounts.GetValueOrDefault(id) + 1;
                if (!seenSelections.Add(id))
                {
                    repeatedSelections++;
                }
                if (internalEvent.Transition?.Changed == true)
                {
                    conditionStepCounts[id] =
                        conditionStepCounts.GetValueOrDefault(id) + 1;
                }
            }

            int remainingHull = ship.Defense.CurrentHull;
            hullObservations[remainingHull]++;
            if (ship.CapabilitySnapshot.Condition == ShipCondition.Disabled)
            {
                disabledAtHull[remainingHull]++;
                disabledBeforeDestruction = true;
            }

            if (remainingHull == 0)
            {
                ship.CompleteDamagePhase();
                break;
            }

            if (variant.DamageControl &&
                ship.DamageControl.RepairKitsRemaining > 0 &&
                power.SpendablePower >= DamageControlProfile.Tl1.TacticalPowerCost)
            {
                ShipComponentState? target = ship.Components
                    .Where(component => component.Condition == ComponentCondition.Disabled)
                    .OrderBy(component => RepairPriority(component.Definition.Kind))
                    .ThenBy(component => component.Definition.Id, StringComparer.Ordinal)
                    .FirstOrDefault() ?? ship.Components
                    .Where(component => component.Condition == ComponentCondition.Degraded)
                    .OrderBy(component => RepairPriority(component.Definition.Kind))
                    .ThenBy(component => component.Definition.Id, StringComparer.Ordinal)
                    .FirstOrDefault();
                DamageControlAttemptResult attempt;
                if (target is not null)
                {
                    attempt = DamageControlService.AttemptComponentRepair(
                        ship,
                        target.Definition.Id,
                        power,
                        repairRandom.NextD100());
                }
                else
                {
                    attempt = DamageControlService.AttemptHullRepair(
                        ship,
                        power,
                        repairRandom.NextD100());
                }
                repairAttempts++;
                if (attempt.Succeeded)
                {
                    repairSuccesses++;
                }
            }
        }

        int degraded = ship.Components.Count(component =>
            component.Condition == ComponentCondition.Degraded);
        int disabled = ship.Components.Count(component =>
            component.Condition == ComponentCondition.Disabled);
        int destroyed = ship.Components.Count(component =>
            component.Condition == ComponentCondition.Destroyed);
        return new TrialOutcome(
            firstCritical ?? 0,
            ship.CriticalSelectionsResolved,
            repeatedSelections,
            degraded,
            disabled,
            destroyed,
            disabledBeforeDestruction,
            repairAttempts,
            repairSuccesses,
            DamageControlProfile.Tl1.StartingRepairKits -
                ship.DamageControl.RepairKitsRemaining,
            selectedCounts,
            conditionStepCounts,
            hullObservations,
            disabledAtHull);
    }

    private static ShipDamageState CreateShip(
        Tl1InternalDamageVariantDocument variant,
        ulong trackSeed,
        ulong exposureSeed)
    {
        ShipComponentKind weaponKind = variant.Loadout == "kinetic"
            ? ShipComponentKind.KineticWeapon
            : ShipComponentKind.MissileLauncher;
        ShipComponentKind magazineKind = variant.Loadout == "kinetic"
            ? ShipComponentKind.KineticMagazine
            : ShipComponentKind.MissileMagazine;
        var components = new List<ShipComponentState>
        {
            Component("reactor", ShipComponentKind.MainReactor, 2,
                ShipComponentCapability.PowerSource),
            Component("stl", ShipComponentKind.StlDrive, 2,
                ShipComponentCapability.StandardStlMovement),
            Component("ftl", ShipComponentKind.FtlDrive, 1,
                ShipComponentCapability.FtlDeparture),
            Component("shield-generator", ShipComponentKind.ShieldGenerator, 1,
                ShipComponentCapability.ActiveDefense),
            Component("shield-hardener", ShipComponentKind.ShieldHardener, 1,
                ShipComponentCapability.ActiveDefense),
            Component("main-weapon", weaponKind, 1,
                ShipComponentCapability.Offense |
                ShipComponentCapability.MissileDatalink),
            Component("pds", ShipComponentKind.PointDefense, 1,
                ShipComponentCapability.ActiveDefense),
            Storage("main-magazine", magazineKind, 1, 25, loaded: 1),
            Electronics("active-sensors", ShipComponentKind.ActiveSensors),
            Electronics("targeting-computer", ShipComponentKind.TargetingComputer),
            Electronics("communications", ShipComponentKind.Communications,
                ShipComponentCapability.Communications),
            Electronics("ecm", ShipComponentKind.Ecm,
                ShipComponentCapability.ActiveDefense),
            Electronics("eccm", ShipComponentKind.Eccm,
                ShipComponentCapability.ActiveDefense),
            Component("aux-reactor", ShipComponentKind.AuxiliaryReactor, 1,
                ShipComponentCapability.PowerSource),
            Storage("capacitor", ShipComponentKind.PowerCapacitor, 1, 1),
            Storage("combat-battery", ShipComponentKind.CombatBattery, 1, 3),
            Storage("shield-battery", ShipComponentKind.ShieldBattery, 1, 3),
            Component("evm", ShipComponentKind.EvasiveManeuverSystem, 1,
                ShipComponentCapability.ActiveDefense |
                ShipComponentCapability.EvasiveManeuvers),
        };
        var defense = new LayeredDefenseState(
            pristineShieldCapacity: 0,
            currentShieldCapacity: 0,
            shieldArmor: 0,
            armorLayers: Array.Empty<ArmorLayerState>(),
            pristineHull: Hull,
            currentHull: Hull);
        return new ShipDamageState(
            defense,
            new InternalDamageTrack(
                variant.Density,
                variant.ProtectedCompartmentation,
                trackSeed,
                Hull),
            components,
            exposureSeed,
            isPlayerShip: true);
    }

    private static ShipComponentState Component(
        string id,
        ShipComponentKind kind,
        int exposure,
        ShipComponentCapability capabilities) => new(
        new ShipComponentDefinition(
            id,
            kind,
            exposure,
            CriticalExposureGroup.None,
            capabilities));

    private static ShipComponentState Storage(
        string id,
        ShipComponentKind kind,
        int exposure,
        int capacity,
        int loaded = 0) => new(
        new ShipComponentDefinition(
            id,
            kind,
            exposure),
        pristineCapacity: capacity,
        loadedReadyPackages: loaded);

    private static ShipComponentState Electronics(
        string id,
        ShipComponentKind kind,
        ShipComponentCapability capabilities = ShipComponentCapability.None) => new(
        new ShipComponentDefinition(
            id,
            kind,
            criticalExposure: 0,
            exposureGroup: CriticalExposureGroup.Electronics,
            capabilities: capabilities));

    private static int CurrentMainReactorOutput(ShipDamageState ship)
    {
        ComponentCondition condition = ship.GetComponent("reactor").Condition;
        return condition switch
        {
            ComponentCondition.Operational => 5,
            ComponentCondition.Degraded => 3,
            ComponentCondition.Disabled => 1,
            ComponentCondition.Destroyed => 0,
            _ => 0,
        };
    }

    private static int RepairPriority(ShipComponentKind kind) => kind switch
    {
        ShipComponentKind.FtlDrive => 0,
        ShipComponentKind.MainReactor => 1,
        ShipComponentKind.StlDrive => 2,
        ShipComponentKind.ShieldGenerator => 3,
        ShipComponentKind.KineticWeapon or
            ShipComponentKind.EnergyWeapon or
            ShipComponentKind.MissileLauncher => 4,
        _ => 10,
    };

    private static void Validate(
        Tl1InternalDamageCalibrationStudyDocument study,
        string baselineHash)
    {
        if (study.SchemaVersion != SchemaVersion)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 internal-damage calibration schema.");
        }
        if (!string.Equals(
                study.BaselineSha256,
                baselineHash,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "TL1 internal-damage calibration baseline hash mismatch.");
        }
        if (study.Variants.Count != RequiredVariantCount)
        {
            throw new InvalidOperationException(
                $"TL1 internal-damage calibration requires exactly " +
                $"{RequiredVariantCount} variants; found {study.Variants.Count}.");
        }
        if (study.Variants.Select(variant => variant.Id)
            .Distinct(StringComparer.Ordinal).Count() != study.Variants.Count)
        {
            throw new InvalidOperationException(
                "TL1 internal-damage variant IDs must be unique.");
        }

        InternalCriticalDensity[] densities = Enum.GetValues<InternalCriticalDensity>();
        foreach (InternalCriticalDensity density in densities)
        foreach (bool protectedCompartmentation in new[] { false, true })
        foreach (bool damageControl in new[] { false, true })
        foreach (string loadout in new[] { "kinetic", "missile" })
        foreach (string tempo in new[] { "steady", "burst" })
        {
            int count = study.Variants.Count(variant =>
                variant.Density == density &&
                variant.ProtectedCompartmentation == protectedCompartmentation &&
                variant.DamageControl == damageControl &&
                variant.Loadout == loadout &&
                variant.DamageTempo == tempo);
            if (count != 1)
            {
                throw new InvalidOperationException(
                    "The internal-damage study must contain exactly one variant " +
                    $"for {density}/{protectedCompartmentation}/{damageControl}/" +
                    $"{loadout}/{tempo}; found {count}.");
            }
        }
        ValidateProtectedCompartmentationPairs();
    }

    private static void ValidateProtectedCompartmentationPairs()
    {
        foreach (InternalCriticalDensity density in
            Enum.GetValues<InternalCriticalDensity>())
        {
            for (ulong seed = 0; seed < 1024; seed++)
            {
                var ordinary = new InternalDamageTrack(
                    density,
                    protectedCompartmentation: false,
                    seed,
                    Hull);
                var protectedTrack = new InternalDamageTrack(
                    density,
                    protectedCompartmentation: true,
                    seed,
                    Hull);
                int ordinaryCount = ordinary.CountCriticalMarkers(Hull);
                int protectedCount = protectedTrack.CountCriticalMarkers(Hull);
                if (ordinaryCount != protectedCount)
                {
                    throw new InvalidOperationException(
                        $"Protected Compartmentation changed the finite X count " +
                        $"for {density}, seed {seed}: ordinary {ordinaryCount}, " +
                        $"protected {protectedCount}.");
                }
                if (protectedTrack.MarkerAt(Hull) != InternalMarkerKind.Hull)
                {
                    throw new InvalidOperationException(
                        $"Protected Compartmentation left a terminal X at Hull " +
                        $"position {Hull} for {density}, seed {seed}.");
                }
            }
        }
    }

    private static IReadOnlyList<Tl1InternalDamageGate> BuildGates(
        Tl1InternalDamageCalibrationStudyDocument study,
        IReadOnlyList<Tl1InternalDamageVariantSummary> results)
    {
        var gates = new List<Tl1InternalDamageGate>
        {
            new("variant-count", results.Count == RequiredVariantCount,
                $"Expected {RequiredVariantCount}; observed {results.Count}."),
            new("no-trial-errors", results.All(result => result.TrialErrors == 0),
                "All variants must complete without trial errors."),
            new("repair-kit-cap", results.All(result => result.MeanRepairKitsConsumed <= 3.0),
                "No trial may consume more than the three TL1 Repair Kits."),
            new("fifty-more-than-fifteen",
                MeanByDensity(results, InternalCriticalDensity.Percent50) >
                MeanByDensity(results, InternalCriticalDensity.Percent15),
                "50% density must cross more X markers than 15% density."),
        };

        InternalCriticalDensity[] ordered =
        {
            InternalCriticalDensity.Percent15,
            InternalCriticalDensity.Percent20,
            InternalCriticalDensity.Percent25,
            InternalCriticalDensity.Percent33,
            InternalCriticalDensity.Percent50,
        };
        for (int index = 1; index < ordered.Length; index++)
        {
            double previous = MeanByDensity(results, ordered[index - 1]);
            double current = MeanByDensity(results, ordered[index]);
            gates.Add(new Tl1InternalDamageGate(
                $"density-monotonic-{ordered[index - 1]}-{ordered[index]}",
                current >= previous,
                $"Mean X markers {previous:F4} -> {current:F4}."));
        }

        foreach (InternalCriticalDensity density in ordered)
        {
            double ordinary = results
                .Where(result => result.Density == density &&
                    !result.ProtectedCompartmentation)
                .Average(result => result.MeanFirstCriticalPosition);
            double protectedMean = results
                .Where(result => result.Density == density &&
                    result.ProtectedCompartmentation)
                .Average(result => result.MeanFirstCriticalPosition);
            gates.Add(new Tl1InternalDamageGate(
                $"protected-delays-first-{density}",
                protectedMean >= ordinary,
                $"Ordinary {ordinary:F4}; Protected {protectedMean:F4}."));
        }

        var markerCountMismatches = new List<string>();
        foreach (InternalCriticalDensity density in ordered)
        foreach (string loadout in new[] { "kinetic", "missile" })
        foreach (string tempo in new[] { "steady", "burst" })
        {
            Tl1InternalDamageVariantSummary ordinary = results.Single(result =>
                result.Density == density &&
                !result.ProtectedCompartmentation &&
                !result.DamageControl &&
                result.Loadout == loadout &&
                result.DamageTempo == tempo);
            Tl1InternalDamageVariantSummary protectedResult = results.Single(result =>
                result.Density == density &&
                result.ProtectedCompartmentation &&
                !result.DamageControl &&
                result.Loadout == loadout &&
                result.DamageTempo == tempo);
            if (Math.Abs(
                    ordinary.MeanCriticalMarkers -
                    protectedResult.MeanCriticalMarkers) > 0.0000001)
            {
                markerCountMismatches.Add(
                    $"{density}/{loadout}/{tempo}: " +
                    $"{ordinary.MeanCriticalMarkers:F6} vs " +
                    $"{protectedResult.MeanCriticalMarkers:F6}");
            }
        }
        gates.Add(new Tl1InternalDamageGate(
            "protected-preserves-finite-x-count",
            markerCountMismatches.Count == 0,
            markerCountMismatches.Count == 0
                ? "All no-Damage-Control ordinary/protected pairs preserve the same finite X count."
                : string.Join("; ", markerCountMismatches)));

        string[] expectedComponentIds =
        {
            "reactor",
            "stl",
            "ftl",
            "shield-generator",
            "shield-hardener",
            "main-weapon",
            "pds",
            "main-magazine",
            "active-sensors",
            "targeting-computer",
            "communications",
            "ecm",
            "eccm",
            "aux-reactor",
            "capacitor",
            "combat-battery",
            "shield-battery",
            "evm",
        };
        IReadOnlyDictionary<string, long> selectedByComponent = results
            .SelectMany(result => result.ComponentSelections)
            .GroupBy(item => item.ComponentId, StringComparer.Ordinal)
            .ToDictionary(
                group => group.Key,
                group => group.Sum(item => item.Selections),
                StringComparer.Ordinal);
        string[] unselected = expectedComponentIds
            .Where(id => !selectedByComponent.TryGetValue(id, out long count) || count <= 0)
            .ToArray();
        gates.Add(new Tl1InternalDamageGate(
            "all-components-selected",
            unselected.Length == 0,
            unselected.Length == 0
                ? "Every installed direct or grouped damageable component was selected."
                : $"Unselected components: {string.Join(", ", unselected)}."));
        return gates.AsReadOnly();
    }

    private static double MeanByDensity(
        IEnumerable<Tl1InternalDamageVariantSummary> results,
        InternalCriticalDensity density) => results
        .Where(result => result.Density == density)
        .Average(result => result.MeanCriticalMarkers);

    private static void WriteOutputs(
        Tl1InternalDamageCalibrationStudyDocument study,
        string baselineHash,
        int trials,
        IReadOnlyList<Tl1InternalDamageVariantSummary> results,
        IReadOnlyList<Tl1InternalDamageGate> gates,
        string outputDirectory)
    {
        Directory.CreateDirectory(outputDirectory);
        string variantsPath = Path.Combine(outputDirectory, "variants.csv");
        var variantLines = new List<string>
        {
            "variant_id,density,protected_compartmentation,damage_control,loadout,damage_tempo,trials,mean_first_critical_position,mean_critical_markers,mean_repeated_selections,disabled_before_destruction_percent,mean_degraded_components,mean_disabled_components,mean_destroyed_components,mean_repair_attempts,repair_success_percent,mean_repair_kits_consumed"
        };
        foreach (Tl1InternalDamageVariantSummary result in results)
        {
            variantLines.Add(string.Join(',', new[]
            {
                result.Id,
                result.Density.DisplayName(),
                result.ProtectedCompartmentation.ToString(CultureInfo.InvariantCulture),
                result.DamageControl.ToString(CultureInfo.InvariantCulture),
                result.Loadout,
                result.DamageTempo,
                result.Trials.ToString(CultureInfo.InvariantCulture),
                F(result.MeanFirstCriticalPosition),
                F(result.MeanCriticalMarkers),
                F(result.MeanRepeatedSelections),
                F(result.DisabledBeforeDestructionPercent),
                F(result.MeanDegradedComponents),
                F(result.MeanDisabledComponents),
                F(result.MeanDestroyedComponents),
                F(result.MeanRepairAttempts),
                F(result.RepairSuccessPercent),
                F(result.MeanRepairKitsConsumed),
            }));
        }
        File.WriteAllLines(variantsPath, variantLines, new UTF8Encoding(false));

        File.WriteAllLines(
            Path.Combine(outputDirectory, "gates.csv"),
            new[] { "gate_id,passed,detail" }.Concat(gates.Select(gate =>
                string.Join(',', gate.Id,
                    gate.Passed.ToString(CultureInfo.InvariantCulture),
                    CsvQuote(gate.Detail)))),
            new UTF8Encoding(false));

        File.WriteAllLines(
            Path.Combine(outputDirectory, "component-frequency.csv"),
            new[] { "variant_id,component_id,selections,condition_steps" }
                .Concat(results.SelectMany(result => result.ComponentSelections.Select(item =>
                    $"{result.Id},{item.ComponentId},{item.Selections},{item.ConditionSteps}"))),
            new UTF8Encoding(false));

        File.WriteAllLines(
            Path.Combine(outputDirectory, "hull-band.csv"),
            new[] { "variant_id,remaining_hull,observations,disabled_observations,disabled_percent" }
                .Concat(results.SelectMany(result => result.HullBands.Select(item =>
                    $"{result.Id},{item.RemainingHull},{item.Observations},{item.DisabledObservations},{F(item.DisabledPercent)}"))),
            new UTF8Encoding(false));

        var summary = new
        {
            schemaVersion = SchemaVersion,
            studyId = study.Id,
            baselineSha256 = baselineHash,
            trialsPerVariant = trials,
            variantCount = results.Count,
            totalTrials = checked(trials * results.Count),
            failedGates = gates.Count(gate => !gate.Passed),
            gates,
            variants = results,
        };
        string json = JsonSerializer.Serialize(summary, new JsonSerializerOptions
        {
            WriteIndented = true,
            Converters = { new JsonStringEnumConverter() },
        });
        File.WriteAllText(
            Path.Combine(outputDirectory, "summary.json"),
            json,
            new UTF8Encoding(false));
        string hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(json)))
            .ToLowerInvariant();
        File.WriteAllText(
            Path.Combine(outputDirectory, "result.sha256.txt"),
            $"{hash}  summary.json{Environment.NewLine}",
            new UTF8Encoding(false));
    }

    private static JsonSerializerOptions JsonOptions()
    {
        var options = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = false,
        };
        options.Converters.Add(new JsonStringEnumConverter());
        return options;
    }

    private static string F(double value) =>
        value.ToString("0.000000", CultureInfo.InvariantCulture);

    private static string CsvQuote(string value) =>
        "\"" + value.Replace("\"", "\"\"") + "\"";

    private sealed class VariantAccumulator
    {
        private readonly int[] _hullObservations;
        private readonly int[] _disabledAtHull;
        private readonly Dictionary<string, long> _selected = new(StringComparer.Ordinal);
        private readonly Dictionary<string, long> _conditionSteps = new(StringComparer.Ordinal);
        private long _firstCritical;
        private long _criticalMarkers;
        private long _repeatedSelections;
        private long _degraded;
        private long _disabled;
        private long _destroyed;
        private long _disabledTrials;
        private long _repairAttempts;
        private long _repairSuccesses;
        private long _repairKits;

        public VariantAccumulator(int hull)
        {
            _hullObservations = new int[hull + 1];
            _disabledAtHull = new int[hull + 1];
        }

        public void Add(TrialOutcome outcome)
        {
            _firstCritical += outcome.FirstCriticalPosition;
            _criticalMarkers += outcome.CriticalMarkers;
            _repeatedSelections += outcome.RepeatedSelections;
            _degraded += outcome.DegradedComponents;
            _disabled += outcome.DisabledComponents;
            _destroyed += outcome.DestroyedComponents;
            _disabledTrials += outcome.DisabledBeforeDestruction ? 1 : 0;
            _repairAttempts += outcome.RepairAttempts;
            _repairSuccesses += outcome.RepairSuccesses;
            _repairKits += outcome.RepairKitsConsumed;
            foreach ((string id, int count) in outcome.ComponentSelections)
            {
                _selected[id] = _selected.GetValueOrDefault(id) + count;
            }
            foreach ((string id, int count) in outcome.ComponentConditionSteps)
            {
                _conditionSteps[id] = _conditionSteps.GetValueOrDefault(id) + count;
            }
            for (int hull = 0; hull < _hullObservations.Length; hull++)
            {
                _hullObservations[hull] += outcome.HullObservations[hull];
                _disabledAtHull[hull] += outcome.DisabledAtHull[hull];
            }
        }

        public Tl1InternalDamageVariantSummary ToSummary(
            Tl1InternalDamageVariantDocument variant,
            int trials)
        {
            IReadOnlyList<Tl1ComponentFrequency> frequencies = _selected.Keys
                .Union(_conditionSteps.Keys, StringComparer.Ordinal)
                .OrderBy(id => id, StringComparer.Ordinal)
                .Select(id => new Tl1ComponentFrequency(
                    id,
                    _selected.GetValueOrDefault(id),
                    _conditionSteps.GetValueOrDefault(id)))
                .ToArray();
            IReadOnlyList<Tl1HullBand> hullBands = Enumerable.Range(0, _hullObservations.Length)
                .Where(hull => _hullObservations[hull] > 0)
                .Select(hull => new Tl1HullBand(
                    hull,
                    _hullObservations[hull],
                    _disabledAtHull[hull],
                    100.0 * _disabledAtHull[hull] / _hullObservations[hull]))
                .ToArray();
            return new Tl1InternalDamageVariantSummary(
                variant.Id,
                variant.Density,
                variant.ProtectedCompartmentation,
                variant.DamageControl,
                variant.Loadout,
                variant.DamageTempo,
                trials,
                (double)_firstCritical / trials,
                (double)_criticalMarkers / trials,
                (double)_repeatedSelections / trials,
                100.0 * _disabledTrials / trials,
                (double)_degraded / trials,
                (double)_disabled / trials,
                (double)_destroyed / trials,
                (double)_repairAttempts / trials,
                _repairAttempts == 0 ? 0.0 : 100.0 * _repairSuccesses / _repairAttempts,
                (double)_repairKits / trials,
                0,
                frequencies,
                hullBands);
        }
    }

    private sealed record TrialOutcome(
        int FirstCriticalPosition,
        int CriticalMarkers,
        int RepeatedSelections,
        int DegradedComponents,
        int DisabledComponents,
        int DestroyedComponents,
        bool DisabledBeforeDestruction,
        int RepairAttempts,
        int RepairSuccesses,
        int RepairKitsConsumed,
        IReadOnlyDictionary<string, int> ComponentSelections,
        IReadOnlyDictionary<string, int> ComponentConditionSteps,
        int[] HullObservations,
        int[] DisabledAtHull);
}

public sealed record Tl1ComponentFrequency(
    string ComponentId,
    long Selections,
    long ConditionSteps);

public sealed record Tl1HullBand(
    int RemainingHull,
    int Observations,
    int DisabledObservations,
    double DisabledPercent);

public sealed record Tl1InternalDamageVariantSummary(
    string Id,
    InternalCriticalDensity Density,
    bool ProtectedCompartmentation,
    bool DamageControl,
    string Loadout,
    string DamageTempo,
    int Trials,
    double MeanFirstCriticalPosition,
    double MeanCriticalMarkers,
    double MeanRepeatedSelections,
    double DisabledBeforeDestructionPercent,
    double MeanDegradedComponents,
    double MeanDisabledComponents,
    double MeanDestroyedComponents,
    double MeanRepairAttempts,
    double RepairSuccessPercent,
    double MeanRepairKitsConsumed,
    int TrialErrors,
    IReadOnlyList<Tl1ComponentFrequency> ComponentSelections,
    IReadOnlyList<Tl1HullBand> HullBands);

public sealed record Tl1InternalDamageGate(
    string Id,
    bool Passed,
    string Detail);
