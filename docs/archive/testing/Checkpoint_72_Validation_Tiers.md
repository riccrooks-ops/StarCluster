# Checkpoint 72 Validation Tiers

## Must always run

The normal Checkpoint 72 acceptance path contains 11 stages. It performs repository/native-dependency checks, the clean warning-as-error .NET build, all unit tests, retained deterministic mechanics regression suites, the 924-row Sensor/EW foundation sweep, an **actual-consumer CP72 preflight**, a **39-variant one-trial full-pipeline smoke**, the 39-variant / 390,000-trial substantive reactive-EW study, retained resource semantics, and ScenarioRunner self-tests.

The preflight and smoke are mandatory before the substantive Monte Carlo stage. They are release-safety checks, not balance evidence.

## Deep Calibration

Deep Calibration remains opt-in. It retains the broader historical/current calibration corpus and substitutes the CP72 preflight/smoke/substantive stages for CP71's primary study. Default workload: 30 stages, 1,583 substantive Monte Carlo variants / 15,830,000 substantive trials, plus 39 smoke trials.

Do not run Deep Calibration merely because it exists. Run it only when a change can affect one of its retained dependency areas or when normal acceptance produces a specific reason to broaden the diagnostic.
