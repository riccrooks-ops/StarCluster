# TL1 Energy Interaction Calibration Plan v0.1

## Purpose

Checkpoint 28 calibrates the TL1 Energy Cannon against the accepted Checkpoint 27c kinetic and defensive baseline. It measures energy output modes, Tactical Power opportunity cost, shield-recharge competition, range retention, EvM, computer and reactor degradation, and cross-family outcomes.

## Accepted inputs

- TL1 cruiser: Shield Capacity 2, Shield Armor 0, base recharge 1; Armor Integrity 4, Armor Protection 0; Hull 12.
- Kinetic control: DAM 3, SPEN 1, APEN 0, Accuracy +20, range 4, zero firing power, 100 packages.
- Energy low: DAM 2, SPEN 0, APEN 0, Accuracy +25, range 5, 1 TP.
- Energy standard: DAM 3, SPEN 1, APEN 1, Accuracy +25, range 5, 2 TP.
- Energy Safe overload: DAM 4, SPEN 1, APEN 1, 3 TP and +1 Strain. The study permits only two safe overload shots before returning to standard output.
- Reactor output 5 TP; EvM costs 1 TP; tactical shield recharge is one Shield per TP, capped by missing capacity and weapon-power reservation.

## Scope

The executable study contains 31 variants and 10,000 trials per variant. It includes energy mirrors at range 0/2/4/5; low, standard, and two-shot safe-burst doctrines; tactical recharge doctrines; EvM; degraded targeting computers; degraded reactors; accuracy and range-penalty controls; and side-swapped energy-versus-kinetic comparisons.

Forced overload beyond the Energy Cannon Strain Limit is excluded until failure and critical-failure consequences are implemented as complete component-state mechanics.

## Gates

- Mirror side-win bias must be no more than 3 percentage points.
- Side-swapped asymmetric pairs must reproduce the opposing-side win rate within 3 percentage points.
- Every variant reports terminal outcomes, turns, hits, Hull state, Tactical Power spent, tactical Shield restoration, and kinetic ammunition use.

## Interpretation

The study is diagnostic. It does not lock final energy values by itself. A mode may be viable as a constrained or emergency choice without matching the standard kinetic cannon in every context.
