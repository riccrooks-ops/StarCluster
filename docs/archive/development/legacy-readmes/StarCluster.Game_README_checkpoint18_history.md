# StarCluster.Game

This is the Godot 4.7.1 .NET presentation project for Star Cluster.

Open `project.godot` in the Godot .NET editor. The project references the engine-independent `..\StarCluster.Core\StarCluster.Core.csproj` library.

Checkpoint 18 retains the tactical order:

1. Movement
2. Direct Fire
3. Missile / Interception
4. Damage
5. Damage Control


## Hybrid incremental movement

During Movement, the player may click any reachable destination within the remaining allowance or choose an adjacent hex for one manual step. **Move to destination** previews and then executes the selected route one entered hex at a time. After every step, authoritative position, line of sight, tracks, missile contacts, and remaining legal destinations refresh. The player may then issue another movement command or select **End movement**.

Adjacent destinations receive stronger map emphasis. Movement allowance exhaustion completes the action automatically. If a multi-hex route detects a previously Unknown hostile missile before reaching the selected destination, the route pauses after the committed step; executed movement is never rewound.

The journal writes one `ShipMovementDestinationCommitted` event per selected route, one `ShipMovementStepResolved` event per entered hex, and one `ShipMovementResolved` summary when movement ends.


## Launcher-to-missile datalink

Checkpoint 16 gives each missile an explicit TL2 datalink receiver. At the start of each missile action, Core checks line of sight from the current launcher coordinate to the missile. A Live link copies the launcher's current report into missile-owned state. A Blocked or unavailable link delivers nothing; the missile retains and ages its prior copy once for that guidance phase.

The development profile keeps a retained copy usable for three missed guidance phases. A missed update changes a retained Current or Approximate report to Stale without changing its copied coordinate. Restored line of sight plus a usable launcher report replaces the copy and resets age. After movement, the link state is refreshed for diagnostics without delivering or aging a second report.

The authoritative journal records action-start and action-end `MissileDatalinkUpdated` events. Friendly route projections use the missile's own last consumed guidance report. Normal player-facing summaries do not reveal enemy datalink state.

## Track reevaluation and once-per-turn aging

Track Update remains event-driven rather than a player action phase. The demonstration performs an initial update before presentation and reevaluates observer-specific tracks after movement, missile launch, and missile movement.

The tactical turn number is the observation epoch. Successful observations refresh immediately. If visibility is then lost later in the same movement epoch, the track becomes Stale at the most recently observed intermediate coordinate without consuming an additional tactical-time age step. Repeated failures during that epoch still cannot accelerate track loss.

Every star is pre-charted navigation knowledge. Other tactical contacts are drawn only from navigation knowledge, retained intelligence, or the player observer's track repository.

## Tactical observability

The right panel is divided into:

- a fixed command area containing turn, phase, required actions, current phase buttons, PDS readiness, and immediate results;
- a separately scrollable detail area containing scenario, overlays, tracks, missile state, pointer inspection, Core results, and automatic journal information.

The command area remains accessible regardless of diagnostic volume.

The installed PDS auxiliary is always identified with TL, range, local acquisition behavior, and remaining attempt budget. Immediate feedback identifies whether the held main weapon or PDS fired, which salvo it targeted, and whether the result was a miss or interception.

## Collocated salvos

Multiple salvos may occupy one hex. Observer-visible contacts are grouped by coordinate and ownership for presentation while retaining independent Core identities.

- Friendly stacks use green `F` plus a count.
- Hostile stacks use red `E` plus a count.
- Friendly and hostile contacts at one coordinate remain separate stacks.
- Repeated clicks on a stack cycle its individual salvos.
- Only the selected salvo route is emphasized when routes overlap.

## Automatic authoritative event journal

Every F5 encounter automatically creates synchronized JSON Lines and readable text logs under Godot's `user://logs` directory. Filenames contain `checkpoint-18`, a UTC start timestamp, and an encounter sequence. Entries are flushed after every event. Reset and scenario changes close the current pair and begin a new pair without overwriting prior evidence.

The journal records observation epoch and whether age advanced, route planning, actual missile movement, transient defensive acquisition, main-weapon and PDS attempts, final status, explicit wait reason, collocated stack changes, and the prior Checkpoint 13a events.

The authoritative journal is a development diagnostic and may contain hidden truth. It remains distinct from a future player-visible combat log.

## Reset and phase state

The right-panel **Reset map / scenario** command uses the same initial Track Update path as system entry and restores both ships, turn 1 Movement, all commitments and selections, defensive budgets, launch counters, an empty missile engagement, and a new checkpoint-18 log pair.

Phase advancement remains explicit until multi-actor and optional-action requirements are mature enough to define safe automatic advancement.

See:

- `..\..\docs\checkpoints\Checkpoint_09_Godot_Presentation_Spike.md`
- `..\..\docs\checkpoints\Checkpoint_09a_Godot_Layout_Hotfix.md`
- `..\..\docs\checkpoints\Checkpoint_10_Tactical_Ship_Movement.md`
- `..\..\docs\checkpoints\Checkpoint_11_Moving_Target_Missile_Guidance.md`
- `..\..\docs\checkpoints\Checkpoint_11a_Turn_By_Turn_Missile_Presentation_Hotfix.md`
- `..\..\docs\checkpoints\Checkpoint_12_Missile_Ownership_And_Interception_Foundations.md`
- `..\..\docs\checkpoints\Checkpoint_12a_Direct_Fire_Commitment_And_Layered_Interception.md`
- `..\..\docs\checkpoints\Checkpoint_13_Target_Track_And_Tactical_Presentation_Foundations.md`
- `..\..\docs\checkpoints\Checkpoint_13a_Automatic_Event_Journal_And_Track_Diagnostics.md`
- `..\..\docs\checkpoints\Checkpoint_13b_Track_Aging_Epochs_And_Tactical_Observability.md`
- `..\..\docs\checkpoints\Checkpoint_13c_Observer_Safe_Tactical_View_And_Resolution_Feedback.md`
- `..\..\docs\checkpoints\Checkpoint_13d_Observed_Launch_Trails_And_Batch_Finalization.md`
- `..\..\docs\checkpoints\Checkpoint_13e_Target_Eligibility_And_Viewport_Stability.md`
- `..\..\docs\checkpoints\Checkpoint_14_Sensor_Signatures_And_Electronic_Warfare_Foundations.md`
- `..\..\docs\checkpoints\Checkpoint_14a_Tactical_Presentation_And_Missile_Architecture_Documentation.md`
- `..\..\docs\checkpoints\Checkpoint_15_Hybrid_Incremental_Tactical_Ship_Movement.md`
- `..\..\docs\checkpoints\Checkpoint_16_Launcher_To_Missile_Datalink_And_Retained_Reports.md`
- `..\..\docs\checkpoints\Checkpoint_17_Missile_Local_Sensors_Report_Arbitration_And_Trail_Clarity.md`
- `..\..\docs\checkpoints\Checkpoint_17a_Causal_Missile_Diagnostics_And_Validation_Clarity.md`
- `..\..\docs\checkpoints\Checkpoint_17b_Combat_Concept_Consolidation_And_Validation_UX_Hotfixes.md`
- `..\..\docs\checkpoints\Checkpoint_17c_Presentation_Concept_Power_Repair_And_Reference_Handoff.md`
- `..\..\docs\checkpoints\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md`
- `..\..\docs\design\Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md`
- `..\..\docs\Prototype_TODO.md`


## Observer-safe tactical-view boundary

Godot now receives one `ObserverSafeMissileViewSnapshot` rather than drawing directly from authoritative salvos. Unknown hostile missiles cannot appear in markers, selection rings, routes, tooltips, or stack counts. Exact hostile route projections are shown only for Firm missile contacts; Approximate and Stale contacts retain awareness without exposing hidden guidance.

Observed hostile trails are split into segments by observation epoch. A missed epoch creates a visible gap, so reacquisition never draws a line across movement that the player did not observe.

After a missile batch resolves, tracks, observer-safe contacts, normalized selection, stacks, and impact cues are refreshed together. The panel reports impacts and remaining visible salvos, and a no-op command explicitly reports that no unresolved salvos remain.

Use the active `..\..\docs\validation\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md` procedure. Completed historical procedures are preserved under `..\..\docs\validation\archive\`.


## Observed launch trails and batch finalization

Checkpoint 13d evaluates hostile missile observation after every entered hex. A Firm-tracked launcher makes a normal launch origin observable; otherwise the visible trail begins at the first detected in-flight hex. Loss closes the current segment, and reacquisition starts a disconnected segment even within the same turn.

Terminal Flights are removed from active markers and represented through observer-safe interception, dud, miss, impact, or self-destruction cues. Search/Wait Flights remain active contacts. Every missile batch uses one mandatory finalization path that refreshes tracks, active contacts, selection, stacks, cues, button state, and the automatic journal. Selected missile highlighting follows the salvo ID to its current observer-safe coordinate.


## Direct-fire target eligibility and viewport stability

Checkpoint 13e separates inspection from legal weapon targeting. Ship fire requires a Firm track, clear current LOS, and current range. A specific missile order requires a Firm track and clear current LOS; only a range shortfall may be deferred into the upcoming missile movement phase. Stale or occluded missiles remain inspectable but must be covered with **Hold main weapon for any missile** rather than a named reserve order.

The right panel is hosted at a fixed width so wrapped command feedback cannot resize or recenter the tactical board. Missile impact and interception cues remain visible through Damage and clear on entry to Damage Control.


## Sensor signatures and electronic warfare

Checkpoint 14 adds immutable Core profiles for target signatures, sensor environments, and electronic-warfare capability. Passive sensing preserves the prior base ranges. Active sensing adds the installed sensor's range bonus, while a target using active sensors adds its active-emission signature. Enabled target jamming reduces both Firm and Approximate envelopes after observer counter-jamming is applied. Blocking stars and planets remain absolute.

The scrollable detail region contains four development controls for player/enemy active sensors and player/enemy jammers. Each change triggers an immediate epoch-safe Track Update without advancing the phase or reopening a resolved command. The journal records every modifier and the resulting effective envelope.

Use the **Sensor and jamming range gate** scenario for the focused validation sequence. The original **Clear direct fire** four-turn regression remains unchanged when all Sensor / EW controls are passive/off.

The current deterministic quality decision is behind `ISensorContactResolutionPolicy`, allowing a later seeded probabilistic policy without moving authoritative track or presentation rules into Godot.


## Checkpoint 14a presentation refinements

The side panel now uses responsive minimum widths and short directional control labels so text remains within the panel at the 1280x800 reference viewport and the observed 1274x796 client area. A compact status block shows `PLAYER -> ENEMY` and `ENEMY -> PLAYER` with distance, base-to-effective Firm/Approximate ranges, and mode/signature/environment/jamming arithmetic.

Approximate contacts use a segmented uncertainty ring plus an `APPROX` tag rather than color alone. All observer-confirmed missile trail segments remain visible at subdued intensity; selection only emphasizes one salvo. Hidden intervals remain disconnected. Friendly planned routes are dashed, while hostile incoming-threat estimates are dotted and do not assert a confirmed enemy lock.

Checkpoint 14a also corrects diagnostic wording so an Approximate guidance arrival is not described as a Stale last-known-coordinate arrival.

The detailed missile architecture remains staged. Checkpoint 16 implements the datalink and retained launcher-report layer. Checkpoint 17 implements missile-local onboard sensors, deterministic launcher/retained/local report arbitration, and per-entered-hex reacquisition and replanning. Terminal seeker acquisition, lock, search, and capability-specific terminal attack gates follow next.


## Missile-local sensors and report arbitration

Checkpoint 17 gives every development missile an inferior TL2 onboard navigation sensor. It observes passively first, may escalate deterministically to Active only after a Passive miss, and owns a separate local report. At action start and after every entered missile hex, Core compares FreshDatalink, RetainedDatalink, and LocalSensor candidates by quality, observation epoch, uncertainty, and then a local exact-tie preference. Better post-entry information replans the remaining route without refunding movement or lifetime range.

Relevant target movement and Sensor/EW changes may refresh a local track immediately but never move or attack the missile outside the Missile / Interception phase. The authoritative journal records local observations, every arbitration, and every no-refund replan.

The tactical display uses selected-only solid observer-confirmed trail segments, selected-only dashed friendly planned routes, and dotted hostile incoming-threat estimates. The optional AUTHORITATIVE DEBUG panel is for focused development validation only and must remain disabled for normal observer-safe checks.

Use the **Missile local-sensor occlusion** scenario and the Checkpoint 17 section of the validation runbook for the focused sequence.


## Checkpoint 17a causal diagnostics and validation clarity

Checkpoint 17a preserves the accepted missile-local guidance rules while correcting the development evidence. The journal now records the exact missile coordinate for each local observation, emits `MissileGuidanceStarted` before explicit `MissileMovementEdgeResolved` events, and places post-entry observation, arbitration, replanning, and interception after the matching edge.

First detection or loss caused by ship movement now emits complete observed-trail segment start/close events. Clicking a singly selected contact again deselects it. Interception feedback remains visible with the batch summary, and active observer-confirmed trails retain a readable opacity floor. The AUTHORITATIVE DEBUG panel lists the exact opportunity/coordinate sequence from the most recent action.

The completed Checkpoint 17a procedure is preserved under `..\..\docs\validation\archive\Tested_Tactical_Regression_Checkpoints_09_Through_17a.md`.


## Checkpoint 17b validation UX hotfixes

Checkpoint 17b gives the scrollable detail/diagnostic region a 190-pixel minimum height. Enabling **AUTHORITATIVE DEBUG** defers one layout frame and automatically brings selected-missile internal details into view. The control remains development-only, default-off, and separate from normal observer-safe knowledge.

The new **Friendly missile route validation** scenario provides a clear Firm-track fixture for launching one player Missile Flight and checking dashed friendly planning against dotted hostile incoming-threat estimation.

The user's partial results are preserved at `..\..\docs\validation\archive\Checkpoint_17b_Partial_Validation_Results.md`; Checkpoint 17c supersedes the presentation acceptance criteria.


## Checkpoint 17c presentation and handoff corrections

Checkpoint 17c increases the default window to 1440x900, moves the **AUTHORITATIVE DEBUG** toggle into the always-visible command region, and gives the detail pane a 280-pixel minimum height. Deferred auto-scroll remains development-only and must not leak hidden hostile state when disabled.

Friendly Missile Flights now behave like player-owned units: their exact own-unit information is available in hover/selection text, but their dashed future plan and historical trail are drawn only while selected. The prior faint solid `VisibleLastExecutedRoute` rendering is removed so a solid line cannot be mistaken for a second future path. Hostile dotted routes remain observer-side threat estimates.

The superseded procedure is preserved at `..\..\docs\validation\archive\Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md`. Concept v0.3r is archived, and the complete `docs\references` library remains part of the handoff.


## Checkpoint 18 terminal resolution

Checkpoint 18 removes `Arrived == impact`. Entering the actual target hex begins a terminal sequence: one standard-PDS entry window, source-neutral Current/Firm acquisition with optional seeker assistance, one standard-PDS pre-attack window, and exactly one bounded d100 attack if the Flight survives with Firm. Standard PDS is terminal defense: it does not spend reactions during ordinary Transit or Stationary opportunities. Its two possible reactions are the target-hex entry window and, after Firm acquisition, the immediate pre-attack window. Held main weapons remain deliberate Transit/Stationary interceptors and do not participate in either terminal window.

Sensor-equipped Flights may use a live Firm datalink report or their own Firm local report. Command-guided Flights require a live remote Firm source. Seeker-only Flights must acquire locally in the target hex. The seeker is an ECCM/acquisition and accuracy aid, not a second cruise track.

Failed acquisition enters Search/Wait. The arrival action pays no extra stationary-search fuel; each later stationary search activation consumes one whole range/fuel unit. Search can immediately transition to attack after Firm reacquisition, or to safe self-destruction when fuel is exhausted.

The Godot encounter uses a seeded terminal d100 source and displays observer-safe `SEARCHING`, `INTERCEPTED`, `DUD`, `MISS`, `IMPACT`, and `SELF-DESTRUCTED` cues. The AUTHORITATIVE DEBUG panel may show report source, seeker roll/chance, hit roll/chance, and reason. Logs use `checkpoint-18`.

Use `..\..\docs\validation\Checkpoint_18_Unified_Missile_Terminal_Solutions_Search_And_Seeker_Assistance.md`. Concept v0.3s is the current design reference.


## Checkpoint 18b headless scenario validation

Checkpoint 18b moves detailed mechanical validation out of the Godot client. `StarCluster.ScenarioRunner` initializes the authoritative map, ships, prior intelligence, tracks, and optional pre-existing Missile Flights through Core services before executing versioned JSON scripts. Godot remains a player-facing host and requires only small presentation smoke checks.

Standard PDS is formally terminal-only: one opportunity at `TerminalEntry` and one at `PreTerminalAttack`. Held main weapons provide ordinary transit interception.


## Checkpoint 18c runner-policy correction

Checkpoint 18c leaves Godot presentation unchanged. It corrects the shared Core contract so held direct-fire weapons may react only during `Transit` or `Stationary`, while standard PDS owns `TerminalEntry` and `PreTerminalAttack`. Pre-existing retained datalink reports also restore a chronologically consistent guidance-phase counter during shared scenario initialization.

## Checkpoint 18d scenario-corpus correction

Checkpoint 18d leaves Godot and Core combat behavior unchanged. It repairs two deterministic scenario definitions, adds whole-batch preflight before any headless scenario executes, and improves ordered-event failure diagnostics. Detailed mechanical acceptance remains in `StarCluster.ScenarioRunner`; Godot remains a presentation and input host.


## Checkpoint 19 validation boundary

Mechanical probability, TL, and parameter-sensitivity testing now belongs in
`StarCluster.ScenarioRunner`. The runner uses the same `StarCluster.Core`
services and produces worker-independent canonical results, resumable trial
records, and compact statistical reports. Godot should not gain temporary
controls or diagnostic layout solely to force hidden mechanical outcomes.

Godot validation remains appropriate for player-facing input, phase controls,
selection, rendering, observer-safe information, and resolution cues. The seven
deterministic headless scenarios remain the required mechanical regression gate
before stochastic studies.


## Checkpoint 20 calibration boundary

Representative Missile Flight, PDS, and target-ECM TL experiments execute in `StarCluster.ScenarioRunner`, not through temporary Godot controls. Godot continues to consume the same `StarCluster.Core` mechanics and remains responsible for player-facing input, rendering, visibility filtering, and presentation smoke checks. The Checkpoint 20 profile values are provisional simulation data and do not yet alter Godot ship or missile definitions.

## Checkpoint 20b calibration boundary

The Checkpoint 20b common-random-numbers and paired-marginal changes are confined
to `StarCluster.ScenarioRunner`. Godot and `StarCluster.Core` combat behavior are
unchanged. Mechanical TL comparisons remain headless; Godot validation remains
limited to player-facing input and presentation.

## Checkpoint 21 calibration boundary

Moving-target pursuit, range, datalink-loss, reacquisition, and per-launch
missile-effectiveness calibration now execute headlessly through
`StarCluster.ScenarioRunner`. Godot and Core combat behavior are not duplicated
or replaced. Godot remains responsible for player-facing input, rendering,
observer-safe visibility, and presentation smoke checks.

## Checkpoint 21a headless calibration repair

Checkpoint 21a changes only scenario-runner instrumentation, calibration
fixtures, operational timeout classification, and full-flight scheduling.
`StarCluster.Core` missile mechanics and Godot presentation behavior remain
unchanged. Detailed pursuit acceptance continues through the shared headless
Core path; no mechanical Godot validation is required.


## Checkpoint 21c headless boundary

Checkpoint 21c changes scenario-runner diagnostics, statistical comparison
scope, and full-flight scheduling. `StarCluster.Core` combat mechanics and
Godot presentation remain unchanged. Candidate-coordinate Search/Wait, semantic
datalink contracts, scheduler proof, and the 288-variant pursuit calibration
are validated headlessly. No mechanical Godot run is required.

## Checkpoint 21e validation boundary

Checkpoint 21e changes only the headless runner's execution scheduler, garbage
collection mode, performance telemetry, and acceptance gate. Godot continues to
consume the same authoritative Core mechanics. No mechanical Godot validation
is required for this scheduler-only pass.


## Checkpoint 22 validation boundary

Checkpoint 22 optimizes only headless Monte Carlo preparation and observation.
Deterministic scenarios and Godot retain full diagnostics. Authoritative missile
and tactical behavior remains in `StarCluster.Core`; no mechanical Godot
validation is required for this performance-only pass.
