# Checkpoint 24 - Unified Tactical Power, Component State, and TL1 Core-Combat Test Foundation

## Purpose

Checkpoint 24 is a documentation, schema, and test-foundation checkpoint built on the accepted Checkpoint 23a repository. It reconciles every material design decision accepted after Checkpoint 23a, replaces legacy power terminology and rerouting assumptions, and establishes one exact provisional TL1 numerical baseline with controlled loadouts and staged scenarios.

This checkpoint changes no runtime combat mechanics. Checkpoint 22d remains the accepted mechanical and performance baseline. Checkpoint 21e remains the frozen Monte Carlo behavioral reference. Checkpoint 23 remains the accepted player-technology and reference-mining foundation.

## Stable Checkpoint 24 contracts

- `SC24_POWER_STATES=AVAILABLE_POWERED_SPENT`
- `SC24_POWER_FLOW=ONE_WAY_UNTIL_TURN_REFRESH`
- `SC24_POWER_OPPORTUNITIES=PRE_MOVEMENT_PRE_DIRECT_FIRE_PRE_MISSILE_PRE_DAMAGE_CONTROL`
- `SC24_REACTOR_ENVELOPE=POST_DAMAGE_CONTROL_TURN_SNAPSHOT`
- `SC24_SHIELD_RESISTANCE=SHIELD_ARMOR_SA_AFTER_SPEN`
- `SC24_RESET_MODEL=TURN_REFRESH_AND_FTL_ONLY`
- `SC24_COMPONENT_STATE=PRISTINE_PERSISTENT_DERIVED_TURN_LOCAL`
- `SC24_COMPONENT_SCHEMA=SHARED_CORE_PLUS_OPTIONAL_PROFILES`
- `SC24_PERSONNEL=CREW_PLUS_MARINES_WITH_THREE_CREW_STAGES`
- `SC24_TEST_BASELINE=EXACT_PROVISIONAL_TL1_CORE_COMBAT_V0_1`
- `SC24_BALANCE_GOAL=SITUATIONAL_VIABILITY_NOT_FORCED_EQUALITY`

## Concept v0.3v

The living Concept now records:

- one player-facing Tactical Power pool with Available, Powered, and Spent point states;
- one-way power flow within a turn, no refund after voluntary shutdown or component failure, and no same-turn restart unless explicit;
- four optional power-adjustment opportunities before Movement, Direct Fire, Missile / Interception, and Damage Control;
- one prospective Sensor/EW Refresh after all boundary changes are finalized, with no retroactive recalculation or point-by-point probing;
- a Turn Power Envelope fixed from post-Damage-Control source conditions for the current turn;
- immediate loss of a damaged component's effect without reclaiming its locked power;
- concurrent Main and Auxiliary Reactors, core-only APUs, Emergency Tactical Output, finite Combat Batteries, reusable Capacitor Banks, and finite Shield Batteries;
- scalable simultaneous ECM and ECCM, range-scaled Active Sensors, non-overloadable Passive Sensors, and rare fixed-profile cloaks;
- self-contained PDS with local tracking and fire control;
- Shield Armor (SA) as specialized resistance to shield-facing damage after SPEN bypass;
- Shield Hardener, generator overcapacity, collapsed-shield recovery acceleration, and fixed battery-discharge contracts;
- kinetic, energy, missile, hybrid, charged, retained, and held-interception weapon identities;
- component-specific magazine and containment hazards plus explicit Auxiliary mitigation;
- once-per-component-per-turn overload, automatic safe overload, Forced Overload only beyond the Strain Limit, and Damage Control Strain removal;
- ordinary STL, EvM, STL overload, tractor hold/pull, deferred Emergency FTL Jump, and rare cloak boundaries;
- Turn Refresh and FTL transition as the only universal reset events;
- pristine installed, persistent current, derived, and turn-local state classes plus deterministic effect precedence;
- modular subsystem profiles around a compact shared component core;
- pristine maximums, current values, and optional field-repair ceilings;
- separate Crew and Marine counts, Total Personnel, Minimum Operating Crew, and three broad Crew casualty stages plus Below Minimum;
- hybrid TL progression through modest statistics, efficiency/integration gains, and qualitative milestones; and
- an exact TL1 calibration ladder that begins with stripped identical cruisers and adds one variable at a time.

## Exact provisional TL1 foundation

Checkpoint 24 introduces four authoritative machine-readable files under `docs/design/player_technology/`:

- `tl1_core_combat_numerical_baseline_v0_1.csv` - 117 exact provisional parameters;
- `tl1_core_combat_loadouts_v0_1.csv` - 13 controlled chassis/loadout fixtures;
- `tl1_core_combat_test_scenarios_v0_1.csv` - 60 staged deterministic and Monte Carlo scenarios;
- `player_tl_design_reconciliation_v0_2.csv` - 24 reconciled design topics.

The same data and Checkpoint 24 decision register are presented in `StarCluster_Player_TL_Framework_Draft_v0_4.xlsx`.

The stripped TL1 core chassis begins with:

- Hull 12;
- passive armor AP 2 / AI 6;
- Shield Capacity 6;
- Main Reactor output 5 TP;
- STL Move 4;
- Fuel 24;
- passive sensor Firm range 3 / Approximate range 5;
- Crew 100;
- Marines 10;
- Minimum Operating Crew 10;
- Damage Control Capacity 2;
- Repair Supplies 6; and
- one Weapon Bay.

The first weapon variants are a kinetic cannon, energy cannon, and missile launcher. Optional TL1 PDS, Shield Hardener, Shield Battery, ECM, ECCM, Active Sensors, reactor overload, Combat Battery, Capacitor Bank, Auxiliary Reactor, APU, personnel/damage, movement, EvM, STL overload, tractor, held-interception, and retreat scenarios are introduced only in later controlled layers.

All values are explicit test inputs, not promoted production balance.

## Test philosophy

The first implementation must preserve experimental isolation:

1. Validate deterministic arithmetic and state contracts.
2. Run symmetric K/K, E/E, and M/M mirror duels with paired side-swapped seeds.
3. Run every cross-family pairing under the same doctrine.
4. Add exactly one optional subsystem or changed rule at a time.
5. Test each countermeasure in irrelevant, relevant, and heavy-threat contexts.
6. Separate component value from the value of simply adding reactor output.
7. Introduce family-specific doctrine only after identical doctrine exposes inherent behavior.

The goal is not equal performance in every matchup. Each option must have a clear purpose and remain viable in its intended region of the parametric space without becoming dominant, oppressive, redundant, or a trap.

## Documentation and schema records

- `docs/Star_Cluster_Game_Concept_v0.3v.docx`
- `docs/design/player_technology/Hull_Armor_Shields_And_Tactical_Power_Foundation.md`
- `docs/design/player_technology/Component_State_And_Profile_Schema_v0_1.md`
- `docs/design/player_technology/TL1_Core_Combat_Test_Plan_v0_1.md`
- `docs/design/player_technology/StarCluster_Player_TL_Framework_Draft_v0_4.xlsx`
- `docs/design/player_technology/tl1_core_combat_numerical_baseline_v0_1.csv`
- `docs/design/player_technology/tl1_core_combat_loadouts_v0_1.csv`
- `docs/design/player_technology/tl1_core_combat_test_scenarios_v0_1.csv`
- `docs/design/player_technology/player_tl_design_reconciliation_v0_2.csv`
- `docs/Prototype_TODO.md`

The schema deliberately uses optional subsystem profile blocks rather than one universal record with mostly empty fields. Testing may add, remove, or simplify fields when evidence shows that they do or do not support visible gameplay.

## Validation boundary

Checkpoint 24 requires:

- exact complete-repository manifest verification;
- native Windows PowerShell parsing and runtime preflight;
- one active Concept v0.3v with v0.3u archived;
- one active Checkpoint 24 validation runbook with Checkpoint 23a archived;
- exact CSV headers and row counts: 117 baseline, 13 loadouts, 60 scenarios, 24 reconciliation rows;
- workbook v0.4 sheets for the baseline, loadouts, test matrix, schema, plan, reconciliation, and decisions through D-232;
- required Checkpoint 24 design markers and terminology;
- clean warning-as-error .NET build;
- all 506 engine-independent tests;
- seven deterministic ScenarioRunner scenarios; and
- 46 ScenarioRunner self-tests.

No Godot mechanics or Monte Carlo calibration run is required because runtime behavior is unchanged.

## Next pass

Implement Phase A deterministic TL1 core-combat contracts from the exact Checkpoint 24 baseline. Only after those contracts pass should the project implement paired Phase B mirror and cross-family duels. Optional systems, differentiated doctrine, movement, and TL2-TL9 progression remain staged behind that evidence.
