# Baseline Tactical Regression Encounter

Use this exact encounter after each tactical checkpoint so screenshots, notes, and automatic journals can be compared directly across versions.

## Setup

- Scenario: **Clear direct fire**
- Interception demonstration result: **MISS**, unless a checkpoint specifically tests success
- Sensor / EW development controls: player passive, enemy passive, player jammer off, enemy jammer off
- Start a new F5 session and preserve the automatically generated checkpoint-stamped `.log` and `.jsonl` pair

## Turn 1

1. Move the player ship from `(-3,3)` to `(0,2)` and commit.
2. Advance to Direct Fire.
3. Select the enemy ship and fire the main weapon.
4. Advance to Missile / Interception.
5. Launch one enemy missile at the player.
6. Confirm the Firm-tracked enemy launch creates an observer-confirmed trail that remains visible at subdued intensity even before `hostile-1` is selected.
7. Select `hostile-1`; confirm its trail begins at `(2,3)` and extends through `(2,2)` to `(1,2)`, then deselect it and confirm the same history remains subdued while the dotted incoming-threat estimate remains distinct. Record the visible missile coordinate, projected route, PDS feedback, and tooltip.
8. Advance through Damage and Damage Control.

## Turn 2

1. Move the player ship from `(0,2)` to `(2,-1)` and commit.
2. Advance to Direct Fire.
3. Select `hostile-1` and attempt main-weapon interception.
4. Advance to Missile / Interception.
5. Launch a second enemy missile.
6. Confirm its observer-confirmed trail remains visible while unselected. Select `hostile-2` and confirm selection only emphasizes the trail from `(2,3)` to `(2,1)` without exposing any hidden segment.
7. Select **Advance unresolved salvos once**.
8. Confirm `hostile-1` advances to `(2,0)`, the PDS result is explicit, and the selected/highlighted coordinate follows the salvo rather than remaining at `(1,2)`.
9. Confirm both salvos advance at most once and no hidden state appears.
10. Advance through Damage and Damage Control.

## Turn 3 — occlusion and hidden contact

1. Move the player ship from `(2,-1)` to `(2,-3)`, behind the planet.
2. Confirm enemy and missile tracks degrade according to observer knowledge.
3. Advance to Direct Fire and click `hostile-1` for inspection.
4. Confirm the Stale/occluded missile cannot receive a specific interception order, the yellow weapon-target ring is absent, and the panel directs the player to **Hold main weapon for any missile**.
5. Select **Hold main weapon for any missile**.
6. Confirm the board position, zoom, and bottom row do not shift when the order is committed.
7. Advance to Missile / Interception.
8. Launch a third enemy missile.
9. Confirm an unacquired missile does not appear, receive a selection ring, alter a visible stack count, draw a route, or create a trail from its unseen launcher.
10. Select **Advance unresolved salvos once**.
11. Confirm visible stale contacts move only according to player knowledge; exact hostile route overlays remain withheld when the contact is not Firm.
12. Advance through Damage and Damage Control.

## Turn 4 — reacquisition, stack, and mixed resolution

1. Move the player ship from `(2,-3)` to `(1,-2)` and commit. Because two movement points remain in Checkpoint 15, select **End movement** before advancing.
2. Confirm the enemy ship and missiles are reacquired as appropriate.
3. For pre-Checkpoint-17 guidance, confirm the historical two-missile `E×2` stack. For Checkpoint 17 and later sensor-equipped missiles, compare the authoritative routes instead: local reacquisition may legitimately prevent collocation. Record the actual visible coordinates and `MissileStackChanged` result.
4. When a visible stack exists, click it repeatedly to cycle individual salvo IDs. When no stack exists, record `stackCount=0` and verify that every visible salvo remains independently selectable.
5. Confirm every observer-confirmed trail remains visible at subdued intensity. Select each visible salvo in turn and confirm selection only emphasizes its complete known history, never bridges movement that occurred while unobserved, and a newly acquired missile's trail begins at its first detected coordinate.
6. Advance to Direct Fire and attempt interception against `hostile-1`.
7. Advance to Missile / Interception.
8. Select **Advance unresolved salvos once** exactly once.
9. Confirm the main weapon and PDS outcomes are distinct.
10. For pre-Checkpoint-17 guidance, confirm the historical `IMPACT x2` result. For Checkpoint 17 and later, use the authoritative final coordinates and guidance sources: impacts occur only for salvos that actually reach the ship with a Current terminal solution. Record `playerImpacts`, surviving contacts, and any impact cue.
11. Advance to Damage and confirm every actual impact or interception cue remains visible throughout the Damage phase.
12. Advance to Damage Control and confirm the prior impact cue clears.
13. Confirm the command becomes disabled because every active salvo has resolved once for the phase.
14. Confirm the journal contains exactly one `MissileBatchResolved` followed by one `TacticalViewRefreshed` for the Turn 4 batch and no `MissileBatchFinalizationFailed` event.

## Additional first-detection trail check

When a later scenario places the launcher outside detection range but a missile enters detection range during its launch movement:

- do not draw a trail to the unseen launcher;
- begin the trail at the first detected entered hex;
- extend it only across continuously detected hexes;
- create a disconnected segment after any loss and reacquisition.

## Checkpoint 14 focused Sensor / EW range-gate check

Run this after completing the unchanged four-turn baseline encounter. Scenario changes begin a new checkpoint-stamped journal pair.

1. Select **Sensor and jamming range gate**. Confirm the player is at `(-4,4)`, the enemy is at `(4,1)`, their distance is 8 hexes, and the central star does not block the line.
2. With all Sensor / EW controls at their default passive/off settings, confirm the player track on the enemy is **Approximate**. The detail panel should report effective Firm 6 and Approximate 10.
3. Turn on **Player active sensors**. Confirm an immediate `SensorStateChanged` Track Update makes the enemy track **Firm**, reports mode `+2`, and changes the effective envelope to Firm 8 / Approximate 12. Confirm the tactical map does not shift.
4. While still in the same tactical turn, turn on **Enemy jammer**. Confirm the player track becomes **Approximate** with raw jamming 3, counter-jamming 1, net jamming 2, and effective Firm 6 / Approximate 10.
5. Turn on **Enemy active emissions**. Confirm the target's +2 active-emission signature restores a **Firm** player track and effective Firm 8 / Approximate 12.
6. Turn Player active sensors off. Confirm the enemy active-emission signature alone still supplies the +2 modifier.
7. Turn Enemy active emissions off while Enemy jammer remains on. Confirm the player evaluation remains **Approximate** at the edge of the effective Approximate envelope (Firm 4 / Approximate 8). Because this is still a successful current observation, its track age must not advance.
8. Select **Blocked fire, indirect missile**, turn Player active sensors on, and turn Enemy active emissions on. Confirm the central star still prevents current detection and no precision target indication appears. The scenario-reset miss may already consume Turn 1's single age step; repeat several sensor toggles and confirm every further Turn 1 miss reports `ageAdvanced=False`. After reaching Turn 2 Movement, change sensor state again and confirm at most the first Turn 2 miss advances age.
9. Confirm every sensor-state event records observer mode, target mode, signature profile, distance, base and effective envelopes, environment profile and penalty, raw jamming, counter-jamming, net jamming, and final evaluation status.
10. Return to **Clear direct fire** with all Sensor / EW controls passive/off before any further baseline comparison.

## Current missile-trail and route presentation policy

Checkpoint 17 supersedes the selected-only Checkpoint 14a trail policy:

- every observer-confirmed trail segment remains visible at subdued intensity;
- selecting a salvo emphasizes but does not create or reveal additional history;
- a Stale trail is visibly dimmer;
- hidden movement is never bridged;
- friendly planned routes are dashed;
- hostile incoming-threat estimates are dotted and do not assert a confirmed lock;
- terminal salvos are removed from the active display.

## Checkpoint 14a focused presentation check

Run this after the Checkpoint 14 sensor/range-gate checks. Use the normal 1280×800 launch size and also verify the observed approximately 1274×796 client area if the operating-system window frame produces it.

1. Confirm the right panel has no clipped text, control captions, or content at its right edge and does not require horizontal scrolling.
2. Cycle every scenario name and confirm the scenario selector stays within the panel. Hover a trimmed caption, if any, and confirm the tooltip remains available.
3. Confirm the tactical board does not recenter, resize, or zoom when long feedback, diagnostic paths, or sensor summaries update.
4. Confirm the `Sensor / EW status` block shows separate `PLAYER -> ENEMY` and `ENEMY -> PLAYER` calculations containing status, distance, base-to-effective Firm/Approximate ranges, mode, target signature, environment, and raw/counter/net jamming.
5. Confirm the control meanings are directional and unambiguous: player active sensors improve player detection and increase player emissions; enemy emissions aid player detection; player jammer impairs enemy detection; enemy jammer impairs player detection.
6. In the **Sensor and jamming range gate** scenario, create an Approximate ship contact. Confirm it has both a segmented uncertainty ring and an `APPROX` text tag; do not rely on color alone.
7. Create an Approximate missile contact if the scenario permits. Confirm the missile stack receives the same segmented `APPROX` cue without exposing an Unknown missile.
8. In the four-turn baseline, confirm observer-confirmed missile trails remain visible while no salvo is selected. Select one salvo and confirm the same history is emphasized without revealing hidden travel.
9. Move behind the planet and select a Stale missile. Confirm its trail remains segmented across hidden movement and is visibly dimmer than a current trail; selection should only increase emphasis.
10. In the passive-sensors/both-jammers variant, confirm a missile reaching an Approximate report records `MovedToApproximateCoordinate` and an Approximate-specific wait reason. Confirm Stale guidance still records `MovedToLastKnownCoordinate` and a Stale-specific reacquisition reason.
11. Confirm all journals and title text use `checkpoint-14a`.


## Checkpoint 15 focused hybrid-movement check

Run this in a fresh **Clear direct fire** encounter with passive sensors and both jammers off.

1. At Turn 1 Movement, select adjacent hex `(-2,2)`. Confirm it has the stronger immediate-step outline, preview it, and select **Move to destination**.
2. Confirm the ship moves only to `(-2,2)`, movement remains open, the panel reports 2/3 movement remaining, and the legal destination overlay is recomputed from `(-2,2)`.
3. Select `(0,2)` as a farther destination. Confirm the preview route begins at `(-2,2)`, uses two entered hexes, and reports the remaining allowance of 2.
4. Select **Move to destination**. Confirm the journal records one `ShipMovementDestinationCommitted`, then exactly two `ShipMovementStepResolved` events and Track Updates with trigger `ShipMovementStepCommitted`. Confirm movement completes automatically at zero remaining allowance.
5. Reset the scenario. Move one adjacent hex, then select **End movement**. Confirm movement resolves with two points unspent and cannot be reopened that turn.
6. Run the baseline through Turn 3. Select `(2,-3)` from `(2,-1)` and commit the routed move around the planet. Confirm every entered coordinate receives its own movement-step event and sensor reevaluation.
7. Identify the last intermediate coordinate at which the enemy still observed the player. Confirm the first later occluded step changes the enemy track immediately to `Stale` at that coordinate, with `ageAdvanced=False` when the track was observed earlier in the same turn.
8. Confirm later misses in Turn 3 do not add another missed-age step or uncertainty increase.
9. Confirm hostile missile guidance on Turn 3 uses the enemy's recorded Stale estimated coordinate rather than the player's hidden authoritative final coordinate. This remains the pre-datalink/pre-seeker missile prototype, so launch eligibility is not yet capability-gated.
10. When a multi-hex route reveals a previously Unknown hostile missile before the final destination, confirm the route pauses after the committed step and the journal reports `Automatic route paused`. Confirm the new contact is shown observer-safely, remaining movement is preserved, and no executed step can be undone. Preserve this case when the current encounter geometry produces it; otherwise retain it as a focused fixture requirement for the first suitable scenario.
11. Confirm the title and automatic journal filenames use `checkpoint-15`.

## Checkpoint 16 focused datalink check

Run this after the accepted Checkpoint 15 movement cases. The authoritative journal is the primary evidence because enemy datalink state is intentionally not exposed in the normal observer-safe contact panel.

1. Start a fresh **Clear direct fire** encounter with passive sensors and both jammers off. Run Turn 1 through an enemy missile launch.
2. Confirm the launch writes an action-start `MissileDatalinkUpdated` event before `MissileGuidanceStarted`. At launch, launcher and missile share a hex, so the event must report `datalinkState=Live`, `reportDelivered=True`, `retainedReportAgePhases=0`, `guidanceSource=FreshDatalink`, and the same target quality/coordinate subsequently used by guidance.
3. Confirm the launch also writes an action-end `MissileDatalinkUpdated` event after movement with `evaluationStage=ActionEnd`, `reportDelivered=False`, and `retainedReportAged=False`. Its link state must reflect the missile's ending coordinate rather than the launch hex.
4. Advance an existing missile in clear geometry. Confirm a Live action-start link copies the launcher's then-current report into missile-owned state and resets retained age to zero. Confirm the guidance event records `guidanceSource=FreshDatalink`.
5. Select **Blocked fire, indirect missile** and launch a missile around the central star. Advance turns until launcher-to-missile LOS becomes Blocked. The launcher-to-target sensor result may be different; verify the two relationships are journaled independently.
6. At the first later action that starts Blocked, confirm `reportDelivered=False`, `retainedReportAged=True`, and retained age increases by exactly one. A previously Current or Approximate copied report must guide as Stale at its copied coordinate.
7. Confirm the retained coordinate does not silently change to a newer launcher coordinate while the link remains Blocked. `launcherTrackQuality` may describe the launcher's current information, but `retainedCoordinate` and the missile's guidance coordinate must remain the prior copied value.
8. Confirm the action-end link refresh never increases retained age. Repeated action-start or action-end diagnostics for one guidance phase must not create multiple age steps.
9. If the route restores launcher-to-missile LOS before the missile terminates, confirm the next action-start update delivers a fresh copy, resets age to zero, and may replan from the missile's current coordinate without restoring cumulative range.
10. Confirm a friendly missile's observer-side projected route follows the missile's last consumed report rather than automatically jumping to a newer ship track before the next datalink delivery.
11. In `MissileBatchResolved`, confirm `launchesResolved`, `existingSalvosAdvanced`, and `totalMissileActionsResolved` are present and arithmetically consistent. `salvosResolved` now matches the total rather than ambiguously naming only the existing batch advances.
12. Confirm the title and automatic journal filenames use `checkpoint-16`.

The seventeen new Core tests provide the authoritative expiration case: a retained report that exceeds `MaximumRetainedReportAgePhases` must produce Lost guidance with no coordinate even though the old copy remains available for diagnostics.


## Checkpoint 17 focused local-sensor and trail-clarity check

Run the accepted Checkpoint 16 datalink cases first only when regression evidence is needed. For the new behavior, select **Missile local-sensor occlusion**. Keep the normal observer-safe panel visible for presentation checks; enable **AUTHORITATIVE DEBUG** only when the steps explicitly call for it.

1. Confirm the title and automatic journal filenames use `checkpoint-17`. Confirm the scenario description identifies the local-sensor occlusion purpose.
2. Launch and advance a sensor-equipped missile. Confirm each missile action begins with `MissileLocalSensorUpdated` followed by `MissileGuidanceArbitrated` before movement. The arbitration event must list every usable candidate and one selected source.
3. Confirm the development missile sensor is inferior to the ship sensor: TL2, Firm 3, Approximate 5, Active bonus +2. Passive is attempted first. An Active local observation may occur only after Passive produced no contact.
4. Maneuver or advance until a missile starts from launcher or retained guidance and then obtains a better local report after entering a hex. Confirm the journal records one `MissileLocalSensorUpdated` for that entered hex, then `MissileGuidanceArbitrated`, then `MissileGuidanceReplanned`.
5. In the replan event, confirm `movementRefunded=False`, the remaining movement equals speed minus already entered hexes, cumulative `distanceTraveled` continues increasing, and maximum range is never restored.
6. Confirm the winning order is quality, source observation epoch, lower uncertainty, and LocalSensor only as an otherwise exact tie-breaker. Preserve one event containing the candidate list and human-readable reason.
7. Move the target one or more ship hexes while a missile is active. Confirm `MissileLocalSensorUpdated` events may refresh its local track during Movement, but no `MissileMoved`, impact, or missile attack occurs until Missile / Interception. Repeated misses in one observation epoch must age the local report at most once.
8. Select a known hostile missile, enable **AUTHORITATIVE DEBUG**, and confirm actual coordinate, range used/maximum, datalink state, retained report, local report, selected source/coordinate, reason, and last-action replan count agree with the authoritative journal. Disable the panel and confirm none of those hidden hostile details remain in normal contact text.
9. Confirm a friendly planned missile route is drawn with dashes. Confirm a hostile incoming-threat estimate is drawn with dots, not dashes, and its help text states that it is not a confirmed enemy lock, datalink, or actual guidance coordinate.
10. Observe a hostile missile trail, deselect it, and confirm the already observed solid trail remains visible at subdued intensity. Reselect it and confirm selection only emphasizes that same history.
11. Break observation and later reacquire the missile. Confirm the old solid trail remains, the hidden interval is blank, and a new disconnected segment begins at the first newly observed coordinate. No line may bridge the unseen movement.
12. Confirm stacked contacts retain independent trails and IDs. Selection may emphasize one stacked salvo, but unselected observer-confirmed histories must not disappear.
13. Confirm every entered missile hex receives no more than one interception resolution even when the post-entry local observation upgrades that hex into a Current final approach.
14. Preserve the matching `.log`, `.jsonl`, one arbitration/replan excerpt, one debug-panel screenshot, one dotted hostile-threat screenshot, one dashed friendly-route screenshot, and one deselected persistent-trail screenshot.

The twenty new Core tests provide deterministic coverage for passive-first Active escalation, same-epoch local-track loss, once-per-epoch local aging, blocked datalink with local guidance, quality/recency/uncertainty arbitration, local exact-tie preference, target-movement observation without out-of-phase movement, per-entered-hex replanning, and cumulative range preservation.


## Checkpoint 17a corrective validation - exact causal diagnostics and UI clarity

Run this after the Checkpoint 17 foundation has passed. Use a fresh F5 session and preserve the matching `checkpoint-17a` `.log` and `.jsonl` pair. Keep **Player sensors Passive**, **Enemy sensors Passive**, **Player jammer Off**, and **Enemy jammer Off** throughout this procedure.

### A. Corrective baseline smoke check

Use **Clear direct fire** for a short two-turn regression.

1. Launch one visible enemy missile and leave it unselected. Confirm its solid observer-confirmed trail remains readable at subdued intensity.
   - Notes/result: ________________________________________________
2. Select the missile. Confirm the same history becomes emphasized without gaining any hidden segment.
   - Notes/result: ________________________________________________
3. Click the same singly selected missile again. Confirm the selection ring clears and the trail returns to subdued intensity.
   - Notes/result: ________________________________________________
4. Hold the main weapon, advance the salvo into defensive range, and confirm any MAIN WEAPON and PDS result remains visible after the final missile-batch summary appears.
   - Notes/result: ________________________________________________
5. In the journal, confirm `MissileGuidanceStarted` appears before the first `MissileMovementEdgeResolved`, and that each edge event appears before its matching post-entry local observation and arbitration.
   - Journal sequence/event numbers: ______________________________
6. Confirm the per-edge event reports `edgeNumber`, `movementSpentThisAction`, `remainingMovementThisAction`, `distanceTraveled`, and `remainingRange`.
   - Notes/result: ________________________________________________

### B. Exact five-turn local-sensor occlusion route

Select **Missile local-sensor occlusion**. Confirm the player starts at `(-2,-1)`, the enemy at `(2,3)`, the enemy contact is Approximate with a segmented orange uncertainty ring and `APPROX` label, and no hostile missile is initially visible.

#### Turn 1

1. End movement at `(-2,-1)`.
2. Hold the main weapon for any missile.
3. Launch one enemy missile at the player.
4. Confirm no hostile missile marker, trail, selection ring, or dotted threat estimate appears.
5. Confirm the launch journal shows a Stale fresh datalink report, Passive-first local sensing with Active escalation only after the Passive miss, and no local contact.
   - Notes/result: ________________________________________________
   - Relevant event numbers: _____________________________________

#### Turn 2

1. Move `(-2,-1) -> (-3,0)`, then end movement with two points unused.
2. Confirm `hostile-1` is first detected at `(2,1)` with a Firm track. A dotted incoming-threat estimate may appear, but no solid trail line is required until a second observed coordinate exists.
3. Confirm the journal writes `MissileContactAcquired` followed by `ObservedTrailSegmentStarted` at `(2,1)` with trigger `ShipMovementStepCommitted`.
4. Hold the main weapon and advance unresolved salvos once.
5. Confirm the missile moves `(2,1) -> (1,1) -> (0,1)` and the solid trail becomes `(2,1) -> (1,1) -> (0,1)`.
6. Confirm the action order is:
   - action-start local observation and arbitration;
   - `MissileGuidanceStarted`;
   - edge to `(1,1)`;
   - local observation at `(1,1)`;
   - arbitration and no-refund replan with `remainingMovementThisAction=1`;
   - edge to `(0,1)`;
   - local observation at `(0,1)`;
   - arbitration;
   - aggregate movement and completion.
7. Confirm every `MissileLocalSensorUpdated.position` and `missileCoordinate` equals the matching action-start or entered-edge coordinate.
   - Notes/result: ________________________________________________
   - Event-number sequence: ______________________________________

#### Turn 3

1. Move `(-3,0) -> (-2,-1)`, then end movement.
2. Confirm target movement refreshes the missile-local report but does not move or attack the missile during Movement.
3. Hold the main weapon and advance once.
4. Confirm the action begins with the launcher's Stale coordinate `(-3,0)` available but selects the newer/better LocalSensor report for `(-2,-1)`.
5. Confirm post-entry sensing upgrades to Current, replans with no refund, and ends at `(-1,0)`.
6. Confirm the action-end datalink state is Blocked with no delivery and no extra aging.
   - Notes/result: ________________________________________________
   - Event-number sequence: ______________________________________

#### Turn 4

1. Move `(-2,-1) -> (-2,-2)`, then end movement.
2. Hold the main weapon and advance once.
3. Confirm the blocked action-start datalink ages the retained report exactly once to age 1, while the Current LocalSensor report wins arbitration.
4. Confirm the missile moves `(-1,0) -> (-1,-1) -> (-1,-2)` and lifetime range becomes `8/10`, with two remaining.
5. Confirm MAIN WEAPON and PDS attempts are distinct, occur no more than once on their respective entered edges, and remain visible after the batch summary.
6. Select the missile, enable **AUTHORITATIVE DEBUG**, and compare:
   - actual coordinate `(-1,-2)`;
   - distance/range `8/10`;
   - datalink Blocked;
   - retained Stale coordinate `(-3,0)`, age 1;
   - local Current coordinate `(-2,-2)`;
   - selected source LocalSensor;
   - observation-step list with exact action-start and entered-edge coordinates.
7. Disable AUTHORITATIVE DEBUG and confirm none of those hidden hostile details remain in normal player-facing text.
   - Notes/result: ________________________________________________
   - Screenshot names: ___________________________________________

#### Turn 5

1. Move `(-2,-2) -> (-1,-2)`, then end movement.
2. Hold the main weapon and advance once.
3. Confirm the blocked retained report ages exactly once to age 2, LocalSensor remains Current at the shared hex, and the missile moves zero hexes.
4. Confirm one final-approach MAIN WEAPON attempt and one final-approach PDS attempt. With the standard MISS demonstration setting, confirm both miss.
5. Confirm the batch records one player impact, removes the terminal missile marker and active trail, and leaves one red impact cue through Damage before clearing on Damage Control.
6. Confirm the enemy ship's segmented `APPROX` cue is absent once its track becomes Stale; a Stale contact must not retain an Approximate uncertainty ring or `APPROX` label.
   - Notes/result: ________________________________________________
   - Event-number sequence: ______________________________________

### C. Trail loss and reacquisition lifecycle

Use either the baseline or another controlled route that causes a visible missile to become Stale and later Firm again.

1. Confirm observer movement that loses the missile writes `MissileContactLost` followed by `ObservedTrailSegmentClosed`.
2. Confirm later observer movement that reacquires it writes `MissileContactAcquired` followed by `ObservedTrailSegmentStarted` at the first newly observed coordinate.
3. Confirm the old solid segment remains readable, the hidden interval is blank, and the new segment is disconnected.
   - Notes/result: ________________________________________________
   - Screenshot names: ___________________________________________

### D. Friendly dashed route and final evidence

1. Launch one friendly missile in any clear scenario with a legal player missile target.
2. Confirm its planned route is dashed, while a hostile incoming-threat estimate is dotted.
3. Confirm the help text states that the dotted hostile path is not proof of an enemy lock, datalink, or actual guidance coordinate.
   - Notes/result: ________________________________________________
4. Preserve:
   - the `checkpoint-17a` `.log` and `.jsonl` pair;
   - numbered notes for A-D;
   - one Approximate contact screenshot;
   - one first-detection trail screenshot;
   - one click-to-deselect screenshot or note;
   - one combined MAIN WEAPON/PDS feedback screenshot;
   - one AUTHORITATIVE DEBUG screenshot and one after it is disabled;
   - one disconnected-trail screenshot; and
   - one friendly dashed-route screenshot.

### Checkpoint 17a acceptance summary

- [ ] 490/490 tests pass.
- [ ] Every local-sensor event uses its exact opportunity coordinate.
- [ ] Guidance start precedes every entered-edge event.
- [ ] Every entered edge precedes its post-entry observation/arbitration.
- [ ] Replanning reports correct spent and remaining movement with no refund.
- [ ] Ship-movement first detection starts a trail segment in the journal.
- [ ] Loss closes a segment; reacquisition starts a disconnected segment.
- [ ] Click-again deselects a single contact.
- [ ] MAIN WEAPON/PDS results remain visible with the batch summary.
- [ ] Older active-salvo trails remain readable at minimum opacity.
- [ ] Debug-panel coordinates match the authoritative edge events.
- [ ] Disabling debug restores the observer-safe information boundary.
- [ ] Friendly plans are dashed; hostile threat estimates are dotted.

## Evidence to preserve

- checkpoint-stamped `.log` and `.jsonl` files;
- one screenshot at the Turn 3 hidden-contact point;
- one screenshot of the Turn 4 missile stack;
- one screenshot immediately after the Turn 4 batch resolves;
- one screenshot of the Sensor / EW range gate showing the track panel and effective modifiers;
- updated notes using the same numbered turn/action format;
- a short Sensor / EW range-gate result summary;
- one screenshot showing an Approximate segmented ring and `APPROX` tag;
- one screenshot showing the unclipped Sensor / EW summary and directional controls;
- one screenshot after the manual one-hex step showing reduced remaining movement and recomputed destinations;
- one Turn 3 screenshot and journal excerpt identifying the last observed intermediate coordinate before occlusion;
- one action-start/action-end datalink event pair for the same missile action;
- one blocked-link retained-report event showing copied coordinate, age, and Stale effective guidance;
- a short note for any deviation from the scripted coordinates or actions.

## Acceptance checks

- No Unknown contact is rendered or selectable.
- No route uses hidden hostile guidance data. Hostile dotted paths are observer-side incoming-threat estimates, not asserted locks.
- Every visible trail begins at an actually observed coordinate.
- Reacquired trails have visible gaps where observation was lost.
- Visible stack counts include only visible active contacts.
- Selected missile highlighting follows the selected salvo's observer-safe coordinate.
- A specific missile order is available only with a Firm current track and clear current weapon LOS; range alone may be deferred.
- Ship fire is unavailable when LOS is blocked or the target is currently out of range.
- Direct-fire feedback never shifts, rescales, or clips the tactical map.
- The right panel contains no horizontal clipping or scrolling at the reference and observed client sizes.
- Approximate contacts have both segmented uncertainty geometry and an `APPROX` tag.
- Every observer-confirmed trail segment remains visible at subdued intensity; selection only emphasizes it, and hidden intervals remain disconnected.
- Missile resolution cues persist through Damage and clear on entry to Damage Control.
- The map and right panel agree after every batch.
- Mixed terminal/active batches still finalize once and redraw.
- Journals contain `MissileBatchResolved` followed by `TacticalViewRefreshed`.
- Sensor-state changes refresh immediately, expose their deterministic modifiers in diagnostics, and do not reopen resolved commands or advance one track's missed age more than once per turn.
- Active sensors, active emissions, and jamming never bypass blocking terrain or expose Unknown authoritative truth.
- A distant ship destination resolves as one committed event per entered hex; each step refreshes tracks before the next step.
- A manual step leaves the remaining allowance available for another adjacent or distant command.
- Same-epoch visibility loss becomes Stale at the most recently observed intermediate coordinate without consuming another age step.
- Newly detected hostile missiles can interrupt an automatic route without rewinding executed movement.
- A missile receives launcher information only through a Live datalink copy; blocked or unavailable links cannot read a newer launcher coordinate.
- Retained datalink age advances no more than once per missile guidance phase and expires at the profile-defined limit.
- Action-end datalink refresh changes link state only; it delivers and ages no report.
- Missile-batch diagnostics distinguish launches, existing-salvo advances, and total missile actions.
