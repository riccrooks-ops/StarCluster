# Payload Characteristic-Space Study Architecture v0.1

Checkpoint 114 turns the CP113 ammunition/warhead architecture into a simulation-only research consumer. It does not change CP109 numerical technology candidates, CP110 Reactor candidates, the C#/Godot production runtime, or Concept v0.7k.

## Purpose

The study answers three questions before any weapon/defense retuning:

1. Do selectable Missile warheads create genuine mission-specific niches against Shields and Armor, or do they merely become weaker/stronger GP missiles?
2. Does the normal GP Missile warhead need technological maturation at Fusion/Antimatter milestones to keep pace with the layered defense ladder?
3. Do proposed selectable Kinetic ammunition modes create contextual tradeoffs, or should they instead be automatic compatible upgrades?

## Information and inventory boundary

- Normal Kinetic and Missile variants draw from their broad generic magazines. No pre-battle subtype inventory is modeled.
- A Missile Flight commits its warhead at launch.
- Adaptive doctrine begins with GP and may switch only from observer-side combat assessment available under Firm track: repeated observed Shield absorption with no observed Armor/Hull damage/penetration. It never reads exact Shield Capacity, Shield Armor, recharge rate, Armor values, hidden component state, or hidden EW arithmetic.
- If a later Firm-track impact reaches Armor/Hull without a Shield effect, adaptive doctrine may return to GP.
- Rare/exotic individually counted ammunition remains outside CP114.

## Missile characteristic families

GP-current is the exact baseline-control path. Specialist profiles include:

- shaped/penetrator candidates: trade raw damage and/or Shield Penetration for Armor Penetration;
- Shield-pressure candidates: add Shield-Capacity-only damage with no structural spillover;
- Shield-Armor reduction candidate: reduces Shield Armor only for that hit and pays a structural-performance cost;
- recharge-suppression candidates: reduce the next legal Shield recharge by a bounded nonstacking amount and pay a structural-performance cost;
- observer-safe adaptive variants of the specialist concepts;
- dual-launcher mixed-salvo variants that combine a specialist flight and a GP flight in the same launch cycle, with reversed sequencing controls;
- Fusion-era and Antimatter-era GP maturation envelopes, treated only as characteristic-space candidates rather than promoted values.

The study intentionally tests both Energy-defense and Missile-defense target packages, each with full defense, no-PDS, no-Hardener, and no-Shield ablations. This prevents a target's offensive family from becoming the only interpretation lane.

## Kinetic characteristic families

- GP-current is the control.
- TL4/5 smart-projectile candidate: +5 accuracy as a possible automatic compatible upgrade.
- Dense/graded penetrator candidates: trade damage and/or SPEN for APEN.
- TL6/7 saturation candidates: split one attack into two or three smaller packets. Every packet independently encounters protection layers; this is deliberately tested because per-packet thresholds may make saturation excellent in one role and ineffective against heavy protection.

Selectable Kinetic ammunition must demonstrate a real tradeoff. A profile that is broadly superior to GP should be treated as evidence for automatic maturation rather than a permanent firing-mode menu item.

## Study population

The frozen CP114 definition contains 3,184 exact-fill mirrored variants:

- 2,720 Missile payload/warhead variants;
- 464 Kinetic ammunition variants.

All payload test ships use the accepted CP111/CP112 exact-fill policy. Residual not-yet-numerical mission/AUX capacity remains zero-tactical-effect accounting rather than empty Space.

The normal native workload is 2,000 trials per variant, or 6,368,000 engagements. The checked-in authoring evidence uses 20 trials per variant (63,680 engagements) only to validate mechanism behavior and identify characteristic-space signals before native execution.

## Damage and mechanic scope

The research consumer remains `layered_defense_hull_only`: Shields, Armor, and Hull are simulated; internal critical/subsystem damage is not. PDS, missile flight timing, movement/fuel/map constraints, Sensor/EW, Tactical Power, Shield recharge/Hardener, Reactor overload, and existing CP111 instrumentation remain active.

Payload-specific telemetry adds specialist/GP launches, payload switches, Shield-only bonus damage, recharge suppression, and observer-side assessment flags. CP114 does not alter ordinary GP behavior; a deterministic regression test requires the GP-control payload path to reproduce the existing ecology trial exactly for the same build and seed.

## Interpretation policy

CP114 has no balance target and no automatic promotion. Win rate is contextual evidence; layer-by-layer damage, unresolved rate, target ablations, payload sequencing, and observer-limited doctrine are equally important. No CP109/CP110 value may change merely because a CP114 candidate performs well or poorly.

A later checkpoint may promote or revise a candidate only after native results establish a useful niche and the design is reconciled back into the technology matrix and production roadmap.
