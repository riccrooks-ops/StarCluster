# Checkpoint 149 - Kinetic Full-Characteristic Multivariate Response-Surface Sweep

**Corrected replacement CR1:** native RepositoryOnly exposed a wrapper-only import-path defect after the isolated 374-test regression had already passed. The focused-test loop did not carry `tools/simulation` on `PYTHONPATH`, causing `test_cp149_kinetic_full_characteristic_sweep.py` to fail import of `starcluster_research`. CR1 centralizes the simulation-path environment for isolated and focused test calls. No research logic, sweep population, numerical value, or acceptance count changes.

## Purpose

Checkpoint 148 is the native-accepted whole-combat Stage-A baseline under `cp147_tactical_utility`. CP149 is the first broad numerical intervention study after that baseline. It does not change accepted gameplay authority. Instead, it sweeps the Kinetic family across the full accepted K-vs-non-K Stage-A context space to map sensitivities, interactions, thresholds, role viability, identity costs, and Pareto regions before any value promotion.

## Frozen baseline

CP149 preserves the CP148 Concept, Technology Numerical Matrix, production C#/Godot mechanics, canonical combat kernel v0.7, tactical-utility doctrine, all non-K weapon values, all defense/PDS/Sensor/EW/AUX/Reactor values, scenario identities, resource environments, and turn/termination semantics. Kinetic SPEN remains exactly 0 as a family-identity constraint.

The submitted native CP148 results archive is provenance-locked by SHA-256 `b00c97b620cc7824760a8af5b41e0e888bb1d7ace16e3d51d426473c6a86788e`; curated accepted CP148 summaries/surfaces are retained under `evidence/checkpoint-149/accepted-cp148/`.

## Operational Kinetic factors

Every TL is centered on the executable reconciled CP148 Kinetic profile, not a stale raw table row. Seven operational factors are swept:

- Accuracy: -10 / 0 / +10 percentage points.
- Damage: -2 / 0 / +2.
- APEN: -2 / 0 / +2.
- Firing TP: -1 / 0 / +1 relative to the Kinetic demand in each resource environment.
- Standard range: -1 / 0 / +1 hex.
- Extended range band (`maxRange-standardRange`): -1 / 0 / +1 hex.
- Ammunition: 25 / 100 / 200 rounds.

Space is also a real Kinetic characteristic, but the fixed Stage-A templates do not automatically spend freed Space on invented AUX. Therefore Space is swept separately at -2/-1/0/+1/+2 Space as a construction legality/headroom surface. It is not falsely treated as direct combat output.

## Design size

Per TL, CP149 uses 163 candidates:

- 1 baseline;
- 14 single-factor axial points;
- 84 points covering every pair of factors at all four low/high combinations;
- 64 high-dimensional resolution-VII half-fraction points.

Across TL1-TL9 this is 1,467 TL-candidates.

The combat context population contains every accepted CP148 same-TL cell with exactly one Kinetic side and one non-K opponent: 2,600 contexts total, preserving both side assignments, all five resource environments, all ten strata, and every opponent family available at that TL.

At 100 common-random-number trials per candidate-context cell:

- 423,800 candidate-context cells;
- **42,380,000 substantive combats**.

RepositoryOnly executes all 1,467 TL-candidates on a 260-context representative smoke panel at one trial/cell = 42,380 smoke combats. This is execution coverage, not balance evidence.

## Analysis outputs

The merged native study emits candidate/context results and response surfaces by TL, opponent, stratum, resource environment, and Armor role, plus:

- candidate ledger;
- axial main-effect estimates;
- all pairwise interaction estimates;
- combat Pareto candidates;
- Kinetic Space construction envelope;
- TP fulfillment/load telemetry;
- delivery, damage, Held-Main/PDS, ammunition/endurance telemetry;
- family identity-stress flags when a Kinetic candidate exceeds contemporary Energy accuracy or range.

Identity-stress candidates remain in the experiment so the cost of preserving family identity is measurable, but no stress candidate or any other candidate may be silently promoted.

## Acceptance

Run in the same fresh extraction:

```powershell
.\tools\checkpoints\checkpoint-149\apply_checkpoint_149.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-149\apply_checkpoint_149.ps1
```

The second invocation is resumable by TL/candidate block and executes the substantive 42.38M-combat study. CP149 remains `tuningAllowed=false`, `automaticPromotion=false`, and `stageBAutomatic=false`. Native acceptance validates execution and evidence integrity; numerical promotion is a later decision after analysis.
