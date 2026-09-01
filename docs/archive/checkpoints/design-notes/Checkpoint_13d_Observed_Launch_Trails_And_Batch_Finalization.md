# Checkpoint 13d — Observed Launch Trails and Guaranteed Batch Finalization

## Purpose

Checkpoint 13d resolves the remaining presentation defects exposed by the repeatable Checkpoint 13c encounter:

- a selected missile could leave an obsolete inspected/highlighted hex after moving;
- a mixed batch with two impacts and one surviving salvo could complete authoritatively without completing the observer-view refresh;
- a detected missile's first visible trail did not begin until a later track refresh, omitting an observed launch or an in-flight acquisition point.

The authoritative simulation and observer-safe knowledge boundary remain separate. This checkpoint adds per-entered-hex observation evidence without exposing hidden movement.

## Implemented behavior

### Observed launch and in-flight trail origins

A hostile missile trail begins at the first coordinate the player actually observes:

- if the launcher has a Firm player track and a normal launch occurs, the launch origin is an observed missile coordinate;
- if the launch is not observed, each entered missile hex is checked in order;
- the first detected entered hex starts the trail;
- every continuously detected entered hex extends that trail;
- a missed entered hex closes the segment;
- later reacquisition starts a disconnected segment, even if loss and reacquisition occur during the same tactical turn.

The model never connects an observed coordinate to an unseen launcher or bridges an unobserved interval.

### Per-hex observer diagnostics

The authoritative journal adds explicit contact and trail events:

- `MissileContactAcquired`;
- `MissileContactMaintained`;
- `MissileContactLost`;
- `ObservedTrailSegmentStarted`;
- `ObservedTrailSegmentExtended`;
- `ObservedTrailSegmentClosed`.

Each event identifies the salvo, coordinate, whether the coordinate was the observed launch origin, and whether the observer-safe trail began or extended there.

### Terminal-contact presentation

Terminal salvos are no longer retained as active tactical-map missile markers. Impact and interception remain visible through resolution cues, immediate feedback, and the event journal. A mixed batch therefore removes arrived salvos while keeping surviving active salvos visible.

### Guaranteed batch finalization

Every `Advance unresolved salvos once` action passes through one mandatory finalization path, including batches containing any mixture of:

- in-flight salvos;
- waiting salvos;
- impacts;
- interceptions;
- destroyed or range-exhausted salvos.

Finalization refreshes tracks, rebuilds the observer-safe view, removes terminal markers, normalizes selection, recomputes stacks, creates resolution cues, updates button state, redraws the board, and writes `MissileBatchResolved` followed by `TacticalViewRefreshed`.

A same-hex sensor acquisition is treated as Firm without requesting a zero-length line-of-sight ray. This specifically protects impact finalization when a missile and its target occupy the same coordinate.

Any unexpected resolution, finalization, or redraw exception is written as `MissileBatchFinalizationFailed` with the failed stage and exception details rather than leaving an apparently inert interface.

### Selection follows salvo identity

Missile selection remains keyed by stable salvo ID. After movement or finalization, the inspected coordinate follows the selected visible salvo's current observer-safe coordinate. It clears when the salvo becomes hidden, terminal, or unselected.

## Repeatable validation encounter

Continue using `docs/validation/archive/Tested_Tactical_Regression_Checkpoints_09_Through_17a.md` without changing the scripted movement and actions.

Additional Checkpoint 13d checks:

- Turn 1 and Turn 2 observed launches show trails beginning at the launcher and extending through the observed launch movement;
- a launch outside observation begins its trail at the first detected entered hex, not at the unseen launcher;
- Turn 2 selection/highlight follows `hostile-1` from `(1,2)` to `(2,0)`;
- Turn 3 `hostile-3` remains absent while Unknown;
- Turn 4 mixed resolution shows `IMPACT x2`, removes the two terminal salvos, keeps `hostile-3` visible at `(2,-1)`, disables the resolved-batch command, and journals exactly one batch-finalization pair.

## Automated coverage

Checkpoint 13d adds 12 engine-independent tests covering:

- observed launch origin as a valid trail start;
- first in-flight detection as a trail start when the launcher is unseen;
- continuous per-hex detection;
- segment closure on a missed hex;
- same-turn loss and reacquisition producing disconnected segments;
- same-coordinate reacquisition starting a new segment;
- origin-only observed launch evidence;
- same-coordinate Firm sensor acquisition;
- omission of terminal friendly and hostile salvos from the active tactical view;
- mixed terminal and active salvo views;
- terminal selection normalization.

Expected complete test count: **411**.
