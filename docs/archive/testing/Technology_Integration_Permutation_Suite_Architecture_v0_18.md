# Technology Integration Permutation Suite Architecture v0.18

## Status

Checkpoint 103 candidate. This supersedes v0.17 for current planning while preserving native-accepted CP102 executable TL3 integration and the frozen CP99 TL1/TL2 regression consumer.

CP103 is the first substantive TL1/TL2/TL3 integration/permutation measurement pass. It does **not** change accepted TL3 values, production rules, or AI doctrine, and it does not automatically promote or retune technology.

## Accepted inputs

- CP102 Corrected Replacement 3 is the native-accepted executable baseline.
- CP99 foundation v0.8 remains the frozen TL1/TL2 exact-edge regression consumer.
- CP102 v7 construction v0.9 and typed-transition v1.0 remain executable regression consumers.
- TL3 values remain those accepted in CP101 and executable in CP102.
- Runtime profiles remain `tl1-tl3-standard-runtime-profiles-v0_4.json`.
- Accepted no-AUX, Sensor/EW, and AI-doctrine bindings are unchanged.


## CP103 research-runtime ownership

CP103 deliberately separates the simulation research tool from the game/mechanics implementation. The native-accepted CP102 C# ScenarioRunner mechanics/regression surface is preserved. CP103 v8 study validation, exhaustive enumeration, population accounting, deterministic sampling, research combat screening, aggregation, and analysis are owned by `tools/simulation/starcluster_research/` under stdlib-only CPython 3.13.x.

This avoids adding checkpoint-specific research routing and report logic to the game-oriented C# toolchain. It does **not** make Python authoritative for production mechanics: deterministic C#/Godot behavior remains the game authority, and the Python parity corpus must reproduce the accepted relationships used by the research model. Python Monte Carlo is screening evidence only.

## CP103 study architecture

CP103 deliberately uses two evidence layers.

### 1. Primary weighted population screen — v1.1

`cross-tl-build-permutation-foundation-v1_1.json`

Purpose: population-aware TL2/TL3 integration measurement across the complete bounded tactical construction population represented by the study axes.

Deterministic envelope:

- 13 independent axes.
- 921,600 raw combinations.
- 164,160 legal tactical builds.
- 43,584 exact-fill builds.
- 82,848 near-fill builds.
- 37,728 underfilled builds.
- 13,474,170,720 unordered-distinct legal pairings.
- all 96 configured composition × frontier-progression × Space-pair population cells are non-empty.
- the 13,474,170,720 unordered-distinct conceptual pairing envelope is accounted by population buckets/combinatorics; CP103 must never materialize or iterate that full pair universe. The executable primary materializes the 164,160 legal builds and then performs bounded deterministic sampling.

Capacity-relative Space classes:

- exact fill: 0 free Space;
- near fill: 1–3 free Space;
- underfilled: more than 3 free Space.

This rule is relative to each selected Hull's actual 35- or 36-Space capacity. A global used-Space threshold would confound Hull progression with utilization class and is prohibited for v8.

Adaptive sample:

- 240 unordered statistical base pairs allocated deterministically across all 96 population cells using square-root population allocation, minimum 1 and maximum 6 representatives per cell;
- mirrored forward/reverse orientation produces 480 weighted statistical logical pairings;
- 32 unordered diversity-overlay base pairs across the 16 highest-population cells, mirrored to 64 zero-weight logical pairings;
- 32 zero-weight named diagnostic logical pairings;
- total 576 logical pairings;
- two mirrored Adaptive Engage movement-order geometries;
- 1,152 generated combat variants;
- 250 substantive trials per variant;
- 288,000 substantive primary trials.

Only the `statistical` sample carries population-representative weight. `diversity` and `named` pairings are diagnostic-only and carry zero inference weight.

### 2. TL1/TL2/TL3 legacy-stack diagnostic overlay — v1.2

`cross-tl-build-permutation-foundation-v1_2.json`

Purpose: preserve explicit complete-tier anchors, legacy-component stacking, mixed old/new packages, integer Space breakpoints, and held-transition negative controls without pretending that this deliberately curated subset represents the broader legal population.

Contract:

- declared raw all-tier axis product: 1,417,176 states;
- v8 `diagnostic_overlay` does **not** materialize that Cartesian universe;
- 33 named recipes resolve to 28 unique legal physical builds;
- 50 mirrored named logical pairings;
- two Adaptive Engage movement-order geometries;
- 100 generated combat variants;
- 250 substantive trials per variant;
- 25,000 substantive diagnostic trials;
- population-inference weight is always zero.

The overlay explicitly carries TL1, TL2, and TL3 runtime profiles. It includes complete-tier Kinetic/Energy/Missile anchors, dual legacy-reactor stacking, dual legacy-main stacking, mixed old-reactor and old-weapon packages under TL3 systems, STL progression, the strategically held FTL transition, the held Kinetic-PDS transition, and Hull-headroom controls.

## Population representation and isomorphic held labels

The weighted v1.1 population intentionally collapses labels that are tactically isomorphic for this study and would otherwise double-count identical tactical states. In particular:

- the weighted population uses the held FTL2 tactical representation rather than separately counting FTL2 and FTL3 labels;
- the weighted population uses Kinetic PDS2 rather than separately counting the held PDS2/PDS3 labels;
- held Shield-capacity labeling is similarly represented by the executable installed Shield state rather than duplicated by TL label alone.

These transitions are **not lost**. They remain explicit zero-weight negative controls in the legacy overlay. This preserves transition visibility without biasing population prevalence.

## Frontier progression semantics

For schema v8 only, `AdvancedComponentCount` is a **TL3 frontier-component stratifier**:

- TL3 Main Weapon and Reactor multiplicity count per installed physical component;
- installed TL3 Computer, Sensor, Shield, Armor, Hull, Shield Hardener, STL, and PDS count once each;
- TL3 ECM/ECCM count per installed suite;
- strategic FTL is excluded from the weighted tactical frontier count because the held TL2/TL3 FTL transition is tactically isomorphic and intentionally collapsed from the primary population;
- lower-TL components do not count toward the TL3 frontier count.

`InformationControlAdvancedCount` similarly counts TL3 Computer, Sensor, ECM, and ECCM frontier elements. For the CP103 primary v1.1 population, an equal-count pairing is classified as `equal_low` when the shared tactical frontier count is **5 or lower** and `equal_high` at **6 or higher**. This v8 threshold is chosen for the broadened tactical-frontier definition and independently validated for bounded sampler feasibility; it does not alter historical V1–V7 thresholds or meanings.

These counts are analysis dimensions. They are not technology scores, utility scores, or balance values. V1–V7 retain their historical semantics unchanged.

## Design questions CP103 is allowed to answer

CP103 may provide evidence about:

- legal-build diversity and concentration;
- population-weighted TL2/TL3 integration outcomes;
- Pareto/frontier domination signals using explicit construction/runtime dimensions;
- whether old-component stacking remains viable or becomes trivially dominated;
- integer Installation Space breakpoints created by 35→36 Hull capacity and 6→5 Reactor Space;
- Tactical Power pressure and opportunity-cost patterns;
- engagement-readiness/activity cliffs;
- mover-order sensitivity;
- family-specific behavior across Kinetic, Energy, and Missile packages.

## Questions CP103 must not answer automatically

CP103 must not automatically:

- promote, demote, or retune a technology value;
- change production initiative;
- prune awkward but legal builds;
- convert the frontier-component count into a scalar technology score;
- assign population weight to the legacy diagnostic overlay;
- infer gameplay value from the one-trial smoke executions;
- treat structural engagement denial as a construction-legality failure;
- turn Tactical Power overcommit into a construction filter.

## Validation sequence

The checkpoint must run, in dependency order:

1. repository/dependency contracts, including the explicit CP103 Python opt-in while preserving historical no-Python defaults;
2. warning-as-error native C# build and 876-test regression suite;
3. deterministic missile/mechanics/Space/Sensor-EW regressions;
4. frozen CP99 exact-edge regression preflight/generation;
5. accepted CP102 construction/transition regression consumers plus its 32-trial actual-consumer smoke;
6. CP103 Python 3.13 environment evidence and six research-engine unit tests;
7. deterministic C#/Python parity corpus;
8. executable v1.1 validation/enumeration/sampling and v1.2 validation/named-build generation;
9. one-trial full-variant Python smoke: 1,152 primary + 100 legacy-overlay trials;
10. Python substantive research: 288,000 primary + 25,000 zero-weight legacy-overlay trials;
11. population-weighted/legacy-overlay Python analysis;
12. resource-endurance/resource-semantics locks;
13. the accepted 70 ScenarioRunner self-tests.

The substantive workload is 313,000 trials. Smoke workloads are release plumbing only and do not enter balance inference. The exact v8 study document must be parsed by the executable Python validator before any enumeration; static PowerShell/regex inspection is not an adequate producer/consumer compatibility check.

## Review outputs

The Python research engine must retain legal-build CSVs and population coverage for the weighted study so post-native review can independently analyze:

- Space utilization and headroom;
- reactor output and installed-reactor count;
- weapon family, multiplicity, and power cost;
- Sensor/EW/Hardener/PDS commitments;
- frontier-component distributions;
- construction composition classes;
- statistical representative weights.

Research-combat output must retain mirrored mover-order review, population weights, track/power denial, attack activity, layer damage, and family-specific telemetry. Named/overlay evidence must remain distinguishable from weighted statistical inference.

## Acceptance boundary

Passing CP103 means the declared sampling architecture and substantive studies executed reproducibly without contract, trial, or deterministic-gate failures. It does not mean the TL3 table is balanced. Any value change after CP103 requires explicit human review and a later focused checkpoint.

### Mixed-era tier routing guardrail

For the V8 all-tier diagnostic overlay, runtime Technology Level is derived from installed/effective selections. Explicit absence placeholders (`installed=false`) may retain later catalog provenance, but they do not raise a legacy build's runtime tier. This prevents canonical no-ECM/no-ECCM/no-PDS/no-Hardener options from silently routing a TL1 anchor through a TL2 runtime profile. Earlier schema semantics remain frozen.
