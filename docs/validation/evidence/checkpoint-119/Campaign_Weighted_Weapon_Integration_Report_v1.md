# CP119 Campaign-Weighted Weapon Integration Report v1

**Evidence status:** bounded authoring evidence only; native substantive validation pending  
**Authoring workload:** 1,152 variants x 50 trials = 57,600 engagements  
**Automatic promotion:** none

## Executive findings

CP119 returns the small CP118 working candidate set to a shared same-TL ecology with native Energy reference builds. The 50-trial authoring pass is intentionally too small for promotion, but it is sufficient to validate routing, telemetry, and broad integration behavior before the 2.304-million-engagement native run.

The strongest bounded signal is that the simplified Kinetic candidate is moderate while the Missile yield candidates are much more consequential. The +5 ACC Kinetic step improves the same-TL ecology by roughly 8 percentage points at TL4-TL6. The D6/D7 GP Missile steps improve their same-TL ecology by roughly 16-28 points over the current D5 packet, which makes them the principal calibration watch item rather than a reason to add new mechanics.

The Swarmer preserves a clear lifecycle. It is not a universal replacement for GP: the early TL2-TL3 packet is target-sensitive, the TL4 mid packet recovers relevance, TL5 defenses push it back again, and the mature TL6-TL7 2 x D4 package becomes strongly relevant while retaining the intended PDS-saturation identity.

## Campaign-weighted ecology

Average conditional win rate across the six legal target packages and balanced/dual-main attacker archetypes:

| TL | Energy native | Kinetic reference | Kinetic +5 ACC | Missile current GP | Working GP | Swarmer |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 36.9% | 77.6% | - | 70.2% | - | - |
| 2 | 58.4% | 67.3% | - | 69.0% | - | 57.7% |
| 3 | 41.3% | 46.5% | - | 61.4% | 77.3% | 28.1% |
| 4 | 66.4% | 52.1% | 59.7% | 40.1% | 56.5% | 54.3% |
| 5 | 60.6% | 44.3% | 53.2% | 44.9% | 70.6% | 33.8% |
| 6 | 61.5% | 41.6% | 50.1% | 44.2% | 72.5% | 74.0% |
| 7 | 56.4% | 50.3% | 54.9% | 27.2% | 76.1% | 59.3% |

TL1-TL6 are the primary inference range. TL7 is shown because it is the advanced-validation band; TL8-TL9 are endpoint/stress evidence and should not drive whole-game complexity.

## Kinetic working candidate

- TL4: +5 ACC changes the ecology by about **+7.7 pp** versus the same-TL reference projectile.
- TL5: +5 ACC changes the ecology by about **+8.8 pp** versus the same-TL reference projectile.
- TL6: +5 ACC changes the ecology by about **+8.5 pp** versus the same-TL reference projectile.
- TL7: +5 ACC changes the ecology by about **+4.6 pp** versus the same-TL reference projectile.

The bounded result is deliberately modest. The candidate changes hit probability without changing packet strength or penetration, which makes it a clean expression of smart/maneuvering projectile maturation. CP119 does not test a selectable Kinetic ammunition mode.

## GP Missile yield

- TL3: `missile-working-fission-d6` changes the ecology by about **+16.0 pp** versus current D5 GP.
- TL4: `missile-working-fission-d6` changes the ecology by about **+16.4 pp** versus current D5 GP.
- TL5: `missile-working-fusion-d7` changes the ecology by about **+25.7 pp** versus current D5 GP.
- TL6: `missile-working-fusion-d7` changes the ecology by about **+28.3 pp** versus current D5 GP.
- TL7: `missile-working-antimatter-d8` changes the ecology by about **+48.9 pp** versus current D5 GP.

These are large candidate effects, especially the TL5-TL6 D7 step. They are the main native-review watch item. CP119 therefore treats D5 -> D6 -> D7 -> D8 as a leading *shape* to test, not as a promoted table. The study adds no GP SPEN/APEN progression.

## Swarmer lifecycle and PDS saturation

- TL2: `swarmer-early-tl2` changes the ecology by about **-11.3 pp** versus current GP.
- TL3: `swarmer-early-tl2` changes the ecology by about **-33.2 pp** versus current GP.
- TL4: `swarmer-mid` changes the ecology by about **+14.2 pp** versus current GP.
- TL5: `swarmer-mid` changes the ecology by about **-11.1 pp** versus current GP.
- TL6: `swarmer-mature` changes the ecology by about **+29.8 pp** versus current GP.
- TL7: `swarmer-mature` changes the ecology by about **+32.1 pp** versus current GP.

The sign changes are useful rather than alarming. They show that a Swarmer can have an era and target niche instead of being an evergreen best-in-slot Missile. The branch remains mechanically simple: two packets, one terminal roll, and a bounded reduction to the existing PDS interception chance.

Selected deterministic PDS probe values:

| TL | GP PDS chance | Swarmer PDS chance | Swarmer packets | Packet damage |
|---:|---:|---:|---:|---:|
| 2 | 32% | 22% | 2 | 2 |
| 4 | 35% | 25% | 2 | 3 |
| 5 | 39% | 29% | 2 | 3 |
| 6 | 39% | 24% | 2 | 4 |
| 7 | 46% | 31% | 2 | 4 |

## Movement-order caution

The 50-trial authoring pass reports a maximum working-profile movement-order swing of about **38.4 pp**. That is not a balance estimate at this sample size. The known movement/sequencing issue remains a separate architecture problem; CP119 does not use weapon statistics to compensate for it.

## Authoring conclusion

The authoring pass supports proceeding to native integration rather than adding mechanics. If native evidence reproduces the same shape, the next design decision should be whether the D6/D7 GP yield milestones are too aggressive in the shared ecology, while the +5 Kinetic ACC step and TL2+ two-packet Swarmer can be judged primarily on role clarity and lifecycle.

No CP119 authoring outcome is a numerical promotion.
