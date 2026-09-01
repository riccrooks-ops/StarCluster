# Checkpoint 133 - Revised Combat-Subsystem Candidate Baseline

## Status

**Authored candidate; native deterministic acceptance required.**

Checkpoint 132 Corrected Replacement 5 is the accepted mechanics/architecture baseline. Its native results are preserved under `docs/validation/evidence/checkpoint-133/accepted-cp132/` with SHA-256 `5b454578e4e24836a9defeabc6309719ab8d9844b679de9c2a94040d21f1a564`.

CP133 changes reference numerical data only. It does **not** change production C#, the canonical Python combat kernel, scenario definitions, or the active Concept. It runs no Monte Carlo and makes no balance claim.

## Purpose

CP133 records the mechanics-first TL1-TL9 candidate baseline developed after the CP132 defense correction. The selected families are intentionally internally coherent rather than balanced. The older Storyboard remains preserved but is not treated as a numerical constraint; later Storyboard prose may be revised to explain the improved family progression.

The revised profiles are:

- Hull;
- mainline Armor;
- mainline Shields;
- Kinetic main;
- Energy main;
- Missile delivery;
- GP Missile warhead; and
- Swarmer Missile.

Unrelated technology profiles, current component Space footprints, Reactor values, and most branch numerics remain unchanged pending later review.

## New candidate rules recorded with the tables

- Firm direct fire: no track-quality penalty.
- Approximate-track direct fire: **-25 percentage points**.
- Direct fire beyond Standard Range but within Maximum Range: **-10 percentage points**.
- These penalties stack; beyond Maximum Range is illegal.
- Missiles use flight endurance/guidance and do not inherit the direct-fire range penalty.
- Energy Low mode: `ceil(Standard TP / 2)` and `ceil(Standard DAM / 2)`.
- Energy Overload: `ceil(Standard TP x 1.5)` and `ceil(Standard DAM x 1.5)`; every overload adds Strain.
- Kinetic main ammunition is 100 across TL1-TL9.
- GP/Swarmer Missile capacity is 25 Flights and launch TP is 0 across TL1-TL9.
- TL6+ mainline Armor has no free regeneration; Tactical Power restores 1 AI/TP up to the listed cap.
- Shield base recharge plus maximum tactical recharge is intentionally sufficient to restore full contemporary SC in one recharge window.

These are **candidate table rules** in CP133. Implementation into the canonical simulation kernel belongs to the next simulation checkpoint so the data pass remains separate from executable-mechanics changes.

## Branch seeds

- `A_b1`: Crystalline composite Armor enters at TL6 with AP2 / AI12 / no regeneration; later progression is intended but not numerically assigned.
- `E_b1`: higher-SPEN Energy-main branch captured as a concept; TL and exact values TBD.
- `M_b2`: Radiation warhead captured as a CREW-damage specialist concept; TL/tradeoff waits for the CREW model.

Except for the established Swarmer profile, these branch seeds are excluded from initial calibration.

## Numerical authorities

CP133 introduces:

- `docs/design/player_technology/technology_numerical_matrix_v0_6.json`
- `docs/design/player_technology/technology_component_table_v0_8.json`
- `docs/design/player_technology/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8.xlsx`
- `docs/design/player_technology/TL1_TL9_Revised_Combat_Subsystem_Candidate_Baseline_v0_1.md`
- `docs/design/player_technology/canonical_numerical_authority_v0_5.json`

The prior CP128/v0.5-v0.7 files remain preserved for historical evidence.

## Planned same-TL calibration

The next executable study should implement the CP133 candidate through the CP132 canonical kernel, then use controlled TLx-vs-TLx reference ships.

Every reference ship should carry:

- the required core ship systems;
- its contemporary mainline Shield; and
- its contemporary mainline Armor.

Initial weapon families are Kinetic, Energy, GP Missile, and Swarmer (TL2+). Specialist branches are excluded initially. The study should record not just wins but combat progression: first contact, first attack, Shield collapse/recovery, Armor exposure/collapse, Hull damage, ammunition, Tactical Power allocations, PDS outcomes, track quality, range bands, and unresolved/timeout reasons.

The purpose is to find trends and discontinuities before tuning any candidate value.

## Acceptance boundary

CP133 acceptance validates data synchronization and repository integrity only. It must confirm:

- accepted CP132 native provenance;
- exact candidate profile values and invariants;
- workbook/JSON synchronization;
- no changes under `src/`, `tests/`, or `tools/simulation/` relative to accepted CP132;
- no Monte Carlo study or substantive trials; and
- a clean full-repository manifest.
