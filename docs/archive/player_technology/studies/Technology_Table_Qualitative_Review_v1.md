# Technology Table Qualitative Review v1

**Checkpoint:** 108  
**Scope:** Names, TL placement, ownership, default-versus-branch status, player-facing expression, KISS boundaries, legacy relevance, pinnacle sanity, and cross-discipline gating.  
**Excluded:** New TL4-TL9 numerical values, combat balance promotion, Monte Carlo, and production gameplay changes.

## Executive result

The CP107b table is fundamentally sound. The review does **not** replace its 10-discipline / 32-lineage / 214-beat foundation. It makes a focused set of corrections where the first explicit table exposed category drift or misleading default placement.

The strongest general conclusion is that a technology beat and a component are not the same thing. CP108 therefore classifies every Storyboard beat by player expression. This lets Hull integration, thermal engineering, gravity architecture, automation, ammunition, operating modes, optional support hardware, infrastructure, and Precursor exceptions coexist without manufacturing one installed component per row.

## Cross-cutting decisions

1. **Quiet primary-family TLs are intentional.** A specialist branch may unlock at a TL while the standard family receives no replacement. This is now explicit in the grid.
2. **Branches do not silently become defaults.** Helical/continuous-induction and macron Kinetics, tunable/free-electron and extreme-frequency beams, missile swarm/bus architecture, and field-assisted missile terminal maneuver remain alternate/specialist expressions.
3. **Passive armor remains passive.** Powered reactive and field-assisted defenses move to Armor Enhancement Branches; the primary passive armor line may be quiet at TL7-TL8.
4. **Information remains observer-safe.** Normal TL9 Sensors/EW/Computing receive meaningful bounded endpoints, but causal/precognitive truth remains Precursor-only.
5. **Missiles receive a normal TL9 endpoint without teleporting past defense.** Field-assisted terminal technology remains track-dependent, on-map, and interceptable; tactical micro-jump delivery remains deferred.
6. **Support catalogs must match the Storyboard.** Missing Shield-support candidates are materialized; the duplicate Armor EM-screen concept is consolidated; the preserved Probe / Survey Drone idea becomes an explicit optional-support candidate.
7. **No hard external research prerequisites are promoted.** Cross-pollination remains useful metadata until a component-level physical dependency is actually proven.
8. **No numerical calibration is performed.** Existing TL1-TL3 numerical authorities remain unchanged, and no TL4-TL9 Space, power, damage, penetration, range, capacity, or efficiency value is assigned.

## Discipline review

### Hull
**Assessment: retain.** Structural integration has a coherent cruiser-scale story from mature composite construction through smart/field-assisted/programable architecture without becoming battleship growth. Damage Control remains bounded by existing conditions/resources. CP108 clarifies that ordinary maintainability and gravity/habitation beats are often automatic/supporting architecture; only robotics/fabrication/patch systems that create meaningful build choices need separate installations.

### Armor
**Assessment: revise.** The CP107b primary passive line incorrectly included powered reactive and field-assisted armor. CP108 moves those concepts into Armor Enhancement Branches. Passive Armor therefore legitimately has quiet primary progression at TL7-TL8. The separate Armor electromagnetic-particle-screen concept is consolidated with Shield Support to avoid duplicate charged-particle defenses; material/radiation hardening remains Armor's distinct specialist response.

### Power
**Assessment: retain with naming cleanup.** The agreed Fission -> Fusion -> Antimatter -> Matter Conversion progression remains the strongest conceptual ladder. TL5 and TL8 component names now name the *new reactor principle*; coexistence with Peak Fusion/Peak Antimatter remains a legacy-catalog rule, not part of a hybrid component name. Thermal progression is supporting integration except where an explicit suppression module/mode creates a player decision.

### Propulsion
**Assessment: retain.** Separate STL and FTL installed families, specialist lower-SF drives, and route/infrastructure discoveries remain coherent. High-TL inertial/metric concepts are late science-fantasy but do not yet demand extra universal mechanics. No tactical micro-jump is promoted.

### Sensors / EW
**Assessment: revise TL7-TL9.** TL7 sensing is reframed as integrated penetrating multimodal sensing rather than a narrow mandatory branch. TL9 now has native normal-player Sensor, ECM, and ECCM endpoints based on multi-domain inference, cross-spectrum deception, and provenance-weighted validation. None provides perfect detection, perfect concealment, hidden-state access, or a truth oracle.

### Computing / Fire Control
**Assessment: retain with pinnacle rename.** The photonic -> adaptive AI -> distributed -> quantum-assisted -> predictive progression is coherent. TL9 is renamed to self-verifying battle synthesis to avoid suggesting causal or precognitive information. Synthetic crew remains deferred because it carries campaign/narrative consequences beyond a simple stat upgrade.

### Shields
**Assessment: revise TL3 wording and support catalog.** TL3 primary Shield maturation is separated from the optional Shield Hardener. The Storyboard's later particle-deflection and field-stabilization support ideas are now explicit optional catalog candidates. These remain specialist counters rather than universal Shield Armor inflation.

### Projectile Weapons
**Assessment: revise ownership/default status.** TL2 penetrator/projectile materials move from the accelerator lineage to Kinetic Ammunition. Helical/continuous-induction and macron/dust accelerators remain branches rather than mandatory standard replacements. This produces legal quiet Kinetic-main TLs while preserving meaningful Projectile research through ammunition/PDS/branch unlocks.

### Energy Weapons
**Assessment: revise branch/default labeling and TL9 name.** Tunable/free-electron and extreme-frequency beams remain specialist branches, not automatic replacements. The TL9 beam is renamed Pinnacle coherent-energy lance so matter-conversion-era reactor science does not imply a weapon that converts the target's matter. Particle/ion/plasma and rare one-off weapons remain distinct branches.

### Missile Weapons
**Assessment: revise TL8-TL9 delivery.** Delivery, guidance, warhead, and AMM axes remain separate. TL8 field-assisted terminal maneuver is promoted as a bounded branch with explicit geometry/track/PDS guardrails. TL9 becomes an integrated field-coupled strike vehicle: a true player-developed pinnacle that remains on-map and interceptable. Matter-conversion warheads and tactical micro-jump delivery remain deferred.

## Support/AUX review

The current catalog now includes the Storyboard's omitted Shield-support candidates and the previously preserved Probe / Survey Drone Package. The probe package passes the KISS test because it directly changes exploration/survey capability while avoiding a probe-fleet management layer. The Hangar / Mission Bay remains deliberately unplaced within its TL2-TL6 window; one starting shuttle remains settled and later Hull/hangar capacity is still a future component/Hull progression decision.

## Runtime/tooling boundary

Star Cluster's **production game/runtime remains C# for Godot**. Python is explicitly permitted for simulation, research, analysis, testing, and checkpoint validation. The production boundary is therefore tested directly (no Python runtime dependency in `StarCluster.Game` / `StarCluster.Core`) rather than treating Python itself as forbidden development tooling.

## Numerical boundary and next work

CP108 is the last qualitative whole-ladder architecture pass recommended before controlled numerical work. After native acceptance and human review, numerical calibration should proceed in bounded subsystem slices, reusing the standing mixed-TL/nonadjacent-TL integration infrastructure and preserving these branch/default/expression distinctions. Whole-ladder population-weighted results should remain screening evidence rather than automatic promotion criteria.
