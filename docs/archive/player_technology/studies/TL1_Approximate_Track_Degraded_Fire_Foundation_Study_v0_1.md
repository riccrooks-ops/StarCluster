# TL1 Approximate-Track Degraded-Fire Foundation Study v0.1

## Current architecture interpretation

This file is retained as historical calibration evidence. Current architecture separates degraded-fire **permission** from its numerical penalty: a specific weapon/variant/upgrade grants permission to fire from Approximate, while the ship Tactical Computer/fire-control profile supplies the degraded-fire penalty. Historical `-10/-20/-25/-30` study fields therefore represent candidate computer/fire-control penalties applied to explicitly enabled study weapons; they are not production weapon-profile-owned numbers. The current TL1 computer working value is -25 percentage points, and no production weapon is enabled merely by this clarification. Ordinary missiles remain Firm-terminal by default; any future Approximate-target missile rule is separate and missile-specific.

## Question

Can a direct-fire weapon carry an explicit data-driven trait that permits fire on an Approximate track at a substantial accuracy penalty, while Firm-only weapons remain blocked and missile/torpedo guidance remains unchanged?

## Scope

Checkpoint 74 implements the generic trait and a controlled diagnostic sweep only. It does **not** assign degraded fire to any production TL1 weapon. Production direct fire therefore remains Firm-only after this checkpoint.

The study holds the accepted TL1 Sensor/EW mechanics fixed and uses Balanced-0 sensing, 5 TP, no overload, no ECCM, no missiles, no PDS, and fixed range. Bilateral normal ECM creates a legitimate Approximate-track condition at ranges 2 and 3.

Contexts:

- Kinetic vs Energy at range 2.
- Kinetic vs Energy at range 3.
- Energy vs Kinetic at range 2.
- Energy vs Kinetic at range 3.

Each context contains five paired variants:

1. unjammed Firm-track reference;
2. bilateral ECM + Firm-only weapons;
3. bilateral ECM + Approximate-track trait at -10 percentage points;
4. bilateral ECM + trait at -20 percentage points;
5. bilateral ECM + trait at -30 percentage points.

## Interpretation

Release gates prove wiring only: Firm references still fire normally, Firm-only weapons remain blocked on Approximate tracks, trait-enabled weapons actually fire, and every context carries the intended symmetric -10/-20/-30 candidate definitions. Observed hit chance, win rate, pacing, and the preferred penalty are review evidence rather than release gates.

The purpose is to identify a qualitative useful-but-inferior penalty region, not to finalize every weapon's degraded-fire behavior. Missile and torpedo rules are explicitly outside this trait.
