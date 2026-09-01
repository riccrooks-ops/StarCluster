# Checkpoint 13 — Target-Track and Tactical-Presentation Foundations

## Purpose

Checkpoint 13 prevents authoritative system state from leaking directly into the tactical display and gives Sensors, Computing, missile guidance, precision fire, and layered interception a common information model.

The checkpoint also folds in the Godot presentation issues documented after Checkpoint 12a:

- no direct-fire line before the player selects a valid target;
- active tracked missiles remain visible during every tactical phase;
- a missile's historical/executed route is distinguished from its projected next route;
- legal movement overlays clear once movement is committed;
- a living prototype TODO document records valid deferred usability and design work.

## Pre-known stars and navigation knowledge

Every star is pre-known on both the strategic star map and the local system map. Visible stellar positions are navigation data, not tactical contacts that must be rediscovered after entering a system.

`NavigationKnowledge` is distinct from tactical sensor tracks. It may also include charted planets, known stations, established jump points, and previously cataloged permanent anomalies. Ships, missiles, wreckage, temporary anomalies, concealed installations, mines, probes, and newly arrived objects normally require prior intelligence or current sensor detection.

`NavigationKnowledge.FromSystemMap` always includes every `MapObjectKind.Star`, even if the caller supplies no charted-object IDs.

## Initial Track Update

`SystemEntryTrackInitializer` establishes observer repositories and runs an initial Track Update before a player-visible tactical snapshot is built. The same initialization path is used for scenario reset.

The intended sequence is:

1. Load authoritative system state internally.
2. Load navigation knowledge and retained intelligence.
3. Create observer-specific track repositories.
4. Run the initial Track Update.
5. Build the player-visible tactical snapshot.
6. Begin turn 1 in Movement.

There must be no frame in which every authoritative occupant is rendered before the first sensor pass.

## Observer-specific track model

Tracks belong to an observer-target pair. The player ship, enemy ship, missile seeker, and point-defense system may hold different information about the same object.

Checkpoint 13 records four track qualities:

- **Firm** — fresh and precise; supplies a target coordinate suitable for normal precision direct fire.
- **Approximate** — current contact with an estimated coordinate and uncertainty radius.
- **Stale** — retained last-known coordinate after one or more missed updates; uncertainty grows according to Computing.
- **Lost** — historical record remains, but no usable tactical coordinate is supplied.

A completely undiscovered target is **Unknown** because no record exists. Unknown is deliberately not an enum value that appears on the map: absence of a record reveals nothing about whether an object exists.

`TacticalTrackRecord` retains source, estimated coordinate, last confirmed coordinate, last update sequence, missed-update count, and uncertainty radius. Each `TacticalTrackUpdateResult` records the event trigger that produced the update. `TacticalTrackRepository` stores records without depending on Godot.

## Sensors and Computing

`SensorProfile` currently supplies deterministic Firm and Approximate range bands and an LOS requirement. `SensorContactEvaluator` returns a Firm, Approximate, or missed observation from authoritative geometry.

`ComputingProfile` controls how many missed updates a Stale track remains usable and how quickly its uncertainty grows. Final TL progressions, signatures, active/passive sensing, environmental modifiers, jamming, spoofing, false contacts, and multi-observer fusion remain deferred.

The first pass is deterministic by design. Sensor probability and EW contests can later replace the observation policy without changing the track repository or tactical consumers.

## Event-driven updates

Track Update is not a player-visible tactical phase. `TrackUpdateTrigger` records why an information refresh occurred.

The Godot demonstration refreshes tracks:

- on initial system entry;
- on scenario reset;
- after a committed ship move or hold command;
- after missile launch;
- after missile movement completes.

The architecture also leaves explicit triggers for sensor-state changes, spawns, and destruction. Information may refresh immediately after each movement event, but an already completed movement command remains locked.

## Player-visible tactical map

`TacticalMapKnowledgeService` constructs a `TacticalMapKnowledgeSnapshot` from:

- navigation knowledge;
- the observer's own objects;
- observer-specific visible tracks.

It never enumerates authoritative map occupants as player-visible contacts merely because they exist. Lost and Unknown contacts are omitted from the current tactical picture. Stale contacts use retained coordinates rather than authoritative positions.

`TacticalMissileKnowledgeService` applies the same rule to salvos. Friendly salvos may expose their exact current coordinate and history, while hostile salvos are presented only at the player observer's tracked coordinate. A hostile missile's authoritative current coordinate, traveled trail, and last executed route are not passed to Godot when the player has only an imperfect track.

The Godot board renders:

- navigation-known stars and charted permanent objects;
- Firm contacts normally;
- Approximate contacts with uncertainty emphasis;
- Stale contacts as ghosted last-known positions;
- no marker for Lost or Unknown contacts.

## Direct fire and interception

`DirectFireTrackEligibility` requires a Firm track for normal precision targeting. The Godot direct-fire line is hidden until the player selects the enemy's Firm contact.

A held main weapon also requires a Firm tactical track on the missile when its shot is taken. The installed Point Defense System remains a distinct layer with independent short-range local acquisition. This preserves the intended possibility that the tactical track is imperfect while a nearby PDS can still detect and engage an incoming missile.

## Missile guidance and route projection

`MissileTargetTrackSnapshot` now accepts Firm/Current, Approximate, Stale, and Lost track states:

- Firm/Current pursues the precise coordinate;
- Approximate pursues the estimated center;
- Stale pursues the retained coordinate;
- Lost waits without moving or spending range.

`MissileRouteProjectionService` produces a non-mutating preview from the missile's current coordinate toward the best presently available track. Projection does not advance the missile, consume range, replace cumulative history, or become authoritative guidance state.

The Godot board separates:

- cumulative traveled history;
- the last executed route plan;
- the dashed projected next route.

Tracked active salvos remain visible during Movement, Direct Fire, Missile / Interception, Damage, and Damage Control.

## Movement presentation

After the player commits a move or hold command:

- movement is marked resolved;
- legal-destination and route-preview overlays are cleared;
- a Track Update runs;
- the player may inspect the refreshed tactical picture;
- phase advancement remains explicit for now.

Automatic phase advancement after every relevant actor and optional action is resolved remains a documented future UX decision rather than being hard-coded around the one-ship prototype.

## Tests

Checkpoint 13 adds **38** engine-independent tests:

- sensor and Computing profile validation;
- Firm, Approximate, Stale, Lost, and Unknown behavior;
- deterministic track update and uncertainty growth;
- observer-specific independence;
- initial system-entry processing;
- reset-safe initialization;
- automatic pre-knowledge of every star;
- navigation knowledge versus hidden authoritative contacts;
- precision direct-fire eligibility;
- imperfect-track missile guidance and waiting;
- non-mutating route projections;
- held-main-weapon Firm-track gating;
- independent PDS local acquisition;
- observer-safe hostile missile presentation without authoritative coordinate or history leakage.

Expected complete suite after application: **349 tests**.

## Local validation

Close Godot, extract the package into the repository root, then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-13\apply_checkpoint_13.ps1
```

Then press F5 in Godot and validate:

1. The star is visible immediately on system entry and after reset.
2. No authoritative contact appears before the initial Track Update.
3. A clear nearby enemy begins as Firm; moving behind the star degrades it without revealing its true hidden position.
4. Direct-fire LOS is not drawn until a Firm ship target is selected.
5. A non-Firm ship contact cannot receive normal precision direct fire.
6. Committing movement clears legal destinations while leaving Movement visibly resolved.
7. Tracked missiles remain visible during every phase.
8. After ship movement, the dashed projected route refreshes without moving the missile or spending range.
9. The missile moves only during Missile / Interception, after which its historical route and traveled trail remain distinct from the next projection.
10. A held main weapon requires a Firm missile track, while the PDS may still react through local acquisition.
11. Reset repeats initial track processing and restores turn 1 Movement without displaying hidden authoritative contacts.

## Deferred

- final Sensors, Computing, signature, and EW TL progressions;
- randomized detection and identification;
- active/passive sensor modes;
- jamming, spoofing, false contacts, and decoys;
- heading/velocity prediction and richer uncertainty regions;
- multi-ship sensor fusion and data links;
- speculative or area fire into uncertainty regions;
- onboard seeker acquisition and reacquisition profiles;
- developer truth-overlay toggle;
- automatic phase advancement after every relevant action is resolved.

## Next candidate checkpoint

After local acceptance, the strongest next focused pass is **sensor signatures and electronic-warfare foundations**, including active/passive sensing, target signatures, deterministic jamming modifiers, seeker reacquisition, and a clean policy seam for later probabilistic resolution. The exact scope should be reviewed before implementation.
