# Component State and Profile Schema v0.1

**Checkpoint 24 status:** accepted conceptual schema; implementation may prune, split, or rename fields when runtime testing shows that a field is redundant.

## Purpose

Star Cluster needs consistent component records without one universal object full of irrelevant empty fields. Every component answers the same conceptual questions, but stores only the optional profile blocks used by its subsystem.

The schema separates:

1. immutable or installed pristine data;
2. persistent current state;
3. derived values;
4. turn-local tactical state; and
5. subsystem-specific optional profiles.

This separation is mandatory unless later implementation evidence supports a simpler representation.

## State ownership

### Installed pristine data

Pristine data describes the installed component or ship layer before damage and temporary modifiers.

Typical fields include:

- stable component ID and display name;
- component family and subtype;
- Item TL;
- installation location, bay, or Auxiliary-capacity cost;
- compatibility profile and required capability tags;
- pristine output, range, capacity, integrity, protection, rating, or movement;
- pristine Strain Limit;
- pristine ammunition, charge, fuel, personnel, or storage capacity;
- component traits and hard blockers.

Pristine values are the normal restoration ceiling. A component, Hull, armor layer, shield, magazine, or personnel space cannot be repaired or replenished above its installed maximum unless an explicit functioning modifier raises that maximum.

### Persistent current state

Persistent state survives turn refreshes and FTL transitions unless a specific rule says otherwise.

Examples:

- current component condition;
- current Hull, Armor Integrity, Armor Protection, and Shield Capacity;
- current field-repair ceiling;
- current ammunition, fuel, battery charges, capacitor charge, Repair Supplies, Crew, and Marines;
- current Strain;
- current charging progress and Ready state when the weapon permits retention;
- persistent damage, adaptation, or repair effects;
- elapsed retention turns when the component has a maximum.

### Derived values

Derived values are recalculated from authoritative source state and should not normally be saved independently.

Examples:

- effective Tactical Power output from all operating reactors;
- effective STL Move and tractor resistance;
- effective weapon attack profile after condition, firing mode, external targeting assistance, and overload;
- active ECM, ECCM, Shield Armor, PDS, or sensor range from current Powered levels;
- installed maximum after functioning Auxiliary modifiers;
- Total Personnel = Crew + Marines;
- current crew casualty stage;
- current installation state: Integrated, Adapted, or Incompatible.

### Turn-local tactical state

Turn-local state clears at Turn Refresh or at the specific earlier event defined by the component.

Examples:

- Available Tactical Power;
- current Powered levels and locked power;
- Spent Tactical Power;
- conditional held-fire power earmarks;
- once-per-turn overload-used flags;
- temporary overload benefits;
- temporary Shield overcapacity;
- Evasive Maneuvering and temporary STL bonuses;
- held-fire orders;
- tractor target and lock state;
- voluntary shutdown and same-turn reactivation prohibition;
- phase-local activation and resolution flags.

## Effect precedence

Unless a component explicitly defines another order, calculate its effective profile in this sequence:

1. pristine installed profile;
2. current condition profile;
3. permanent installation and functioning Auxiliary modifiers;
4. current Powered level;
5. selected normal operating mode;
6. overload benefit;
7. external situational effects;
8. final minimums, maximums, and caps.

The same named effect from the same source does not stack with itself. Different sources combine only when their rules permit it. Explicit exceptions override this default order.

## Common component core

Every installed component uses a compact common record:

- `component_id`
- `display_name`
- `component_family_id`
- `subtype_id`
- `item_tl`
- `installation_location`
- `capacity_cost`
- `compatibility_profile_id`
- `required_capability_tags`
- `non_emulatable_capability_tags`
- `special_traits`
- `current_condition`
- `repair_difficulty`

## Optional profile blocks

### Power profile

Use when a component consumes, provides, stores, or modifies Tactical Power.

- core-power behavior;
- Powered levels and cost per level;
- Spent action and upkeep costs;
- maximum normal Powered level;
- legal power-adjustment opportunities;
- shutdown behavior;
- same-turn reactivation rule;
- Emergency Tactical Output restrictions;
- one-operation-per-turn or discharge limits.

### Reactor and stored-power profile

- normal Tactical Power output;
- Degraded output;
- Emergency Tactical Output;
- core-power capability;
- overload output;
- battery charge count and discharge amount;
- capacitor capacity, charge rate, and discharge rate;
- charge/discharge windows.

Main and Auxiliary Reactors provide core power and Tactical Power simultaneously. An APU provides core power only. Installed Auxiliary Reactors are already connected to the ship; no default Backup Power Bus component is required.

### Weapon profile

- weapon family;
- local/manual targeting capability;
- external targeting-assistance eligibility;
- Accuracy, DAM, SPEN, APEN, and Maximum Range;
- normal and adjustable output modes;
- Tactical Power cost;
- ammunition family, cost, capacity, and Ready Package behavior;
- attack or cycle limit;
- held-interception eligibility;
- valid target classes;
- charging turns and charge cost;
- Ready-state upkeep and maximum retention;
- safe discharge behavior;
- secondary-hazard traits.

A weapon contains the local controls needed for ordinary operation. An external Targeting Computer may improve accuracy, but losing it does not disable an otherwise functional weapon unless that weapon explicitly requires external fire control.

### Defensive profile

- Shield Capacity and Base Recharge;
- Tactical recharge amount and per-turn cap;
- collapsed-shield and recovery behavior;
- Shield Armor supplied by the generator or hardener;
- temporary overcapacity overload;
- Armor Protection and Armor Integrity;
- Powered Armor or defensive-field behavior;
- field-repair ceiling.

### Sensor and electronic-warfare profile

- passive detection and discrimination envelopes;
- Active Sensor range settings;
- Active Sensor overload range;
- ECM and ECCM normal maximums;
- power per ECM/ECCM rating;
- prospective Sensor/EW Refresh behavior;
- cloak strength, restrictions, shutdown effects, and decloak penalties.

Active Sensor power increases range rather than intrinsic sensor accuracy. Passive Sensors and standard cloaks are not overloadable by default.

### PDS profile

- self-contained local fire control;
- valid threat classes;
- Powered readiness cost;
- Reaction Capacity;
- terminal windows;
- attack or interception chance inputs;
- ammunition family and consumption;
- per-shot power only when explicitly stated;
- Evasive Compensation.

### Propulsion and tractor profile

- pristine STL Move;
- movement fuel cost;
- Evasive Maneuvering power, fuel, and combat effects;
- STL overload Move bonus and costs;
- Degraded movement and fuel profile;
- tractor acquisition attack profile;
- Tractor Power and normal maximum;
- Powered maintenance cost;
- pull/hold behavior;
- valid target classes.

A tractor may hold or pull. It does not freely reposition a target. Multiple tractors combine to hold only; they do not combine into a multi-vector pull under the initial KISS rule.

### Personnel profile

Ship-level personnel state uses:

- Crew Capacity;
- pristine Crew complement;
- current Crew;
- Minimum Operating Crew;
- current Crew casualty stage;
- Marine Capacity;
- pristine Marine complement;
- current Marines;
- derived Total Personnel.

Crew and Marines are distinct countable units. Senior officers remain separate future entities.

### Condition and repair profile

- Operational behavior;
- Degraded behavior;
- Disabled behavior;
- Destroyed behavior;
- pristine maximum;
- current value;
- current field-repair ceiling;
- repair difficulty and eligible materials;
- full-facility restoration behavior.

If a functioning Auxiliary component raises a maximum and later loses function, immediately clamp the current value to the new valid maximum unless that component explicitly defines another transition.

### Overload and Strain profile

- overloadable: yes/no;
- overload modes;
- overload benefit and duration;
- additional power and fuel costs;
- Strain gained;
- Strain Limit;
- forced-overload target number and modifiers;
- critical-success effect;
- critical-failure effect;
- damage interaction.

Safe overload at or below the resulting Strain Limit succeeds automatically. An overload that would exceed the limit rolls before receiving the benefit. Failure provides no benefit. Declared resources and the overload opportunity are normally lost, and listed Strain is still applied, unless the component explicitly says otherwise.

### Hazard and mitigation profile

- Volatile Charge;
- Containment Failure;
- Explosive Magazine;
- Inert Ammunition;
- Insensitive Munitions;
- Safe Discharge;
- Armored Magazine interaction;
- collateral damage effect.

Hazards remain component-specific. There is no universal rule that every damaged weapon explodes.

### Reset profile

- Turn Refresh behavior;
- FTL-transition behavior;
- persistent-state exceptions.

The game has no universal “combat ended” reset. Turn Refresh clears power accounting and one-turn effects. FTL transition clears encounter-specific tactical states without repairing damage, restoring shields, replenishing resources, or removing Strain.

## KISS pruning rule

A field that does not support an implemented rule, a player-visible consequence, validation evidence, or save compatibility should be removed or deferred. Schema consistency is valuable; empty bookkeeping is not.
