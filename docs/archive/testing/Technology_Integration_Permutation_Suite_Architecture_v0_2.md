# Technology Integration Permutation Suite Architecture v0.2

## Purpose

The Technology Integration Permutation Suite is the standing cross-subsystem calibration framework for sequential Star Cluster technology design. It prevents each checkpoint from inventing a new stochastic architecture while preserving causal isolation.

## Current package boundary

Checkpoint 82 consolidates the accepted Checkpoint 79a / 80 / 81a information-control evidence into `tl2_computing_sensor_ew_working_profile_v0_1.json`. That package is a **validated working candidate**, not production component data.

The validated TL2 information-control package carries:

- Tactical Computer ordinary targeting **+12 pp**;
- computer-owned degraded-fire penalty **-25 pp**;
- Evasive Compensation **0**;
- Sensor Discrimination Resistance **1**;
- ECM normal ceiling **2** at **1 TP/rating**;
- ECCM normal ceiling **2** at **1 TP/rating**.

Sensor range, reactor growth, and new TL2 Sensor/EW overload/efficiency behavior remain outside that promotion boundary.

## Reusable axes

The machine-readable v0.2 suite defines reusable axes for weapon/opponent family, geometry, information-control package, power environment, degraded-fire permission, and doctrine. Later checkpoints extend only the dimension whose dependency changed. A study should not activate every Cartesian combination merely because the suite can describe it.

## Pairing and execution

Use common random streams for candidate/control pairs where practical. Any new or materially changed integrated study must execute the actual-consumer preflight and a one-trial full-pipeline smoke before substantive Monte Carlo. Smoke gates validate configuration/mechanics, not statistical outcomes.

## Cross-study integration audit

Before handoff, audit the new/changed study through:

1. required-variant dispatch;
2. pre-run validation;
3. shared/global release-gate classifications, including policy telemetry;
4. current study-family execution whitelists such as reactive EW;
5. study-specific gates;
6. report writers/output routing;
7. schema and baseline bindings;
8. checkpoint stage definitions and workload accounting.

This checklist is mandatory even when local native PowerShell/.NET execution is unavailable.

## Historical continuity

`technology_integration_permutation_suite_v0_1.json` remains the exact CP81-era coverage definition for reproducibility. v0.2 is the current planning definition and must not rewrite historical study IDs or outputs merely for naming cleanup.
