# Finite In-Combat Armor Regeneration Candidate Delta v0.1

**Checkpoint:** 137  
**Comparison baseline:** native-accepted CP136 same-TL evidence.

CP137 changes no numerical subsystem values. It changes only the tactical endurance of mainline self-healing Armor.

| TL | AI/TP | TP cap/turn | Combat regeneration reserve |
|---:|---:|---:|---:|
| 6 | 1 | 1 | 3 AI |
| 7 | 1 | 1 | 4 AI |
| 8 | 1 | 1 | 5 AI |
| 9 | 1 | 2 | 6 AI |

Reserve is consumed only when AI is actually restored. When the reserve reaches zero, the Armor cannot regenerate further during that engagement. TL6 A_b1 Crystalline remains AP2/AI11 with no regeneration and a zero reserve.

Out-of-combat self-healing is a separate recovery concept: regenerative Armor may recover toward pristine AI between combats, but timing, resources, facilities, and replenishment of tactical regenerative material remain deferred.

The exact CP136 same-TL study is repeated at 5,000 trials/variant with master seed 134001. Reactor TP is intentionally held so the finite-regeneration effect can be isolated before a later power-economy pivot.
