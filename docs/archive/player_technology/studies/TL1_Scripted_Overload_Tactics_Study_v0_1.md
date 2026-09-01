# TL1 Scripted Bounded Overload Tactics Study v0.1

## Purpose

Checkpoint 66 follows accepted Checkpoint 65b without changing weapon, defense, sensor, EW, reactor-output, map, movement-fuel, or Installation Space balance numbers. Checkpoint 65b validated bilateral sensing on the radius-5 map, final-position combat geometry, finite-map kiting pressure, and mirrored movement-order bounds. It also produced a clean environment in which a one-hex sensing or movement advantage has visible tactical value.

Checkpoint 66 therefore exercises the existing overload/Strain concept as **scripted tactical choices**, not as a full tactical-response AI.

The questions are:

1. What is the tactical value of committing TL1 STL Overload I before Movement when it can help obtain or preserve preferred range?
2. What is the tactical value of holding power until the later acquisition window and using TL1 Active Sensor Overload I when it converts an otherwise unavailable Firm solution?
3. How do those choices interact with movement order, symmetric EW pressure, finite-map perimeter pressure, fuel, and the 5-TP production reactor?
4. Can the accepted overload timing and bounded component modes be exercised without introducing an automatic omniscient counter-response?

No target win rate, family ranking, or overload-use frequency is a release gate.

## Authoritative timing and overload rules

Concept v0.6e preserves the existing Tactical Power adjustment windows and overload/Strain framework. Checkpoint 66 does not create a new reserve-power pool or reopen an earlier power window.

- An STL overload that affects Movement must be declared and funded before Movement. Both ships' scripted STL decisions are determined from the same pre-Movement state before either ship moves.
- Moving second provides geometric information, but it does not permit a reactive STL overload after seeing the first mover.
- Active Sensor overload is a later-window acquisition choice and may use Tactical Power still Available at that legal boundary.
- Tactical Power remains universal. There is no separate propulsion, sensor, or overload currency.
- Each component exposes only listed overload modes. Spare TP never creates an unlisted mode.
- Strain is persistent rules state. The Checkpoint 66 **safe-only doctrine** simply refuses an overload whose resulting Strain would exceed that component's TL1 Strain Limit. This is an AI/study policy, not a rules exception; Forced Overload and Damage Control Strain removal remain authoritative concepts for later integration.

## TL1 overload seed exercised by this study

### STL Drive Overload I

- Additional Tactical Power: 1 TP.
- Movement benefit: +1 Move for the turn.
- Additional overload fuel cost: 2 fuel.
- Strain: +1.
- Strain Limit: 2.
- Eligibility: Operational drive only.
- Frequency: at most once per component per turn.

The extra movement hex, if actually traversed, also pays the ordinary 2-fuel-per-hex movement cost. Thus overload has both its explicit extra fuel cost and any ordinary fuel cost created by additional travel.

### Active Sensor Overload I

TL1 Active Sensors retain their normal 1-TP and 2-TP settings. Overload I is one bounded mode:

- additional Tactical Power above rated maximum: 1 TP;
- total active-sensor commitment: 3 TP;
- Firm range: +2 hexes beyond the normal 2-TP setting;
- Approximate range: +2 hexes beyond the normal 2-TP setting;
- Strain: +1;
- Strain Limit: 2;
- eligibility: Operational Active Sensor only;
- frequency: at most once per component per turn.

This is not arbitrary TP stacking. Missile terminal seekers remain distinct from the ship's Active Sensor suite.

### ECM/ECCM

Concept v0.6e also records the current bounded TL1 ECM/ECCM Overload I concept, but Checkpoint 66 does **not** exercise it. The balanced-generalist study fixture does not install an explicit ECM/ECCM component, so fabricating such hardware for this matrix would confound the study.

## Scripted policies

Side A is assigned one of four declared plans:

1. `none` - no STL or Active Sensor overload.
2. `stl` - `SafeRangePressure` STL overload, no sensor overload.
3. `sensor` - no STL overload, `SafeWhenNeeded` sensor overload.
4. `combined` - both scripted policies are available at their legal windows.

Side B always uses no overload policy in this first diagnostic. This asymmetry is intentional: Checkpoint 66 measures the marginal value and opportunity cost of a declared Side-A tactic before a later full AI is taught to select and counter tactics dynamically.

`SafeRangePressure` attempts STL Overload I only when the ship begins Movement outside its own weapon family's preferred range envelope and the safe Strain/power conditions are met.

`SafeWhenNeeded` attempts Active Sensor Overload I only when the post-Movement geometry lies beyond the normal 2-TP Firm envelope but within the overloaded Firm envelope, and sufficient Tactical Power remains at the legal acquisition boundary.

## Study matrix

The matrix focuses on missile-standoff interactions where the new choices are most likely to matter:

- five ordered weapon pairings: Kinetic/Missile, Missile/Kinetic, Energy/Missile, Missile/Energy, Missile/Missile;
- two symmetric EW regimes: EW0 and EW1;
- four Side-A overload plans: none, STL, sensor, combined;
- two movement orders: SideAFirst and SideBFirst.

**5 x 2 x 4 x 2 = 80 variants.**

Each weapon-pair/EW lane shares a comparison group and seed across all eight plan/order variants.

Controls remain:

- `balanced_generalist_major` construction on both sides;
- TL1 production runtime profiles;
- 5 TP per operational main reactor;
- FullVolleyFirst power doctrine;
- bilateral TrackAwareOpponentRange + AcquisitionFirstAutoActive sensing;
- radius-5 map and initial range 4;
- 200 starting fuel / 2 fuel per traversed hex / EvM +1 rule;
- EvM off in this isolation;
- tactical disengagement off;
- no full tactical-response AI.

## Release-gate boundary

Release gates verify mechanics and coverage, not balance outcomes. They require:

- exact 80-variant coverage and paired lanes;
- zero overload activations in no-overload controls;
- no Side-B overload activations;
- observed STL overload use somewhere the scripted range-pressure condition permits it;
- observed Side-A Active Sensor overload use in at least one EW1 Missile lane;
- safe-only mean overload use bounded by the TL1 Strain Limit;
- consistent fuel accounting: ordinary movement fuel plus the explicit STL-overload fuel cost;
- preserved finite-map, 5-TP, bilateral sensing, final-position, and movement-order controls;
- zero trial errors.

Win share is review evidence only. Energy APEN and other contextual capabilities remain protected from premature retuning.

## Interpretation

Review the paired CSV for:

- conditional win differences between no-overload and each scripted overload plan;
- final range and closest approach;
- Side-A/Side-B movement and fuel expenditure;
- STL and sensor overload activation rates;
- Firm/Approximate/NoTrack behavior and track-denied attacks;
- insufficient-power preventions after an overload consumes TP;
- missile launches and range exhaustion;
- movement-order sensitivity.

Checkpoint 66 should tell us whether these bounded overload tools create meaningful tactical options and opportunity costs. It should **not** decide the final tactical AI, overload-damage probabilities, or component balance numbers.
