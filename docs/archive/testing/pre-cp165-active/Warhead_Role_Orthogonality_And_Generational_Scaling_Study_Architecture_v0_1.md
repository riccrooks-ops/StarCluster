# Warhead Role Orthogonality and Generational Scaling Study Architecture v0.1

**Checkpoint:** 116  
**Accepted baseline:** CP115a  
**Status:** Diagnostic research architecture; no automatic promotion

## Purpose

CP115a validated that Missile general-purpose (GP) payloads must mature energetically and that static specialist packets become artificially obsolete. It also exposed a confound: the CP115 GP candidates increased **DAM, SPEN, and APEN together**. That made it impossible to distinguish energetic maturation from hidden specialist penetration.

CP116 separates those dimensions before any final payload calibration.

## Design questions

1. How much late-TL Missile performance comes from raw energetic yield versus SPEN or APEN?
2. Can a useful GP line remain broad-purpose if energetic yield rises while penetration stays at the existing GP baseline?
3. Do generation-relative specialist warheads retain meaningful niches without becoming universal best-in-slot?
4. Does a contemporary GP + specialist dual-launcher package outperform dual GP only in appropriate defensive contexts?
5. Do Kinetic saturation/tandem concepts remain coherent when their packet budgets mature with the contemporary projectile instead of freezing at TL6-sized packets?

## GP role orthogonality

CP116 treats the existing `SPEN 1 / APEN 2` GP values as a **study baseline**, not a final rule.

For each Missile energetic generation the study includes:

- **Pure-yield GP:** DAM increases; SPEN/APEN stay at the baseline.
- **SPEN-only matched-DAM control:** same DAM as the lower pure-yield candidate; only SPEN rises.
- **APEN-only matched-DAM control:** same DAM; only APEN rises.
- **Bundled-penetration matched-DAM control:** same DAM; both penetration axes rise.
- **Higher-yield pure GP anchor:** another DAM step with baseline SPEN/APEN.

The penetration controls are intentionally diagnostic. They are not preferred GP designs and cannot promote automatically.

## Energetic generations

| Study TL | Generation | Pure-yield lower | Pure-yield anchor | Penetration baseline |
|---:|---|---|---|---|
| 4 | Fission | D6 | D7 | SP1 / AP2 |
| 5 | Fusion | D7 | D8 | SP1 / AP2 |
| 7 | Antimatter | D9 | D10 | SP1 / AP2 |
| 9 | Antimatter | D9 | D10 | SP1 / AP2 |

These are characteristic-space points only. The study does not assert that fission/fusion/antimatter must ultimately map to those exact numbers or TLs.

## Generational specialist model

Specialists are based on the **contemporary energetic generation**, then pay a role cost.

- **Armor specialist:** lower DAM and Shield performance; increased APEN.
- **Shield-bypass specialist:** lower DAM and Armor performance; increased SPEN.
- **Shield-pressure specialist:** lower structural packet and APEN; extra Shield-Capacity damage.
- **Shield-recharge specialist:** lower Armor penetration; bounded recharge suppression after Shield contact.

CP115-style static small specialists are retained as controls so artificial obsolescence is measurable directly.

## Missile doctrine variants

For dual-launcher ships CP116 compares:

- dual pure GP;
- fixed specialist + contemporary GP;
- observer-safe adaptive GP/specialist pairing for Shield-pressure and recharge-suppression roles.

Payload selection still uses generic Missile Flight inventory. The warhead is committed at launch and cannot change in flight.

Adaptive doctrine may use only Firm-track observed combat effects. It never reads exact hostile Shield/Armor values.

## Kinetic refinement

The Kinetic section is secondary but preserves the same generational principle:

- maneuvering/smart projectiles remain automatic +ACC candidates;
- dense penetrators retain a Shield/general-damage opportunity cost;
- saturation rounds keep one battery attack roll, gain +ACC/coverage, and resolve smaller packets;
- TL8/TL9 saturation packet sizes mature from the contemporary Kinetic projectile instead of remaining frozen at the TL6 packet size;
- tandem rounds keep one hit roll and resolve ordered Shield-facing/Armor-facing packets; reversed-order controls isolate sequencing effects.

## Target fixtures

CP116 reuses eight CP115 target fixtures:

- five legal exact-fill packages: Shield-heavy, Shield-isolated, balanced layered, Armor-exposed, and PDS-heavy;
- three controlled diagnostic fixtures: Shield-overmatch, Armor-heavy, and lightly protected.

Controlled fixtures are characteristic probes only and are never production-promotion gates.

## Population

- Missile study TLs: 4, 5, 7, 9.
- Kinetic study TLs: 6, 8, 9.
- Energy native-reference TLs: 4, 5, 7, 9.
- Two attacker archetypes per weapon family where applicable: balanced and dual-main.
- Both movement-order mirrors.
- **2,976 total variants:** 2,176 Missile + 672 Kinetic + 128 Energy reference.
- Authoring: 25 trials/variant = 74,400 engagements.
- Native substantive: 2,000 trials/variant = 5,952,000 engagements.

## Deterministic packet-layer probe

In addition to combat Monte Carlo, CP116 resolves each fixed Missile/Kinetic candidate once against every applicable target fixture at its initial defensive state. The resulting `packet_layer_probe.csv` isolates per-hit Shield Armor, Shield Capacity, Armor, Hull, Shield-specific bonus damage, and recharge-suppression behavior without movement, PDS, target offense, or kill-speed confounds.

This probe is diagnostic only; it does not replace full combat.

## Interpretation guardrails

- Weapon families are intentionally asymmetric. Equal all-defense performance is not a goal.
- GP should be broadly useful under uncertainty, not automatically optimal against every defense.
- A specialist should gain a recognizable niche and pay a meaningful opportunity cost elsewhere.
- High late-TL GP performance caused by matched-DAM SPEN/APEN controls is evidence of **specialization leakage**, not proof that GP should inherit those values.
- Conversely, a pure-yield GP that becomes too weak against ordinary balanced defenses may indicate the final GP baseline needs some explicitly justified penetration maturation; CP116 does not preclude that conclusion.
- Internal critical/subsystem damage remains outside the research consumer.
- No CP116 result changes CP109/CP110 numbers, the Concept, Storyboard TL placement, or production C#/Godot behavior automatically.
