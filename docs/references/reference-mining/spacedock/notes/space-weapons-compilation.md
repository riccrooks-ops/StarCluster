# Spacedock Mining Note - Space Weapons Compilation

- **Source ID:** SD-SW
- **Source:** Spacedock - Space Weapons (long compilation)
- **URL:** https://www.youtube.com/watch?v=uhLyMdxmw9M
- **Status:** mined
- **Authority:** reference only; not a Star Cluster rule

## High-value design signals

This compilation overlaps many standalone weapon videos. Its greatest value is **system-level comparison**: engagement range emerges from weapon physics, target mobility, sensing, EW, guidance, and defenses; weapon families should progress through different architectures; PDS and EW have multiple distinct branches/counterplays.

Future standalone videos that match compilation chapters should be checked for duplication before new observations are created.

## Observations

### SD-SW-001 - Kinetic effective range depends on target response time
- **Timestamp:** 2:40-3:41
- **Source idea:** Unguided projectile hit probability depends on projectile speed, distance, target size and target acceleration; closer/faster shots reduce the target's ability to evade.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** KINETIC_WEAPONS, ENGAGEMENT_ENVELOPE, MOVEMENT
- **Assessment:** Supports family-specific effective range without collapsing physical range, tracking and attack eligibility into one number.

### SD-SW-002 - Kinetic fire can create maneuver/evasion pressure
- **Timestamp:** 2:48-3:10
- **Source idea:** Threatening fire can force a target to maneuver even when the shot is not expected to hit, potentially consuming propellant or position.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** KINETIC_WEAPONS, MOVEMENT, FUEL, SPECIALIZED_COUNTERPLAY
- **Assessment:** Potential future suppression/evasion-pressure mechanic if movement/evasion becomes rich enough. Avoid a generic suppression status bonus/penalty.

### SD-SW-003 - Kinetic technology has multiple engineering branches
- **Timestamp:** 4:17-12:07 and 1:56:45-2:05:53
- **Source idea:** Chemical guns, coilguns, railguns, hybrids and advanced electromagnetic launchers trade simplicity, power, timing, wear, projectile complexity and velocity differently.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** KINETIC_WEAPONS, QUALITATIVE_TECH_PROGRESSION, WEAPON_FAMILY_IDENTITY
- **Assessment:** Strong basis for Kinetic progression through architecture rather than automatic DAM/APEN increases.

### SD-SW-004 - Missiles are miniature spacecraft
- **Timestamp:** 13:10-20:42
- **Source idea:** Missile propulsion, guidance, seeker, payload, power, sensors, EW/countermeasures and launch architecture can vary independently.
- **Relationship:** corroborates_existing
- **Disposition:** discuss
- **Tags:** MISSILES, QUALITATIVE_TECH_PROGRESSION, GUIDANCE, SENSORS
- **Assessment:** Strong model for modular missile progression; especially consistent with existing command-guided versus local-seeker distinctions.

### SD-SW-005 - Missile size trades salvo density against per-missile capability
- **Timestamp:** 18:13-18:52
- **Source idea:** Many small missiles stress defenses but have less room for seekers/power/payload, while larger missiles are more capable but easier to engage individually.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** MISSILES, PDS, SALVO_ARCHITECTURE, SPECIALIZED_COUNTERPLAY
- **Assessment:** Strong future design axis: saturation missiles versus fewer sophisticated heavy missiles.

### SD-SW-006 - One laser generator can feed multiple beam directors
- **Timestamp:** 46:00-46:40
- **Source idea:** A large internal laser generator can route output among multiple external directing apertures/turrets.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** ENERGY_WEAPONS, MOUNT_ARCHITECTURE, REDUNDANCY
- **Assessment:** Excellent Energy-specific architecture for rapid retargeting/director redundancy. Multiple directors must not silently become multiple Main Weapon attack packages.

### SD-SW-007 - Particle beams can justify a distinct weapon family
- **Timestamp:** 51:12-1:02:23
- **Source idea:** Particle beams differ from lasers in propagation, accelerator architecture, penetration, radiation effects and possible active defenses.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** PARTICLE_WEAPONS, WEAPON_FAMILY_IDENTITY, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Enough distinct behavior exists to investigate Particle weapons as a future family rather than an Energy reskin.

### SD-SW-008 - Macron/dust accelerators are a distinct late accelerator concept
- **Timestamp:** 1:02:33-1:11:12
- **Source idea:** Microscopic high-velocity projectiles can create dense erosive streams with unusual detectability/interception and payload possibilities.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** KINETIC_WEAPONS, MACRONS, EXOTIC_WEAPON
- **Assessment:** Interesting late Kinetic/accelerator branch; lower priority until ordinary families are mature.

### SD-SW-009 - Conventional plasma bolts may not earn a separate family
- **Timestamp:** 1:11:15-1:19:41
- **Source idea:** Plausible plasma weapon concepts struggle with expansion and often converge toward very high-speed directed plasma/particle-beam behavior.
- **Relationship:** conflicts_or_warns
- **Disposition:** retain_reference
- **Tags:** PLASMA_WEAPONS, WEAPON_FAMILY_IDENTITY
- **Assessment:** Design guardrail: do not add a Plasma family simply because genre convention expects one; it must earn a distinct gameplay role.

### SD-SW-010 - Point defense has multiple architecture families
- **Timestamp:** 1:29:00-1:38:20
- **Source idea:** Kinetic/flak, laser and interceptor-missile defenses offer different engagement windows, ammunition/power costs and threat-processing behavior.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** PDS, QUALITATIVE_TECH_PROGRESSION, WEAPON_FAMILY_IDENTITY
- **Assessment:** One of the strongest compilation candidates. Future PDS progression should consider branching architectures rather than only higher numerical ratings.

### SD-SW-011 - PDS can combine local fire control with ship-level information
- **Timestamp:** 1:37:03-1:37:34
- **Source idea:** Defensive weapons may carry their own sensing/control or consume data from the ship's larger systems.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** PDS, TACTICAL_COMPUTER, SENSORS
- **Assessment:** Strong support for current Star Cluster PDS architecture: self-contained local terminal opportunity with optional main Tactical Computer assistance.

### SD-SW-012 - Active emitters create anti-radiation opportunities
- **Timestamp:** 1:44:15-1:44:54
- **Source idea:** Sensors/jammers can be attacked by weapons that home on their emissions rather than defeating the signal-processing contest directly.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** ELECTRONIC_WARFARE, SENSORS, MISSILES, SPECIALIZED_COUNTERPLAY
- **Assessment:** Strong future counterplay candidate, especially because it answers powerful active ECM with a different targeting path rather than a simple ECM nerf.

### SD-SW-013 - EW can deceive rather than only deny
- **Timestamp:** 1:39:26-1:47:45
- **Source idea:** Electronic attack includes false signatures, range/velocity deception, decoys, communications disruption and directional effects, not merely stronger noise.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** ELECTRONIC_WARFARE, QUALITATIVE_TECH_PROGRESSION, DECEPTION
- **Assessment:** Strong later-TL ECM/EW progression direction that reduces pressure to escalate one universal rating indefinitely.

### SD-SW-014 - Mines make most sense at strategic constraints
- **Timestamp:** 2:05:57-2:13:50
- **Source idea:** Space is too large for ordinary dense minefields except around strategically constrained locations; mobile/ranged mines increasingly resemble disposable weapon platforms or missiles.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** MINES, STRATEGIC_LAYER, EXPLORATION
- **Assessment:** Favor gates, stations, approaches, anomalies and prepared system-map hazards over generic tactical-hex mine spam.

### SD-SW-015 - Turrets are substantial internal weapon architecture
- **Timestamp:** 2:14:01 onward
- **Source idea:** Turrets include deep internal support, feed, structure and traverse systems rather than only the visible rotating mount.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** MAIN_WEAPON, INSTALLATION_SPACE, MOUNT_ARCHITECTURE
- **Assessment:** Reinforces Main Weapon Installation Space as ship-integrated architecture and supports future turret/spinal/beam-director distinctions.

### SD-SW-016 - Radiation attacks create non-hull consequences
- **Timestamp:** 21:39-31:21 and 56:21-57:37
- **Source idea:** Nuclear/particle radiation can harm crew and electronics differently from ordinary structural damage, while shielding carries substantial engineering cost.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** RADIATION, DEFERRED_CREW_EFFECTS, COMPUTING
- **Assessment:** Revisit after dedicated Radiation Weapons material and mature Crew/internal-damage systems. Avoid a generic extra damage type now.

### SD-SW-017 - Engagement range is a systems interaction
- **Timestamp:** recurring across Kinetic, Missile, Laser, Particle and EW chapters
- **Source idea:** Useful range emerges from projectile/beam behavior, target mobility, sensor uncertainty, guidance, EW and defensive interception rather than a single physical reach number.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** ENGAGEMENT_ENVELOPE, SENSORS, ELECTRONIC_WARFARE, MOVEMENT
- **Assessment:** Strong cross-source validation of Star Cluster's separation of physical reach, track quality and attack eligibility.

### SD-SW-018 - Gameplay family identity matters more than perfect scientific taxonomy
- **Timestamp:** recurring across weapon chapters
- **Source idea:** Categories blur physically: particle beams are particles, plasma is matter, electromagnetic guns are power-hungry, lasers may be chemically powered.
- **Relationship:** new_candidate
- **Disposition:** retain_reference
- **Tags:** WEAPON_FAMILY_IDENTITY, DESIGN_GUARDRAIL
- **Assessment:** Define Star Cluster families by coherent technology lineage and gameplay identity rather than taxonomy purity.

### SD-SW-019 - Exceptional weapons should feel like events
- **Timestamp:** 31:31-40:35
- **Source idea:** Memorable superweapons are distinguished by preparation, visible commitment, buildup and consequences rather than only larger output.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** RARE_WEAPON_EVENT, OVERLOAD, CHARGING, SPECIAL_WEAPON
- **Assessment:** Excellent principle for rare/Precursor/experimental weapons using existing charging, Tactical Power commitment and Strain concepts.

## Candidate discussion queue

1. Qualitative PDS families.
2. Modular missile progression and salvo-size tradeoffs.
3. Anti-emitter/home-on-jam counterplay and deceptive EW modes.
4. Particle weapons as a distinct future family.
5. Strategic/system-layer minefields.
6. Rare superweapons as committed events rather than giant damage numbers.
7. Mount architecture and distributed Energy beam directors.

## Checkpoint 92 duplicate-chapter re-review refinements

The 16 standalone videos confirmed as exact/near-exact chapter duplicates were preserved separately but generated no standalone observation IDs. Their re-review extended the SD-SW observation set below. These are still reference-only observations.

### SD-SW-020 - Kinetic and Energy weapon families can differ in resource burden: finite ammunition and magazines versus power/thermal demand, with hybrid technologies sometimes carrying both.
- **Timestamp:** 2:29:21-2:38:24
- **Source idea:** Kinetic and Energy weapon families can differ in resource burden: finite ammunition and magazines versus power/thermal demand, with hybrid technologies sometimes carrying both.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** WEAPON_FAMILY_IDENTITY, AMMUNITION, TACTICAL_POWER, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Useful family identity axis; do not turn it into an absolute physics taxonomy.

### SD-SW-021 - Kinetic systems can vary through projectile, accelerator and ammunition changes, while Energy systems can vary through emitter, focusing, steering and efficiency changes.
- **Timestamp:** 2:29:21-2:38:24
- **Source idea:** Kinetic systems can vary through projectile, accelerator and ammunition changes, while Energy systems can vary through emitter, focusing, steering and efficiency changes.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** WEAPON_FAMILY_IDENTITY, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Strong support for asymmetric family-specific TL progression.
### SD-SW-022 - Radiation-oriented weapons can be countered by dedicated shielding/hardening, but that protection carries engineering cost.
- **Timestamp:** 2:22:07-2:29:13
- **Source idea:** Radiation-oriented weapons can be countered by dedicated shielding/hardening, but that protection carries engineering cost.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** RADIATION, SPECIALIZED_COUNTERPLAY, SHIP_ARCHITECTURE
- **Assessment:** Prefer specialist hardening/traits over a universal radiation-resistance stat until radiation mechanics earn that complexity.

### SD-SW-023 - Particle composition and mass can change how deeply energy is deposited and how strongly secondary ionizing effects threaten crew/electronics.
- **Timestamp:** 2:22:07-2:29:13
- **Source idea:** Particle composition and mass can change how deeply energy is deposited and how strongly secondary ionizing effects threaten crew/electronics.
- **Relationship:** extends_candidate
- **Disposition:** defer
- **Tags:** RADIATION, PARTICLE_WEAPONS, DEFERRED_CREW_EFFECTS
- **Assessment:** Potential future specialization axis; avoid detailed dose simulation.

### SD-SW-024 - Radiological contamination and lingering exposure can matter after an attack even when the immediate structural effect is limited.
- **Timestamp:** 2:22:07-2:29:13
- **Source idea:** Radiological contamination and lingering exposure can matter after an attack even when the immediate structural effect is limited.
- **Relationship:** context_only
- **Disposition:** defer
- **Tags:** RADIATION, STRATEGIC_LAYER, SCENARIO
- **Assessment:** Better suited to scenario/salvage consequences than universal tactical bookkeeping.

### SD-SW-025 - Minefields derive much of their value from uncertainty and area denial rather than raw damage alone.
- **Timestamp:** 2:05:57-2:13:50
- **Source idea:** Minefields derive much of their value from uncertainty and area denial rather than raw damage alone.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** MINES, INFORMATION, AREA_DENIAL
- **Assessment:** Supports observer-safe hazard regions and route pressure rather than visible mine-counter spam.

### SD-SW-026 - Mine counterplay can include sensing, probes, spoofing, sweeping, disposable clearing assets and route choice.
- **Timestamp:** 2:05:57-2:13:50
- **Source idea:** Mine counterplay can include sensing, probes, spoofing, sweeping, disposable clearing assets and route choice.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** MINES, SPECIALIZED_COUNTERPLAY, SENSORS, EXPLORATION
- **Assessment:** Strong counterplay vocabulary if minefields are introduced.

### SD-SW-027 - As mines gain range, mobility or autonomous pursuit they increasingly blur into disposable platforms or missiles.
- **Timestamp:** 2:05:57-2:13:50
- **Source idea:** As mines gain range, mobility or autonomous pursuit they increasingly blur into disposable platforms or missiles.
- **Relationship:** extends_candidate
- **Disposition:** retain_reference
- **Tags:** MINES, MISSILES, WEAPON_FAMILY_IDENTITY
- **Assessment:** Classify future systems by behavior rather than naming convention.

### SD-SW-028 - Large weapon mounts trade structural mass/output against tracking responsiveness and target-switch agility.
- **Timestamp:** 2:14:01-2:22:00
- **Source idea:** Large weapon mounts trade structural mass/output against tracking responsiveness and target-switch agility.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** MAIN_WEAPON, MOUNT_ARCHITECTURE, ENGAGEMENT_ENVELOPE
- **Assessment:** Useful distinction for heavy/spinal/turreted architectures without degrees-per-second simulation.

### SD-SW-029 - Phased-array or other nonmechanical beam steering can improve rapid retargeting and distributed aperture use without increasing total generator output.
- **Timestamp:** 1:48:01-1:56:35; 2:14:01-2:22:00
- **Source idea:** Phased-array or other nonmechanical beam steering can improve rapid retargeting and distributed aperture use without increasing total generator output.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** ENERGY_WEAPONS, MOUNT_ARCHITECTURE, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Strong high-TL integration direction; no free extra attack packages.

### SD-SW-030 - Kinetic ammunition can use penetrators, proximity/submunition packages, guided or smart projectiles, specialized armatures and exotic materials in addition to changes in the launcher itself.
- **Timestamp:** 1:56:45-2:05:53
- **Source idea:** Kinetic ammunition can use penetrators, proximity/submunition packages, guided or smart projectiles, specialized armatures and exotic materials in addition to changes in the launcher itself.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** KINETIC_WEAPONS, AMMUNITION, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** One of the richest Kinetic progression axes.
### SD-SW-031 - Rail, coil and hybrid/helical electromagnetic launchers trade timing/control complexity, current, wear, projectile interaction and accelerator architecture in different ways.
- **Timestamp:** 1:56:45-2:05:53
- **Source idea:** Rail, coil and hybrid/helical electromagnetic launchers trade timing/control complexity, current, wear, projectile interaction and accelerator architecture in different ways.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** KINETIC_WEAPONS, ARCHITECTURAL_TECH_BREAKTHROUGH, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Promising maturation branch; exact implementation remains open.
### SD-SW-032 - Advanced laser systems can distribute generation and steering across multiple apertures/arrays for resilience and rapid engagement changes.
- **Timestamp:** 1:48:01-1:56:35
- **Source idea:** Advanced laser systems can distribute generation and steering across multiple apertures/arrays for resilience and rapid engagement changes.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** ENERGY_WEAPONS, REDUNDANCY, MOUNT_ARCHITECTURE
- **Assessment:** Corroborates distributed-director architecture while keeping one bounded output pool.

### SD-SW-033 - Laser-coupled particle concepts offer an exotic route to reduced divergence or extreme-range directed effects.
- **Timestamp:** 1:48:01-1:56:35
- **Source idea:** Laser-coupled particle concepts offer an exotic route to reduced divergence or extreme-range directed effects.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** ENERGY_WEAPONS, PARTICLE_WEAPONS, EXOTIC_WEAPON
- **Assessment:** Preserve as exotic/Precursor/high-TL inspiration rather than ordinary progression.

### SD-SW-034 - Physical/active decoys are a distinct EW tool from continuous jamming and can attack seeker discrimination rather than raw signal strength.
- **Timestamp:** 1:38:29-1:47:45
- **Source idea:** Physical/active decoys are a distinct EW tool from continuous jamming and can attack seeker discrimination rather than raw signal strength.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** ELECTRONIC_WARFARE, DECEPTION, MISSILES
- **Assessment:** Potential qualitative EW progression without another stacked rating.

### SD-SW-035 - Communications jamming can attack command links and datalinks rather than only sensor discrimination.
- **Timestamp:** 1:38:29-1:47:45
- **Source idea:** Communications jamming can attack command links and datalinks rather than only sensor discrimination.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** ELECTRONIC_WARFARE, COMMUNICATIONS, MISSILES, GUIDANCE
- **Assessment:** Especially relevant to command-guided missile chains; needs explicit observer-safe mechanics later.

### SD-SW-036 - Directional jamming can concentrate effect when threat direction is known, at the cost of coverage/flexibility.
- **Timestamp:** 1:38:29-1:47:45
- **Source idea:** Directional jamming can concentrate effect when threat direction is known, at the cost of coverage/flexibility.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** ELECTRONIC_WARFARE, SPECIALIZED_COUNTERPLAY
- **Assessment:** Interesting specialist system; avoid baseline facing/allocation micromanagement.

### SD-SW-037 - Point-defense systems can use high-volume kinetic fire, proximity/submunition packages, local fire-control improvements and guided intercept rounds.
- **Timestamp:** 1:29:00-1:38:20
- **Source idea:** Point-defense systems can use high-volume kinetic fire, proximity/submunition packages, local fire-control improvements and guided intercept rounds.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** PDS, KINETIC_WEAPONS, QUALITATIVE_TECH_PROGRESSION, AMMUNITION
- **Assessment:** Strong family-specific PDS progression vocabulary.
### SD-SW-038 - Point defense operates during a short terminal closing interval in which reaction time and opportunities to re-engage an incoming threat are limited.
- **Timestamp:** 1:29:00-1:38:20
- **Source idea:** Point defense operates during a short terminal closing interval in which reaction time and opportunities to re-engage an incoming threat are limited.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** PDS, ENGAGEMENT_ENVELOPE, REACTION_CAPACITY
- **Assessment:** Supports current abstraction; no need for turret-arc or burst-by-burst timing.
### SD-SW-039 - Anti-missile missiles form a distinct guided defensive layer with finite interceptor inventory and potentially longer reach than terminal gun/laser PDS.
- **Timestamp:** 1:29:00-1:38:20
- **Source idea:** Anti-missile missiles form a distinct guided defensive layer with finite interceptor inventory and potentially longer reach than terminal gun/laser PDS.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** PDS, MISSILES, AMMUNITION, SPECIALIZED_COUNTERPLAY
- **Assessment:** Natural future extended-defense family; keep distinct from standard terminal PDS.

### SD-SW-040 - Destroying or mission-killing an incoming missile can still leave high-velocity fragments that are physically hazardous.
- **Timestamp:** 1:29:00-1:38:20
- **Source idea:** Destroying or mission-killing an incoming missile can still leave high-velocity fragments that are physically hazardous.
- **Relationship:** context_only
- **Disposition:** retain_reference
- **Tags:** PDS, AVOID_EXCESS_SIMULATION, MISSILES
- **Assessment:** Record the physical caveat, but retain Star Cluster's attack-package abstraction and no universal residual-debris damage roll unless a special trait later earns one.
### SD-SW-041 - Macron weapons fire enormous streams of microscopic projectiles that can be carried in very large physical quantities, while their electrostatic accelerator infrastructure can be substantial.
- **Timestamp:** 1:02:33-1:11:12
- **Source idea:** Macron weapons fire enormous streams of microscopic projectiles that can be carried in very large physical quantities, while their electrostatic accelerator infrastructure can be substantial.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** MACRONS, KINETIC_WEAPONS, AMMUNITION, INSTALLATION_SPACE
- **Assessment:** Distinctive late-Kinetic trade: abundant attack material, demanding launcher.
### SD-SW-042 - Fissile or fusion payloads inside macrons can release additional nuclear energy on impact, and related microreaction concepts can also be used for power generation or propulsion.
- **Timestamp:** 1:02:33-1:11:12
- **Source idea:** Fissile or fusion payloads inside macrons can release additional nuclear energy on impact, and related microreaction concepts can also be used for power generation or propulsion.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** MACRONS, CROSS_CATEGORY_INTERACTION, KINETIC_WEAPONS, POWER, PROPULSION
- **Assessment:** Excellent example of enabling science shared across categories without merging ownership.
### SD-SW-043 - Particle species can shift a beam from shallow material damage toward deeper ionization/radiation and electronics effects.
- **Timestamp:** 51:12-1:02:23
- **Source idea:** Particle species can shift a beam from shallow material damage toward deeper ionization/radiation and electronics effects.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** PARTICLE_WEAPONS, RADIATION, WEAPON_FAMILY_IDENTITY
- **Assessment:** Strong subtype/progression axis; does not require a universal radiation bar.

### SD-SW-044 - Neutralizing a charged particle beam after acceleration can reduce electrostatic bloom and preserve a tighter beam over distance.
- **Timestamp:** 51:12-1:02:23
- **Source idea:** Neutralizing a charged particle beam after acceleration can reduce electrostatic bloom and preserve a tighter beam over distance.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** PARTICLE_WEAPONS, ENGAGEMENT_ENVELOPE, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Strong qualitative maturation step.
### SD-SW-045 - Electrostatic, magnetic and plasma-screen defenses provide specialist countermeasure concepts against particle beams.
- **Timestamp:** 51:12-1:02:23
- **Source idea:** Electrostatic, magnetic and plasma-screen defenses provide specialist countermeasure concepts against particle beams.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** PARTICLE_WEAPONS, SPECIALIZED_COUNTERPLAY, AUXILIARY
- **Assessment:** Prefer specialist auxiliaries/traits over redefining ordinary shields.

### SD-SW-046 - Ultra-relativistic electron beams greatly reduce bloom, carry extreme energy, penetrate strongly, generate high-energy secondary radiation and are very difficult to deflect.
- **Timestamp:** 59:03-1:02:23
- **Source idea:** Ultra-relativistic electron beams greatly reduce bloom, carry extreme energy, penetrate strongly, generate high-energy secondary radiation and are very difficult to deflect.
- **Relationship:** conflicts_or_warns
- **Disposition:** defer
- **Tags:** PARTICLE_WEAPONS, EXOTIC_WEAPON, RARE_WEAPON_EVENT
- **Assessment:** Preserve as exceptional/Precursor/very-late candidate unless substantial costs and counters are proven.
### SD-SW-047 - Continuous-wave and pulsed lasers deposit energy differently; short high-energy pulses can create mechanical shock and drilling-like effects, and pulse duration changes the result.
- **Timestamp:** 40:41-51:02
- **Source idea:** Continuous-wave and pulsed lasers deposit energy differently; short high-energy pulses can create mechanical shock and drilling-like effects, and pulse duration changes the result.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** ENERGY_WEAPONS, QUALITATIVE_TECH_PROGRESSION, PULSED_WEAPON
- **Assessment:** Strong basis for a pulsed-laser maturation step; exact DAM/APEN/mode mechanics remain open.
### SD-SW-048 - Chemical lasers can trade finite expendable reactants for high output/reduced ship electrical dependence.
- **Timestamp:** 41:45-43:00
- **Source idea:** Chemical lasers can trade finite expendable reactants for high output/reduced ship electrical dependence.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** ENERGY_WEAPONS, AMMUNITION, TACTICAL_POWER
- **Assessment:** Useful faction/specialist Beam identity; Beam does not have to mean infinite electrical ammunition.

### SD-SW-049 - Distributed strategic focusing arrays can create system-scale laser infrastructure useful for weapons, propulsion, sensing, communications or power transfer.
- **Timestamp:** 49:04-50:35
- **Source idea:** Distributed strategic focusing arrays can create system-scale laser infrastructure useful for weapons, propulsion, sensing, communications or power transfer.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** ENERGY_WEAPONS, STRATEGIC_LAYER, INFRASTRUCTURE, CROSS_CATEGORY_INTERACTION
- **Assessment:** Better fit for installations/Precursor infrastructure than ordinary cruiser Main Weapons.

### SD-SW-050 - Superweapon status is a role/scale/narrative descriptor, and extraordinary effects can emerge from unusual uses of established systems rather than a dedicated weapon family.
- **Timestamp:** 31:31-40:35
- **Source idea:** Superweapon status is a role/scale/narrative descriptor, and extraordinary effects can emerge from unusual uses of established systems rather than a dedicated weapon family.
- **Relationship:** extends_candidate
- **Disposition:** retain_reference
- **Tags:** RARE_WEAPON_EVENT, SPECIAL_WEAPON, WEAPON_FAMILY_IDENTITY
- **Assessment:** Do not create a Superweapon TL family; use rare scenario/Precursor/artifact effects when appropriate.

### SD-SW-051 - Nuclear devices are commonly missile-delivered, and nuclear energy can also be engineered into several directed terminal effects rather than only an omnidirectional detonation.
- **Timestamp:** 21:39-31:21
- **Source idea:** Nuclear devices are commonly missile-delivered, and nuclear energy can also be engineered into several directed terminal effects rather than only an omnidirectional detonation.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** NUCLEAR, MISSILES, WARHEAD, WEAPON_FAMILY_IDENTITY
- **Assessment:** Strong support for separating missile delivery/guidance from warhead effect.
### SD-SW-052 - Bomb-pumped beams, directed plasma charges and nuclear formed penetrators can focus nuclear output into qualitatively different terminal attack mechanisms.
- **Timestamp:** 25:40-31:21
- **Source idea:** Bomb-pumped beams, directed plasma charges and nuclear formed penetrators can focus nuclear output into qualitatively different terminal attack mechanisms.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** NUCLEAR, MISSILES, WARHEAD, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Rich advanced-warhead vocabulary; exact Star Cluster stats remain open.

### SD-SW-053 - The same directed nuclear-energy principles can be applied to propulsion or converted back into weapons such as plasma jets and explosively formed penetrators.
- **Timestamp:** 25:40-31:21
- **Source idea:** The same directed nuclear-energy principles can be applied to propulsion or converted back into weapons such as plasma jets and explosively formed penetrators.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** NUCLEAR, CROSS_CATEGORY_INTERACTION, MISSILES, KINETIC_WEAPONS, POWER
- **Assessment:** Use causal prerequisite tags if adopted; do not merge the research families.
### SD-SW-054 - Enhanced-radiation nuclear devices deliberately shift more of their output toward neutrons, threatening crew over distances where strong material damage may be much lower.
- **Timestamp:** 23:57-25:39
- **Source idea:** Enhanced-radiation nuclear devices deliberately shift more of their output toward neutrons, threatening crew over distances where strong material damage may be much lower.
- **Relationship:** extends_candidate
- **Disposition:** defer
- **Tags:** NUCLEAR, RADIATION, DEFERRED_CREW_EFFECTS, CAPTURE
- **Assessment:** Potential niche payload after crew/internal systems mature; specialist hardening can counter it.
### SD-SW-055 - A deliberately broader, shorter-ranged directed nuclear effect can be used defensively to destroy incoming weapons across a volume of space.
- **Timestamp:** 27:03-27:10
- **Source idea:** A deliberately broader, shorter-ranged directed nuclear effect can be used defensively to destroy incoming weapons across a volume of space.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** NUCLEAR, PDS, MISSILES, SPECIALIZED_COUNTERPLAY
- **Assessment:** Interesting AMM/emergency-defense concept with obvious scarcity/collateral costs.
### SD-SW-056 - Missile designs vary separately in propulsion/endurance, guidance and sensors, warhead type, physical size and launcher integration.
- **Timestamp:** 12:27-21:30
- **Source idea:** Missile designs vary separately in propulsion/endurance, guidance and sensors, warhead type, physical size and launcher integration.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** MISSILES, GUIDANCE, SENSORS, WARHEAD, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Strong structural support for modular missile progression.
### SD-SW-057 - Unguided rockets/torpedoes remain a legitimate distinct munition form with shorter useful reach but lower guidance complexity.
- **Timestamp:** 14:44-15:07
- **Source idea:** Unguided rockets/torpedoes remain a legitimate distinct munition form with shorter useful reach but lower guidance complexity.
- **Relationship:** new_candidate
- **Disposition:** retain_reference
- **Tags:** MISSILES, UNGUIDED, WEAPON_FAMILY_IDENTITY
- **Assessment:** Supports retaining unguided rockets as a real capability combination.

### SD-SW-058 - Seeker sophistication and countermeasures form an arms race in discrimination, decoys/blinding and onboard power/integration complexity.
- **Timestamp:** 13:46-14:44
- **Source idea:** Seeker sophistication and countermeasures form an arms race in discrimination, decoys/blinding and onboard power/integration complexity.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** MISSILES, GUIDANCE, ELECTRONIC_WARFARE, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Higher-TL guidance can improve robustness/information quality rather than raw warhead damage.

### SD-SW-059 - Many-small versus few-large missile designs trade defensive saturation against per-vehicle sensor, power, protection and payload capability.
- **Timestamp:** 18:13-19:32
- **Source idea:** Many-small versus few-large missile designs trade defensive saturation against per-vehicle sensor, power, protection and payload capability.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** MISSILES, SALVO_ARCHITECTURE, PDS
- **Assessment:** Maps naturally to different physical compositions inside one Missile Flight abstraction.

### SD-SW-060 - Missile engine/propellant choices trade acceleration, range/endurance and cost; beamed-power propulsion can extend range while shifting the propulsion power burden back to the launching platform.
- **Timestamp:** 20:26-21:30
- **Source idea:** Missile engine/propellant choices trade acceleration, range/endurance and cost; beamed-power propulsion can extend range while shifting the propulsion power burden back to the launching platform.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** MISSILES, PROPULSION, TACTICAL_POWER, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Useful progression axis; beamed-power missiles need a distinct reason to exist over firing the beam directly.
### SD-SW-061 - Projectile mass, velocity and construction can trade broad energy deposition against narrow penetration/internal effects.
- **Timestamp:** 1:24-4:03
- **Source idea:** Projectile mass, velocity and construction can trade broad energy deposition against narrow penetration/internal effects.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** KINETIC_WEAPONS, APEN, DAMAGE, WEAPON_FAMILY_IDENTITY
- **Assessment:** Supports family-appropriate DAM/APEN trade space without automatic penetration every TL.

### SD-SW-062 - Coilguns require precise staged electromagnetic timing, while railguns avoid that timing burden but face high-current, heating, arcing, erosion and materials problems.
- **Timestamp:** 4:03-8:03
- **Source idea:** Coilguns require precise staged electromagnetic timing, while railguns avoid that timing burden but face high-current, heating, arcing, erosion and materials problems.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** KINETIC_WEAPONS, COMPUTING, MATERIALS, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Good sparse cross-category prerequisite vocabulary.
### SD-SW-063 - Kinetic launchers can require recoil compensation, structural bracing, cooling and wear management in addition to the accelerator and projectile themselves.
- **Timestamp:** 6:30-10:31
- **Source idea:** Kinetic launchers can require recoil compensation, structural bracing, cooling and wear management in addition to the accelerator and projectile themselves.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** KINETIC_WEAPONS, INSTALLATION_SPACE, AVOID_EXCESS_SIMULATION
- **Assessment:** Strong abstraction support.
### SD-SW-064 - Proximity/submunition Kinetic packages can trade individual hit effect for a larger effective interception/damage volume, especially against exposed or small systems.
- **Timestamp:** 2:38:34-2:47:05
- **Source idea:** Proximity/submunition Kinetic packages can trade individual hit effect for a larger effective interception/damage volume, especially against exposed or small systems.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** KINETIC_WEAPONS, AMMUNITION, PDS, SPECIALIZED_COUNTERPLAY
- **Assessment:** Interesting ammunition specialization; avoid generic size accuracy modifiers.

### SD-SW-065 - Missile closing speed, maneuver and remaining propellant affect the terminal interception opportunity available to point defense.
- **Timestamp:** 2:38:34-2:47:05
- **Source idea:** Missile closing speed, maneuver and remaining propellant affect the terminal interception opportunity available to point defense.
- **Relationship:** extends_candidate
- **Disposition:** defer
- **Tags:** MISSILES, PDS, ENGAGEMENT_ENVELOPE, PROPULSION
- **Assessment:** Useful rationale for bounded terminal-defense windows; defer detailed closing-time simulation.
