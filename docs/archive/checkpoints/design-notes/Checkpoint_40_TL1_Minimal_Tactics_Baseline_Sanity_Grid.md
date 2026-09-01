# Checkpoint 40 - TL1 Minimal-Tactics Baseline Sanity Grid

## Purpose

Checkpoint 40 asks whether the accepted TL1 production values produce broadly plausible combat before adaptive tactics and higher technology complicate the picture. The study is a baseline sanity check, not a demand for perfect weapon-family parity.

## Primary grid

The primary study contains all nine ordered kinetic, energy, and missile pairings at fixed Ranges 2, 3, 4, and 5. Each of the 36 variants uses:

- production Kinetic DAM 4/APEN 0;
- production Armor AP 0;
- Hold orders for both ships;
- no movement or STL overload;
- no withdrawal or disengagement objective;
- no Evasive Maneuvers;
- no Damage Control;
- no Protected Compartmentation.

The primary lane retains ordinary automatic and causal rules: base Shield recharge, automatic PDS against eligible missiles, Tactical Power, ammunition, weapon recycle, missile flight and range, internal criticals, component conditions, and terminal destruction or mission-kill assessment.

## Diagnostic controls

The full 36-variant grid is repeated with Armor AP 1 solely to confirm that energy APEN behaves sensibly once armor protection exists. This does not promote AP 1 to the TL1 production baseline.

At Range 4, one factor is added or removed at a time:

- Damage Control enabled with the accepted component-first/reserve-one doctrine;
- Evasive Maneuvers enabled;
- Protected Compartmentation enabled;
- base Shield recharge disabled;
- PDS disabled for the five missile-facing ordered pairings.

These controls identify causes without turning the primary grid into another tactical-doctrine study.

## Review interpretation

Balance signals are intentionally non-blocking. Broad review bands classify the stronger side's win percentage as essentially even, soft advantage, strong advantage, large advantage, or likely baseline gap. Pacing flags identify high mean duration, a large share of combats beyond 18 turns, or unresolved outcomes.

Range 5 includes deliberate envelope controls. A direct-fire family that cannot legally attack at that range is not automatically considered underpowered; the result proves that range advantage matters under fixed geometry.

## Permanent baseline binding

The Checkpoint 39c preflight prohibition against copied mutable production values remains permanent. Production-profile scenarios and deterministic expectations must resolve mutable balance values from the authoritative baseline or derive them from resolved inputs/results. Explicit fixed mechanics fixtures remain allowed only when clearly separated from production calibration.

## Outputs

The focused stage writes:

- `summary.json` - study and gate summary;
- `variants.csv` - complete causal telemetry for all 113 variants;
- `gates.csv` - blocking implementation and coverage gates;
- `review-grid.csv` - non-blocking AP 0 Range 2-5 balance and pacing review grid;
- `result.sha256.txt` - focused output digest.

All historical isolated and integrated lanes remain configured as regression controls.
