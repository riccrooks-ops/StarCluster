# Weapon Family Simplification and Swarmer Architecture Report v1

**Checkpoint:** 117  
**Accepted evidence baseline:** Checkpoint 116 native results  
**Status:** architecture consolidation candidate; no numerical promotion; zero new Monte Carlo trials

## Executive finding

CP114-CP116 were useful because they exposed which weapon dimensions materially affect combat. They also demonstrated the danger of converting every useful diagnostic axis into a player-facing ammunition or warhead selector. CP117 therefore compresses the weapon model back toward KISS.

The active baseline becomes:

- **Energy:** tactical flexibility comes from a small number of meaningful power/output modes.
- **Kinetic:** one normal ammunition pool; compatible projectile materials, penetrator engineering, programmable behavior, and smart/maneuvering correction auto-mature when they are strict improvements. Normal play does not require a Kinetic ammunition selector.
- **Missile:** normal GP payloads mature primarily by energetic yield at major technology milestones. Distinct Missile Flight families may branch when the whole delivery package behaves differently.
- **Swarmer Missile:** retained as the principal near-term Missile family branch because it has a simple, intuitive whole-Flight identity: more terminal coverage and bounded PDS saturation in exchange for lower concentrated packet strength.

## Why simplify now

CP116 validated a strong conceptual point: raw energetic yield, SPEN, APEN, Shield pressure, recharge suppression, packet ordering, and coverage can all matter. That does not mean they all deserve normal UI controls. Keeping them all would create a combinatorial loadout system, encourage target-stat optimization, and make rare TL8-TL9 breakpoints drive the entire weapon architecture.

CP117 instead preserves the experimental results as evidence and future optional concepts while promoting only the smallest set of mechanics needed to retain family identity.

## Kinetic consolidation

The normal Kinetic line should become easier to understand, not more menu-heavy, as it matures. Smart projectiles and better penetrator/material engineering are therefore automatic compatible improvements unless a future branch carries a genuine cost worth exposing.

The CP114-CP116 dense-penetrator, Kinetic saturation, tandem, and reversed-packet profiles remain useful research probes. They are removed from the active baseline rather than deleted from project history. A genuinely different projectile concept should generally become a distinct installed Kinetic family rather than another per-shot ammunition toggle.

## Missile GP energetic progression

The normal GP Missile payload uses the broad generic Missile store and automatically matures at major energetic milestones. CP117 preserves the working milestones for later calibration:

- TL1: mature conventional/fission-era GP baseline;
- TL5: Fusion microcharge GP candidate milestone, with the existing Power relationship;
- TL7: Antimatter GP candidate milestone, with the existing Power relationship;
- TL8-TL9: endpoint validation; no requirement to invent another ordinary payload family merely to populate the ladder.

Higher energetic generation primarily raises usable yield/DAM. It does not automatically grant more SPEN/APEN. Exact GP DAM and the permanent baseline penetration remain calibration questions.

## Swarmer Missile

Swarmer is a distinct Missile Flight family, provisionally centered on TL5-TL7. It is not a normal warhead selection and not Kinetic submunition ammunition.

The later calibration contract is intentionally compact:

- one Flight counter;
- one generic Missile-ammunition expenditure;
- one terminal attack roll;
- ordinary Firm-terminal requirement unless an explicit later technology changes it;
- a small bounded number of lower-strength internal packets after a successful terminal attack;
- a bounded PDS-saturation trait candidate representing many terminal vehicles/submunitions;
- no additional PDS reaction windows or natural-critical rolls;
- lower concentrated packet strength, making heavy flat protection a natural weakness.

The only near-term numerical axes worth sweeping are terminal coverage/accuracy, internal packet strength/count, and the size of the PDS-saturation effect.

## Specialist concepts retained, not normalized

Shaped/APEN, directed-pulse/shield-disruption, radiation/electronics, antimatter-catalyzed bridge, matter-conversion, and similar payload concepts remain in the Storyboard/Idea Register. CP117 does not assume a normal standing warhead menu. A specialist may return when play demonstrates a clear mission that cannot be expressed cleanly by the GP line or a distinct Missile family.

Rare/Exotic ammunition may still be individually tracked when scarcity itself is gameplay.

## Calibration weighting

The next numerical pass should not weight the technology ladder uniformly:

| Priority | TLs | Interpretation |
|---|---|---|
| Primary campaign | TL1-TL6 | Main balance/calibration evidence |
| Advanced game | TL7 | Confirm mature family identity and viability |
| Endpoint/stress | TL8-TL9 | Catch runaway thresholds, dead systems, or implementation defects without redesigning the whole game around rare pinnacle cases |

This does not permit TL8-TL9 to be broken. It prevents those endpoint cases from generating unnecessary mechanics across all earlier play.

## Frozen boundaries

CP117 makes no production C#/Godot change, no CP109 numerical matrix change, no CP110 Reactor change, and no Python combat-consumer change. It adds no new Monte Carlo study. Accepted CP116 native evidence remains the final broad payload characteristic-space dataset for this consolidation phase.

## Recommended next pass

After native acceptance, run a deliberately small TL1-TL7 calibration study focused on:

1. narrowing GP Missile yield at the TL1, Fusion, and Antimatter milestones;
2. a few Swarmer candidates spanning coverage/accuracy, lower packet strength, and bounded PDS saturation;
3. ordinary Kinetic profiles with automatic smart-projectile accuracy maturation, not ammunition permutations;
4. representative Shield-heavy, Armor-heavy, balanced, and PDS-heavy targets;
5. TL8-TL9 endpoint sanity checks only.

No value should promote automatically from that study.
