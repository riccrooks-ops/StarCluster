# Checkpoint 74c Validation Tiers

## Must always run

Repository/dependency contract, build/unit tests, accepted deterministic mechanics corpora, Sensor/EW foundation, CP74 degraded-fire actual-consumer preflight, one-trial full-pipeline smoke, the 20-variant degraded-fire foundation study, resource-semantics locks, and ScenarioRunner self-tests.

CP74c is a release-gate-only hotfix. CP73 EW doctrine Monte Carlo remains intentionally absent. CP74 game mechanics, study inputs, AI doctrine, candidate penalties, production definitions, and Concept content remain frozen. The only ScenarioRunner change is that shared weapon-family coverage now uses the study's declared family scope: CP74 requires Kinetic and Energy because missiles are intentionally excluded; all existing studies retain their prior three-family requirement. The preflight summary reports the same study-aware family scope.

## Deep Calibration

Opt-in only. No substantive CP74 dependency changed in CP74c, so Deep Calibration is not recommended unless native normal acceptance reveals an unrelated regression.
