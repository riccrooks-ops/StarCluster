# Checkpoint 69 Validation Tiers

## Must always run

Checkpoint 69d normal acceptance contains eleven stages:

1. accepted deterministic moving-missile scenarios;
2. TL1 Phase A mechanics corpus;
3. TL1 Phase B direct-fire corpus;
4. TL1 35-Space deterministic construction envelope;
5. TL1 deterministic Sensor/EW foundation and range sweep;
6. executable TL1 Balanced-0/1/2 integrated-loader and coverage preflight;
7. 72-variant, one-trial-per-variant full-pipeline execution smoke;
8. TL1 Balanced-0/1/2 operational Sensor/EW candidate combat;
9. deterministic auxiliary resource endurance;
10. Checkpoint 53 resource-semantics lock;
11. ScenarioRunner self-tests.

The deterministic foundation evaluates **7 profiles x 12 causal contexts x 11 ranges = 924 rows**. The operational candidate study evaluates **72 Monte Carlo variants / 720,000 default trials**.

The normal suite therefore contains **11 stages / 72 substantive Monte Carlo variants / 720,000 substantive default trials**, plus **72 smoke trials** (720,072 total trial executions). The CP69d preflight invokes the actual integrated C# consumer and catalog binding path without trials; the smoke stage then exercises every candidate variant through the complete simulation, gate, and report pipeline once before the full study.

## Deep Calibration

Deep Calibration retains the accepted historical TL1 calibration corpus, including Checkpoint 65b geometry and Checkpoint 67a overload/EW evidence, and adds the current Checkpoint 69 deterministic foundation plus operational candidate stage.

Checkpoint 69d Deep Calibration contains **30 stages / 1,616 substantive Monte Carlo variants / 16,160,000 substantive default trials**, plus the same **72 smoke trials** (16,160,072 total trial executions).

Deep Calibration is optional for initial Checkpoint 69 acceptance. The substantive Sensor/EW change is directly exercised by the normal deterministic and operational stages. Run Deep Calibration only when normal evidence indicates an interacting regression or when a later promotion changes production Sensor/EW values used by historical studies.

## Release interpretation

Blocking gates verify repository integrity, native dependencies, deterministic causal semantics, same-hex LOS/EW behavior, candidate/matrix coverage, power/fuel accounting, telemetry integrity, and execution without trial errors. For the 1-TP normal Active Sensor mode, cumulative trial power is validated against the count of powered sensor evaluations rather than against a single-use constant.

No target win rate and no preferred sensor candidate is blocking. Balanced-0/1/2 remain candidates until their operational evidence is reviewed.
