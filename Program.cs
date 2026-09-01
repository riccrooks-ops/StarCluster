using StarCluster.ScenarioRunner.DamageScaling;
using StarCluster.ScenarioRunner.AuxiliaryTechnology;
using StarCluster.ScenarioRunner.TL1;
using StarCluster.ScenarioRunner.TL1PhaseB;
using StarCluster.ScenarioRunner.TL1Calibration;
using StarCluster.ScenarioRunner.TL1Architecture;
using StarCluster.ScenarioRunner.TL2Scaling;
using StarCluster.ScenarioRunner.TL1SensorEw;
using StarCluster.ScenarioRunner.CrossTlIntegration;

namespace StarCluster.ScenarioRunner;

public static class Program
{
    public static int Main(string[] args)
    {
        try
        {
            return Run(args);
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine($"ERROR: {exception}");
            return 2;
        }
    }

    private static int Run(string[] args)
    {
        string command = args.Length == 0 ? "run-all" : args[0].ToLowerInvariant();
        return command switch
        {
            "run" or "single" => RunDeterministicSingle(args),
            "run-all" => RunDeterministicAll(args),
            "batch" => RunBatch(args),
            "sweep" => RunSweep(args),
            "calibrate" => RunCalibration(args),
            "pursuit-calibrate" or "full-flight-calibrate" =>
                RunFullFlightCalibration(args),
            "allocation-profile" or "profile-allocations" =>
                RunAllocationProfile(args),
            "map-optimization-proof" or "prove-map-optimization" =>
                RunMapOptimizationProof(args),
            "tl1-phase-a-single" => RunTl1PhaseASingle(args),
            "tl1-phase-a" => RunTl1PhaseAAll(args, preflightOnly: false),
            "tl1-phase-a-preflight" => RunTl1PhaseAAll(args, preflightOnly: true),
            "tl1-phase-b" => RunTl1PhaseBAll(args, preflightOnly: false),
            "tl1-phase-b-preflight" => RunTl1PhaseBAll(args, preflightOnly: true),
            "tl1-installation-space-envelope" => RunTl1InstallationSpaceEnvelope(args, preflightOnly: false),
            "tl1-installation-space-envelope-preflight" => RunTl1InstallationSpaceEnvelope(args, preflightOnly: true),
            "cross-tl-build-permutation" => RunCrossTlBuildPermutation(args, preflightOnly: false),
            "cross-tl-build-permutation-preflight" => RunCrossTlBuildPermutation(args, preflightOnly: true),
            "tl1-kinetic-calibration" => RunTl1KineticCalibration(args, preflightOnly: false),
            "tl1-kinetic-calibration-preflight" => RunTl1KineticCalibration(args, preflightOnly: true),
            "tl1-energy-calibration" => RunTl1EnergyCalibration(args, preflightOnly: false),
            "tl1-energy-calibration-preflight" => RunTl1EnergyCalibration(args, preflightOnly: true),
            "tl1-weapon-matrix" => RunTl1WeaponMatrix(args, preflightOnly: false),
            "tl1-weapon-matrix-preflight" => RunTl1WeaponMatrix(args, preflightOnly: true),
            "tl1-pds-calibration" => RunTl1PdsCalibration(args, preflightOnly: false),
            "tl1-pds-calibration-preflight" => RunTl1PdsCalibration(args, preflightOnly: true),
            "tl1-defensive-calibration" => RunTl1DefensiveCalibration(args, preflightOnly: false),
            "tl1-defensive-calibration-preflight" => RunTl1DefensiveCalibration(args, preflightOnly: true),
            "tl1-power-envelope-calibration" => RunTl1PowerEnvelopeCalibration(args, preflightOnly: false),
            "tl1-power-envelope-calibration-preflight" => RunTl1PowerEnvelopeCalibration(args, preflightOnly: true),
            "tl1-range-control-calibration" => RunTl1RangeControlCalibration(args, preflightOnly: false),
            "tl1-range-control-calibration-preflight" => RunTl1RangeControlCalibration(args, preflightOnly: true),
            "tl1-internal-damage-calibration" => RunTl1InternalDamageCalibration(args, preflightOnly: false),
            "tl1-internal-damage-calibration-preflight" => RunTl1InternalDamageCalibration(args, preflightOnly: true),
            "tl1-damage-control-calibration" => RunTl1DamageControlCalibration(args, preflightOnly: false),
            "tl1-damage-control-calibration-preflight" => RunTl1DamageControlCalibration(args, preflightOnly: true),
            "tl1-combat-pacing" => RunTl1CombatPacing(args, preflightOnly: false),
            "tl1-combat-pacing-preflight" => RunTl1CombatPacing(args, preflightOnly: true),
            "tl1-integrated-tactical-combat" => RunTl1IntegratedTacticalCombat(args, preflightOnly: false),
            "tl1-integrated-tactical-combat-preflight" => RunTl1IntegratedTacticalCombat(args, preflightOnly: true),
            "tl1-sensor-ew-foundation" => RunTl1SensorEwFoundation(args, preflightOnly: false),
            "tl1-sensor-ew-foundation-preflight" => RunTl1SensorEwFoundation(args, preflightOnly: true),
            "auxiliary-component-foundation" => RunAuxiliaryComponentFoundation(args, preflightOnly: false),
            "auxiliary-component-foundation-preflight" => RunAuxiliaryComponentFoundation(args, preflightOnly: true),
            "auxiliary-resource-endurance" => RunAuxiliaryResourceEndurance(args, preflightOnly: false),
            "auxiliary-resource-endurance-preflight" => RunAuxiliaryResourceEndurance(args, preflightOnly: true),
            "combat-scaling-tl2" => RunCombatScalingTl2(args, preflightOnly: false),
            "combat-scaling-tl2-preflight" => RunCombatScalingTl2(args, preflightOnly: true),
            "damage-scale-parity" => RunDamageScaleParity(args),
            "self-test" => RunSelfTests(args),
            _ => throw new InvalidOperationException(Usage()),
        };
    }

    private static int RunDeterministicSingle(string[] args)
    {
        string scenarioPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "single requires a scenario JSON file path.");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-19-single");
        return RunDeterministicScenarios(
            new[] { scenarioPath },
            outputDirectory);
    }

    private static int RunDeterministicAll(string[] args)
    {
        string scenarioDirectory = GetOption(args, "--scenario-dir") ??
            Path.Combine("src", "StarCluster.ScenarioRunner", "Scenarios");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-19-deterministic");
        string[] scenarioFiles = Directory
            .GetFiles(
                scenarioDirectory,
                "*.json",
                SearchOption.TopDirectoryOnly)
            .OrderBy(path => path, StringComparer.Ordinal)
            .ToArray();
        return RunDeterministicScenarios(scenarioFiles, outputDirectory);
    }

    private static int RunBatch(string[] args)
    {
        string scenarioPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "batch requires a scenario JSON file path.");
        ScenarioDocument scenario =
            ScenarioDocumentSerialization.ReadScenario(scenarioPath);
        string variantId = GetOption(args, "--variant-id") ??
            Path.GetFileNameWithoutExtension(scenarioPath);
        var options = new MonteCarloBatchOptions
        {
            Trials = GetRequiredIntOption(args, "--trials"),
            MasterSeed = GetUlongOption(
                args,
                "--master-seed",
                checked((ulong)Math.Max(0, scenario.RandomSeed))),
            Jobs = GetIntOption(args, "--jobs", 1),
            Resume = HasFlag(args, "--resume"),
            CheckpointEvery = GetIntOption(args, "--checkpoint-every", 256),
            TraceSamples = GetIntOption(args, "--trace-samples", 0),
            KeepTrialJournal = !HasFlag(args, "--discard-trials"),
        };
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-19-batch", variantId);
        MonteCarloBatchRunResult result = MonteCarloBatchRunner.Run(
            scenario,
            variantId,
            options,
            outputDirectory);
        Console.WriteLine(
            $"Batch: {result.Results.TrialCount} trials; " +
            $"{result.Results.ErrorCount} errors; resumed {result.ResumedTrials}; " +
            $"executed {result.ExecutedTrials}. Hash: {result.ResultsSha256}. " +
            $"Output: {result.OutputDirectory}");
        return result.Passed ? 0 : 1;
    }

    private static int RunSweep(string[] args)
    {
        string sweepPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "sweep requires a sweep JSON file path.");
        SweepDocument sweep = ScenarioDocumentSerialization.ReadSweep(sweepPath);
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-19-sweep", sweep.Id);
        MonteCarloSweepRunResult result = MonteCarloSweepRunner.Run(
            sweep,
            sweepPath,
            GetIntOption(args, "--jobs", 1),
            HasFlag(args, "--resume"),
            GetIntOption(args, "--checkpoint-every", 256),
            GetIntOption(args, "--trace-samples", 0),
            outputDirectory);
        return result.Passed ? 0 : 1;
    }

    private static int RunCalibration(string[] args)
    {
        string studyPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "calibrate requires a calibration study JSON file path.");
        TechnologyCalibrationStudyDocument study =
            ScenarioDocumentSerialization.ReadCalibrationStudy(studyPath);
        string studyDirectory = Path.GetDirectoryName(Path.GetFullPath(studyPath)) ??
            throw new InvalidOperationException(
                "Calibration study directory could not be resolved.");
        string catalogPath = Path.GetFullPath(
            Path.Combine(studyDirectory, study.ProfileCatalog));
        TechnologyProfileCatalogDocument catalog =
            ScenarioDocumentSerialization.ReadTechnologyProfileCatalog(catalogPath);
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-20-calibration");
        int? trialsOverride = GetOption(args, "--trials") is string trialsText
            ? ParseInt(trialsText, "--trials")
            : null;
        TechnologyCalibrationRunResult result = TechnologyCalibrationRunner.Run(
            study,
            catalog,
            studyPath,
            GetIntOption(args, "--jobs", 1),
            trialsOverride,
            HasFlag(args, "--keep-trials"),
            outputDirectory);
        return result.Passed ? 0 : 1;
    }

    private static int RunFullFlightCalibration(string[] args)
    {
        string studyPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "pursuit-calibrate requires a full-flight study JSON file path.");
        FullFlightCalibrationStudyDocument study =
            ScenarioDocumentSerialization.ReadFullFlightCalibrationStudy(studyPath);
        string studyDirectory = Path.GetDirectoryName(Path.GetFullPath(studyPath)) ??
            throw new InvalidOperationException(
                "Full-flight study directory could not be resolved.");
        string catalogPath = Path.GetFullPath(
            Path.Combine(studyDirectory, study.ProfileCatalog));
        TechnologyProfileCatalogDocument catalog =
            ScenarioDocumentSerialization.ReadTechnologyProfileCatalog(catalogPath);
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-21-full-flight-calibration");
        int? trialsOverride = GetOption(args, "--trials") is string trialsText
            ? ParseInt(trialsText, "--trials")
            : null;
        FullFlightCalibrationRunResult result = FullFlightCalibrationRunner.Run(
            study,
            catalog,
            studyPath,
            GetIntOption(args, "--jobs", 1),
            trialsOverride,
            HasFlag(args, "--keep-trials"),
            HasFlag(args, "--scheduler-proof"),
            ParseTrialExecutionMode(
                GetOption(args, "--trial-execution") ?? "compact"),
            outputDirectory);
        return result.Passed ? 0 : 1;
    }

    private static int RunAllocationProfile(string[] args)
    {
        string studyPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "allocation-profile requires a full-flight study JSON file path.");
        FullFlightCalibrationStudyDocument study =
            ScenarioDocumentSerialization.ReadFullFlightCalibrationStudy(studyPath);
        string studyDirectory = Path.GetDirectoryName(Path.GetFullPath(studyPath)) ??
            throw new InvalidOperationException(
                "Full-flight study directory could not be resolved.");
        string catalogPath = Path.GetFullPath(
            Path.Combine(studyDirectory, study.ProfileCatalog));
        TechnologyProfileCatalogDocument catalog =
            ScenarioDocumentSerialization.ReadTechnologyProfileCatalog(catalogPath);
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-22c-allocation-profile");
        AllocationProfileRunResult result = AllocationProfileRunner.Run(
            study,
            catalog,
            GetIntOption(args, "--trials", 4),
            GetIntOption(args, "--warmup-trials", 1),
            outputDirectory);
        return result.Passed ? 0 : 1;
    }

    private static int RunMapOptimizationProof(string[] args)
    {
        string studyPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "map-optimization-proof requires a full-flight study JSON file path.");
        FullFlightCalibrationStudyDocument study =
            ScenarioDocumentSerialization.ReadFullFlightCalibrationStudy(studyPath);
        string studyDirectory = Path.GetDirectoryName(Path.GetFullPath(studyPath)) ??
            throw new InvalidOperationException(
                "Full-flight study directory could not be resolved.");
        string catalogPath = Path.GetFullPath(
            Path.Combine(studyDirectory, study.ProfileCatalog));
        TechnologyProfileCatalogDocument catalog =
            ScenarioDocumentSerialization.ReadTechnologyProfileCatalog(catalogPath);
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-22c-map-optimization-proof");
        MapOptimizationRunResult result = MapOptimizationRunner.Run(
            study,
            catalog,
            GetIntOption(args, "--parity-trials", 4),
            GetIntOption(args, "--map-measurements", 3),
            outputDirectory);
        return result.Passed ? 0 : 1;
    }

    private static int RunTl1PhaseASingle(string[] args)
    {
        string scenarioPath = args.Length >= 2
            ? args[1]
            : throw new InvalidOperationException(
                "tl1-phase-a-single requires a scenario JSON file path.");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-25-tl1-phase-a-single");
        return Tl1ScenarioCorpusRunner.Run(
            new[] { scenarioPath },
            baselinePath,
            outputDirectory,
            preflightOnly: false);
    }

    private static int RunTl1PhaseAAll(
        string[] args,
        bool preflightOnly)
    {
        string scenarioDirectory = GetOption(args, "--scenario-dir") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1PhaseA");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-25-tl1-phase-a");
        string[] scenarioFiles = Directory.GetFiles(
                scenarioDirectory,
                "*.json",
                SearchOption.TopDirectoryOnly)
            .OrderBy(path => path, StringComparer.Ordinal)
            .ToArray();
        return Tl1ScenarioCorpusRunner.Run(
            scenarioFiles,
            baselinePath,
            outputDirectory,
            preflightOnly);
    }

    private static int RunTl1PhaseBAll(string[] args, bool preflightOnly)
    {
        string scenarioDirectory = GetOption(args, "--scenario-dir") ??
            Path.Combine("src", "StarCluster.ScenarioRunner", "Scenarios", "TL1PhaseB");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-26-tl1-phase-b");
        string[] scenarioFiles = Directory.GetFiles(
                scenarioDirectory, "*.json", SearchOption.TopDirectoryOnly)
            .OrderBy(path => path, StringComparer.Ordinal)
            .ToArray();
        return Tl1PhaseBRunner.Run(
            scenarioFiles, baselinePath, outputDirectory, preflightOnly);
    }

    private static int RunTl1KineticCalibration(string[] args, bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine("src", "StarCluster.ScenarioRunner", "Scenarios", "TL1Calibration", "tl1-kc01-kinetic-interaction-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-27-tl1-kinetic-calibration");
        int? trials = GetOption(args, "--trials") is string text ? ParseInt(text, "--trials") : null;
        return Tl1KineticCalibrationRunner.Run(studyPath, baselinePath, outputDirectory, trials,
            GetIntOption(args, "--jobs", 1), preflightOnly);
    }

    private static int RunTl1EnergyCalibration(string[] args, bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine("src", "StarCluster.ScenarioRunner", "Scenarios", "TL1Calibration", "tl1-ec01-energy-interaction-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-28-tl1-energy-calibration");
        int? trials = GetOption(args, "--trials") is string text ? ParseInt(text, "--trials") : null;
        return Tl1EnergyCalibrationRunner.Run(studyPath, baselinePath, outputDirectory, trials,
            GetIntOption(args, "--jobs", 1), preflightOnly);
    }

    private static int RunTl1WeaponMatrix(string[] args, bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine("src", "StarCluster.ScenarioRunner", "Scenarios", "TL1Calibration", "tl1-wm01-complete-weapon-matrix.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-29-tl1-weapon-matrix");
        int? trials = GetOption(args, "--trials") is string text ? ParseInt(text, "--trials") : null;
        return Tl1WeaponMatrixRunner.Run(studyPath, baselinePath, outputDirectory, trials,
            GetIntOption(args, "--jobs", 1), preflightOnly);
    }

    private static int RunTl1PdsCalibration(string[] args, bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-pds01-interception-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-30-tl1-pds-calibration");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1PdsCalibrationRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }

    private static int RunTl1DefensiveCalibration(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-ds01-layered-defensive-systems-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-31-tl1-defensive-calibration");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1DefensiveCalibrationRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }

    private static int RunTl1PowerEnvelopeCalibration(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-pe02-main-power-interception-correction-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-33-tl1-power-correction-calibration");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1PowerEnvelopeCalibrationRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }


    private static int RunTl1RangeControlCalibration(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-rc01-scripted-relative-range-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-35-tl1-range-control-calibration");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1RangeControlCalibrationRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }

    private static int RunTl1InternalDamageCalibration(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-id01-internal-damage-and-damage-control-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-36-tl1-internal-damage-calibration");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1InternalDamageCalibrationRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }

    private static int RunTl1DamageControlCalibration(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-dc01-damage-control-doctrine-study.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-37-tl1-damage-control-calibration");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1DamageControlCalibrationRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }

    private static int RunTl1CombatPacing(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-cp01-critical-density-and-immobile-timing.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-37-tl1-combat-pacing");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1CombatPacingRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }

    private static int RunTl1IntegratedTacticalCombat(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL1Calibration",
                "tl1-itc01-cross-family-dynamic-range.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine(
                "out",
                "checkpoint-42-tl1-integrated-tactical-combat");
        int? trials = GetOption(args, "--trials") is string text
            ? ParseInt(text, "--trials")
            : null;
        return Tl1IntegratedTacticalCombatRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            trials,
            GetIntOption(args, "--jobs", 1),
            preflightOnly);
    }


    private static int RunTl1InstallationSpaceEnvelope(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "ArchitectureTechnology",
                "tl1-space01-35-space-construction-envelope.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-60-tl1-installation-space-envelope");
        return Tl1InstallationSpaceEnvelopeRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            preflightOnly);
    }


    private static int RunCrossTlBuildPermutation(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "ArchitectureTechnology",
                "cross-tl-build-permutation-foundation-v0_1.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_3.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-87-cross-tl-build-permutation");
        return CrossTlBuildPermutationRunner.Run(
            studyPath, baselinePath, outputDirectory, preflightOnly);
    }


    private static int RunTl1SensorEwFoundation(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "SensorEw",
                "tl1-sew02-sensor-ew-foundation-range-sweep.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_3.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-69-tl1-sensor-ew-foundation");
        return Tl1SensorEwFoundationRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            preflightOnly);
    }

    private static int RunAuxiliaryComponentFoundation(
        string[] args,
        bool preflightOnly)
    {
        string catalogPath = GetOption(args, "--catalog-file") ??
            LegacyPlayerTechnologyFile("auxiliary_component_catalog_v0_1.json");
        string schemaPath = GetOption(args, "--schema-file") ??
            LegacyPlayerTechnologyFile("auxiliary_component_catalog_schema_v0_1.json");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-43-auxiliary-component-foundation");
        return AuxiliaryComponentFoundationRunner.Run(
            catalogPath,
            schemaPath,
            outputDirectory,
            preflightOnly);
    }

    private static int RunAuxiliaryResourceEndurance(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "ArchitectureTechnology",
                "aux-end01-resource-endurance-stress.json");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-52-auxiliary-resource-endurance");
        return AuxiliaryResourceEnduranceRunner.Run(
            studyPath, outputDirectory, preflightOnly);
    }

    private static int RunCombatScalingTl2(
        string[] args,
        bool preflightOnly)
    {
        string studyPath = GetOption(args, "--study-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "TL2Scaling",
                "tl2-identity-preserving-refinement-v0_2.json");
        string baselinePath = GetOption(args, "--baseline-file") ??
            LegacyPlayerTechnologyFile("tl1_core_combat_numerical_baseline_v0_1.csv");
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-42-combat-scaling-tl2");
        return CombatScalingStudyRunner.Run(
            studyPath,
            baselinePath,
            outputDirectory,
            preflightOnly);
    }

    private static int RunSelfTests(string[] args)
    {
        string scenarioPath = GetOption(args, "--scenario-file") ??
            Path.Combine(
                "src",
                "StarCluster.ScenarioRunner",
                "Scenarios",
                "terminal-two-window-hit.json");
        return ScenarioRunnerSelfTests.Run(scenarioPath);
    }

    private static int RunDeterministicScenarios(
        IReadOnlyList<string> scenarioFiles,
        string outputDirectory)
    {
        if (scenarioFiles.Count == 0)
        {
            throw new InvalidOperationException("No scenario JSON files were found.");
        }

        IReadOnlyList<ScenarioInput> scenarios = ReadAndPreflightScenarios(
            scenarioFiles,
            outputDirectory);
        if (scenarios.Count == 0)
        {
            return 1;
        }

        int failed = 0;
        foreach (ScenarioInput scenario in scenarios)
        {
            try
            {
                ScenarioRunResult result = new ScenarioExecutor(scenario.Document).Execute();
                ScenarioOutputWriter.Write(result, outputDirectory);

                if (result.Passed)
                {
                    Console.WriteLine(
                        $"PASS {scenario.Document.Id} " +
                        $"({result.Runtime.Journal.Events.Count} events)");
                }
                else
                {
                    failed++;
                    Console.WriteLine(
                        $"FAIL {scenario.Document.Id} " +
                        $"({result.Failures.Count} assertion failures)");
                    foreach (string failure in result.Failures)
                    {
                        Console.WriteLine($"     {failure}");
                    }
                }
            }
            catch (Exception exception)
            {
                failed++;
                string fallbackId = Path.GetFileNameWithoutExtension(scenario.Path);
                WriteRunnerError(outputDirectory, fallbackId, exception.ToString());
                Console.WriteLine(
                    $"FAIL {fallbackId} (runner exception: {exception.Message})");
            }
        }

        Console.WriteLine(
            $"Scenarios: {scenarios.Count - failed} passed, {failed} failed, " +
            $"{scenarios.Count} total. Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static IReadOnlyList<ScenarioInput> ReadAndPreflightScenarios(
        IEnumerable<string> scenarioFiles,
        string outputDirectory)
    {
        var scenarios = new List<ScenarioInput>();
        var failures = new List<(string Path, string Id, string Message)>();

        foreach (string scenarioFile in scenarioFiles)
        {
            string fallbackId = Path.GetFileNameWithoutExtension(scenarioFile);
            try
            {
                ScenarioDocument document =
                    ScenarioDocumentSerialization.ReadScenario(scenarioFile);
                string scenarioId = string.IsNullOrWhiteSpace(document.Id)
                    ? fallbackId
                    : document.Id;
                IReadOnlyList<string> documentFailures =
                    ScenarioPreflightValidator.Validate(document);
                foreach (string failure in documentFailures)
                {
                    failures.Add((scenarioFile, scenarioId, failure));
                }

                scenarios.Add(new ScenarioInput(scenarioFile, document));
            }
            catch (Exception exception)
            {
                failures.Add((scenarioFile, fallbackId, exception.Message));
            }
        }

        if (failures.Count == 0)
        {
            Console.WriteLine(
                $"Scenario preflight: {scenarios.Count} passed, 0 failed.");
            return scenarios.AsReadOnly();
        }

        Console.WriteLine(
            $"Scenario preflight failed: {failures.Count} issue(s) across " +
            $"{failures.Select(item => item.Id).Distinct(StringComparer.Ordinal).Count()} " +
            "scenario(s). No scenarios were executed.");
        foreach (var group in failures.GroupBy(item => item.Id, StringComparer.Ordinal))
        {
            Console.WriteLine($"FAIL {group.Key} (preflight)");
            var report = new List<string>();
            foreach (var failure in group)
            {
                Console.WriteLine($"     {failure.Message}");
                report.Add($"Scenario file: {Path.GetFullPath(failure.Path)}");
                report.Add($"Preflight failure: {failure.Message}");
            }

            WriteRunnerError(
                outputDirectory,
                group.Key,
                string.Join(Environment.NewLine, report));
        }

        return Array.Empty<ScenarioInput>();
    }

    private static void WriteRunnerError(
        string outputDirectory,
        string scenarioId,
        string message)
    {
        string failureDirectory = Path.Combine(outputDirectory, scenarioId);
        Directory.CreateDirectory(failureDirectory);
        File.WriteAllText(
            Path.Combine(failureDirectory, "runner-error.txt"),
            message + Environment.NewLine);
    }

    private static int RunDamageScaleParity(string[] args)
    {
        string outputDirectory = GetOption(args, "--output-dir") ??
            Path.Combine("out", "checkpoint-122", "canonical-damage-scale-parity");
        return CanonicalDamageScaleParityRunner.Run(outputDirectory);
    }

    private static string LegacyPlayerTechnologyFile(string fileName) =>
        Path.Combine(
            "docs",
            "archive",
            "player_technology",
            "pre-cp165-active",
            fileName);

    private static string? GetOption(string[] args, string name)
    {
        for (int index = 0; index < args.Length - 1; index++)
        {
            if (string.Equals(args[index], name, StringComparison.OrdinalIgnoreCase))
            {
                return args[index + 1];
            }
        }

        return null;
    }

    private static bool HasFlag(string[] args, string name) =>
        args.Any(argument => string.Equals(
            argument,
            name,
            StringComparison.OrdinalIgnoreCase));

    private static int GetRequiredIntOption(string[] args, string name)
    {
        string value = GetOption(args, name) ??
            throw new InvalidOperationException($"Required option {name} was not supplied.");
        return ParseInt(value, name);
    }

    private static int GetIntOption(string[] args, string name, int defaultValue)
    {
        string? value = GetOption(args, name);
        return value is null ? defaultValue : ParseInt(value, name);
    }

    private static ulong GetUlongOption(
        string[] args,
        string name,
        ulong defaultValue)
    {
        string? value = GetOption(args, name);
        if (value is null)
        {
            return defaultValue;
        }
        if (!ulong.TryParse(
                value,
                System.Globalization.NumberStyles.Integer,
                System.Globalization.CultureInfo.InvariantCulture,
                out ulong parsed))
        {
            throw new InvalidOperationException(
                $"Option {name} requires a non-negative integer, received '{value}'.");
        }
        return parsed;
    }

    private static MonteCarloTrialExecutionMode ParseTrialExecutionMode(
        string value) => value.Trim().ToLowerInvariant() switch
        {
            "compact" or "compact-metrics" =>
                MonteCarloTrialExecutionMode.CompactMetrics,
            "diagnostic" or "diagnostic-journal" =>
                MonteCarloTrialExecutionMode.DiagnosticJournal,
            _ => throw new InvalidOperationException(
                "Option --trial-execution requires compact or diagnostic, " +
                $"received '{value}'."),
        };

    private static int ParseInt(string value, string name)
    {
        if (!int.TryParse(
                value,
                System.Globalization.NumberStyles.Integer,
                System.Globalization.CultureInfo.InvariantCulture,
                out int parsed))
        {
            throw new InvalidOperationException(
                $"Option {name} requires an integer, received '{value}'.");
        }
        return parsed;
    }

    private static string Usage() =>
        "Usage:\n" +
        "  single <scenario.json> [--output-dir DIR]\n" +
        "  run-all [--scenario-dir DIR] [--output-dir DIR]\n" +
        "  damage-scale-parity [--output-dir DIR]\n" +
        "  batch <scenario.json> --trials N [--master-seed N] [--jobs N] " +
        "[--variant-id ID] [--resume] [--checkpoint-every N] " +
        "[--trace-samples N] [--discard-trials] [--output-dir DIR]\n" +
        "  sweep <sweep.json> [--jobs N] [--resume] " +
        "[--checkpoint-every N] [--trace-samples N] [--output-dir DIR]\n" +
        "  calibrate <study.json> [--jobs N] [--trials N] [--keep-trials] " +
        "[--output-dir DIR]\n" +
        "  pursuit-calibrate <study.json> [--jobs N] [--trials N] " +
        "[--scheduler-proof] [--trial-execution compact|diagnostic] " +
        "[--keep-trials] [--output-dir DIR]\n" +
        "  allocation-profile <study.json> [--trials N] " +
        "[--warmup-trials N] [--output-dir DIR]\n" +
        "  map-optimization-proof <study.json> [--parity-trials N] " +
        "[--map-measurements N] [--output-dir DIR]\n" +
        "  tl1-phase-a-single <scenario.json> [--baseline-file FILE] " +
        "[--output-dir DIR]\n" +
        "  tl1-phase-a [--scenario-dir DIR] [--baseline-file FILE] " +
        "[--output-dir DIR]\n" +
        "  tl1-phase-a-preflight [--scenario-dir DIR] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  tl1-phase-b [--scenario-dir DIR] [--baseline-file FILE] " +
        "[--output-dir DIR]\n" +
        "  tl1-phase-b-preflight [--scenario-dir DIR] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  tl1-installation-space-envelope [--study-file FILE] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  tl1-installation-space-envelope-preflight [--study-file FILE] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  cross-tl-build-permutation [--study-file FILE] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  cross-tl-build-permutation-preflight [--study-file FILE] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  tl1-kinetic-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-energy-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-weapon-matrix [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-pds-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-defensive-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-power-envelope-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-range-control-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-internal-damage-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-damage-control-calibration [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-combat-pacing [--study-file FILE] [--trials N] " +
        "[--jobs N] [--output-dir DIR]\n" +
        "  tl1-integrated-tactical-combat [--study-file FILE] " +
        "[--trials N] [--jobs N] [--output-dir DIR]\n" +
        "  tl1-integrated-tactical-combat-preflight [--study-file FILE] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  tl1-sensor-ew-foundation [--study-file FILE] " +
        "[--baseline-file FILE] [--output-dir DIR]\n" +
        "  auxiliary-component-foundation [--catalog-file FILE] " +
        "[--schema-file FILE] [--output-dir DIR]\n" +
        "  auxiliary-resource-endurance [--study-file FILE] " +
        "[--output-dir DIR]\n" +
        "  combat-scaling-tl2 [--study-file FILE] [--baseline-file FILE] " +
        "[--output-dir DIR]\n" +
        "  self-test [--scenario-file FILE]";

    private sealed record ScenarioInput(string Path, ScenarioDocument Document);
}
