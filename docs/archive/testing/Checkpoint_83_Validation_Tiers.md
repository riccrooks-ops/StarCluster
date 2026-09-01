# Checkpoint 83 Validation Tiers

## Must always run

Checkpoint 83 follows accepted Checkpoint 82a and adds **Power / Reactor** as a first-class axis in Technology Integration Permutation Suite v0.3. The focused hypothesis revalidates a TL2 **Early Practical Fusion 6-TP Operational-output candidate** against the accepted TL1 **Peak-Fission 5-TP** reference while holding the Main Reactor footprint at 6 Space and preserving the validated TL2 information-control working package.

The release path runs repository/manifest and native-dependency validation, warning-as-error build and unit tests, deterministic moving-missile scenarios, TL1 Phase A/B, the 35-Space construction envelope, the accepted deterministic Sensor/EW foundation, CP83 actual-consumer preflight, a 96-variant one-trial full-pipeline smoke, the substantive CP83 paired study, deterministic resource semantics, and ScenarioRunner self-tests.

CP83 release gates are **mechanical and semantic**. They prove the exact 96-variant 5-TP/6-TP pairing, unchanged +12/DR1/ECM2/ECCM2 information-control package, current reactive-EW consumer path, clean Firm controls, DR1+ECCM1 and wide ECCM2 Firm restoration, the fixed -25 degraded-fire fallback, Sensor/EW overload/efficiency isolation, Side-B 5-TP reference, no Evasive Compensation, no production promotion, and review-only outcome policy.

The normal study contains **96 substantive variants at 10,000 trials each (960,000 substantive trials)** plus 96 one-trial smoke executions. The variants are 12 combat/geometry comparison groups x four information-control environments x two reactor outputs. The 5-TP/6-TP pair in each environment shares the same comparison group for common-random-stream comparison.

The study changes **normal Operational reactor output only**. Reactor Degraded/Disabled output mapping, overload, efficiency, storage, auxiliary generation, footprint reduction, prerequisites, and reliability remain deferred/not promoted.

## Deep Calibration

Deep Calibration remains opt-in and dependency-driven. It adds CP83 to the retained historical stochastic corpus: **36 stages, 1,790 substantive variants, 17,900,000 substantive trials, plus 246 one-trial smoke executions** at default settings.

Do not run Deep Calibration merely because CP83 uses Monte Carlo. Use it only if normal acceptance exposes a broader regression or a later Power/Reactor change alters a dependency shared with the historical corpus.
