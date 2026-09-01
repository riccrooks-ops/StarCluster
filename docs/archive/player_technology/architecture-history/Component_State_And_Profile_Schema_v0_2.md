# Component State and Profile Schema v0.2

**Checkpoint 25 status:** implemented Core-state foundation plus extensible design schema. Fields remain removable when testing shows they do not support visible gameplay.

## Design goals

- Keep a compact shared component identity.
- Add only the optional profile blocks a subsystem actually uses.
- Separate pristine design data, persistent current state, derived values, and turn-local state.
- Calculate derived values rather than storing duplicate state.
- Keep ordinary subsystem capabilities internal unless an explicit external prerequisite creates a meaningful installation or damage decision.
- Preserve exact test inputs and stable IDs while allowing display names and balance values to change.

## Shared component identity

Every installed component may provide:

- `component_id`
- `display_name`
- `component_family`
- `subtype`
- `technology_level`
- `size_or_capacity_cost`
- `installation_requirements`
- `compatibility_requirements`
- `capability_tags`
- `valid_installation_locations`
- `special_traits`

The shared record does not contain every possible weapon, shield, sensor, reactor, or movement field.

## State classes

### Pristine installed state

The undamaged installed profile after permanent installation modifiers:

- pristine integrity or capacity;
- pristine output, range, rating, movement, ammunition, or storage;
- pristine Strain Limit;
- pristine Crew or Marine capacity where applicable;
- field-repair ceiling when lower than the pristine maximum.

### Persistent current state

Saved through Turn Refresh and FTL transition:

- component condition;
- current integrity, capacity, ammunition, fuel, battery charges, and capacitor charge;
- current Strain;
- current Crew and Marines;
- weapon charge progress and Ready state when retention is legal;
- persistent damage effects and current field-repair ceiling.

### Derived state

Calculated from pristine data, condition, installed modifiers, current power, operating mode, overload, and situational effects:

- reactor output;
- effective STL Move and tractor resistance;
- current ECM/ECCM rating;
- active-sensor range;
- current Shield Armor;
- effective weapon packet;
- available Auxiliary capacity;
- repair difficulty.

Derived values should not be independently saved unless an explicit snapshot or replay contract requires them.

### Turn-local state

Cleared by Turn Refresh unless stated otherwise:

- Turn Power Envelope;
- Powered and Spent Tactical Power;
- held-power earmarks;
- overload-used flags and temporary overload benefits;
- temporary Shield overcapacity;
- Evasive Maneuvering and temporary movement bonuses;
- held-fire orders;
- tractor locks;
- voluntary-shutdown and same-turn reactivation flags.

FTL transition additionally clears encounter-specific state and all charging / Ready weapon state, but does not repair, replenish, or remove Strain.

## Deterministic effect precedence

Apply effects in this order unless a component explicitly overrides it:

1. pristine component profile;
2. component condition;
3. permanent installation and Auxiliary modifiers;
4. current Powered level;
5. selected safe operating mode;
6. overload benefit;
7. external situational effects;
8. explicit final caps.

The same effect from the same source never stacks with itself. Different sources combine only when their profiles permit it.

## Optional profile blocks

### Power profile

- core-power behavior;
- Powered levels and cost per level;
- Spent action and upkeep costs;
- maximum safe operating level;
- legal power-adjustment opportunities;
- shutdown and same-turn reactivation rules;
- Emergency Tactical Output restrictions.

### Layered-defense profile

- pristine and current Shield Capacity;
- Shield Armor;
- base and Tactical recharge;
- collapse and recovery rules;
- temporary overcapacity overload;
- armor-layer AP and AI;
- Hull Integrity;
- repair ceilings.

### Weapon profile

- family and stable weapon ID;
- range and accuracy profile;
- DAM, SPEN, and APEN packet;
- safe output modes;
- Tactical Power and ammunition costs;
- magazine capacity;
- firing and interception eligibility;
- valid target classes;
- Degraded profile;
- secondary-hazard traits.

### Charging profile

- required consecutive charging turns;
- Spent Tactical Power per charging turn;
- Ready-state retention allowed;
- retention upkeep;
- maximum normal retention, if any;
- forced-retention option, if any;
- safe discharge behavior;
- condition and FTL reset behavior.

### Reactor and stored-power profile

- Operational and Degraded output;
- Emergency Tactical Output;
- core-power capability;
- overload output and Strain;
- battery discharge amount, charges, and per-turn limit;
- capacitor capacity, charge rate, discharge rate, and operation limit;
- APU core-only capability.

### Sensor and EW profile

- passive sensor capability;
- active-sensor range levels;
- active-sensor overload range;
- ECM and ECCM maximum ratings;
- power per rating;
- Sensor/EW Refresh behavior;
- cloak profile and restrictions.

### Propulsion and tractor profile

- pristine and Degraded STL Move;
- fuel cost;
- Evasive Maneuvering costs and effect;
- STL overload Move bonus;
- tractor acquisition profile;
- Tractor Power, maximum, and maintenance cost;
- hold/pull behavior;
- valid target classes.

### Personnel profile

- Crew Capacity, pristine Crew, current Crew, and Minimum Operating Crew;
- Crew casualty stage;
- Marine Capacity, pristine Marines, and current Marines;
- derived Total Personnel.

### Condition and repair profile

- Operational, Degraded, Disabled, and Destroyed behavior;
- current value and repair ceiling;
- repair difficulty and material cost;
- full-facility restoration behavior;
- interactions with maximum-raising Auxiliary components.

### Overload and Strain profile

- overloadable flag;
- named overload modes;
- benefit, duration, and declared resources;
- Strain gained and Strain Limit;
- forced-overload success threshold;
- critical-success and critical-failure effects;
- damage and secondary-hazard interaction.

## Checkpoint 25 runtime mapping

Checkpoint 25 implements the following engine-independent Core types:

| Contract | Core type |
|---|---|
| Component condition | `Combat/Components/ComponentCondition.cs` |
| Attack packet | `Combat/Damage/AttackPacket.cs` |
| Armor layer persistent state | `Combat/Damage/ArmorLayerState.cs` |
| Layered defense persistent state | `Combat/Damage/LayeredDefenseState.cs` |
| Layered packet resolution | `Combat/Damage/LayeredDamageResolver.cs` |
| Turn-start Shield recharge | `Combat/Damage/ShieldRechargeService.cs` |
| Tactical Power ledger | `Combat/Power/TacticalPowerLedger.cs` |
| Reactor condition, output, overload, and Strain | `Combat/Power/ReactorState.cs` |
| Weapon packet and resource state | `Combat/Weapons/WeaponState.cs` |
| Charging and Ready-state lifecycle | `Combat/Weapons/ChargedWeaponState.cs` |

The ScenarioRunner adapters under `src/StarCluster.ScenarioRunner/TL1/` load exact baseline values and materialize synthetic deterministic fixtures. They do not become the authoritative owner of Core combat rules.

## Deliberately deferred runtime blocks

Checkpoint 25 does not yet implement:

- stochastic direct-fire hit resolution;
- full ship condition, Crew-casualty, or Damage Control state machines;
- energy-weapon overload Strain;
- PDS, ECM/ECCM, Active Sensors, batteries, capacitors, Auxiliary Reactors, APUs, tractors, EvM, or movement integration;
- Phase B duel initiative, doctrine, endpoint, and paired Monte Carlo contracts.

These blocks remain represented in the design schema and exact scenario matrix, but implementation proceeds only when the preceding deterministic layer passes.
