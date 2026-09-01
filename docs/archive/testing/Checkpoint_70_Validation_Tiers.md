# Checkpoint 70 Validation Tiers

## Must always run

Checkpoint 70 normal acceptance contains eleven stages:

1. accepted deterministic moving-missile scenarios;
2. TL1 Phase A mechanics corpus;
3. TL1 Phase B direct-fire corpus;
4. TL1 35-Space deterministic construction envelope;
5. TL1 deterministic Sensor/EW foundation and range sweep;
6. executable CP70 ECM-cost integrated-loader and coverage preflight;
7. 99-variant, one-trial-per-variant full-pipeline execution smoke;
8. TL1 ECM Tactical Power cost and point-blank counterplay study;
9. deterministic auxiliary resource endurance;
10. Checkpoint 53 resource-semantics lock;
11. ScenarioRunner self-tests.

The deterministic Sensor/EW foundation remains **924 rows**. The substantive CP70 study is **99 variants / 990,000 default trials**, preceded by **99 smoke trials**. Total trial executions are therefore **990,099**, not 1,980,000; the acceptance aggregator honors the smoke stage's explicit `trialsPerVariant = 1`.

## Deep Calibration

Deep Calibration retains the historical TL1 calibration corpus but replaces the CP69 candidate preflight/smoke/full study with the current CP70 equivalents. It contains **30 stages / 1,643 substantive Monte Carlo variants / 16,430,000 substantive default trials**, plus **99 smoke trials** for **16,430,099 total trial executions**.

Deep Calibration is not required for initial CP70 acceptance. The normal suite directly exercises the changed EW power-cost path and fixed same-hex geometry.

## Release interpretation

Blocking gates verify repository integrity, native dependencies, build/tests, deterministic causal Sensor/EW semantics, exact 99-variant matrix coverage, fixed range-zero geometry, 1-TP Active Sensor accounting, actual exercise of all five requested ECM costs, actual ECCM counter use, zero historical static EW penalty, and execution without trial errors.

No target win rate is blocking. ECM costs 2-5 are sensitivity values only. A later design decision must distinguish between a healthy power-opportunity-cost solution and evidence that the same-hex discrimination rule itself needs a principled constraint.
