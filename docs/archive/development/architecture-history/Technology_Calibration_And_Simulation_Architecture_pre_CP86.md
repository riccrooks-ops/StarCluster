# Technology Calibration and Simulation Architecture

## Authority and scope

The active Concept document under `docs/` is the top-level rules and design authority. Focused subsystem architecture documents and machine-readable profiles refine that direction for implementation and testing. Calibration studies are evidence: they can validate mechanics, expose tradeoffs, and support a proposed value, but a green study does not automatically promote a component, technology, AI doctrine, or numerical profile into production.

Historical checkpoint chronology that previously lived in this file is preserved at `docs/archive/design-architecture/Technology_Calibration_And_Simulation_Architecture_historical_checkpoint_evolution.md`. Historical study definitions and stable identifiers may remain in their original machine-consumed paths when reproducibility requires them; their continued presence does not make them current design authority.

## Dependency boundary

Technology calibration belongs in the engine-independent simulation host. The Godot client presents and commands authoritative state but does not own TL conversion formulas, balance targets, or statistical experiments.

```text
StarCluster.Core
    ^
    |-- StarCluster.Game            player-facing host
    `-- StarCluster.ScenarioRunner  deterministic and Monte Carlo host
```

`StarCluster.Core` owns authoritative mechanics. `StarCluster.ScenarioRunner` supplies declared study inputs, executes Core mechanics, and reports diagnostics. A study must not reimplement a competing combat rule merely to obtain a desired result.

## Current technology-calibration principles

- Technology categories advance independently. There is no universal ship-TL combat multiplier and broad low-TL research cannot synthesize an undeclared high-TL capability.
- Component or capability TL owns its relevant behavior. Cross-category prerequisites remain sparse, explicit, and justified by the underlying technology fiction.
- Technology progression may introduce a capability, mature an older family, improve integration or miniaturization, reduce Space or Tactical Power burden, improve reliability/resilience, or improve a primary performance statistic. Raw-stat growth is not mandatory at every TL.
- Contemporary component combinations must pass both logical design review and mathematical/combinatorial review under the same Installation Space, Tactical Power, prerequisite, and stacking rules.
- Simulation diagnoses the consequences of declared rules; it does not manufacture predetermined TL-versus-TL win ratios.

### Direct fire, computers, and EW

Degraded direct fire has split ownership. A specific weapon profile, variant, or upgrade owns **permission** to fire from an Approximate track. The ship Tactical Computer/fire-control profile owns the **numerical accuracy penalty** for executing that mode. The current TL1 Tactical Computer working value is -25 percentage points, but no production weapon gains the capability merely because that computer rating exists.

Tactical Computer, Sensor, ECM, ECCM, and Power / Reactor technology histories evolve independently. Later values and capability breakpoints must be tested in their contemporary Tactical Power and combat environment rather than extrapolated linearly. Degraded fire must remain materially inferior to restoring a Firm solution through appropriate counter-EW when ECCM is affordable; otherwise the fallback has made the dedicated countermeasure economically irrelevant.

Ordinary missiles retain their separate Firm-terminal architecture. Any future Approximate-target missile capability, including a volume-saturation/Swarmer concept, must be explicit in the missile profile and validated through missile-specific guidance, ammunition, interception, and terminal-resolution rules.

## Whole-ladder architecture roadmap

Before exact calibration of a tightly interacting next-TL subsystem group, maintain a whole-ladder **Technology Architecture Matrix** that sketches TL1-TL9 capability roles without pretending that all later numbers are already known. The active Matrix v1 covers Tactical Computer, Sensor, ECM, and ECCM under `docs/design/player_technology/`.

The matrix uses five explicit states: **current/working**, **validated working candidate**, **legacy candidate**, **hypothesis**, and **deferred**. Review the whole ladder for stacked capability spikes, dead levels, design-space exhaustion, and accidental linear-growth assumptions; then validate and promote exact values sequentially, one TL at a time. After a promotion, revise the matrix before designing the next TL. This keeps long-range architecture visible without turning a conceptual roadmap into production data.

Progression streams are mechanically distinct for design and calibration but do not automatically create new player-visible research categories. Tactical Computer remains owned by Computing / Fire Control; Sensor, ECM, and ECCM remain streams within Sensors / EW; Power / Reactor remains its existing research discipline. Their interacting values must be revalidated together whenever a dependency change can alter the information/EW or whole-ship Tactical Power contest.

The first TL2 Matrix v1 information-control package has now completed its initial evidence loop. Checkpoint 79a validated Sensor DR1 / ECM2 / ECCM2 mechanics and tall-versus-wide counterplay. Checkpoint 80 showed that old Sensor + ECCM2 is mechanically valid but can incur severe 2-TP power pressure while DR1 + ECCM1 remains the efficient contemporary path; the 6-TP sensitivity demonstrated an integer power/support breakpoint rather than broken EW mechanics. Checkpoint 81a then revalidated the historical +12 ordinary Tactical Computer targeting value across current EW permutations while holding degraded fire at -25 and Evasive Compensation at 0. Accordingly, +12 targeting, DR1, ECM2, and ECCM2 at one TP per rating are **validated working candidates** for further TL2 integration. They are not a complete production TL2 combat vector: Sensor reach and new TL2 Sensor/EW overload/efficiency behavior remain unpromoted/deferred. Power / Reactor progression is now evaluated as its own dependency rather than being silently inferred from the information-control package.

### Cross-TL Sensor/EW diagnostic plumbing

Cross-TL studies may assign Sensor/EW profiles independently to the two simulated ships so a new sensor can be isolated without silently upgrading the opponent's sensing. They may also declare a normal ECM/ECCM rating for a side when testing a candidate rating ceiling. These are study inputs, not production component assignments. Legacy studies default to their shared Sensor/EW profile and rating 1 behavior.

Normal EW Tactical Power scales with the requested normal rating at the declared power-per-rating cost; component-condition overhead remains additive and overload remains a separate mechanism. A study that changes normal rating must state whether overload, efficiency, sensor reach, computer performance, and other EW dependencies are held constant. The first CP79 isolation holds all of those dimensions except Sensor Discrimination Resistance and normal ECM/ECCM rating.

### Advanced power demand and tall viability

Higher technology is not assumed to be automatically cheaper to power. A component that pushes a capability frontier may legitimately require more Tactical Power, while a later maturation step may instead improve efficiency. Power demand and power efficiency are therefore separate progression dimensions.

A tall or heavily skewed research path may expose reactor, Installation Space, or combat-package opportunity costs because support technologies did not advance in lockstep. That pressure is an intended design constraint, not a mandate that every advanced system fit comfortably into an old power budget. The corresponding guardrail is that higher TL must still broaden or improve viable solutions rather than make new equipment systematically unusable. Validate high-demand tall builds, mixed-TL alternatives, and bounded reactor sensitivity before promoting a candidate or declaring it over-costed.

Accepted Checkpoint 80 applied that rule to the CP79a candidate interaction. TL1 Sensor DR0 + ECCM2 was compared against TL2 Sensor DR1 + ECCM1 under missile/PDS and direct-fire pressure at the accepted 5-TP production reference, with Side-A reactor output 6 used only as diagnostic sensitivity. The result supports higher-TL power pressure as a real design constraint while preserving the guardrail that contemporary tall progression remains viable. Checkpoint 83 now reuses that sensitivity only as evidence motivating a current-architecture Early Practical Fusion candidate: 6 Operational TP at the same 6-Space primary-reactor footprint as the TL1 5-TP Peak-Fission reference. The CP83 study changes Operational output only; damage-state output, overload, efficiency, storage, auxiliary generation, reliability, Space, and prerequisites remain separate deferred properties. The candidate is not production authority unless explicitly accepted after native evidence review.


### Power / Reactor progression isolation

Power progression is not one scalar ladder. Treat normal Tactical Power output, output per Installation Space, Degraded/Disabled output, overload margin and strain, conversion efficiency, reliability, storage/buffering, auxiliary generation, and enabling prerequisites as separable properties. A checkpoint may change more than one only when the hypothesis explicitly requires it.

The first standing-suite Power experiment holds the primary-reactor footprint at 6 Space and varies only Side-A normal Operational Tactical Power from 5 to 6. It retains the accepted TL2 information-control package, the 35-Space EW-capable combat fixture, production fuel/movement/PDS rules, and the -25 degraded-fire guardrail. Mature TL1 reactors are not prohibited from stacking where ship architecture allows them; their full additional Space and opportunity cost are part of the capability-frontier comparison.

### Standing technology-integration permutation suites

As interacting subsystem properties mature, prefer reusable **data-driven permutation suites** over creating a wholly bespoke Monte Carlo topology for every checkpoint. A standing suite declares its technology axes, combat contexts, pairing rules, frozen dimensions, and expected Cartesian coverage in machine-readable form; an individual checkpoint activates only the subset needed to answer its current causal question.

This does not mean running every imaginable combination every time. Causal interpretability and dependency-triggered validation still govern workload. Add a dimension when a changed dependency can plausibly interact with it, and retain paired common-random-number comparisons where they improve sensitivity. Actual-consumer preflight and one-trial full-pipeline smoke remain mandatory whenever the suite or consumer plumbing changes. Checkpoint 81a accepted the first standing TL2 Computer/Sensor/EW paired study. Checkpoint 82a consolidated the validated TL2 information-control package in `technology_integration_permutation_suite_v0_2.json`. Checkpoint 83 advances the standing definition to `technology_integration_permutation_suite_v0_3.json`, adding Power / Reactor as a first-class axis and pairing the 5-TP control against the 6-TP candidate across the same information-control environments. Earlier v0.1/v0.2 definitions remain historical coverage rather than being rewritten.

## Study lifecycle

Use the smallest study that answers the current question.

1. **Declare the hypothesis and dependencies.** State which mechanic, component data, doctrine, and environmental assumptions are in scope and what would require revalidation later.
2. **Prove deterministic contracts first.** New rules enter through unit/Core/ScenarioRunner deterministic cases before large stochastic studies.
3. **Run an actual-consumer preflight.** A new or materially changed runner study must be exercised by the real consumer path before substantive Monte Carlo.
4. **Run a tiny full-pipeline smoke.** Normally use one trial per variant to verify parsing, materialization, telemetry, gates, output routing, and aggregation semantics.
5. **Run only the substantive study needed for the decision.** Report exact variant and trial counts, seed policy, gates, output paths, and acceptance interpretation.
6. **Review evidence; do not auto-promote.** Candidate values and AI doctrines require an explicit repository/design decision after results are reviewed.

The active validation suite is tiered. Must-always-run validation contains repository/manifest checks, clean warning-as-error build, unit tests, deterministic authoritative mechanics, and current architecture/combinatorial contracts. **Deep Calibration** contains longer stochastic studies and is opt-in when a declared dependency changes or a competing hypothesis is intentionally being evaluated.

See `docs/design/testing/README.md` and `docs/design/testing/Checkpoint_83_Validation_Tiers.md` for the current tier contract.

## Reproducibility and random streams

Deterministic scenarios use declared seeds and testable random streams. Monte Carlo studies must preserve materialized variant identity, master seed policy, trial index, and stream identity so results do not depend on worker count, resume boundaries, or completion order.

Common-random-number studies may deliberately give paired variants corresponding trial streams to reduce comparison noise. When used, the pairing policy and any stream fingerprint must be explicit. Execution timing and worker telemetry are noncanonical diagnostics and must not change canonical result hashes.

Stable historical seed labels or checkpoint-named study IDs may remain when they are part of an accepted reproducibility contract. They are compatibility identifiers, not statements of current design authority.

## Mechanical and statistical failure separation

Mechanical correctness is a release gate. Trial errors, invariant failures, missing expected variants, malformed outputs, telemetry-semantic mismatches, or actual-consumer failures reject the study independently of gameplay statistics.

Statistical gates are appropriate only for a declared hypothesis whose direction or bound is justified. A result should not fail merely because a matchup does not reach a predetermined win rate. Contextual advantages must be tested in contexts that exercise them; an unexercised statistic is not automatically worthless.

Report more than win percentage where the mechanic calls for it. Useful diagnostics can include attack eligibility, hit chance, firing opportunities, Tactical Power denials, PDS attempts, track quality, ECCM/ECM activations, fuel/endurance, unresolved outcomes, time to resolution, component condition, and resource exhaustion.

## Architecture and combinatorial studies

Ship-construction studies use the current unified Installation Space architecture and explicit prerequisites. They should enumerate representative normal and deliberately odd legal builds, check integer breakpoints, stacked compact legacy components, Pareto domination, power feasibility, and practical subsystem floors.

Do not restore obsolete Weapon Bay/AUX-capacity architecture, arbitrary single-main limits, or historical forced TL win-rate gates simply because old fixtures or reports still exist. Retain a historical fixture only when it still tests an authoritative rule or is required to reproduce accepted evidence.

## AI doctrine evidence

Accepted tactical heuristics are versioned doctrine assets with lifecycle state, evidence provenance, dependencies, information-parity constraints, and revalidation triggers. A stochastic study may produce an evidence draft, but automatic doctrine promotion is prohibited. Unrelated changes rely on deterministic doctrine regression tests; expensive doctrine Monte Carlo is rerun only when a declared dependency changes or a competing doctrine is being evaluated.

## Historical evidence policy

Historical reports, study definitions, baseline snapshots, and compatibility identifiers are retained when they support reproducibility or still-valid regression evidence. Historical procedures that no longer belong in the active release gate should live under an archive/tested location or remain clearly labeled as frozen evidence rather than accumulating in current navigation and runbooks.

When a current architecture document replaces a historical chronology, preserve the historical content once in the archive instead of duplicating it throughout active documentation.
