# TL1 Bilateral Overload / EW Counterplay Study v0.1

## Purpose

Checkpoint 67 extends the accepted Checkpoint 66d bounded-overload evidence without introducing a full tactical AI. The study measures two tactical questions under the existing Tactical Power commitment windows:

1. How much does **pre-Movement STL overload** matter when either ship, both ships, or neither ship precommits it before movement order is resolved?
2. After Movement fixes the geometry, how do **Active Sensor, ECM, and ECCM overload choices** interact when uncommitted Tactical Power remains available at the existing acquisition/fire-control adjustment window?

No target win rate is a release gate. The study is diagnostic and may reveal that a scripted overload choice is beneficial, irrelevant, or harmful.

## Authoritative fuel update

Checkpoint 67 adopts **100 fuel** as the player-cruiser tactical baseline. Fuel costs are unchanged:

- 2 fuel per ship hex actually traversed;
- EvM costs a flat +1 fuel for the turn;
- TL1 STL Overload I retains its listed +2 extra fuel cost.

Historical Checkpoint 65b and Checkpoint 66d studies explicitly retain their original 200-fuel fixtures as frozen historical evidence.

## Fixed controls

- TL1 production reactor output: 5 TP.
- Tactical Power doctrine: FullVolleyFirst.
- Radius-5 finite tactical map.
- Initial separation: range 4.
- Bilateral TrackAwareOpponentRange + AcquisitionFirstAutoActive sensing.
- EvM off in this study.
- Tactical disengagement off.
- Safe-only overload scripting stops before Forced Overload would be required.
- Existing overload-damage consequences remain deferred.

## 60-variant matrix

### A. Bilateral STL precommit matrix - 48 variants

Three ordered matchups:

- Kinetic vs Missile;
- Energy vs Missile;
- Missile vs Kinetic.

For each matchup, run symmetric EW0 and EW1 controls, both movement orders, and four pre-Movement STL commitments:

- neither ship overloads;
- Side A overloads;
- Side B overloads;
- both ships overload.

Both STL decisions are resolved from the same pre-Movement state **before either ship moves**. The second mover may react geometrically, but cannot retroactively add an STL overload after observing the first mover.

### B. Post-Movement EW response matrix - 12 variants

Missile vs Missile, both movement orders, with the 35-Space `balanced_generalist_ew_major` fixture on both sides. The fixture adds explicit 1-Space ECM and 1-Space ECCM support systems to the accepted 33-Space balanced generalist.

Six paired response packages:

1. control - no overload;
2. Side A Active Sensor overload available;
3. Side B ECM safe overload;
4. Side B ECM safe overload + Side A Active Sensor overload available;
5. Side B ECM safe overload + Side A ECCM safe overload;
6. Side B ECM safe overload + Side A Active Sensor and ECCM safe overloads.

These are scripted legal-window decisions, not a general tactical-response AI.

For this diagnostic only, the package-listed ECM/ECCM commitments are funded first at that post-Movement window; AcquisitionFirstAutoActive then allocates the minimum legal sensor power from what remains. This is an explicit **study priority**, not a production Tactical Power priority rule.

## EW resolution in this diagnostic

Normal ECM/ECCM rating is 1 when the installed Operational/Degraded system can be powered. `SafeOverload` requests one additional TP and, when the component is Operational and its resulting Strain remains at or below the TL1 limit, increases that system's rating by 1 and adds 1 Strain.

For an observer, explicit net EW pressure is:

`fixed scenario penalty + max(0, target ECM rating - observer ECCM rating)`.

The fixed scenario penalty remains useful in the STL matrix as an abstract EW0/EW1 control. The post-Movement counterplay matrix uses zero fixed penalty so the effect comes from installed ECM/ECCM systems.

## Telemetry improvement

Checkpoint 67 separates several states that Checkpoint 66d could conflate:

- STL overload requests versus actual activations;
- Active Sensor overload planning opportunities before Movement;
- Active Sensor overload requests after Movement;
- actual sensor overload activations;
- ECM/ECCM power committed;
- ECM/ECCM overload requests and activations;
- overload requests explicitly denied by insufficient Tactical Power versus the safe Strain limit.

This makes it possible to distinguish a **contingency that altered movement planning** from an overload that was actually needed and activated after the opponent moved, and to separate explicit power/Strain denials from the remaining request-minus-activation cases such as component condition or fuel.

## Interpretation guardrails

- Do not promote a scripted doctrine to production AI merely because it wins this matrix.
- Do not retune overload values from one matchup.
- Do not treat unused contextual advantages, including Energy APEN, as worthless when the current target does not exercise them.
- Fuel, initiative/movement order, sensor range, EW, and overload all interact; results are evidence for later tactical-AI design, not preset balance targets.
