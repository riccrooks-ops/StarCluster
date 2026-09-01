# TL1-TL9 Recharge and Damage Control Candidate Delta v0.1

**Checkpoint:** 135  
**Comparison baseline:** accepted CP134 same-TL evidence.

This is a narrow before/after delta. All CP134 weapon, Hull, Armor, Reactor, Space, range/track, Energy-mode, PDS, and TL6 A_b1 values remain unchanged.

## Shield recharge

A collapsed Shield no longer returns to full SC in one recharge window.

| TL | SC | Base | per TP | TP cap | Max restore from 0 | Missing after max |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 1 | 1 | 2 | 3 | 1 |
| 2 | 5 | 2 | 1 | 2 | 4 | 1 |
| 3 | 6 | 2 | 1 | 2 | 4 | 2 |
| 4 | 7 | 2 | 1 | 3 | 5 | 2 |
| 5 | 8 | 3 | 1 | 3 | 6 | 2 |
| 6 | 8 | 3 | 1 | 3 | 6 | 2 |
| 7 | 9 | 3 | 1 | 4 | 7 | 2 |
| 8 | 10 | 4 | 2 | 2 | 8 | 2 |
| 9 | 12 | 6 | 2 | 2 | 10 | 2 |

## Damage Control prepared Repair Kits

`3 / 3 / 4 / 4 / 5 / 5 / 6 / 6 / 7` at TL1-TL9. The existing TL repair chances and Hull-per-success yields are unchanged.

For the CP135 same-TL study, Damage Control uses a single consistent Hull-only doctrine: if Hull is damaged, a surviving ship with at least 1 TP and 1 kit attempts one Hull repair in the Damage Control phase. The attempt spends 1 TP and 1 kit whether successful or not; success uses the TL profile and queues restoration to the following Turn Refresh. Component repair is not exercised. Armor regeneration remains a separate built-in material capability and may use remaining Damage-Control-window TP after the Hull attempt.
