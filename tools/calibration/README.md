# Headless Calibration Harness

`tools/calibration` contains the stable native-Windows orchestration layer for deterministic and Monte Carlo validation. It is not a second rules engine.

## Authority boundaries

- `StarCluster.Core` owns game mechanics and state transitions.
- `StarCluster.Tests` owns direct deterministic behavioral contracts.
- `StarCluster.ScenarioRunner` consumes Core through versioned scenarios/studies and emits evidence.
- `StarCluster.Game` is the Godot presentation/input host and does not define calibration mechanics.
- the active Concept and focused architecture notes define current design intent; retained historical study inputs remain evidence rather than automatic current authority.

## Normal checkpoint workflow

Run the active wrapper under `tools/checkpoints/checkpoint-<id>/`. The wrapper performs the native-dependency precheck, checkpoint-specific repository/architecture contract, then calls the shared harness with the active JSON definition.

The shared harness validates the pinned .NET SDK, repository manifest, PowerShell syntax/dependencies, warning-as-error build, xUnit tests, ordered ScenarioRunner stages, stage exit codes, evidence outputs, and acceptance-summary accounting. Checkpoint-specific mechanical assertions belong in compiled tests, executable runner validation, or the checkpoint contract; the harness itself remains generic.

## Validation tiers

Current checkpoints distinguish **must-always-run** deterministic/core validation from optional **Deep Calibration**. Historical Monte Carlo stages are not rerun merely because they exist. A stochastic study belongs in the active path only when the changed mechanic or a declared dependency can affect its conclusions, or when a competing candidate is deliberately being evaluated.

Any new or materially changed runner study must include an actual-consumer preflight and a tiny full-pipeline smoke before substantive Monte Carlo execution. Successful statistical gates create evidence; they do not automatically promote balance values, technology, or AI doctrine.

## Native dependency contract

The active Windows acceptance path uses PowerShell plus the pinned .NET SDK. Checkpoint definitions declare `nativeDependencyPrecheck`, and the guard rejects accidental Python dependencies in the native release path unless a future dependency is deliberately approved.

## Historical definitions

Older checkpoint definitions and scenario inputs remain at stable paths when required for reproducibility or Deep Calibration. Their presence does not make their old workload, terminology, or design assumptions current. The former accumulated checkpoint-by-checkpoint README is preserved at `docs/archive/source-readmes/Calibration_Harness_README_historical_checkpoint_commands.md`.
