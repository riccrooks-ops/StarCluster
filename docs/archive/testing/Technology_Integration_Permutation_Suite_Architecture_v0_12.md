# Technology Integration Permutation Suite Architecture v0.12

## Authority

This is the current standing integration-suite architecture. It extends accepted v0.12 without changing the legal construction envelope, gameplay rules, component values, Technology Architecture, AI doctrine, or reference-mining authority. Its purpose is to improve **sampling quality and analysis fidelity** before the cross-TL study is scaled further.

Version 0.12 preserves the complete deterministic **82,944 raw / 22,592 legal** build envelope and its **255,187,936 unordered distinct** legal-pair population. It does not promote any technology candidate.


## CP95 instrumentation boundary

CP95 preserves the exact accepted CP94 legal-build envelope, adaptive allocation, 192 statistical base pairs, 24 zero-weight diversity base pairs, 48 named diagnostics, three geometries, pair-selection seed `940177`, combat master seed `940100`, and 1,500 substantive trials per variant. The purpose is causal instrumentation replay, not a new balance sample.

The critical hardening rule is that **movement-path closest approach is not post-Movement combat geometry**. The existing minimum-range metric remains available as path/closest-approach evidence. A new runtime channel records, per trial, the minimum final post-Movement range at an ordinary combat firing window, the number of firing windows, side-specific and mutual structural ready-window counts, and whether each side/mutual pair reached a structural ready window at least once in that trial. Generated variants carry the readiness class and maximum ready range as explicit runtime fields rather than requiring the consumer to infer them from a profile-label string. The maximum ready range remains a reference-context structural estimate rather than an absolute runtime action ceiling; legal EW/power state may produce action outside that estimate, and CP95 reports that divergence for review instead of failing the counter-integrity gate.

Observed-engagement diagnosis must use that post-Movement ready-window telemetry. A dynamic pair with no mutual ready-window trial is `movement_did_not_reach_mutual_ready_range`, even if the movement path passed through the nominal ready range. A structurally ready fixed reference that fails to record its firing window is `fixed_reference_ready_geometry_not_observed` and is blocking. Reaching mutual post-Movement ready geometry while both sides remain inactive is also blocking in a substantive run. One-side inactivity remains review evidence protected by side/family/context activity gates.

CP95 additionally emits `cross-tl-cp95-outlier-review.csv`, which keeps engagement anomalies, path-versus-post-Movement divergence, runtime-action/structural-readiness divergence, and high/extreme mover-order sensitivity as separate review categories. This is a triage instrument, not an automatic technology/gameplay promotion rule.

## Why v0.12 exists

Native CP94 acceptance plus subsequent review confirmed the matched/readiness/Space/population pipeline, but it also exposed two analysis limitations:

1. one sampled pair per population cell can carry too much weight when cell populations are concentrated and internally heterogeneous; and
2. a structurally `closing_ready` pair can still produce zero combat activity when TrackAware movement does not reach the actual Firm-and-weapon-ready range.

CP93 also showed that mover order can have a small median effect but a very large tail for some pairings. Version 0.12 therefore improves **within-cell representation**, **individual observed-engagement diagnosis**, and **mover-order-neutral reporting** before any broad component tuning or much larger Monte Carlo expansion.

## Legal-build and population envelope

The current 35-Space generalized envelope remains unchanged:

- **82,944** raw Cartesian combinations;
- **22,592** legal builds;
- **4,672 exact-fill** builds at 35 Space;
- **11,328 near-fill** builds at 32-34 Space;
- **6,592 underfilled** builds at 31 Space or less;
- **510,398,464** oriented self-inclusive pairings;
- **255,210,528** unordered-with-self pairings;
- **510,375,872** oriented distinct pairings; and
- **255,187,936** unordered distinct pairings.

Construction legality still requires at least one Main Weapon and one Reactor. Optional second homogeneous Main Weapons/Reactors remain legal when Space permits. Redundant same-type ECM/ECCM remains non-additive and resolves the highest applicable functional rating. Tactical Power insufficiency remains an operational tradeoff rather than a construction-legality filter.

## Adaptive statistical sampling

The same **96 primary population cells** remain authoritative for current screening. They are defined by:

- four composition classes;
- four orientation-neutral progression-magnitude strata; and
- six canonical Space-pair strata.

Version 0.12 replaces the uniform one-pair-per-cell statistical slice with **192 unordered distinct statistical base pairs**. Every cell receives at least one base pair. Remaining representatives are allocated deterministically in proportion to the square root of cell population, with a maximum of five statistical representatives per cell. This deliberately gives more representation to high-population cells without allowing the largest cells to consume the entire sample.

Every statistical base pair is emitted in **both orientations**, producing **384 statistical logical pairings**.

Population inference uses only this statistical sample. If a cell receives `n` statistical representatives, each representative carries exactly `cell_population / n` population-representative weight. The forward representatives across all 96 cells therefore sum back to the complete 255,187,936 unordered-distinct legal-pair population.

The square-root allocation is a bounded screening policy, not a claim of optimal statistical design. Later checkpoints may refine allocation using observed within-cell variance or other validated information.

## Diagnostic secondary-diversity overlay

Primary population cells do not directly stratify by weapon-family pairing or information-control gap. Those dimensions remain important comparability metadata, so v0.12 adds a separate diagnostic overlay rather than corrupting the statistical weights.

The **12 highest-population primary cells** each receive **2 additional unordered distinct base pairs**, for **24 diversity base pairs / 48 mirrored logical orientations**. Selection first prefers family-pair plus information-control-distance-band combinations not already present in that cell's statistical sample. If a cell lacks enough distinct secondary combinations, deterministic unique pairs fill the remaining diagnostic slots.

Information-control distance is reported as:

- `equal` for distance 0;
- `near` for distance 1-2; and
- `far` for distance 3 or more.

Diversity-overlay pairs carry **zero population-inference weight**. They are present to reveal within-cell heterogeneity and missing secondary coverage, not to change population estimates.

## Retained named diagnostics and total workload shape

The durable **48 named diagnostic logical pairings** remain unchanged and also carry zero population-inference weight.

The CP95 bounded screen therefore contains:

- 384 statistical mirrored logical pairings;
- 48 diversity-overlay mirrored logical pairings;
- 48 named diagnostic logical pairings;
- **480 total logical pairings**;
- 3 geometries per pairing; and
- **1,440 generated actual-consumer variants**.

The changed study must pass generator preflight, generated-study actual-consumer preflight, and a **1-trial-per-variant full-pipeline smoke** before substantive Monte Carlo.

## Exact engagement-ready range

The existing structural readiness classes remain:

- `reference_ready`;
- `closing_ready`; and
- `engagement_denied`.

Version 0.12 additionally records the **maximum ready range in hexes** at which the side can simultaneously obtain the required Firm track and satisfy physical weapon range against that opponent under the declared reference Sensor/EW capability.

- `reference_ready` has ready range 3;
- `closing_ready` has ready range 2, 1, or 0; and
- `engagement_denied` has ready range -1.

This value is diagnostic architecture. It does not change the movement doctrine or combat rules.

## Individual observed-engagement diagnosis

Aggregate family/context activity remains useful, but it may hide a dead individual pairing inside a healthy cohort. Version 0.12 therefore classifies every statistical/diversity matched result independently.

For a geometry in which both sides are structurally expected to engage:

- `active` means **both sides** produced family-appropriate main-weapon actions;
- `movement_did_not_reach_mutual_ready_range` means one or both sides remained inactive and dynamic movement never reached the stricter of the two sides' required ready ranges;
- `ready_geometry_reached_but_one_side_inactive` means the required mutual geometry was reached and exactly one side still produced no family-appropriate main action; and
- `ready_geometry_reached_but_no_actions` means the required mutual geometry was reached but neither side produced a family-appropriate main action.

Pairs not structurally mutual-ready in the geometry are reported as `not_mutually_expected`.

`movement_did_not_reach_mutual_ready_range` is a doctrine/movement diagnostic and does not by itself fail the study. `ready_geometry_reached_but_one_side_inactive` remains explicit review evidence and is additionally protected by the retained side/family/context cohort gate, so one side's healthy activity cannot silently stand in for the other. In a substantive multi-trial run, `ready_geometry_reached_but_no_actions` is a blocking individual integration/activity failure because the pair reached a structurally attack-capable geometry but the actual consumer still produced no relevant combat action. The one-trial smoke does not use a stochastic zero-action event as a blocking balance/activity conclusion.

This distinction prevents path-closest-approach telemetry from being mistaken for an observed post-Movement firing window from being mislabeled as build illegality.

## Mover-order-neutral matched reporting

Both existing TrackAware movement-order bounds remain authoritative diagnostic contexts. No production initiative rule is chosen by v0.12.

For every statistical/diversity matched bundle, the two orientations and two dynamic mover orders are combined to report build X in both conditions:

- X moves first;
- X moves second; and
- X mover-order-neutral estimate = the mean of those two conditional-win estimates.

The report also records `initiative_gap_pp = abs(X-first - X-second)` and assigns a diagnostic sensitivity class:

- `< 5 pp`: `low`;
- `5 to < 15 pp`: `moderate`;
- `15 to < 30 pp`: `high`; and
- `>= 30 pp`: `extreme`.

These boundaries are report labels only. They do not define gameplay balance gates or a future initiative system.

Population-weighted mover-neutral summaries use **statistical representative weights only**. Diversity and named diagnostics remain review evidence.

## Required reporting layers

Version 0.12 keeps three questions separate rather than collapsing them into one aggregate:

1. **all legal** - what the sampled legal ecosystem looks like, including structurally denied pairings;
2. **structurally mutual-ready** - what the sampled population looks like when both builds are theoretically capable of engaging in the declared geometry; and
3. **observed active** - what the sampled population looks like when the actual runtime produced family-appropriate main-weapon activity.

Raw and population-weighted screening estimates are reported where meaningful. A cell population weight describes prevalence; it never makes a few sampled representatives exhaustive of the internal diversity of that cell.

No universal scalar technology score is introduced. Progression magnitude/direction, Space use, family pairing, information-control gap, readiness, exact ready range, and observed activity remain explicit dimensions.

## CP95 bounded proving workload

Checkpoint 95 deliberately improves the **number and diversity of sampled pairs** while slightly reducing per-variant trials from CP93's 2,000 to **1,500**. This keeps the pass focused on sampling quality rather than simply buying narrower Monte Carlo error bars on a weak sample.

Default CP95 workload:

- **1,440 generated variants**;
- **1,440 one-trial smoke executions**; and
- **2,160,000 substantive trial executions** at 1,500 trials per variant.

Total planned trial executions including smoke: **2,161,440**.

Deep Calibration is not applicable to CP95. A larger/high-trial study should wait until native evidence confirms that the adaptive sample, diversity overlay, individual engagement diagnostics, and mover-neutral reports behave as intended.

## Execution guards

1. Preserve the accepted complete legal-build envelope and deterministic population-cell accounting.
2. Allocate exactly 192 statistical unordered base pairs across all 96 cells under the declared deterministic bounded square-root policy.
3. Mirror every statistical base pair in both orientations.
4. Split each cell's population inference weight equally among its statistical representatives and recover the complete unordered-distinct population across forward representatives.
5. Add exactly 24 diagnostic diversity base pairs in the 12 largest cells; keep their population-inference weight at zero.
6. Preserve all 48 named diagnostic logical pairings with zero population-inference weight.
7. Record exact ready range consistently with readiness class.
8. Preserve side-specific direct-fire/missile telemetry, aggregate reconciliation, and side/family/context activity cohorts restricted to side-variants that reached ready geometry.
9. Surface individual mutual-ready inactivity, including one-side-inactive and both-sides-zero states; block the individual substantive gate only when mutual ready geometry was reached yet both sides remained inactive.
10. Report mover-order-neutral estimates and initiative sensitivity while retaining both mover-order bounds.
11. Actual-consumer preflight and one-trial full-pipeline smoke are mandatory before substantive Monte Carlo.
12. Preserve the proven Sensor/EW JSON binding contract and the proven direct named-parameter checkpoint-wrapper-to-harness invocation.
13. No gameplay/component/Technology Matrix/AI-doctrine/reference-mining change may be smuggled into this sampling-quality pass.
14. No automatic candidate promotion or retuning is permitted from screening output.

## Expansion direction

If CP95 is native-clean, the next expansion should be evidence-driven rather than mechanically increasing every cell equally. High-population or high-variance regions may justify more representatives; initiative-sensitive or readiness/doctrine-pathological regions may justify focused diagnostics; and only after the sample is demonstrably representative enough should the project increase trial counts or use the standing suite for promotion-quality technology calibration.
