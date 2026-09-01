# TL1 Kinetic Interaction Calibration Plan v0.1

## Purpose

Checkpoint 27 measures how the revised TL1 kinetic packet and defensive envelope interact before any value is promoted as final balance. The study is intentionally broader than a normal matchup sweep: it isolates damage, penetration, Shield, Armor, Hull, range, EvM, and targeting condition so threshold effects and stalls are visible.

## Revised provisional baseline

| Parameter | Value |
|---|---:|
| Shield Capacity | 2 |
| Shield Armor / Protection | 0 |
| Base Shield recharge | 1 per turn |
| Armor Integrity | 4 |
| Armor Protection | 0 |
| Hull | 12 |
| Kinetic DAM | 3 |
| Kinetic SPEN | 1 |
| Kinetic APEN | 0 |
| Kinetic magazine | 100 attack packages |
| Missile magazine | 24 missiles |

One kinetic package is one attack action. The physical weapon may represent a shell, burst, or salvo. The magazine is intended to support multiple encounters rather than one duel.

## Phase B calibration matrix

The executable study contains 29 variants:

- baseline at range 0, 2, and 4;
- both-sided and one-sided EvM;
- one-sided Degraded Targeting Computer with side-swapped partner;
- DAM 2 and 4 controls around DAM 3;
- SPEN 0 and 2 controls around SPEN 1;
- Shield Capacity 1, 3, and 4 controls around 2;
- Shield Armor 1 and 2 controls around 0;
- Shield recharge 0 and 2 controls around 1;
- Armor Integrity 2, 6, and 8 controls around 4;
- Armor Protection 1 and 2 crossed with APEN 0, 1, and 2;
- Hull 8 and 16 controls around 12.

## Trial contract

- Default: 10,000 trials per variant.
- Master seed: 270100.
- Each trial receives side-independent deterministic d100 streams.
- All variants use common random numbers for the same trial index.
- Worker count cannot alter trial outcomes.
- Mirror variants require absolute Side A versus Side B win-rate difference no greater than 3 percentage points.
- One-sided EvM and one-sided computer-damage variants require explicit side-swapped partners with no greater than 3 percentage points reflected-side difference.
- Reduced trial counts are smoke tests only and cannot support balance conclusions.

## Required outputs

Each variant reports:

- Side A wins, Side B wins, mutual destruction, and unresolved rates with Wilson 95% confidence intervals;
- mean and percentile duel length;
- mean hits by side;
- mean remaining Shield, Armor Protection, Armor Integrity, and Hull by side;
- rates of Hull damage and complete Armor depletion by side;
- mean ammunition consumption by side;
- mirror and side-swap gate results.

## Interpretation guardrails

A value is not accepted merely because a symmetry gate passes. Symmetry proves implementation fairness, not fun. Review must also identify:

- damage packets that cannot progress through a defense;
- excessive unresolved or stall rates;
- duel lengths too short to support tactical decisions;
- duel lengths so long that combat becomes repetitive;
- ammunition consumption inconsistent with several engagements between resupply opportunities;
- thresholds where one point of SPEN, APEN, Shield Armor, or Armor Protection changes the matchup qualitatively.

Energy and missile cross-family balance remains outside this checkpoint.
