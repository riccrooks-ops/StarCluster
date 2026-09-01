# TL1 Bilateral Tactical Geometry, Fuel, and Movement-Order Study v0.1

## Purpose

Checkpoint 65 follows accepted Checkpoint 64 without changing weapon, sensor, EW, reactor, armor, shield, PDS, or missile balance numbers. Checkpoint 64 showed that track-aware movement can correct self-inflicted acquisition denial, but the one-sided Established-Firm opponent also created an artificial movement and missile-intercept advantage.

Checkpoint 65 therefore moves the diagnostic onto the actual finite tactical system map and makes operational sensing bilateral.

The questions are:

1. What movement-order advantage exists when both ships try to maintain their own tactically preferred range?
2. How does the radius-5 map naturally constrain kiting without an arbitrary turn limit?
3. Does the new 200-fuel / 2-fuel-per-hex rule behave coherently while remaining unlikely to dominate ordinary 1-on-1 engagements?
4. Do missile chase/intercept outcomes remain pathological once both sides obey the same acquisition rules and finite geometry?

No target win rate is a release gate.

## Authoritative Concept updates

Checkpoint 65 updates the Concept to v0.6d. The simulator is subordinate to those rules.

- Tactical system map: radius 5, 11 hexes across, 91 cells.
- Ship tactical fuel baseline: 200.
- Each ship hex actually traversed costs 2 fuel.
- EvM costs a flat additional 1 fuel for the turn, replacing the prior doubled-movement-fuel rule.
- Existing Tactical Power adjustment/commitment windows remain unchanged.
- Existing overload/Strain rules remain unchanged. No arbitrary extra Tactical Power may be dumped into a component beyond its listed modes.
- Movement-phase power commitments are already fixed when movement order becomes informative; the second mover may react geometrically but cannot retroactively declare STL overload.
- Ordinary post-Movement combat uses final coordinates. Historical closest approach does not grant a normal Direct Fire or launch opportunity.
- The traversed path and closest approach remain authoritative for explicit Movement-phase/event-driven effects, sensing observations, missile-local observations, LOS/occlusion changes, fuel use, and diagnostics.

## Finite-map movement primitive

Checkpoint 65 adds an opt-in finite-map movement resolver using the existing `HexMap` and `HexCoord` types. It is intentionally not a full tactical AI.

For a declared Close/Open/Maintain order, the primitive:

1. enumerates legal destinations inside the finite radius-5 map and within current STL movement allowance;
2. prefers destinations that obey the requested range direction and minimize error from the requested tactical range;
3. among equally useful destinations, prefers interior room before spending extra movement;
4. constructs a deterministic shortest legal hex path;
5. records full movement distance, path minimum/maximum separation, final coordinate, and whether the destination lies on the map boundary.

Because the map is finite, a kiter can legitimately preserve standoff only while geometry allows it. There is no scenario rule such as "kiting stops after N turns."

## Movement-order bounds

Checkpoint 65 does not define the final production initiative system.

Every family/regime lane is run twice with paired random streams:

- `SideAFirst`: Side A chooses and resolves movement, then Side B chooses movement from the resulting geometry.
- `SideBFirst`: Side B moves first and Side A reacts second.

The second mover receives geometric information only. No Movement-phase Tactical Power allocation is reopened.

These two runs deliberately bound the tactical value of moving second before later officer/initiative rules decide how production movement order is obtained.

## Fuel

The finite-map study uses the authoritative baseline:

- starting fuel: 200;
- 2 fuel per ship hex actually traversed;
- EvM flat fuel cost: +1 for the turn.

EvM is disabled in the Checkpoint 65 Monte Carlo matrix so movement fuel accounting is isolated: mean fuel spent must equal mean movement hexes x 2. The shared fuel-rule service and unit tests also encode the stationary-EvM cost of exactly 1 fuel for later use.

Fuel can cap available movement if a very long engagement ever exhausts the store. It is expected to be telemetry rather than the primary 1-on-1 outcome driver at TL1.

## Bilateral sensing and combat geometry

Both ships use the same acquisition regime. Checkpoint 65 no longer grants an operational lane a one-sided Established-Firm opponent.

Three regimes are used:

1. `established-firm-bilateral` — both sides use the bilateral Established-Firm ceiling with opponent-aware weapon-range movement.
2. `bilateral-track-aware-clear` — both sides use TrackAwareOpponentRange + AcquisitionFirstAutoActive in clear space.
3. `bilateral-track-aware-ew1` — the same bilateral operational doctrine under symmetric EW1 range pressure.

All normal Direct Fire and missile launch authorization uses final end-of-Movement separation. Missile flight on the finite-map path uses authoritative hex coordinates and pursues the target's current coordinate after Movement.

Checkpoint 65 is a geometry/fuel foundation, not the final movement-event integration pass. The Concept makes every traversed hex authoritative for explicit Movement-phase events; this study records the full ship path/closest approach and charges fuel per traversed hex, but it does not yet retrofit every possible per-step sensor refresh, LOS/occlusion transition, or missile-local observation into the integrated Monte Carlo runner. Those event hooks remain part of later production integration rather than being approximated as post-Movement attacks.

## Study matrix

The study holds construction fixed at the accepted `balanced_generalist_major` package on both sides so geometry is not confounded by odd-build composition.

**3 Side-A weapon families x 3 Side-B weapon families x 3 bilateral regimes x 2 movement orders = 54 variants.**

Controls:

- TL1 production profiles on both sides;
- 5 TP per operational main reactor;
- FullVolleyFirst diagnostic power doctrine;
- zero-effect TL1 AUX profile;
- initial range 4;
- radius-5 map;
- EvM disabled;
- tactical disengagement disabled;
- no new automatic STL, sensor, ECM, or ECCM overload doctrine.

## Overload boundary

The Concept's existing overload/Strain framework remains authoritative, including pre-Movement STL overload timing and later legal power-adjustment windows for systems used after Movement. Checkpoint 65 deliberately does **not** teach the AI to choose overload modes. The study establishes geometry, movement order, bilateral acquisition, and fuel first so later overload decisions can be evaluated against a stable tactical foundation.

## Interpretation

Review:

- movement-order conditional win bounds;
- final range and path closest approach;
- movement hexes and fuel spent/remaining;
- boundary occupancy/pressure;
- bilateral Firm/Approximate/NoTrack behavior;
- attacks prevented for track or range;
- missile launches, travel, terminal attacks, and range exhaustion;
- initiative/movement-order sensitivity by family matchup.

Do not tune component numbers from this checkpoint alone. Energy APEN and all other contextual advantages remain valid design value even when the current TL1 opponent does not expose the relevant mechanic.
