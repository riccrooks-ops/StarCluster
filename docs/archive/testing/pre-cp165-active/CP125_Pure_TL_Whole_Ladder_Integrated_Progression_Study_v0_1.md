# CP125 Pure-TL Whole-Ladder Integrated Progression Study v0.1

**Checkpoint:** 125  
**Accepted reference baseline:** CP123  
**Accepted instrumentation baseline:** CP124  
**Accepted implementation baseline:** CP122 Corrected Replacement 1

## Purpose

CP125 is the first large integrated combat study of the revised TL1-TL9 technology baseline. It deliberately keeps **each individual ship technologically homogeneous**: every component installed on a ship resolves at that ship's single TL. The opposing ship may be the same TL or any other TL from 1 through 9. Mixed-generation component loadouts remain deferred to a later checkpoint.

The study is intended to answer two related questions with one population:

1. **Within-TL ecology:** how do legal pure-generation builds interact against peers of the same TL?
2. **Technology progression:** what population-level combat advantage does TL distance confer when a coherent TL ship fights another coherent TL ship?

CP125 is not an automatic rebalance. Numerical results are review evidence. Only execution/instrumentation/population-integrity failures are blocking gates.

## Build universe

CP125 reuses the accepted CP124 exhaustive legal-build universe unchanged:

- 14,112 raw combinations;
- **9,427 legal builds**;
- TL1-TL9;
- Kinetic / Energy / Missile Main Weapons;
- one or two Main Weapons;
- one or two Reactors;
- Shield absent/present;
- redundant non-additive ECM/ECCM installations;
- Kinetic / Energy / AMM PDS or no PDS;
- Shield Hardener when legal;
- GP and, from TL2 onward, Swarmer Missile payload choices;
- residual Installation Space represented as zero-tactical-effect mission/AUX capacity.

No CP123 numerical value is changed by CP125.

## Pairing design

A literal Cartesian product would require 44,429,451 unordered legal-build pairs before side/movement mirrors. CP125 instead uses a deterministic coverage design that retains the complete build universe while keeping the workload analyzable.

### Off-diagonal TL cells

For every canonical TL pair `TLx < TLy`, the sampler emits `max(builds(TLx), builds(TLy))` base pairings after deterministic seeded shuffling. The larger build population appears exactly once; the smaller population cycles evenly. Therefore **every legal build from both TLs appears at least once in that TL relationship**.

### Same-TL diagonal cells

For `TLx vs TLx`, CP125 emits two deterministic deranged rounds, for `2 × builds(TLx)` base pairings. Every build participates in both rounds, and duplicate unordered pairs are prohibited.

### Whole-ladder coverage

The resulting plan contains:

- **45 canonical unordered TL cells**;
- **81 ordered TL cells** after side assignment;
- **70,034 base build pairings**;
- **84,843 build × opponent-TL coverage relationships**, which is exactly 9 opponent-TL relationships for every one of the 9,427 builds;
- **280,136 execution variants** after both side assignments and both movement orders.

Each canonical cell carries a design weight equal to its complete legal-build pair population divided by its sampled base-pair count. The weights reconstruct the complete pair population exactly in every canonical TL cell.

## Symmetry control

Every base pairing emits four variants:

1. build 1 as Side A / build 2 as Side B, Side A moves first;
2. build 1 as Side A / build 2 as Side B, Side B moves first;
3. build 2 as Side A / build 1 as Side B, Side A moves first;
4. build 2 as Side A / build 1 as Side B, Side B moves first.

This separates technology/family effects from side-label and movement-order effects. Ordered-TL inference averages movement-order mirrors. Delta-TL inference additionally normalizes which physical build occupies Side A/B.

## Acceptance smoke

Before substantive execution, the native checkpoint wrapper performs **one trial for every one of the 280,136 planned variants**. This is an execution gate only. It must cover all 81 ordered TL cells with zero trial errors. One-trial win/loss outcomes carry no balance weight.

## Substantive workload

The substantive study executes:

- **280,136 variants**;
- **200 trials per variant**;
- **56,027,200 total engagements**;
- recommended `--jobs 24` on the current native workstation.

The 200-trial per-variant depth is not intended to make every individual build-pair estimate a high-precision balance result. Precision comes primarily from the very broad population and weighted aggregation across hundreds or thousands of pairings per TL cell. Individual pair outcomes remain diagnostic.

## Primary analysis products

CP125 writes the full variant-level aggregate evidence plus population-weighted summaries:

- `tl_matchup_summary.csv` — complete 9×9 ordered TL matrix;
- `delta_tl_summary.csv` — normalized higher-TL advantage for Delta-TL 0 through 8;
- `family_matchup_summary.csv` — Kinetic, Energy, GP Missile and Swarmer interactions across TL cells;
- `tl_telemetry_summary.csv` — population-weighted CP124 raw telemetry by ordered TL cell;
- `pairing_outcomes.csv` — side/movement-normalized base-pair outcomes;
- `build_opponent_tl_summary.csv` — every build against every opponent TL;
- `movement_order_summary.csv` — mover-order sensitivity by canonical TL cell;
- `variants.csv` — full reconstructible variant-level aggregate evidence.

Raw telemetry remains governed by `Telemetry_Instrumentation_Contract_v0_1`. Derived rates are secondary to the underlying counters/quantities.

## Interpretation rules

CP125 does **not** require a fixed win-rate curve such as “TL+1 must win 60%.” Technology progression can be uneven, specialization can preserve unfavorable individual matchups, and family asymmetry is intentional.

Review should instead ask whether the population-level progression is coherent:

- does one-TL advantage generally matter without eliminating counterplay?
- does larger Delta-TL increasingly translate into decisive advantage?
- are there unexplained weak or cliff-like TL transitions?
- are family-specific strengths and weaknesses still visible?
- do power pressure, information control, PDS, layered defense and movement order explain the observed differences?
- do lower-TL populations ever systematically dominate materially higher-TL populations?

Any such finding is a **review signal**, not a blocking checkpoint gate.

## Explicit research-consumer limits

CP124 limits remain in force:

- internal critical/subsystem damage is not simulated by the Python ecology consumer;
- the Python ETA Missile travel abstraction is not full C# moving-target/range-exhaustion parity;
- Damage Control progression is instrumented/reference-valid but is not scheduled into these combat encounters;
- residual mission/AUX Space has zero tactical effect until numerical support/mission consumers are introduced.

These limits must be considered when interpreting CP125. In particular, CP125 must not be used to calibrate critical cadence or production Missile range-exhaustion behavior.

## Post-CP125 direction

If CP125 executes cleanly, analyze the 9×9 and Delta-TL progression first. Focused follow-up studies should be driven by observed causal signals rather than by a predetermined sequence of tiny calibration checkpoints. Once the pure-generation curve is understood, proceed to mixed-/legacy-TL ship ecology using CP125 as the control population.
