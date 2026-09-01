# Checkpoint 163 — APU Maturation and Stacking Resilience Diagnostic

## Purpose

CP162 established a strong provisional power-density result: the former Auxiliary Reactor is healthiest at a fixed **2-Space / +1 TP** base point, with unrestricted stacking bounded by Space economics. CP163 adopts the user-facing name **Auxiliary Power Unit (APU)** for that component and asks when the same 2-Space package should mature to +2 TP at higher TLs.

The principal timing candidates are TL5, TL6, TL7, and TL8, with a flat +1 control. Sparse +3 TP probes at TL8 and TL9 establish the late upper boundary. Main Reactor Space remains fixed at 6, and Operational output remains locally bracketed at PF4 -1 / PF4 / PF4 +1.

## Frozen authority

- CP160-PF4 remains the research-execution baseline.
- CP162 native results are accepted diagnostic evidence.
- Production numerical authority is unchanged.
- The Concept is unchanged.
- Main/PDS/core-defense values and prior AUX magnitudes are unchanged.
- Main Reactor footprint is fixed at 6 Space.
- APU footprint is fixed at 2 Space.

## Naming boundary

CP163 calls CP162's `Auxiliary Reactor` candidate the **Auxiliary Power Unit (APU)** per current design direction. The older active-catalog entry also named `Auxiliary Power Unit` describes a separate core-continuity-only concept; that authority is frozen in CP163. Naming/catalog consolidation is intentionally deferred rather than silently merging two concepts during a numerical diagnostic.

## APU maturation trajectories

- `APU_FLAT_1`: +1 TP at TL1–TL9.
- `APU_MATURE_TL5`: +1 TP at TL1–4, +2 TP at TL5–9.
- `APU_MATURE_TL6`: +1 TP at TL1–5, +2 TP at TL6–9.
- `APU_MATURE_TL7`: +1 TP at TL1–6, +2 TP at TL7–9.
- `APU_MATURE_TL8`: +1 TP at TL1–7, +2 TP at TL8–9.
- Boundary only: 2-Space / +3 TP at TL8 and TL9.

The execution engine de-duplicates these trajectories into 16 unique TL-local APU power points so identical +1/+2 cells are not rerun needlessly. Trajectory-level summaries are reconstructed from those common cells.

## Stacking and resilience

No installation-count cap is imposed. Static analysis screens every legal APU count; stochastic and combat layers exercise 1/2/3/MAX tiers. A deterministic independent-unit failure surface reports retained APU TP after losing one or more APU components, using the existing TL1 boundary of **0 flexible TP while degraded**. No new higher-TL degraded-output rule is invented in this pass, and full integrated component-damage execution remains deferred until a maturation trajectory is selected.

The key safety requirement is unchanged: an APU stack must remain a granular supplement, not an economically superior modular replacement for a full 6-Space Main Reactor.

## Planned scale

- 22,482 pre-existing legal powered architectures retained as the construction reference.
- 5 maturation trajectories, de-duplicated to 16 unique TL-local APU power points.
- 288 aggregate exact static legal-stack support rows.
- 330 deterministic APU component-failure/resilience rows.
- 1,152 stochastic variants × 5,000 turns = **5,760,000 turn-demand samples**.
- 384 mirrored combat contexts × three Main-Reactor offsets = 1,152 cells.
- 2,000 trials/cell = **2,304,000 substantive combats**.

No selection, tuning, PF5 promotion, catalog rename, or production promotion occurs in CP163.
