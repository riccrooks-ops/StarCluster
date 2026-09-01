# Checkpoint 13b — Track-Aging Epochs and Tactical Observability

## Purpose

Checkpoint 13b accepts the Checkpoint 13a automatic journal and corrects the most important behavior it exposed: event-driven sensor reevaluations must not make tracks age several times during one tactical turn. The pass also makes layered interception and collocated missile contacts understandable from the tactical map without requiring the authoritative log.

## Once-per-turn observation epochs

Track visibility continues to be reevaluated after every relevant event, including movement, launch, and missile movement. Successful observations still refresh a track immediately. A failed observation, however, can advance an observer-target track's missed-update age only once during the current observation epoch.

The prototype uses the tactical turn number as the epoch identifier:

- repeated misses during one turn consume at most one age step;
- firing additional missiles cannot accelerate unrelated track loss;
- successful observation in a turn protects the track from later same-turn missed reevaluations;
- the next turn permits one additional missed-observation age step;
- different observers and different targets keep independent epoch state.

`TacticalTrackRecord` retains the last epoch in which it was observed and the last epoch in which a missed observation advanced its age. `TacticalTrackUpdateResult` reports the supplied epoch and whether that reevaluation actually advanced age.

## Collocated missile presentation

Multiple salvos may legally occupy one hex. Presentation now groups observer-visible contacts by coordinate and ownership without merging their identities.

- Friendly and hostile contacts remain separate stacks even when collocated.
- A composite marker displays `F` or `E` plus a visible count.
- Repeated clicks on the same stack cycle through its individual salvos.
- Only the selected salvo's route is emphasized when several routes overlap.
- Pointer and right-panel inspection continue to list each salvo independently.
- Observer-visible stack changes are recorded in the diagnostic journal.

The Core grouping service is presentation-neutral and preserves every stable salvo ID for targeting and diagnostics.

## Layered-defense feedback

The command area now identifies the installed Point Defense System before it fires, including TL, range, automatic local acquisition, and remaining attempt budget. Immediate feedback distinguishes:

- held main-weapon acquisition and attempt;
- PDS acquisition and attempt;
- target salvo;
- miss versus successful interception;
- later missile movement and terminal state.

The main weapon and PDS remain independent defensive layers with separate budgets. Feedback does not change interception eligibility or simulation order.

## Fixed command area

Turn, phase, required actions, phase advancement, current phase commands, PDS readiness, and immediate results remain fixed at the top of the right panel. Scenario detail, inspection, tactical state, and the automatic journal occupy a separately scrollable lower region. Diagnostic volume can no longer push Move, Direct Fire, or Missile controls below the visible panel.

## Causal journal semantics

Missile diagnostics now record a causal lifecycle:

1. guidance starts with track quality, guidance coordinate, route status, and planned route;
2. the actual movement path and distance are recorded;
3. transient defensive acquisition and interception attempts are recorded in resolution order;
4. guidance completes with final status, wait reason, lifetime distance, and remaining range.

The journal distinguishes movement followed by waiting from a missile that never moved. It also records observation epoch, whether track age advanced, and the most recent observed/aged epochs.

## Tests

Checkpoint 13b adds **20** engine-independent tests:

- ten once-per-epoch tracking tests;
- six missile-stack grouping and identity tests;
- four diagnostic-event semantic and ordering tests.

Expected complete suite after application: **385 tests**.

## Local validation

Close Godot, extract the package into the repository root, and run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-13b\apply_checkpoint_13b.ps1
```

Then press F5 and verify:

1. Repeated launch and movement events in one turn do not increase one stale track's missed-update count more than once.
2. A missed track can age once again after the turn advances.
3. Two hostile missiles entering one hex display one red `E` stack with a count.
4. Repeatedly clicking that stack cycles individual salvo IDs and routes.
5. Friendly and hostile missiles at one coordinate remain visually distinct stacks.
6. The PDS is visible as an installed auxiliary before the missile phase.
7. Held-main-weapon and PDS attempts produce immediate, distinct feedback.
8. The command buttons remain visible while the lower diagnostic region scrolls.
9. JSONL and text logs show guidance start, movement, interception, completion, route coordinates, wait reason, and epoch-aging fields in causal order.
10. Reset starts a new checkpoint-13b timestamped encounter pair.

Upload the matching `.log` and `.jsonl` files with screenshots when requesting review.

## Deferred

- final player-facing combat log and animation timing;
- automatic phase advancement after all actors and optional actions are resolved;
- detailed stack-expansion UI for large mixed contact groups;
- sensor signatures, active/passive modes, jamming, spoofing, and countermeasures;
- final TL progression and interception balance.

## Next candidate checkpoint

After local acceptance, the next candidate is sensor-signature and electronic-warfare foundations. Those systems should use the once-per-turn aging model and the expanded journal rather than introducing a separate hidden-information path.
