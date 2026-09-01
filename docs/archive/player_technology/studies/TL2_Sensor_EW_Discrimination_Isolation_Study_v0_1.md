# TL2 Sensor/EW Discrimination Isolation Study v0.1

## Status

Checkpoint 79 diagnostic study plan. Candidate values are **not production authority** unless a later accepted checkpoint explicitly promotes them.

Technology Architecture Matrix v1 remains the conceptual planning authority. Concept v0.6q remains the top-level design authority.

## Purpose

The first TL2 calibration pass isolates the smallest contemporary Sensor/EW package proposed by Matrix v1 while holding the accepted TL1 combat foundation constant. The study asks whether Sensor Discrimination Resistance 1, normal ECM rating 2, and normal ECCM rating 2 create useful tall-versus-wide counterplay without collapsing Tactical Power competition or making the accepted -25 degraded-fire fallback an easy substitute for Firm-track restoration.

This pass deliberately does **not** test the legacy TL2 Tactical Computer +12 ordinary-targeting candidate. The TL1 Tactical Computer/fire-control profile remains in use, including the -25 percentage-point degraded-fire rating for the one explicit study-only degraded-fire package. Sensor ranges, active-sensor power, overload envelope, same-hex Burn-through +1, reactor output, weapons, defenses, movement/fuel rules, PDS, missile terminal rules, and Damage Control remain at the accepted TL1 foundation.

## Candidate package under test

| Property | TL1 control | TL2 candidate in CP79 |
|---|---:|---:|
| Passive Firm / Approximate range | 1 / 3 | 1 / 3 (held) |
| Active Firm / Approximate range | 3 / 4 | 3 / 4 (held) |
| Normal Active Sensor power | 1 TP | 1 TP (held) |
| Active overload | +1/+1 range, +1 TP | held; no overload requested |
| Sensor Discrimination Resistance | 0 | **1** |
| Same-hex Burn-through Resistance | +1 | +1 (held) |
| Normal ECM ceiling | 1 | **2** |
| Normal ECCM ceiling | 1 | **2** |
| ECM/ECCM normal power | 1 TP/rating | **1 TP/rating** |
| ECM/ECCM overload | accepted TL1 model | deferred; no overload requested |
| Tactical Computer ordinary targeting | TL1 current | **TL1 current; +12 TL2 candidate excluded** |
| Degraded-fire penalty | -25 pp when supported | -25 pp held |

The resolver relationship remains:

`Effective Jamming Margin = max(0, ECM - ECCM - Sensor DR - Burn-through)`

Only a positive effective margin may degrade an otherwise Firm observation. Same-hex line of sight remains unoccludable and the existing +1 same-hex Burn-through still applies.

## Diagnostic arithmetic outside same-hex Burn-through

The study must preserve these candidate relationships before Monte Carlo outcomes are considered:

- TL1 Sensor DR 0 + ECM 1 + ECCM 1 -> margin 0.
- TL1 Sensor DR 0 + ECM 2 + ECCM 1 -> margin 1.
- TL1 Sensor DR 0 + ECM 2 + ECCM 2 -> margin 0.
- TL2 Sensor DR 1 + ECM 1 + ECCM 0 -> margin 0.
- TL2 Sensor DR 1 + ECM 2 + ECCM 0 -> margin 1.
- TL2 Sensor DR 1 + ECM 2 + ECCM 1 -> margin 0.

These are architecture checks, not desired win-rate targets.

## Operational study

Study ID: `tl2-itc06-sensor-ew-discrimination-isolation`

The study uses six paired combat contexts: Kinetic-vs-Missile and Energy-vs-Missile at fixed range 3, plus dynamic Track-Aware Opponent Range contexts with both Side-A-first and Side-B-first movement orders. Each context contains nine packages, for **54 variants** total.

The nine packages are:

1. Unjammed TL1 Firm reference.
2. TL1 Sensor / ECM 1 / reactive ECCM 1 accepted consumer control.
3. TL1 Sensor versus ECM 2, Firm-only, no ECCM.
4. TL1 Sensor versus ECM 2 with reactive ECCM 1.
5. TL1 Sensor versus ECM 2 with reactive ECCM 2 (wide-research compensation diagnostic).
6. TL1 Sensor versus ECM 2 with explicit study-only -25 degraded fire and no ECCM.
7. TL2 Sensor DR 1 versus ECM 1 with no ECCM (tall-research value diagnostic).
8. TL2 Sensor DR 1 versus ECM 2, Firm-only, no ECCM.
9. TL2 Sensor DR 1 versus ECM 2 with reactive ECCM 1 (tall-plus-support diagnostic).

Side B remains on the TL1 Balanced-0 sensor control in every variant so Missile sensing/acquisition is not silently upgraded while Side A's sensor is isolated. Ordinary missiles remain on their accepted Firm-terminal architecture and never receive degraded-fire permission.

## Actual-consumer infrastructure added for the study

The integrated tactical-combat study document now supports optional per-side Sensor/EW profile IDs and optional per-side normal ECM/ECCM rating overrides. Legacy studies retain the shared Sensor/EW profile and normal rating 1 defaults, so historical behavior is unchanged.

A normal EW rating override consumes the existing normal power cost **per rating point**. At the CP79 candidate cost of 1 TP/rating, rating 2 consumes 2 TP before any component-condition overhead. Overload remains a separate mechanism and is not requested by CP79 variants.

These fields are diagnostic/runtime plumbing, not a promotion of TL2 production components.

## Release gates versus review evidence

Release gates verify only structural/semantic behavior: variant coverage, actual-consumer binding, TL1 rating-1 control behavior, ECM-2 degradation of a TL1 sensor, insufficiency of ECCM 1 against ECM 2 with DR 0, restoration by ECCM 2, tall Sensor DR 1 value against old ECM 1, continued vulnerability of DR 1 to contemporary ECM 2, restoration by DR 1 + ECCM 1, and explicit degraded-fire/missile boundaries.

The following remain **human review evidence** rather than release targets:

- win share;
- turns to resolution and unresolved rate;
- Tactical Power spent on ECM/ECCM and active sensing;
- direct-fire hit throughput;
- PDS opportunity cost under missile pressure;
- whether wide ECCM 2 or tall Sensor DR 1 is economically attractive;
- whether -25 degraded fire remains a meaningful but materially inferior fallback;
- whether any TL2 candidate should be promoted, revised, or rejected.

## Promotion rule

Checkpoint 79 itself promotes nothing. If native results support a TL2 candidate, a later checkpoint must explicitly update production component data, Concept/Matrix status, and the appropriate regression contracts. If results expose an interaction problem, revise the Matrix candidate before moving to later TL progression.
