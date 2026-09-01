using System.Text.Json;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tactics;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Combat.Weapons;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using StarCluster.Core.Diagnostics;
using StarCluster.ScenarioRunner.TL2Scaling;
using StarCluster.ScenarioRunner.CrossTlIntegration;

namespace StarCluster.ScenarioRunner;

public static class ScenarioRunnerSelfTests
{
    public static int Run(string scenarioPath)
    {
        var tests = new List<(string Name, Action Body)>
        {
            ("seed derivation is stable", TestStableSeed),
            ("trial indexes receive different seeds", TestDifferentTrialSeeds),
            ("random stream IDs are separated", TestSeparatedStreams),
            ("deterministic random streams replay", TestRandomReplay),
            ("Wilson interval bounds are valid", TestWilsonInterval),
            ("scenario overrides update typed documents", TestOverride),
            ("worker counts produce identical results", () => TestWorkerIndependence(scenarioPath)),
            ("resume extension matches a fresh run", () => TestResume(scenarioPath)),
            ("PDS TL calibration is bounded and directional", TestCalibrationPdsChance),
            ("seeker-only acquisition responds to net ECM", TestCalibrationAcquisition),
            ("representative calibration matrix has stable cardinality", () => TestCalibrationMatrix(scenarioPath)),
            ("effective-hit aggregation includes ordinary and critical hits", TestEffectiveHitMetric),
            ("common random numbers align different variants", () => TestCommonRandomNumbers(scenarioPath)),
            ("paired binary differences preserve discordant counts", TestPairedBinaryDifference),
            ("Holm adjustment controls the marginal family", TestHolmAdjustment),
            ("practical-effect threshold suppresses trivial contradictions", TestPracticalEffectThreshold),
            ("full-flight matrix has stable cardinality", TestFullFlightMatrix),
            ("full-flight movement policies materialize deterministic routes", TestFullFlightMovementPolicies),
            ("occluded datalink variants seed valid prior flight state", TestFullFlightOcclusionSeed),
            ("full-flight scenarios stop after terminal resolution", TestFullFlightStopContract),
            ("full-flight matrix covers relative speed classes", TestFullFlightRelativeSpeedCoverage),
            ("full-flight variants pair live and occluded datalinks", TestFullFlightDatalinkPairs),
            ("full-flight safety caps scale with missile endurance", TestFullFlightSafetyTurnCap),
            ("crossing-weave is distinct and deterministic", TestFullFlightCrossingWeave),
            ("target-entered missile hex creates an authoritative opportunity", TestTargetEnteredMissileOpportunity),
            ("terminal opportunity diagnostics match authoritative records", TestOpportunityDiagnosticsMatchAuthority),
            ("operational safety caps classify stalled missiles", TestOperationalSafetyCapClassification),
            ("full-flight scenarios materialize operational turn limits", TestOperationalTurnLimitMaterialization),
            ("global trial scheduler honors the 24-worker ceiling", TestVariantWorkerCeiling),
            ("trial-block sizing preserves bounded granularity", TestTrialBlockSizing),
            ("trial blocks cover every variant trial exactly once", TestTrialBlockCoverage),
            ("scenario runner uses server garbage collection", TestServerGarbageCollection),
            ("candidate-coordinate Search/Wait is not terminal acquisition", () =>
                TestCandidateCoordinateSearchDiagnostic(scenarioPath)),
            ("discarded trial journals retain error details", () =>
                TestDiscardedJournalRetainsErrors(scenarioPath)),
            ("scheduler proof corpus has twenty-four stable variants", TestSchedulerProofCorpus),
            ("relative-motion datalink comparisons can be descriptive", TestDescriptiveDatalinkPolicies),
            ("semantic occlusion permits resolution before a guidance update", TestSemanticOcclusionContract),
            ("scenario execution plans reuse immutable preparation", () =>
                TestScenarioExecutionPlanReuse(scenarioPath)),
            ("compact and diagnostic trials preserve identical outcomes", () =>
                TestCompactDiagnosticParity(scenarioPath)),
            ("compact trials suppress diagnostic journal materialization", () =>
                TestCompactJournalSuppression(scenarioPath)),
            ("compact track refresh preserves authoritative final state", () =>
                TestCompactTrackRefreshParity(scenarioPath)),
            ("profiled trials preserve canonical outcomes",
                TestProfiledTrialParity),
            ("allocation attribution records a bounded stage hierarchy",
                TestAllocationStageHierarchy),
            ("optimized calibration maps are bounded and deterministic",
                TestOptimizedCalibrationMapSizing),
            ("optimized and reference maps preserve canonical trial outcomes",
                TestOptimizedReferenceMapParity),
            ("initialization attribution isolates map creation",
                TestInitializationStageAttribution),
            ("CP74 firm-reference gate distinguishes EW contamination from later sensor damage",
                TestCp74FirmReferenceGateSemantics),
            ("CP81 Tactical Computer override preserves local PDS base and missile guidance",
                TestCp81TacticalComputerOverrideSemantics),
            ("CP84 Shield Capacity override preserves recharge, armor, reactor, and weapons",
                TestCp84ShieldCapacityOverrideSemantics),
            ("CP85 Armor AP/AI overrides are independent and preserve shield, reactor, and weapons",
                TestCp85ArmorOverrideSemantics),
            ("CP86 weapon penetration override changes only the selected family SPEN/APEN",
                TestCp86WeaponPenetrationOverrideSemantics),
            ("CP87 cross-TL Cartesian enumeration preserves the 512-build foundation envelope",
                TestCp87CrossTlCartesianFoundation),
            ("CP88 legal-build guardrail requires a Main Weapon and a Reactor without banning explicit duplication",
                TestCp88MinimumCombatCoreGuardrail),
            ("CP88 EW affordability uses actual rated normal power cost",
                TestCp88RatedEwAffordability),
            ("CP90 generalized cross-TL Cartesian foundation expands multiplicity and progression strata",
                TestCp90GeneralizedCrossTlFoundation),
            ("CP90 redundant ECM/ECCM resolves highest functional rating without additive stacking",
                TestCp90NonAdditiveEwRedundancy),
            ("CP93 matched cross-TL strata and distinct-pair arithmetic remain deterministic",
                TestCp93MatchedCrossTlStrata),
            ("CP94 adaptive cross-TL quotas and information-control bands remain deterministic",
                TestCp94AdaptiveCrossTlSampling),
            ("CP96 readiness cohorts separate reference context, observed ready windows, and runtime bilateral activity",
                TestCp96ReadinessCohortSemantics),
            ("CP97 pre-contact search advances one hex toward center without target input",
                TestCp97EncounterSearch),
            ("CP97 failed overload memory blocks same-or-farther retry but permits closer retry",
                TestCp97OverloadRangeMemory),
            ("CP97 material observable-state change re-enables a failed overload",
                TestCp97OverloadMaterialStateChange),
            ("CP99 normal combat construction requires an installed Sensor in addition to a Main Weapon and Reactor",
                TestCp99MandatorySensorCombatCore),
            ("CP102 TL3 construction semantics preserve variable Hull capacity and Shield-Hardener compatibility",
                TestCp102ConstructionSemantics),
            ("CP102 TL3 dual Active sensor modes are normal data-driven 1/2-TP operating modes",
                TestCp102DualActiveSensorModes),
            ("CP102 TL3 full-strength Rating-2 EW costs 1 TP without changing legacy per-rating semantics",
                TestCp102FullStrengthEwEfficiency),
            ("CP102 TL3 Evasive Compensation only offsets the firing ship own Evasive penalty",
                TestCp102EvasiveCompensation),
            ("CP102 TL3 weapon power and Energy rated-mode overrides remain executable and family-local",
                TestCp102EnergyRatedModes),
            ("CP102 TL3 AMM readiness supports RC1 at 1 TP and RC2 at 2 TP",
                TestCp102AmmReadiness),
            ("CP102 PDS ammunition bridge preserves frozen legacy Kinetic semantics and explicit v7 family semantics",
                TestCp102PdsAmmunitionBridge),
        };

        int passed = 0;
        foreach ((string name, Action body) in tests)
        {
            try
            {
                body();
                passed++;
                Console.WriteLine($"PASS self-test: {name}");
            }
            catch (Exception exception)
            {
                Console.WriteLine($"FAIL self-test: {name} ({exception.Message})");
            }
        }

        Console.WriteLine(
            $"Runner self-tests: {passed} passed, {tests.Count - passed} failed, " +
            $"{tests.Count} total.");
        return passed == tests.Count ? 0 : 1;
    }


    private static void TestCp102ConstructionSemantics()
    {
        Require(CrossTlBuildPermutationRunner.ShieldHardenerCompatibilityForSelfTest(
                shieldInstalled: true, hardenerInstalled: true),
            "A TL3 Shield Hardener must be legal when a Shield Generator is installed.");
        Require(!CrossTlBuildPermutationRunner.ShieldHardenerCompatibilityForSelfTest(
                shieldInstalled: false, hardenerInstalled: true),
            "A Shield Hardener must not be legal without a Shield Generator.");
        Require(CrossTlBuildPermutationRunner.ShieldHardenerCompatibilityForSelfTest(
                shieldInstalled: false, hardenerInstalled: false),
            "A ship without a Shield Hardener must not require a Shield Generator.");

        const int tl3Capacity = 36;
        const int mandatorySupport = 3 + 3 + 5 + 5; // computer + sensor + STL + FTL
        int oneMainOneReactor = 6 + 5 + mandatorySupport;
        int twoMainOneReactor = 12 + 5 + mandatorySupport;
        int oneMainTwoReactor = 6 + 10 + mandatorySupport;
        int twoMainTwoReactor = 12 + 10 + mandatorySupport;
        Require(oneMainOneReactor == 27 && twoMainOneReactor == 33 &&
                oneMainTwoReactor == 32 && twoMainTwoReactor == 38 &&
                twoMainTwoReactor > tl3Capacity,
            "CP102 TL3 base construction arithmetic must remain 27/33/32/38 against the 36-Space Hull envelope.");
    }

    private static void TestCp102DualActiveSensorModes()
    {
        var envelope = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .ApplySensorEnvelopeOverridesForSelfTest(
                lowFirm: 3, lowApprox: 4, lowPower: 1,
                highFirm: 4, highApprox: 5, highPower: 2);
        Require(envelope.LowFirm == 3 && envelope.LowApprox == 4 && envelope.LowPower == 1 &&
                envelope.HighFirm == 4 && envelope.HighApprox == 5 && envelope.HighPower == 2 &&
                !envelope.SingleActiveMode,
            "TL3 sensor overrides must materialize Low 3/4 @1 TP and High 4/5 @2 TP as two normal operating levels.");
    }

    private static void TestCp102FullStrengthEwEfficiency()
    {
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .EffectiveRatedEwPowerCostForSelfTest(1, 2) == 2,
            "Legacy Rating-2 EW at 1 TP/rating must continue to cost 2 TP.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .EffectiveRatedEwPowerCostForSelfTest(1, 2, fullStrengthNormalPowerCostOverride: 1) == 1,
            "TL3 full-strength Rating-2 EW must cost 1 TP total when the explicit full-strength override is present.");
    }

    private static void TestCp102EvasiveCompensation()
    {
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyEvasiveCompensationForSelfTest(5, 5, ComponentCondition.Operational) == 0,
            "Operational TL3 EvComp5 must fully offset a 5-point own-Evasive firing penalty.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyEvasiveCompensationForSelfTest(3, 5, ComponentCondition.Operational) == 0,
            "Evasive Compensation must never turn a smaller penalty into a positive attack bonus.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyEvasiveCompensationForSelfTest(5, 5, ComponentCondition.Disabled) == 5,
            "A Disabled Tactical Computer must provide no Evasive Compensation.");
    }

    private static void TestCp102EnergyRatedModes()
    {
        var kinetic = new ScalingWeaponProfile(
            WeaponFamily.Kinetic, 4, 1, 1, 20, 0, 4, 1, 100);
        var energy = new ScalingWeaponProfile(
            WeaponFamily.Energy, 3, 1, 1, 25, 0, 5, 2, null);
        var missile = new ScalingWeaponProfile(
            WeaponFamily.Missile, 5, 1, 2, 0, 55, 6, 0, 25);
        var profile = new TechnologyCombatProfile(
            "cp102-energy", "CP102 Energy self-test", 3,
            12, 5, 1, 3, 1, 0, 6,
            12, 25, 1, 3, 3, 4,
            kinetic, energy, missile);

        TechnologyCombatProfile low = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .ApplyPrimaryWeaponPerformanceOverrides(profile, WeaponFamily.Energy, 2, 1, 10);
        TechnologyCombatProfile high = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .ApplyPrimaryWeaponPerformanceOverrides(profile, WeaponFamily.Energy, 4, 3, 25);
        Require(low.Energy.Damage == 2 && low.Energy.PowerCost == 1 && low.Energy.AccuracyBonus == 10,
            "TL3 Energy Low mode must resolve as 1 TP -> DAM2 at Acc+10.");
        Require(high.Energy.Damage == 4 && high.Energy.PowerCost == 3 && high.Energy.AccuracyBonus == 25,
            "TL3 Energy High mode must resolve as 3 TP -> DAM4 at Acc+25.");
        Require(low.Kinetic == kinetic && low.Missile == missile &&
                high.Kinetic == kinetic && high.Missile == missile,
            "Energy rated-mode overrides must not alter Kinetic or Missile profiles.");

        TechnologyCombatProfile kineticZeroPower =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyPrimaryWeaponPerformanceOverrides(
                    profile, WeaponFamily.Kinetic, 4, 0, 20);
        Require(kineticZeroPower.Kinetic.PowerCost == 0 &&
                kineticZeroPower.Energy == energy && kineticZeroPower.Missile == missile,
            "TL3 Kinetic maturation must preserve a valid family-local 0-TP ordinary firing cost.");
        (int zeroSpent, int zeroSpendable) =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .SpendAttackPowerForSelfTest(6, 0);
        (int oneSpent, int oneSpendable) =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .SpendAttackPowerForSelfTest(6, 1);
        Require(zeroSpent == 0 && zeroSpendable == 6 &&
                oneSpent == 1 && oneSpendable == 5,
            "The integrated attack-power consumer must treat 0 TP as a valid no-op spend and positive costs as ordinary ledger spends.");
    }

    private static void TestCp102AmmReadiness()
    {
        (int Power, int Reactions) low = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .PdsReadinessModeForSelfTest(
                primaryPower: 2, primaryReactions: 2,
                fallbackPower: 1, fallbackReactions: 1, availablePower: 1);
        (int Power, int Reactions) high = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .PdsReadinessModeForSelfTest(
                primaryPower: 2, primaryReactions: 2,
                fallbackPower: 1, fallbackReactions: 1, availablePower: 2);
        Require(low == (1, 1),
            "TL3 AMM must fall back to 1 TP -> RC1 when High readiness is not affordable.");
        Require(high == (2, 2),
            "TL3 AMM must select 2 TP -> RC2 when High readiness is affordable.");
    }


    private static void TestCp102PdsAmmunitionBridge()
    {
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .InitialBuildPdsAmmunitionForSelfTest(1, pdsFamily: null, perInstallationAmmunition: null) == 50,
            "Legacy build-based Kinetic PDS without v7 family metadata must retain the frozen 50-round integrated-combat allowance.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .InitialBuildPdsAmmunitionForSelfTest(1, pdsFamily: "Kinetic", perInstallationAmmunition: 60) == 60,
            "Explicit v7 Kinetic PDS ammunition must use the declared 60-round allowance.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .InitialBuildPdsAmmunitionForSelfTest(1, pdsFamily: "Energy", perInstallationAmmunition: null) is null,
            "Explicit v7 Energy PDS with no ammunition value must remain ammunition-free/unlimited rather than inheriting legacy Kinetic ammunition.");
    }

    private static void TestCp99MandatorySensorCombatCore()
    {
        Require(CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(
                1, 1, 1, minimumMainWeaponCount: 1, minimumReactorCount: 1, minimumSensorCount: 1),
            "A Main Weapon, Reactor, and installed Sensor must satisfy the CP99 normal combat core.");
        Require(!CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(
                1, 1, 0, minimumMainWeaponCount: 1, minimumReactorCount: 1, minimumSensorCount: 1),
            "A sensorless otherwise-armed ship must be excluded from the CP99 ordinary legal combat population.");
        Require(CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(1, 1),
            "Historical pre-CP99 guardrail self-tests must retain their weapon/reactor-only default semantics.");
    }

    private static void TestCp97EncounterSearch()
    {
        HexMap map = HexMap.CreateHexagon(5);
        EncounterSearchMove move = EncounterSearchMovementResolver.ResolveTowardCenter(
            map, new HexCoord(-5, 0), availableMovementHexes: 4);
        Require(move.MovementHexes == 1 && move.Destination.Length() == 4,
            "CP97 search must move exactly one hex toward center regardless of excess STL allowance.");
    }

    private static void TestCp97OverloadRangeMemory()
    {
        var memory = new TacticalCombatBlackboard("B");
        var state = new TacticalObservableStateSignature(
            true, false, ComponentCondition.Operational, ComponentCondition.Operational);
        memory.RecordOverloadFailure(TacticalEscalationKind.EccmOverload, 2, state);
        Require(!memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 2, state) &&
                !memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 3, state) &&
                memory.CanAttemptOverload(TacticalEscalationKind.EccmOverload, 1, state),
            "CP97 overload memory must block same/farther retries while permitting a closer attempt.");
    }

    private static void TestCp97OverloadMaterialStateChange()
    {
        var memory = new TacticalCombatBlackboard("B");
        var state = new TacticalObservableStateSignature(
            true, false, ComponentCondition.Operational, ComponentCondition.Operational);
        memory.RecordOverloadFailure(TacticalEscalationKind.ActiveSensorOverload, 1, state);
        TacticalObservableStateSignature changed = state with { OpponentEcmEmissionObserved = false };
        Require(memory.CanAttemptOverload(TacticalEscalationKind.ActiveSensorOverload, 1, changed),
            "CP97 overload memory must permit a new attempt after a materially changed observable state.");
    }

    private static void TestCp93MatchedCrossTlStrata()
    {
        Require(CrossTlBuildPermutationRunner.SpaceUtilizationClassForSelfTest(35, 35, 32) == "exact_fill" &&
                CrossTlBuildPermutationRunner.SpaceUtilizationClassForSelfTest(34, 35, 32) == "near_fill" &&
                CrossTlBuildPermutationRunner.SpaceUtilizationClassForSelfTest(32, 35, 32) == "near_fill" &&
                CrossTlBuildPermutationRunner.SpaceUtilizationClassForSelfTest(31, 35, 32) == "underfilled",
            "CP93 Space-utilization classification drifted.");
        Require(CrossTlBuildPermutationRunner.ProgressionMagnitudeStratumForSelfTest(3, 3, 2, 3) == "equal_low" &&
                CrossTlBuildPermutationRunner.ProgressionMagnitudeStratumForSelfTest(5, 5, 2, 3) == "equal_high" &&
                CrossTlBuildPermutationRunner.ProgressionMagnitudeStratumForSelfTest(3, 5, 2, 3) == "near" &&
                CrossTlBuildPermutationRunner.ProgressionMagnitudeStratumForSelfTest(2, 6, 2, 3) == "far",
            "CP93 orientation-neutral progression-magnitude classification drifted.");
        Require(CrossTlBuildPermutationRunner.SpacePairStratumForSelfTest("near_fill", "exact_fill") == "exact_fill-near_fill" &&
                CrossTlBuildPermutationRunner.SpacePairStratumForSelfTest("underfilled", "near_fill") == "near_fill-underfilled" &&
                CrossTlBuildPermutationRunner.SpacePairStratumForSelfTest("exact_fill", "exact_fill") == "exact_fill-exact_fill",
            "CP93 canonical Space-pair classification drifted.");
        const long legalBuilds = 22592L;
        long unorderedDistinct = legalBuilds * (legalBuilds - 1L) / 2L;
        long orientedDistinct = legalBuilds * (legalBuilds - 1L);
        Require(unorderedDistinct == 255187936L && orientedDistinct == 510375872L,
            "CP93 distinct legal-pair envelope arithmetic drifted.");

        const string camelCaseSensorCatalog = """
        {
          "schemaVersion": "star-cluster-tl1-sensor-ew-foundation-v1",
          "id": "cp93-self-test",
          "checkpoint": 93,
          "status": "self-test",
          "policy": "Verify the v4 readiness loader accepts authoritative camelCase Sensor/EW catalogs.",
          "maxTacticalSeparationHexes": 10,
          "candidates": [
            {
              "id": "candidate",
              "isHistoricalControl": true,
              "passiveFirmRange": 1,
              "passiveApproximateRange": 3,
              "activeFirmRange": 3,
              "activeApproximateRange": 4,
              "activePowerCost": 1,
              "activeOverloadAdditionalPowerCost": 1,
              "activeOverloadFirmBonus": 1,
              "activeOverloadApproximateBonus": 1,
              "rationale": "Binding regression guard.",
              "discriminationResistance": 0,
              "pointBlankBurnThroughResistance": 1
            }
          ]
        }
        """;
        Require(CrossTlBuildPermutationRunner.SensorEwCatalogCandidateCountForSelfTest(camelCaseSensorCatalog) == 1,
            "CP93 readiness loader must preserve the established case-insensitive Sensor/EW catalog binding contract.");
        Require(CrossTlBuildPermutationRunner.PopulationCellKeyForSelfTest(
                "single-no-ew-redundancy", "equal_low", "exact_fill-exact_fill") ==
                "single-no-ew-redundancy~equal_low~exact_fill-exact_fill",
            "CP93 population-cell keys must remain safe inside pipe-delimited profile-label metadata.");
    }

    private static void TestCp94AdaptiveCrossTlSampling()
    {
        int[] quotas = CrossTlBuildPermutationRunner.AllocateAdaptiveQuotasForSelfTest(
            new long[] { 1, 4, 9, 16 }, 8, 1, 0.5, 4);
        Require(quotas.Sum() == 8 && quotas.All(quota => quota is >= 1 and <= 4),
            "CP94 adaptive quotas must conserve the requested base-pair budget within configured bounds.");
        Require(quotas[3] >= quotas[2] && quotas[2] >= quotas[1] && quotas[1] >= quotas[0],
            "CP94 adaptive quotas must not allocate fewer representatives to larger synthetic populations under square-root weighting.");
        Require(CrossTlBuildPermutationRunner.InformationControlDistanceBandForSelfTest(0, 2) == "equal" &&
                CrossTlBuildPermutationRunner.InformationControlDistanceBandForSelfTest(1, 2) == "near" &&
                CrossTlBuildPermutationRunner.InformationControlDistanceBandForSelfTest(2, 2) == "near" &&
                CrossTlBuildPermutationRunner.InformationControlDistanceBandForSelfTest(3, 2) == "far",
            "CP94 information-control distance bands must remain equal/near/far at the configured boundary.");
    }

    private static void TestCp96ReadinessCohortSemantics()
    {
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .PostMovementReadyWindowReachedForSelfTest(1, 1),
            "CP95 final post-Movement range 1 must reach a ready range of 1.");
        Require(!TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .PostMovementReadyWindowReachedForSelfTest(2, 1),
            "CP95 movement-path closest approach must not substitute for a final post-Movement range that remains outside ready range.");
        Require(!TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .PostMovementReadyWindowReachedForSelfTest(0, -1),
            "CP95 engagement-denied metadata must never create a ready firing window.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .RuntimeActionOutsideStructuralReadyEstimateForSelfTest(1.0, 0.0),
            "CP95 must retain legal runtime action outside the static structural ready-range estimate as review telemetry rather than rejecting the firing-window counters.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .CrossTlObservedReferenceReadyWindowForSelfTest(0.25) &&
                !TL1Calibration.Tl1IntegratedTacticalCombatRunner.CrossTlObservedReferenceReadyWindowForSelfTest(0.0),
            "CP96 observed firing-window readiness must be an explicit post-Movement observation rather than a static reference prediction.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .CrossTlRuntimeBilateralActiveForSelfTest(0.5, 0.25) &&
                !TL1Calibration.Tl1IntegratedTacticalCombatRunner.CrossTlRuntimeBilateralActiveForSelfTest(0.5, 0.0),
            "CP96 runtime bilateral activity must depend only on both sides actually producing family-appropriate actions.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .CrossTlReferenceRuntimeRelationForSelfTest(false, true) == "reference_not_expected_runtime_active" &&
                TL1Calibration.Tl1IntegratedTacticalCombatRunner.CrossTlReferenceRuntimeRelationForSelfTest(true, false) == "reference_expected_runtime_inactive",
            "CP96 must preserve reference-context false-negative and reference-expected/runtime-inactive classifications explicitly.");
        Require(!TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .RuntimeActionOutsideStructuralReadyEstimateForSelfTest(1.0, 100.0),
            "CP95 runtime/structural divergence review must clear when the structural ready window was actually observed.");

        string movementDenied = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .DiagnoseCrossTlObservedEngagementForSelfTest(
                "dynamic-a-first", "closing_ready", "reference_ready", 0.0, 0.0, 0.0);
        Require(movementDenied == "movement_did_not_reach_mutual_ready_range",
            "CP95 dynamic diagnosis must use observed post-Movement ready-window reach, not path closest approach.");

        string reachedButInactive = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .DiagnoseCrossTlObservedEngagementForSelfTest(
                "dynamic-a-first", "closing_ready", "reference_ready", 0.0, 0.0, 100.0);
        Require(reachedButInactive == "ready_geometry_reached_but_no_actions",
            "CP95 must distinguish reached firing geometry from a true zero-action integration failure.");

        string fixedTelemetryFailure = TL1Calibration.Tl1IntegratedTacticalCombatRunner
            .DiagnoseCrossTlObservedEngagementForSelfTest(
                "fixed-r3", "reference_ready", "reference_ready", 0.0, 0.0, 0.0);
        Require(fixedTelemetryFailure == "fixed_reference_ready_geometry_not_observed",
            "CP95 fixed-reference readiness must fail explicitly if post-Movement firing-window telemetry is missing.");
    }

    private static void TestCp90GeneralizedCrossTlFoundation()
    {
        long count = CrossTlBuildPermutationRunner.ComputeCartesianCountForSelfTest(
            new[] { 8, 4, 2, 3, 3, 2, 6, 6, 2 });
        Require(count == 82944L,
            $"CP90 generalized cross-TL Cartesian foundation expected 82944 raw combinations; observed {count}.");
        Require(CrossTlBuildPermutationRunner.ProgressionDirectionForSelfTest(2, 4) == "side_a_lower" &&
                CrossTlBuildPermutationRunner.ProgressionDirectionForSelfTest(4, 4) == "equal" &&
                CrossTlBuildPermutationRunner.ProgressionDirectionForSelfTest(5, 4) == "side_a_higher",
            "CP90 progression direction classification drifted.");
        Require(CrossTlBuildPermutationRunner.ProgressionStratumForSelfTest(2, 3, 2, 3) == "side_a_lower_near" &&
                CrossTlBuildPermutationRunner.ProgressionStratumForSelfTest(1, 4, 2, 3) == "side_a_lower_far" &&
                CrossTlBuildPermutationRunner.ProgressionStratumForSelfTest(3, 3, 2, 3) == "equal_low" &&
                CrossTlBuildPermutationRunner.ProgressionStratumForSelfTest(5, 5, 2, 3) == "equal_high" &&
                CrossTlBuildPermutationRunner.ProgressionStratumForSelfTest(6, 4, 2, 3) == "side_a_higher_near" &&
                CrossTlBuildPermutationRunner.ProgressionStratumForSelfTest(7, 4, 2, 3) == "side_a_higher_far",
            "CP90 progression-distance stratum classification drifted.");
    }

    private static void TestCp90NonAdditiveEwRedundancy()
    {
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ResolveHighestFunctionalEwRatingForSelfTest(new[] { 2, 2 }, new[] { true, true }) == 2,
            "Two functional ECM2/ECCM2 installations must remain rating 2 rather than add to rating 4.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ResolveHighestFunctionalEwRatingForSelfTest(new[] { 1, 2 }, new[] { true, true }) == 2,
            "Mixed rating-1/rating-2 redundancy must resolve to the highest functional rating 2.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ResolveHighestFunctionalEwRatingForSelfTest(new[] { 1, 2 }, new[] { true, false }) == 1,
            "Mixed EW redundancy must fall back to rating 1 when the higher-rated installation is unavailable.");
    }

    private static void TestCp88MinimumCombatCoreGuardrail()
    {
        Require(CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(1, 1),
            "One Main Weapon plus one Reactor must satisfy the combat core.");
        Require(!CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(0, 1),
            "A reactor-only combat build must be illegal.");
        Require(!CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(1, 0),
            "A weapon-only combat build must be illegal.");
        Require(CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(2, 1) &&
                CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(1, 2) &&
                CrossTlBuildPermutationRunner.MeetsMinimumCombatCoreForSelfTest(2, 2),
            "Optional explicit second Main Weapons/Reactors must not be rejected by the minimum-core guardrail.");
    }

    private static void TestCp88RatedEwAffordability()
    {
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .EffectiveRatedEwPowerCostForSelfTest(1, 1) == 1,
            "Rating-1 EW at base cost 1 must cost 1 TP.");
        Require(TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .EffectiveRatedEwPowerCostForSelfTest(1, 2) == 2,
            "Rating-2 EW at base cost 1 must reserve 2 TP for doctrine affordability.");
    }

    private static void TestCp87CrossTlCartesianFoundation()
    {
        long count = CrossTlBuildPermutationRunner.ComputeCartesianCountForSelfTest(
            new[] { 4, 2, 2, 2, 2, 2, 2, 2 });
        Require(count == 512L,
            $"CP87 cross-TL Cartesian foundation expected 512 combinations; observed {count}.");
        long oriented = count * count;
        long unorderedWithSelf = (count * (count + 1L)) / 2L;
        Require(oriented == 262144L && unorderedWithSelf == 131328L,
            "CP87 cross-TL pairing-envelope arithmetic drifted.");
    }

    private static void TestCp86WeaponPenetrationOverrideSemantics()
    {
        var kinetic = new ScalingWeaponProfile(
            WeaponFamily.Kinetic, 4, 1, 0, 5, 0, 3, 1, 10);
        var energy = new ScalingWeaponProfile(
            WeaponFamily.Energy, 3, 1, 1, 5, 0, 3, 1, null);
        var missile = new ScalingWeaponProfile(
            WeaponFamily.Missile, 5, 1, 2, 0, 63, 6, 0, 6);
        var control = new TechnologyCombatProfile(
            "cp86-control", "CP86 control", 1,
            100, 5, 0, 3, 1, 0, 6,
            12, 47, 1, 2, 1, 2,
            kinetic, energy, missile);

        TechnologyCombatProfile kineticCandidate =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyPrimaryWeaponPenetrationOverrides(
                    control, WeaponFamily.Kinetic, 2, 1);
        Require(kineticCandidate.Kinetic.ShieldPenetration == 2 &&
                kineticCandidate.Kinetic.ArmorPenetration == 1,
            "CP86 Kinetic penetration override did not update SPEN/APEN.");
        Require(kineticCandidate.Kinetic.Damage == kinetic.Damage &&
                kineticCandidate.Kinetic.AccuracyBonus == kinetic.AccuracyBonus &&
                kineticCandidate.Kinetic.MaximumRange == kinetic.MaximumRange &&
                kineticCandidate.Kinetic.PowerCost == kinetic.PowerCost,
            "CP86 Kinetic penetration override changed non-penetration weapon properties.");
        Require(kineticCandidate.Energy == energy && kineticCandidate.Missile == missile,
            "CP86 Kinetic penetration override changed another weapon family.");
        Require(kineticCandidate.ShieldCapacity == control.ShieldCapacity &&
                kineticCandidate.ArmorIntegrity == control.ArmorIntegrity &&
                kineticCandidate.ArmorProtection == control.ArmorProtection &&
                kineticCandidate.ReactorOutput == control.ReactorOutput,
            "CP86 penetration override changed defense or reactor properties.");
        Require(control.Kinetic.ShieldPenetration == 1 && control.Kinetic.ArmorPenetration == 0,
            "CP86 penetration override mutated the control profile.");

        TechnologyCombatProfile energyCandidate =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyPrimaryWeaponPenetrationOverrides(
                    control, WeaponFamily.Energy, 2, 2);
        Require(energyCandidate.Energy.ShieldPenetration == 2 &&
                energyCandidate.Energy.ArmorPenetration == 2 &&
                energyCandidate.Kinetic == kinetic && energyCandidate.Missile == missile,
            "CP86 Energy penetration override did not remain family-local.");

        TechnologyCombatProfile missileCandidate =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyPrimaryWeaponPenetrationOverrides(
                    control, WeaponFamily.Missile, 2, 3);
        Require(missileCandidate.Missile.ShieldPenetration == 2 &&
                missileCandidate.Missile.ArmorPenetration == 3 &&
                missileCandidate.Kinetic == kinetic && missileCandidate.Energy == energy,
            "CP86 Missile penetration override did not remain family-local.");
    }

    private static void TestCp85ArmorOverrideSemantics()
    {
        var kinetic = new ScalingWeaponProfile(
            WeaponFamily.Kinetic, 10, 0, 0, 5, 0, 3, 1, 10);
        var energy = new ScalingWeaponProfile(
            WeaponFamily.Energy, 10, 0, 0, 5, 0, 3, 1, null);
        var missile = new ScalingWeaponProfile(
            WeaponFamily.Missile, 10, 0, 0, 0, 63, 6, 0, 6);
        var control = new TechnologyCombatProfile(
            "cp85-control", "CP85 control", 1,
            100, 4, 0, 3, 1, 0, 6,
            12, 47, 1, 2, 1, 2,
            kinetic, energy, missile);

        TechnologyCombatProfile integrityOnly =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyArmorOverrides(control, 5, null);
        TechnologyCombatProfile protectionOnly =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyArmorOverrides(control, null, 1);
        TechnologyCombatProfile combined =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyArmorOverrides(control, 5, 1);

        Require(integrityOnly.ArmorIntegrity == 5 && integrityOnly.ArmorProtection == 0,
            "CP85 AI-only override changed AP or failed to update AI.");
        Require(protectionOnly.ArmorIntegrity == 4 && protectionOnly.ArmorProtection == 1,
            "CP85 AP-only override changed AI or failed to update AP.");
        Require(combined.ArmorIntegrity == 5 && combined.ArmorProtection == 1,
            "CP85 combined armor override failed to update AP/AI independently.");
        Require(combined.ShieldCapacity == 3 && combined.ShieldBaseRecharge == 1 &&
                combined.ShieldArmor == 0 && combined.ReactorOutput == 6,
            "CP85 armor override changed shield or reactor properties.");
        Require(combined.TargetingBonus == 12 && combined.EffectivePdsChance == 47,
            "CP85 armor override changed fire-control properties.");
        Require(combined.Kinetic == kinetic && combined.Energy == energy && combined.Missile == missile,
            "CP85 armor override changed weapon/APEN profile data.");
        Require(control.ArmorIntegrity == 4 && control.ArmorProtection == 0,
            "CP85 armor override mutated the control profile.");
        Require(ReferenceEquals(
                TL1Calibration.Tl1IntegratedTacticalCombatRunner
                    .ApplyArmorOverrides(control, null, null),
                control),
            "Missing CP85 armor overrides should preserve the original profile instance.");
    }

    private static void TestCp84ShieldCapacityOverrideSemantics()
    {
        var kinetic = new ScalingWeaponProfile(
            WeaponFamily.Kinetic, 10, 0, 0, 5, 0, 3, 1, 10);
        var energy = new ScalingWeaponProfile(
            WeaponFamily.Energy, 10, 0, 0, 5, 0, 3, 1, null);
        var missile = new ScalingWeaponProfile(
            WeaponFamily.Missile, 10, 0, 0, 0, 63, 6, 0, 6);
        var control = new TechnologyCombatProfile(
            "cp84-control", "CP84 control", 1,
            100, 20, 10, 2, 1, 0, 5,
            12, 47, 1, 2, 1, 2,
            kinetic, energy, missile);

        TechnologyCombatProfile candidate =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyShieldCapacityOverride(control, 3);

        Require(candidate.ShieldCapacity == 3,
            "CP84 Shield Capacity override did not update capacity.");
        Require(candidate.ShieldBaseRecharge == 1 && candidate.ShieldArmor == 0,
            "CP84 Shield Capacity override changed recharge or hardening properties.");
        Require(candidate.ReactorOutput == 5 && candidate.TargetingBonus == 12 &&
                candidate.EffectivePdsChance == 47,
            "CP84 Shield Capacity override changed reactor or fire-control properties.");
        Require(candidate.Kinetic == kinetic && candidate.Energy == energy &&
                candidate.Missile == missile,
            "CP84 Shield Capacity override changed weapon-profile data.");
        Require(control.ShieldCapacity == 2,
            "CP84 Shield Capacity override mutated the TL1 control profile.");
        Require(ReferenceEquals(
                TL1Calibration.Tl1IntegratedTacticalCombatRunner
                    .ApplyShieldCapacityOverride(control, null),
                control),
            "A missing Shield Capacity override should preserve the original profile instance.");
    }

    private static void TestCp81TacticalComputerOverrideSemantics()
    {
        var kinetic = new ScalingWeaponProfile(
            WeaponFamily.Kinetic, 10, 0, 0, 5, 0, 3, 1, 10);
        var energy = new ScalingWeaponProfile(
            WeaponFamily.Energy, 10, 0, 0, 5, 0, 3, 1, null);
        var missile = new ScalingWeaponProfile(
            WeaponFamily.Missile, 10, 0, 0, 0, 63, 6, 0, 6);
        var control = new TechnologyCombatProfile(
            "cp81-control", "CP81 control", 1,
            100, 20, 10, 20, 1, 0, 5,
            10, 45, 1, 2, 1, 2,
            kinetic, energy, missile);

        TechnologyCombatProfile candidate =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner
                .ApplyTacticalComputerTargetingOverride(control, 12);

        Require(candidate.TargetingBonus == 12,
            "CP81 +12 override did not update ordinary Tactical Computer targeting.");
        Require(candidate.EffectivePdsChance == 47,
            "CP81 +12 override did not preserve the 35-point local PDS base plus main-computer assistance.");
        Require(candidate.Missile.GuidanceChance == 63,
            "CP81 Tactical Computer override incorrectly changed independent missile guidance.");
        Require(candidate.Kinetic == kinetic && candidate.Energy == energy &&
                candidate.Missile == missile,
            "CP81 Tactical Computer override changed weapon-profile data outside fire-control assistance.");
        Require(control.TargetingBonus == 10 && control.EffectivePdsChance == 45,
            "CP81 Tactical Computer override mutated the TL1 control profile.");
        Require(ReferenceEquals(
                TL1Calibration.Tl1IntegratedTacticalCombatRunner
                    .ApplyTacticalComputerTargetingOverride(control, null),
                control),
            "A missing Tactical Computer override should preserve the original profile instance.");
    }

    private static void TestCp74FirmReferenceGateSemantics()
    {
        bool cleanDespitePossibleLaterApproximateTelemetry =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner.Tl1ApproximateTrackFirmReferenceIsClean(
                    meanFirmTrackA: 8.0,
                    meanFirmTrackB: 8.0,
                    meanEcmPowerA: 0.0,
                    meanEcmPowerB: 0.0,
                    meanEccmPowerA: 0.0,
                    meanEccmPowerB: 0.0,
                    meanDirectShots: 12.0);
        Require(
            cleanDespitePossibleLaterApproximateTelemetry,
            "An unjammed Firm-reference lane with ordinary fire was rejected by the CP74 gate semantics.");

        bool contaminatedByEcm =
            TL1Calibration.Tl1IntegratedTacticalCombatRunner.Tl1ApproximateTrackFirmReferenceIsClean(
                    meanFirmTrackA: 8.0,
                    meanFirmTrackB: 8.0,
                    meanEcmPowerA: 1.0,
                    meanEcmPowerB: 0.0,
                    meanEccmPowerA: 0.0,
                    meanEccmPowerB: 0.0,
                    meanDirectShots: 12.0);
        Require(
            !contaminatedByEcm,
            "A CP74 Firm-reference lane with ECM power was incorrectly accepted as clean.");
    }

    private static void TestStableSeed()
    {
        ulong first = TrialSeedDeriver.Derive(19UL, "variant", 7, 2UL);
        ulong second = TrialSeedDeriver.Derive(19UL, "variant", 7, 2UL);
        Require(first == second, "Identical seed inputs produced different outputs.");
    }

    private static void TestDifferentTrialSeeds()
    {
        ulong first = TrialSeedDeriver.Derive(19UL, "variant", 7, 0UL);
        ulong second = TrialSeedDeriver.Derive(19UL, "variant", 8, 0UL);
        Require(first != second, "Adjacent trials received the same seed.");
    }

    private static void TestSeparatedStreams()
    {
        ulong interception = TrialSeedDeriver.Derive(19UL, "variant", 7, 1UL);
        ulong terminal = TrialSeedDeriver.Derive(19UL, "variant", 7, 2UL);
        Require(interception != terminal, "Interception and terminal streams collided.");
    }

    private static void TestRandomReplay()
    {
        var first = new DeterministicRandomStream(123456UL);
        var second = new DeterministicRandomStream(123456UL);
        for (int index = 0; index < 64; index++)
        {
            Require(
                first.NextUInt64() == second.NextUInt64(),
                $"Random replay diverged at item {index}.");
        }
    }

    private static void TestWilsonInterval()
    {
        ProbabilityMetricSummary metric = MonteCarloStatistics.CreateMetric(
            "test",
            50,
            100);
        Require(metric.Confidence95Low < 0.5, "Wilson low bound is not below p.");
        Require(metric.Confidence95High > 0.5, "Wilson high bound is not above p.");
        Require(
            metric.Confidence95Low >= 0.0 && metric.Confidence95High <= 1.0,
            "Wilson interval left the probability domain.");
    }

    private static void TestOverride()
    {
        var scenario = new ScenarioDocument
        {
            Defenses =
            {
                new DefenseDocument { Id = "pds", InterceptionChancePercent = 0 },
            },
        };
        using JsonDocument value = JsonDocument.Parse("40");
        ScenarioDocument updated = ScenarioOverrideApplier.Apply(
            scenario,
            new[]
            {
                new ScenarioOverrideDocument
                {
                    Path = "defenses[0].interceptionChancePercent",
                    Value = value.RootElement.Clone(),
                },
            });
        Require(
            updated.Defenses[0].InterceptionChancePercent == 40,
            "Override did not update interceptionChancePercent.");
        Require(
            scenario.Defenses[0].InterceptionChancePercent == 0,
            "Override mutated the base scenario.");
    }

    private static void TestWorkerIndependence(string scenarioPath)
    {
        ScenarioDocument scenario = PrepareStochasticScenario(scenarioPath);
        string root = CreateTemporaryDirectory();
        try
        {
            MonteCarloBatchRunResult serial = MonteCarloBatchRunner.Run(
                scenario,
                "self-test-repro",
                Options(128, jobs: 1, resume: false),
                Path.Combine(root, "jobs-1"));
            MonteCarloBatchRunResult parallel = MonteCarloBatchRunner.Run(
                scenario,
                "self-test-repro",
                Options(128, jobs: 4, resume: false),
                Path.Combine(root, "jobs-4"));
            Require(serial.Passed && parallel.Passed, "A reproducibility batch failed.");
            Require(
                string.Equals(
                    serial.ResultsSha256,
                    parallel.ResultsSha256,
                    StringComparison.Ordinal),
                "Result hashes changed with worker count.");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static void TestResume(string scenarioPath)
    {
        ScenarioDocument scenario = PrepareStochasticScenario(scenarioPath);
        string root = CreateTemporaryDirectory();
        try
        {
            string resumeDirectory = Path.Combine(root, "resume");
            MonteCarloBatchRunner.Run(
                scenario,
                "self-test-resume",
                Options(32, jobs: 2, resume: false),
                resumeDirectory);
            MonteCarloBatchRunResult resumed = MonteCarloBatchRunner.Run(
                scenario,
                "self-test-resume",
                Options(128, jobs: 4, resume: true),
                resumeDirectory);
            MonteCarloBatchRunResult fresh = MonteCarloBatchRunner.Run(
                scenario,
                "self-test-resume",
                Options(128, jobs: 1, resume: false),
                Path.Combine(root, "fresh"));
            Require(resumed.ResumedTrials == 32, "Resume did not reuse 32 trials.");
            Require(resumed.ExecutedTrials == 96, "Resume did not execute 96 trials.");
            Require(
                string.Equals(
                    resumed.ResultsSha256,
                    fresh.ResultsSha256,
                    StringComparison.Ordinal),
                "Extended resume result differs from a fresh run.");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static void TestCommonRandomNumbers(string scenarioPath)
    {
        ScenarioDocument scenario = PrepareStochasticScenario(scenarioPath);
        const string seedNamespace = "self-test-common-random-numbers";
        MonteCarloTrialResult first = MonteCarloTrialResult.Execute(
            scenario,
            "variant-a",
            trialIndex: 7,
            masterSeed: 20UL,
            randomSeedNamespace: seedNamespace);
        MonteCarloTrialResult second = MonteCarloTrialResult.Execute(
            scenario,
            "variant-b",
            trialIndex: 7,
            masterSeed: 20UL,
            randomSeedNamespace: seedNamespace);
        Require(first.Error is null && second.Error is null, "A common-random trial failed.");
        Require(
            first.TrialSeedHex == second.TrialSeedHex &&
            first.InterceptionSeedHex == second.InterceptionSeedHex &&
            first.TerminalSeedHex == second.TerminalSeedHex,
            "Different variants did not receive identical common random streams.");
        Require(
            first.FinalStatus == second.FinalStatus &&
            first.FinalOutcome == second.FinalOutcome &&
            first.InterceptionStage == second.InterceptionStage,
            "Identical scenarios diverged under common random streams.");
    }

    private static void TestPairedBinaryDifference()
    {
        PairedBinaryDifferenceSummary summary = PairedMarginalStatistics.Compare(
            new[] { false, true, true, false },
            new[] { false, false, true, true },
            "flat");
        Require(summary.NeitherTrue == 1, "Paired neither-true count was incorrect.");
        Require(summary.FromOnlyTrue == 1, "Paired from-only count was incorrect.");
        Require(summary.ToOnlyTrue == 1, "Paired to-only count was incorrect.");
        Require(summary.BothTrue == 1, "Paired both-true count was incorrect.");
        Require(Math.Abs(summary.ObservedDelta) < 1e-12, "Balanced discordance did not produce a zero delta.");
        Require(summary.RawPValue > 0.99, "Balanced discordance should not reject equality.");
    }

    private static void TestHolmAdjustment()
    {
        double[] adjusted = PairedMarginalStatistics.AdjustHolm(
            new[] { 0.01, 0.04, 0.03 });
        Require(Math.Abs(adjusted[0] - 0.03) < 1e-12, "First Holm value was incorrect.");
        Require(Math.Abs(adjusted[1] - 0.06) < 1e-12, "Third-ranked Holm value lost monotonicity.");
        Require(Math.Abs(adjusted[2] - 0.06) < 1e-12, "Second-ranked Holm value was incorrect.");
    }

    private static void TestPracticalEffectThreshold()
    {
        Require(
            !PairedMarginalStatistics.IsStatisticallyContradictory(
                "nondecreasing",
                observedDelta: -0.005,
                holmAdjustedPValue: 0.001,
                minimumPracticalDelta: 0.01,
                familywiseAlpha: 0.05),
            "A statistically detectable but trivial delta failed the practical threshold.");
        Require(
            PairedMarginalStatistics.IsStatisticallyContradictory(
                "nondecreasing",
                observedDelta: -0.02,
                holmAdjustedPValue: 0.01,
                minimumPracticalDelta: 0.01,
                familywiseAlpha: 0.05),
            "A practical, Holm-significant directional reversal was not rejected.");
    }

    private static void TestFullFlightMatrix()
    {
        FullFlightCalibrationStudyDocument study = CreateFullFlightStudy();
        TechnologyProfileCatalogDocument catalog = CreateCalibrationCatalog();
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareVariants(study, catalog);
        Require(variants.Count == 288, "Full-flight matrix did not produce 288 variants.");
        Require(
            variants.Select(item => item.Id).Distinct(StringComparer.Ordinal).Count() == 288,
            "Full-flight variant IDs are not unique.");
    }

    private static void TestFullFlightMovementPolicies()
    {
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareVariants(
                CreateFullFlightStudy(),
                CreateCalibrationCatalog());
        PreparedFullFlightCalibrationVariant stationary = variants.Single(item =>
            item.Id == "command-guided-m2-t2-stationary-live");
        PreparedFullFlightCalibrationVariant retreat = variants.Single(item =>
            item.Id == "command-guided-m2-t2-straight-retreat-live");
        PreparedFullFlightCalibrationVariant crossing = variants.Single(item =>
            item.Id == "command-guided-m2-t2-crossing-weave-live");
        PreparedFullFlightCalibrationVariant turnback = variants.Single(item =>
            item.Id == "command-guided-m2-t2-turnback-live");
        Require(
            stationary.Scenario.Actions.All(action => action.Type != "moveShip"),
            "Stationary policy unexpectedly created ship movement actions.");
        ActionDocument firstRetreat = retreat.Scenario.Actions.First(action =>
            action.Type == "moveShip");
        Require(
            firstRetreat.Destination is { Q: 17, R: 11 },
            "Straight-retreat policy did not move along the expected hex vector.");
        ActionDocument firstCrossing = crossing.Scenario.Actions.First(action =>
            action.Type == "moveShip");
        Require(
            firstCrossing.Destination is { Q: 16, R: 13 },
            "Crossing-weave did not begin on the expected crossing vector.");
        ActionDocument[] turnbackMoves = turnback.Scenario.Actions
            .Where(action => action.Type == "moveShip")
            .Take(2)
            .ToArray();
        Require(
            turnbackMoves.Length == 2 &&
            turnbackMoves[0].Destination is { Q: 17, R: 11 } &&
            turnbackMoves[1].Destination is { Q: 16, R: 12 },
            "Turnback policy did not return to its prior coordinate.");
    }

    private static void TestFullFlightOcclusionSeed()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .Single(item =>
                    item.Id == "sensor-only-m4-t4-stationary-occluded");
        MissileDocument missile = variant.Scenario.Missiles.Single();
        Require(
            variant.Scenario.Map.Objects.Count(item =>
                item.Id.StartsWith("datalink-occluder-", StringComparison.Ordinal)) == 3,
            "Occluded variant did not include the datalink blocker.");
        Require(
            missile.EnteredCoordinates.Count == 3 &&
            missile.GuidancePhaseCount == 1 &&
            missile.RetainedDatalink is { LinkState: "Blocked", AgePhases: 0 },
            "Occluded variant did not seed coherent pre-existing missile history.");
        Require(
            ScenarioPreflightValidator.Validate(variant.Scenario).Count == 0,
            "Occluded full-flight scenario failed preflight.");
    }

    private static void TestFullFlightStopContract()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .First();
        Require(
            variant.Scenario.StopWhenAllMissilesTerminal,
            "Full-flight scenario did not request terminal early-stop behavior.");
    }

    private static void TestFullFlightRelativeSpeedCoverage()
    {
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareVariants(
                CreateFullFlightStudy(),
                CreateCalibrationCatalog());
        bool missileFaster = variants.Any(item =>
            item.MissileTechnology.FlightSpeedHexesPerTurn >
            item.TargetPropulsionTechnology.ShipMovementHexesPerTurn);
        bool equalSpeed = variants.Any(item =>
            item.MissileTechnology.FlightSpeedHexesPerTurn ==
            item.TargetPropulsionTechnology.ShipMovementHexesPerTurn);
        bool targetFaster = variants.Any(item =>
            item.MissileTechnology.FlightSpeedHexesPerTurn <
            item.TargetPropulsionTechnology.ShipMovementHexesPerTurn);
        Require(
            missileFaster && equalSpeed && targetFaster,
            "Full-flight matrix does not cover faster, equal, and slower missile relationships.");
    }

    private static void TestFullFlightDatalinkPairs()
    {
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareVariants(
                CreateFullFlightStudy(),
                CreateCalibrationCatalog());
        Require(
            variants.Any(item => item.Id == "seeker-only-m4-t6-crossing-weave-live") &&
            variants.Any(item => item.Id == "seeker-only-m4-t6-crossing-weave-occluded"),
            "Full-flight matrix did not create paired live/occluded datalink variants.");
    }

    private static void TestFullFlightSafetyTurnCap()
    {
        FullFlightCalibrationStudyDocument study = CreateFullFlightStudy();
        TechnologyProfileCatalogDocument catalog = CreateCalibrationCatalog();
        RepresentativeMissileProfileDocument command = catalog.MissileProfiles.Single(item =>
            item.Id == "command-guided");
        RepresentativeMissileProfileDocument sensor = catalog.MissileProfiles.Single(item =>
            item.Id == "sensor-only");
        TechnologyLevelCalibrationDocument low = catalog.TechnologyLevels.Single(item =>
            item.TechnologyLevel == 2);
        TechnologyLevelCalibrationDocument high = catalog.TechnologyLevels.Single(item =>
            item.TechnologyLevel == 6);
        int lowCap = FullFlightCalibrationModel.CalculateSafetyTurnCap(study, command, low);
        int highCap = FullFlightCalibrationModel.CalculateSafetyTurnCap(study, sensor, high);
        Require(lowCap >= study.MinimumSafetyTurns, "Low-TL safety cap ignored the minimum.");
        Require(highCap > lowCap, "Higher endurance did not increase the safety cap.");
    }

    private static void TestFullFlightCrossingWeave()
    {
        PreparedFullFlightCalibrationVariant crossing =
            FullFlightCalibrationModel.PrepareVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .Single(item => item.Id == "command-guided-m2-t2-crossing-weave-live");
        CoordinateDocument[] destinations = crossing.Scenario.Actions
            .Where(action => action.Type == "moveShip")
            .Select(action => action.Destination!)
            .Take(4)
            .ToArray();
        Require(
            destinations.Length == 4 &&
            destinations[0] is { Q: 16, R: 13 } &&
            destinations[1] is { Q: 17, R: 13 } &&
            destinations[2] is { Q: 17, R: 12 } &&
            destinations[3] is { Q: 16, R: 12 },
            "Crossing-weave did not produce its deterministic four-turn loop.");
    }

    private static ScenarioRunResult ExecuteTargetEnteredOpportunityScenario()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .Single(item => item.Id == "command-guided-m6-t2-turnback-live");
        return new ScenarioExecutor(variant.Scenario).Execute();
    }

    private static void TestTargetEnteredMissileOpportunity()
    {
        ScenarioRunResult result = ExecuteTargetEnteredOpportunityScenario();
        Require(
            result.TerminalOpportunities.Any(item =>
                item.Source == ScenarioTerminalOpportunitySource.TargetEnteredMissileHex),
            "Target movement onto an in-flight missile did not create the authoritative opportunity.");
    }

    private static void TestOpportunityDiagnosticsMatchAuthority()
    {
        ScenarioRunResult result = ExecuteTargetEnteredOpportunityScenario();
        int diagnostics = result.Runtime.Journal.Events.Count(item =>
            item.EventType == DiagnosticEventType.MissileTerminalOpportunity);
        Require(
            diagnostics == result.TerminalOpportunities.Count,
            "Diagnostic and authoritative terminal-opportunity counts diverged.");
    }

    private static void TestOperationalSafetyCapClassification()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .Single(item => item.Id == "command-guided-m6-t2-stationary-occluded");
        ScenarioDocument scenario = variant.Scenario;
        MissileDocument missile = scenario.Missiles.Single();
        missile.RetainedDatalink = null;
        const int operationalTurnLimit = 2;
        scenario.OperationalTurnLimit = operationalTurnLimit;

        int missileActions = 0;
        scenario.Actions = scenario.Actions
            .TakeWhile(action =>
            {
                if (string.Equals(
                        action.Type,
                        "advanceMissile",
                        StringComparison.OrdinalIgnoreCase))
                {
                    missileActions++;
                }
                return missileActions <= operationalTurnLimit;
            })
            .ToList();
        while (scenario.Actions.Count > 0 &&
               scenario.Actions.Count(action => string.Equals(
                   action.Type,
                   "advanceMissile",
                   StringComparison.OrdinalIgnoreCase)) > operationalTurnLimit)
        {
            scenario.Actions.RemoveAt(scenario.Actions.Count - 1);
        }

        Require(
            ScenarioPreflightValidator.Validate(scenario).Count == 0,
            "The forced operational-timeout scenario failed preflight.");
        MonteCarloTrialResult trial = MonteCarloTrialResult.Execute(
            scenario,
            variant.Id,
            trialIndex: 0,
            masterSeed: 21UL,
            randomSeedNamespace: "self-test-full-flight-timeout");
        Require(trial.Error is null, "Operational-timeout trial failed.");
        Require(
            trial.OperationalTimeoutReached && !trial.UnexplainedUnresolved,
            "Stalled missile was not classified as an explained operational timeout.");
        Require(
            trial.MissileActions == operationalTurnLimit,
            "Operational timeout did not consume the configured operational-turn limit.");
    }

    private static void TestOperationalTurnLimitMaterialization()
    {
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareVariants(
                CreateFullFlightStudy(),
                CreateCalibrationCatalog());
        Require(
            variants.All(item =>
                item.Scenario.OperationalTurnLimit == item.SafetyTurnCap &&
                item.Scenario.Actions.Count(action => action.Type == "advanceMissile") ==
                    item.SafetyTurnCap),
            "A full-flight variant did not materialize its derived operational turn limit.");
    }

    private static void TestVariantWorkerCeiling()
    {
        Require(
            FullFlightCalibrationRunner.ResolveVariantWorkerCount(24, 288) == 24,
            "Requested 24-worker execution did not resolve to 24 workers.");
        Require(
            FullFlightCalibrationRunner.ResolveVariantWorkerCount(32, 288) == 24,
            "Variant scheduler exceeded the 24-worker ceiling.");
        Require(
            FullFlightCalibrationRunner.ResolveVariantWorkerCount(8, 4) == 4,
            "Variant scheduler exceeded the available variant count.");
    }

    private static void TestTrialBlockSizing()
    {
        Require(
            FullFlightCalibrationRunner.ResolveTrialBlockSize(32) == 4,
            "A 32-trial scheduler proof did not resolve to four-trial blocks.");
        Require(
            FullFlightCalibrationRunner.ResolveTrialBlockSize(128) == 8,
            "A 128-trial run did not resolve to eight-trial blocks.");
        Require(
            FullFlightCalibrationRunner.ResolveTrialBlockSize(1_000) == 16,
            "A 1,000-trial calibration did not resolve to sixteen-trial blocks.");
    }

    private static void TestTrialBlockCoverage()
    {
        const int variantCount = 24;
        const int trialsPerVariant = 32;
        const int blockSize = 4;
        IReadOnlyList<FullFlightCalibrationRunner.TrialBlock> blocks =
            FullFlightCalibrationRunner.CreateTrialBlocks(
                variantCount,
                trialsPerVariant,
                blockSize);
        Require(
            blocks.Count == 192,
            "The 24-variant scheduler proof did not produce 192 trial blocks.");

        var coverage = new int[variantCount, trialsPerVariant];
        foreach (FullFlightCalibrationRunner.TrialBlock block in blocks)
        {
            Require(
                block.VariantIndex >= 0 && block.VariantIndex < variantCount,
                "A trial block referenced an invalid variant index.");
            Require(
                block.Count > 0 && block.Count <= blockSize,
                "A trial block exceeded its configured size.");
            for (int offset = 0; offset < block.Count; offset++)
            {
                int trialIndex = block.StartTrialIndex + offset;
                Require(
                    trialIndex >= 0 && trialIndex < trialsPerVariant,
                    "A trial block referenced an invalid trial index.");
                coverage[block.VariantIndex, trialIndex]++;
            }
        }

        for (int variantIndex = 0; variantIndex < variantCount; variantIndex++)
        {
            for (int trialIndex = 0; trialIndex < trialsPerVariant; trialIndex++)
            {
                Require(
                    coverage[variantIndex, trialIndex] == 1,
                    $"Variant {variantIndex} trial {trialIndex} was scheduled " +
                    $"{coverage[variantIndex, trialIndex]} times.");
            }
        }
    }

    private static void TestServerGarbageCollection()
    {
        Require(
            System.Runtime.GCSettings.IsServerGC,
            "The ScenarioRunner runtime did not enable server garbage collection.");
    }

    private static void TestCandidateCoordinateSearchDiagnostic(
        string scenarioPath)
    {
        string scenarioDirectory = Path.GetDirectoryName(
            Path.GetFullPath(scenarioPath)) ??
            throw new InvalidOperationException(
                "The deterministic scenario directory could not be resolved.");
        ScenarioDocument scenario = ScenarioDocumentSerialization.ReadScenario(
            Path.Combine(
                scenarioDirectory,
                "blocked-retained-report-search.json"));
        ShipDocument target = scenario.Ships.Single(item => item.Id == "ship-player");
        target.Position = new CoordinateDocument { Q = -1, R = 2 };
        ScenarioRunResult result = new ScenarioExecutor(
            scenario,
            new ScenarioExecutionOptions
            {
                EvaluateAssertions = false,
            }).Execute();
        DiagnosticEvent[] events = result.Runtime.Journal.Events.ToArray();
        Require(
            events.Any(item =>
                item.EventType == DiagnosticEventType.MissileSearchActivated &&
                item.Data.TryGetValue("searchTrigger", out string? trigger) &&
                trigger == "CandidateCoordinateReached"),
            "Candidate-coordinate arrival did not record Search/Wait activation.");
        Require(
            events.All(item =>
                item.EventType != DiagnosticEventType.MissileTerminalAcquisitionResolved),
            "A non-co-located candidate coordinate was mislabeled as terminal acquisition.");
    }

    private static void TestDiscardedJournalRetainsErrors(string scenarioPath)
    {
        ScenarioDocument scenario =
            ScenarioDocumentSerialization.ReadScenario(scenarioPath);
        scenario.InitialPhase = "Movement";
        string root = CreateTemporaryDirectory();
        try
        {
            MonteCarloBatchRunResult result = MonteCarloBatchRunner.Run(
                scenario,
                "self-test-error-journal",
                new MonteCarloBatchOptions
                {
                    Trials = 2,
                    MasterSeed = 210300UL,
                    Jobs = 1,
                    Resume = false,
                    CheckpointEvery = 2,
                    TraceSamples = 0,
                    KeepTrialJournal = false,
                },
                root);
            string errorsPath = Path.Combine(root, "errors.jsonl");
            Require(!result.Passed, "The deliberately invalid batch unexpectedly passed.");
            Require(File.Exists(errorsPath), "The error journal was not retained.");
            Require(
                File.ReadLines(errorsPath).Count() == 2,
                "The error journal did not preserve both failed trials.");
            Require(
                !File.Exists(Path.Combine(root, "trials.jsonl")),
                "The discarded full trial journal was unexpectedly retained.");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static void TestSchedulerProofCorpus()
    {
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareSchedulerProofVariants(
                CreateFullFlightStudy(),
                CreateCalibrationCatalog());
        Require(variants.Count == 24, "Scheduler proof corpus did not contain 24 variants.");
        Require(
            variants.Select(item => item.Id)
                .Distinct(StringComparer.Ordinal)
                .Count() == 24,
            "Scheduler proof variant IDs were not unique.");
        Require(
            variants.Select(item => item.TargetMovementPolicy)
                .Distinct(StringComparer.Ordinal)
                .Count() == 4,
            "Scheduler proof corpus did not cover all relative-motion policies.");
    }

    private static void TestDescriptiveDatalinkPolicies()
    {
        Require(
            FullFlightCalibrationRunner.IsInferentialDatalinkPolicy(
                FullFlightCalibrationModel.StationaryPolicy),
            "Stationary datalink comparison should remain inferential.");
        Require(
            FullFlightCalibrationRunner.IsInferentialDatalinkPolicy(
                FullFlightCalibrationModel.StraightRetreatPolicy),
            "Straight-retreat datalink comparison should remain inferential.");
        Require(
            !FullFlightCalibrationRunner.IsInferentialDatalinkPolicy(
                FullFlightCalibrationModel.CrossingWeavePolicy) &&
            !FullFlightCalibrationRunner.IsInferentialDatalinkPolicy(
                FullFlightCalibrationModel.TurnbackPolicy),
            "Crossing-weave and turnback datalink comparisons should be descriptive.");
        Require(
            !PairedMarginalStatistics.IsStatisticallyContradictory(
                "descriptive",
                observedDelta: -1.0,
                holmAdjustedPValue: 0.0,
                minimumPracticalDelta: 0.01,
                familywiseAlpha: 0.05),
            "A descriptive comparison was incorrectly treated as contradictory.");
    }

    private static void TestSemanticOcclusionContract()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .Single(item =>
                    item.Id == "command-guided-m4-t4-turnback-occluded");
        var beforeUpdate = new MonteCarloTrialResult();
        Require(
            FullFlightCalibrationRunner.DatalinkSemanticContractPassed(
                variant,
                beforeUpdate),
            "Occluded terminal resolution before a guidance update was rejected.");
        var blockedUpdate = new MonteCarloTrialResult
        {
            DatalinkUpdateAttempted = true,
            DatalinkBlockedObserved = true,
        };
        Require(
            FullFlightCalibrationRunner.DatalinkSemanticContractPassed(
                variant,
                blockedUpdate),
            "A correctly blocked guidance update was rejected.");
        var invalidFreshUpdate = new MonteCarloTrialResult
        {
            DatalinkUpdateAttempted = true,
            DatalinkLiveObserved = true,
            UsedFreshDatalinkGuidance = true,
        };
        Require(
            !FullFlightCalibrationRunner.DatalinkSemanticContractPassed(
                variant,
                invalidFreshUpdate),
            "Fresh guidance while occluded was not rejected.");
    }

    private static void TestScenarioExecutionPlanReuse(string scenarioPath)
    {
        ScenarioDocument scenario = PrepareStochasticScenario(scenarioPath);
        ScenarioExecutionPlan plan = ScenarioExecutionPlan.Prepare(scenario);
        Require(
            ReferenceEquals(plan.Document, scenario),
            "The execution plan did not retain its immutable scenario document.");
        Require(
            plan.ActionKinds.Count == scenario.Actions.Count,
            "The execution plan did not preclassify every action.");
        Require(
            plan.InitializationRequest.Missiles.Count == scenario.Missiles.Count,
            "The execution plan did not materialize the missile initialization request.");
        StarCluster.Core.Simulation.ScenarioInitializationResult runtime =
            StarCluster.Core.Simulation.ScenarioInitializationService.Initialize(
                plan.InitializationRequest,
                recordDiagnostics: false);
        Require(
            plan.CreateDefenses(runtime).Count == scenario.Defenses.Count,
            "The execution plan did not materialize every prepared defense.");
    }

    private static void TestCompactDiagnosticParity(string scenarioPath)
    {
        ScenarioDocument scenario = PrepareStochasticScenario(scenarioPath);
        ScenarioExecutionPlan plan = ScenarioExecutionPlan.Prepare(scenario);
        MonteCarloTrialResult diagnostic = MonteCarloTrialResult.Execute(
            plan,
            "compact-parity",
            7,
            220100UL,
            "compact-parity-seed",
            MonteCarloTrialExecutionMode.DiagnosticJournal);
        MonteCarloTrialResult compact = MonteCarloTrialResult.Execute(
            plan,
            "compact-parity",
            7,
            220100UL,
            "compact-parity-seed",
            MonteCarloTrialExecutionMode.CompactMetrics);
        string diagnosticJson = JsonSerializer.Serialize(
            diagnostic,
            ScenarioDocumentSerialization.CompactWriteOptions);
        string compactJson = JsonSerializer.Serialize(
            compact,
            ScenarioDocumentSerialization.CompactWriteOptions);
        Require(
            string.Equals(diagnosticJson, compactJson, StringComparison.Ordinal),
            "Compact execution changed the canonical Monte Carlo trial result.");
    }

    private static void TestCompactJournalSuppression(string scenarioPath)
    {
        ScenarioDocument scenario = PrepareStochasticScenario(scenarioPath);
        ScenarioExecutionPlan plan = ScenarioExecutionPlan.Prepare(scenario);
        ScenarioRunResult result = new ScenarioExecutor(
            plan,
            new ScenarioExecutionOptions
            {
                EvaluateAssertions = false,
                RecordCompletionEvent = false,
                RecordDiagnostics = false,
                CaptureExecutionMetrics = true,
            }).Execute();
        Require(
            result.Runtime.Journal.Events.Count == 0,
            "Compact execution materialized diagnostic journal events.");
        Require(
            result.ExecutionMetrics is not null,
            "Compact execution did not capture direct metrics.");
    }

    private static void TestCompactTrackRefreshParity(string scenarioPath)
    {
        ScenarioDocument scenario = PrepareStochasticScenario(scenarioPath);
        ScenarioExecutionPlan plan = ScenarioExecutionPlan.Prepare(scenario);
        ScenarioRunResult diagnostic = new ScenarioExecutor(
            plan,
            new ScenarioExecutionOptions
            {
                EvaluateAssertions = false,
                RecordCompletionEvent = false,
                RecordDiagnostics = true,
                CaptureExecutionMetrics = true,
            }).Execute();
        ScenarioRunResult compact = new ScenarioExecutor(
            plan,
            new ScenarioExecutionOptions
            {
                EvaluateAssertions = false,
                RecordCompletionEvent = false,
                RecordDiagnostics = false,
                CaptureExecutionMetrics = true,
            }).Execute();
        GuidedMissileSalvo diagnosticMissile = diagnostic.Runtime.MissileEngagement.Salvos.Single();
        GuidedMissileSalvo compactMissile = compact.Runtime.MissileEngagement.Salvos.Single();
        Require(
            diagnosticMissile.Status == compactMissile.Status &&
            diagnosticMissile.CurrentCoordinate == compactMissile.CurrentCoordinate &&
            diagnosticMissile.DistanceTraveled == compactMissile.DistanceTraveled &&
            diagnosticMissile.TotalFuelSpent == compactMissile.TotalFuelSpent,
            "Compact track refresh changed authoritative missile state.");

        string[] diagnosticTracks = diagnostic.Runtime.Tracks.Records
            .OrderBy(item => item.ObserverId, StringComparer.Ordinal)
            .ThenBy(item => item.TargetId, StringComparer.Ordinal)
            .Select(TrackFingerprint)
            .ToArray();
        string[] compactTracks = compact.Runtime.Tracks.Records
            .OrderBy(item => item.ObserverId, StringComparer.Ordinal)
            .ThenBy(item => item.TargetId, StringComparer.Ordinal)
            .Select(TrackFingerprint)
            .ToArray();
        Require(
            diagnosticTracks.SequenceEqual(compactTracks, StringComparer.Ordinal),
            "Compact track refresh changed authoritative tactical-track state.");
    }


    private static void TestProfiledTrialParity()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareSchedulerProofVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .First(item =>
                    item.TargetMovementPolicy !=
                        FullFlightCalibrationModel.StationaryPolicy);
        ScenarioExecutionPlan plan = ScenarioExecutionPlan.Prepare(variant.Scenario);
        MonteCarloTrialResult baseline = MonteCarloTrialResult.Execute(
            plan,
            variant.Id,
            3,
            220200UL,
            "allocation-profile-parity",
            MonteCarloTrialExecutionMode.CompactMetrics);
        var profile = new ScenarioAllocationProfile();
        MonteCarloTrialResult profiled = MonteCarloTrialResult.Execute(
            plan,
            variant.Id,
            3,
            220200UL,
            "allocation-profile-parity",
            MonteCarloTrialExecutionMode.CompactMetrics,
            profile);
        string baselineJson = JsonSerializer.Serialize(
            baseline,
            ScenarioDocumentSerialization.CompactWriteOptions);
        string profiledJson = JsonSerializer.Serialize(
            profiled,
            ScenarioDocumentSerialization.CompactWriteOptions);
        Require(
            string.Equals(baselineJson, profiledJson, StringComparison.Ordinal),
            "Allocation profiling changed the canonical trial outcome.");
    }

    private static void TestAllocationStageHierarchy()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareSchedulerProofVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .First(item =>
                    item.TargetMovementPolicy !=
                        FullFlightCalibrationModel.StationaryPolicy);
        ScenarioExecutionPlan plan = ScenarioExecutionPlan.Prepare(variant.Scenario);
        var profile = new ScenarioAllocationProfile();
        MonteCarloTrialResult result = MonteCarloTrialResult.Execute(
            plan,
            variant.Id,
            5,
            220201UL,
            "allocation-profile-hierarchy",
            MonteCarloTrialExecutionMode.CompactMetrics,
            profile);
        Require(
            string.IsNullOrWhiteSpace(result.Error),
            "The profiled hierarchy trial returned an execution error.");

        ScenarioAllocationMeasurement total = profile.Get(
            ScenarioAllocationStage.TrialTotal);
        Require(
            total.InvocationCount == 1 && total.AllocatedBytes > 0,
            "The allocation profile did not record one positive trial total.");
        Require(
            profile.Get(ScenarioAllocationStage.RuntimeInitialization)
                .InvocationCount == 1,
            "Runtime initialization was not attributed exactly once.");
        Require(
            profile.Get(ScenarioAllocationStage.ShipMovement)
                .InvocationCount > 0,
            "Ship movement was not represented in the profile corpus.");
        Require(
            profile.Get(ScenarioAllocationStage.MissileAdvancement)
                .InvocationCount > 0,
            "Missile advancement was not represented in the profile corpus.");
        Require(
            profile.Get(ScenarioAllocationStage.PhaseAdvancement)
                .InvocationCount > 0,
            "Phase advancement was not represented in the profile corpus.");
        Require(
            profile.Get(ScenarioAllocationStage.ResultProjection)
                .InvocationCount == 1,
            "Result projection was not attributed exactly once.");

        ScenarioAllocationStage[] topLevel =
        {
            ScenarioAllocationStage.SeedDerivation,
            ScenarioAllocationStage.TrialSetup,
            ScenarioAllocationStage.ExecutorConstruction,
            ScenarioAllocationStage.ShipMovement,
            ScenarioAllocationStage.MissileAdvancement,
            ScenarioAllocationStage.PhaseAdvancement,
            ScenarioAllocationStage.ScenarioFinalization,
            ScenarioAllocationStage.ResultProjection,
        };
        long topLevelBytes = topLevel.Sum(
            stage => profile.Get(stage).AllocatedBytes);
        Require(
            topLevelBytes <= total.AllocatedBytes,
            "Top-level allocation stages exceeded the measured trial total.");

        long missileDetailBytes = new[]
        {
            ScenarioAllocationStage.MissileInterceptionContext,
            ScenarioAllocationStage.MissileDatalinkUpdate,
            ScenarioAllocationStage.MissileGuidanceAdvance,
            ScenarioAllocationStage.MissileOutcomeCapture,
            ScenarioAllocationStage.TrackRefreshAfterMissileMovement,
        }.Sum(stage => profile.Get(stage).AllocatedBytes);
        Require(
            missileDetailBytes <= profile.Get(
                ScenarioAllocationStage.MissileAdvancement).AllocatedBytes,
            "Missile detail allocation exceeded its parent stage.");
    }


    private static void TestOptimizedCalibrationMapSizing()
    {
        IReadOnlyList<PreparedFullFlightCalibrationVariant> variants =
            FullFlightCalibrationModel.PrepareVariants(
                CreateFullFlightStudy(),
                CreateCalibrationCatalog());
        int minimumRadius = variants.Min(item => item.Scenario.Map.Radius);
        int maximumRadius = variants.Max(item => item.Scenario.Map.Radius);
        Require(
            minimumRadius == 30 &&
            maximumRadius > minimumRadius &&
            maximumRadius < FullFlightCalibrationModel.ReferenceMapRadius,
            $"Optimized calibration radius range was {minimumRadius}..{maximumRadius}, outside the expected bounded range.");
        Require(
            variants.All(item =>
                item.Scenario.Map.Radius <
                    FullFlightCalibrationModel.ReferenceMapRadius),
            "An optimized calibration map retained the radius-192 reference topology.");
        Require(
            FullFlightCalibrationModel.CalculateHexCellCount(5) == 91 &&
            FullFlightCalibrationModel.CalculateHexCellCount(192) == 111169,
            "Hex-cell cardinality calculation changed.");

        long referenceCells = FullFlightCalibrationModel.CalculateHexCellCount(
            FullFlightCalibrationModel.ReferenceMapRadius);
        double averageRetention = variants.Average(item =>
            FullFlightCalibrationModel.CalculateHexCellCount(
                item.Scenario.Map.Radius) /
            (double)referenceCells);
        Require(
            averageRetention < 0.05,
            $"Optimized calibration maps retained {averageRetention:P2} of reference cells.");

        foreach (PreparedFullFlightCalibrationVariant variant in variants)
        {
            int requiredRadius =
                FullFlightCalibrationModel.CalculateRequiredExplicitCoordinateRadius(
                    variant.Scenario);
            Require(
                variant.Scenario.Map.Radius - requiredRadius >=
                    FullFlightCalibrationModel.OptimizedMapSafetyMargin,
                $"Variant '{variant.Id}' did not preserve the configured map safety margin.");
        }
    }

    private static void TestOptimizedReferenceMapParity()
    {
        FullFlightCalibrationStudyDocument study = CreateFullFlightStudy();
        TechnologyProfileCatalogDocument catalog = CreateCalibrationCatalog();
        const string variantId =
            "sensor-plus-seeker-m6-t6-straight-retreat-occluded";
        PreparedFullFlightCalibrationVariant optimized =
            FullFlightCalibrationModel.PrepareVariants(
                    study,
                    catalog,
                    FullFlightMapSizingMode.OptimizedVariant)
                .Single(item => item.Id == variantId);
        PreparedFullFlightCalibrationVariant reference =
            FullFlightCalibrationModel.PrepareVariants(
                    study,
                    catalog,
                    FullFlightMapSizingMode.ReferenceRadius192)
                .Single(item => item.Id == variantId);
        Require(
            optimized.Scenario.Map.Radius < reference.Scenario.Map.Radius &&
            reference.Scenario.Map.Radius ==
                FullFlightCalibrationModel.ReferenceMapRadius,
            "Representative optimized and reference maps were not distinct.");

        MonteCarloTrialResult optimizedResult = MonteCarloTrialResult.Execute(
            ScenarioExecutionPlan.Prepare(optimized.Scenario),
            optimized.Id,
            7,
            220202UL,
            "map-sizing-parity",
            MonteCarloTrialExecutionMode.CompactMetrics);
        MonteCarloTrialResult referenceResult = MonteCarloTrialResult.Execute(
            ScenarioExecutionPlan.Prepare(reference.Scenario),
            reference.Id,
            7,
            220202UL,
            "map-sizing-parity",
            MonteCarloTrialExecutionMode.CompactMetrics);
        Require(
            string.IsNullOrWhiteSpace(optimizedResult.Error) &&
            string.IsNullOrWhiteSpace(referenceResult.Error),
            "Representative map-parity trials returned an execution error.");
        string optimizedJson = JsonSerializer.Serialize(
            optimizedResult,
            ScenarioDocumentSerialization.CompactWriteOptions);
        string referenceJson = JsonSerializer.Serialize(
            referenceResult,
            ScenarioDocumentSerialization.CompactWriteOptions);
        Require(
            string.Equals(optimizedJson, referenceJson, StringComparison.Ordinal),
            "Representative optimized and radius-192 reference maps changed the canonical trial result.");
    }

    private static void TestInitializationStageAttribution()
    {
        PreparedFullFlightCalibrationVariant variant =
            FullFlightCalibrationModel.PrepareSchedulerProofVariants(
                    CreateFullFlightStudy(),
                    CreateCalibrationCatalog())
                .First(item =>
                    item.TargetMovementPolicy !=
                        FullFlightCalibrationModel.StationaryPolicy);
        var profile = new ScenarioAllocationProfile();
        MonteCarloTrialResult result = MonteCarloTrialResult.Execute(
            ScenarioExecutionPlan.Prepare(variant.Scenario),
            variant.Id,
            8,
            220203UL,
            "initialization-attribution",
            MonteCarloTrialExecutionMode.CompactMetrics,
            profile);
        Require(
            string.IsNullOrWhiteSpace(result.Error),
            "Initialization-attribution trial returned an execution error.");

        ScenarioAllocationStage[] initializationStages =
        {
            ScenarioAllocationStage.InitializationMapCreation,
            ScenarioAllocationStage.InitializationStaticObjectPlacement,
            ScenarioAllocationStage.InitializationShipStateCreation,
            ScenarioAllocationStage.InitializationPriorTrackSeeding,
            ScenarioAllocationStage.InitializationMissileStateCreation,
            ScenarioAllocationStage.InitializationTurnAndJournalCreation,
            ScenarioAllocationStage.InitializationInitialTrackRefresh,
            ScenarioAllocationStage.InitializationDiagnostics,
            ScenarioAllocationStage.InitializationResultConstruction,
        };
        Require(
            initializationStages.All(stage =>
                profile.Get(stage).InvocationCount == 1),
            "One or more initialization detail stages were not recorded exactly once.");
        long detailBytes = initializationStages.Sum(stage =>
            profile.Get(stage).AllocatedBytes);
        long runtimeBytes = profile.Get(
            ScenarioAllocationStage.RuntimeInitialization).AllocatedBytes;
        Require(
            detailBytes <= runtimeBytes,
            "Initialization detail allocation exceeded RuntimeInitialization.");
        long mapBytes = profile.Get(
            ScenarioAllocationStage.InitializationMapCreation).AllocatedBytes;
        Require(
            mapBytes > 0 &&
            initializationStages
                .Where(stage =>
                    stage != ScenarioAllocationStage.InitializationMapCreation)
                .All(stage => mapBytes >= profile.Get(stage).AllocatedBytes),
            "Map creation was not isolated as the largest initialization detail stage.");
    }

    private static string TrackFingerprint(
        StarCluster.Core.Combat.Tracking.TacticalTrackRecord record) =>
        string.Join(
            "|",
            record.ObserverId,
            record.TargetId,
            record.SourceType,
            record.Quality,
            record.EstimatedCoordinate?.ToString() ?? "none",
            record.LastObservedCoordinate?.ToString() ?? "none",
            record.LastUpdatedSequence,
            record.MissedUpdateCount,
            record.UncertaintyRadiusHexes,
            record.LastObservedEpoch?.ToString() ?? "none",
            record.LastAgedEpoch?.ToString() ?? "none",
            record.ActiveObservedSegmentId?.ToString() ?? "none",
            string.Join(",", record.ObservedCoordinateHistory),
            string.Join(",", record.ObservedSamples.Select(item => item.ToString())));

    private static void TestCalibrationPdsChance()
    {
        var pds = new PdsTechnologyCalibrationDocument
        {
            EqualTechnologyInterceptionChancePercent = 35,
            InterceptionChancePercentPerTechnologyDelta = 10,
            MinimumInterceptionChancePercent = 5,
            MaximumInterceptionChancePercent = 95,
        };
        int lower = TechnologyCalibrationModel.CalculatePdsInterceptionChancePercent(
            pds,
            pdsTechnologyLevel: 2,
            missileTechnologyLevel: 6);
        int equal = TechnologyCalibrationModel.CalculatePdsInterceptionChancePercent(
            pds,
            pdsTechnologyLevel: 4,
            missileTechnologyLevel: 4);
        int higher = TechnologyCalibrationModel.CalculatePdsInterceptionChancePercent(
            pds,
            pdsTechnologyLevel: 6,
            missileTechnologyLevel: 2);
        Require(lower == 5, "Lower-TL PDS did not clamp to 5%.");
        Require(equal == 35, "Equal-TL PDS did not produce 35%.");
        Require(higher == 75, "Higher-TL PDS did not produce 75%.");
    }

    private static void TestCalibrationAcquisition()
    {
        TechnologyProfileCatalogDocument catalog = CreateCalibrationCatalog();
        RepresentativeMissileProfileDocument seekerOnly = catalog.MissileProfiles
            .Single(item => item.Id == "seeker-only");
        TechnologyLevelCalibrationDocument missile = catalog.TechnologyLevels
            .Single(item => item.TechnologyLevel == 2);
        TechnologyLevelCalibrationDocument equalEcm = catalog.TechnologyLevels
            .Single(item => item.TechnologyLevel == 2);
        TechnologyLevelCalibrationDocument superiorEcm = catalog.TechnologyLevels
            .Single(item => item.TechnologyLevel == 6);
        double equal = TechnologyCalibrationModel.CalculateAcquisitionSuccessProbability(
            seekerOnly,
            missile,
            equalEcm,
            catalog);
        double inferior = TechnologyCalibrationModel.CalculateAcquisitionSuccessProbability(
            seekerOnly,
            missile,
            superiorEcm,
            catalog);
        Require(Math.Abs(equal - 0.60) < 1e-12, "Equal-TL seeker acquisition was not 60%.");
        Require(Math.Abs(inferior - 0.20) < 1e-12, "Superior ECM did not reduce seeker acquisition to 20%.");
    }

    private static void TestCalibrationMatrix(string scenarioPath)
    {
        var study = new TechnologyCalibrationStudyDocument
        {
            Id = "self-test-calibration",
            Name = "Self-test calibration",
            BaseScenario = scenarioPath,
            ProfileCatalog = "unused",
            MissileProfiles =
            {
                "command-guided",
                "seeker-only",
                "sensor-only",
                "sensor-plus-seeker",
            },
            MissileTechnologyLevels = { 2, 4, 6 },
            PdsTechnologyLevels = { 2, 4, 6 },
            TargetEcmTechnologyLevels = { 2, 4, 6 },
        };
        TechnologyProfileCatalogDocument catalog = CreateCalibrationCatalog();
        ScenarioDocument scenario = ScenarioDocumentSerialization.ReadScenario(scenarioPath);
        IReadOnlyList<PreparedTechnologyCalibrationVariant> variants =
            TechnologyCalibrationModel.PrepareVariants(study, catalog, scenario);
        Require(variants.Count == 108, "Calibration matrix did not produce 108 variants.");
        Require(
            variants.Select(item => item.Id).Distinct(StringComparer.Ordinal).Count() == 108,
            "Calibration variant IDs are not unique.");
        Require(
            variants.Any(item => item.Id == "seeker-only-m4-p6-e2"),
            "Expected stable calibration variant ID was not produced.");
    }

    private static void TestEffectiveHitMetric()
    {
        var trials = new[]
        {
            new MonteCarloTrialResult
            {
                TrialIndex = 0,
                FinalStatus = "Expended",
                FinalOutcome = "Hit",
            },
            new MonteCarloTrialResult
            {
                TrialIndex = 1,
                FinalStatus = "Expended",
                FinalOutcome = "CriticalHit",
            },
            new MonteCarloTrialResult
            {
                TrialIndex = 2,
                FinalStatus = "Expended",
                FinalOutcome = "Miss",
            },
        };
        MonteCarloResultsDocument results = MonteCarloStatistics.Aggregate(
            trials,
            "run",
            "scenario",
            "variant",
            1UL,
            "scenario-hash",
            "runner-hash",
            "core-hash");
        ProbabilityMetricSummary metric = results.Metrics.Single(item =>
            item.Key == "effect.effectiveHit");
        Require(metric.Count == 2, "Effective-hit aggregation did not count hit plus critical hit.");
    }

    private static FullFlightCalibrationStudyDocument CreateFullFlightStudy() => new()
    {
        Id = "self-test-full-flight",
        Name = "Self-test full-flight calibration",
        ProfileCatalog = "unused",
        TrialsPerVariant = 16,
        MasterSeed = 21UL,
        MinimumSafetyTurns = 2,
        SafetyTurnBuffer = 1,
        FixedPdsTechnologyLevel = 4,
        FixedTargetEcmTechnologyLevel = 4,
        MissileProfiles =
        {
            "command-guided",
            "seeker-only",
            "sensor-only",
            "sensor-plus-seeker",
        },
        MissileTechnologyLevels = { 2, 4, 6 },
        TargetPropulsionTechnologyLevels = { 2, 4, 6 },
        TargetMovementPolicies =
        {
            "stationary",
            "straight-retreat",
            "crossing-weave",
            "turnback",
        },
        DatalinkConditions = { "live", "occluded" },
    };

    private static TechnologyProfileCatalogDocument CreateCalibrationCatalog()
    {
        var catalog = new TechnologyProfileCatalogDocument
        {
            Id = "self-test-catalog",
            Name = "Self-test catalog",
            MissileProfiles =
            {
                new RepresentativeMissileProfileDocument
                {
                    Id = "command-guided",
                    Name = "Command-guided",
                    DatalinkInstalled = true,
                },
                new RepresentativeMissileProfileDocument
                {
                    Id = "seeker-only",
                    Name = "Seeker-only",
                    DatalinkInstalled = true,
                    SeekerInstalled = true,
                },
                new RepresentativeMissileProfileDocument
                {
                    Id = "sensor-only",
                    Name = "Sensor-only",
                    DatalinkInstalled = true,
                    SensorInstalled = true,
                },
                new RepresentativeMissileProfileDocument
                {
                    Id = "sensor-plus-seeker",
                    Name = "Sensor plus seeker",
                    DatalinkInstalled = true,
                    SensorInstalled = true,
                    SeekerInstalled = true,
                },
            },
        };
        catalog.TechnologyLevels.Add(CreateTechnologyLevel(2, 60, 60, 2, 10));
        catalog.TechnologyLevels.Add(CreateTechnologyLevel(4, 70, 70, 4, 15));
        catalog.TechnologyLevels.Add(CreateTechnologyLevel(6, 80, 80, 6, 20));
        return catalog;
    }

    private static TechnologyLevelCalibrationDocument CreateTechnologyLevel(
        int level,
        int hit,
        int acquisition,
        int eccm,
        int accuracy) => new()
        {
            TechnologyLevel = level,
            FlightSpeedHexesPerTurn = level <= 2 ? 2 : level <= 4 ? 3 : 4,
            ShipMovementHexesPerTurn = level <= 2 ? 1 : level <= 4 ? 2 : 3,
            MaximumRangeHexes = 4 + (level * 2),
            DatalinkRetainedReportAgePhases = Math.Max(1, level / 2),
            SensorFirmRangeHexes = level + 1,
            SensorApproximateRangeHexes = level + 3,
            SensorActiveModeBonusHexes = Math.Max(1, level / 2),
            SensorMaximumLocalTrackAgeEpochs = Math.Max(1, level / 2),
            GuidanceBaseHitChancePercent = hit,
            SeekerBaseAcquisitionChancePercent = acquisition,
            SeekerEccmStrength = eccm,
            SeekerAccuracyBonusPercent = accuracy,
            TerminalEcmStrength = level,
        };

    private static ScenarioDocument PrepareStochasticScenario(string scenarioPath)
    {
        ScenarioDocument scenario =
            ScenarioDocumentSerialization.ReadScenario(scenarioPath);
        using JsonDocument value = JsonDocument.Parse("40");
        return ScenarioOverrideApplier.Apply(
            scenario,
            new[]
            {
                new ScenarioOverrideDocument
                {
                    Path = "defenses[0].interceptionChancePercent",
                    Value = value.RootElement.Clone(),
                },
            });
    }

    private static MonteCarloBatchOptions Options(
        int trials,
        int jobs,
        bool resume) => new()
        {
            Trials = trials,
            MasterSeed = 190100UL,
            Jobs = jobs,
            Resume = resume,
            CheckpointEvery = 32,
            TraceSamples = 0,
        };

    private static string CreateTemporaryDirectory()
    {
        string path = Path.Combine(
            Path.GetTempPath(),
            "star-cluster-runner-self-test-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}
