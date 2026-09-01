# TL2 EW Power Pressure and Tall Viability Study v0.1

## Status

Checkpoint 80 diagnostic follow-up to accepted Checkpoint 79a. This file remains the focused historical CP80 study record. Its reactor-output 6 rows remain **sensitivity evidence only** and were never promoted. Sensor DR 1 plus normal ECM/ECCM ceiling 2 at 1 TP/rating were later supported by CP81a-era integration and are now **validated working candidates**, not production component data; consult Technology Architecture Matrix v1 and the active Concept for current status.

Technology Architecture Matrix v1 remains the current TL1-TL9 progression-planning authority. Concept v0.6t is the current top-level design authority; this historical study does not supersede either source.

## Accepted evidence carried forward from Checkpoint 79a

Native Checkpoint 79a acceptance succeeded with 863/863 unit tests, all 11 runner stages, 47 ScenarioRunner self-tests, 54 substantive variants / 540,000 substantive trials, zero failed gates, and zero trial errors. The accepted CP79a substantive summary SHA-256 is:

`eecbdf5a935d984655416c3fe4fae61308493cad778c89b2272f84ea5b761c61`

The CP79a evidence established the mechanical relationships we wanted:

- Sensor DR 1 resists obsolete ECM 1 without powered ECCM.
- Sensor DR 1 alone remains vulnerable to contemporary ECM 2.
- Sensor DR 1 + ECCM 1 restores Firm against ECM 2.
- A TL1 Sensor + ECCM 2 can also restore Firm against ECM 2 by paying the full 2-TP ECCM cost.
- The old-Sensor + ECCM2 route was substantially more power-punishing under missile/PDS pressure, especially for the power-hungry Energy package.
- The explicit -25 degraded-fire fallback remained useful but materially inferior to the appropriate contemporary Sensor DR1 + ECCM1 response.

Those results are evidence, not an automatic TL2 production promotion.

## Purpose

Checkpoint 80 isolates the **power-pressure consequence** of the CP79a EW candidates. The core design question is not whether ECCM 2 can restore Firm; CP79a already proved that. The question is whether the brute-force mixed-tech path is appropriately expensive rather than universally bad, and whether the contemporary tall Sensor path remains viable for power-hungry ships.

Higher-TL equipment is allowed to demand more Tactical Power. Technology progression does **not** imply automatic power efficiency. A tall or heavily skewed research path may therefore produce a ship that cannot power every advanced system simultaneously. That is a legitimate build and reactor tradeoff, provided higher TL still broadens or improves viable solutions rather than systematically making advanced builds unusable.

Checkpoint 80 therefore compares the same Sensor/EW response packages under two kinds of combat pressure:

1. **Missile pressure**, where Side A must also preserve PDS opportunity.
2. **Direct-fire pressure**, where PDS is installed but should consume no combat power because no hostile missiles exist.

It also repeats the two Firm-restoring paths with a **6-TP Side-A reactor sensitivity**. Reactor 6 is not promoted by this study; it is a diagnostic probe drawn from the previously tested historical TL2 power vector. The study asks whether one additional TP rescues an otherwise over-constrained build, or instead crosses an integer breakpoint that erases healthy tradeoffs.

## Frozen architecture

Checkpoint 80 keeps the following unchanged from accepted 79a:

- TL1 production combat profiles and weapon statistics;
- the 35-Space `balanced_generalist_ew_major` fixture;
- TL1 Tactical Computer behavior and the -25 degraded-fire penalty;
- explicit weapon permission as the prerequisite for degraded direct fire;
- Sensor Balanced-0 reach, normal Active Sensor power, overload envelope, and same-hex Burn-through +1;
- Sensor DR 0 / DR 1 candidate pair;
- normal ECM/ECCM power cost of 1 TP per rating;
- ECM/ECCM overload behavior (not requested);
- movement/fuel, defenses, Damage Control, PDS rules, and ordinary missile Firm-terminal architecture;
- FullVolleyFirst Tactical Power doctrine;
- no production degraded-fire grant and no missile degraded-fire capability.

The legacy TL2 Tactical Computer +12 ordinary-targeting candidate remains excluded so the study does not stack another offensive improvement onto the power-pressure question.

## Operational study

Study ID: `tl2-itc07-ew-power-pressure-tall-viability`

The study contains **12 combat contexts**, each with six response packages, for **72 variants / 720,000 default substantive trials**.

### Combat contexts

Each Kinetic and Energy Side-A package is tested against both Missile and Kinetic Side-B opponents:

- fixed range 3 with simultaneous movement order;
- dynamic Track-Aware Opponent Range with Side A moving first;
- dynamic Track-Aware Opponent Range with Side B moving first.

This produces four family pairings x three geometry/order contexts:

- Kinetic vs Missile;
- Energy vs Missile;
- Kinetic vs Kinetic;
- Energy vs Kinetic.

Side B uses the TL1 Balanced-0 sensor control in every context. Jammed packages use candidate ECM rating 2. Firm-reference packages use no hostile ECM.

### Six response packages

1. **Firm reference, 5 TP** — TL1 Sensor, no hostile ECM, no ECCM.
2. **Wide ECCM2, 5 TP** — TL1 Sensor + reactive ECCM rating 2 against ECM 2.
3. **Tall DR1 + ECCM1, 5 TP** — Sensor DR 1 + reactive ECCM rating 1 against ECM 2.
4. **Degraded -25, 5 TP** — TL1 Sensor, no ECCM, explicit study-only weapon degraded fire at -25 pp against ECM 2.
5. **Wide ECCM2, 6-TP sensitivity** — same old-Sensor + ECCM2 package with Side-A reactor output 6.
6. **Tall DR1 + ECCM1, 6-TP sensitivity** — same contemporary tall package with Side-A reactor output 6.

Side B remains at reactor output 5 in every variant. The 6-TP rows therefore isolate Side-A power headroom rather than changing both sides at once.

## What this study should reveal

The most useful evidence is comparative, not a target win percentage:

- whether ECCM2 is mainly punished when PDS competes for the same power, or whether it is broadly unattractive even against direct-fire opponents;
- whether Sensor DR1 + ECCM1 remains a credible tall contemporary solution on Energy ships at 5 TP;
- how much one additional Side-A TP changes offense, PDS, shield/recharge opportunity, insufficient-power preventions, and combat pacing;
- whether the 6-TP sensitivity rescues a constrained design without simply erasing all meaningful power choices;
- whether the -25 degraded-fire fallback remains materially inferior to the contemporary Firm-restoring path while still providing useful agency;
- whether a future rating-2 ECCM doctrine should become more power-aware, rather than blindly paying 2 TP whenever Firm restoration is mechanically possible.

## Release gates versus review evidence

Release gates remain structural and mechanical. They verify the 72-variant package, family/geometry coverage, clean Firm references, actual Firm restoration by both ECCM paths, execution of the -25 Approximate-fire fallback, and execution of the reactor-6 sensitivity rows. They do **not** require one candidate to achieve a chosen win rate.

Human review will assess:

- conditional win share and unresolved rate;
- turns to resolution;
- direct-fire hit throughput;
- mean active-sensor and ECCM Tactical Power;
- insufficient-power preventions;
- hostile missile launches and Side-A PDS attempts/intercepts;
- direct-fire-opponent cases where PDS should cease to be the dominant competing power sink;
- 5-TP versus 6-TP deltas for wide and tall responses;
- degraded-fire versus ECCM economic value;
- whether the current reactive ECCM behavior needs a rating-aware affordability refinement.

## Promotion rule

Checkpoint 80 promotes nothing automatically. Sensor DR1, ECM2, ECCM2, and reactor output 6 remain candidate/sensitivity values until the native results are reviewed. A later promotion must update Concept/Matrix status and production component data explicitly.
