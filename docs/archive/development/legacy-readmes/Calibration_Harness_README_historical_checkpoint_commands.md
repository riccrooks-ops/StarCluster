# Headless C# Calibration Lane

This directory contains the stable, Godot-independent calibration harness used by current and future Star Cluster technology checkpoints.

## Authority boundaries

- `StarCluster.Core` is the single authoritative rules implementation.
- `StarCluster.ScenarioRunner` loads scenario data and executes deterministic and Monte Carlo studies.
- `StarCluster.Tests` supplies engine-independent behavioral tests.
- `StarCluster.Game` and Godot are validated separately at integration milestones.

Routine calibration does not parse README, Concept, workbook, or C# prose to infer mechanics. Mechanical acceptance comes from compiled C# tests, typed scenario validation, study execution, and process exit codes. Documentation is reported as present or missing, but it cannot block calibration.

## Stable harness

Run a versioned checkpoint definition through:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\calibration\run_calibration_checkpoint.ps1 `
  -CheckpointDefinition .\tools\calibration\checkpoints\checkpoint-36.json
```

Checkpoint wrappers under `tools/checkpoints/` contain only parameter forwarding. They must not add checkpoint-specific assertions.

## Definition format

Checkpoint definitions use schema version 1 and declare:

- pinned .NET SDK and configuration;
- headless solution, test project, and runner project;
- repository manifest and output root;
- default trial and worker counts;
- optional non-blocking documentation paths;
- ordered ScenarioRunner commands and arguments.

The stable harness validates the typed definition, repository paths, unique stage IDs, positive defaults, manifest hashes, PowerShell syntax, the pinned SDK, build/test exit codes, and every configured runner exit code. Checkpoint 36 also writes incremental `acceptance-summary.json` and `acceptance-summary.txt` files in the output root and finalizes success or first failure.

## Integration lane

Use `tools/integration/run_full_solution_validation.ps1` at major integration milestones. It builds the full solution, including `StarCluster.Game`, and runs the shared test project. Routine calibration checkpoints do not require Godot or the game project.

## Checkpoint 35

The Checkpoint 35 definition adds the `tl1-range-control-calibration` runner stage while reusing the same harness unchanged. The wrapper under `tools/checkpoints/checkpoint-35/` contains parameter forwarding only.


## Checkpoint 36

The Checkpoint 36 definition retains every accepted lane, adds `tl1-internal-damage-calibration`, and expects 12 ScenarioRunner stages. The wrapper under `tools/checkpoints/checkpoint-36/` contains parameter forwarding only. Successful runs preserve concise acceptance summaries in `out/checkpoint-36`.

## Checkpoint 37

`tools/calibration/checkpoints/checkpoint-37.json` runs 13 stages and replaces the historical 80-variant internal-damage policy study with:

- `tl1-damage-control-calibration`: 64 variants with explicit eligibility, five calibration Repair Kits, four doctrines, and separate Hull/component accounting;
- `tl1-combat-pacing`: 8 mirror-duel variants comparing 25%/33 1/3%, ordinary/Protected placement, Damage Control off/on, >18-turn frequency, mission kills, and following-turn Immobile Target timing.

Use `tools/checkpoints/checkpoint-37/apply_checkpoint_37.ps1`. At 10,000 trials the Monte Carlo workload is 779 variants and 7,790,000 trials.
## Checkpoint 38

`tools/calibration/checkpoints/checkpoint-38.json` runs 14 stages. It retains the accepted 48-variant weapon matrix and 75-variant scripted relative-range study, then adds `tl1-integrated-tactical-combat`: 90 cross-family variants using shared scripted/preferred-range policies, simultaneous STL-conditioned range resolution, independent missile travel, 33 1/3% critical density, normal three-kit Damage Control, Protected Compartmentation, and following-turn Immobile Target timing.

Use `tools/checkpoints/checkpoint-38/apply_checkpoint_38.ps1`. At 10,000 trials the Monte Carlo workload is 869 variants and 8,690,000 trials.



## Checkpoint 39

`checkpoints/checkpoint-39.json` retains all accepted lanes and adds a 44-variant movement, kinetic, defense, and engagement-termination diagnostic stage. Production integrated combat uses ship Move = Drive TL, missile Move = Missile Drive TL + 1, TL1 kinetic DAM 4/APEN 0, AP 0 production armor, zero-TP missile launch, and a 25-Flight missile magazine. The kinetic comparison arms use AP 1 diagnostic armor so APEN remains measurable. Disengagement requires an explicit withdrawal objective and three consecutive qualifying Open turns.

## Checkpoint 40

`checkpoints/checkpoint-40.json` retains all accepted lanes and adds `tl1-minimal-tactics-baseline`: 113 variants containing a 36-variant AP 0 Range 2-5 ordered-family grid, a complete 36-variant AP 1 diagnostic grid, and Range 4 single-factor controls for Damage Control, Evasive Maneuvers, Protected Compartmentation, base Shield recharge, and PDS. Review bands are non-blocking; typed coverage and mechanics contracts remain blocking.

Use `tools/checkpoints/checkpoint-40/apply_checkpoint_40.ps1`. At 10,000 trials the Monte Carlo workload is 1,026 variants and 10,260,000 trials.

## Checkpoint 48

`checkpoints/checkpoint-48.json` runs 24 stages. It retains the complete accepted corpus, formally uses the accepted `tl2-production` profile, and adds `auxiliary-single-slot-performance-screening`: 1,455 variants containing 1,323 legal one-AUX comparisons and 132 isolated no-AUX diagnostics across TL1v1, TL2v2, TL1v2, and Kinetic/Energy/Missile same-family contexts.

Use `tools/checkpoints/checkpoint-48/apply_checkpoint_48.ps1`. At 10,000 trials the Monte Carlo workload is 6,013 variants and 60,130,000 trials.

## Checkpoint 66+ native dependency contract

Starting with Checkpoint 66, checkpoint definitions must declare a required `nativeDependencyPrecheck`. The shared harness enforces it before repository/output/native work. The active Windows acceptance path must not depend on `python`, `python3`, or `py`; supported native dependencies remain PowerShell plus the pinned .NET SDK unless a future dependency is deliberately approved.
