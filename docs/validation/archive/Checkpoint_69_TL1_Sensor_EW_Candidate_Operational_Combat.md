# Checkpoint 69 - TL1 Sensor/EW Candidate Operational Combat

## Scope

Checkpoint 69 follows the accepted Checkpoint 68 deterministic foundation with two agreed changes and one focused operational study:

- add **Balanced-0**: Passive Firm/Approximate **1/3**, normal Active **3/4**, overloaded Active **4/5**;
- remove the range-zero automatic-Firm shortcut so emissions and ECM/ECCM discrimination still resolve at same hex;
- preserve **same-hex LOS cannot be occluded** as an explicit guardrail;
- compare Balanced-0, Balanced-1, and Balanced-2 in integrated tactical combat without promoting any candidate to production.

The operational matrix holds the accepted 35-Space EW-capable build, 5-TP production reactor, FullVolleyFirst doctrine, AcquisitionFirstAutoActive tracking, radius-5 finite map, and 100-fuel baseline constant. Static/dynamic net-EW range subtraction is disabled for the candidate study; the causal Sensor/EW resolver determines track quality directly.

## Acceptance commands

Run these from the repository root on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69\apply_checkpoint_69.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69\apply_checkpoint_69.ps1
```

Deep Calibration is optional:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-69\apply_checkpoint_69.ps1 -DeepCalibration
```

## Expected normal suite

- pinned .NET SDK: **8.0.423**;
- warning-as-error clean build;
- **835** unit tests expected from the CP68 count plus four same-hex Sensor/EW regression tests;
- **9** ScenarioRunner stages;
- **46** ScenarioRunner self-tests;
- deterministic Sensor/EW foundation: **7 profiles x 12 contexts x 11 ranges = 924 rows**;
- deterministic Sensor/EW foundation gates: **18**;
- operational candidate combat: **72 variants x 10,000 trials = 720,000 trials**;
- PowerShell plus pinned .NET only; Python runtime dependencies are rejected before native work.

## Operational candidate matrix

Each leading candidate receives the same 24-variant matrix:

- candidates: Balanced-0, Balanced-1, Balanced-2;
- weapon pairings: Kinetic vs Missile, Energy vs Missile, Kinetic vs Energy;
- movement order: Side A first, Side B first;
- packages:
  1. `clear-normal` - normal sensor operation, no ECM/ECCM;
  2. `clear-overload` - safe Sensor overload when needed, no ECM/ECCM;
  3. `jammed-no-counter` - defending Side B normal ECM, no attacking ECCM;
  4. `jammed-eccm` - defending Side B normal ECM, attacking Side A normal ECCM.

All packages use the same EW-capable construction so component presence does not confound the comparison. Comparison groups pair random streams across candidate/package variants within each weapon/movement lane.

## What to inspect after the normal run

Primary outputs:

- `out/checkpoint-69/tl1-sensor-ew-foundation/candidate-summary.csv`
- `out/checkpoint-69/tl1-sensor-ew-foundation/range-sweep.csv`
- `out/checkpoint-69/tl1-sensor-ew-foundation/gates.csv`
- `out/checkpoint-69/tl1-sensor-ew-candidate-operational-combat/sensor-ew-candidate-operational-combat-review.csv`
- the integrated study's standard summary and gate outputs in the same directory.

Review Balanced-0 versus Balanced-1 first. Their Active and overload envelopes are identical; only passive Approximate range differs (3 versus 2), making this the cleanest test of whether broader passive awareness has operational value without improving passive Firm targeting.

Then compare Balanced-1 versus Balanced-2. Their passive and normal Active envelopes are identical; Balanced-2 overload extends by +2/+2 rather than +1/+1, isolating the value and breakpoint risk of the stronger overload envelope.

Inspect track-quality telemetry, attack denials from unavailable Firm tracks, Active Sensor TP use, overload requests/activations, ECM/ECCM power use, movement/final-range behavior, and family-specific outcomes. Win shares are evidence, not pass/fail targets.

## Interpretation guardrails

A green Checkpoint 69 run proves the causal rules and declared matrix executed correctly. It does **not** automatically select a production sensor envelope.

Do not rebalance weapon ranges, ECM strength, sensor Space cost, reactor output, fuel, or weapon families from one aggregate win-rate number. Candidate promotion should follow the combined evidence on information value, attack eligibility, Tactical Power cost, overload dependence, EW counterplay, geometry, and matchup behavior.

Deep Calibration is not required for initial acceptance because the new 72-variant operational study is already in the must-always-run suite. Run Deep Calibration only if normal results expose a plausible regression in the retained historical dependency area or if specifically requested.
