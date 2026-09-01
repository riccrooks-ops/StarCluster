# Checkpoint 76 Validation Tiers

## Must always run

Checkpoint 76 is the operational degraded-fire/ECCM counterplay and upgrade-path guardrail checkpoint. The normal release path must run the repository/dependency contract, warning-as-error build and unit tests, accepted deterministic mechanics corpora, TL1 Phase A/B, the 35-Space construction envelope, the Sensor/EW foundation, the CP76 actual-consumer preflight, all 54 one-trial full-pipeline smoke variants, all 54 substantive operational variants, resource-semantics locks, and ScenarioRunner self-tests.

The 54-variant study deliberately compares -20 and -25 weapon-specific degraded-fire candidates against no-ECCM, accepted reactive-ECCM, and aggressive-ECCM responses. It retains production 5 TP, Balanced-0 sensing, FullVolleyFirst, PDS, movement, and the pre-combat EW sub-phase. Hostile ECM uses the accepted `tl1-ew-preserve-combat-package-v1` affordability doctrine; reactive response uses accepted `tl1-ew-reactive-eccm-v1`. Aggressive ECCM is a diagnostic control, not a proposed default doctrine.

Release gates verify study wiring, actual Firm/Approximate counterplay, ECCM/ECM exercise, weapon-specific trait isolation, and missile exclusion. Win share, combat duration, the relative desirability of -20 versus -25, and the amount of ECCM value are human-review evidence. There is no automatic combat-outcome promotion gate.

Production weapons remain unchanged. Degraded fire is not assigned by Kinetic/Energy family. It remains an explicit property of a particular weapon profile/variant/upgrade. Ordinary missiles remain on their Checkpoint 75 Firm-terminal architecture; future approximate-terminal missiles require a separate explicit missile capability and are not implemented here.

CP73 doctrine Monte Carlo is not rerun. Checkpoint 76 consumes the accepted v0.2 doctrine asset as an operational dependency without evaluating a competing ECM doctrine.

## Deep Calibration

Deep Calibration remains opt-in. Run it only if normal Checkpoint 76 acceptance exposes a regression, the operational study identifies a concrete dependency requiring broader calibration, or another declared dependency changes. The normal 540,000-trial study is the intended evidence for the ECCM-value question.
