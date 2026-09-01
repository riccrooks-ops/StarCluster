# Checkpoint 16 - Launcher-to-Missile Datalink and Retained Reports

## Purpose

Checkpoint 16 replaces the prototype's implicit shared launcher track with an explicit launcher-to-missile datalink foundation. A missile now guides from a report copied into its own state only when its launcher has a live communications path to it. Planetary or stellar occlusion can interrupt later updates without exposing the target's authoritative coordinate.

This pass deliberately stops before missile-local sensors, terminal seekers, and capability-specific launch gating. Its purpose is to make the launcher report an honest, separately aged information source that those later systems can arbitrate against.

## Independent line-of-sight relationships

Two geometric checks remain distinct:

1. **Launcher-to-target sensor LOS** determines what report the launcher owns.
2. **Launcher-to-missile datalink LOS** determines whether that report can be copied to the missile.

`MissileDatalinkService.EvaluateLink` uses the common direct-fire line-of-sight geometry. The link is:

- `Unavailable` when no receiver is installed;
- `Live` when the profile does not require LOS, the launcher and missile share a hex, or LOS is not blocked; and
- `Blocked` when a star or planet blocks launcher-to-missile LOS.

A live datalink does not improve the launcher's target track. A blocked target sensor path and a blocked missile communications path are separate facts.

## Copied missile-owned reports

`MissileDatalinkReport` is an immutable copied value containing:

- target ID;
- quality received from the launcher;
- copied guidance coordinate;
- launcher observation epoch;
- missile guidance phase in which the copy arrived; and
- retained age in missed guidance phases.

`GuidedMissileSalvo` owns the retained report. It never stores a reference to a mutable launcher track and never queries the target ship directly.

At the start of each missile action:

1. Evaluate launcher-to-missile LOS.
2. If the link is Live and the launcher report has a usable coordinate, copy it and reset retained age to zero.
3. Otherwise retain the prior copy and age it once for that guidance phase.
4. Convert the missile-owned report into the guidance snapshot consumed by `MissileGuidanceService`.

A fresh Current, Approximate, or Stale report preserves its delivered quality at age zero. After one missed delivery, any retained usable report is Stale. The copied coordinate remains unchanged while blocked even if the launcher later owns a different target coordinate.

## Bounded retention and expiration

`MissileDatalinkProfile.MaximumRetainedReportAgePhases` controls how long a retained report remains usable. The Checkpoint 16 development profile uses three missed guidance phases.

- Age zero: use the delivered quality.
- Age one through the configured maximum: use Stale guidance at the copied coordinate.
- Age beyond the maximum: guidance becomes Lost and exposes no coordinate.

A live link with no usable launcher coordinate does not erase the retained copy; it ages the copy just as a blocked or unavailable link does. Restored LOS plus a usable launcher report replaces the old copy and resets age.

Repeated same-phase evaluations do not age the report twice. This protects the model when later checkpoints add per-entered-hex link checks and local sensor events.

## Action-start delivery and action-end state

Checkpoint 16 delivers reports at missile-action start. After movement, it reevaluates and records the final link state without delivering or aging another report.

This means a missile that moves out from behind a planet can end the action with a Live datalink, but receives the launcher's next copy at the beginning of its following missile action. A missile that moves behind a planet can end the action Blocked after already using the report delivered at action start. No movement, cumulative range, or report age is refunded or duplicated.

The separate public `RefreshLinkState` operation establishes the seam needed for later per-step communications behavior without coupling datalink ownership to Godot.

## Guidance provenance and presentation

`MissileGuidanceReportSource` currently records:

- `FreshDatalink`;
- `RetainedDatalink`; or
- `None`.

The authoritative journal writes this provenance into datalink and guidance events. Friendly observer-side route projections now use the missile's own last consumed guidance coordinate rather than silently substituting the player's newer ship track. Enemy datalink state is not added to normal player-visible contact summaries.

## Diagnostics

Each missile action records:

- an action-start `MissileDatalinkUpdated` event;
- launcher and missile coordinates;
- datalink state and LOS quality;
- launcher track quality;
- whether a report was delivered or retained;
- whether retained age advanced or expired;
- copied coordinate and source epoch;
- effective guidance quality and guidance source; and
- an action-end state-only `MissileDatalinkUpdated` event after movement.

The action-end event explicitly performs no report delivery and no aging.

Checkpoint 16 also clarifies missile-batch accounting. `MissileBatchResolved` now records separately:

- launches resolved earlier in the phase;
- existing salvos advanced by the batch; and
- total missile actions resolved in the phase.

## Godot development profile

The current demo missile has:

- an installed TL2 datalink receiver;
- required launcher-to-missile LOS; and
- a maximum retained-report age of three missed guidance phases.

The existing demo still permits generic Stale-track launches because capability-specific launch eligibility is not yet enforced. That later gate will distinguish command-guided, seeker-only, sensor-only, and sensor-plus-seeker missiles.

## Tests

Checkpoint 16 adds seventeen engine-independent tests covering:

- profile validation;
- unavailable, same-hex, clear, and blocked links;
- Current and Approximate report copying;
- blocked-link retention and quality degradation;
- copied-coordinate independence from newer blocked launcher data;
- once-per-guidance-phase aging;
- restored-link replacement;
- live-link/no-coordinate retention;
- profile-defined expiration;
- state-only action-end refresh; and
- datalink-aware launch-service integration; and
- friendly observer-safe projection from the missile's consumed report rather than a newer observer track.

Expected complete engine-independent suite after application: **470 tests**.

## Apply

With Godot closed:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-16\apply_checkpoint_16.ps1
```

Then run the Checkpoint 16 focused datalink check in `docs\validation\Baseline_Tactical_Regression_Encounter.md` and preserve the checkpoint-stamped JSONL/readable logs and requested screenshots.

## Deliberately deferred

- missile-local sensor repositories and observation timing;
- passive/active missile sensor mode switching;
- launcher/local report arbitration;
- command-guided, seeker-only, sensor-only, and sensor-plus-seeker launch gates;
- terminal local acquisition and seeker lock;
- communications jamming, latency, bandwidth, relays, and spoofing;
- waiting/search endurance; and
- mid-action report delivery after a link is restored during missile movement.
