# TL1 Reactive Pre-Combat EW Sub-Phase Study v0.1

## Purpose

Checkpoint 72 holds the accepted Checkpoint 71 Sensor/EW numbers fixed and tests **timing and Tactical Power commitment**, not new balance values.

The authoritative candidate sequence for this pass is:

1. Movement completes and final post-Movement geometry is known.
2. Normal sensor observations are established.
3. Both sides may commit ECM from remaining Available Tactical Power.
4. Resolve the post-ECM observation state for both sides.
5. Each side may commit ECCM once from remaining Available Tactical Power. `ReactiveNormal` commits ECCM only when the observable post-ECM result was actually degraded by ECM; `Normal` is the automatic comparison doctrine.
6. Resolve final track quality.
7. Direct-fire, missile, and future torpedo combat consume those finalized tracks.

There is **no EW initiative roll**, no alternating last-word chain, and no second ECM response. “Reserved TP” is only shorthand for ordinary Available/uncommitted Tactical Power.

## Frozen TL1 controls

- Balanced-0 Sensor/EW envelope: Passive 1/3, Active 3/4, Overload 4/5.
- Sensor Discrimination Resistance 0.
- same-hex Burn-through Resistance +1; no TL1 burn-through beyond range 0.
- normal ECM 1 rating / 1 TP.
- normal ECCM 1 rating / 1 TP.
- 5-TP production Main Reactor.
- FullVolleyFirst tactical-power doctrine.
- 35-Space `balanced_generalist_ew_major` fixture on both sides.
- Active-first acquisition.
- no STL or Sensor overload.
- no historical static EW range penalty.
- radius-5 map and 100 starting fuel.

## 39-variant matrix

The study uses 39 variants at 10,000 trials per substantive variant.

- **18 unilateral operational**: Kinetic-vs-Missile, Energy-vs-Missile, and Kinetic-vs-Energy; both movement orders; clear, automatic ECCM, and reactive ECCM packages.
- **9 unilateral point-blank**: Kinetic-vs-Missile, Kinetic-vs-Energy, and Energy-vs-Kinetic at fixed range 0; clear, automatic ECCM, and reactive ECCM packages.
- **12 bilateral operational**: the three operational family pairings; both movement orders; both sides running ECM with either automatic ECCM or reactive ECCM.

Paired comparison groups use the same deterministic random stream within each tactical context.

## Questions

Checkpoint 72 is diagnostic. It asks:

- Does reactive ECCM avoid the CP71 point-blank power waste when burn-through already preserves Firm?
- Does reactive ECCM still activate when ordinary-range ECM actually degrades an otherwise Firm observation?
- Can both ships use ECM and independently answer with ECCM without movement initiative creating a last-word EW advantage?
- Does letting EW spend only remaining Available TP create meaningful weapon/PDS opportunity costs without double spending?
- Do finalized EW tracks feed direct-fire and missile combat correctly?

No target win rate is a release gate.

## Deferred movement-phase engagement granularity

Star Fleet Battles was reviewed as a design reference because proportional movement with fire opportunities between movement increments prevents a fast unit from passing through tactically important geometry with no engagement opportunity. Star Cluster does **not** import its 32-impulse system or power-to-speed economy in Checkpoint 72. If future playtesting shows whole-phase Movement creates excessive “bounce/overrun” initiative artifacts, test a much lighter event-driven intermediate engagement window with simultaneous fire commitment.
