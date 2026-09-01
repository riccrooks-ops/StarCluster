# Checkpoint 15 - Hybrid Incremental Tactical Ship Movement

## Purpose

Checkpoint 15 implements the accepted hybrid tactical movement model. The player may select one adjacent hex, reassess, and then select any farther legal destination within the reduced allowance. A distant selection remains a convenience command only: every traversed hex is committed and observed separately by the authoritative simulation.

This pass also incorporates the Concept-document print-layout correction requested after Checkpoint 14a and records the refined missile launch-eligibility rules.

## Authoritative movement state

`ShipMovementTurnState` records:

- the movement-phase starting coordinate;
- maximum movement allowance;
- every entered coordinate in order;
- distance spent and remaining movement; and
- whether movement has ended.

`ShipMovementTurnService` provides the shared Core operations used by human input, later AI movement, and later automatic routes:

- begin one movement action;
- plan any destination using the remaining allowance;
- recompute legal destinations from the current coordinate;
- commit exactly one adjacent step; and
- end movement early without refunding or rewinding executed steps.

The prior one-command `ShipMovementService` remains for compatibility, but the Checkpoint 15 Godot flow uses the new turn-scoped service.

## Hybrid Godot interaction

During Movement:

1. All currently reachable destinations are highlighted.
2. Adjacent one-step destinations receive a stronger outline.
3. Clicking any highlighted hex previews the deterministic route from the ship's current coordinate using only remaining movement.
4. **Move to destination** executes the route one entered hex at a time.
5. After each entered hex, Core movement state, ship position, tracks, line of sight, missile presentation, and the remaining legal destination set refresh.
6. If movement remains, the player may select another adjacent or distant destination.
7. **End movement** consumes the movement action with any unused allowance left unspent.
8. If an automatic multi-hex route acquires a previously Unknown hostile missile before reaching the selected destination, execution pauses after the committed step so the player can reassess. Executed steps are never undone.

Movement allowance exhaustion completes movement automatically.

## Per-step Track Update semantics

Each entered ship hex triggers `ShipMovementStepCommitted` in the current turn's observation epoch. Diagnostics record:

- one `ShipMovementDestinationCommitted` event for each selected route;
- one `ShipMovementStepResolved` event per entered hex; and
- one `ShipMovementResolved` event when movement ends or the allowance is exhausted.

Visibility loss after a successful observation in the same epoch now changes the track immediately to **Stale** at the most recent observed coordinate, without consuming an additional tactical-time age step. Repeated misses in that epoch still cannot accelerate aging. This allows a ship moving behind a planet to leave the observer with the last intermediate hex it actually saw, rather than the movement command's starting coordinate.

This is the required foundation for later missiles to maintain, lose, or regain launcher and onboard tracks while moving around major bodies.

## Missile launch-eligibility design contract

The detailed missile architecture remains documented rather than implemented in this checkpoint. The accepted minimum launcher-track rules are now explicit:

| Missile capability | Minimum launch information |
|---|---|
| Command-guided; no onboard sensor or seeker | Current Firm launcher track and live launcher-to-missile datalink |
| Seeker-only | Current Firm or Approximate launcher track |
| Sensor-only | Firm, Approximate, or a data-defined usable Stale report |
| Sensor plus seeker | Firm, Approximate, or a data-defined usable Stale report |

A Stale launch for a sensor-equipped missile must be limited by report age and missile search capability. A launcher blocked by a planet may launch such a weapon toward the last observed intermediate coordinate; the missile will later require its own permitted acquisition behavior to continue effectively.

## Concept document correction

Concept v0.3m:

- preserves v0.3l exactly in `docs/archive`;
- adds the Checkpoint 15 hybrid movement and per-step track-loss decisions;
- clarifies missile launch eligibility;
- constrains Section 18's table and both appendix tables to the normal printable text width with standard page margins; and
- validates all pages through the DOCX render-and-review workflow.

## Tests

Checkpoint 15 adds twelve movement-service tests and one focused same-epoch visibility-loss test. Expected complete engine-independent suite after application: **453 tests**.

## Apply

With Godot closed:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-15\apply_checkpoint_15.ps1
```

Then run the Checkpoint 15 focused movement check in `docs\validation\Baseline_Tactical_Regression_Encounter.md` and preserve the checkpoint-stamped JSONL/readable logs and requested screenshots.

## Deliberately deferred

- missile-local sensors and passive/active switching;
- launcher-to-missile datalink LOS;
- missile launch gating by installed capability;
- seeker acquisition and terminal lock;
- target-entry and target-departure missile observations;
- automatic alternate-route selection and player-chosen waypoints beyond committing an intermediate destination first; and
- enemy/AI use of the shared step service.

## Consolidated package and rerunnable application

The complete Checkpoint 15 archive includes the entire checkpoint overlay, the corrected hybrid-movement test fixture, the exact Checkpoint 14a Concept keeper, and the focused validation wording. The applier accepts the prior Concept keeper from either its root location or the archive location and does not retire the root copy until validation, build, tests, and architecture checks all succeed. A failed application can therefore be corrected and rerun without reapplying Checkpoint 14a.
