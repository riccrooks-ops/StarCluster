# Technology Integration Permutation Suite Architecture v0.9

## Authority

This is the current standing integration-suite architecture. It defines reusable coverage, legal-build enumeration, screening, and escalation rules. It is **not** a checkpoint evidence log and does not itself promote gameplay values.

## Generalized legal-build envelope

The current TL1/TL2 working envelope uses a 35-Space cruiser and independently enumerates weapon, reactor, tactical computer, sensor, shield, armor, ECM, ECCM, and PDS choices. The fixed shell holds only the mandatory STL and FTL drives constant at 10 Space.

The first generalized multiplicity envelope supports one or two homogeneous Main Weapons and one or two homogeneous Main Reactors as explicit construction choices. It also permits the optional absence of active sensors, shields, PDS, ECM, and ECCM. Multiple ECM/ECCM suites may be installed for redundancy; their ratings never add and runtime resolves the highest applicable functional rating. Tactical Power sufficiency is an operational tradeoff, not a construction-legality filter.

The deterministic envelope contains **82,944 raw combinations**, of which **22,592 are legal at 35 Space or less**; **4,672** exactly fill 35 Space. The legal envelope represents **510,398,464 oriented** or **255,210,528 unordered-with-self** potential pairings. The current footprint does not permit a legal build containing both two full Main Weapons and two full Main Reactors.

## Bounded screening strategy

Expensive combat simulation does not exhaustively Monte Carlo the full pairing envelope. The current screen combines:

- 48 durable named/diagnostic ordered pairings; and
- a deterministic 96-pair stratified sample drawn from the complete legal envelope.

The stratified sample crosses four composition classes—single/no-EW-redundancy, EW redundancy, Main-Weapon/Reactor duplication, and combined duplication—with six progression-distance strata: Side A lower-near, lower-far, equal-low, equal-high, higher-near, and higher-far. Near means an Advanced Component Count difference of 1–2; equal-low means both sides have at most 3 advanced components. Four ordered pairings are selected per composition/stratum cell.

The resulting 144 logical pairings are executed at fixed Range 3 and both TrackAware movement orders for **432 actual-consumer variants**. Sampling is deterministic and repeatable; it is screening evidence, not a claim that sampled builds are representative of player choice frequencies.

## Execution guards

1. Deterministically enumerate the complete legal-build envelope and validate construction/multiplicity rules.
2. Generate physical build documents for every build referenced by the bounded screen.
3. Actual-consumer preflight the generated combat study.
4. Run one trial per variant through the full combat pipeline before substantive Monte Carlo.
5. Preserve the accepted rated-cost, preserve-combat-package EW doctrine.
6. Broad legal-build screening may include strategically weak or track-denied fixed references. Release gating rejects pure self-inflicted power-doctrine zero-attack deadlocks, while dynamic contexts must preserve every attack type materially active in the fixed reference.
7. Redundant same-type ECM/ECCM suites use the highest applicable functional rating and never add ratings.
8. Win rates, rankings, progression strata, and build-composition outcomes remain human-review evidence. No automatic candidate promotion or retuning is permitted.

## Expansion direction

The generalized builder is deliberately extensible. Later envelopes may add heterogeneous dual-main/dual-reactor combinations, more component families, compatibility/prerequisite rules, broader TL ranges, and larger or adaptive samples. Expansion should preserve causal interpretability through deterministic enumeration, explicit strata, screening, and targeted high-trial escalation rather than indiscriminate exhaustive Monte Carlo.

Shared sensitivity/integration axes never imply symmetric technology progression across subsystem families.
