# Checkpoint 82 Validation Tiers

## Must always run

Checkpoint 82 follows accepted Checkpoint 81a and performs **deterministic evidence consolidation only**. It does not introduce or modify an integrated Monte Carlo study. Normal acceptance therefore runs the stable must-always-run foundation: repository/manifest and native-dependency validation, warning-as-error build, unit tests, deterministic missile scenarios, TL1 Phase A/B mechanics, the 35-Space construction envelope, the deterministic Sensor/EW foundation, deterministic resource semantics, and ScenarioRunner self-tests.

The checkpoint contract verifies that:

- Concept v0.6t and Technology Architecture Matrix v1 use the new **validated working candidate** status correctly;
- the machine-readable TL2 information-control working package exactly records +12 Tactical Computer targeting, -25 degraded-fire penalty, Evasive Compensation 0, Sensor DR1, ECM2, ECCM2, and 1 TP/rating;
- Sensor physical reach, reactor growth, and new TL2 overload/efficiency behavior are explicitly unpromoted/deferred;
- accepted CP79a, CP80, and CP81a evidence hashes are preserved;
- the standing Technology Integration Permutation Suite v0.2 treats the TL2 information-control package as a reusable axis and includes the full cross-study integration-audit checklist;
- historical identifiers such as `tl2-production` are explicitly compatibility evidence rather than current design authority;
- production degraded-fire assignment and ordinary missile Firm-terminal rules remain unchanged.

Normal acceptance contains **8 stages and 0 Monte Carlo variants/trials**.

## Deep Calibration

Deep Calibration remains opt-in and dependency-driven. Checkpoint 82 carries forward the accepted Checkpoint 81a deep suite unchanged in substantive coverage: **33 stages, 1,694 substantive variants, 16,940,000 substantive trials, plus 150 one-trial smoke executions** at default settings.

Do not run Deep Calibration for the evidence-consolidation pass. Use it only if normal acceptance exposes a broader regression or a later subsystem integration changes a dependency shared with the historical stochastic corpus.
