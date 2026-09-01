# CP116 Warhead Role Orthogonality and Generational Scaling — Authoring Report v1

**Evidence status:** bounded authoring evidence only; native substantive study pending.  
**Workload:** 2,976 variants × 25 trials = 74,400 engagements.  
**Damage scope:** layered Shield / Armor / Hull only; internal critical/subsystem damage disabled.  
**Promotion:** none.

## Executive findings

### 1. The user's GP-specialization concern is real

CP115a increased GP DAM and penetration together. CP116's same-DAM controls show that penetration can be responsible for a very large fraction of the apparent late-TL improvement.

At TL9, the balanced Missile attacker using **D9 / SP1 / AP2** pure GP averages about **24% conditional wins** across legal targets in the bounded sample. Holding DAM at 9 but increasing only SPEN to 3 raises that average to about **78%**; increasing only APEN to 3 raises it to about **44%**; bundling SP3/AP3 raises it to about **80%**.

The target-level split is even clearer. Against the TL9 Shield-isolated legal target, the same D9 packet moves from roughly **10%** with SP1/AP2 to **94%** with SP3/AP2. Against the balanced-layered target it moves from about **10%** to **96%**. The SPEN change is therefore not a minor maturity bonus; it fundamentally changes the warhead's role.

This is strong evidence that GP energetic maturation and penetration specialization must not be bundled automatically.

### 2. Raw yield still matters independently

The pure-yield anchors remain important. At TL4, D7/SP1/AP2 outperforms the matched-DAM D6 penetration controls in aggregate. At TL5, D8/SP1/AP2 likewise outperforms the lower D7 controls. This reproduces the CP114 result that packet size has to clear layered integer thresholds before penetration can exploit them.

At TL9, D10/SP1/AP2 recovers substantial performance over D9/SP1/AP2 but remains weak against the strongest Shield/PDS packages. That may be healthy Missile-family behavior: GP remains broadly useful, while specialist warheads exist for unusually strong defenses.

### 3. Generational specialists no longer suffer artificial packet obsolescence

The generation-relative specialist controls dramatically outperform the old static CP115 specialists at high TL. In the bounded balanced-attacker legal-target averages:

| TL | Role | Generational | Static CP115-style |
|---:|---|---:|---:|
| 4 | Armor | 39% | 23% |
| 4 | Shield pressure | 63% | 19% |
| 5 | Armor | 59% | 32% |
| 5 | Shield pressure | 74% | 10% |
| 7 | Armor | 81% | 21% |
| 7 | Shield pressure | 95% | 19% |
| 9 | Armor | 54% | 20% |
| 9 | Shield pressure | 79% | 0% |

The magnitude is not a calibration recommendation. It establishes the architectural point: a TL7/TL9 specialist cannot remain a TL1-sized structural packet and still provide a fair test of the specialist concept.

### 4. Contemporary GP + specialist pairing begins to show real niches

Fixed dual-launcher pairing now produces situations where a specialist helps without being universally superior.

At TL9 in the bounded sample, dual pure D10/SP1/AP2 GP averages about **60%** across legal targets. GP + Shield-pressure rises to roughly **69%**, and GP + recharge-suppression to about **67%**, while Armor and Shield-bypass pairings are lower in aggregate.

The effect is target-dependent. Against the TL9 Shield-overmatch controlled fixture, dual GP is about **59%**, GP + Shield-pressure about **83%**, and GP + recharge-suppression about **83%**. Against Armor-exposed targets, GP remains fully effective and the specialist generally adds no value.

That is much closer to the intended payload relationship than CP115's static specialist tests.

### 5. Kinetic coverage remains a specialist rather than a universal upgrade

Maturing the packet size does not erase the saturation identity. +ACC coverage rounds remain excellent against the lightly protected fixture and remain essentially ineffective against the controlled Armor-heavy target because each small packet pays flat protection separately.

The TL9 two-packet saturation candidate matures from D3 packets to D4 packets, but still records approximately zero Armor-heavy success in the bounded study while retaining strong light-target performance. This is a coherent niche, not a balance failure.

Tandem sequencing remains mechanically meaningful. Reversed packet order changes Armor-heavy results at TL6/TL8/TL9 despite identical total packet budgets, confirming that ordered mixed projectiles are not merely cosmetic.

## GP control summary

Legal-target conditional win averages from the bounded sample:

| TL | Attacker | Pure lower-yield GP | SPEN-only same DAM | APEN-only same DAM | SPEN+APEN same DAM | Higher-yield pure GP |
|---:|---|---:|---:|---:|---:|---:|
| 4 | Balanced | 33% | 41% | 39% | 38% | 52% |
| 4 | Dual-main | 56% | 55% | 55% | 52% | 68% |
| 5 | Balanced | 58% | 64% | 58% | 60% | 69% |
| 5 | Dual-main | 67% | 66% | 71% | 69% | 82% |
| 7 | Balanced | 82% | 87% | 82% | 87% | 86% |
| 7 | Dual-main | 78% | 79% | 79% | 77% | 86% |
| 9 | Balanced | 24% | 78% | 44% | 80% | 61% |
| 9 | Dual-main | 47% | 48% | 53% | 62% | 60% |

The 25-trial authoring sample is too small for promotion decisions. The striking TL9 separation is a hypothesis for the native 2,000-trial run, not a final number.

## Adaptive doctrine

CP116 records 128 adaptive-pair summary rows in authoring, with 20 rows showing at least one natural switch. Unlike CP115a, the generation-relative specialist environment therefore produces some natural observer-safe switching. This is information telemetry only and is not a blocking gate.

## Recommendation pending native results

If the native run reproduces the authoring pattern:

1. Retain the architectural rule that GP energetic maturation does **not** automatically add SPEN/APEN.
2. Treat SPEN/APEN changes as explicit technology/warhead characteristics whose role must be justified separately.
3. Narrow GP yield by generation before calibrating specialist intensity.
4. Calibrate generation-relative specialists against their intended defense niches rather than against all-target averages.
5. Keep Kinetic coverage/tandem concepts as specialist candidates; do not force them to stay equally useful against heavy flat protection.

No numerical profile in CP116 should promote automatically even if it performs strongly.
