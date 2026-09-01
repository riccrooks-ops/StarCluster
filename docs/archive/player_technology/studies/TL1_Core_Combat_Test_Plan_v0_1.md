# TL1 Core Combat Test Plan v0.1

**Checkpoint 24 status:** exact provisional test specification; no value is promoted as final balance.

## Goal

The TL1 test program measures how the smallest complete combat loop behaves before optional systems, advanced technology, and differentiated doctrine obscure cause and effect.

The program does not seek equal win rates for every weapon and subsystem. It seeks situational viability:

- every option has a clear purpose;
- the intended threat makes the option valuable;
- the option carries a visible opportunity cost when irrelevant;
- a counter helps without completely erasing the system it counters;
- no option is routinely dominant, oppressive, redundant, or a trap.

## Controlled TL1 chassis

All core duel variants share one stripped TL1 cruiser chassis:

- one Hull, one primary armor layer, one shield generator, one main reactor, one FTL drive, one STL drive, passive sensors, one Targeting Computer, one Weapon Bay, Crew, Marines, and Damage Control;
- no PDS, ECM, ECCM, Shield Hardener, battery, capacitor, Auxiliary Reactor, APU, tractor, cloak, powered armor, or other optional Auxiliary component;
- one weapon-family variant: kinetic, energy, or missile;
- identical starting state, geometry, initiative policy, and doctrine;
- fixed Current/Firm tracks for the first weapon tests;
- no movement, Evasive Maneuvering, overload, held interception, or discretionary retreat in the first duel layer.

This is a laboratory fixture, not a claim that a campaign ship will always launch in this exact configuration.

## Core doctrine v0.1

At the start of each turn:

1. apply Base Shield Recharge;
2. spend up to the listed Tactical Shield Recharge cap when shields are below maximum;
3. retain any unused Tactical Power;
4. do not overload;
5. do not move or use Evasive Maneuvering;
6. fire the installed weapon once at its standard legal mode against the sole Firm target;
7. assign Damage Control by the same fixed priority: Disabled reactor, Disabled weapon, Degraded reactor, Degraded weapon, Hull, then Strain;
8. continue until the configured destruction or mission-kill endpoint.

Later stages may give each weapon family an appropriate doctrine, but only after the common doctrine exposes inherent component behavior.

## Test ladder

### Phase A — deterministic mechanics

Confirm exact packet order and resource accounting before Monte Carlo:

- shield bypass, Shield Armor, capacity, overflow;
- Armor Protection and Armor Integrity;
- Hull and internal exposure;
- recharge timing;
- power state transitions;
- ammunition and Ready Packages;
- charge and retention;
- overload and forced-overload outcomes;
- turn and FTL resets.

### Phase B — core mirror and cross-family duels

Run K/K, E/E, and M/M mirror matches first. Mirror win rate should approach 50% under paired side-swapped seeds. Then run every cross-family pairing in both side assignments.

### Phase C — one defensive subsystem at a time

Add one PDS, Shield Hardener, Shield Battery, or other defense while holding the chassis, weapon, doctrine, and reactor constant. Test no relevant threat, relevant threat, and heavy relevant threat.

### Phase D — electronic warfare

Add ECM and ECCM independently and together. Compare early and delayed activation at legal power-adjustment opportunities. Resolve one prospective Sensor/EW Refresh after all boundary changes are finalized.

### Phase E — power flexibility and overload

Add Reactor overload, Combat Battery, Capacitor Bank, Auxiliary Reactor, and APU one at a time. Separate the value of the component from the value of simply increasing reactor output.

### Phase F — damage, personnel, and recovery

Introduce component conditions, Crew casualty chunks, Marines where boarding is relevant, Damage Control, Strain removal, and component-specific magazine or containment hazards.

### Phase G — movement and positional systems

Introduce range control, Evasive Maneuvering, STL overload, moving-target missile pursuit, tractors, held interception, and retreat.


## Fixture conventions

The 13 rows in `tl1_core_combat_loadouts_v0_1.csv` are reusable ship loadouts. The scenario matrix uses `side_a_fixture` and `side_b_fixture` because deterministic mechanics cases also require synthetic packet, state, damage, personnel, or target fixtures that are not complete reusable ships.

A fixture value that matches a reusable `loadout_id` uses that loadout unchanged except for the scenario's stated variable. A value ending in `_fixture`, `tl1_standard_test_cruiser`, or `none` is scenario-local and is defined by the row's doctrine, changed variable, metrics, and acceptance contract. Implementation must materialize those synthetic fixtures explicitly rather than silently adding them to the reusable-loadout catalog.

## Symmetric and asymmetric comparisons

Every optional subsystem begins with:

1. neither side has it;
2. both sides have it;
3. only Side A has it;
4. only Side B has it under side-swapped paired seeds.

For power-consuming systems, also compare:

- component added with the same reactor;
- component added with additional reactor output.

This distinguishes a strong but costly system from a weak system and exposes mandatory power upgrades.

## Relevance states

Each countermeasure is tested in three contexts:

- **irrelevant:** the opposing threat is absent;
- **relevant:** the intended threat appears at ordinary intensity;
- **heavy:** the intended threat is emphasized or saturated.

Example: PDS should add little or no value against a kinetic-only opponent, materially reduce ordinary missile effectiveness, and remain helpful without making a missile-heavy doctrine nonviable.

## Trial modes

- deterministic contract cases use fixed rolls and exact expected state;
- mirror and cross-family Monte Carlo use common random numbers and side-swapped pairs;
- initial exploratory batches use 10,000 paired trials per comparison;
- promotion-quality batches use a larger count selected from observed uncertainty and practical-effect thresholds;
- worker count and resume boundaries must not change canonical results.

## Metrics

Record at minimum:

- win, mission kill, destruction, surrender, retreat, and unresolved rates;
- turns to endpoint;
- shieldless turns and shield-collapse count;
- damage absorbed, bypassed, and applied to armor and Hull;
- Armor Integrity and Armor Protection collapse timing;
- component condition steps;
- Crew and Marine casualties;
- Damage Control attempts, successes, and materials consumed;
- Available, Powered, earmarked, and Spent Tactical Power by phase;
- unused Tactical Power;
- overload use, forced-overload attempts, failures, and Strain;
- ammunition, battery, capacitor, and fuel use;
- PDS attempts and interception outcomes;
- track-quality transitions and missed firing opportunities;
- tractor hold/pull results and movement denied.

## Interpretation labels

Use these review labels rather than demanding numerical equality:

- **Dominant:** routinely best across unrelated contexts.
- **Viable:** useful in its intended contexts with meaningful costs.
- **Niche:** narrow but real purpose.
- **Trap:** appears useful but is almost never worth its cost.
- **Oppressive:** invalidates the system it counters.
- **Redundant:** another option provides the same purpose more efficiently.

The desired design space contains mostly Viable options and some intentional Niche options.

## Traceability

The authoritative exact test values are stored in `tl1_core_combat_numerical_baseline_v0_1.csv`. Standard loadouts are in `tl1_core_combat_loadouts_v0_1.csv`. The staged scenario matrix is in `tl1_core_combat_test_scenarios_v0_1.csv` and is also mirrored in the Checkpoint 24 technology workbook.
