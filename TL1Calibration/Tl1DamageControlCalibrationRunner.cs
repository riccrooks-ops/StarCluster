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

public static class Tl1DamageControlCalibrationRunner
{
    private const string SchemaVersion =
        "star-cluster-tl1-damage-control-calibration-v1";
    private const int RequiredVariantCount = 64;
    private const int Hull = 12;
    private const int HullRepairThreshold = Hull / 2;

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1DamageControlCalibrationStudyDocument study =
            JsonSerializer.Deserialize<Tl1DamageControlCalibrationStudyDocument>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                "TL1 Damage Control study could not be read.");
        string baselineHash = Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselinePath)))
            .ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine(
            "TL1 Damage Control preflight: 64 variants; 25% and 33 1/3% " +
            "H/X densities, ordinary and Protected placement, four repair " +
            "doctrines, kinetic and missile loadouts, steady and burst Hull " +
            "packets, explicit repair eligibility, five calibration Repair " +
            "Kits, and separate Hull/component accounting verified; passed.");
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

        var results = new Tl1DamageControlVariantSummary[study.Variants.Count];
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
                Tl1DamageControlVariantSummary result = results[item.index];
                Console.WriteLine(
                    $"PASS {item.variant.Id}: turns {result.MeanTurns:F2}, " +
                    $"component attempts {result.MeanComponentRepairAttempts:F2}, " +
                    $"Hull attempts {result.MeanHullRepairAttempts:F2}, " +
                    $"kits {result.MeanRepairKitsConsumed:F2}.");
            });

        IReadOnlyList<Tl1DamageControlGate> gates = BuildGates(results);
        WriteOutputs(
            study,
            baselineHash,
            trials,
            results,
            gates,
            outputDirectory);
        int failed = gates.Count(gate => !gate.Passed);
        Console.WriteLine(
            $"TL1 Damage Control Calibration: {results.Length} variants, " +
            $"{trials} trials each, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static Tl1DamageControlVariantSummary RunVariant(
        ulong masterSeed,
        Tl1DamageControlVariantDocument variant,
        int trials)
    {
        var aggregate = new VariantAccumulator(Hull);
        for (int trial = 0; trial < trials; trial++)
        {
            aggregate.Add(RunTrial(masterSeed, variant, trial));
        }
        return aggregate.ToSummary(variant, trials);
    }

    private static TrialOutcome RunTrial(
        ulong masterSeed,
        Tl1DamageControlVariantDocument variant,
        int trialIndex)
    {
        ulong trackSeed = TrialSeedDeriver.Derive(
            masterSeed,
            "checkpoint-37-damage-control-track",
            trialIndex,
            StableVariantSalt(variant));
        ulong exposureSeed = TrialSeedDeriver.Derive(
            masterSeed,
            "checkpoint-37-damage-control-exposure",
            trialIndex,
            StableVariantSalt(variant) + 1UL);
        var repairRandom = new DeterministicRandomStream(
            TrialSeedDeriver.Derive(
                masterSeed,
                "checkpoint-37-damage-control-rolls",
                trialIndex,
                StableVariantSalt(variant) + 2UL));
        ShipDamageState ship = CreateShip(variant, trackSeed, exposureSeed);
        var selectedCounts = new Dictionary<string, int>(StringComparer.Ordinal);
        var conditionStepCounts = new Dictionary<string, int>(StringComparer.Ordinal);
        var repairTargets = new Dictionary<string, TrialRepairTargetCounter>(
            StringComparer.Ordinal);
        int? firstCritical = null;
        int? kitsAtFirstCritical = null;
        int repeatedSelections = 0;
        var seenSelections = new HashSet<string>(StringComparer.Ordinal);
        int[] hullObservations = new int[Hull + 1];
        int[] disabledAtHull = new int[Hull + 1];
        int damage = variant.DamageTempo == "burst" ? 3 : 1;
        var auxiliaryReactor = new AuxiliaryReactorState(1, 1);

        int turns = 0;
        int totalAttempts = 0;
        int componentAttempts = 0;
        int hullAttempts = 0;
        int degradedAttempts = 0;
        int disabledAttempts = 0;
        int componentSuccesses = 0;
        int hullSuccesses = 0;
        int degradedSuccesses = 0;
        int disabledSuccesses = 0;
        int componentActivations = 0;
        int hullActivations = 0;
        int tacticalPowerSpent = 0;
        int noRepairableDamageSkips = 0;
        int noPowerSkips = 0;
        int noKitSkips = 0;
        int doctrineDeferrals = 0;
        int invalidAttemptTargets = 0;
        int hullThresholdViolations = 0;
        int reserveOneViolations = 0;
        bool disabledBeforeDestruction = false;

        while (!ship.IsDestroyed)
        {
            turns++;
            PendingRepair[] pending = ship.PendingRepairs.ToArray();
            ship.ApplyPendingRepairsAtTurnRefresh();
            foreach (PendingRepair repair in pending)
            {
                if (repair.Kind == PendingRepairKind.Hull)
                {
                    hullActivations++;
                }
                else if (repair.ComponentId is string componentId)
                {
                    componentActivations++;
                    RepairTarget(repairTargets, componentId).Activations++;
                }
            }

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
                if (firstCritical is null)
                {
                    firstCritical = internalEvent.InternalPosition;
                    kitsAtFirstCritical = ship.DamageControl.RepairKitsRemaining;
                }
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

            if (variant.Doctrine == Tl1DamageControlDoctrine.None)
            {
                continue;
            }

            DamageControlEligibility eligibility =
                DamageControlService.EvaluateEligibility(ship, power);
            if (!eligibility.CanAttempt)
            {
                if (!eligibility.HasRepairableComponentDamage &&
                    !eligibility.HasRepairableHullDamage)
                {
                    noRepairableDamageSkips++;
                }
                if (!eligibility.HasTacticalPower)
                {
                    noPowerSkips++;
                }
                if (!eligibility.HasRepairKit)
                {
                    noKitSkips++;
                }
                continue;
            }

            ShipComponentState? target = SelectComponentRepairTarget(ship);
            DamageControlAttemptResult? attempt = null;
            ComponentCondition? targetCondition = null;
            if (target is not null)
            {
                targetCondition = target.Condition;
                if (targetCondition is not (ComponentCondition.Degraded or
                    ComponentCondition.Disabled))
                {
                    invalidAttemptTargets++;
                }
                attempt = DamageControlService.AttemptComponentRepair(
                    ship,
                    target.Definition.Id,
                    power,
                    repairRandom.NextD100());
                componentAttempts++;
                TrialRepairTargetCounter counter =
                    RepairTarget(repairTargets, target.Definition.Id);
                counter.Attempts++;
                if (targetCondition == ComponentCondition.Degraded)
                {
                    degradedAttempts++;
                    counter.DegradedAttempts++;
                }
                else if (targetCondition == ComponentCondition.Disabled)
                {
                    disabledAttempts++;
                    counter.DisabledAttempts++;
                }
                if (attempt.Succeeded)
                {
                    componentSuccesses++;
                    counter.Successes++;
                    if (targetCondition == ComponentCondition.Degraded)
                    {
                        degradedSuccesses++;
                    }
                    else if (targetCondition == ComponentCondition.Disabled)
                    {
                        disabledSuccesses++;
                    }
                }
            }
            else if (ShouldAttemptHullRepair(variant.Doctrine, ship))
            {
                int kitsBefore = ship.DamageControl.RepairKitsRemaining;
                if (ship.Defense.CurrentHull > HullRepairThreshold)
                {
                    hullThresholdViolations++;
                }
                if (variant.Doctrine ==
                        Tl1DamageControlDoctrine.HullHalfReserveOne &&
                    kitsBefore <= 1)
                {
                    reserveOneViolations++;
                }
                attempt = DamageControlService.AttemptHullRepair(
                    ship,
                    power,
                    repairRandom.NextD100());
                hullAttempts++;
                if (attempt.Succeeded)
                {
                    hullSuccesses++;
                }
            }
            else
            {
                doctrineDeferrals++;
            }

            if (attempt is not null)
            {
                totalAttempts++;
                tacticalPowerSpent += attempt.TacticalPowerSpent;
            }
        }

        int degraded = ship.Components.Count(component =>
            component.Condition == ComponentCondition.Degraded);
        int disabled = ship.Components.Count(component =>
            component.Condition == ComponentCondition.Disabled);
        int destroyed = ship.Components.Count(component =>
            component.Condition == ComponentCondition.Destroyed);
        int kitsConsumed =
            DamageControlProfile.Tl1CalibrationFiveKits.StartingRepairKits -
            ship.DamageControl.RepairKitsRemaining;
        return new TrialOutcome(
            turns,
            firstCritical ?? 0,
            kitsAtFirstCritical ??
                DamageControlProfile.Tl1CalibrationFiveKits.StartingRepairKits,
            ship.CriticalSelectionsResolved,
            repeatedSelections,
            degraded,
            disabled,
            destroyed,
            disabledBeforeDestruction,
            totalAttempts,
            componentAttempts,
            hullAttempts,
            degradedAttempts,
            disabledAttempts,
            componentSuccesses,
            hullSuccesses,
            degradedSuccesses,
            disabledSuccesses,
            componentActivations,
            hullActivations,
            kitsConsumed,
            ship.DamageControl.RepairKitsRemaining,
            tacticalPowerSpent,
            noRepairableDamageSkips,
            noPowerSkips,
            noKitSkips,
            doctrineDeferrals,
            invalidAttemptTargets,
            hullThresholdViolations,
            reserveOneViolations,
            selectedCounts,
            conditionStepCounts,
            repairTargets.ToDictionary(
                item => item.Key,
                item => item.Value.ToOutcome(),
                StringComparer.Ordinal),
            hullObservations,
            disabledAtHull);
    }

    private static bool ShouldAttemptHullRepair(
        Tl1DamageControlDoctrine doctrine,
        ShipDamageState ship)
    {
        if (!DamageControlService.HasRepairableHullDamage(ship))
        {
            return false;
        }
        if (ship.Defense.CurrentHull > HullRepairThreshold)
        {
            return false;
        }
        return doctrine switch
        {
            Tl1DamageControlDoctrine.HullHalf => true,
            Tl1DamageControlDoctrine.HullHalfReserveOne =>
                ship.DamageControl.RepairKitsRemaining > 1,
            _ => false,
        };
    }

    private static ShipComponentState? SelectComponentRepairTarget(
        ShipDamageState ship) => ship.Components
        .Where(component => component.Condition == ComponentCondition.Disabled)
        .OrderBy(component => RepairPriority(component.Definition.Kind))
        .ThenBy(component => component.Definition.Id, StringComparer.Ordinal)
        .FirstOrDefault() ?? ship.Components
        .Where(component => component.Condition == ComponentCondition.Degraded)
        .OrderBy(component => RepairPriority(component.Definition.Kind))
        .ThenBy(component => component.Definition.Id, StringComparer.Ordinal)
        .FirstOrDefault();

    private static TrialRepairTargetCounter RepairTarget(
        IDictionary<string, TrialRepairTargetCounter> targets,
        string componentId)
    {
        if (!targets.TryGetValue(componentId, out TrialRepairTargetCounter? counter))
        {
            counter = new TrialRepairTargetCounter();
            targets.Add(componentId, counter);
        }
        return counter;
    }

    private static ShipDamageState CreateShip(
        Tl1DamageControlVariantDocument variant,
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
        return new ShipDamageState(
            new LayeredDefenseState(
                0, 0, 0, Array.Empty<ArmorLayerState>(), Hull, Hull),
            new InternalDamageTrack(
                variant.Density,
                variant.ProtectedCompartmentation,
                trackSeed,
                Hull),
            components,
            exposureSeed,
            isPlayerShip: true,
            damageControlProfile: DamageControlProfile.Tl1CalibrationFiveKits);
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
        new ShipComponentDefinition(id, kind, exposure),
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

    private static int CurrentMainReactorOutput(ShipDamageState ship) =>
        ship.GetComponent("reactor").Condition switch
        {
            ComponentCondition.Operational => 5,
            ComponentCondition.Degraded => 3,
            ComponentCondition.Disabled => 1,
            ComponentCondition.Destroyed => 0,
            _ => 0,
        };

    private static int RepairPriority(ShipComponentKind kind) => kind switch
    {
        ShipComponentKind.MainReactor => 0,
        ShipComponentKind.StlDrive => 1,
        ShipComponentKind.KineticWeapon or
            ShipComponentKind.EnergyWeapon or
            ShipComponentKind.MissileLauncher => 2,
        ShipComponentKind.ShieldGenerator => 3,
        ShipComponentKind.FtlDrive => 4,
        _ => 10,
    };

    private static ulong StableVariantSalt(
        Tl1DamageControlVariantDocument variant)
    {
        string text = string.Join("|",
            variant.Density,
            variant.ProtectedCompartmentation,
            variant.Doctrine,
            variant.Loadout,
            variant.DamageTempo);
        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(text));
        return BitConverter.ToUInt64(hash, 0);
    }

    private static void Validate(
        Tl1DamageControlCalibrationStudyDocument study,
        string baselineHash)
    {
        if (study.SchemaVersion != SchemaVersion)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 Damage Control calibration schema.");
        }
        if (!string.Equals(
                study.BaselineSha256,
                baselineHash,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "TL1 Damage Control calibration baseline hash mismatch.");
        }
        if (study.Variants.Count != RequiredVariantCount)
        {
            throw new InvalidOperationException(
                $"TL1 Damage Control calibration requires exactly " +
                $"{RequiredVariantCount} variants; found {study.Variants.Count}.");
        }
        if (study.Variants.Select(variant => variant.Id)
            .Distinct(StringComparer.Ordinal).Count() != study.Variants.Count)
        {
            throw new InvalidOperationException(
                "TL1 Damage Control variant IDs must be unique.");
        }

        InternalCriticalDensity[] densities =
        {
            InternalCriticalDensity.Percent25,
            InternalCriticalDensity.Percent33,
        };
        foreach (InternalCriticalDensity density in densities)
        foreach (bool protectedCompartmentation in new[] { false, true })
        foreach (Tl1DamageControlDoctrine doctrine in
            Enum.GetValues<Tl1DamageControlDoctrine>())
        foreach (string loadout in new[] { "kinetic", "missile" })
        foreach (string tempo in new[] { "steady", "burst" })
        {
            int count = study.Variants.Count(variant =>
                variant.Density == density &&
                variant.ProtectedCompartmentation == protectedCompartmentation &&
                variant.Doctrine == doctrine &&
                variant.Loadout == loadout &&
                variant.DamageTempo == tempo);
            if (count != 1)
            {
                throw new InvalidOperationException(
                    "The Damage Control study must contain exactly one variant " +
                    $"for {density}/{protectedCompartmentation}/{doctrine}/" +
                    $"{loadout}/{tempo}; found {count}.");
            }
        }

        if (DamageControlProfile.Tl1CalibrationFiveKits.StartingRepairKits != 5)
        {
            throw new InvalidOperationException(
                "The Checkpoint 37 calibration profile must start with five Repair Kits.");
        }
    }

    private static IReadOnlyList<Tl1DamageControlGate> BuildGates(
        IReadOnlyList<Tl1DamageControlVariantSummary> results)
    {
        const double tolerance = 0.0000001;
        var gates = new List<Tl1DamageControlGate>
        {
            new("variant-count", results.Count == RequiredVariantCount,
                $"Expected {RequiredVariantCount}; observed {results.Count}."),
            new("no-trial-errors", results.All(result => result.TrialErrors == 0),
                "All variants must complete without trial errors."),
            new("five-kit-cap", results.All(result =>
                    result.MaximumRepairKitsConsumed <= 5),
                "No trial may consume more than the five calibration Repair Kits."),
            new("no-invalid-attempt-targets", results.All(result =>
                    result.MeanInvalidAttemptTargets == 0.0),
                "No attempt may be made without a repairable Hull or component target."),
            new("no-hull-threshold-violations", results.All(result =>
                    result.MeanHullThresholdViolations == 0.0),
                "Threshold doctrines may repair Hull only at six Hull or fewer."),
            new("reserve-one-preserved", results.All(result =>
                    result.MeanReserveOneViolations == 0.0),
                "The reserve-one doctrine may not spend its final kit on Hull."),
            new("none-doctrine-does-not-attempt", results
                    .Where(result => result.Doctrine == Tl1DamageControlDoctrine.None)
                    .All(result => result.MeanRepairAttempts == 0.0),
                "The no-Damage-Control doctrine must make no attempts."),
            new("component-only-never-repairs-hull", results
                    .Where(result => result.Doctrine ==
                        Tl1DamageControlDoctrine.ComponentOnly)
                    .All(result => result.MeanHullRepairAttempts == 0.0),
                "Component-only doctrine must never spend a kit on Hull."),
            new("attempts-equal-kits", results.All(result =>
                    Math.Abs(result.MeanRepairAttempts -
                        result.MeanRepairKitsConsumed) <= tolerance),
                "Every legal attempt consumes exactly one Repair Kit."),
            new("attempts-equal-tactical-power", results.All(result =>
                    Math.Abs(result.MeanRepairAttempts -
                        result.MeanTacticalPowerSpent) <= tolerance),
                "Every legal attempt consumes exactly one Tactical Power."),
            new("subsystem-attempts-observed", results
                    .Where(result => result.Doctrine != Tl1DamageControlDoctrine.None &&
                        result.Density == InternalCriticalDensity.Percent33)
                    .All(result => result.ComponentAttemptCoveragePercent > 0.0),
                "Every 33 1/3% Damage Control variant must reach subsystem repair attempts."),
            new("thirty-three-more-critical-than-twenty-five",
                results.Where(result => result.Density ==
                        InternalCriticalDensity.Percent33)
                    .Average(result => result.MeanCriticalMarkers) >
                results.Where(result => result.Density ==
                        InternalCriticalDensity.Percent25)
                    .Average(result => result.MeanCriticalMarkers),
                "33 1/3% density must cross more critical markers than 25%."),
        };

        foreach (InternalCriticalDensity density in new[]
        {
            InternalCriticalDensity.Percent25,
            InternalCriticalDensity.Percent33,
        })
        {
            double ordinary = results
                .Where(result => result.Density == density &&
                    !result.ProtectedCompartmentation)
                .Average(result => result.MeanFirstCriticalPosition);
            double protectedMean = results
                .Where(result => result.Density == density &&
                    result.ProtectedCompartmentation)
                .Average(result => result.MeanFirstCriticalPosition);
            gates.Add(new Tl1DamageControlGate(
                $"protected-delays-first-{density}",
                protectedMean >= ordinary,
                $"Ordinary {ordinary:F4}; Protected {protectedMean:F4}."));
        }
        return gates.AsReadOnly();
    }

    private static void WriteOutputs(
        Tl1DamageControlCalibrationStudyDocument study,
        string baselineHash,
        int trials,
        IReadOnlyList<Tl1DamageControlVariantSummary> results,
        IReadOnlyList<Tl1DamageControlGate> gates,
        string outputDirectory)
    {
        Directory.CreateDirectory(outputDirectory);
        var variantLines = new List<string>
        {
            "variant_id,density,protected_compartmentation,doctrine,loadout,damage_tempo,trials,mean_turns,mean_first_critical_position,mean_kits_at_first_critical,mean_critical_markers,mean_repeated_selections,disabled_before_destruction_percent,mean_degraded_components,mean_disabled_components,mean_destroyed_components,mean_repair_attempts,mean_component_attempts,mean_hull_attempts,component_success_percent,hull_success_percent,degraded_success_percent,disabled_success_percent,component_attempt_coverage_percent,mean_component_activations,mean_hull_activations,mean_repair_kits_consumed,maximum_repair_kits_consumed,mean_repair_kits_remaining,mean_tactical_power_spent,mean_no_repairable_damage_skips,mean_no_power_skips,mean_no_kit_skips,mean_doctrine_deferrals,mean_invalid_attempt_targets,mean_hull_threshold_violations,mean_reserve_one_violations"
        };
        foreach (Tl1DamageControlVariantSummary result in results)
        {
            variantLines.Add(string.Join(',', new[]
            {
                result.Id,
                result.Density.DisplayName(),
                result.ProtectedCompartmentation.ToString(CultureInfo.InvariantCulture),
                result.Doctrine.ToString(),
                result.Loadout,
                result.DamageTempo,
                result.Trials.ToString(CultureInfo.InvariantCulture),
                F(result.MeanTurns),
                F(result.MeanFirstCriticalPosition),
                F(result.MeanRepairKitsAtFirstCritical),
                F(result.MeanCriticalMarkers),
                F(result.MeanRepeatedSelections),
                F(result.DisabledBeforeDestructionPercent),
                F(result.MeanDegradedComponents),
                F(result.MeanDisabledComponents),
                F(result.MeanDestroyedComponents),
                F(result.MeanRepairAttempts),
                F(result.MeanComponentRepairAttempts),
                F(result.MeanHullRepairAttempts),
                F(result.ComponentRepairSuccessPercent),
                F(result.HullRepairSuccessPercent),
                F(result.DegradedRepairSuccessPercent),
                F(result.DisabledRepairSuccessPercent),
                F(result.ComponentAttemptCoveragePercent),
                F(result.MeanComponentRepairActivations),
                F(result.MeanHullRepairActivations),
                F(result.MeanRepairKitsConsumed),
                result.MaximumRepairKitsConsumed.ToString(
                    CultureInfo.InvariantCulture),
                F(result.MeanRepairKitsRemaining),
                F(result.MeanTacticalPowerSpent),
                F(result.MeanNoRepairableDamageSkips),
                F(result.MeanNoPowerSkips),
                F(result.MeanNoKitSkips),
                F(result.MeanDoctrineDeferrals),
                F(result.MeanInvalidAttemptTargets),
                F(result.MeanHullThresholdViolations),
                F(result.MeanReserveOneViolations),
            }));
        }
        File.WriteAllLines(
            Path.Combine(outputDirectory, "variants.csv"),
            variantLines,
            new UTF8Encoding(false));

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
                .Concat(results.SelectMany(result =>
                    result.ComponentSelections.Select(item =>
                        $"{result.Id},{item.ComponentId},{item.Selections}," +
                        $"{item.ConditionSteps}"))),
            new UTF8Encoding(false));

        File.WriteAllLines(
            Path.Combine(outputDirectory, "repair-target-frequency.csv"),
            new[]
            {
                "variant_id,component_id,attempts,degraded_attempts,disabled_attempts,successes,activations"
            }.Concat(results.SelectMany(result =>
                result.RepairTargets.Select(item =>
                    $"{result.Id},{item.ComponentId},{item.Attempts}," +
                    $"{item.DegradedAttempts},{item.DisabledAttempts}," +
                    $"{item.Successes},{item.Activations}"))),
            new UTF8Encoding(false));

        File.WriteAllLines(
            Path.Combine(outputDirectory, "hull-band.csv"),
            new[]
            {
                "variant_id,remaining_hull,observations,disabled_observations,disabled_percent"
            }.Concat(results.SelectMany(result => result.HullBands.Select(item =>
                $"{result.Id},{item.RemainingHull},{item.Observations}," +
                $"{item.DisabledObservations},{F(item.DisabledPercent)}"))),
            new UTF8Encoding(false));

        var summary = new
        {
            schemaVersion = SchemaVersion,
            studyId = study.Id,
            baselineSha256 = baselineHash,
            trialsPerVariant = trials,
            variantCount = results.Count,
            totalTrials = checked(trials * results.Count),
            calibrationRepairKits =
                DamageControlProfile.Tl1CalibrationFiveKits.StartingRepairKits,
            hullRepairThreshold = HullRepairThreshold,
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
        string hash = Convert.ToHexString(
                SHA256.HashData(Encoding.UTF8.GetBytes(json)))
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

    private sealed class TrialRepairTargetCounter
    {
        public int Attempts { get; set; }
        public int DegradedAttempts { get; set; }
        public int DisabledAttempts { get; set; }
        public int Successes { get; set; }
        public int Activations { get; set; }

        public TrialRepairTargetOutcome ToOutcome() => new(
            Attempts,
            DegradedAttempts,
            DisabledAttempts,
            Successes,
            Activations);
    }

    private sealed class VariantAccumulator
    {
        private readonly int[] _hullObservations;
        private readonly int[] _disabledAtHull;
        private readonly Dictionary<string, long> _selected = new(StringComparer.Ordinal);
        private readonly Dictionary<string, long> _conditionSteps = new(StringComparer.Ordinal);
        private readonly Dictionary<string, RepairTargetTotals> _repairTargets =
            new(StringComparer.Ordinal);
        private long _turns;
        private long _firstCritical;
        private long _kitsAtFirstCritical;
        private long _criticalMarkers;
        private long _repeatedSelections;
        private long _degraded;
        private long _disabled;
        private long _destroyed;
        private long _disabledTrials;
        private long _repairAttempts;
        private long _componentAttempts;
        private long _hullAttempts;
        private long _degradedAttempts;
        private long _disabledAttempts;
        private long _componentSuccesses;
        private long _hullSuccesses;
        private long _degradedSuccesses;
        private long _disabledSuccesses;
        private long _componentActivations;
        private long _hullActivations;
        private long _repairKitsConsumed;
        private int _maximumRepairKitsConsumed;
        private long _repairKitsRemaining;
        private long _tacticalPowerSpent;
        private long _noRepairableDamageSkips;
        private long _noPowerSkips;
        private long _noKitSkips;
        private long _doctrineDeferrals;
        private long _invalidAttemptTargets;
        private long _hullThresholdViolations;
        private long _reserveOneViolations;
        private long _trialsWithComponentAttempt;

        public VariantAccumulator(int hull)
        {
            _hullObservations = new int[hull + 1];
            _disabledAtHull = new int[hull + 1];
        }

        public void Add(TrialOutcome outcome)
        {
            _turns += outcome.Turns;
            _firstCritical += outcome.FirstCriticalPosition;
            _kitsAtFirstCritical += outcome.RepairKitsAtFirstCritical;
            _criticalMarkers += outcome.CriticalMarkers;
            _repeatedSelections += outcome.RepeatedSelections;
            _degraded += outcome.DegradedComponents;
            _disabled += outcome.DisabledComponents;
            _destroyed += outcome.DestroyedComponents;
            _disabledTrials += outcome.DisabledBeforeDestruction ? 1 : 0;
            _repairAttempts += outcome.RepairAttempts;
            _componentAttempts += outcome.ComponentRepairAttempts;
            _hullAttempts += outcome.HullRepairAttempts;
            _degradedAttempts += outcome.DegradedRepairAttempts;
            _disabledAttempts += outcome.DisabledRepairAttempts;
            _componentSuccesses += outcome.ComponentRepairSuccesses;
            _hullSuccesses += outcome.HullRepairSuccesses;
            _degradedSuccesses += outcome.DegradedRepairSuccesses;
            _disabledSuccesses += outcome.DisabledRepairSuccesses;
            _componentActivations += outcome.ComponentRepairActivations;
            _hullActivations += outcome.HullRepairActivations;
            _repairKitsConsumed += outcome.RepairKitsConsumed;
            _maximumRepairKitsConsumed = Math.Max(
                _maximumRepairKitsConsumed,
                outcome.RepairKitsConsumed);
            _repairKitsRemaining += outcome.RepairKitsRemaining;
            _tacticalPowerSpent += outcome.TacticalPowerSpent;
            _noRepairableDamageSkips += outcome.NoRepairableDamageSkips;
            _noPowerSkips += outcome.NoPowerSkips;
            _noKitSkips += outcome.NoKitSkips;
            _doctrineDeferrals += outcome.DoctrineDeferrals;
            _invalidAttemptTargets += outcome.InvalidAttemptTargets;
            _hullThresholdViolations += outcome.HullThresholdViolations;
            _reserveOneViolations += outcome.ReserveOneViolations;
            _trialsWithComponentAttempt += outcome.ComponentRepairAttempts > 0 ? 1 : 0;
            foreach ((string id, int count) in outcome.ComponentSelections)
            {
                _selected[id] = _selected.GetValueOrDefault(id) + count;
            }
            foreach ((string id, int count) in outcome.ComponentConditionSteps)
            {
                _conditionSteps[id] =
                    _conditionSteps.GetValueOrDefault(id) + count;
            }
            foreach ((string id, TrialRepairTargetOutcome target) in
                outcome.RepairTargets)
            {
                if (!_repairTargets.TryGetValue(id, out RepairTargetTotals? totals))
                {
                    totals = new RepairTargetTotals();
                    _repairTargets.Add(id, totals);
                }
                totals.Add(target);
            }
            for (int hull = 0; hull < _hullObservations.Length; hull++)
            {
                _hullObservations[hull] += outcome.HullObservations[hull];
                _disabledAtHull[hull] += outcome.DisabledAtHull[hull];
            }
        }

        public Tl1DamageControlVariantSummary ToSummary(
            Tl1DamageControlVariantDocument variant,
            int trials)
        {
            IReadOnlyList<Tl1DamageControlComponentFrequency> frequencies =
                _selected.Keys
                    .Union(_conditionSteps.Keys, StringComparer.Ordinal)
                    .OrderBy(id => id, StringComparer.Ordinal)
                    .Select(id => new Tl1DamageControlComponentFrequency(
                        id,
                        _selected.GetValueOrDefault(id),
                        _conditionSteps.GetValueOrDefault(id)))
                    .ToArray();
            IReadOnlyList<Tl1DamageControlRepairTargetFrequency> repairTargets =
                _repairTargets
                    .OrderBy(item => item.Key, StringComparer.Ordinal)
                    .Select(item => item.Value.ToFrequency(item.Key))
                    .ToArray();
            IReadOnlyList<Tl1DamageControlHullBand> hullBands =
                Enumerable.Range(0, _hullObservations.Length)
                    .Where(hull => _hullObservations[hull] > 0)
                    .Select(hull => new Tl1DamageControlHullBand(
                        hull,
                        _hullObservations[hull],
                        _disabledAtHull[hull],
                        100.0 * _disabledAtHull[hull] /
                            _hullObservations[hull]))
                    .ToArray();
            return new Tl1DamageControlVariantSummary(
                variant.Id,
                variant.Density,
                variant.ProtectedCompartmentation,
                variant.Doctrine,
                variant.Loadout,
                variant.DamageTempo,
                trials,
                (double)_turns / trials,
                (double)_firstCritical / trials,
                (double)_kitsAtFirstCritical / trials,
                (double)_criticalMarkers / trials,
                (double)_repeatedSelections / trials,
                100.0 * _disabledTrials / trials,
                (double)_degraded / trials,
                (double)_disabled / trials,
                (double)_destroyed / trials,
                (double)_repairAttempts / trials,
                (double)_componentAttempts / trials,
                (double)_hullAttempts / trials,
                Percent(_componentSuccesses, _componentAttempts),
                Percent(_hullSuccesses, _hullAttempts),
                Percent(_degradedSuccesses, _degradedAttempts),
                Percent(_disabledSuccesses, _disabledAttempts),
                100.0 * _trialsWithComponentAttempt / trials,
                (double)_componentActivations / trials,
                (double)_hullActivations / trials,
                (double)_repairKitsConsumed / trials,
                _maximumRepairKitsConsumed,
                (double)_repairKitsRemaining / trials,
                (double)_tacticalPowerSpent / trials,
                (double)_noRepairableDamageSkips / trials,
                (double)_noPowerSkips / trials,
                (double)_noKitSkips / trials,
                (double)_doctrineDeferrals / trials,
                (double)_invalidAttemptTargets / trials,
                (double)_hullThresholdViolations / trials,
                (double)_reserveOneViolations / trials,
                0,
                frequencies,
                repairTargets,
                hullBands);
        }

        private static double Percent(long numerator, long denominator) =>
            denominator == 0 ? 0.0 : 100.0 * numerator / denominator;
    }

    private sealed class RepairTargetTotals
    {
        private long _attempts;
        private long _degradedAttempts;
        private long _disabledAttempts;
        private long _successes;
        private long _activations;

        public void Add(TrialRepairTargetOutcome outcome)
        {
            _attempts += outcome.Attempts;
            _degradedAttempts += outcome.DegradedAttempts;
            _disabledAttempts += outcome.DisabledAttempts;
            _successes += outcome.Successes;
            _activations += outcome.Activations;
        }

        public Tl1DamageControlRepairTargetFrequency ToFrequency(
            string componentId) => new(
            componentId,
            _attempts,
            _degradedAttempts,
            _disabledAttempts,
            _successes,
            _activations);
    }

    private sealed record TrialRepairTargetOutcome(
        int Attempts,
        int DegradedAttempts,
        int DisabledAttempts,
        int Successes,
        int Activations);

    private sealed record TrialOutcome(
        int Turns,
        int FirstCriticalPosition,
        int RepairKitsAtFirstCritical,
        int CriticalMarkers,
        int RepeatedSelections,
        int DegradedComponents,
        int DisabledComponents,
        int DestroyedComponents,
        bool DisabledBeforeDestruction,
        int RepairAttempts,
        int ComponentRepairAttempts,
        int HullRepairAttempts,
        int DegradedRepairAttempts,
        int DisabledRepairAttempts,
        int ComponentRepairSuccesses,
        int HullRepairSuccesses,
        int DegradedRepairSuccesses,
        int DisabledRepairSuccesses,
        int ComponentRepairActivations,
        int HullRepairActivations,
        int RepairKitsConsumed,
        int RepairKitsRemaining,
        int TacticalPowerSpent,
        int NoRepairableDamageSkips,
        int NoPowerSkips,
        int NoKitSkips,
        int DoctrineDeferrals,
        int InvalidAttemptTargets,
        int HullThresholdViolations,
        int ReserveOneViolations,
        IReadOnlyDictionary<string, int> ComponentSelections,
        IReadOnlyDictionary<string, int> ComponentConditionSteps,
        IReadOnlyDictionary<string, TrialRepairTargetOutcome> RepairTargets,
        int[] HullObservations,
        int[] DisabledAtHull);
}

public sealed record Tl1DamageControlComponentFrequency(
    string ComponentId,
    long Selections,
    long ConditionSteps);

public sealed record Tl1DamageControlRepairTargetFrequency(
    string ComponentId,
    long Attempts,
    long DegradedAttempts,
    long DisabledAttempts,
    long Successes,
    long Activations);

public sealed record Tl1DamageControlHullBand(
    int RemainingHull,
    int Observations,
    int DisabledObservations,
    double DisabledPercent);

public sealed record Tl1DamageControlVariantSummary(
    string Id,
    InternalCriticalDensity Density,
    bool ProtectedCompartmentation,
    Tl1DamageControlDoctrine Doctrine,
    string Loadout,
    string DamageTempo,
    int Trials,
    double MeanTurns,
    double MeanFirstCriticalPosition,
    double MeanRepairKitsAtFirstCritical,
    double MeanCriticalMarkers,
    double MeanRepeatedSelections,
    double DisabledBeforeDestructionPercent,
    double MeanDegradedComponents,
    double MeanDisabledComponents,
    double MeanDestroyedComponents,
    double MeanRepairAttempts,
    double MeanComponentRepairAttempts,
    double MeanHullRepairAttempts,
    double ComponentRepairSuccessPercent,
    double HullRepairSuccessPercent,
    double DegradedRepairSuccessPercent,
    double DisabledRepairSuccessPercent,
    double ComponentAttemptCoveragePercent,
    double MeanComponentRepairActivations,
    double MeanHullRepairActivations,
    double MeanRepairKitsConsumed,
    int MaximumRepairKitsConsumed,
    double MeanRepairKitsRemaining,
    double MeanTacticalPowerSpent,
    double MeanNoRepairableDamageSkips,
    double MeanNoPowerSkips,
    double MeanNoKitSkips,
    double MeanDoctrineDeferrals,
    double MeanInvalidAttemptTargets,
    double MeanHullThresholdViolations,
    double MeanReserveOneViolations,
    int TrialErrors,
    IReadOnlyList<Tl1DamageControlComponentFrequency> ComponentSelections,
    IReadOnlyList<Tl1DamageControlRepairTargetFrequency> RepairTargets,
    IReadOnlyList<Tl1DamageControlHullBand> HullBands);

public sealed record Tl1DamageControlGate(
    string Id,
    bool Passed,
    string Detail);
