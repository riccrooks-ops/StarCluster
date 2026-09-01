# CP127 Main-Subsystem TL Stabilization and Baseline Consolidation Study v0.1

**Checkpoint:** 127 candidate  
**Accepted evidence control:** CP126 native full-map results  
**Source candidate:** `technology_numerical_matrix_v0_4.json`  
**Ship policy:** pure same-TL component profiles per ship; no mixed-TL ships

## Purpose

CP127 is the final bounded main-subsystem stabilization pass before the project resumes broad whole-ladder sensitivity work and then mixed-/legacy-TL ecology. It corrects two explicit movement-authority drifts, applies one narrowly attributed TL8 Energy correction, and rebaselines the affected whole-ladder evidence on the accepted CP126 full-map consumer.

The study is **not** an optimizer and adjacent-TL win rate is **not** a balance target.

## Candidate changes under test

Exactly **nine numerical leaves** change from the CP123/CP126 matrix:

- STL Move: TL5 6→5, TL8 9→8, TL9 10→9, restoring **Move = Drive TL** at every TL;
- Missile Move: TL5 5→6, TL8 8→9, TL9 9→10, restoring **Missile Move = Drive TL + 1** at every TL;
- TL8 Energy Low/Standard/High damage: **8/11/13 → 7/10/12**.

No other main-subsystem numerical leaf is changed. FTL remains the explicit strategic ladder 1/2/3/4/4/6/7/9/12. Most AUX progression remains deferred.

## Full-map baseline re-execution

The CP127 candidate re-executes three complete CP126-compatible lanes:

1. all **9,220 adjacent-population tasks / 36,880 variants**;
2. all **7,699 exact matched-composition tasks / 30,796 variants**;
3. all CP125-seeded TL8/TL9 same-TL Missile-vs-Missile tasks under the corrected candidate, **1,727 tasks / 6,908 variants**.

Combined final-baseline workload: **18,646 tasks / 74,584 variants**.

These results are directly compared to the frozen CP126 native summaries embedded under `docs/validation/evidence/checkpoint-127/`.

## TL5→TL6 one-axis attribution

A deterministic evenly spaced sample of **120 exact matched-composition TL5→TL6 tasks** is reused for nine counterfactual holds. Each counterfactual reverts one TL6 main-system package toward TL5 while leaving the candidate build population and all other TL6 characteristics intact:

- Hull durability;
- Armor;
- STL Move;
- Tactical Computer combat integration;
- Sensor range/discrimination;
- Shield capacity/recharge;
- Kinetic Main performance;
- Energy Main performance;
- Missile delivery/guidance performance.

The candidate reference comes from the full matched-composition execution, so the nine counterfactuals add **4,320 variants**.

Reactor is not assigned a dedicated combat ablation because TL5→TL6 does not increase Operational Tactical Power; its changed degraded/emergency outputs require internal component-state damage that this Python consumer does not simulate, while its Space reduction belongs to design-envelope analysis already separated by matched composition. FTL is strategic and is not a tactical-combat causal axis. ECM/ECCM have no TL5→TL6 rating change. PDS is treated as AUX/support for this stabilization boundary.

## TL8 Energy 2x2 factorial

A deterministic sample of **120 TL8 Energy-isolation quad tasks** crosses Energy/Kinetic attackers against Shield/no-Shield defenders under four Energy parameter states:

| Condition | TL8 Energy damage | APEN |
|---|---:|---:|
| candidate_damage_apen3 | 7/10/12 | 3 |
| cp126_damage_apen3 | 8/11/13 | 3 |
| candidate_damage_apen2 | 7/10/12 | 2 |
| cp126_damage_apen2 | 8/11/13 | 2 |

This adds **7,680 variants** and distinguishes raw-damage pressure from APEN without changing Accuracy, SPEN, range, Space, Tactical Power, target population, or the corrected movement rules.

The design objective is interpretive rather than a hard threshold: the candidate should reduce Energy's no-Shield general-purpose advantage while retaining a meaningful Shield-facing advantage.

## Physical symmetry gate

The accepted CP126 blocking physical symmetry gate is re-run against the revised matrix:

- 9 TLs;
- 5 representative cases per TL;
- both mover orientations;
- 25 trials per case;
- **2,250 comparisons / 4,500 combat executions**;
- **zero mismatches required**.

No numerical table adjustment is allowed to weaken the already accepted coordinate/orientation invariance.

## Workload

- legal pure-TL builds: **9,427**;
- final-baseline variants: **74,584**;
- TL5→TL6 ablation variants: **4,320**;
- TL8 Energy factorial variants: **7,680**;
- total variants: **86,584**;
- one-trial full-pipeline smoke: **86,584 engagements**;
- substantive trials per variant: **100**;
- substantive workload: **8,658,400 engagements**.

This is intentionally much smaller than CP126's 34.75M run. CP126 already established the geometry/fidelity population; CP127 needs enough paired evidence to confirm the narrow corrections and establish the revised baseline without opening another general calibration campaign.

## Primary outputs

- `adjacent_population_summary.csv`
- `matched_composition_summary.csv`
- `cp126_transition_comparison.csv`
- `late_missile_summary.csv`
- `tl5_tl6_ablation_summary.csv`
- `tl8_energy_factorial_summary.csv`
- plan `numerical_change_ledger.csv`
- raw per-condition `variants.csv`

## Acceptance boundary

Blocking:

- the source matrix contains anything other than the declared nine numerical changes;
- STL or Missile movement invariants fail;
- FTL deliberate strategic ladder drifts;
- legal-build population changes unexpectedly;
- native build/test/parity failure;
- physical symmetry mismatch;
- plan/smoke/substantive count mismatch;
- trial errors;
- mixed-TL ship contamination.

Not blocking by itself:

- a strong TL5→TL6 or TL7→TL8 transition;
- uneven adjacent-TL progression;
- late Missile unresolved rate;
- a counterfactual having little or no measured effect;
- an AUX/PDS interaction that is not being promoted in CP127.

Those are review evidence. If they expose a concrete new pathology, the candidate table can be revised before CP127 is accepted; they are not automatic numerical gates.
