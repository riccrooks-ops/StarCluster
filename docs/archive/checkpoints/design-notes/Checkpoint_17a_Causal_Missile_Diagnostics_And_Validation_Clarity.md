# Checkpoint 17a - Causal Missile Diagnostics and Validation Clarity

## Purpose

Checkpoint 17a is a corrective consolidation pass over the accepted Checkpoint 17 missile-local sensor foundation. It does not change report arbitration, movement, range, datalink retention, or terminal-impact rules. It makes the development evidence match the already-correct authoritative behavior and improves the repeatability of manual validation.

The pass corrects six observed issues:

- `MissileLocalSensorUpdated` now records the missile coordinate for the exact observation opportunity rather than the action-ending coordinate.
- every entered missile edge has an explicit `MissileMovementEdgeResolved` event before its post-entry observation and arbitration;
- missile journal events are emitted in causal order;
- first detection, loss, and reacquisition caused by ship movement now emit complete trail-segment lifecycle events;
- clicking a singly selected contact again deselects it; and
- interception feedback and older active-salvo trails remain readable after the batch summary refresh.

## Causal missile journal

One autonomous missile action is now journaled in this order:

1. action-start datalink update;
2. action-start local-sensor observation;
3. action-start report arbitration;
4. `MissileGuidanceStarted` using the initial selected report and initial route;
5. `MissileMovementEdgeResolved` for one entered hex;
6. post-entry `MissileLocalSensorUpdated` at that entered coordinate;
7. post-entry `MissileGuidanceArbitrated`;
8. optional `MissileGuidanceReplanned` with movement already spent and remaining movement;
9. interception events for that edge;
10. repeated edge groups as movement permits;
11. aggregate `MissileMoved`; and
12. launch or guidance completion.

The aggregate movement event remains useful for summaries, but it no longer substitutes for per-edge chronology. Stationary final-approach interception remains after `MissileGuidanceStarted` and before completion.

## Exact local-sensor coordinates

`RecordLocalSensorObservation` receives the coordinate attached to the immutable `MissileAutonomousGuidanceStep`. Action-start observations therefore use the action-start coordinate, and each post-entry observation uses that entered coordinate. The journal also writes `missileCoordinate` in the event data so text and JSONL evidence can be compared directly with arbitration, replanning, and the authoritative debug panel.

## Observer trail lifecycle

Track refreshes caused by player ship movement or Sensor/EW changes can begin or close a hostile missile's observed trail even when the missile itself did not move. Checkpoint 17a records those transitions explicitly:

- Unknown or Stale to Firm/Approximate: `MissileContactAcquired`, then `ObservedTrailSegmentStarted` at the first observed coordinate;
- Firm/Approximate to Stale/Unknown: `MissileContactLost`, then `ObservedTrailSegmentClosed`;
- later Firm/Approximate reacquisition: a new start event and a disconnected segment.

Missile-movement observation retains its existing per-entered-hex trail events. The corrective path excludes those triggers to prevent duplicate lifecycle records.

## Presentation corrections

A singly selected missile or ship can be deselected by clicking it again. Collocated missile stacks retain repeated-click cycling because each click can choose a different stable salvo identity.

Main-weapon and PDS feedback is retained for the remainder of the Missile / Interception phase and is shown together with the final batch summary. Observer-confirmed trails use a minimum opacity floor while the salvo remains active. Stale history remains dimmer than Current history, but it no longer fades below practical readability.

The authoritative debug panel now lists the most recent observation opportunities and their exact missile coordinates, marking steps that triggered a replan.

## Validation procedure

`docs/validation/archive/Tested_Tactical_Regression_Checkpoints_09_Through_17a.md` now contains a dedicated Checkpoint 17a procedure with:

- neutral Sensor/EW setup;
- the proven five-turn local-sensor occlusion route;
- expected player-visible behavior;
- expected authoritative event order and fields;
- explicit debug-panel comparison points;
- click-to-deselect and feedback-persistence checks; and
- numbered note fields plus screenshot and journal evidence requirements.

The historical Turn 4 stack and `IMPACT x2` baseline expectations are no longer mandatory for sensor-equipped Checkpoint 17+ missiles. Local reacquisition can legitimately change those routes. The runbook now treats authoritative routes and resulting geometry as the source of truth.

## Tests

Checkpoint 17a preserves the accepted **490-test** engine-independent suite. It updates the existing diagnostic-event semantics test to include `MissileMovementEdgeResolved`; the corrective changes otherwise live in the Godot presentation and development-journal integration layer.

Expected complete suite: **490 tests**.

## Deferred work

Terminal seeker acquisition, lock retention/loss, search behavior, and capability-specific terminal attack gates remain the next substantive checkpoint.
