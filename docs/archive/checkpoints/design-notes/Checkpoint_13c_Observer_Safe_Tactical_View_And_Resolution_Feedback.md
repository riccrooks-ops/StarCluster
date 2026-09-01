# Checkpoint 13c — Observer-Safe Tactical View and Resolution Feedback

## Purpose

Checkpoint 13c closes the information leaks and ambiguous post-resolution presentation found during the repeatable Checkpoint 13b encounter. The authoritative simulation remains unchanged: enemy missiles may move, wait, reacquire, collide, or impact while hidden. The normal tactical map must render only the player's observer-safe knowledge.

## Implemented behavior

### Observer-safe missile view boundary

Godot now consumes one engine-independent `ObserverSafeMissileViewSnapshot` containing only:

- observer-visible missile contacts;
- observer-safe route projections;
- a selected salvo ID only when that salvo is visible to the observer.

Unknown missiles are absent from markers, stacks, tooltips, selection rings, route overlays, and counts. A newly launched enemy missile never force-selects authoritative salvo state.

### Hostile route disclosure

- Friendly missile routes may use the player's own target track.
- A Firm hostile missile contact may show an explicitly observer-side threat projection from the confirmed missile coordinate toward the player's own known coordinate.
- Approximate and Stale hostile contacts do not show an exact projected route.
- Unknown and Lost contacts have no normal tactical marker or route.

The authoritative diagnostic journal still records hidden guidance for development review.

### Observer-safe traveled trails

Observed hostile coordinates now retain their observation epoch. Presentation builds separate trail segments and never draws a continuous line across a missed observation epoch. Reacquisition after hidden movement produces a new segment instead of retroactively revealing the hidden path.

### Batch-resolution feedback

After `Advance unresolved salvos once`, the complete batch now performs:

1. authoritative salvo resolution;
2. track refresh;
3. observer-safe view reconstruction;
4. selection normalization;
5. stack recomputation;
6. impact/interception cue construction;
7. map redraw and observer-safe summary feedback.

The command reports explicit impact counts, visible salvos remaining, and visible waiting salvos. Impact cues remain visible on the map until the next phase transition or tactical action. Pressing the command when no unresolved salvos remain produces an explicit message instead of appearing unresponsive.

### Diagnostic additions

The authoritative journal adds:

- `MissileBatchResolved`;
- `TacticalViewRefreshed`;
- visible contact IDs after the refresh;
- normalized selected salvo ID;
- resolution-cue count;
- player and enemy impact counts.

## Repeatable validation encounter

Use `docs/validation/archive/Tested_Tactical_Regression_Checkpoints_09_Through_17a.md` for each checkpoint until the tactical foundation stabilizes. Upload the matching checkpoint-stamped `.log` and `.jsonl` files plus screenshots of any unexpected state.

## Automated coverage

Checkpoint 13c adds 14 engine-independent tests covering:

- Unknown hostile contacts omitted from the view;
- hidden salvos unable to inflate visible stack counts;
- invalid or hidden selections cleared;
- own missiles remaining visible;
- exact hostile routes withheld for Approximate and Stale tracks;
- Firm hostile threat projections;
- view construction not mutating authoritative flight state;
- continuous observed trails within one or consecutive epochs;
- trail breaks across missed epochs;
- reacquisition never bridging hidden movement.

Expected complete test count: **399**.
