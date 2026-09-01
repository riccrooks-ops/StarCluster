# CP118 Simplified Weapon Progression Report v1

**Evidence status:** bounded authoring evidence only; native substantive validation pending  
**Authoring workload:** 1,824 variants x 50 trials = 91,200 engagements  
**Automatic promotion:** none

## Executive findings

CP118's bounded pass supports the CP117 simplification direction. GP Missile yield remains the major progression lever, a simple Swarmer can plausibly exist much earlier than TL5, and automatic Kinetic accuracy is a useful maturation axis without requiring an ammunition-selection UI.

The study also shows why Swarmer should be allowed to have an **era** rather than being forced to remain competitive through TL9. Small submunition packets are naturally punished as Shield/Armor flat protection rises. A mature two-packet Swarmer can regain relevance around TL6-TL7 through better terminal coverage, higher submunition yield, and bounded PDS saturation, then fade again at TL8-TL9 without requiring additional late-game rules.

## Missile GP yield

All GP yield candidates retain SPEN 1 / APEN 2 in this study.

Selected balanced-target authoring rates averaged across balanced and dual-main attackers:

| TL | Current D5 | Lower contemporary candidate | Higher contemporary candidate |
|---:|---:|---:|---:|
| 3 | 78% | D6: 93% | - |
| 4 | 38% | D6: 70% | - |
| 5 | 58% | Fusion D6: 81% | Fusion D7: 93% |
| 6 | 43% | Fusion D6: 81% | Fusion D7: 95% |
| 7 | 8% | Antimatter D7: 85% | Antimatter D8: 92% |
| 8* | 2% | Antimatter D7: 32% | Antimatter D8: 63% |
| 9* | 0% | Antimatter D7: 7% | Antimatter D8: 20% |

`*` TL8-TL9 are endpoint/stress evidence, not normal calibration anchors.

The authoring pass does **not** select D6/D7/D8 as final values. It confirms that increasing yield without penetration creep can restore Missile relevance through the likely campaign range while leaving strong Shield/PDS packages meaningful.

## Swarmer introduction and maturation

### Early branch

At TL1, the simple two-packet Swarmer is already viable. The PDS-resistant early candidate is approximately even with GP against the PDS-heavy legal target (~46% vs ~46%) and approximately even against the Shield-heavy legal target (~89% vs ~89%), while its smaller packets improve performance against exposed Armor through higher terminal connection probability.

At TL2 the early Swarmer remains usable but is generally weaker than GP. By TL3, the same frozen early packet largely collapses against stronger layered defenses. This is useful evidence that **early introduction is plausible but static Swarmer stats should not be evergreen**.

### Mid and mature branch

The two-packet mid candidate (2 x D3, +10 terminal guidance, -10 pp PDS interception) recovers a niche at TL4: about 55% on balanced targets versus ~38% for current GP. It falls behind again at TL5 as defenses progress.

The mature two-packet candidate (2 x D4, +15 terminal guidance, -15 pp PDS interception) is strongly relevant at TL6 and remains useful at TL7:

| Target | TL6 mature Swarmer | TL6 Fusion D7 GP | TL7 mature Swarmer | TL7 Antimatter D7 GP |
|---|---:|---:|---:|---:|
| Balanced | ~97% | ~95% | ~71% | ~85% |
| PDS-heavy | ~33% | ~33% | ~23% | ~48% |
| Shield-heavy | ~25% | ~11% | ~12% | ~8% |
| Armor-exposed | ~100% | ~100% | ~100% | ~100% |

The mature Swarmer produces much better terminal survival than GP against PDS. In the TL6 PDS-heavy lane, its bounded saturation candidate lowers the observed interception-per-attempt rate from roughly 40% to roughly 25% and raises Missile hits per launch from roughly 0.37-0.38 to roughly 0.59.

By TL8-TL9 the same mature Swarmer fades sharply. CP118 treats that as potentially healthy lifecycle behavior rather than a defect requiring another late-game mechanic.

The three-packet D2 candidate is usually too weak against flat protection even though it creates more terminal hits. This favors a simple two-packet Swarmer expression over a "more submunitions is always better" progression.

## Kinetic automatic progression

The Kinetic candidates are single-axis diagnostic controls, not selectable ammunition.

At TL4, averaged across the four legal targets:

- current projectile: ~47% mean conditional win, ~64% direct hit rate;
- +5 ACC: ~54%, ~69% hit rate;
- +10 ACC: ~61%, ~75% hit rate;
- +1 Damage: ~71%, ~65% hit rate;
- +1 APEN: ~46%, ~64% hit rate.

At TL5-TL7, +ACC continues to increase actual hit frequency in a predictable way. +Damage often produces a larger raw combat swing, including against Shields, while +APEN is more target-dependent. This is an important family-identity signal: **accuracy is the cleaner smart-munition maturation axis**, whereas repeatedly adding raw Damage can erase Kinetic's intended relative difficulty against Shields much faster.

The bounded pass does not set final +ACC increments. It supports testing automatic smart-projectile accuracy as the primary projectile maturation axis while allowing accelerator technology itself to determine when raw Damage/APEN should change.

## KISS conclusions from authoring

1. A Swarmer need not be a high-TL technology. TL1-TL2 introduction is mechanically plausible.
2. Swarmer can mature through only three understandable characteristics: terminal coverage, internal packet strength/count, and bounded PDS saturation.
3. Swarmer does not need to remain competitive at TL8-TL9. Natural obsolescence or later replacement is acceptable.
4. Two larger submunition packets currently look healthier than three very small packets.
5. GP Missile maturation can be investigated with Damage alone; CP118 deliberately adds no GP SPEN/APEN.
6. Kinetic smart-projectile accuracy is useful and can remain automatic. The study does not justify reopening a normal Kinetic ammunition menu.
7. TL8-TL9 remain stress checks. No CP118 design choice should be complicated solely to rescue those endpoint rows.

## Native-validation question

The 3.648-million-engagement native pass should confirm whether these qualitative relationships survive sampling noise. No candidate will be automatically promoted even if it leads its authoring cohort.
