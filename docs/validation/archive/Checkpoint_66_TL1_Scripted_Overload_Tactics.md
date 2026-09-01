# Checkpoint 66 - TL1 Scripted Bounded Overload Tactics

## Objective

Validate the first scripted use of the existing overload/Strain framework on the accepted Checkpoint 65b finite-map battlefield without implementing a full tactical-response AI or changing production balance numbers.

Checkpoint 66 exercises bounded TL1 STL and Active Sensor overload modes at their already-defined Tactical Power windows, preserves bilateral operational sensing, 5-TP production reactors, radius-5 geometry, final-position combat, mirrored movement-order bounds, and the 200/2/+1 tactical fuel rules.

## Permanent native dependency precheck

Checkpoint 66 establishes the no-Python acceptance rule as a shared checkpoint contract rather than a local convention.

For Checkpoint 66 and later, the shared harness requires a `nativeDependencyPrecheck` definition before it proceeds. The precheck must inspect the active apply script, contract, shared harness, guard script, and active normal/deep definitions. Any executable dependency on `python`, `python3`, or `py` in those native paths is a release failure.

The authoritative Windows acceptance path is PowerShell plus the pinned .NET SDK unless a future dependency is deliberately approved.

## Authoritative rules

- Concept: `docs/Star_Cluster_Game_Concept_v0.6e.docx`.
- Tactical Power adjustment windows remain the existing Concept windows; Checkpoint 66 does not invent a reserve pool or reopen earlier allocations.
- TL1 STL Overload I: +1 TP, +1 Move, +2 explicit overload fuel, +1 Strain, Strain Limit 2, Operational-only.
- TL1 Active Sensor Overload I: +1 TP above the normal 2-TP maximum (3 TP total), +2 Firm and +2 Approximate range, +1 Strain, Strain Limit 2, Operational-only.
- Checkpoint 66's scripted doctrine uses safe overloads only and stops before exceeding the Strain Limit. Forced Overload remains a valid rules concept but is not simulated in this diagnostic.
- STL overload decisions are determined before either ship moves. Moving second cannot retroactively overload propulsion.
- Active Sensor overload occurs only at the later legal acquisition boundary.
- Tactical map: radius 5 / 11 hexes across / 91 cells.
- Tactical fuel: 200 start / 2 per traversed ship hex / EvM +1. EvM is off in this matrix.
- Ordinary post-Movement combat uses final positions. Closest approach/path history remains Movement-phase/event/diagnostic evidence.
- No target win rate or family ranking is a release gate.

## Study matrix

The primary study is `tl1-itc09-scripted-overload-tactics`.

**5 ordered weapon pairings x 2 bilateral EW regimes x 4 Side-A overload plans x 2 movement orders = 80 variants.**

Ordered pairings:

- Kinetic vs Missile
- Missile vs Kinetic
- Energy vs Missile
- Missile vs Energy
- Missile vs Missile

Side-A overload plans:

- none
- STL only
- Active Sensor only
- combined STL + Active Sensor

Side B uses no overload policy in this first marginal-value diagnostic. Both sides otherwise use the balanced-generalist construction, TL1 production profile, 5 TP, FullVolleyFirst, bilateral TrackAwareOpponentRange + AcquisitionFirstAutoActive sensing, radius-5 map, and the same fuel rules.

All eight plan/order variants within a weapon-pair/EW lane share a comparison group and seed.

## Repository-only validation

Use a clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66\apply_checkpoint_66.ps1 -RepositoryOnly
```

RepositoryOnly must perform the native dependency precheck before the checkpoint contract/harness path proceeds, then verify the full manifest, PowerShell syntax, checkpoint definitions, active documentation/runbook bindings, historical Checkpoint 65b freezes, exact 80-variant study coverage, overload seed values, and archive hygiene.

## Normal acceptance

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66\apply_checkpoint_66.ps1
```

Expected normal suite: **8 stages / 80 Monte Carlo variants / 800,000 trials at the default 10,000 trials per variant**. Default parallelism is `--jobs 24`.

Native acceptance must use the pinned .NET SDK, clean warning-as-error build, unit tests, and all configured runner stages. The primary overload study must report zero failed gates and zero trial errors.

Primary review artifact:

`out/checkpoint-66/tl1-scripted-overload-tactics/scripted-overload-tactics-review.csv`

## Deep Calibration

Deep Calibration remains optional:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-66\apply_checkpoint_66.ps1 -DeepCalibration
```

Expected deep suite: **25 stages / 1,484 Monte Carlo variants / 14,840,000 default trials**.

Do not run Deep Calibration merely to accept Checkpoint 66 unless the normal study exposes a dependency requiring historical stochastic evidence.
