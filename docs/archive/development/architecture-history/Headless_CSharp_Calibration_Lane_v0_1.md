# Headless C# Calibration Lane v0.1

## Design rule

Star Cluster has one authoritative rules implementation: `StarCluster.Core` in C#. The calibration runner and the Godot game both consume that library.

## Why calibration is separate from Godot

Technology calibration changes numerical inputs, fixed doctrines, and scenario matrices frequently. Requiring the complete Godot application and release-document scaffolding for each experiment adds failure points that do not test the combat rules. A headless lane preserves rapid iteration without introducing a second simulator.

## Mechanical ownership

- Core: state transitions, combat ordering, resources, damage, sensors, missiles, and power.
- ScenarioRunner: structured inputs, deterministic/Monte Carlo orchestration, gates, and reports.
- Tests: direct behavioral contracts.
- Game: presentation, input, scenes, save integration, and Godot adapters.

## Harness ownership

The shared PowerShell harness performs only orchestration and repository integrity. It does not infer mechanics by searching source text or documentation. Mechanical correctness belongs in compiled C# tests and executable scenario validation.

## Checkpoint definition

Each calibration checkpoint supplies a JSON definition containing paths, workload defaults, and ordered runner commands. The stable harness is changed only when the calibration platform itself changes.

## Integration cadence

Godot integration runs at major milestones: completed subsystem groups, movement/geometry integration, complete TL1 combat, and production-facing UI transitions. This prevents long-lived integration drift while avoiding a full game build for every balance pass.
