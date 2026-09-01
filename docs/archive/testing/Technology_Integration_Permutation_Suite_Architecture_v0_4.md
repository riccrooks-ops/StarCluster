# Technology Integration Permutation Suite Architecture v0.4

## Purpose

The Technology Integration Permutation Suite is the standing cross-subsystem calibration framework for sequential Star Cluster technology design. It prevents each checkpoint from inventing a new stochastic architecture while preserving causal isolation.

## Current package boundary

The validated TL2 information-control package remains `tl2_computing_sensor_ew_working_profile_v0_1.json`: +12 pp Tactical Computer targeting, -25 pp computer-owned degraded fire, Evasive Compensation 0, Sensor DR1, and ECM/ECCM normal ceilings 2 at 1 TP/rating. These are working candidates rather than a complete production TL2 combat profile.

Checkpoint 84 adds **Power / Reactor and Shield Capacity** as a first-class suite axis. The accepted TL1 reference is Peak Fission at **5 Operational TP / 6 Space**. The first TL2 Power hypothesis is Early Practical Fusion at **6 Operational TP / 6 Space**. That value remains a candidate until CP83 native evidence is reviewed; no other TL2 reactor statistic is inferred from it.

## Reusable axes

v0.4 defines reusable axes for weapon/opponent family, geometry, information-control package, **Power/Reactor package**, degraded-fire permission, and doctrine. Later checkpoints extend only a changed dependency and should not activate every Cartesian combination merely because the suite can describe it.

Power/Reactor packages distinguish output from efficiency, condition mapping, overload behavior, storage, auxiliary generation, and footprint. A future checkpoint that changes one of those properties should not silently inherit another.

## Current CP83 slice

`tl2-itc09-power-reactor-progression-permutations` reuses the CP81a context structure and fixes the validated TL2 +12 Tactical Computer candidate. The active slice is:

- two Side-A direct-fire families;
- two opponent families;
- three geometry/movement contexts;
- four information-control environments;
- two reactor outputs, 5 TP and 6 TP.

That produces **96 paired variants**. The two reactor variants in each environment share the same `comparisonGroup` for common-random-stream comparison.

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

CP79 and CP81 demonstrated that a study can compile and even execute variants while still being missing from a shared/global consumer classification. Those classification checks are therefore explicit release contracts for subsequent suite expansions.

## Power/Reactor progression guardrails

- Higher-TL reactors may expand output density, efficiency, resilience, overload tolerance, or another capability frontier; they do not need to improve every property at once.
- A new reactor family should make at least one useful ship design envelope achievable that the predecessor cannot reproduce as efficiently under the same Space and support constraints.
- Mature legacy reactors may still be stacked where architecture permits. Do not invent an anti-stacking rule solely to make a frontier reactor superior; charge the real Space, power, reliability, and opportunity costs instead.
- A higher-TL power system may remove one bottleneck without erasing all Tactical Power choices. Test both high-demand and lower-demand packages.
- Tall/skewed research remains legal: insufficient supporting Power technology can constrain advanced equipment, but progression must not make advanced builds systematically unusable.

## Historical continuity

`technology_integration_permutation_suite_v0_1.json` and v0.2 remain exact historical/current-planning predecessors for reproducibility. v0.4 is the current planning definition. Historical study IDs and runtime compatibility labels are not renamed merely for presentation cleanup.


## CP84 Shield Capacity axis

CP84 carries the accepted CP83 6-TP/6-Space Early Practical Fusion value forward as a validated working candidate and adds Shield Capacity as a separately factored axis. The current Shield axis contains the TL1 Shield 2 reference, Shield 3 primary TL2 candidate, and Shield 4 upper sensitivity. Recharge, hardening, condition behavior, sustained maintenance, overload, and shield-generator Space are not bundled with capacity.

The activated CP84 submatrix is 2 Side-A direct-fire families x 3 opponent families x 3 geometry/order contexts x 2 information-control environments x 3 shield capacities x 2 reactor outputs = **216 variants**. Comparison groups retain common random streams across all twelve Shield/Power/environment permutations within a combat geometry so capacity and reactor deltas can be paired directly.

Stateful turn-power planning is part of this slice because shield recharge must compete prospectively with offense, PDS, and reactive ECCM. The study emits explicit Side-A tactical-recharge opportunity, power-spent, and reserve-denial telemetry. Statistical outcomes remain review-only; smoke/release gates assert configuration and consumer-path invariants rather than requiring stochastic thresholds.
