# Hull, Armor, Shields, Tactical Power, and TL1 Test Foundation

**Checkpoint 25 status:** accepted conceptual foundation plus the first executable deterministic Core mechanics and Phase A scenario corpus. Balance remains provisional.

## Purpose

This document consolidates the Hull, layered-defense, Tactical Power, weapon-energy, overload, propulsion, personnel, and test-design decisions accepted after Checkpoint 23a. It replaces the earlier pre-calibration note while retaining its accepted armor and shield mathematics.

Exact numbers in the TL1 baseline are test inputs, not final progression values. The Concept and Decision Register remain authoritative. The companion CSVs and workbook make every test value and scenario traceable.

## KISS boundary

Star Cluster is a space-opera command game, not an engineering simulator.

- Use a small number of visible resources and reusable rules.
- Add detail only when it creates a meaningful decision or necessary causal explanation.
- Do not track heat, coolant, wiring, crew fatigue, departmental staffing, or electrical load as universal resources.
- Components contain their ordinary local controls, targeting, containment, and support unless an external prerequisite is explicit.
- External systems may enhance a component without being required for its basic function. A weapon can use local/manual targeting after the ship Targeting Computer is lost; it merely loses the computer's accuracy assistance.
- Prefer exact, versioned test values over undocumented ranges.

## State classes

### Persistent state

Persistent values survive Turn Refresh and FTL transition unless an explicit rule says otherwise:

- current Hull, Armor Integrity, Armor Protection, and Shield Capacity;
- component condition;
- current Strain;
- ammunition, fuel, battery charges, capacitor charge, and Repair Supplies;
- Crew and Marines;
- charging progress and Ready state when the weapon permits retention;
- field-repair ceilings and persistent damage effects.

### Derived state

Derived values are recalculated from authoritative sources rather than stored independently:

- current reactor output;
- effective STL Move and tractor resistance;
- effective sensor range, ECM, ECCM, Shield Armor, and weapon profile;
- installed maximums after functioning Auxiliary modifiers;
- Crew casualty stage;
- Total Personnel = Crew + Marines.

### Turn-local state

Turn-local values clear at Turn Refresh or their explicitly defined earlier endpoint:

- Available Tactical Power;
- Powered levels and locked power;
- Spent power;
- held-fire earmarks;
- overload-used flags and temporary benefits;
- Shield overcapacity;
- Evasive Maneuvering and temporary STL bonuses;
- held-fire orders and tractor locks;
- voluntary shutdown and same-turn reactivation restrictions.

There is no universal combat-end reset. The only universal reset events are Turn Refresh and FTL transition.

## Effect precedence

Unless an explicit component rule overrides it, apply effects in this order:

1. pristine installed profile;
2. condition profile;
3. permanent installation and functioning Auxiliary modifiers;
4. current Powered level;
5. selected normal operating mode;
6. overload benefit;
7. external situational effects;
8. final caps and floors.

The same effect from the same source does not stack with itself. Different sources combine only where their rules permit it.

## Pristine values and repair ceilings

Every repairable value distinguishes:

- pristine installed maximum;
- current value;
- current field-repair ceiling, where applicable.

Field repair cannot exceed the field ceiling or pristine installed maximum. A full drydock, starbase, or equivalent facility may restore the pristine maximum.

A functioning Auxiliary component may raise an installed maximum. If that modifier loses function, immediately clamp the current value to the new valid maximum unless the component explicitly defines another transition.

## Hull and armor

Hull TL remains the quality of the cruiser structural platform, not a change in ship class. It governs bounded durability, structural tolerance, compartmentation, service access, internal-space efficiency, integration, and repairability.

High player Hull TL may provide engineered self-sealing or bounded reconstruction that consumes eligible resources. It never restores a Destroyed ship or replaces component repair. Truly organic or freely regenerative hulls remain alien, Precursor, rare biotechnology, or campaign rewards.

### Attack package

Every attack package may carry:

```text
DAM   = Damage
SPEN  = Shield Penetration
APEN  = Armor Penetration
```

Either penetration value may be zero. Neither may create damage above DAM.

### Primary armor

For each armor layer reached:

```text
Effective AP = max(0, Current AP - APEN)
Net Damage   = max(0, Incoming Damage - Effective AP)
```

Apply Net Damage to:

```text
Armor Integrity -> Armor Protection -> next layer or Hull
```

Armor Protection is evaluated once for that layer and packet. AP is not recalculated after the same packet strips it. APEN keeps its original value across all reached layers. Primary passive armor has one AP/AI track and no component-condition track.

### Ablative and composite armor

- One optional Auxiliary ablative outer layer may have its own AP and AI.
- It resolves before primary armor and is normally nonrepairable in combat.
- Composite or reinforced armor modifies the primary layer rather than creating another layer.
- Armor-to-Hull compatibility remains comparatively relaxed and uses explicit mounting, capacity, repair, or adaptation costs instead of a universal relative-TL ban.

## Shields and Shield Armor

Standard shields are renewable Shield Capacity. Specialized equipment may provide **Shield Armor (SA)**, which resists shield-facing damage after SPEN bypass.

For one attack package:

```text
Shield Bypass       = min(DAM, SPEN)
Shield-Facing DAM   = DAM - Shield Bypass
Post-SA Damage      = max(0, Shield-Facing DAM - SA)
Shield Absorption   = min(Current Shield Capacity, Post-SA Damage)
Shield Overflow     = Post-SA Damage - Shield Absorption
Damage to next layer = Shield Bypass + Shield Overflow
```

SA does not reduce SPEN bypass and never adds capacity.

### Shield generator conditions

| Condition | Existing field | Recharge behavior |
|---|---|---|
| Operational | Retained | Full defined Base and Tactical recharge |
| Degraded | Retained | Explicit reduced recharge profile |
| Disabled | Retained until absorbed | No recharge; system is out of commission |
| Destroyed | Immediately collapses | None |

### Recharge timing

The initial baseline remains start-of-turn recharge:

1. refresh Tactical Power from the post-Damage-Control power sources;
2. apply Base Recharge;
3. choose Tactical Shield Recharge;
4. immediately mark recharge power Spent;
5. begin Movement.

End-of-turn recharge remains a comparison scenario rather than the current rule.

### Shield Hardener

A Shield Hardener is a Powered system that supplies SA. It may be activated or increased at a legal power-adjustment opportunity. Added SA applies prospectively. Power remains locked through Turn Refresh even if the hardener is shut down or Disabled.

A hardener may overload to exceed its normal SA maximum for the remainder of the turn. That overload costs the listed extra power and adds Strain.

### Shield Generator overload

An Operational noncollapsed generator may overload to create temporary Shield overcapacity above the installed maximum. The excess absorbs damage normally, cannot be restored once lost, and disappears at Turn Refresh.

A collapsed generator may instead overload to improve its next legal recovery. The baseline does not allow same-turn shield restart after collapse. An advanced explicit component may test that capability later.

### Shield Battery

A Shield Battery:

- uses finite fixed charges;
- has no Tactical Power cost to discharge;
- restores a fixed all-or-nothing amount;
- wastes restoration above the current maximum;
- normally permits one discharge per turn;
- is not overloadable;
- is an emergency reserve rather than a routine missing-shield refill;
- cannot restore expended charges without shipyard or drydock service.

A component with a higher discharge limit is not overloading; it simply has a different listed rate.

## One Tactical Power pool

The player sees one remaining Tactical Power total. Each point is in one of three player-facing states:

| State | Meaning |
|---|---|
| Available | Not yet powering a sustained system or spent on an action |
| Powered | Locked into an ongoing system or posture |
| Spent | Used for an immediate action or upkeep and unavailable until Turn Refresh |

The state flow is one-way during a turn:

```text
Available -> Powered
Available -> Spent
Available -> conditional held-fire earmark -> Spent if triggered
```

Powered or Spent power never returns to Available during the turn.

### Core power

Core power abstracts ordinary ship operation:

- life support;
- ordinary controls;
- computers and fire control;
- passive sensors;
- ordinary communications;
- routine component control, autoloading, and containment;
- normal STL/FTL operation already represented by drive and fuel rules;
- maintenance of an existing shield field;
- hangar and ordinary shuttle launch operations.

Core-powered components remain damageable.

### Power-adjustment opportunities

The initial legal opportunities are:

- before Movement;
- before Direct Fire;
- before Missiles / Interception;
- before Damage Control.

These are activation deadlines, not mandatory reallocation prompts. The interface should not stop the turn when no change is requested.

At a legal opportunity, the player may add Available power to an eligible system, use a permitted battery or capacitor, declare a persistent overload, or shut a system down. Shutting down immediately ends its effect but does not release its power. A voluntarily shut-down system normally cannot restart during the same turn.

No power adjustment occurs:

- between individual movement hexes;
- during a sensor calculation;
- during an attack package or committed volley;
- between PDS attempts in the same terminal sequence;
- retroactively after a result is known.

### Sensor/EW Refresh

After all sensor, ECM, and ECCM changes at a boundary are finalized, resolve one prospective Sensor/EW Refresh. Previous movement, observations, attacks, and locks are not recalculated. This allows delayed EW activation to matter without permitting repeated power probing.

### Disabled Powered component

If a Powered component becomes Disabled or Destroyed:

- its effect ends immediately for later resolution;
- its power remains locked and unusable until Turn Refresh;
- no mid-resolution power prompt occurs;
- previously resolved effects remain unchanged.

### Turn Power Envelope

At Turn Refresh, determine all current reactor contributions after prior Damage Control. Ordinary mid-turn reactor damage does not remove Available power, cancel Powered systems, reclaim Spent power, or invalidate paid charging stages. The new condition changes the next turn's output.

An explicit catastrophic bus-collapse or similar named effect may override this rule. Ordinary reactor damage does not.

## Power sources and storage

### Main and Auxiliary Reactors

Main and Auxiliary Reactors operate simultaneously. Each provides:

- core power while functional; and
- its listed Tactical Power contribution.

An Auxiliary Reactor remains connected and useful after loss of the main Reactor unless it is itself damaged or an explicit critical effect disrupts distribution. No default Backup Power Bus component is required.

A main- or Auxiliary-Reactor overload adds its listed Tactical Power for the current turn and Strain. Each reactor may overload independently once per turn.

### Reactor conditions

- Operational: listed full output.
- Degraded: listed reduced output.
- Disabled: main Reactor uses its listed Emergency Tactical Output; an ordinary disabled Auxiliary Reactor provides none.
- Destroyed: no output from that source.

Emergency Tactical Output replaces normal main-reactor output, refreshes each turn while Disabled, and cannot be overloaded.

Ordinary reactor destruction does not automatically damage an Auxiliary Reactor, APU, battery, or capacitor. Feedback or collateral damage requires an explicit critical, volatile, or overloaded-destruction effect.

### APU

An Auxiliary Power Unit supplies core operation only and contributes no flexible Tactical Power unless an advanced component explicitly says otherwise.

### Combat Battery

A Combat Battery:

- has finite charges;
- provides a fixed all-or-nothing amount of Available Tactical Power;
- normally permits one discharge per turn;
- loses any injected power still unused at Turn Refresh;
- does not recharge during battle unless explicitly stated.

### Capacitor Bank

A Capacitor Bank is reusable storage:

- charging Spends Tactical Power;
- stored charge persists between combat turns; completing FTL travel refills an installed bank to full capacity;
- discharge adds Available Tactical Power;
- capacity, charge rate, and discharge rate are fixed component values;
- one charge or discharge operation is allowed per turn by default.

The initial test permits charging at Turn Refresh or during Damage Control. Testing may narrow this to one window.

## PDS and held interception

### Self-contained PDS

A PDS installation includes its local tracking, fire control, weapon, and ordinary support. It does not require the main Targeting Computer or ship sensor to engage a valid local terminal threat unless its component explicitly says otherwise. An Operational or Degraded main Targeting Computer may nevertheless assist the local PDS solution by its listed bonus; Disabled, Destroyed, or absent main fire control provides no assistance.

PDS readiness is Powered. Individual attacks normally do not spend additional Tactical Power. Kinetic and AMM systems consume their listed ammunition per attempt; an energy PDS pays a higher Powered cost and normally has no conventional ammunition.

### Held main-weapon interception

A weapon placed on held interception:

- reserves its normal attack opportunity;
- follows its standard targeting, range, LOS, ammunition, and power rules;
- earmarks the required Available power for the selected firing mode;
- does not create a fourth power state.

If triggered, the earmarked power becomes Spent and ammunition is consumed. If the declared window closes unused, the earmark is removed and the power remains Available for later legal actions. The reserved weapon cycle is still lost for any earlier opportunity it deliberately skipped.

## Weapon families

### Kinetic

- finite ammunition;
- zero or minimal Tactical Power firing cost;
- conventional cannon may use zero power;
- railguns and mass drivers may use a small power cost;
- ammunition type normally changes during refit or other noncombat preparation, not mid-combat;
- explosive ammunition may cause magazine hazards, while inert projectiles normally do not.

### Energy

- higher Tactical Power cost;
- no conventional ammunition;
- may support defined safe output modes;
- may overload through one explicit weapon-specific mode;
- containment or power feedback may create component-specific secondary hazards.

### Missile

- no normal launch Tactical Power cost;
- finite Missile Flight supply;
- self-contained propulsion and payload;
- susceptible to PDS and held interception;
- magazines may explode when their explicit hazard applies.

### Hybrid and exotic

Hybrid systems combine explicit energy, ammunition, charge, and hazard costs. They do not receive every advantage automatically.

## Charging and Ready weapons

Each weapon defines:

- charge turns and beginning-of-turn payment;
- whether a completed charge may be retained;
- Ready-state upkeep;
- maximum normal retention, including indefinite retention when allowed;
- forced-retention availability;
- safe discharge and catastrophic hazards.

On the final charging turn, pay the final charge cost at Turn Refresh. The weapon becomes Ready and may fire that turn or later without another firing-power cost.

If retained, pay the listed Spent upkeep at the beginning of each later turn. Normal retention adds no Strain. Forced retention beyond a weapon's normal limit may add Strain when explicitly supported.

Stopping retention safely discharges the weapon. Firing discharges it through the attack. A Degraded weapon follows its own Degraded profile. Disabling or Destroying the charging component resets the charge. FTL transition clears all charging and Ready state.

Secondary hazards remain component-specific: Volatile Charge, Containment Failure, Explosive Magazine, Inert Ammunition, Safe Discharge, Insensitive Munitions, and Armored Magazine interactions.

## Overload and Strain

### Eligibility

Overload normally applies to systems that generate, channel, contain, or project substantial energy:

- Main and Auxiliary Reactors;
- energy and eligible hybrid weapons;
- Shield Generators and Shield Hardeners;
- STL drives and selected propulsion modes;
- tractor beams;
- ECM, ECCM, and Active Sensors;
- other explicitly identified energy systems.

It does not normally apply to:

- computers and Targeting Computers;
- passive armor or Hull;
- conventional kinetic weapons;
- missile launchers;
- passive sensors;
- fixed-capacity Shield or Combat Batteries;
- ordinary hangars and shuttles;
- standard cloaks.

Each component may overload once per turn unless its profile explicitly says otherwise. The effect may be persistent for the remainder of the turn or instantaneous for one action.

### Roll timing

When an overload is declared:

1. determine the resulting Strain;
2. if it remains at or below the component's Strain Limit, the overload succeeds automatically;
3. if it exceeds the limit, roll immediately before receiving the benefit.

A component above its limit does not roll for ordinary operation. Every later overload while above the limit requires another forced-overload roll.

### Results

- Success: overload works and listed Strain is applied.
- Failure: overload does not work; the opportunity and normally declared inputs are lost; listed Strain is still applied.
- Critical success: overload works with a favorable listed effect, commonly one less Strain.
- Critical failure: overload fails, Strain applies, the component normally worsens one condition step, and any explicit secondary hazard resolves.

The component profile may override whether an attempted resource is lost or whether the benefit partially occurs.

### Strain removal

Damage Control may assign a repair task to remove Strain. It competes with Hull and component repair, consumes the allocated material, and uses one roll. Full drydock or starbase servicing removes all Strain automatically. FTL transition does not remove Strain.

## Sensors, ECM, ECCM, and cloak

### Passive Sensors

Passive Sensors are core-powered and not overloadable by default.

### Active Sensors

Active Sensors are Powered at defined range settings. More power extends detection and discrimination range; it does not improve intrinsic sensor quality. Overload extends range beyond the normal maximum.

### ECM and ECCM

ECM and ECCM may run simultaneously. Each may be Powered at any integer level up to its component maximum, normally one power per rating point. Additional power may be added at a legal opportunity and remains locked. Overload may raise the rating above the normal maximum for the remainder of the turn.

### Cloak

A cloak is a rare Powered system, likely Precursor or similarly exceptional technology. It is not overloadable by default. A cloak may be shut down at a legal opportunity or by an incompatible action, but the locked power does not return and the cloak cannot reactivate during the same turn. Sensor, movement, firing, and decloak limitations remain component-specific and deferred.

## Propulsion and tractors

### Ordinary movement

Installed STL and FTL drives provide ordinary movement using their fuel rules. They do not consume Tactical Power merely to operate normally.

### Evasive Maneuvering

Evasive Maneuvering:

- is declared before Movement;
- Spends its listed Tactical Power;
- consumes additional fuel;
- grants its listed defensive effect for the remainder of the turn;
- imposes its existing offensive penalties unless compensated;
- adds no Strain by default.

An overloaded EvM is not a universal rule. A particular drive may offer it as an alternative overload mode. Early drives may choose Emergency Thrust or overloaded evasion, not both.

### STL overload

STL overload adds the drive's listed Move for the current turn, consumes additional fuel and power, and adds Strain. The higher effective Move also increases resistance to tractor effects. It does not automatically improve Evasive Maneuvering.

A Degraded drive uses its explicit profile. Reduced Move and increased fuel may both apply, but their severity must be tuned because they are a double penalty.

### Emergency FTL Jump

Unsafe combat escape is a separate future procedure, not ordinary FTL overload. Candidate costs include concentrated Tactical Power, core-only operation during spin-up, no movement or weapons, interruption risk, FTL Strain or damage, and a random arrival among mapped valid systems. Extra fuel is not required by default. Exact rules remain deferred.

### Tractor beam

A tractor is a beam weapon. It uses normal acquisition and remains Powered while maintaining the lock.

```text
Remaining target Move = max(0, effective target STL Move - applied Tractor Power)
```

- below target Move: the target may move normally with the remaining allowance;
- equal to target Move: the target is held;
- above target Move: excess may pull the target that many hexes toward the tractor source;
- tractor action is hold or pull, not arbitrary repositioning;
- multiple tractors add their power but may only hold under the initial KISS rule;
- overload may exceed the tractor's normal maximum;
- ships and explicitly listed movable units are valid; stars, planets, moons, anomalies, jump points, terrain, and other stellar/environmental features are not.

## Crew and Marines

Crew and Marines are distinct countable resources:

- Crew operates and repairs the ship;
- Marines board, repel boarders, and secure captured vessels;
- Total Personnel is derived as Crew + Marines;
- Senior Officers remain a future separate system.

The TL1 test baseline begins with:

- Crew 100;
- Marines 10;
- Minimum Operating Crew 10.

Crew casualties occur through explicit meaningful events and chunks, not as a percentage automatically tied to Hull loss.

The initial three stages are:

| Crew | Stage | Initial effect |
|---|---|---|
| 51–100 | Effective | No general penalty |
| 21–50 | Reduced | -10 percentage points to Damage Control |
| 10–20 | Critical | -20 Damage Control and -1 Damage Control Capacity |
| 0–9 | Below Minimum | Core/emergency operation only; no normal Damage Control |

These effects are exact provisional test values, not final crew balance.

## Reset rules

### Turn Refresh

Turn Refresh:

- generates the new Tactical Power pool from current sources;
- clears prior Powered and Spent accounting;
- clears held-fire earmarks and orders;
- ends one-turn overload benefits, Shield overcapacity, Evasive Maneuvering, temporary STL bonuses, and tractor locks;
- resets once-per-turn limits;
- retains persistent damage, resources, Strain, Crew, Marines, and eligible charge progress/Ready state;
- immediately charges required Ready-state upkeep when the player chooses to retain a charge.

### FTL transition

FTL transition additionally:

- clears all charging and Ready weapon state;
- clears tractor locks, powered tactical systems, held orders, temporary defenses, cloak state, and encounter-specific tactical effects;
- converts or clears tactical tracks according to strategic-contact rules.

It does not:

- repair Hull, armor, shields, or components;
- remove Strain;
- replenish ammunition, fuel, batteries, capacitors, Repair Supplies, Crew, or Marines;
- automatically restore Shield Capacity.

## TL1 numerical and scenario baseline

Checkpoint 25 retains the three exact core variants on one stripped chassis:

- TL1 Core Kinetic Cruiser;
- TL1 Core Energy Cruiser;
- TL1 Core Missile Cruiser.

Only the weapon family changes. Initial duels use identical doctrine, fixed Firm tracks, range 2, no movement, no optional systems, and no overload. Optional TL1 items are added one at a time in later scenario layers.

Authoritative test data:

- `tl1_core_combat_numerical_baseline_v0_1.csv`
- `tl1_core_combat_loadouts_v0_1.csv`
- `tl1_core_combat_test_scenarios_v0_2.csv`
- `TL1_Core_Combat_Test_Plan_v0_2.md`
- `Component_State_And_Profile_Schema_v0_2.md`
- `tl1_phase_a_scenario_schema_v0_1.json`
- `StarCluster_Player_TL_Framework_Draft_v0_5.xlsx`

## Calibration interpretation

The goal is not exact equality. Each component must be viable in its intended parametric region.

Test each countermeasure when:

- its relevant threat is absent;
- its relevant threat is present at ordinary intensity;
- its relevant threat is heavy or saturated.

Classify results as Dominant, Viable, Niche, Trap, Oppressive, or Redundant. Promote only evidence-supported changes.

## Checkpoint 25 implementation boundary

The following accepted rules now execute in `StarCluster.Core`:

- exact SPEN -> SA -> Shield Capacity -> APEN/AP -> AI -> AP -> Hull packet order;
- multiple armor layers and overkill reporting;
- turn-start Base and Tactical Shield recharge with condition profiles and Spent power;
- Available, Powered, Spent, and held-power earmark accounting;
- powered-system shutdown / disable lock without same-turn refund or restart;
- Reactor output by condition plus safe and forced overload, criticals, Strain, and once-per-turn use;
- safe kinetic, low/standard energy, and missile resource packets;
- charging, Ready state, retention, safe discharge, component disablement, and FTL clearing.

The Phase A runner loads the 117-value baseline and executes 54 named cases across 12 JSON documents. Each result records the baseline SHA-256. The scenario adapters create fixtures and compare expected subsets; they do not own authoritative Core mechanics.

Checkpoint 25 deliberately does not implement stochastic direct-fire hit, duel initiative, endpoints, doctrine, Crew casualty/Damage Control state machines, optional systems, movement, or energy-weapon overload. Phase B must define those contracts before balance trials begin.

## Deferred decisions

- final TL1 values after the first simulations;
- TL2–TL9 progression and hybrid milestones;
- exact internal damage-track generation for the TL1 chassis;
- detailed boarding resolution and Marine losses;
- cloak profiles and decloak penalties;
- Emergency FTL Jump procedure;
- exact reactor-feedback, magazine, and containment critical effects;
- whether capacitor charging remains legal at both Turn Refresh and Damage Control;
- specialized immediate shield restart;
- multi-tractor conflict geometry beyond the hold-only baseline;
- detailed charged-weapon families and energy torpedoes;
- final Crew stage effects beyond Damage Control.
