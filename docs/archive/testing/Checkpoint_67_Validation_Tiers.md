# Checkpoint 67 Validation Tiers

## Must always run

Checkpoint 67 normal acceptance contains eight stages:

1. accepted deterministic moving-missile scenarios;
2. TL1 Phase A mechanics corpus;
3. TL1 Phase B direct-fire corpus;
4. TL1 35-Space deterministic construction envelope;
5. TL1 bilateral overload/EW counterplay study - 60 Monte Carlo variants;
6. deterministic auxiliary resource endurance;
7. Checkpoint 53 resource-semantics lock;
8. ScenarioRunner self-tests.

At the default 10,000 trials, the normal Monte Carlo workload is **600,000 trials**.

The normal acceptance suite is the required release gate for this checkpoint.

## Deep Calibration

Deep Calibration retains the historical Monte Carlo/calibration corpus and adds Checkpoint 67 as the newest study. It is intentionally optional unless a change touches an older calibrated mechanic, a normal result raises a cross-study regression concern, or the project owner requests the deeper pass.

Checkpoint 67 Deep Calibration contains **26 stages / 1,544 Monte Carlo variants / 15,440,000 default trials**.

## Release interpretation

No target win rate is blocking. Checkpoint 67 gates mechanical coverage, data bindings, fuel accounting, safe Strain bounds, planning/request/activation and power/Strain-denial telemetry, legal EW installation, and execution of the scripted counterplay matrix. Win shares and tactical advantages remain review evidence.
