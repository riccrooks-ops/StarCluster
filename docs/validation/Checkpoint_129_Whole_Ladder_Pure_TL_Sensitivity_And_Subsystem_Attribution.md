# Checkpoint 129 — Whole-Ladder Pure-TL Sensitivity and Subsystem Attribution

## Status

Corrected Replacement 1 candidate pending native Windows acceptance. CP128 is the accepted frozen main-subsystem numerical/documentation/evidence baseline. CP122 Corrected Replacement 1 remains the accepted production implementation baseline.

## Purpose

CP129 performs the first broad sensitivity study after the main-subsystem table freeze. It does **not** change a technology value, production C# gameplay source, or scenario definition, and it does **not** construct legal mixed-TL ships. The new research consumer uses the accepted full radius-5 System Map and physical-entity RNG ownership to measure whole-ladder progression and transition-local marginal subsystem effects.

## Corrected Replacement 1 repair

The original CP129 candidate passed preflight, 176 Python tests, native build, xUnit, ScenarioRunner/parity, plan reconstruction, and physical symmetry, then failed at RepositoryOnly stage 9 while writing the smoke-lane summary with `ValueError: dict contains fields not in fieldnames: 'changed_fields'`. The first three baseline smoke rows lacked that key while holdback rows added it. Corrected Replacement 1 makes the smoke summary schema explicit and uniform and adds a permanent serialization regression. No gameplay or research workload changed.

The wrapper now also accepts `-Jobs <1-61>` (default 24). This is a performance-only control; RepositoryOnly and substantive worker counts are recorded independently.

## Required native sequence

Run from a clean extraction at the repository root. The substantive command intentionally requires the successful RepositoryOnly marker from the same unchanged extraction.

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-129\apply_checkpoint_129.ps1 -RepositoryOnly -Jobs 24
```

RepositoryOnly must pass before continuing. It validates:

- Python 3.13 and pinned .NET SDK 8.0.423;
- pre-package/evidence ZIP hygiene;
- CP128 native provenance and frozen current numerical/document authorities;
- stdlib-only active Python acceptance surface;
- 177 Python tests;
- warning-as-error native build;
- 907 xUnit tests;
- 70 ScenarioRunner self-tests;
- 25 C#/Python research-parity fixtures;
- deterministic CP129 plan reconstruction;
- 2,250 physical-symmetry comparisons / 4,500 executions with zero mismatches; and
- all 626,028 one-trial pipeline variants with zero trial errors.

Then, in the same extraction, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-129\apply_checkpoint_129.ps1 -Jobs 24
```

The substantive phase consumes the accepted RepositoryOnly marker, revalidates repository/preflight contracts, and executes **45,665,000 engagements** across 626,028 variants. You may choose a different valid `-Jobs` value for this phase without changing study semantics.

## Study lanes

### A. Whole-ladder control

All 9,427 legal pure-TL builds remain represented against every opponent TL. Pairing identity, weighting, seeds, side assignments, mover orders, map geometry, and physical RNG ownership are deterministic. The overlapping adjacent-TL subset must reproduce the accepted CP127 full-map adjacent summary exactly.

### B. Main-only adjacent control

Only PDS and Shield Hardener are removed. This controls for the two deferred optional/support choices most likely to obscure main-subsystem interpretation while preserving ECM/ECCM, Shields, duplicate Main Weapons/Reactors, and Missile payload branches.

### C. Matched-composition performance holdbacks

For every adjacent TL transition and each of ten main combat packages—Hull, Armor, Reactor, STL, Computer, Sensor, ECM, ECCM, Shield, and installed offense—the higher-TL side temporarily uses the lower-TL **performance** characteristics while retaining its higher-TL construction footprint and composition. These counterfactuals are not legal ship designs and cannot promote a mixed-TL component rule.

### D. Construction-envelope sensitivity

Hull capacity and main-system Space progression are re-enumerated separately. This measures how miniaturization/capacity changes alter the legal build universe without confounding them with combat-stat effects.

## Interpretation limits

- Adjacent-TL win rates are not targets.
- Marginal holdback effects are non-additive because subsystem interactions are real.
- Damage Control has no current tactical performance holdback because the research combat consumer does not schedule it.
- FTL has no tactical performance holdback because it is strategic.
- Most AUX numerical stabilization remains deferred.
- A frozen main-table value should be reopened only for a concrete pathology supported by the broad evidence; this checkpoint does not auto-promote changes.
- Raw per-variant CSV detail is transient and is removed after aggregate analysis; deterministic study definitions, seeds, task plans, pairing aggregates, summary tables, and acceptance records remain.

## Expected workload

- raw build combinations: 14,112
- legal pure-TL builds: 9,427
- whole-ladder base pairings: 70,034
- whole-ladder variants: 280,136
- main-only legal builds: 1,856
- main-only adjacent variants: 7,136
- matched-composition adjacent tasks: 7,699
- matched variants per sensitivity condition: 30,796
- sensitivity conditions: 11 (baseline + 10 packages)
- sensitivity variants: 338,756
- total variants / one-trial smoke: 626,028
- substantive engagements: 45,665,000

## Evidence handoff

After both commands succeed, zip `out\checkpoint-129` and return it for assessment. Do not run an additional calibration mode; CP129 has one substantive study only.
