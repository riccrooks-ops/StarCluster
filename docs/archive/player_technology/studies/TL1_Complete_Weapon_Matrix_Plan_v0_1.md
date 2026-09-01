# TL1 Complete Weapon Matrix Plan v0.1

## Purpose

Checkpoint 29 completes the stripped-down TL1 kinetic, energy, and missile comparison before ECM, ECCM, PDS, richer Tactical Power doctrines, component damage, or specialized counters are introduced. The purpose is to find mechanically broken interactions, not to force final parity among weapon families.

## Revised Evasive Maneuvering

- Attacks against an evasive target suffer -10 percentage points.
- Direct fire by an evasive shooter suffers -5 percentage points.
- Target EvM reduces missile terminal Guidance by 10 percentage points.
- Launcher EvM does not impose a post-launch accuracy penalty on an autonomous Missile Flight.
- EvM remains 1 Spent Tactical Power and doubled STL fuel under the accepted broader rules.

## Accepted baseline weapon values

| Family | Accuracy / Guidance | DAM | SPEN | APEN | Range | Resource |
|---|---:|---:|---:|---:|---:|---|
| Kinetic | +20 Accuracy | 3 | 1 | 0 | 4 hexes | 100 attack packages |
| Energy standard | +25 Accuracy | 3 | 1 | 1 | 5 hexes | 2 TP per attack; no ammunition |
| Missile | 55% Guidance | 5 | 1 | 2 | 6 traveled hexes | 24 Missile Flights |

The TL1 missile moves 1 hex per missile action, replans toward the current target position each action, and accumulates every traveled hex against Maximum Range.

## Executable study

The study contains 48 variants at 10,000 trials each. It includes:

- kinetic, energy, and missile mirrors at ranges 0, 2, and 4;
- one-sided and two-sided EvM for all three families;
- every side-swapped kinetic-energy, kinetic-missile, and energy-missile matchup at ranges 0, 2, and 4;
- missile Guidance controls at 55%, 65%, and 75%;
- missile warhead DAM 4, 5, and 6 controls;
- shield-focused and armor-focused penetration packets;
- four-missile ammunition exhaustion;
- launch separation beyond missile Maximum Range;
- equal-speed target outrunning a TL1 missile;
- Speed 2 pursuit control;
- moving-target missile-versus-kinetic side swaps.

## Mechanical classifications

The study reports and preserves these findings without immediately adding compensating subsystem rules:

- normal resolution;
- hard stall / unresolved at turn cap;
- ammunition exhausted before destruction;
- missile range exhausted;
- target cannot be caught;
- weapon packet cannot produce permanent progress;
- processing-side bias;
- asymmetric side-swap mismatch.

## Gates

- Mirror exclusive-win side bias must be no more than 3 percentage points.
- Side-swapped cross-family pairs must reproduce the opposing-side exclusive-win rate within 3 percentage points.
- Every variant reports turns, direct-fire hits, launches, missile hits, range exhaustion, remaining Hull, and ammunition consumption.

## Scope restraint

This checkpoint does not add ECM, ECCM, PDS, held interception, command-guidance bonuses, active-sensor bonuses, component damage, surrender, retreat, or expanded Tactical Power doctrines. The existing full-flight missile runtime remains preserved and separately regression-tested; the TL1 weapon matrix is a controlled combat-calibration layer, not a replacement for that runtime.
