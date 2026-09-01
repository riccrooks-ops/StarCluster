# Checkpoint 74d - Degraded-Fire Firm-Reference Gate Semantics Hotfix

## Intent

Checkpoint 74d is a release-gate semantics hotfix for Checkpoint 74/74a/74b/74c. Native CP74c successfully passed repository validation, the warning-as-error build, all 853 unit tests, deterministic scenarios, TL1 Phase A/B, construction checks, Sensor/EW foundation, the CP74 actual-consumer preflight, and all 20 one-trial smoke variants with zero smoke release-gate failures. All 20 substantive variants / 200,000 trials also completed. The substantive stage then failed exactly one release gate: `tl1-c74-firm-reference-clean`.

The failed gate conflated a configuration invariant with whole-engagement telemetry. CP74 firm-reference variants are correctly configured with no ECM or ECCM and use Balanced-0 AcquisitionFirstAutoActive at fixed range 2 or 3. However, `MeanFirmTrackEvaluations*` and `MeanApproximateTrackEvaluations*` are cumulative whole-fight telemetry. Later combat damage can legitimately degrade or disable Active Sensors and produce Approximate observations even though the reference began unjammed and behaved correctly. Therefore a release gate must not require zero Approximate observations across the entire engagement.

CP74d changes the Firm-reference release predicate to validate the actual invariant: all four reference lanes must establish Firm tracks, spend zero ECM/ECCM Tactical Power, and execute ordinary direct fire. Whole-fight Approximate observations are allowed after legitimate sensor damage. No combat mechanic, study input, degraded-fire penalty, AI doctrine, Concept content, production weapon definition, or outcome target changes.

## Native evidence preceding the hotfix

The CP74c native run established before the gate failure:

- warning-as-error build: 0 warnings, 0 errors;
- 853/853 unit tests passed;
- deterministic moving-missile scenarios passed;
- TL1 Phase A and Phase B corpora passed;
- TL1 35-Space construction envelope passed;
- TL1 Sensor/EW foundation passed;
- CP74 actual-consumer preflight passed;
- all 20 one-trial smoke variants completed and all smoke gates passed;
- all 20 substantive variants / 200,000 trials completed;
- the substantive report listed exactly one failed gate: `tl1-c74-firm-reference-clean`.

## Expanded mismatch audit

Before packaging CP74d, every CP74 study-specific gate is audited against the telemetry semantics it consumes:

1. `tl1-c74-variant-coverage`: cardinality and trial-error invariant only.
2. `tl1-c74-firm-reference-clean`: now checks Firm observations, zero ECM/ECCM power, and ordinary direct fire; it does not require zero later Approximate observations.
3. `tl1-c74-firm-only-approx-blocked`: controlled bilateral ECM/no-ECCM lanes must produce Approximate observations and block Firm-only direct fire.
4. `tl1-c74-trait-enables-approximate-fire`: trait lanes must produce Approximate observations and actually fire with a positive final hit chance.
5. `tl1-c74-accuracy-penalty-sweep-configured`: validates only the configured symmetric -10/-20/-30 candidate values; observed accuracy/outcome ordering remains review evidence.
6. `tl1-c74-no-missile-degraded-fire`: validates the direct-fire-only study scope.
7. `tl1-c74-outcomes-review-only`: deliberately prevents win-rate/pacing targets from becoming release gates.

The actual-consumer validator is also rechecked against the study JSON: Firm references are ECM=None/ECCM=None and trait-off; all Approximate lanes are bilateral ECM=Normal/ECCM=None; missiles and secondary weapon families remain excluded.

CP74d additionally adds a ScenarioRunner self-test for the corrected Firm-reference predicate. The self-test proves that a clean unjammed reference is accepted and that actual ECM power contamination is rejected. ScenarioRunner self-test count therefore rises from 46 to 47.

## Degraded-fire foundation retained unchanged

`tl1-itc16-approximate-track-degraded-fire` remains the same 20-variant diagnostic: 2 direct-fire family orientations x 2 fixed ranges x 5 track/penalty cases. Production weapons remain Firm-only. The diagnostic trait remains opt-in, its -10/-20/-30 percentage-point candidates remain study-only, and missiles/torpedoes remain excluded from degraded direct fire.

## Native acceptance

Extract this complete repository over the repository root, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74d\apply_checkpoint_74d.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-74d\apply_checkpoint_74d.ps1 -Jobs 24
```

Expected normal workload:

- 11 runner stages.
- 853 unit tests if no unrelated test-count changes occur.
- 924 deterministic Sensor/EW foundation rows.
- 20-variant actual-consumer degraded-fire preflight.
- 20 one-trial full-pipeline smoke executions.
- 20 substantive variants / 200,000 substantive trials.
- 47 ScenarioRunner self-tests.

## Deep Calibration

Do not run by default. CP74d changes only release-gate semantics and adds a deterministic self-test for that gate; no substantive gameplay dependency changes.
