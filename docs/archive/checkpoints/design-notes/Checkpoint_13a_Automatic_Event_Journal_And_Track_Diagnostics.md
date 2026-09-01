# Checkpoint 13a — Automatic Event Journal and Track Diagnostics

## Purpose

Checkpoint 13a accepts the Checkpoint 13 tracking foundation and adds the observability required to diagnose multi-turn tactical behavior without relying on screenshots or recollection. Every Godot encounter automatically creates an authoritative event journal; no enable, export, or open-folder action is required.

The pass also resolves the track-presentation issues found during Checkpoint 13 validation: pointer inspection now includes track state and missile contacts, hostile missile trails contain only positions actually observed by the player, and projected route lines begin outside the missile marker so the first segment remains visible.

## Automatic logging policy

The Godot prototype always starts synchronized logs under `user://logs/`:

- one JSON Lines file for exact structured review;
- one human-readable text file for quick inspection.

A filename includes the checkpoint identifier, UTC start time, and encounter sequence:

```text
star-cluster-checkpoint-13a-20260727T151422315Z-encounter-001.jsonl
star-cluster-checkpoint-13a-20260727T151422315Z-encounter-001.log
```

Each event is appended and flushed immediately. Closing the scene writes a terminal session event. Resetting or changing the scenario closes the current pair and begins a new timestamped pair; prior evidence is never overwritten.

The right panel displays the current session ID, both absolute file paths, and the latest diagnostic entries. There is intentionally no button for opening the folder or enabling the logger.

## Engine-independent event model

`StarCluster.Core.Diagnostics` adds:

- `DiagnosticEventType` — stable event categories;
- `DiagnosticEvent` — immutable event data;
- `DiagnosticEventJournal` — monotonic event sequencing and recent-event access;
- `DiagnosticEventJsonlFormatter` — one camel-case JSON object per line with string enum names;
- `DiagnosticEventTextFormatter` — deterministic readable output.

The Core event record supports:

- checkpoint and session IDs;
- UTC timestamp and sequence number;
- turn and tactical phase;
- actor and target IDs;
- before and after coordinates;
- event-specific structured fields.

File persistence remains in `StarCluster.Game`, preserving the one-way architecture and keeping Godot and operating-system APIs out of the simulation library.

## Recorded tactical events

The Checkpoint 13a Godot fixture records:

- session start and end;
- scenario initialization and reset;
- every observer-target track update and quality transition;
- ship move and hold resolution;
- tactical phase advancement;
- direct-fire and defensive reserve commitments;
- missile launch and one-phase movement resolution;
- guidance quality, route status, movement, waiting, lifetime range, and terminal state;
- every held-main-weapon and PDS interception attempt;
- entry into the currently placeholder Damage and Damage Control phases.

A waiting missile entry explicitly identifies `WaitingForTrack` versus `WaitingForRoute`, movement of zero, cumulative distance, and remaining range. This makes cases such as “Turn 3: hostile-1 lost its target track and preserved fuel” directly reviewable.

## Observer-safe trails and inspection

`TacticalTrackRecord` now retains a history of coordinates actually supplied by successful observations. Repeated observations at the same coordinate do not create duplicate trail points.

Friendly missile contacts may continue to expose exact owned travel history. Hostile missile contacts expose only their observer-derived coordinate history and never receive the authoritative last executed route through the player presentation object.

The board tooltip and right-panel inspection now merge:

- navigation-known and tracked map contacts;
- friendly and hostile missile contacts;
- track quality;
- missile state and range summary.

They no longer report a tracked missile hex as `occupants: empty`, and they do not enumerate hidden authoritative occupants.

Projected dashed paths are trimmed away from the origin and destination marker centers. This keeps the first visible segment from being obscured by the `F`, `E`, ship, or target marker.

## Tests

Checkpoint 13a adds **16** engine-independent tests:

- journal constructor validation;
- monotonic event sequencing;
- UTC timestamp normalization;
- defensive copying of event data;
- recent-event selection;
- turn-number validation;
- readable text formatting;
- camel-case JSONL and string enums;
- coordinate serialization;
- observed-coordinate history creation, deduplication, and extension;
- hostile missile trail presentation without authoritative route leakage.

Expected complete suite after application: **365 tests**.

## Local validation

Close Godot, extract the package into the repository root, and run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-13a\apply_checkpoint_13a.ps1
```

Then press F5 and perform several turns, including movement behind an occluder, held interception, missile waiting, reacquisition, and reset. Confirm:

1. The right panel identifies a `checkpoint-13a` timestamped session.
2. Both `.jsonl` and `.log` files appear automatically under the displayed `user://logs` path.
3. A reset starts a new encounter-numbered pair rather than overwriting the previous files.
4. Missile and ship pointer summaries include track state.
5. A tracked missile is not described as an empty cell.
6. A hostile observed trail grows only when new positions are observed.
7. The first dashed projected-route segment remains visible outside the missile marker.
8. A missile with a Lost target track produces an explicit zero-movement `WaitingForTrack` journal entry.
9. Reacquisition produces a later track transition and resumed guidance entry.

Upload the `.log` and `.jsonl` pair with any screenshots when requesting analysis.

## Deferred

- filtering the authoritative journal into a player-visible combat log;
- retention limits, compression, and privacy controls for release builds;
- simulation seed and random-roll capture when probabilistic systems are introduced;
- source-specific LOS blocker details in every track update;
- richer grouped event presentation and replay tooling;
- automatic phase advancement after all relevant actions are resolved.

## Next candidate checkpoint

After local acceptance and review of a real generated journal, the next candidate remains sensor signatures and electronic-warfare foundations. The journal should be used to validate every later hidden-information and probabilistic rule.
