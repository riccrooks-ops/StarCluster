# Checkpoint 14 — Sensor Signatures and Electronic-Warfare Foundations

## Purpose

Checkpoint 14 replaces the prototype's fixed range-only sensor check with a data-driven, observer-specific foundation for:

- passive and active sensor modes;
- target signatures, including additional emissions from active sensors;
- deterministic environmental sensing penalties;
- target jamming opposed by observer counter-jamming;
- explicit effective Firm and Approximate envelopes;
- a replaceable sensor-resolution policy for later seeded probabilistic detection;
- immediate event-driven Track Update after sensor or jammer state changes.

The checkpoint does **not** weaken the observer-safe tactical-view boundary, current direct-fire eligibility, once-per-turn track aging, missile range accounting, or occlusion rules established through Checkpoint 13e.

## Accepted rules

### Effective sensor envelope

For this foundation, the same deterministic modifier is applied to the installed sensor's Firm and Approximate ranges:

```text
effective range = base range
                + observer active-mode bonus
                + target signature modifier
                - environmental penalty
                - max(0, target jamming - observer counter-jamming)
```

Both effective ranges are clamped to zero, and the Approximate envelope can never be smaller than the Firm envelope.

The current Godot fixture uses deliberately visible placeholder values:

- Sensors TL 3: Firm 6, Approximate 10;
- active observer bonus: +2 hexes;
- standard ship active-emission signature: +2 hexes;
- missile-plume baseline signature: +1 hex;
- jammer penalty: 3 hexes;
- counter-jamming strength: 1 hex;
- clear-space environmental penalty: 0.

These are test values, not the final TL 1–9 progression.

### Hard geometry remains authoritative

- A star or planet that blocks the sensor line still prevents detection.
- Active sensors and a strong target signature do not see through a blocking body.
- A contact in the observer's own hex is locally acquired as Firm even when nominal range has been reduced to zero.
- Point Defense retains its independent local-acquisition path.

### Active sensing has two effects

- The observer's active mode improves its effective sensor envelope.
- A target operating active sensors contributes an additional active-emission signature to observers evaluating that target.

Active mode is therefore not a free universal upgrade. The final action cost, power use, enemy-awareness consequence, and TL progression remain deferred.

### Jamming and counter-jamming

Jamming is target protection in this checkpoint. When enabled, the target's jammer reduces an observer's effective ranges after the observer's counter-jamming strength is applied. Counter-jamming cannot turn the net penalty negative.

Area jamming, escort jamming, burn-through actions, spoofing, false contacts, decoys, and communications effects remain deferred.

### Resolution-policy seam

`SensorContactEvaluator` computes geometry and all effective modifiers, then delegates the clear-geometry quality decision to `ISensorContactResolutionPolicy`.

The current `DeterministicSensorContactResolutionPolicy` returns:

- Firm inside the effective Firm envelope;
- Approximate inside the remaining effective Approximate envelope;
- Missed beyond the effective Approximate envelope.

A later seeded probabilistic policy can use the same context without changing track repositories, weapon eligibility, missile guidance, Godot presentation, or diagnostic formatting.

### Sensor-state Track Update

Changing active/passive mode or jammer state triggers `TrackUpdateTrigger.SensorStateChanged` immediately. It refreshes information and projections but:

- does not advance the tactical phase;
- does not reopen a resolved movement or weapon command;
- advances missed-track age at most once for that observer-target pair in the current tactical turn;
- records the complete sensor envelope and modifiers in the authoritative journal.

## Engine-independent implementation

New Core types:

- `SensorMode`
- `SensorSignatureProfile`
- `ElectronicWarfareProfile`
- `SensorEnvironmentProfile`
- `SensorContactEvaluationContext`
- `SensorContactEvaluationResult`
- `SensorContactEvaluationStatus`
- `SensorContactResolution`
- `SensorContactResolutionContext`
- `ISensorContactResolutionPolicy`
- `DeterministicSensorContactResolutionPolicy`

Updated Core behavior:

- `SensorProfile` now contains an explicit active-mode range bonus while preserving existing constructor compatibility.
- `SensorContactEvaluator.Observe` remains a neutral backward-compatible path.
- `SensorContactEvaluator.Evaluate` returns the observation plus all diagnostic evidence.
- Per-entered-hex missile observation accepts the same evaluation context.
- Sensor-state changes use the existing epoch-safe Track Update machinery.

## Godot demonstration

The scrollable detail region now contains development controls for:

- player active sensors;
- enemy active emissions;
- player jammer;
- enemy jammer.

Changing any control performs an immediate Track Update. The fixed tactical command area and map viewport remain isolated from the additional text.

A fifth scenario, **Sensor and jamming range gate**, places the two ships eight clear hexes apart:

1. Passive sensors, passive target, jammer off: Approximate.
2. Player active sensors on: Firm.
3. Enemy jammer on: Approximate because the +2 active bonus is opposed by net jamming 2.
4. Enemy active emissions on as well: Firm because the target's +2 signature restores the envelope.

The track panel and JSONL journal show the base ranges, each modifier, net jamming, effective ranges, final sensor evaluation, and normal track transition.

## Tests

Checkpoint 14 adds 19 engine-independent tests covering:

- profile validation;
- neutral backward compatibility;
- active observer range;
- active target emissions;
- quiet signatures;
- deterministic jamming and counter-jamming;
- environmental penalties;
- absolute occlusion;
- same-hex local acquisition;
- custom resolution policy injection;
- out-of-range diagnostics;
- once-per-turn aging under repeated sensor-state misses.

Expected complete suite after application: **440 tests**.

## Local validation

Close Godot, extract the package into the repository root, then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-14\apply_checkpoint_14.ps1
```

Then:

1. Run `docs\validation\Baseline_Tactical_Regression_Encounter.md` unchanged with all Sensor / EW controls at their default passive/off states.
2. Confirm the Checkpoint 13e target eligibility, viewport stability, impact-cue lifetime, hidden-contact behavior, and missile range bookkeeping remain unchanged.
3. Run the focused Sensor / EW range-gate sequence in the validation document.
4. Confirm repeated sensor-state toggles in one turn do not repeatedly increase missed-track age.
5. Confirm no active or high-signature contact can be detected through the central star.
6. Assess the selected-versus-unselected observed missile-trail presentation during the repeated baseline run and record the preferred policy.

## Deferred

- final Sensors & Computing TL 1–9 values;
- sensor power, heat, and tactical action costs;
- damage and crew penalties;
- active-sensor enemy-awareness consequences;
- area and escort jamming;
- burn-through or focused scan actions;
- spoofed coordinates, false contacts, decoys, and deception quality;
- simultaneous-track capacity and report fusion;
- multi-ship data links and track handoff;
- missile seeker acquisition, reacquisition, search patterns, and onboard EW;
- seeded probabilistic detection and recorded random rolls.

## Next candidate checkpoint

After local acceptance, the next focused pass should be **missile seeker acquisition and reacquisition foundations**, using the same signature/EW evaluation context while keeping owner tactical tracks, onboard seeker tracks, and player presentation explicitly separate. False contacts and decoys should remain a later checkpoint unless seeker behavior first proves that the identity and observer boundaries are sound.
