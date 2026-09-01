# TL1-TL9 Revised Combat-Subsystem Candidate Baseline v0.1

**Checkpoint:** 133  
**Status:** mechanics-first candidate; intentionally unbalanced; same-TL calibration pending.

CP132 is the accepted mechanics baseline. This document records the revised logical progression for the selected combat families without requiring the older Storyboard to remain numerically authoritative. Reactor values, most component Space costs, unrelated subsystem profiles, and most branch numerics are unchanged/pending.

## Universal provisional combat modifiers

- Firm direct fire: no track-quality penalty.
- Approximate-track direct fire: **-25 percentage points**.
- Direct fire beyond Standard Range and within Maximum Range: **-10 percentage points**.
- The two penalties stack. Beyond Maximum Range is illegal. Missiles do not use the direct-fire range penalty.
- Energy Low mode: `ceil(Standard TP / 2)` and `ceil(Standard DAM / 2)`.
- Energy Overload: `ceil(Standard TP x 1.5)` and `ceil(Standard DAM x 1.5)`; every overload adds Strain.
- Kinetic main ammunition: 100. GP/Swarmer Missile Flights: 25. Missile launch TP: 0.

## Mainline revised values

| TL | Hull Space/Hull | Armor AP/AI/RegenCap | Shield SC/Base/+perTP/CapTP/SA | K ACC/D/SP/AP/Rstd-Rmax/TP | E ACC/Dstd/SP/Rstd-Rmax/TPstd | GP M Range/Move/D/SP/AP | Swarmer packets |
|---:|---|---|---|---|---|---|---|
| 1 | 35/24 | 0/6/0 | 4/2/1/2/0 | +20/D6/SP0/AP0/R2-3/1TP | +25/D5/SP0/R2-4/2TP | R6/M2/D8/SP0/AP0 | — |
| 2 | 35/25 | 0/8/0 | 5/2/1/3/0 | +20/D7/SP0/AP1/R2-3/1TP | +30/D5/SP0/R3-4/2TP | R7/M3/D8/SP0/AP0 | 2xD3 / SP0 / +10 terminal / PDS -10 |
| 3 | 36/26 | 1/9/0 | 6/2/2/2/0 | +20/D7/SP0/AP1/R2-4/1TP | +30/D5/SP0/R4-5/2TP | R7/M4/D8/SP0/AP0 | 2xD3 / SP0 / +10 terminal / PDS -10 |
| 4 | 36/27 | 1/10/0 | 7/3/2/2/0 | +25/D7/SP0/AP2/R2-4/1TP | +30/D6/SP0/R4-6/2TP | R8/M5/D9/SP0/AP0 | 2xD4 / SP0 / +10 terminal / PDS -10 |
| 5 | 37/28 | 2/10/0 | 8/2/2/3/0 | +25/D8/SP0/AP2/R3-5/1TP | +30/D6/SP1/R4-6/2TP | R9/M6/D10/SP0/AP0 | 2xD4 / SP0 / +10 terminal / PDS -10 |
| 6 | 37/29 | 1/10/1 | 8/4/2/2/0 | +30/D8/SP0/AP2/R3-6/1TP | +35/D6/SP1/R5-7/2TP | R10/M7/D10/SP0/AP0 | 2xD4 / SP0 / +10 terminal / PDS -10 |
| 7 | 38/30 | 1/12/2 | 9/3/2/3/0 | +30/D9/SP0/AP2/R3-6/1TP | +35/D7/SP1/R5-7/2TP | R10/M8/D11/SP0/AP0 | 2xD5 / SP0 / +15 terminal / PDS -15 |
| 8 | 38/31 | 2/12/2 | 10/4/3/2/1 | +30/D10/SP0/AP3/R4-7/2TP | +35/D8/SP2/R5-8/4TP | R11/M9/D12/SP1/AP0 | 2xD5 / SP1 / +15 terminal / PDS -15 |
| 9 | 39/32 | 3/14/3 | 12/6/3/2/1 | +35/D11/SP0/AP3/R4-8/2TP | +40/D9/SP2/R5-9/4TP | R12/M10/D14/SP1/AP0 | 2xD6 / SP1 / +15 terminal / PDS -15 |

## Branch seeds

- **A_b1 - Crystalline composite armor:** introduced at TL6 as AP2 / AI12 / no tactical regeneration. Later-TL advancement is intended but values are TBD.
- **E_b1 - higher-SPEN Energy:** concept captured; placement and numerical profile TBD.
- **M_b2 - Radiation warhead:** concept captured as a CREW-damage specialist; placement/tradeoffs wait for the CREW model.

## Shield recharge invariant

At every TL, `Base Recharge + (Recharge per TP x TP cap)` is intentionally sufficient to restore the listed full SC from zero in one recharge window. Excess recharge is lost.

## Planned calibration boundary

Initial post-implementation balance work uses TLx-vs-TLx reference ships. Every reference ship carries the contemporary mainline Shield and Armor plus required core ship systems. The initial offensive family set is Kinetic, Energy, GP Missile, and Swarmer (TL2+). Branch profiles are excluded until the mainline trends are mechanically reasonable.
