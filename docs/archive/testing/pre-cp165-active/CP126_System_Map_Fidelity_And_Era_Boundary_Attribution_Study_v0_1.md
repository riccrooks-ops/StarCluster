# CP126 System Map Fidelity and Era-Boundary Attribution Study v0.1

**Checkpoint:** 126  
**Accepted pure-TL control:** CP125  
**Accepted technology-reference baseline:** CP123  
**Accepted instrumentation baseline:** CP124  
**Starting implementation baseline:** CP122 Corrected Replacement 1

## Purpose

CP126 resolves the research-consumer fidelity and attribution questions exposed by CP125 before any mixed-TL ship study. It does not change the CP123 technology values. It makes a narrow mechanics/fairness correction to finite-map tie-breaking, restores the accepted full System Map/Adaptive Engage/Missile-pursuit behavior to the high-throughput Python consumer, proves side/mover symmetry, and then uses focused substantive lanes to explain the important CP125 signals.

The study keeps every individual ship **pure TL**. Mixed-TL loadouts remain deferred.

## Why this checkpoint exists

The production tactical architecture has long used a radius-5 finite hex System Map. The CP111-era Python ecology consumer deliberately reduced that map to the opposite-edge centerline and represented Missile travel as ETA-to-terminal so broad legal-build studies could be executed cheaply. That abstraction was valid for its original screening purpose, but CP125 revealed movement-order, Side-A/EW, late-Missile and era-boundary signals that are sensitive enough that the deferred full-map fidelity work can no longer remain implicit.

CP126 therefore preserves CP125 as the **axial-lane control** and adds a versioned full-map consumer rather than rewriting the historical consumer.

## Accepted finite-map encounter semantics

The full-map consumer and shared C#/Python fixtures use:

- radius 5;
- **91 legal hexes**;
- opposite-edge starts at `(-5,0)` and `(5,0)`, range 10 (the map is 11 hexes across but there are ten moves between the two edge cells);
- before contact, one observer-safe hex of centerward search per activation;
- after contact, Adaptive Engage using only information the actor has legitimately observed;
- target-specific demonstrated attack range and observed-opponent attack range;
- one-sided standoff only after the ship has actually demonstrated an attack beyond any range at which the opponent has demonstrated an attack;
- finite-map boundary enforcement for closing, opening and kiting;
- Missile objects with actual System Map coordinates;
- per-turn Missile movement toward the target's **current post-Movement coordinate**;
- Missile speed and total travel-range limits;
- rerouting and range-exhaustion telemetry.

Internal critical/subsystem damage remains outside the Python research consumer and is not calibrated by CP126.

## Orientation-neutral geometry correction

During parity/symmetry work, CP126 found that two accepted finite-map primitives used global axial `Q/R` ordering as a final equal-choice tie-break. A physical mirror on the left and right halves of the map could therefore choose different equally legal routes merely because one absolute coordinate sorted first.

CP126 corrects this in both C# and Python for:

1. finite ship movement/path selection; and
2. finite Missile shortest-path pursuit.

Equal physical choices now use target-relative cross/dot ordering. When ships are co-located, the encounter-bearing reference supplies the orientation basis. The correction changes **no technology statistic, weapon value, defense value, map radius, movement allowance or tactical objective**. Its purpose is to remove coordinate-system handedness as a hidden side advantage.

## Physical random streams

The old ecology consumer used one sequential RNG stream. Side processing order could therefore change which physical ship received which random values after a side swap. CP126's full-map consumer assigns deterministic streams to **physical ship identity and event type** instead: direct fire, Missile terminal guidance, PDS, and other stochastic events are associated with the physical actor/defender rather than the Side-A/Side-B label.

This allows side-swap/mover-swap mirrors to be a real blocking equivalence test. Isolation conditions also use common random numbers where appropriate so condition deltas are less noisy.

## Shared C#/Python geometry parity

`system_map_research_parity_fixtures_v0_1.json` is a shared deterministic authority consumed by both languages. It covers:

- radius-5 map cell count;
- pre-contact centerward search;
- finite ship movement and off-axis paths;
- actual Missile movement;
- moving-target reroute cases;
- terminal arrival;
- range exhaustion;
- physical 180-degree mirror symmetry.

Native CP126 acceptance additionally compiles/runs the production C# solution and xUnit geometry tests. Python parity alone is not sufficient to claim production fidelity.

## Blocking symmetry gate

Before any substantive study, CP126 executes a dedicated physical symmetry population:

- TL1-TL9;
- five representative cases per TL;
- both mover orientations;
- 25 trials per case;
- **2,250 mirrored comparisons / 4,500 combat executions**.

The same physical ships under side/mover swap must reproduce the same outcomes, turns, information/EW state, power events, Missile flow and damage outcomes after perspective normalization.

**Any mismatch is a blocking mechanics/instrumentation failure.**

## Technology-era interpretation

CP126 uses the project's broad discovery-era structure as interpretive context:

- **TL1:** baseline;
- **TL2-TL4:** low-technology discoveries and maturation;
- **TL5-TL7:** mid-technology discoveries and maturation;
- **TL8-TL9:** high-technology discoveries/maturation.

These are not rigid promises that every lineage jumps at the boundary. They do mean that TL1->2, TL4->5 and TL7->8 deserve explicit review as broad era entries, while unexpectedly large interior steps such as TL5->6 require attribution rather than assumption.

## Study lanes

### 1. Adjacent pure-TL population

Reuse the exact CP125 deterministic adjacent-TL base pairing IDs for all eight transitions and execute them on the full System Map. This preserves the CP125 population-weight control while measuring how much the progression signal changes under full geometry.

The output also compares mover-order sensitivity for **every adjacent transition**, including the previously notable TL3->4 transition.

### 2. Exact matched-composition adjacent TL

For every lower-TL legal composition that has the same component-count/options composition at the next TL, pair the two exact compositions. This holds build structure constant and isolates coherent stat/capability progression.

The legal-envelope comparison separately reports newly enabled higher-TL compositions. Of particular interest:

- TL4->5: 736 common compositions / 128 newly legal TL5 compositions;
- **TL5->6: 864 common / 680 newly legal TL6 compositions**;
- TL7->8: 1,728 common / 0 newly legal TL8 compositions.

The full-population minus matched-composition result helps separate scalar/capability improvement from miniaturization/integration-driven design-envelope expansion.

### 3. Movement-order hotspots

Reuse the exact CP125 same-TL TL2 and TL7 pairing IDs under the full map and compare mover-order distributions against the frozen CP125 axial results.

TL3->4 mover-order behavior is covered by the adjacent-population geometry comparison, so all previously identified movement-sensitive regions are represented.

### 4. Swarmer lifecycle / PDS isolation

At TL7-TL9, match GP and Swarmer attackers by the rest of their composition and cross them against matched no-PDS and AMM defenders.

This is a **lifecycle/niche test**, not an assumption that Swarmer must receive ordinary TL8/TL9 upgrades. The current standard Swarmer progression matures at TL2/TL3/TL5/TL7 and is intentionally carried forward as mature legacy technology afterward. The question is whether it retains a meaningful anti-PDS role as high-tech defenses advance.

### 5. Late Energy isolation

At TL7-TL9, match Energy and Kinetic attackers by the rest of their composition and cross them against matched no-Shield and Shield defenders. This tests whether CP125's late Energy strength is primarily its intended Shield-facing identity or remains unusually strong when Shield interaction is removed.

### 6. Late Missile geometry/stalemate lane

Reuse the exact CP125 same-TL Missile-vs-Missile pairing IDs at TL8 and TL9:

- TL8: **860 base pairings**;
- TL9: **867 base pairings**;
- total: **1,727 base pairings / 6,908 full-map variants**.

This directly compares unresolved rate, duration, mover-order sensitivity and Missile pursuit/rerouting against the frozen axial control. It is the primary test of whether the CP125 late-Missile stalemate signal survives actual finite-map movement.

## Workload

The combined plan contains:

- **9,427** legal pure-TL builds;
- **25,678 compact tasks**;
- **139,000 full execution variants** after all required side/movement/condition mirrors;
- **139,000 one-trial full-pipeline smoke engagements**;
- **250 substantive trials per variant**;
- **34,750,000 substantive engagements**.

The task-based Windows worker path reconstructs mirrors locally so spawn/pickling overhead does not dominate native execution.

## Telemetry

CP126 extends the accepted CP124 47-metric raw contract to **61 raw metrics**. New metrics cover:

- pre-contact search movement;
- Adaptive Engage Close/Open/Maintain/Standoff orders;
- boundary-ending moves;
- contact-establishment turn;
- Missile movement hexes;
- Missile reroutes and target-movement reroutes;
- Missile range exhaustion;
- maximum Missile travel distance;
- demonstrated own attack range;
- observed opponent attack range.

See `Telemetry_Instrumentation_Contract_v0_2.md` and its JSON authority.

## Primary outputs

- `adjacent_population_summary.csv`
- `matched_composition_summary.csv`
- `era_boundary_attribution_summary.csv`
- `adjacent_telemetry_summary.csv`
- `geometry_delta_summary.csv`
- `movement_geometry_comparison.csv`
- `late_missile_geometry_summary.csv`
- `swarmer_lifecycle_summary.csv`
- `energy_isolation_summary.csv`
- `normalized_pairing_outcomes.csv`
- `variants.csv`

## Acceptance boundary

The following are blocking:

- accepted CP125 provenance drift;
- shared C#/Python geometry fixture failure;
- native warning-as-error build or xUnit failure;
- physical side/mover symmetry mismatch;
- mixed-TL ship contamination;
- plan/count/mirror/telemetry integrity failure;
- one-trial smoke error;
- substantive trial error.

The following are **not** blocking:

- the size of any TL advantage;
- whether TL4->5 or TL5->6 is stronger;
- late Energy strength;
- Swarmer decline or persistence;
- movement-order sensitivity that remains after symmetry/fidelity correction;
- late Missile unresolved rate.

Those are the evidence CP126 exists to measure. No numerical value is automatically promoted or demoted.

## Post-CP126 direction

If CP126 proves the full-map consumer and resolves/quantifies the CP125 sensitivities, use its results to decide whether focused numerical changes are warranted. Only after those issues are understood should the project advance to mixed-/legacy-TL ship ecology.
