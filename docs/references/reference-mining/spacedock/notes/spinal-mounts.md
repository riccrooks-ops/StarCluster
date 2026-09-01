# Spacedock Mining Note - Spinal Mounts

- **Source ID:** SD-SM
- **Source:** Spacedock - Spinal Mounts
- **URL:** https://www.youtube.com/watch?v=PZEbI1vToqc
- **Status:** mined
- **Authority:** reference only; not a Star Cluster rule

## High-value design signals

This source is highly relevant to **Main Weapon installation architecture**, especially Kinetic/Particle weapons. Its best gameplay avenue is a restricted engagement envelope: spinal systems gain exceptional long-range/accelerator performance while accepting close-range tracking and fire-versus-maneuver limitations.

## Observations

### SD-SM-001 - Removing a turret permits a much larger integrated weapon
- **Timestamp:** 2:51-3:20
- **Source idea:** A fixed ship-integrated mount can devote more structure/length to the weapon than a traversing turret.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** MAIN_WEAPON, INSTALLATION_SPACE, SHIP_ARCHITECTURE
- **Assessment:** Strong corroboration for Star Cluster's large Main Weapon Space abstraction, including ship-integrated support/reinforcement rather than literal barrel volume.

### SD-SM-002 - Accelerator length can buy projectile velocity and range
- **Timestamp:** 2:51-3:20
- **Source idea:** Kinetic and particle accelerators can exploit extra axial length to reach higher velocities and effective range.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** KINETIC_WEAPONS, PARTICLE_WEAPONS, RANGE, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Strong family-specific progression path that does not require another DAM/APEN increment.

### SD-SM-003 - Structural rigidity can improve pointing stability
- **Timestamp:** 3:21-3:44
- **Source idea:** A rigidly mounted system avoids some turret vibration and has predictable recoil geometry.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** MAIN_WEAPON, ACCURACY, ENGAGEMENT_ENVELOPE
- **Assessment:** Could support range/accuracy identity for spinal systems rather than raw damage alone.

### SD-SM-004 - Mount architecture reallocates mass/structure
- **Timestamp:** 3:36-4:07
- **Source idea:** Eliminating turret machinery/armor can reallocate mass and structure to weapon or protection.
- **Relationship:** context_only
- **Disposition:** retain_reference
- **Tags:** SHIP_ARCHITECTURE, INSTALLATION_SPACE
- **Assessment:** Useful rationale for Space tradeoffs. Do not add a separate mass currency unless gameplay needs one.

### SD-SM-005 - Whole-ship aiming creates a close-range tracking weakness
- **Timestamp:** 4:15-5:15
- **Source idea:** The whole ship can point precisely but rotates more slowly than a turret and may fail to track fast nearby targets.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** MAIN_WEAPON, ENGAGEMENT_ENVELOPE, MOVEMENT, SPECIALIZED_COUNTERPLAY
- **Assessment:** Excellent natural counterplay: long-range superiority versus close-range/agile-target vulnerability.

### SD-SM-006 - Fixed forward weapons can force a fire-versus-maneuver choice
- **Timestamp:** 5:23-5:57
- **Source idea:** A ship may need to choose between holding weapon alignment and making a major burn in another direction.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** MAIN_WEAPON, MOVEMENT, COMMAND_DECISION, AVOID_EXCESS_SIMULATION
- **Assessment:** Strong tactical candidate. Explore an abstract Firing Alignment/commitment before adding full facing/arcs.

### SD-SM-007 - Spinal weapons favor specialist ship roles
- **Timestamp:** 6:04-6:41
- **Source idea:** Siege, fortress-breaking, or small anti-capital craft can justify a weapon disproportionately large for the hull.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** SHIP_ARCHITECTURE, SPECIALIZATION, LEGAL_BUILD_EXTREMES
- **Assessment:** Fits generalized legal-build philosophy: extreme but legal designs should be testable rather than pruned.

### SD-SM-008 - Semi-fixed/gimballed mounts offer an intermediate architecture
- **Timestamp:** 6:55-7:21
- **Source idea:** A mostly fixed weapon can retain some limited aim while preserving many structural advantages.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** MAIN_WEAPON, MOUNT_ARCHITECTURE
- **Assessment:** Potential intermediate progression or family-specific mount type if full spinal/turret distinction proves valuable.

### SD-SM-009 - Lasers do not gain from axial mounting in the same way
- **Timestamp:** 7:21-7:46
- **Source idea:** Laser-generating machinery can be placed internally and route its beam to separate directing optics.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** ENERGY_WEAPONS, WEAPON_FAMILY_IDENTITY, MOUNT_ARCHITECTURE
- **Assessment:** Important guardrail: a generic Spinal trait should not give identical benefits to every Main Weapon family.

### SD-SM-010 - Particle beams may occupy a semi-spinal middle ground
- **Timestamp:** 7:46-8:08
- **Source idea:** Particle streams may benefit from axial accelerator length but permit limited electromagnetic steering.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** PARTICLE_WEAPONS, WEAPON_FAMILY_IDENTITY, MOUNT_ARCHITECTURE
- **Assessment:** Useful if Particle weapons become a distinct family: more aim freedom than rigid Kinetic spinal systems, less than beam-director Energy systems.

### SD-SM-011 - Broadside fixed weapons decouple firing and thrust axes
- **Timestamp:** 8:08-8:53
- **Source idea:** Broadside fixed mounts permit movement orthogonal to the target while firing.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** MOUNT_ARCHITECTURE, MOVEMENT, FACING
- **Assessment:** Interesting, but likely not worth introducing firing arcs/facing by itself.

## Candidate discussion queue

1. Spinal architecture as a restricted-performance Main Weapon choice.
2. Close-range tracking counterplay.
3. Abstract fire-versus-maneuver commitment before full facing.
4. Kinetic accelerator/mount progression distinct from Energy beam-director progression.
