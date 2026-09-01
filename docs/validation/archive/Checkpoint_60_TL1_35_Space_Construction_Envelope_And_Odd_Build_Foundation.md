# Checkpoint 60 - TL1 35-Space Construction Envelope and Odd-Build Foundation

## Purpose

Checkpoint 60 is the first implementation pass after acceptance of the Checkpoint 59 validation scrub. It does **not** change the accepted TL1 combat numbers. It turns the working 35-Installation-Space player-cruiser architecture into an exhaustive deterministic construction envelope, applies the retained TL1 standard Tactical Power demands as a diagnostic, and preserves normal plus deliberately odd legal builds for the next composed-ship Monte Carlo pass.

The active Concept is `docs/Star_Cluster_Game_Concept_v0.6c.docx`. The active construction seed is `docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_2.json`. The detailed architecture note is `docs/design/player_technology/TL1_35_Space_Construction_Envelope_v0_1.md`.

## What changed

- Added `tl1-installation-space-envelope` to ScenarioRunner.
- Added the deterministic study `tl1-space01-35-space-construction-envelope.json`.
- Exhaustively enumerate legal macro designs from the current TL1 footprints: 35 total Space; fixed primary STL 5, FTL 5, tactical computer 3; at least one 6-Space main weapon and one 6-Space main reactor; optional Active Sensor 3, Shield Generator 3, and 2-Space Kinetic PDS installations.
- Leave residual support Space untyped rather than prematurely freezing the AUX/ammunition catalogue.
- Expand each legal macro design across retained TL1 Kinetic, Energy, and Missile main-weapon power patterns.
- Use the accepted 5-TP Operational Fission Reactor and retained K/E/M standard costs 1/2/0 TP, Kinetic PDS readiness 1 TP, and Active Sensor setting-1 cost 1 TP.
- Treat nominal power overcommit as a tactical operating constraint, not a construction-legality failure.
- Preserve six legal reference/odd builds plus one intentional 37-Space illegal dual-main/dual-reactor control for the next simulation pass.

## Expected deterministic envelope

The current study must produce:

- **27 legal macro loadouts**;
- **96 weapon/power variants**;
- **4 exact-fill macro loadouts**;
- maximum **2** main weapons;
- maximum **2** main reactors;
- maximum **5** current-footprint Kinetic PDS installations when other optional major systems are omitted;
- dual-main plus dual-reactor fixed core at **37 Space**, therefore illegal at TL1;
- **5** nominal power-overcommit variants;
- **10** variants exactly consuming installed main-reactor output;
- nominal Tactical Power margin from **-2 to +10 TP**.

These are arithmetic consequences of the current working seed, not final balance targets.

## Default: must always run

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-60\apply_checkpoint_60.ps1 -RepositoryOnly
```

Then:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-60\apply_checkpoint_60.ps1
```

The launcher verifies the Checkpoint 60 architecture/validation contract, then the shared calibration harness performs repository-manifest validation, pinned SDK confirmation, a clean warnings-as-errors build, the xUnit suite, and **7 deterministic runner stages**:

1. accepted deterministic moving-missile scenarios;
2. TL1 Phase A mechanics corpus;
3. TL1 Phase B direct-fire corpus;
4. TL1 35-Space construction envelope and nominal power diagnostics;
5. Auxiliary resource-endurance contracts;
6. deterministic resource-semantics lock;
7. ScenarioRunner self-tests.

The default Checkpoint 60 suite has **0 Monte Carlo variants**.

## Optional: Deep Calibration

Checkpoint 60 retains the same twelve accepted TL1 stochastic studies as Checkpoint 59. Run them only when broader combat-regression evidence is needed or a changed mechanic can plausibly affect their dependency area:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-60\apply_checkpoint_60.ps1 -DeepCalibration
```

At the normal 10,000-trial setting, Deep Calibration remains **1,026 variants / 10.26 million trials**. The new architecture-envelope stage is deterministic and adds no trials.

Because Checkpoint 60 changes ScenarioRunner code but does not change combat mechanics, a clean default run is the release requirement. Running Deep Calibration once is welcome broader regression evidence but is not required by the dependency policy.

## Output to inspect

The new stage writes under `out/checkpoint-60/tl1-installation-space-envelope`:

- `macro-loadouts.csv` - all 27 legal major-system combinations and residual support Space;
- `power-variants.csv` - all 96 weapon-family/power variants;
- `reference-builds.csv` - the six legal stress candidates plus the illegal control;
- `gates.csv` - exact deterministic acceptance gates;
- `summary.json` - envelope and power-margin summary;
- `result-sha256.txt` - deterministic output digest.

## Acceptance

Checkpoint 60 is acceptable when:

1. repository-only validation succeeds on native Windows PowerShell;
2. the normal checkpoint builds with the pinned .NET SDK and zero warnings/errors;
3. all xUnit tests and all 7 configured runner stages pass;
4. the architecture stage reports exactly 27 macro loadouts, 96 power variants, 4 exact-fill macro loadouts, 5 nominal power-overcommit variants, 10 exact-power variants, and zero failed gates;
5. the active Concept and machine-readable baseline agree on the 35-Space architecture and construction-vs-power distinction;
6. no obsolete calibration stage is reintroduced into the active lineup.

## Handoff

After acceptance, inspect the deterministic outputs rather than changing combat numbers immediately. The next checkpoint should compose a deliberately small Monte Carlo ship matrix from the balanced reference and odd legal designs, using the accepted TL1 combat mechanics to diagnose attack density, power starvation/surplus, PDS concentration, defense opportunity cost, pacing, and matchup sensitivity without a target win ratio.
