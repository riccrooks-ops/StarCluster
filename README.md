# StarCluster.ScenarioRunner

`StarCluster.ScenarioRunner` is the headless deterministic/calibration consumer for Star Cluster's engine-independent rules. It executes versioned scenario and study documents against `StarCluster.Core`, emits machine-readable evidence, and provides self-tests for runner semantics.

## Current role

Use the active checkpoint script under `tools/checkpoints/` for normal release acceptance. The checkpoint definition determines which commands belong to the must-always-run suite and which longer studies belong to opt-in Deep Calibration. Historical existence alone is not a reason to rerun an expensive Monte Carlo stage.

The runner's responsibilities are:

- deserialize and validate scenario/study inputs before substantive execution;
- consume the same Core rules or explicitly documented calibration models used by the study;
- emit deterministic diagnostics, summaries, CSV evidence, release gates, and SHA-256 evidence hashes;
- preserve player-information parity in AI doctrine studies;
- keep historical study inputs reproducible even when later architecture clarifies how a calibration field should be interpreted.

## Degraded-fire study interpretation

Retained integrated-combat studies contain fields such as `sideAApproximateDirectFireAccuracyPenalty`. These are historical calibration overrides. Current architecture interprets such a value as the **universal -25 percentage-point Approximate-track penalty** being tested for a weapon that the study explicitly enables for Approximate-track fire. Production `DirectFireWeaponProfile` owns only permission to use degraded fire; it does not own the numerical penalty.

Ordinary missiles do not inherit direct-fire degraded-fire behavior. Any future Approximate-target missile capability must be implemented and validated as a separate missile-profile rule.

## Direct execution

Direct runner commands remain useful for focused development, but release acceptance should normally use the checkpoint harness so manifest, dependency, build, unit-test, smoke/preflight, and stage accounting cannot be skipped accidentally.

Historical command-by-command checkpoint notes are retained in `docs/archive/source-readmes/StarCluster.ScenarioRunner_README_historical_checkpoint_commands.md`.
