# Checkpoint 75 Validation Tiers

## Must always run

Checkpoint 75 is the applied direct-fire degraded-fire candidate study plus missile terminal-guidance guardrail checkpoint. The normal release path must run the repository/dependency contract, warning-as-error build and unit tests, accepted deterministic mechanics corpora, TL1 Phase A/B, the 35-Space construction envelope, the Sensor/EW foundation, the CP75 actual-consumer preflight, all 40 one-trial full-pipeline smoke variants, all 40 substantive applied degraded-fire variants, resource-semantics locks, and ScenarioRunner self-tests.

The CP75 applied study is intentionally review-only. It compares Kinetic and Energy family packages using the provisional -20 and newly added -25 percentage-point Approximate-track penalties at fixed ranges 2 and 3. It does not assign degraded fire to any production weapon and it does not use win rate, pacing, or penalty ordering as a release target.

The missile terminal tests are release-critical even though missiles are absent from the Monte Carlo study. They must prove that baseline command-guided missiles require a live Current/Firm launcher datalink, peer terminal guidance requires an explicit profile capability, a sensor-plus-seeker missile cannot refine a merely remote Approximate cue directly into terminal Firm, and a seeker-only co-located acquisition path remains a distinct architecture. Missile and torpedo attacks do not inherit direct-fire degraded-fire eligibility.

CP73 EW doctrine Monte Carlo remains intentionally absent. The accepted `tl1-ew-preserve-combat-package-v1` default and reactive ECCM behavior are frozen unless a declared dependency changes or a competing doctrine is deliberately evaluated.

## Deep Calibration

Deep Calibration remains opt-in. Run it only if normal CP75 acceptance reveals a regression, an applied degraded-fire result exposes a dependency that needs broader calibration, or a declared dependency of an older study has changed. The normal CP75 evidence is sufficient for the intended -20/-25 Kinetic/Energy comparison.
