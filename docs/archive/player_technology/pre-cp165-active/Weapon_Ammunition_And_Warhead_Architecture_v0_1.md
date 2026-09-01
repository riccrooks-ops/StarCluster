# Weapon Ammunition and Warhead Architecture v0.1

**Checkpoint:** 113  
**Status:** Architecture candidate; no balance calibration or production promotion

Reconcile Kinetic ammunition and Missile warhead progression with CP108/CP109 technology architecture, CP112 causal diagnostics, the Concept, and preserved reference material before payload numerical calibration.

## Core rules

- Weapon families express tactical flexibility differently: Energy through power/output modes; Kinetic through projectile engineering; Missiles through delivery/guidance plus mission-specific warheads.
- If a compatible ammunition improvement strictly dominates its predecessor and has no meaningful tactical cost, it is an automatic family upgrade rather than a selectable loadout choice.
- A selectable ammunition or warhead mode must be non-dominating: it gains a real capability while sacrificing another meaningful characteristic.
- Compatibility is explicit. Researching a munition does not make every old or alternate weapon family capable of firing it.
- Normal ammunition variants never require per-type magazine bookkeeping. One Kinetic attack spends one Kinetic Ammunition Package; one missile launch spends one Missile Flight.
- Missile warhead choice is committed at launch and cannot change after the flight is launched.
- General-purpose ammunition remains the safe default when target defenses are unknown. Specialist modes become valuable when intelligence or observed combat effects justify them.
- Combat feedback must be observer-safe: show qualitative effects that could be observed, never hidden enemy arithmetic or exact undiscovered component values.
- An anti-shield payload must be tested against shield sustain/recharge, not merely given a higher paper SPEN value. It must create cumulative shield progress without becoming universal best-in-slot.
- Internal-damage payloads remain deferred until the Python research consumer can parity-validate critical/subsystem effects.

## Normal ammunition accounting

| Family | Resource | Subtype inventory? | Rule |
|---|---|---|---|
| Kinetic | Kinetic Ammunition Package | No | 1 per committed main-weapon attack unless a weapon profile explicitly says otherwise |
| Missile | Missile Flight | No | 1 per committed launch unless an explicit salvo/bus mode says otherwise; warhead selected when launch is committed; immutable in flight |
| Exotic / rare | explicit individual counter or named store | Yes, when applicable | Use only when limited availability is itself a strategic/tactical decision. |

## Kinetic progression

| TL | Technology | Expression | Compatibility | Prerequisites | Tactical role | Characteristic space | CP109 relationship |
|---:|---|---|---|---|---|---|---|
| 1 | Contemporary general-purpose projectile package | automatic_baseline | legacy_em_accelerator; smart_munition_interface; field_relativistic_accelerator | — | Balanced contemporary projectile/manufacturing baseline. Fragmentation/fuzing detail remains abstract unless a real target/mechanic makes it a decision. | baseline Damage/SPEN/APEN; munition hazard trait where explosive packages exist | Current TL1 Kinetic profile remains the numerical placeholder. |
| 2 | Improved penetrator/projectile materials | automatic_upgrade | legacy_em_accelerator; smart_munition_interface; field_relativistic_accelerator | — | Strict material/manufacturing maturation. If no meaningful cost exists, older standard projectile does not remain a UI choice. | APEN/material efficiency improvement; no mandatory launcher change | Supports the current TL2 APEN1 candidate without creating a separate ammo selector. |
| 4 | Maneuvering / programmable smart projectile | automatic_compatible_upgrade | smart_munition_interface | Computing / Fire Control TL4 | Terminal correction and programmable fuzing improve a compatible accelerator. Because the old CP109 version had only benefits, it should not be a separate selectable loadout. | accuracy/terminal-correction improvement; possible Approximate-Track/volume-fire permission if later calibrated; guidance/interface resilience | CP109 branch kinetic-smart-projectile selectable numeric candidate is suspended pending calibration of this automatic expression. |
| 5 | Dense / graded penetrator package | selectable_normal | smart_munition_interface; field_relativistic_accelerator | — | Armor-focused projectile that must sacrifice enough general damage or shield performance to remain a real choice. | APEN +1 to +2 relative to contemporary general package; DAM -1 and/or SPEN -1; no free accuracy bonus | The CP109 -1 DAM / +1 APEN concept remains a useful candidate point, not a promoted value. |
| 6 | Micro-submunition / saturation package | selectable_normal | smart_munition_interface | — | Trades per-packet penetration/effect for multiple smaller packets or a broader effective damage volume. | 2-3 bounded packets; lower DAM per packet; lower or unchanged APEN/SPEN per packet; possible small-target/volume-fire niche when such mechanics are supported | The CP109 2 x DAM3 point remains an uncalibrated example, not an adopted packet profile. |
| 8 | Exotic dense-matter projectile | exotic_individually_tracked_if_adopted | field_relativistic_accelerator; exotic_payload_interface | — | Preserved weird-science projectile. If adopted, scarcity/handling is itself gameplay and therefore may justify per-shot tracking. | extreme penetration; handling/compatibility limits; resource scarcity; counterplay | No active normal-player numerical profile. |

## Missile warhead progression

| TL | Warhead | Expression | Compatibility | Prerequisites | Tactical role | Characteristic space | CP109 relationship |
|---:|---|---|---|---|---|---|---|
| 1 | Conventional general-purpose warhead | automatic_baseline | conventional_flight_body; high_energy_payload_bus; antimatter_hardened_payload_bus | — | Balanced structural payload; safest choice when target defenses are not known. | balanced DAM/SPEN/APEN | Current D5/SP1/AP2 remains the simulated GP placeholder until payload calibration. |
| 3 | Shaped / advanced penetrator warhead | selectable_normal | conventional_flight_body; high_energy_payload_bus; antimatter_hardened_payload_bus | — | Armor specialist. Must give up shield effectiveness and/or raw structural damage so it does not strictly dominate GP. | APEN +1 to +2; DAM -1 and/or SPEN -1; no free seeker benefit | CP109 D5/SP1/AP3 is suspended because it strictly dominates GP on APEN with no tradeoff. |
| 4 | Nuclear directed-pulse / shield-disruption warhead | selectable_normal | high_energy_payload_bus; antimatter_hardened_payload_bus | — | Shield specialist derived from directed high-energy payload engineering. It must create cumulative shield pressure while sacrificing armor/Hull performance. | extra shield-only Capacity damage; temporary reduction/ignore of Shield Armor for this hit; bounded next-recharge suppression; lower APEN and/or lower post-shield structural damage | CP109 nuclear-shaped raw-damage candidate is suspended; CP113 reframes the TL4 specialist around anti-shield role rather than universal payload escalation. |
| 5 | Fusion microcharge general-purpose warhead | automatic_compatible_upgrade | high_energy_payload_bus; antimatter_hardened_payload_bus | Power TL2 | High-energy GP maturation. Because an otherwise superior fusion payload would be an obvious choice, it should replace the older GP package rather than create loadout clutter. | bounded increase in general-purpose damage and/or penetration; strategic resupply/resource cost may differ later; no per-type tactical inventory | CP109 D8/SP2/AP3 is not retained as an active numerical candidate; exact GP improvement requires calibration. |
| 6 | Radiation / electronics-disruption warhead | deferred_specialist | high_energy_payload_bus; antimatter_hardened_payload_bus | — | Specialist anti-crew/electronics/internal-effect payload. Do not use it as a substitute anti-shield mechanic while internal damage/crew consequences are absent. | crew/electronics effect after appropriate penetration; hardening counterplay; lower ordinary structural effect | Remains deferred until internal critical/subsystem research consumer exists. |
| 7 | Antimatter general-purpose warhead | automatic_compatible_upgrade | antimatter_hardened_payload_bus | Power TL5 | Antimatter-era GP maturation. Tactical subtype bookkeeping remains abstract; containment/resource consequences belong to compatibility, hazards, resupply and campaign economy. | large but bounded GP effect increase; containment/signature/hazard traits; strategic resource burden | CP109 D10/SP3/AP4 branch value is suspended; exact contemporary GP stats require calibration against defenses. |
| 9 | Matter-conversion warhead | exotic_individually_tracked_if_adopted | exotic_payload_interface | Power TL9 | Rule-breaking pinnacle payload is not ordinary generic-ammunition progression. If ever adopted, rarity/scarcity and counterplay justify explicit shot counts. | bounded conversion effect; strict scarcity; special defenses/counters; campaign consequence | No active normal-player numerical profile. |

## Observer-safe combat assessment

Give the player and AI enough legitimate feedback to recognize ineffective attacks without revealing exact hidden defense statistics.

**Firm-track feedback:**
- active shield presence may be identified once energized or conspicuously struck
- shield absorption observed
- shield collapse observed
- armor contact observed
- hull penetration confirmed
- no observed armor/hull penetration after a resolved hit
- on a later Firm observation, whether a previously collapsed/damaged shield is active again may be observed

**Approximate-track boundary:** Limit to conspicuous effects and uncertain impact assessment; do not expose layer-by-layer resolution from an Approximate contact by default.

**Never reveal by default:**
- exact hostile Shield Capacity
- exact Shield Armor
- exact recharge value
- exact Armor Protection/Integrity
- hidden component stats
- hidden ECM/ECCM arithmetic
- future random outcomes

**AI parity:** AI receives only the same derived assessment flags and remembered observations that the player could possess; it may not read authoritative hidden defender state.

**TL9 example:** Repeated Damage-5 missile hits that visibly flare/restore the shield but never show armor or Hull penetration can legitimately teach the commander that the current payload is not creating cumulative progress, without revealing the 1+3+1 hidden arithmetic.

## Anti-shield calibration requirements

- Test shield specialist, balanced defense, and no-shield controls at each relevant TL.
- Test with PDS present and removed so interception does not mask payload effectiveness.
- Measure Shield Armor prevented, Shield Capacity removed, recharge opportunities/restoration, armor contact, Hull penetration, magazine exhaustion, and unresolved rate.
- A shield-specialist payload should create materially more cumulative shield progress than GP against shield-heavy targets, but should lose materially to GP/penetrator against unshielded or armor-heavy targets.
- Do not require every specialist missile to defeat equal-TL maximum defense; require a useful niche and a credible route to progress under finite ammunition.
- Keep movement-order cliff lanes separate from payload balance inference until their sequencing/geometry issue is understood.

## Suspended CP109 payload candidates

| ID | Reason |
|---|---|
| kinetic-smart-projectile | Strictly beneficial selectable mode would be a non-choice; re-expressed as automatic compatible upgrade. |
| missile-shaped-warhead | D5/SP1/AP3 strictly improves APEN over GP with no cost; specialist must trade something. |
| missile-nuclear-shaped | Raw D7/SP2/AP3 universal escalation obscures the more useful anti-shield specialist role. |
| missile-fusion-warhead | If superior high-energy GP, it should automatically replace earlier GP on compatible flights; exact stats need calibration. |
| missile-antimatter-warhead | If superior high-energy GP, it should automatically replace earlier GP on compatible flights; exact stats need calibration. |

## Reference synthesis

| Source | Signal retained |
|---|---|
| Concept v0.7j | Existing generic Ammunition Package / Missile Flight accounting, shared magazines, payload-variant expression, family-specific resource identity, and observer-safe sensor presentation already support this architecture. |
| Technology Family Storyboard v1.2 | Kinetic ammunition and Missile warheads already exist as independent lineages; CP113 mainly reconciles expression and tactical choice. |
| CP112 native diagnostics | Late Missile Damage-5 packets can be completely absorbed by Shield Armor + renewable Shield Capacity + passive Armor, proving payload interaction is a material calibration axis. |
| Spacedock reference-mining corpus | Kinetic projectile sophistication is a major progression axis; missile delivery, guidance and payload can progress independently; proximity/submunitions and directed nuclear effects provide non-scalar specialization inspiration. |
| GURPS Space 4e | Pattern-level support that missile bodies may carry qualitatively different payloads; no mechanics copied. |
| Master of Orion II manual | Pattern-level support for weapon specialization/modification with explicit tradeoffs; no names, exact mechanics or balance values copied. |
| Star Fleet Battles rules | Pattern-level support for finite ammunition, alternative ammunition, seeking-weapon modularity and specialized payload/guidance roles; no detailed rules copied. |

## Next pass

Implement these payload expressions as simulation-only candidate modes and run controlled ammunition/warhead characteristic sweeps before changing Shields, standard Missile GP numbers, Kinetic profiles, or the production runtime.

