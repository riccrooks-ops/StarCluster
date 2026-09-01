# Star Cluster Technology Integration Permutation Suite Architecture v0.17

## Purpose

Version 0.17 converts the complete CP101 TL3 base table from a registered conceptual package into a **CP102 executable integration candidate** without changing any accepted TL3 value. The native-accepted CP99 v6 TL1/TL2 exact-edge foundation remains frozen as a regression consumer. CP102 adds a separate v7 consumer because TL3 introduces progression that cannot be represented honestly as a same-Space scalar replacement.

This document owns testing/integration architecture. Component intent and values remain owned by the Technology Matrix and `tl3_base_technology_candidates_v0_2.json`; the executable binding is recorded in `tl3_executable_implementation_profile_v0_1.json`; game-facing mechanics remain in the Concept.

## Lifecycle boundary

CP102 changes the lifecycle state from **registered conceptual candidate** to **implemented/executable candidate**. It does not calibrate or promote TL3. In particular:

- The accepted CP101 TL3 base-table values are unchanged.
- CP99 v6 remains the accepted TL1/TL2 regression surface.
- CP102 v7 enables `tl3CombatConsumerEnabled=true` only because every registered TL3 base transition now has an owning construction/progression/runtime representation.
- The CP102 1-trial smoke is pipeline evidence only; no win rate or combat outcome from it is balance evidence.

## Retained native-accepted regression consumer

`cross-tl-build-permutation-foundation-v0_8.json` remains the frozen CP99 TL1/TL2 reference:

- 82,944 raw combinations;
- 11,776 legal builds;
- 2,944 exact-fill, 6,656 near-fill, and 2,176 underfilled builds;
- 37,184 legal exact same-Space TL1->TL2 progression edges;
- 181 populated exact-edge strata;
- 362 deterministic lower->higher pairs; and
- 724 mirrored range-10 Adaptive Engage variants.

CP102 does not rerun the CP99 181,000-trial substantive screen merely because the technology consumer is generalized.

## CP102 v7 construction envelope

`cross-tl-build-permutation-foundation-v0_9.json` uses coverage mode `construction_envelope`. Its purpose is construction legality, not combat.

It enumerates **221,184 raw spatial combinations** and **51,264 legal builds** across the TL2/TL3 35/36-Space envelope. Of those legal builds, **10,752 are exact-fill**. The v7 axes explicitly include Hull capacity, Main Weapon, Main Reactor, Tactical Computer, Sensor, Shield, Shield Hardener, Armor, ECM, ECCM, STL, FTL, and PDS.

For this construction-only pass, technology or operating-mode states that are **Installation-Space-isomorphic** are deliberately collapsed where they cannot change legality. For example, one installed 2-Space PDS footprint is sufficient to test construction pressure; family/readiness semantics belong to the transition smoke. The envelope still requires explicit one/two Main and one/two Reactor states plus single/redundant EW states.

Deterministic construction invariants include:

- at least one Main Weapon, one Reactor, and one installed Sensor;
- explicit optional second Main Weapon and second Reactor;
- Tactical Power sufficiency is not a construction filter;
- Shield Hardener requires an installed Shield Generator;
- same-type ECM/ECCM ratings are non-additive and redundancy resolves the highest applicable functional rating;
- TL2 Hull capacity remains 35 while TL3 Hull capacity is 36; and
- no legal current build fits two full Main Weapons plus two full Main Reactors: the TL3 mandatory core remains 38/36.

The construction envelope generates **zero combat variants**.

## CP102 v7 semantic transition smoke

`cross-tl-build-permutation-foundation-v1_0.json` uses coverage mode `transition_smoke`. It enumerates **43,008 raw / 38,400 legal** transition-bearing states and validates **220,416 legal TL2->TL3 progression edges** across all 16 registered base transitions.

Each transition is typed and declares its installed-Space and Hull-capacity deltas independently:

| Transition | Kind | Installed-Space delta | Capacity delta |
|---|---|---:|---:|
| Hull h2 -> h3 | capacity integration | 0 | +1 |
| Tactical Computer c2 -> c3 | capability addition | 0 | 0 |
| Sensor s2 -> s3 | operating-mode addition | 0 | 0 |
| ECM2 -> ECM3 | power efficiency | 0 | 0 |
| ECCM2 -> ECCM3 | power efficiency | 0 | 0 |
| Reactor r2 -> r3 | miniaturization | -1 | 0 |
| STL2 -> STL3 | primary performance | 0 | 0 |
| FTL2 -> FTL3 | primary performance | 0 | 0 |
| no Hardener -> TL3 Hardener | optional-component unlock | +1 | 0 |
| Armor a2 -> a3 | protection maturation | 0 | 0 |
| Kinetic k2 -> k3 | power efficiency | 0 | 0 |
| Energy e2 -> e3 | safe-output maturation | 0 | 0 |
| Missile m2 -> m3 | autonomy/propulsion | 0 | 0 |
| Kinetic PDS2 -> PDS3 | explicit hold | 0 | 0 |
| Energy PDS2 -> PDS3 | power efficiency | 0 | 0 |
| AMM PDS2 -> PDS3 | readiness-mode addition | 0 | 0 |

The smoke selects exactly one legal lower->higher named pair for each transition and mirrors each pair across Side-A-first and Side-B-first range-10 Adaptive Engage geometry. The generated study is therefore **16 pairs x 2 mover orders = 32 variants**, at **1 trial per variant**.

## Runtime ownership proven by CP102

The v7 consumer binds the accepted TL3 values to existing runtime owners rather than adding opaque checkpoint special cases:

- **Hull:** selected Hull option owns Installation Space capacity, so 35/36-Space legality is per build rather than a global constant.
- **Tactical Computer:** EvComp5 is condition-aware and offsets only the firing ship's own Evasive penalty, never below zero.
- **Sensor:** Low 3/4 @1 TP and High 4/5 @2 TP flow through separate data-driven normal power levels. High is normal operation, not Strain-producing overload. CP102 transition variants keep overload disabled beyond High.
- **ECM/ECCM:** TL3 uses an explicit full-strength normal-cost field so Rating2 can cost 1 TP total without redefining the legacy 1-TP-per-rating field. Same-type redundancy remains non-additive.
- **Reactor:** 6 TP per reactor is retained while the v7 footprint changes from 6 to 5 Space.
- **STL/FTL:** Move3 tactical/strategic values are bound independently; STL's existing bounded overload costs and Strain rules remain held.
- **Shield:** the Hardener is a separate 1-Space damageable component. When functional and powered for 1 TP it adds SA1; it is not folded into the primary Shield Generator.
- **Armor:** AP1/AI5 uses the ordinary independent armor override path.
- **Kinetic Main:** ordinary firing cost changes from 1 TP to 0 while the packet/range/ammunition profile is held.
- **Energy Main:** safe Low/Standard/High states remain 1 TP/DAM2/+10, 2 TP/DAM3/+25, and 3 TP/DAM4/+25. The transition smoke selects High to exercise the new output path; deterministic self-tests cover Low/High family-local performance binding. Tactical player/AI mode choice remains separate future UI/doctrine work.
- **Missile Main:** Move4 and standard onboard navigation-sensor presence are represented without inventing the deferred detailed navigation-sensor profile. Seeker remains optional and ordinary terminal Firm requirements are unchanged.
- **Kinetic PDS:** base13/RC1/1TP/Ammo60 is an explicit TL3 hold.
- **Energy PDS:** base16/RC1 remains, with readiness reduced to 1 TP.
- **AMM PDS:** preferred 2 TP/RC2 readiness now has an executable 1 TP/RC1 fallback when only one TP is available. Existing seeded automatic allocation and two-attempt-per-flight cap remain authoritative.

## Native acceptance sequence

A CP102 release is not accepted until a clean extracted full repository passes the user-facing two-step sequence **in the same tree**:

1. `-RepositoryOnly`, including dependency/interface checks, manifest/repository contracts, CP101 provenance, v7 JSON/count reconstruction, 16-transition coverage, and sequence-safe generated-artifact normalization.
2. the full CP102 run immediately afterward, including warning-as-error build, xUnit tests, ScenarioRunner self-tests, frozen CP99 v6 regression preflight, CP102 v7 construction-envelope actual-consumer preflight, CP102 v7 transition generation, and the 32-variant one-trial integrated smoke.

The tiny smoke must complete with zero failed gates and zero trial errors before any substantive TL3 Monte Carlo is attempted.

## Next use after acceptance

Once CP102 passes native acceptance, a later checkpoint can perform the first substantive TL1/TL2/TL3 integration/permutation study. That study should test design diversity, mixed-era stacking, Pareto domination, integer Space breakpoints, and Tactical-Power opportunity costs. It should not modify CP101/CP102 values merely because an outlier appears; diagnostic evidence should first identify whether the issue is technology math, doctrine, geometry, or sampling.
