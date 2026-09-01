# Weapon-Family Payload Characteristic-Space Study Architecture v0.2

## Purpose

Checkpoint 115 refines the ammunition/warhead characteristic space exposed by CP114 without promoting production values. The study asks whether Kinetic, Energy, and Missile families can preserve distinct identities across different defensive architectures rather than being tuned toward identical all-target performance.

The design lens is asymmetrical competence, not hard rock-paper-scissors: Kinetic may prefer Armor-heavy targets and struggle more against Shields; Energy may interact efficiently with Shields yet need not be best against Armor; Missiles may provide broader general-purpose reach plus mission-specific warheads while paying finite-ammunition, flight-time, guidance, and PDS costs. This lens is diagnostic and does not itself impose a new numeric rule.

## Authority and non-promotion boundary

- C#/Godot remains the production runtime authority.
- Python remains a research/test consumer.
- CP109 numerical candidates and CP110 Reactor candidates remain unchanged.
- CP114 is the accepted payload-characteristic-space diagnostic baseline.
- CP115 candidate profiles are simulation-only and cannot automatically promote a technology value.
- The research damage model remains `layered_defense_hull_only`; internal critical/subsystem damage is not simulated.

## Study population

The final CP115 population contains **4,064 mirrored variants**:

- **2,272 Missile family-characteristic variants** across TL4, TL5, TL7, and TL9;
- **1,664 Kinetic family-characteristic variants** across TL4-TL9;
- **128 native Energy reference variants** across TL4, TL5, TL7, and TL9.

The population uses 138 underlying exact-fill study builds. Five target classes are legal exact-fill ship packages; three are controlled diagnostic fixtures. Controlled fixtures are excluded from any promotion inference and exist only to expose characteristic-space behavior.

The checked-in authoring run uses 20 trials per variant = **81,280 engagements**. The native substantive run uses 2,000 trials per variant = **8,128,000 engagements**.

## Target fixtures

1. **shield-heavy-legal** — legal Energy defense-specialist package.
2. **shield-isolated-legal** — same package with PDS removed to separate Shield sustain from interception.
3. **shield-overmatch-fixture** — controlled fixture with PDS removed, +6 Shield Capacity, and +1 Base Recharge. This intentionally severe target tests whether anti-Shield specialists have a niche under unusually strong sustain.
4. **balanced-layered-legal** — legal balanced Energy defense.
5. **armor-exposed-legal** — legal exact-fill target with Shield/PDS/Hardener removed and residual Space filled by zero-effect mission/AUX capacity.
6. **pds-heavy-legal** — legal Missile-defense package.
7. **armor-heavy-fixture** — controlled exposed-Armor fixture with +1 Armor Protection and +4 Armor Integrity.
8. **light-fixture** — controlled lightly protected target with no Shield/PDS/Hardener, AP 0, and AI 2; used to expose coverage/accuracy niches.

## Missile GP energetic progression

CP115 treats the old Damage-5 GP packet as a legacy control rather than assuming it remains contemporary at every TL. It samples candidate GP envelopes by energetic generation:

- **Fission-era GP**, studied at TL4/TL5: D6/SP1/AP2, D6/SP2/AP2, D7/SP1/AP2.
- **Fusion-era GP**, studied at TL5/TL7/TL9: D7/SP1/AP2, D7/SP2/AP3, D8/SP2/AP3.
- **Antimatter-era GP**, studied at TL7/TL9: D8/SP2/AP3, D9/SP3/AP3, D10/SP3/AP4 upper anchor.

These are characteristic envelopes, not selected values. The study evaluates the principle that raw packet size must first cross layered-defense thresholds before SPEN/APEN become valuable.

## Missile specialist warheads with contemporary GP

CP114 showed that specialists paired with the obsolete Damage-5 GP packet could change Shield state without creating enough structural progress. CP115 therefore pairs specialists with the contemporary GP candidate rather than the legacy control.

Specialists:

- **shaped/APEN** — D5/SP1/AP3 contextual physical-defense specialist;
- **Shield-pressure** — D3/SP1/AP0 plus +4 Shield-Capacity-only pressure;
- **Shield-recharge suppression** — D4/SP1/AP0 plus bounded suppression 4;
- **Shield-Armor reduction** — D4/SP1/AP0 with Shield Armor reduction 1.

For dual-main Missile attackers, static paired profiles fire specialist in weapon slot 0 and the selected contemporary GP in slot 1. Observer-safe adaptive pairs begin with GP in both slots and switch slot 0 only after Firm-track combat assessment shows repeated Shield interaction with no observed Armor/Hull penetration. The AI never reads exact hidden defense values.

## Kinetic automatic and selectable candidates

### Smart/maneuvering projectile

+5 and +10 ACC envelopes preserve one attack roll per battery and the existing damage packet. If a later native result shows no meaningful cost or downside, this remains a likely automatic compatible upgrade rather than a firing-mode choice.

### Dense penetrator

Two characteristic envelopes test whether APEN can form a genuine Armor specialist rather than a universal upgrade:

- DAM -1 / APEN +1;
- DAM -1 / SPEN -1 / APEN +2.

### Saturation/submunition

CP114's packet-splitting-only model omitted the natural coverage advantage of submunitions. CP115 adds accuracy and keeps one battery = one d100 attack package:

- +10 ACC, 2 x D3 packets, SP1/AP0;
- +15 ACC, 3 x D2 packets, SP0/AP0;
- +20 ACC, 2 x D3 packets, SP0/AP0.

A successful attack package resolves the component packets separately through layered protection. This intentionally makes the mode attractive against lightly protected/evasive targets while potentially poor against flat per-packet Armor/Shield protection.

### Ordered tandem packets

Tandem candidates use one hit roll and then resolve an ordered packet package:

- +5 ACC; D3/SP2/AP0 followed by D3/SP0/AP2;
- +5 ACC; D2/SP2/AP0 followed by D4/SP0/AP3;
- a reversed-order control with the same packet budget.

The reverse control isolates whether layer sequencing itself creates the value. These are candidate package mechanics, not extra battery attacks and not separate ammunition inventories.

## Energy reference

Existing Energy behavior is included as a native reference only. CP115 does not redesign or rebalance Energy. The reference helps determine whether candidate Kinetic/Missile niches exist relative to current same-TL ecology, but no rule requires Energy to be weak against Armor or strong against every Shield package.

## Information boundary

Missile adaptive doctrine uses only observer-safe combat assessment already established by CP113/CP114. A Firm track may expose qualitative Shield interaction, Shield collapse/recovery, Armor contact, or Hull penetration; it does not reveal exact capacity, recharge, AP, AI, hidden component state, or hidden EW arithmetic.

## Interpretation rules

- Do not average away intended family niches.
- A specialist succeeding against its intended target and failing elsewhere can be healthy.
- A candidate that dominates both its niche and general targets may be a strict upgrade and should not become a selectable mode without a real cost.
- Controlled fixtures are characteristic probes, not build-legality or balance-promoting evidence.
- Movement-order artifacts remain a separate architecture problem and should not be compensated for by payload tuning.
- No candidate is promoted from CP115 automatically.

## Validation requirements

Before handoff, CP115 must pass:

1. CPython 3.13 runtime boundary verification;
2. prepackage root hygiene apply/check;
3. the full Python self-test suite;
4. 25 deterministic C#/Python parity fixtures;
5. all 4,064 variants at one trial each;
6. deterministic reconstruction of the checked-in 81,280-engagement authoring evidence;
7. full repository JSON and manifest validation;
8. frozen CP109/CP110 numerical authority, C#/tests, CP114 payload consumer/study, and other unchanged executable surfaces;
9. the native 8,128,000-engagement substantive study for full acceptance.
