# CP113 Weapon Ammunition / Warhead Reference Sweep

**Checkpoint:** 113  
**Status:** design synthesis; no calibration or production promotion

## Why this sweep was necessary

CP112 showed that the current late-TL Missile consumer can launch and hit while producing no Hull penetration because a flat Damage-5 packet can be completely absorbed by layered Shield Armor, renewable Shield Capacity, and passive Armor. At the same time, the qualitative technology foundation already contains independent Kinetic-ammunition and Missile-warhead progressions that were not expressed by the research consumer. CP113 therefore reviews the existing architecture before changing Shield or weapon numbers.

## Existing Star Cluster authority

- Concept 10.17 already abstracts one projectile attack as one Ammunition Package and one missile launch as one Missile Flight, with broad magazines rather than literal rounds.
- Concept weapon-family identity already distinguishes ammunition-fed Kinetics/Missiles from power-mode Energy weapons.
- The Storyboard already separates Kinetic launcher technology from projectile packages, and Missile delivery/guidance from warhead effects.
- CP109 created raw numerical branch placeholders for smart Kinetics and several Missile warheads, but those values were never calibrated or promoted.
- CP112 demonstrated that payload/layer interaction is now a material missing axis, so calibrating the flat GP missile first would risk tuning an incomplete weapon model.

## Reference-material synthesis

**Spacedock reference mining.** The corpus repeatedly treats projectile construction/ammunition as a major Kinetic progression axis and treats a missile as a small vehicle whose propulsion, guidance, seeker, payload, power and countermeasures can mature separately. It also preserves proximity/submunition concepts and directed nuclear terminal effects. This strongly supports asymmetric family mechanics rather than giving every weapon a generic Low/Normal/Overload control.

**GURPS Space.** The weapons discussion provides broad pattern-level support that a missile body may carry qualitatively different warheads, including kinetic-kill or energetic payloads. CP113 uses only that conceptual separation and copies no game mechanics.

**Master of Orion II.** Its weapon-modification system is useful only as a pattern: specialist improvements can have real size/cost/compatibility tradeoffs, and missile guidance/defensive characteristics need not be the same axis as payload. CP113 does not copy its names, values, or modification rules.

**Star Fleet Battles.** Its finite ammunition, alternative ammunition, seeking-weapon modules, and multi-warhead examples reinforce that launcher, guidance, payload and magazine constraints can be distinct. CP113 deliberately avoids SFB's detailed ammunition accounting and impulse-level complexity.

## Reconciliation conclusions

1. Kinetic ammunition should be mostly automatic maturation when a new compatible projectile is simply better. The TL2 material improvement and TL4 smart/maneuvering projectile therefore should not become fake loadout choices.
2. Kinetic selectable modes are reserved for genuine tradeoffs, currently dense/graded penetrators and saturation/submunition packages.
3. Missile warheads are more naturally mission-specific. General-purpose warheads can auto-mature at major high-energy breakthroughs, while armor-penetrating and shield-disruption warheads remain selectable from the same generic Missile Flight magazine.
4. A TL4 directed-pulse/shield-disruption warhead is the current anti-shield architecture candidate. Its exact mechanic is deliberately left to simulation: extra shield-only damage, bounded Shield-Armor reduction, or limited recharge suppression are the leading characteristic axes.
5. The TL6 radiation/electronics-disruption payload stays deferred until internal critical/subsystem and crew effects exist in the Python research consumer.
6. Normal Fusion/Antimatter-era payloads do not get separate tactical inventory counts merely because their physics is exotic by modern standards. Once they are normal player technology, they use the generic Missile Flight store; strategic Resource/resupply cost can later reflect their engineering burden.
7. Matter-conversion, alien, Precursor, and other genuinely rare payloads may be individually tracked by shot because scarcity itself is a gameplay decision.
8. Sensor/intelligence gameplay does not need to expose exact enemy defenses for specialist warheads to be usable. Firm-track combat assessment can report observable layer effects—shield absorption/collapse, armor contact, Hull penetration, and later shield restoration—without revealing exact capacities or hidden arithmetic.

## Why CP113 does not rebalance the TL9 stalemate

The architecture now supplies plausible future tools for breaking a shield-sustain equilibrium, but their effectiveness must be measured. CP113 therefore suspends several uncalibrated CP109 payload branch numbers that would otherwise be strict upgrades or universal raw-damage escalations. The next study should implement candidate payload modes only in the Python research consumer and sweep their tradeoffs against shield-heavy, armor-heavy, and generalist controls.
