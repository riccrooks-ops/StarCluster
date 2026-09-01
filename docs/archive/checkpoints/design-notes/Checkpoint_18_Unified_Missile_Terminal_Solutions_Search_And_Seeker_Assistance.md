# Checkpoint 18 - Unified Missile Terminal Solutions, Search, and Seeker Assistance

## Purpose

Checkpoint 18 removes the prototype shortcut that treated reaching a guidance coordinate as an automatic impact. A tactical hex is a large volume of space. Reaching the target hex now creates a terminal opportunity with explicit defense, acquisition, search, and attack stages.

The checkpoint also carries forward the accepted Checkpoint 17c documentation-title and presentation cleanup.

## Accepted terminal sequence

For a Missile Flight that enters the actual target hex:

1. Resolve the terminal-entry standard-PDS window.
2. If the flight survives, evaluate its selected report and terminal equipment.
3. Accept a legitimate Current/Firm report from an allowed live source, or let an installed seeker attempt to convert an eligible cue into Firm.
4. If no Firm solution exists, enter Search/Wait without charging stationary-search fuel on the arrival action.
5. If Firm exists, resolve the distinct pre-attack standard-PDS window.
6. If the flight survives, resolve exactly one bounded d100 terminal attack.
7. Record the result explicitly as dud, miss, hit, critical hit, interception, or safe self-destruction.

Standard PDS may attempt the same Flight at most once per defending ship in each of the two terminal windows. These terminal windows supplement rather than replace the earlier per-entered-hex interception-envelope behavior established by Checkpoints 12 and 12a. All transit and terminal reactions still consume the installed system's shared per-phase attempt budget. Installed PDS components contribute Reaction Capacity, but combined capacity does not create additional attempts in one terminal window.

## Track-source-neutral terminal eligibility

Terminal eligibility is based on the legitimacy, freshness, and quality of the report rather than one hard-coded source.

- Command-guided missiles require a live Current/Firm remote report because they have no missile-local navigation source.
- Sensor-equipped missiles may use either a live Current/Firm datalink or peer report, when available, or their own Current/Firm local sensor report.
- Seeker-only missiles use an eligible remote cue to reach the target hex and must acquire locally before attack.
- Sensor-plus-seeker missiles may use a legitimate Firm report directly or use the seeker to improve an eligible terminal cue.
- Retained Stale reports can guide cruise movement but cannot authorize a terminal attack.
- `PeerGuidance` is represented as a future source seam; production peer-link delivery remains deferred.

## Seeker and Guidance Computer roles

The seeker is an optional co-located terminal augment. It does not create or maintain a second cruise track.

- Seeker acquisition uses a data-driven base chance, terminal ECCM, target terminal ECM, and bounded d100 roll.
- After Firm exists, an installed seeker may add a separate accuracy bonus.
- The missile Guidance Computer supplies the base hit chance and minimum/maximum bounds.
- Natural 01 is a dud/fuse failure and leaves an inert recoverable object.
- Natural 100 is a critical hit flag for later damage resolution.

The provisional Checkpoint 18 profile exists to exercise architecture and presentation. It is not final balance.

## Search and fuel

Arrival movement already consumes distance/range fuel. Failed acquisition on that same action does not also consume stationary-search fuel.

A later Search/Wait activation:

- consumes one whole fuel unit;
- reevaluates legitimate remote and missile-local information;
- attacks immediately if Firm is gained and the pre-attack PDS window is survived;
- resumes cruise if a better report moves the guidance coordinate elsewhere; or
- safely self-destructs if the activation exhausts its remaining fuel without a terminal attack.

Cumulative movement plus stationary-search expenditure remains bounded by the Flight's maximum range.

## Core implementation

Checkpoint 18 adds:

- `MissileTerminalState` and `MissileTerminalOutcome`;
- immutable `MissileTerminalResolution` records;
- `MissileGuidanceComputerProfile`, `MissileTerminalSeekerProfile`, and `MissileTerminalProfile`;
- replaceable seeded and fixed d100 terminal random sources;
- centralized `MissileTerminalResolutionService` acquisition and attack gates;
- separate `TerminalEntry` and `PreTerminalAttack` interception opportunities;
- Search/Wait fuel accounting on `GuidedMissileSalvo`;
- explicit terminal resolution on movement results and tactical contacts; and
- `PeerGuidance` as a future report-source seam.

Broad flight state remains separate from terminal detail. `GuidedMissileStatus` now distinguishes active search, expended attacks, duds, interception, range exhaustion, destruction, and safe self-destruction. The obsolete `Arrived` shortcut is removed.

## Godot presentation and diagnostics

The development encounter uses a seeded terminal random source and a provisional sensor-plus-seeker Flight profile.

Observer-safe presentation can show only legitimately observable terminal cues:

- `SEARCHING`
- `INTERCEPTED`
- `DUD`
- `MISS`
- `IMPACT`
- `SELF-DESTRUCTED`

Searching Flights remain active tactical contacts. Terminal Flights leave the active contact set and are represented through retained resolution cues when observable.

The authoritative journal adds events for terminal opportunity, Search/Wait activation, acquisition resolution, terminal attack resolution, and self-destruction. Interception records identify the exact opportunity. The development-only AUTHORITATIVE DEBUG panel may show hidden report source, acquisition chance/roll, effective hit chance/roll, and reason; normal player presentation must not.

## Tests

Checkpoint 18 adds 22 focused terminal tests and updates the earlier guidance/interception expectations. Coverage includes:

- live, blocked, retained, local, and peer report gates;
- sensor-only use of either datalink or local Firm information;
- seeker-only and sensor-plus-seeker acquisition;
- terminal ECM/ECCM and seeker accuracy;
- natural 01, natural 100, ordinary hit, and ordinary miss;
- one PDS attempt per defending ship in each of two terminal windows;
- entry and pre-attack interception ordering;
- no arrival double-charge;
- later Search/Wait fuel and immediate attack; and
- zero-fuel safe self-destruction.

The expected clean engine-independent suite after application is **493 passing tests**. The previously reported 490-test Checkpoint 17c total included 19 obsolete pre-guidance `MissileSalvoTests` cases left by historical overlay extraction. Removing that superseded file produces the canonical 471-test Checkpoint 17c baseline; Checkpoint 18 adds 22 tests for a total of 493.

## Explicitly deferred

Checkpoint 18 does not implement:

- warhead packets or layered ship damage;
- magazines, reload, or tactical power costs;
- final TL progressions or balanced missile component catalogs;
- production peer-guidance delivery and arbitration;
- detailed seeker cones, facing, lock retention, false targets, or decoys;
- recovery gameplay for duds; or
- broad automatic PDS threat-allocation across a simultaneous multi-Flight batch.

## Next recommendation

First validate the Checkpoint 18 terminal sequence and observer-safe cues. Then add representative Missile Flight profiles and balance fixtures. The leading broader systems pass should be tactical power, because sensors, ECM, PDS, shields, and weapons will all depend on its activation and damage-state contract before layered damage is implemented.
