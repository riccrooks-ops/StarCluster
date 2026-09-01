# Checkpoint 25 - TL1 Deterministic Layered Damage, Power, and Phase A Scenario Foundation

## Purpose

Checkpoint 25 is the first executable implementation of the Checkpoint 24 TL1 calibration foundation. It adds authoritative engine-independent mechanics and a baseline-driven deterministic scenario corpus while deliberately stopping before stochastic duel balance.

Checkpoint 24 remains the accepted conceptual, schema, and exact numerical foundation. Checkpoint 25 proves that the first rules can be represented consistently in Core, asserted through headless scenarios, and added without changing the accepted moving-missile runtime.

## Stable Checkpoint 25 contracts

- `SC25_DAMAGE_ORDER=SPEN_SA_SHIELD_APEN_AP_AI_AP_HULL`
- `SC25_ARMOR_AP=ONCE_PER_PACKET_PER_LAYER`
- `SC25_SHIELD_RECHARGE=TURN_START_BASE_PLUS_SPENT_TACTICAL`
- `SC25_POWER_LEDGER=AVAILABLE_POWERED_SPENT_WITH_EARMARKS`
- `SC25_POWER_SHUTDOWN=EFFECT_ENDS_POWER_REMAINS_LOCKED`
- `SC25_REACTOR=CONDITION_OUTPUT_TURN_ENVELOPE_OVERLOAD_STRAIN`
- `SC25_WEAPON_PACKETS=SAFE_KINETIC_ENERGY_MISSILE_RESOURCES`
- `SC25_CHARGING=SPENT_PROGRESS_READY_RETENTION_SAFE_DISCHARGE`
- `SC25_RESETS=TURN_REFRESH_AND_FTL_ONLY`
- `SC25_SCENARIO_CORPUS=12_DOCUMENTS_54_CASES`
- `SC25_BALANCE_CLAIM=NONE_PHASE_A_FIDELITY_ONLY`

## Core implementation

### Layered damage

New types under `src/StarCluster.Core/Combat/Damage/` implement:

- immutable `AttackPacket` DAM, SPEN, and APEN;
- mutable armor layers with pristine/current AP and AI;
- Shield Capacity, Shield Armor, temporary overcapacity, Hull, and multiple armor layers;
- exact packet resolution and detailed per-layer results;
- Hull overkill reporting;
- turn-start Shield recharge with Operational, Degraded, Disabled, and Destroyed profiles.

The resolver applies Shield Armor only to shield-facing damage after SPEN bypass, evaluates AP once per packet per layer, applies net damage to AI and then AP, and passes remaining damage forward.

### Tactical Power

New types under `Combat/Power/` implement:

- one Turn Power Envelope;
- Available, Powered, Spent, and earmarked accounting;
- increasing a sustained system with remaining spendable power;
- voluntary shutdown or disablement ending the effect without releasing locked power;
- same-turn reactivation prohibition;
- held-power conversion to Spent on trigger or release when unused;
- turn and FTL ledger clearing;
- Main Reactor output by condition;
- once-per-turn overload;
- automatic safe overload at or below the Strain Limit;
- forced d100 overload beyond the limit;
- success, failure, critical success, and critical failure outcomes.

Mid-turn source damage is asserted by the Phase A runner: the current ledger remains unchanged, while the next `BeginTurn` uses the new condition output.

### Weapons and charging

New types under `Combat/Weapons/` implement:

- kinetic, energy, missile, and hybrid family identifiers;
- exact packet, Tactical Power, ammunition, and pristine-ammunition profiles;
- power/ammunition spending whether a declared shot hits or misses;
- charging progress through one consecutive Spent payment per required turn;
- incomplete progress resets when a required turn passes without payment;
- Ready state after the final payment, with that payment covering firing during the same turn;
- optional indefinite or capped retention upkeep, paid before a carried Ready weapon may fire on a later turn;
- firing or stopped retention safely discharging the charge;
- Disabled/Destroyed component safe discharge;
- FTL transition clearing charge and Ready state.

Checkpoint 25 executes safe low/standard energy modes. Energy-weapon overload is intentionally excluded until its additional power, Strain, once-per-turn use, and forced-failure behavior are implemented together.

## ScenarioRunner implementation

`src/StarCluster.ScenarioRunner/TL1/` adds:

- a robust CSV baseline loader with source SHA-256 `50316e0528f5e80a16957017ecf407ce4655c40d57dc9e077d09d0d86e19bd7a`;
- exact TL1 fixture factories;
- typed operation documents;
- preflight validation;
- deterministic operation execution;
- recursive expected-subset comparison;
- per-scenario JSON and readable result output;
- corpus execution and summary reporting.

New commands:

```text
tl1-phase-a-single <scenario.json>
tl1-phase-a
tl1-phase-a-preflight
```

Default inputs:

- baseline: `docs/design/player_technology/tl1_core_combat_numerical_baseline_v0_1.csv`;
- corpus: `src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/`;
- output: `out/checkpoint-25-tl1-phase-a/`.

## Executable Phase A corpus

The 12 scenario documents contain 54 cases:

| Matrix row | Subject | Cases |
|---|---|---:|
| TL1-A01 | shield bypass, SA, capacity, overflow | 5 |
| TL1-A02 | AP, AI, multiple layers, Hull, overkill | 5 |
| TL1-A03 | turn-start Shield recharge | 6 |
| TL1-A04 | one-way power and earmarks | 4 |
| TL1-A05 | powered-system shutdown / disable lock | 2 |
| TL1-A06 | unused held interception | 2 |
| TL1-A07 | triggered held interception | 2 |
| TL1-A08 | mid-turn Reactor condition and next refresh | 3 |
| TL1-A09 | safe, forced, failed, and critical overload | 7 |
| TL1-A10 | Turn Refresh and FTL reset | 2 |
| TL1-A11 | safe weapon family resource packets | 5 |
| TL1-A12 | charging, retention, discharge, consecutive-payment enforcement, non-retaining auto-discharge, and FTL | 11 |

The corpus includes edge and rejection cases, not only successful nominal actions.

## Data and documentation

Checkpoint 25 adds or promotes:

- Concept v0.3w and Decisions D-233 through D-240;
- `Component_State_And_Profile_Schema_v0_2.md`;
- `TL1_Core_Combat_Test_Plan_v0_2.md`;
- `tl1_phase_a_scenario_schema_v0_1.json`;
- `tl1_core_combat_test_scenarios_v0_2.csv` with 62 rows and runtime linkage;
- `StarCluster_Player_TL_Framework_Draft_v0_5.xlsx` with a Phase A Runtime sheet;
- updated foundation, architecture, TODO, README, checkpoint, and validation records.

The 117-value numerical baseline and 13 reusable loadouts remain unchanged.

## Automated coverage

Checkpoint 25 adds 56 engine-independent unit tests over layered damage, Shield recharge, Tactical Power, Reactor overload, weapon resources, and charging. Combined with the accepted suite, the expected Windows total is 562 tests.

Acceptance also retains:

- seven deterministic moving-missile scenarios;
- 46 ScenarioRunner self-tests;
- the complete reference-library hash contract;
- clean warnings-as-errors compilation.

## Validation boundary

Passing Checkpoint 25 means:

- Core arithmetic and state contracts compile and pass;
- all 54 Phase A cases match their accepted expected subsets;
- the exact baseline used is traceable by hash;
- the existing missile runtime and ScenarioRunner infrastructure remain regression-safe;
- documentation and machine-readable data agree.

It does not mean:

- TL1 weapon values are balanced;
- direct-fire hit, initiative, endpoints, doctrine, or Damage Control are complete;
- optional systems are implemented;
- Phase B Monte Carlo may begin without its explicit contracts.

## Next pass

Define and implement the Phase B duel contract. Start with K/K only after fixing initiative, Firm-track hit resolution, commitment ordering, endpoints, doctrine, metrics, side-swapped common random numbers, and moving Missile Flight compatibility. Then add E/E, M/M, and cross-family pairings incrementally.
