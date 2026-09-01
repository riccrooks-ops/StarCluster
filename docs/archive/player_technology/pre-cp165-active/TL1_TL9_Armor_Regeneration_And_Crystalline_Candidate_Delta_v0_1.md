# TL1-TL9 Armor Regeneration and Crystalline Candidate Delta v0.1

**Checkpoint:** 136  
**Comparison baseline:** accepted CP135 same-TL evidence.

CP136 changes only mainline Armor and the TL6 A_b1 Crystalline seed. Shield recharge, Hull-only Damage Control, weapons, Hull, Reactor, PDS, Space, range/track modifiers, reference builds, master seed, and study geometry are held from CP135.

## Mainline Armor

| TL | AP | AI | Regen AI/TP | Regen TP cap |
|---:|---:|---:|---:|---:|
| 1 | 0 | 6 | 0 | 0 |
| 2 | 0 | 8 | 0 | 0 |
| 3 | 1 | 9 | 0 | 0 |
| 4 | 1 | 10 | 0 | 0 |
| 5 | 2 | 10 | 0 | 0 |
| 6 | 1 | 9 | 1 | 1 |
| 7 | 1 | 10 | 1 | 1 |
| 8 | 2 | 11 | 1 | 1 |
| 9 | 3 | 12 | 1 | 2 |

The intended identity is steady rather than rapid Armor recovery: TL6-TL8 restore at most 1 AI/turn through tactical regeneration, while TL9 can spend at most 2 TP to restore 2 AI/turn. There is no free Armor regeneration.

## A_b1 Crystalline Composite Armor

TL6 only: **AP2 / AI11 / no regeneration**. It remains a passive alternative to TL6 mainline AP1/AI9 with 1 AI/TP, cap 1. Later-TL Crystalline progression remains TBD.

## Study boundary

Rerun the exact CP135 196-context / 392-variant same-TL diagnostic at 5,000 trials/variant with master seed 134001. TL6 still crosses mainline/mainline, mainline/A_b1, A_b1/mainline, and A_b1/A_b1. Missile-bearing lanes retain PDS off/on. No 50/50 target and no automatic promotion.
