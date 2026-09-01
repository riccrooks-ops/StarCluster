# Checkpoint 68 Validation Tiers

## Must always run

Checkpoint 68 normal acceptance contains eight stages:

1. accepted deterministic moving-missile scenarios;
2. TL1 Phase A mechanics corpus;
3. TL1 Phase B direct-fire corpus;
4. TL1 35-Space deterministic construction envelope;
5. TL1 deterministic Sensor/EW foundation and range sweep;
6. deterministic auxiliary resource endurance;
7. Checkpoint 53 resource-semantics lock;
8. ScenarioRunner self-tests.

The new primary study is deterministic: **0 Monte Carlo variants / 0 Monte Carlo trials**. It evaluates 6 sensor profiles x 12 causal contexts x 11 ranges = **792 deterministic rows**.

## Deep Calibration

Deep Calibration retains Checkpoint 67a's accepted bilateral overload/EW Monte Carlo study and the historical calibration corpus, then adds the deterministic Checkpoint 68 foundation stage. It remains optional unless a later production sensor/EW change is promoted into integrated combat.

Checkpoint 68 Deep Calibration contains **27 stages / 1,544 Monte Carlo variants / 15,440,000 default trials**.

## Release interpretation

No target win rate or preferred sensor candidate is blocking. Release gates verify causal semantics, candidate coverage, active-emission and ECM-emission behavior, ECCM's limited role, occlusion, physical-weapon-range independence, the STL prepared-overload stand-down rule, data bindings, and the CP66+ no-Python native-acceptance contract.
