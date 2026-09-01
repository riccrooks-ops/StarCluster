# Player Technology Reference Mining and Design Reconciliation

**Checkpoint 23 status:** framework and reference-mining draft; no numerical TL balance is promoted to production rules.

## Purpose

This pass mines the preserved reference library for useful questions, naming patterns, subsystem relationships, tradeoffs, and presentation ideas before Star Cluster commits to player-technology numbers. The current Concept and Decision Register remain authoritative. External sources are evidence and inspiration, never specifications.

## Originality rule

Star Cluster may be influenced by the design problems other games solve, but it must solve them in its own way. Do not reproduce proprietary prose, art, distinctive names, exact technology ladders, construction tables, numerical progressions, formulas, combat matrices, or another game's defining core mechanics. Every adopted idea must be restated as an original Star Cluster decision and tested against KISS, the single-ship campaign, observer-safe information, and the intended fantastical space-opera tone.

## Main findings

### Keep the visible tree compact

The reference library demonstrates both the usefulness and the cost of detailed subsystem trees. Star Cluster retains ten broad player-facing research categories: Hull, Armor, Power, Propulsion, Sensors/EW, Computing/Fire Control, Shields, Kinetic/Projectile Weapons, Beam/Energy Weapons, and Missile Weapons. Multiple component families and capability tags may live under a category without becoming new visible trees.

### Use one Propulsion TL with separate FTL and STL components

Strategic interstellar travel and local tactical movement are distinct installed systems. They should have independent names, statistics, damage states, and possible Item TLs, while sharing one player-visible Propulsion research level. This preserves clarity and allows a refitted ship to carry, for example, a modern STL drive and an older FTL drive.

### Let categories advance independently

Research does not advance in lockstep. Compatibility is evaluated when a component is installed or operated. Most standard component families should depend on no more than two related support categories, plus any explicit physical or capability tags.

### Reserve Adapted for real space-opera engineering

Adapted equipment is neither ordinary integration nor arbitrary permission. A valid adapter, interface, converter, stabilizer, control core, or expert jury-rig makes the system usable at an explicit cost. The schema reserves visible Adaptation Strain accumulated during meaningful stress events, warning thresholds, and condition-step failure. Workshop adaptations are more stable than field jury-rigs.

A Skilled Chief Engineer may bridge a limited one-TL support shortfall or reduce strain. A Legendary Chief Engineer may bridge up to two TLs for one selected installation or create a temporary emergency jury-rig. No engineer can improvise missing bay volume, mount geometry, containment, an absent power form, or a non-emulatable capability tag.

### Progress through more than raw output

Technology levels may improve performance, efficiency, reliability, capacity burden, repairability, integration, or operating modes. Anchor TL 1, 3, 5, 7, and 9 first. Use TL 2, 4, 6, and 8 to mature the previous breakthrough or introduce a smaller but visible capability. TL 9 must be campaign-defining without becoming Precursor magic.

### Use references as both inspiration and warning

Detailed design systems provide valuable causal checklists, but Star Cluster should not become a construction worksheet. Comprehensive combat systems reveal possible sensor, EW, missile, damage, and logistics relationships, but they also show why the player-facing rule set must remain bounded. Compact games show that a few visible resources and states can create strong decisions, but Star Cluster retains its own map, turn, damage, and campaign structures.

## Artifacts

- `StarCluster_Player_TL_Framework_Draft_v0_3.xlsx` - review workbook.
- `player_tl_components_draft_v0_3.csv` - 99 standard named components, stable IDs, naming/mechanical promises, and source-influence tags.
- `player_tl_compatibility_profiles_draft_v0_3.csv` - 11 family-level support profiles and adaptation/engineer schema.
- `player_reference_library_v0_1.csv` - complete local reference inventory and originality policy.
- `player_reference_insights_v0_1.csv` - paraphrased source-to-design observations and adoption status.
- `player_tl_design_reconciliation_v0_1.csv` - current decisions after comparing the references to Star Cluster.

## Next calibration pass

1. Review and revise the current names, especially repeated use of `Metric`, without changing stable IDs.
2. Define units and fields for Hull, Armor, Shields, Power, FTL, and STL.
3. Draft TL 1/3/5/7/9 anchor values and reference cruisers.
4. Fill intermediate TLs with meaningful maturity or capability steps.
5. Test matched-TL and mixed-TL ships, including compatibility and power starvation.
6. Decompose Missile Flight subsystems only after the broader framework is stable.

## Checkpoint 23a reconciliation addendum

The post-Checkpoint-23 discussion established a more precise defensive and power foundation:

- Hull TL is the structural platform: bounded Hull durability, STL/FTL stress tolerance, compartmentation, internal-space efficiency, integration, and repairability. High player TLs may use engineered bounded self-repair; organic hulls remain alien, Precursor, or rare biotechnology.
- Every attack package may carry DAM, SPEN, and APEN. Penetration never creates additional damage.
- Primary armor uses AP and AI. Each layer resolves once per attack package; Net Damage removes AI, then AP, then passes inward. APEN retains the same value across layers.
- One Auxiliary ablative armor layer may have its own AP and AI and is normally expendable. Composite armor modifies the primary layer instead.
- Standard Shields remain renewable capacity. Optional Shield Protection may come from specialized equipment.
- Shield recharge uses a start-of-turn baseline after Tactical Power refresh, while end-of-turn recharge remains a comparison case.
- One Tactical Power pool uses Available, Committed, and Consumed states. Committed power may be rerouted prospectively; Consumed power cannot be recovered that turn.
- Computers and fire control use routine core power but remain damageable components.

These decisions narrow the Checkpoint 24 statistical schema without selecting numerical curves.
