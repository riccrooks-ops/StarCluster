# Checkpoint 29 - Revised Evasive Maneuvering and Complete TL1 Weapon Matrix

Checkpoint 29 extends the accepted Checkpoint 28 calibration foundation with the complete stripped-down TL1 kinetic-energy-missile matrix.

It revises Evasive Maneuvering from -10 incoming / -10 own fire to -10 incoming / -5 own direct fire, updates every deterministic and stochastic direct-fire lane to the new value, and adds a 48-variant paired weapon-family study.

The missile layer uses the accepted provisional TL1 values: 24 Missile Flights, zero launch Tactical Power, DAM 5, SPEN 1, APEN 2, Speed 1, Maximum Range 6 traveled hexes, and 55% terminal Guidance. Missile routes are recalculated against target movement each action, traveled range is cumulative, and already-launched missiles continue after launcher destruction.

The study includes mirror and cross-family range tests, all side swaps, EvM, Guidance, warhead, ammunition, range, speed, and outrun controls. It is intended to expose impossible penetration, hard stalls, ammunition exhaustion, range exhaustion, and uncaught targets before subsystem counters are introduced.

Checkpoint 29 does not add ECM, ECCM, PDS, richer Tactical Power doctrines, or final weapon-balance rulings.


## Checkpoint 29a release-process hotfix

Checkpoint 29a archives the Checkpoint 28 validation runbook before manifest locking and adds `tools/checkpoints/checkpoint-29/build_checkpoint_29_release.ps1`. The release builder must complete repository normalization, the complete warnings-as-errors acceptance suite, an idempotence preflight, isolated staging, ZIP creation, and post-archive release validation in that order. This prevents normalization from creating repository-owned files that are absent from the manifest.


## Checkpoint 29b hotfix

Checkpoint 29b corrects the repository README release identity by explicitly naming active Concept v0.4a. The pre-archive builder now validates required README metadata before normalization, build, manifest staging, or ZIP creation. No combat mechanics, scenario definitions, baseline values, workbook content, or Concept decisions changed.

## Checkpoint 29c hotfix

Checkpoint 29c corrects the workbook validation contract to require the retained `Checkpoint 28 Energy` sheet and the new `Checkpoint 29 Matrix` sheet. The prior validator incorrectly requested a nonexistent `Checkpoint 29 Energy` sheet. The pre-archive builder now validates these exact sheet names directly from the packaged workbook before release. No mechanics or calibration inputs changed.
