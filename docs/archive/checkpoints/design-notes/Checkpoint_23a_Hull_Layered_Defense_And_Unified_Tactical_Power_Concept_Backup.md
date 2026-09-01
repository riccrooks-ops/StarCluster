# Checkpoint 23a - Hull, Layered Defense, and Unified Tactical Power Concept Backup

## Purpose

Checkpoint 23a is a documentation-only backup checkpoint built on the accepted Checkpoint 23 Revision 3 repository. It captures the material design decisions reached before the foundational numerical calibration pass. It changes no runtime combat mechanics and promotes no numerical TL values.

Checkpoint 23 remains the accepted player-technology/reference-mining framework. Checkpoint 22d remains the accepted mechanical/performance baseline. Checkpoint 21e remains the frozen behavioral reference.

## Stable documentation contracts

- `SC23A_HULL_MODEL=STRUCTURAL_PLATFORM_WITH_BOUNDED_ENGINEERED_SELF_REPAIR`
- `SC23A_ARMOR_MODEL=LAYERED_AP_AI_SINGLE_CALCULATION_PER_LAYER`
- `SC23A_SHIELD_MODEL=RENEWABLE_CAPACITY_WITH_OPTIONAL_SHIELD_PROTECTION`
- `SC23A_TACTICAL_POWER_MODEL=ONE_POOL_AVAILABLE_COMMITTED_CONSUMED`
- `SC23A_RECHARGE_TIMING=START_OF_TURN_BASELINE_END_OF_TURN_COMPARISON`
- `SC23A_ORGANIC_HULL_POLICY=ALIEN_PRECURSOR_OR_RARE_BIOTECH`

## Concept v0.3u

The living Concept now records:

- Hull TL as the quality of the cruiser structural platform, including bounded Hull durability, STL/FTL stress tolerance, compartmentation, internal-space efficiency, integration, and repairability;
- engineered high-TL self-sealing or bounded reconstruction for the player ladder, while truly organic hulls remain alien, Precursor, or rare biotechnology;
- attack packages with DAM, SPEN, and APEN, any of which may be zero;
- one armor calculation per attack package and per armor layer;
- Net Damage applied to Armor Integrity, then Armor Protection, then the next layer or Hull;
- unchanged APEN across layers and no penetration-created damage;
- one primary passive armor AP/AI track with no component-condition track;
- one optional Auxiliary ablative outer layer with its own AP and AI;
- composite or reinforced armor as a modifier to the primary layer rather than another layer;
- standard renewable Shield Capacity with optional Shield Protection;
- turn-start Shield recharge as the initial baseline, with end-of-turn recharge retained for simulation comparison;
- one Tactical Power pool with Available, Committed, and Consumed point states;
- prospective release of Committed power and no refund of Consumed power;
- routine core power for computers and fire control, while those components remain damageable;
- consistent Operational, Degraded, Disabled, and Destroyed terminology, with Disabled always meaning out of commission;
- distinct Shield Battery, Shield Booster, Power Stabilizer, and Shield Hardener roles; and
- consecutive Tactical Power requirements for multi-turn charging.

## Detailed design records

- `docs/design/player_technology/Hull_Armor_Shields_And_Tactical_Power_Foundation.md`
- `docs/design/player_technology/Online_Reference_Review_Queue.md`

The online review queue includes the project owner's FTL wiki and community-strategy links, Galactic Civilizations, and other candidate comparative sources. They remain inspiration only; no proprietary names, data, tables, prose, events, formulas, or defining mechanics may be copied.

## Validation boundary

Checkpoint 23a requires:

- exact complete-repository manifest verification;
- native Windows PowerShell parsing and runtime preflight;
- sole active Concept v0.3u and archived v0.3t;
- sole active Checkpoint 23a validation runbook;
- reference-library, CSV, and workbook contracts inherited from Checkpoint 23;
- required Checkpoint 23a design markers and documents;
- clean warning-as-error .NET build;
- 506 engine-independent tests;
- seven deterministic scenarios; and
- 46 ScenarioRunner self-tests.

No mechanical Godot validation or Monte Carlo recalibration is required because no runtime mechanics changed.

## Next pass

Checkpoint 24 defines the smallest useful statistics and units for Hull, Armor, Shields, Reactor/Tactical Power, FTL, and STL; drafts TL 1/3/5/7/9 anchor alternatives; and builds the simulation matrix for layered defense, Shield recharge timing, Tactical Power decisions, compatibility, and matched/mixed-TL reference cruisers.
