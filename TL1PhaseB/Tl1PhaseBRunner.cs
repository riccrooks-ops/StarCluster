using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;
using StarCluster.ScenarioRunner.TL1;

namespace StarCluster.ScenarioRunner.TL1PhaseB;

public sealed record Tl1PhaseBCaseResult(
    string Id,
    string Name,
    string Operation,
    bool Passed,
    IReadOnlyList<string> Failures,
    object Actual);

public static class Tl1PhaseBRunner
{
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = true,
        Converters = { new JsonStringEnumConverter() },
    };

    public static int Run(
        IReadOnlyList<string> files,
        string baselinePath,
        string outputDirectory,
        bool preflightOnly)
    {
        if (files.Count == 0)
        {
            throw new InvalidOperationException(
                "No TL1 Phase B scenario files were found.");
        }

        Tl1BaselineCatalog baseline = Tl1BaselineCatalog.Load(baselinePath);
        var documents = files.Select(Read).ToArray();
        var errors = Validate(documents, baseline).ToArray();
        if (errors.Length > 0)
        {
            foreach (string error in errors)
            {
                Console.WriteLine($"FAIL {error}");
            }
            return 1;
        }

        int caseCount = documents.Sum(document => document.Cases.Count);
        Console.WriteLine(
            $"TL1 Phase B preflight: {documents.Length} scenario documents, " +
            $"{caseCount} cases, {baseline.Count}-value baseline bindings verified; passed.");
        if (preflightOnly)
        {
            return 0;
        }

        Directory.CreateDirectory(outputDirectory);
        int failed = 0;
        foreach (Tl1PhaseBScenarioDocument document in documents)
        {
            Tl1PhaseBCaseResult[] caseResults = document.Cases
                .Select(testCase => Execute(testCase, baseline))
                .ToArray();
            int failures = caseResults.Count(result => !result.Passed);
            failed += failures;
            string directory = Path.Combine(outputDirectory, document.Id);
            Directory.CreateDirectory(directory);
            File.WriteAllText(
                Path.Combine(directory, "cases.json"),
                JsonSerializer.Serialize(caseResults, Options));
            File.WriteAllText(
                Path.Combine(directory, "summary.json"),
                JsonSerializer.Serialize(new
                {
                    document.Id,
                    document.Name,
                    passed = failures == 0,
                    caseCount = caseResults.Length,
                    passedCases = caseResults.Length - failures,
                    failedCases = failures,
                    baselineSha256 = baseline.Sha256,
                    baselineValueCount = baseline.Count,
                }, Options));
            File.WriteAllLines(
                Path.Combine(directory, "results.log"),
                caseResults.Select(result =>
                    $"{(result.Passed ? "PASS" : "FAIL")} {result.Id}: " +
                    string.Join("; ", result.Failures)));
            Console.WriteLine(
                $"{(failures == 0 ? "PASS" : "FAIL")} {document.Id} " +
                $"({caseResults.Length - failures}/{caseResults.Length} cases)");
            foreach (Tl1PhaseBCaseResult result in caseResults.Where(item => !item.Passed))
            {
                foreach (string failure in result.Failures)
                {
                    Console.WriteLine($"     {result.Id}: {failure}");
                }
            }
        }

        Console.WriteLine(
            $"TL1 Phase B: {caseCount - failed} passed, {failed} failed, " +
            $"{caseCount} cases. Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static Tl1PhaseBScenarioDocument Read(string path) =>
        JsonSerializer.Deserialize<Tl1PhaseBScenarioDocument>(
            File.ReadAllText(path),
            Options) ??
        throw new InvalidOperationException(
            $"Could not read TL1 Phase B scenario '{path}'.");

    private static IEnumerable<string> Validate(
        IReadOnlyList<Tl1PhaseBScenarioDocument> documents,
        Tl1BaselineCatalog baseline)
    {
        foreach (Tl1PhaseBScenarioDocument document in documents)
        {
            if (string.IsNullOrWhiteSpace(document.Id))
            {
                yield return "scenario document missing id";
            }
            if (!string.Equals(
                    document.SchemaVersion,
                    "star-cluster-tl1-phase-b-v1",
                    StringComparison.Ordinal))
            {
                yield return $"{document.Id}: unsupported schemaVersion";
            }
            if (!string.Equals(
                    document.BaselineSha256,
                    baseline.Sha256,
                    StringComparison.OrdinalIgnoreCase))
            {
                yield return $"{document.Id}: baseline hash mismatch";
            }
            if (document.Cases.Count == 0)
            {
                yield return $"{document.Id}: contains no cases";
            }

            foreach (Tl1PhaseBCaseDocument testCase in document.Cases)
            {
                if (!string.Equals(
                        testCase.ProfileSource,
                        "baseline",
                        StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(
                        testCase.ProfileSource,
                        "explicit",
                        StringComparison.OrdinalIgnoreCase))
                {
                    yield return $"{testCase.Id}: profileSource must be baseline or explicit";
                }
                if (!IsWeaponFamily(testCase.WeaponFamily))
                {
                    yield return $"{testCase.Id}: unsupported weaponFamily '{testCase.WeaponFamily}'";
                }
                if (!IsTargetingCondition(testCase.TargetingCondition))
                {
                    yield return $"{testCase.Id}: unsupported targetingCondition '{testCase.TargetingCondition}'";
                }
                if (string.Equals(
                        testCase.ProfileSource,
                        "baseline",
                        StringComparison.OrdinalIgnoreCase))
                {
                    if (testCase.WeaponAccuracy is not null ||
                        testCase.ComputerBonus is not null ||
                        testCase.DamageA is not null ||
                        testCase.DamageB is not null ||
                        testCase.ExpectedChance is not null ||
                        testCase.ExpectedHullA is not null ||
                        testCase.ExpectedHullB is not null ||
                        testCase.ExpectedTurnsResolved is not null)
                    {
                        yield return
                            $"{testCase.Id}: baseline profile contains copied numerical overrides; " +
                            "use the baseline catalog or set profileSource to explicit";
                    }
                }
                else if (testCase.WeaponAccuracy is null ||
                         testCase.ComputerBonus is null ||
                         testCase.DamageA is null ||
                         testCase.DamageB is null)
                {
                    yield return
                        $"{testCase.Id}: explicit profile requires weaponAccuracy, " +
                        "computerBonus, damageA, and damageB";
                }

                if (testCase.Operation is Tl1PhaseBOperation.KineticMirrorDuel)
                {
                    if (!string.Equals(
                            testCase.WeaponFamily,
                            "kinetic",
                            StringComparison.OrdinalIgnoreCase))
                    {
                        yield return $"{testCase.Id}: kinetic mirror duel requires weaponFamily kinetic";
                    }
                    if (testCase.RollsA.Count < testCase.TurnCap ||
                        testCase.RollsB.Count < testCase.TurnCap)
                    {
                        yield return $"{testCase.Id}: duel roll lists must cover the turn cap";
                    }
                }
            }
        }

        string[] ids = documents
            .SelectMany(document => document.Cases)
            .Select(testCase => testCase.Id)
            .ToArray();
        if (ids.Distinct(StringComparer.Ordinal).Count() != ids.Length)
        {
            yield return "corpus contains duplicate case IDs";
        }
    }

    private static Tl1PhaseBCaseResult Execute(
        Tl1PhaseBCaseDocument testCase,
        Tl1BaselineCatalog baseline)
    {
        var failures = new List<string>();
        ResolvedProfile resolved = ResolveProfile(testCase, baseline);
        DirectFireAccuracyResult accuracy = DirectFireAccuracyCalculator.Calculate(
            resolved.Accuracy,
            testCase.RangeHexes,
            testCase.TargetEvasive,
            testCase.ShooterEvasive);
        int expectedChance = testCase.ExpectedChance ?? CalculateExpectedChance(
            resolved.Accuracy,
            testCase.RangeHexes,
            testCase.TargetEvasive,
            testCase.ShooterEvasive);
        if (accuracy.FinalChance != expectedChance)
        {
            failures.Add(
                $"chance expected {expectedChance}, actual {accuracy.FinalChance}");
        }

        string outcomeA = string.Empty;
        string outcomeB = string.Empty;
        int hullA = resolved.HullA;
        int hullB = resolved.HullB;
        bool mutual = false;
        string duelOutcome = string.Empty;
        int turnsResolved = 0;

        if (testCase.Operation is Tl1PhaseBOperation.Roll)
        {
            outcomeA = DirectFireHitResolver.Resolve(
                testCase.RollA,
                accuracy.FinalChance).ToString();
        }
        else if (testCase.Operation is Tl1PhaseBOperation.SimultaneousVolley)
        {
            DirectFireCombatant sideA = Combatant(
                "A",
                resolved.HullA,
                resolved.ReactorOutput);
            DirectFireCombatant sideB = Combatant(
                "B",
                resolved.HullB,
                resolved.ReactorOutput);
            SimultaneousDirectFireBatchResult batch =
                SimultaneousDirectFireResolver.Resolve(new[]
                {
                    new SimultaneousDirectFireOrder(
                        sideA,
                        sideB,
                        Weapon("A", resolved.DamageA, resolved.WeaponPower),
                        resolved.Accuracy,
                        testCase.RangeHexes,
                        testCase.ShooterEvasive,
                        testCase.TargetEvasive,
                        testCase.RollA),
                    new SimultaneousDirectFireOrder(
                        sideB,
                        sideA,
                        Weapon("B", resolved.DamageB, resolved.WeaponPower),
                        resolved.Accuracy,
                        testCase.RangeHexes,
                        testCase.TargetEvasive,
                        testCase.ShooterEvasive,
                        testCase.RollB),
                });
            outcomeA = batch.Attacks[0].Outcome.ToString();
            outcomeB = batch.Attacks[1].Outcome.ToString();
            hullA = sideA.Defense.CurrentHull;
            hullB = sideB.Defense.CurrentHull;
            mutual = batch.MutualDestruction;
        }
        else if (testCase.Operation is Tl1PhaseBOperation.KineticMirrorDuel)
        {
            Tl1DuelCalibrationProfile profile =
                Tl1BaselineFactory.CreateKineticDuelProfile(
                    baseline,
                    testCase.RangeHexes,
                    testCase.ShooterEvasive,
                    testCase.TargetEvasive,
                    resolved.ComputerBonus,
                    resolved.ComputerBonus,
                    testCase.TurnCap);
            var simulator = new Tl1KineticDuelSimulator(profile);
            int rollIndexA = 0;
            int rollIndexB = 0;
            Tl1CalibrationDuelResult result = simulator.Run(
                () => testCase.RollsA[rollIndexA++],
                () => testCase.RollsB[rollIndexB++]);
            duelOutcome = result.Outcome.ToString();
            turnsResolved = result.Turns;
            hullA = result.SideA.Defense.CurrentHull;
            hullB = result.SideB.Defense.CurrentHull;
        }

        if (!string.IsNullOrEmpty(testCase.ExpectedOutcomeA) &&
            !string.Equals(
                outcomeA,
                testCase.ExpectedOutcomeA,
                StringComparison.Ordinal))
        {
            failures.Add(
                $"outcomeA expected {testCase.ExpectedOutcomeA}, actual {outcomeA}");
        }
        if (!string.IsNullOrEmpty(testCase.ExpectedOutcomeB) &&
            !string.Equals(
                outcomeB,
                testCase.ExpectedOutcomeB,
                StringComparison.Ordinal))
        {
            failures.Add(
                $"outcomeB expected {testCase.ExpectedOutcomeB}, actual {outcomeB}");
        }

        if (testCase.Operation is Tl1PhaseBOperation.SimultaneousVolley)
        {
            int expectedHullA = testCase.ExpectedHullA ?? ExpectedHullAfterVolley(
                resolved.HullA,
                resolved.DamageB,
                testCase.ExpectedOutcomeB);
            int expectedHullB = testCase.ExpectedHullB ?? ExpectedHullAfterVolley(
                resolved.HullB,
                resolved.DamageA,
                testCase.ExpectedOutcomeA);
            if (hullA != expectedHullA)
            {
                failures.Add($"hullA expected {expectedHullA}, actual {hullA}");
            }
            if (hullB != expectedHullB)
            {
                failures.Add($"hullB expected {expectedHullB}, actual {hullB}");
            }
        }

        if (mutual != testCase.ExpectedMutualDestruction)
        {
            failures.Add(
                $"mutualDestruction expected {testCase.ExpectedMutualDestruction}, actual {mutual}");
        }
        if (!string.IsNullOrEmpty(testCase.ExpectedDuelOutcome) &&
            !string.Equals(
                duelOutcome,
                testCase.ExpectedDuelOutcome,
                StringComparison.Ordinal))
        {
            failures.Add(
                $"duelOutcome expected {testCase.ExpectedDuelOutcome}, actual {duelOutcome}");
        }
        if (testCase.ExpectedTurnsResolved is int expectedTurns &&
            turnsResolved != expectedTurns)
        {
            failures.Add(
                $"turnsResolved expected {expectedTurns}, actual {turnsResolved}");
        }

        return new Tl1PhaseBCaseResult(
            testCase.Id,
            testCase.Name,
            testCase.Operation.ToString(),
            failures.Count == 0,
            failures.AsReadOnly(),
            new
            {
                chance = accuracy.FinalChance,
                expectedChance,
                profileSource = testCase.ProfileSource,
                weaponFamily = testCase.WeaponFamily,
                targetingCondition = testCase.TargetingCondition,
                resolvedWeaponAccuracy = resolved.WeaponAccuracy,
                resolvedComputerBonus = resolved.ComputerBonus,
                resolvedDamageA = resolved.DamageA,
                resolvedDamageB = resolved.DamageB,
                outcomeA,
                outcomeB,
                hullA,
                hullB,
                mutualDestruction = mutual,
                duelOutcome,
                turnsResolved,
            });
    }

    private static ResolvedProfile ResolveProfile(
        Tl1PhaseBCaseDocument testCase,
        Tl1BaselineCatalog baseline)
    {
        bool baselineProfile = string.Equals(
            testCase.ProfileSource,
            "baseline",
            StringComparison.OrdinalIgnoreCase);
        int weaponAccuracy = baselineProfile
            ? baseline.GetInt(WeaponAccuracyKey(testCase.WeaponFamily))
            : testCase.WeaponAccuracy!.Value;
        int computerBonus = baselineProfile
            ? TargetingBonus(baseline, testCase.TargetingCondition)
            : testCase.ComputerBonus!.Value;
        int defaultDamage = baselineProfile
            ? baseline.GetInt(WeaponDamageKey(testCase.WeaponFamily))
            : testCase.DamageA!.Value;
        int hull = baseline.GetInt("hull_points");
        int reactorOutput = baseline.GetInt("reactor_output");
        int weaponPower = baselineProfile
            ? baseline.GetInt(WeaponPowerKey(testCase.WeaponFamily))
            : 1;
        var accuracy = new DirectFireAccuracyProfile(
            baseline.GetInt("direct_fire_base_chance"),
            weaponAccuracy,
            computerBonus,
            baseline.GetInt("direct_fire_range_penalty"),
            baseline.GetInt("target_evasive_penalty"),
            baseline.GetInt("shooter_evasive_penalty"),
            baseline.GetInt("direct_fire_minimum_chance"),
            baseline.GetInt("direct_fire_maximum_chance"));
        return new ResolvedProfile(
            accuracy,
            weaponAccuracy,
            computerBonus,
            testCase.HullA ?? hull,
            testCase.HullB ?? hull,
            testCase.DamageA ?? defaultDamage,
            testCase.DamageB ?? defaultDamage,
            reactorOutput,
            weaponPower);
    }

    private static int CalculateExpectedChance(
        DirectFireAccuracyProfile profile,
        int rangeHexes,
        bool targetEvasive,
        bool shooterEvasive)
    {
        int unbounded = profile.BaseChance +
            profile.WeaponAccuracy +
            profile.TargetingComputerBonus -
            (rangeHexes * profile.RangePenaltyPerHex) -
            (targetEvasive ? profile.TargetEvasivePenalty : 0) -
            (shooterEvasive ? profile.ShooterEvasivePenalty : 0);
        return Math.Clamp(
            unbounded,
            profile.MinimumChance,
            profile.MaximumChance);
    }

    private static int ExpectedHullAfterVolley(
        int startingHull,
        int incomingDamage,
        string expectedOutcome) =>
        IsHit(expectedOutcome)
            ? Math.Max(0, startingHull - incomingDamage)
            : startingHull;

    private static bool IsHit(string outcome) =>
        string.Equals(outcome, "Hit", StringComparison.Ordinal) ||
        string.Equals(outcome, "CriticalHit", StringComparison.Ordinal);

    private static int TargetingBonus(
        Tl1BaselineCatalog baseline,
        string condition) =>
        condition.Trim().ToLowerInvariant() switch
        {
            "operational" => baseline.GetInt("targeting_accuracy_bonus"),
            "degraded" => baseline.GetInt("targeting_degraded_bonus"),
            "disabled" or "destroyed" => 0,
            _ => throw new InvalidOperationException(
                $"Unsupported targeting condition '{condition}'."),
        };

    private static string WeaponAccuracyKey(string family) =>
        family.Trim().ToLowerInvariant() switch
        {
            "kinetic" => "kinetic_accuracy",
            "energy" => "energy_accuracy",
            _ => throw new InvalidOperationException(
                $"Unsupported direct-fire family '{family}'."),
        };

    private static string WeaponDamageKey(string family) =>
        family.Trim().ToLowerInvariant() switch
        {
            "kinetic" => "kinetic_damage",
            "energy" => "energy_standard_damage",
            _ => throw new InvalidOperationException(
                $"Unsupported direct-fire family '{family}'."),
        };

    private static string WeaponPowerKey(string family) =>
        family.Trim().ToLowerInvariant() switch
        {
            "kinetic" => "kinetic_power",
            "energy" => "energy_standard_power",
            _ => throw new InvalidOperationException(
                $"Unsupported direct-fire family '{family}'."),
        };

    private static bool IsWeaponFamily(string family) =>
        string.Equals(family, "kinetic", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(family, "energy", StringComparison.OrdinalIgnoreCase);

    private static bool IsTargetingCondition(string condition) =>
        string.Equals(condition, "operational", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(condition, "degraded", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(condition, "disabled", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(condition, "destroyed", StringComparison.OrdinalIgnoreCase);

    private static DirectFireCombatant Combatant(
        string id,
        int hull,
        int reactorOutput) => new(
        id,
        new LayeredDefenseState(
            0,
            0,
            0,
            Array.Empty<ArmorLayerState>(),
            hull,
            hull),
        CreatePowerLedger(reactorOutput),
        100,
        10);

    private static TacticalPowerLedger CreatePowerLedger(int reactorOutput)
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(reactorOutput);
        return ledger;
    }

    private static WeaponState Weapon(
        string id,
        int damage,
        int powerCost) => new(
        new WeaponProfile(
            id,
            WeaponFamily.Kinetic,
            "standard",
            new AttackPacket(damage, 0, 0),
            powerCost,
            1,
            12));

    private sealed record ResolvedProfile(
        DirectFireAccuracyProfile Accuracy,
        int WeaponAccuracy,
        int ComputerBonus,
        int HullA,
        int HullB,
        int DamageA,
        int DamageB,
        int ReactorOutput,
        int WeaponPower);
}
