using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.ScenarioRunner.TL1Calibration;

public static class Tl1CombatPacingRunner
{
    private const string SchemaVersion = "star-cluster-tl1-combat-pacing-v1";
    private const int RequiredVariantCount = 8;
    private const int Hull = 12;
    private const int RangeHexes = 2;
    private const int MaximumTurns = 40;
    private const int LongCombatThreshold = 18;

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        int? trialsOverride,
        int jobs,
        bool preflightOnly)
    {
        Tl1CombatPacingStudyDocument study =
            JsonSerializer.Deserialize<Tl1CombatPacingStudyDocument>(
                File.ReadAllText(studyPath), JsonOptions()) ??
            throw new InvalidOperationException(
                "TL1 combat-pacing study could not be read.");
        string baselineHash = Convert.ToHexString(
                SHA256.HashData(File.ReadAllBytes(baselinePath)))
            .ToLowerInvariant();
        Validate(study, baselineHash);
        Console.WriteLine(
            "TL1 combat-pacing preflight: 8 paired mirror-duel variants; " +
            "25% and 33 1/3% internal critical densities, ordinary and " +
            "Protected Compartmentation, Damage Control off/on, five-kit " +
            "calibration allowance, simultaneous committed fire, and " +
            "start-of-turn Immobile Target snapshots verified; passed.");
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

        var results = new Tl1CombatPacingVariantSummary[study.Variants.Count];
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
                    study.MasterSeed, item.variant, trials);
                Tl1CombatPacingVariantSummary result = results[item.index];
                Console.WriteLine(
                    $"PASS {result.Id}: mean {result.MeanTurns:F2}, " +
                    $">18 turns {result.Over18TurnsPercent:F2}%, " +
                    $"mission kill {result.MissionKillPercent:F2}%, " +
                    $"immobile bonus {result.TrialsWithImmobileBonusPercent:F2}%.");
            });

        IReadOnlyList<Tl1CombatPacingGate> gates = BuildGates(results);
        WriteOutputs(
            study, baselineHash, trials, results, gates, outputDirectory);
        int failed = gates.Count(gate => !gate.Passed);
        Console.WriteLine(
            $"TL1 Combat Pacing: {results.Length} variants, {trials} trials " +
            $"each, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static Tl1CombatPacingVariantSummary RunVariant(
        ulong masterSeed,
        Tl1CombatPacingVariantDocument variant,
        int trials)
    {
        var accumulator = new PacingAccumulator();
        for (int trial = 0; trial < trials; trial++)
        {
            accumulator.Add(RunTrial(masterSeed, variant, trial));
        }
        return accumulator.ToSummary(variant, trials);
    }

    private static PacingTrialOutcome RunTrial(
        ulong masterSeed,
        Tl1CombatPacingVariantDocument variant,
        int trialIndex)
    {
        ulong salt = StableVariantSalt(variant);
        var sideA = CreateSide(
            "A",
            variant,
            TrialSeedDeriver.Derive(
                masterSeed, "checkpoint-37-pacing-track-a", trialIndex, salt),
            TrialSeedDeriver.Derive(
                masterSeed, "checkpoint-37-pacing-exposure-a", trialIndex, salt + 1UL));
        var sideB = CreateSide(
            "B",
            variant,
            TrialSeedDeriver.Derive(
                masterSeed, "checkpoint-37-pacing-track-b", trialIndex, salt + 2UL),
            TrialSeedDeriver.Derive(
                masterSeed, "checkpoint-37-pacing-exposure-b", trialIndex, salt + 3UL));
        var attackRandom = new DeterministicRandomStream(
            TrialSeedDeriver.Derive(
                masterSeed, "checkpoint-37-pacing-attacks", trialIndex, salt + 4UL));
        var repairRandomA = new DeterministicRandomStream(
            TrialSeedDeriver.Derive(
                masterSeed, "checkpoint-37-pacing-repair-a", trialIndex, salt + 5UL));
        var repairRandomB = new DeterministicRandomStream(
            TrialSeedDeriver.Derive(
                masterSeed, "checkpoint-37-pacing-repair-b", trialIndex, salt + 6UL));

        int? firstCriticalTurn = null;
        int? firstConsequentialImpairmentTurn = null;
        int? firstImmobileSnapshotTurn = null;
        int totalCriticalSelections = 0;
        int immobileBonusAttacks = 0;
        int sameTurnImmobileBonusViolations = 0;
        int repairAttempts = 0;
        int componentRepairAttempts = 0;
        int hullRepairAttempts = 0;
        int repairSuccesses = 0;
        int repairActivations = 0;
        int invalidRepairAttempts = 0;
        bool trialHadImmobileBonus = false;
        PacingResolution resolution = PacingResolution.Unresolved;
        int turns = 0;

        while (turns < MaximumTurns)
        {
            turns++;
            repairActivations += BeginSideTurn(sideA);
            repairActivations += BeginSideTurn(sideB);

            bool missionKilledA = IsMissionKilled(sideA);
            bool missionKilledB = IsMissionKilled(sideB);
            if (missionKilledA || missionKilledB)
            {
                resolution = PacingResolution.MissionKill;
                break;
            }

            bool evasiveA = TryActivateEvasiveManeuvers(sideA);
            bool evasiveB = TryActivateEvasiveManeuvers(sideB);
            SideCommitment commitmentA = CommitAttack(
                sideA, sideB, evasiveA, evasiveB, attackRandom.NextD100());
            SideCommitment commitmentB = CommitAttack(
                sideB, sideA, evasiveB, evasiveA, attackRandom.NextD100());

            if (commitmentA.TargetSnapshot.IsImmobile && commitmentA.Fired)
            {
                immobileBonusAttacks++;
                trialHadImmobileBonus = true;
                firstImmobileSnapshotTurn ??= turns;
            }
            if (commitmentB.TargetSnapshot.IsImmobile && commitmentB.Fired)
            {
                immobileBonusAttacks++;
                trialHadImmobileBonus = true;
                firstImmobileSnapshotTurn ??= turns;
            }
            if ((!commitmentA.TargetSnapshot.IsImmobile &&
                    commitmentA.TargetMobilityBonus != 0) ||
                (!commitmentB.TargetSnapshot.IsImmobile &&
                    commitmentB.TargetMobilityBonus != 0))
            {
                sameTurnImmobileBonusViolations++;
            }

            DamageApplication damageToB = ApplyCommittedAttack(
                commitmentA, sideB);
            DamageApplication damageToA = ApplyCommittedAttack(
                commitmentB, sideA);
            totalCriticalSelections +=
                damageToA.CriticalSelections + damageToB.CriticalSelections;
            if (damageToA.CriticalSelections > 0 ||
                damageToB.CriticalSelections > 0)
            {
                firstCriticalTurn ??= turns;
            }
            if (damageToA.ConsequentialConditionStep ||
                damageToB.ConsequentialConditionStep)
            {
                firstConsequentialImpairmentTurn ??= turns;
            }

            if (damageToA.StlBecameImmobileThisTurn &&
                commitmentB.TargetMobilityBonus != 0)
            {
                sameTurnImmobileBonusViolations++;
            }
            if (damageToB.StlBecameImmobileThisTurn &&
                commitmentA.TargetMobilityBonus != 0)
            {
                sameTurnImmobileBonusViolations++;
            }

            bool destroyedA = sideA.Ship.IsPendingDestruction ||
                sideA.Ship.Defense.CurrentHull == 0;
            bool destroyedB = sideB.Ship.IsPendingDestruction ||
                sideB.Ship.Defense.CurrentHull == 0;
            if (destroyedA)
            {
                sideA.Ship.CompleteDamagePhase();
            }
            if (destroyedB)
            {
                sideB.Ship.CompleteDamagePhase();
            }
            if (destroyedA || destroyedB)
            {
                resolution = PacingResolution.Destruction;
                break;
            }

            if (variant.DamageControl ==
                Tl1CombatPacingDamageControlMode.ComponentFirstReserveOne)
            {
                DamageControlTurnResult dcA = AttemptDamageControl(
                    sideA, repairRandomA);
                DamageControlTurnResult dcB = AttemptDamageControl(
                    sideB, repairRandomB);
                repairAttempts += dcA.Attempts + dcB.Attempts;
                componentRepairAttempts +=
                    dcA.ComponentAttempts + dcB.ComponentAttempts;
                hullRepairAttempts += dcA.HullAttempts + dcB.HullAttempts;
                repairSuccesses += dcA.Successes + dcB.Successes;
                invalidRepairAttempts +=
                    dcA.InvalidAttempts + dcB.InvalidAttempts;
            }

            missionKilledA = IsMissionKilled(sideA);
            missionKilledB = IsMissionKilled(sideB);
            if (missionKilledA || missionKilledB)
            {
                resolution = PacingResolution.MissionKill;
                break;
            }
        }

        return new PacingTrialOutcome(
            turns,
            resolution,
            turns > LongCombatThreshold,
            firstCriticalTurn,
            firstConsequentialImpairmentTurn,
            firstImmobileSnapshotTurn,
            totalCriticalSelections,
            immobileBonusAttacks,
            trialHadImmobileBonus,
            sameTurnImmobileBonusViolations,
            repairAttempts,
            componentRepairAttempts,
            hullRepairAttempts,
            repairSuccesses,
            repairActivations,
            invalidRepairAttempts,
            sideA.Ship.Defense.CurrentHull + sideB.Ship.Defense.CurrentHull,
            sideA.Ship.DamageControl.RepairKitsRemaining +
                sideB.Ship.DamageControl.RepairKitsRemaining);
    }

    private static int BeginSideTurn(PacingSide side)
    {
        int activations = side.Ship.PendingRepairs.Count;
        side.Ship.ApplyPendingRepairsAtTurnRefresh();
        side.Ship.BeginTurn();
        side.RecycleThisTurn = side.RecycleNextTurn;
        side.RecycleNextTurn = false;
        side.Power.BeginTurn(CurrentReactorOutput(side.Ship));
        return activations;
    }

    private static SideCommitment CommitAttack(
        PacingSide attacker,
        PacingSide target,
        bool attackerEvasive,
        bool targetEvasive,
        int roll)
    {
        ShipCombatTurnSnapshot targetSnapshot =
            ShipCombatTurnSnapshot.Capture(target.Ship);
        ShipComponentState weapon = attacker.Ship.GetComponent("main-weapon");
        ConditionedWeaponPerformance performance = ComponentPerformance.Weapon(
            WeaponFamily.Kinetic,
            weapon.Condition,
            normalDamage: 4,
            normalPowerCost: 1,
            damagePointScale: DamagePointScale.Legacy);
        ShipComponentState magazine = attacker.Ship.GetComponent("main-magazine");
        bool ammunitionAvailable =
            (magazine.Condition is ComponentCondition.Operational or
                ComponentCondition.Degraded) && magazine.CurrentContents > 0;
        bool canFire = performance.CanFire &&
            !attacker.RecycleThisTurn &&
            ammunitionAvailable &&
            attacker.Power.SpendablePower >= performance.TacticalPowerCost;
        if (!canFire)
        {
            return new SideCommitment(
                attacker.Id,
                target.Id,
                false,
                false,
                0,
                0,
                targetSnapshot,
                targetEvasive,
                attackerEvasive,
                0);
        }

        attacker.Power.Spend(performance.TacticalPowerCost);
        magazine.ConsumeContents(1);
        attacker.RecycleNextTurn = performance.RequiresFullRecycleTurnAfterFire;
        int computerBonus = ComponentPerformance.TargetingComputerBonus(
            10,
            attacker.Ship.GetComponent("targeting-computer").Condition);
        int targetEvasivePenalty = ComponentPerformance.EvasiveDefenseBonus(
            10,
            target.Ship.GetComponent("evm").Condition);
        int shooterEvasivePenalty =
            ComponentPerformance.EvasiveAttackPenaltyMagnitude(
                5,
                attacker.Ship.GetComponent("evm").Condition);
        var profile = new DirectFireAccuracyProfile(
            baseChance: 50,
            weaponAccuracy: 20,
            targetingComputerBonus: computerBonus,
            rangePenaltyPerHex: 5,
            targetEvasivePenalty: targetEvasivePenalty,
            shooterEvasivePenalty: shooterEvasivePenalty);
        DirectFireAccuracyResult accuracy = DirectFireAccuracyCalculator.Calculate(
            profile,
            RangeHexes,
            targetEvasive,
            attackerEvasive,
            targetStlCondition: targetSnapshot.StlCondition);
        DirectFireRollOutcome outcome = DirectFireHitResolver.Resolve(
            roll, accuracy.FinalChance);
        return new SideCommitment(
            attacker.Id,
            target.Id,
            true,
            DirectFireHitResolver.IsHit(outcome),
            performance.Damage,
            accuracy.FinalChance,
            targetSnapshot,
            targetEvasive,
            attackerEvasive,
            accuracy.TargetMobilityBonus);
    }

    private static bool TryActivateEvasiveManeuvers(PacingSide side)
    {
        if (!CanReserveEvasiveManeuvers(side) || side.Power.SpendablePower < 1)
        {
            return false;
        }

        ShipComponentState weapon = side.Ship.GetComponent("main-weapon");
        ShipComponentState magazine = side.Ship.GetComponent("main-magazine");
        ConditionedWeaponPerformance performance = ComponentPerformance.Weapon(
            WeaponFamily.Kinetic,
            weapon.Condition,
            normalDamage: 4,
            normalPowerCost: 1,
            damagePointScale: DamagePointScale.Legacy);
        bool attackReady = performance.CanFire &&
            !side.RecycleThisTurn &&
            (magazine.Condition is ComponentCondition.Operational or
                ComponentCondition.Degraded) &&
            magazine.CurrentContents > 0;
        if (attackReady &&
            side.Power.SpendablePower < performance.TacticalPowerCost + 1)
        {
            return false;
        }

        side.Power.Spend(1);
        return true;
    }

    private static bool CanReserveEvasiveManeuvers(PacingSide side) =>
        side.Ship.CapabilitySnapshot.HasEvasiveManeuvers &&
        side.Power.SpendablePower >= 1;

    private static DamageApplication ApplyCommittedAttack(
        SideCommitment commitment,
        PacingSide target)
    {
        if (!commitment.Fired || !commitment.Hit)
        {
            return DamageApplication.None;
        }
        ComponentCondition stlBefore =
            target.Ship.GetComponent("stl").Condition;
        ShipDamageResolution resolution = ShipDamageResolver.ResolvePacket(
            target.Ship,
            new AttackPacket(commitment.Damage, 1, 0));
        ComponentCondition stlAfter =
            target.Ship.GetComponent("stl").Condition;
        bool consequential = resolution.InternalEvents.Any(internalEvent =>
            internalEvent.Transition?.Changed == true &&
            internalEvent.Selection is not null &&
            IsConsequentialComponent(target.Ship.GetComponent(
                internalEvent.Selection.ComponentId).Definition.Kind));
        bool stlBecameImmobile =
            (stlBefore is ComponentCondition.Operational or
                ComponentCondition.Degraded) &&
            (stlAfter is ComponentCondition.Disabled or
                ComponentCondition.Destroyed);
        return new DamageApplication(
            resolution.InternalEvents.Count(internalEvent =>
                internalEvent.Selection is not null),
            consequential,
            stlBecameImmobile);
    }

    private static DamageControlTurnResult AttemptDamageControl(
        PacingSide side,
        DeterministicRandomStream repairRandom)
    {
        DamageControlEligibility eligibility =
            DamageControlService.EvaluateEligibility(side.Ship, side.Power);
        if (!eligibility.CanAttempt)
        {
            return DamageControlTurnResult.None;
        }

        ShipComponentState? component = SelectComponentRepairTarget(side.Ship);
        if (component is not null)
        {
            if (component.Condition is not
                (ComponentCondition.Degraded or ComponentCondition.Disabled))
            {
                return new DamageControlTurnResult(0, 0, 0, 0, 1);
            }
            DamageControlAttemptResult result =
                DamageControlService.AttemptComponentRepair(
                    side.Ship,
                    component.Definition.Id,
                    side.Power,
                    repairRandom.NextD100());
            return new DamageControlTurnResult(
                1, 1, 0, result.Succeeded ? 1 : 0, 0);
        }

        if (DamageControlService.HasRepairableHullDamage(side.Ship) &&
            side.Ship.Defense.CurrentHull <= Hull / 2 &&
            side.Ship.DamageControl.RepairKitsRemaining > 1)
        {
            DamageControlAttemptResult result =
                DamageControlService.AttemptHullRepair(
                    side.Ship, side.Power, repairRandom.NextD100());
            return new DamageControlTurnResult(
                1, 0, 1, result.Succeeded ? 1 : 0, 0);
        }
        return DamageControlTurnResult.None;
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

    private static bool IsMissionKilled(PacingSide side)
    {
        if (side.Ship.CapabilitySnapshot.HasOffensiveCapability)
        {
            return false;
        }
        return !side.Ship.PendingRepairs.Any(repair =>
            repair.Kind == PendingRepairKind.Component &&
            repair.ComponentId is string id &&
            side.Ship.GetComponent(id).Definition.Capabilities
                .HasFlag(ShipComponentCapability.Offense));
    }

    private static bool IsConsequentialComponent(ShipComponentKind kind) => kind is
        ShipComponentKind.MainReactor or
        ShipComponentKind.AuxiliaryReactor or
        ShipComponentKind.StlDrive or
        ShipComponentKind.KineticWeapon or
        ShipComponentKind.KineticMagazine or
        ShipComponentKind.TargetingComputer or
        ShipComponentKind.EvasiveManeuverSystem;

    private static int CurrentReactorOutput(ShipDamageState ship)
    {
        int main = ship.GetComponent("reactor").Condition switch
        {
            ComponentCondition.Operational => 5,
            ComponentCondition.Degraded => 3,
            ComponentCondition.Disabled => 1,
            ComponentCondition.Destroyed => 0,
            _ => 0,
        };
        int auxiliary = ship.GetComponent("aux-reactor").Condition switch
        {
            ComponentCondition.Operational => 1,
            _ => 0,
        };
        return main + auxiliary;
    }

    private static PacingSide CreateSide(
        string id,
        Tl1CombatPacingVariantDocument variant,
        ulong trackSeed,
        ulong exposureSeed)
    {
        var components = new[]
        {
            Component("reactor", ShipComponentKind.MainReactor, 2,
                ShipComponentCapability.PowerSource),
            Component("stl", ShipComponentKind.StlDrive, 2,
                ShipComponentCapability.StandardStlMovement),
            Component("ftl", ShipComponentKind.FtlDrive, 1,
                ShipComponentCapability.FtlDeparture),
            Component("main-weapon", ShipComponentKind.KineticWeapon, 1,
                ShipComponentCapability.Offense),
            Storage("main-magazine", ShipComponentKind.KineticMagazine, 1, 100),
            Electronics("targeting-computer", ShipComponentKind.TargetingComputer),
            Electronics("active-sensors", ShipComponentKind.ActiveSensors),
            Component("evm", ShipComponentKind.EvasiveManeuverSystem, 1,
                ShipComponentCapability.ActiveDefense |
                ShipComponentCapability.EvasiveManeuvers),
            Component("aux-reactor", ShipComponentKind.AuxiliaryReactor, 1,
                ShipComponentCapability.PowerSource),
        };
        var defense = new LayeredDefenseState(
            pristineShieldCapacity: 2,
            currentShieldCapacity: 2,
            shieldArmor: 0,
            armorLayers: new[]
            {
                new ArmorLayerState(
                    "primary-armor",
                    pristineProtection: 1,
                    currentProtection: 1,
                    pristineIntegrity: 4,
                    currentIntegrity: 4),
            },
            pristineHull: Hull,
            currentHull: Hull);
        var ship = new ShipDamageState(
            defense,
            new InternalDamageTrack(
                variant.Density,
                variant.ProtectedCompartmentation,
                trackSeed,
                Hull),
            components,
            exposureSeed,
            isPlayerShip: true,
            damageControlProfile: DamageControlProfile.Tl1CalibrationFiveKits);
        return new PacingSide(id, ship, new TacticalPowerLedger());
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
        int capacity) => new(
        new ShipComponentDefinition(id, kind, exposure),
        pristineCapacity: capacity,
        currentContents: capacity);

    private static ShipComponentState Electronics(
        string id,
        ShipComponentKind kind) => new(
        new ShipComponentDefinition(
            id,
            kind,
            criticalExposure: 0,
            exposureGroup: CriticalExposureGroup.Electronics));

    private static int RepairPriority(ShipComponentKind kind) => kind switch
    {
        ShipComponentKind.KineticWeapon => 0,
        ShipComponentKind.MainReactor => 1,
        ShipComponentKind.StlDrive => 2,
        ShipComponentKind.TargetingComputer => 3,
        ShipComponentKind.EvasiveManeuverSystem => 4,
        _ => 10,
    };

    private static ulong StableVariantSalt(
        Tl1CombatPacingVariantDocument variant)
    {
        string text = string.Join(
            "|",
            variant.Density,
            variant.ProtectedCompartmentation,
            variant.DamageControl);
        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(text));
        return BitConverter.ToUInt64(hash, 0);
    }

    private static void Validate(
        Tl1CombatPacingStudyDocument study,
        string baselineHash)
    {
        if (study.SchemaVersion != SchemaVersion)
        {
            throw new InvalidOperationException(
                "Unexpected TL1 combat-pacing schema.");
        }
        if (!string.Equals(
                study.BaselineSha256,
                baselineHash,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "TL1 combat-pacing baseline hash mismatch.");
        }
        if (study.Variants.Count != RequiredVariantCount)
        {
            throw new InvalidOperationException(
                $"TL1 combat-pacing requires exactly {RequiredVariantCount} " +
                $"variants; found {study.Variants.Count}.");
        }
        if (study.Variants.Select(variant => variant.Id)
            .Distinct(StringComparer.Ordinal).Count() != study.Variants.Count)
        {
            throw new InvalidOperationException(
                "TL1 combat-pacing variant IDs must be unique.");
        }

        foreach (InternalCriticalDensity density in new[]
        {
            InternalCriticalDensity.Percent25,
            InternalCriticalDensity.Percent33,
        })
        foreach (bool protectedCompartmentation in new[] { false, true })
        foreach (Tl1CombatPacingDamageControlMode damageControl in
            Enum.GetValues<Tl1CombatPacingDamageControlMode>())
        {
            int count = study.Variants.Count(variant =>
                variant.Density == density &&
                variant.ProtectedCompartmentation == protectedCompartmentation &&
                variant.DamageControl == damageControl);
            if (count != 1)
            {
                throw new InvalidOperationException(
                    "The combat-pacing study must contain exactly one variant " +
                    $"for {density}/{protectedCompartmentation}/{damageControl}; " +
                    $"found {count}.");
            }
        }
    }

    private static IReadOnlyList<Tl1CombatPacingGate> BuildGates(
        IReadOnlyList<Tl1CombatPacingVariantSummary> results)
    {
        const double tolerance = 0.0000001;
        return new List<Tl1CombatPacingGate>
        {
            new("variant-count", results.Count == RequiredVariantCount,
                $"Expected {RequiredVariantCount}; observed {results.Count}."),
            new("no-trial-errors", results.All(result => result.TrialErrors == 0),
                "Every mirror-duel trial must complete without an exception."),
            new("no-same-turn-immobile-bonus", results.All(result =>
                    result.SameTurnImmobileBonusViolations == 0),
                "STL loss during a simultaneous damage window must not alter " +
                "accuracy already committed that turn."),
            new("immobile-bonus-observed", results
                    .Where(result => result.Density ==
                        InternalCriticalDensity.Percent33)
                    .All(result => result.TrialsWithImmobileBonusPercent > 0.0),
                "Every 33 1/3% lane must observe following-turn Immobile " +
                "Target bonus attacks."),
            new("no-damcon-attempts-when-disabled", results
                    .Where(result => result.DamageControl ==
                        Tl1CombatPacingDamageControlMode.None)
                    .All(result => Math.Abs(result.MeanRepairAttempts) <= tolerance),
                "Damage Control-off variants must make no repair attempts."),
            new("damcon-attempts-observed", results
                    .Where(result => result.DamageControl ==
                        Tl1CombatPacingDamageControlMode.ComponentFirstReserveOne)
                    .All(result => result.MeanRepairAttempts > 0.0),
                "Every Damage Control-on variant must reach legal repair attempts."),
            new("no-invalid-repair-attempts", results.All(result =>
                    result.InvalidRepairAttempts == 0),
                "No pacing trial may attempt an ineligible repair target."),
            new("bounded-turns", results.All(result =>
                    result.P90Turns <= MaximumTurns + tolerance),
                $"P90 must remain within the {MaximumTurns}-turn simulation bound."),
            new("resolution-accounting", results.All(result =>
                    Math.Abs(result.DestructionPercent +
                        result.MissionKillPercent +
                        result.UnresolvedPercent - 100.0) <= 0.0001),
                "Destruction, mission-kill, and unresolved outcomes must total 100%."),
        }.AsReadOnly();
    }

    private static void WriteOutputs(
        Tl1CombatPacingStudyDocument study,
        string baselineHash,
        int trials,
        IReadOnlyList<Tl1CombatPacingVariantSummary> results,
        IReadOnlyList<Tl1CombatPacingGate> gates,
        string outputDirectory)
    {
        Directory.CreateDirectory(outputDirectory);
        var lines = new List<string>
        {
            "variant_id,density,protected_compartmentation,damage_control,trials,mean_turns,median_turns,p75_turns,p90_turns,over_18_turns_percent,destruction_percent,mission_kill_percent,unresolved_percent,mean_first_critical_turn,mean_first_consequential_impairment_turn,mean_first_immobile_snapshot_turn,mean_critical_selections,mean_immobile_bonus_attacks,trials_with_immobile_bonus_percent,same_turn_immobile_bonus_violations,mean_repair_attempts,mean_component_repair_attempts,mean_hull_repair_attempts,repair_success_percent,mean_repair_activations,invalid_repair_attempts,mean_combined_hull_at_end,mean_combined_kits_remaining"
        };
        foreach (Tl1CombatPacingVariantSummary result in results)
        {
            lines.Add(string.Join(',', new[]
            {
                result.Id,
                result.Density.DisplayName(),
                result.ProtectedCompartmentation.ToString(
                    CultureInfo.InvariantCulture),
                result.DamageControl.ToString(),
                result.Trials.ToString(CultureInfo.InvariantCulture),
                F(result.MeanTurns),
                F(result.MedianTurns),
                F(result.P75Turns),
                F(result.P90Turns),
                F(result.Over18TurnsPercent),
                F(result.DestructionPercent),
                F(result.MissionKillPercent),
                F(result.UnresolvedPercent),
                F(result.MeanFirstCriticalTurn),
                F(result.MeanFirstConsequentialImpairmentTurn),
                F(result.MeanFirstImmobileSnapshotTurn),
                F(result.MeanCriticalSelections),
                F(result.MeanImmobileBonusAttacks),
                F(result.TrialsWithImmobileBonusPercent),
                result.SameTurnImmobileBonusViolations.ToString(
                    CultureInfo.InvariantCulture),
                F(result.MeanRepairAttempts),
                F(result.MeanComponentRepairAttempts),
                F(result.MeanHullRepairAttempts),
                F(result.RepairSuccessPercent),
                F(result.MeanRepairActivations),
                result.InvalidRepairAttempts.ToString(
                    CultureInfo.InvariantCulture),
                F(result.MeanCombinedHullAtEnd),
                F(result.MeanCombinedRepairKitsRemaining),
            }));
        }
        File.WriteAllLines(
            Path.Combine(outputDirectory, "variants.csv"),
            lines,
            new UTF8Encoding(false));
        File.WriteAllLines(
            Path.Combine(outputDirectory, "gates.csv"),
            new[] { "gate_id,passed,detail" }.Concat(gates.Select(gate =>
                string.Join(',',
                    gate.Id,
                    gate.Passed.ToString(CultureInfo.InvariantCulture),
                    CsvQuote(gate.Detail)))),
            new UTF8Encoding(false));

        var summary = new
        {
            schemaVersion = SchemaVersion,
            studyId = study.Id,
            baselineSha256 = baselineHash,
            trialsPerVariant = trials,
            variantCount = results.Count,
            totalTrials = checked(trials * results.Count),
            maximumTurns = MaximumTurns,
            longCombatThreshold = LongCombatThreshold,
            calibrationRepairKits =
                DamageControlProfile.Tl1CalibrationFiveKits.StartingRepairKits,
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

    private sealed class PacingAccumulator
    {
        private readonly List<int> _turns = new();
        private long _longCombats;
        private long _destruction;
        private long _missionKill;
        private long _unresolved;
        private long _firstCriticalTurns;
        private long _firstCriticalObservations;
        private long _firstConsequenceTurns;
        private long _firstConsequenceObservations;
        private long _firstImmobileTurns;
        private long _firstImmobileObservations;
        private long _criticalSelections;
        private long _immobileBonusAttacks;
        private long _trialsWithImmobileBonus;
        private long _sameTurnViolations;
        private long _repairAttempts;
        private long _componentRepairAttempts;
        private long _hullRepairAttempts;
        private long _repairSuccesses;
        private long _repairActivations;
        private long _invalidRepairAttempts;
        private long _combinedHullAtEnd;
        private long _combinedKitsRemaining;

        public void Add(PacingTrialOutcome outcome)
        {
            _turns.Add(outcome.Turns);
            _longCombats += outcome.Over18Turns ? 1 : 0;
            _destruction += outcome.Resolution == PacingResolution.Destruction ? 1 : 0;
            _missionKill += outcome.Resolution == PacingResolution.MissionKill ? 1 : 0;
            _unresolved += outcome.Resolution == PacingResolution.Unresolved ? 1 : 0;
            if (outcome.FirstCriticalTurn is int firstCritical)
            {
                _firstCriticalTurns += firstCritical;
                _firstCriticalObservations++;
            }
            if (outcome.FirstConsequentialImpairmentTurn is int firstConsequence)
            {
                _firstConsequenceTurns += firstConsequence;
                _firstConsequenceObservations++;
            }
            if (outcome.FirstImmobileSnapshotTurn is int firstImmobile)
            {
                _firstImmobileTurns += firstImmobile;
                _firstImmobileObservations++;
            }
            _criticalSelections += outcome.CriticalSelections;
            _immobileBonusAttacks += outcome.ImmobileBonusAttacks;
            _trialsWithImmobileBonus += outcome.TrialHadImmobileBonus ? 1 : 0;
            _sameTurnViolations += outcome.SameTurnImmobileBonusViolations;
            _repairAttempts += outcome.RepairAttempts;
            _componentRepairAttempts += outcome.ComponentRepairAttempts;
            _hullRepairAttempts += outcome.HullRepairAttempts;
            _repairSuccesses += outcome.RepairSuccesses;
            _repairActivations += outcome.RepairActivations;
            _invalidRepairAttempts += outcome.InvalidRepairAttempts;
            _combinedHullAtEnd += outcome.CombinedHullAtEnd;
            _combinedKitsRemaining += outcome.CombinedRepairKitsRemaining;
        }

        public Tl1CombatPacingVariantSummary ToSummary(
            Tl1CombatPacingVariantDocument variant,
            int trials)
        {
            int[] ordered = _turns.OrderBy(value => value).ToArray();
            return new Tl1CombatPacingVariantSummary(
                variant.Id,
                variant.Density,
                variant.ProtectedCompartmentation,
                variant.DamageControl,
                trials,
                _turns.Average(),
                Percentile(ordered, 0.50),
                Percentile(ordered, 0.75),
                Percentile(ordered, 0.90),
                100.0 * _longCombats / trials,
                100.0 * _destruction / trials,
                100.0 * _missionKill / trials,
                100.0 * _unresolved / trials,
                MeanObserved(_firstCriticalTurns, _firstCriticalObservations),
                MeanObserved(_firstConsequenceTurns, _firstConsequenceObservations),
                MeanObserved(_firstImmobileTurns, _firstImmobileObservations),
                (double)_criticalSelections / trials,
                (double)_immobileBonusAttacks / trials,
                100.0 * _trialsWithImmobileBonus / trials,
                _sameTurnViolations,
                (double)_repairAttempts / trials,
                (double)_componentRepairAttempts / trials,
                (double)_hullRepairAttempts / trials,
                _repairAttempts == 0
                    ? 0.0
                    : 100.0 * _repairSuccesses / _repairAttempts,
                (double)_repairActivations / trials,
                _invalidRepairAttempts,
                (double)_combinedHullAtEnd / trials,
                (double)_combinedKitsRemaining / trials,
                0);
        }

        private static double MeanObserved(long total, long observations) =>
            observations == 0 ? 0.0 : (double)total / observations;

        private static double Percentile(IReadOnlyList<int> ordered, double percentile)
        {
            if (ordered.Count == 0)
            {
                return 0.0;
            }
            double index = percentile * (ordered.Count - 1);
            int lower = (int)Math.Floor(index);
            int upper = (int)Math.Ceiling(index);
            if (lower == upper)
            {
                return ordered[lower];
            }
            double fraction = index - lower;
            return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction;
        }
    }

    private sealed class PacingSide
    {
        public PacingSide(
            string id,
            ShipDamageState ship,
            TacticalPowerLedger power)
        {
            Id = id;
            Ship = ship;
            Power = power;
        }

        public string Id { get; }
        public ShipDamageState Ship { get; }
        public TacticalPowerLedger Power { get; }
        public bool RecycleThisTurn { get; set; }
        public bool RecycleNextTurn { get; set; }
    }

    private enum PacingResolution
    {
        Destruction,
        MissionKill,
        Unresolved,
    }

    private sealed record SideCommitment(
        string AttackerId,
        string TargetId,
        bool Fired,
        bool Hit,
        int Damage,
        int FinalChance,
        ShipCombatTurnSnapshot TargetSnapshot,
        bool TargetEvasive,
        bool AttackerEvasive,
        int TargetMobilityBonus);

    private sealed record DamageApplication(
        int CriticalSelections,
        bool ConsequentialConditionStep,
        bool StlBecameImmobileThisTurn)
    {
        public static DamageApplication None { get; } = new(0, false, false);
    }

    private sealed record DamageControlTurnResult(
        int Attempts,
        int ComponentAttempts,
        int HullAttempts,
        int Successes,
        int InvalidAttempts)
    {
        public static DamageControlTurnResult None { get; } = new(0, 0, 0, 0, 0);
    }

    private sealed record PacingTrialOutcome(
        int Turns,
        PacingResolution Resolution,
        bool Over18Turns,
        int? FirstCriticalTurn,
        int? FirstConsequentialImpairmentTurn,
        int? FirstImmobileSnapshotTurn,
        int CriticalSelections,
        int ImmobileBonusAttacks,
        bool TrialHadImmobileBonus,
        int SameTurnImmobileBonusViolations,
        int RepairAttempts,
        int ComponentRepairAttempts,
        int HullRepairAttempts,
        int RepairSuccesses,
        int RepairActivations,
        int InvalidRepairAttempts,
        int CombinedHullAtEnd,
        int CombinedRepairKitsRemaining);
}

public sealed record Tl1CombatPacingGate(
    string Id,
    bool Passed,
    string Detail);

public sealed record Tl1CombatPacingVariantSummary(
    string Id,
    InternalCriticalDensity Density,
    bool ProtectedCompartmentation,
    Tl1CombatPacingDamageControlMode DamageControl,
    int Trials,
    double MeanTurns,
    double MedianTurns,
    double P75Turns,
    double P90Turns,
    double Over18TurnsPercent,
    double DestructionPercent,
    double MissionKillPercent,
    double UnresolvedPercent,
    double MeanFirstCriticalTurn,
    double MeanFirstConsequentialImpairmentTurn,
    double MeanFirstImmobileSnapshotTurn,
    double MeanCriticalSelections,
    double MeanImmobileBonusAttacks,
    double TrialsWithImmobileBonusPercent,
    long SameTurnImmobileBonusViolations,
    double MeanRepairAttempts,
    double MeanComponentRepairAttempts,
    double MeanHullRepairAttempts,
    double RepairSuccessPercent,
    double MeanRepairActivations,
    long InvalidRepairAttempts,
    double MeanCombinedHullAtEnd,
    double MeanCombinedRepairKitsRemaining,
    int TrialErrors);
