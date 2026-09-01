# AUX System Reference Synthesis and Sweep v1

**Checkpoint:** 138  
**Status:** Candidate reference architecture and full-ship integration plan; no numerical promotion.

## Purpose

CP138 covers the entire current installed-support/AUX catalog without pretending that every campaign or TBD component already has a combat mechanic. It separates **reference coverage** from **combat execution**. The primary combat sweep uses only mechanics already executable in the canonical kernel: ECM, ECCM, Kinetic/Energy/AMM PDS, and Shield Hardener. The remaining catalog is mapped to role philosophies, source observations, Space/TP expectations, prerequisites, and future test hooks.

## Reference principles

- Qualitative progression and sparse causal cross-category links are preferred to universal stat inflation (RM-THEME-001/005).
- Specialist counterplay is preferred to universal nerfs or mandatory equipment (RM-THEME-006).
- Engineering consequences are abstracted through Space, Tactical Power, resource endurance, conditions, and explicit traits rather than detailed engineering bookkeeping (RM-THEME-007).
- Power generation, storage, conditioning, and thermal/signature support remain distinct concepts (RM-THEME-012).
- Sensors, EW, communications, datalinks, and stealth form an information ecology (RM-THEME-013).
- Exploration support earns Space by improving endurance or consequential discovery, not by creating a second minigame (RM-THEME-014).

## Reference philosophies

### Combat Generalist
Balanced tactical package covering information control, terminal defense, and bounded shield hardening without installing every specialist.

### Information Control
Sensors, communications, EW, datalink resilience, probes, and signature-management support.

### Missile-Defense Escort
Terminal interception, track resilience, and threat-specific protection for missile-heavy engagements.

### Shield Specialist
Optional shield support and penetration counterplay, re-vetted against the post-CP135 partial-recharge shield model.

### Damage Resilience
Passive protection, emergency continuity, crew survival, and bounded repair support.

### Power Flexibility
Emergency power, sustained generation alternatives, storage, conditioning, and signature/output tradeoffs.

### Expedition / Survey
Scientific discovery, remote surveying, endurance, mission support, and self-sufficiency.

### Industrial / Logistics
Cargo, extraction, processing, fabrication, salvage, and field sustainment.

### Assault / Relief
Boarding, rescue, medical, shuttle, towing, and planetary mission support.

### Munition Endurance
Ammunition reserves and weapon-family endurance without individual feed-path bookkeeping.

## Combat execution boundary

CP138 reference ships are exact-fill cruisers: a core contemporary ship plus a deliberate tactical AUX role, with all remaining Installation Space recorded as mission/support fill. This is not the same as installing every useful AUX system. The role package is the tactical variable; mission/support fill represents the rest of the ship without inventing unsupported combat bonuses.

Primary executable roles: Mission Control, Electronic Attack, Counter-EW, Information Control, AMM Escort, Energy Screen, Kinetic Screen, Shield Guard (TL3+), and Combat Generalist.

Power-supply/storage AUX are deliberately excluded from the primary combat sweep. CP138 measures the demand of credible full ships first; Reactor TP and power AUX are a later controlled phase.

## Shield AUX re-vetting

- **Shield Battery:** reject direct carry-forward of the legacy numeric seed. On the current x2 damage scale it would restore 6 points and can recreate full-reset behavior.
- **Shield Booster:** reject direct carry-forward of the legacy seed; +4 SC on the current scale is too large to assume.
- **Shield Hardener:** retain the existing executable 1-Space, 1-TP sustained, SA2 nonstacking candidate for integration testing.
- **Particle/charged-beam screen:** defer until an attack tag can exercise its specialist niche.
- **Field Stabilizer:** defer until a dedicated high-SPEN specialist lane can distinguish it from the Hardener.

## Interpretation rule

CP138 is diagnostic. It does not target 50/50 matchups and does not automatically promote or rebalance AUX values. A component becoming mandatory across unrelated roles is a warning signal; a specialist being powerful in its intended lane is not inherently a problem. Reactor output is frozen so the sweep can first expose real Tactical Power demand.

