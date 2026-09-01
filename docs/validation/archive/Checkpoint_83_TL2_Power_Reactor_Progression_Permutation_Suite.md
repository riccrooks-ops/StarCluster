# Checkpoint 83 - TL2 Power / Reactor Progression Permutation Suite

## Purpose

Checkpoint 83 extends the standing Technology Integration Permutation Suite with **Power / Reactor** as a first-class axis. It revalidates the historical TL2 Reactor-6 evidence as a deliberately narrow **Early Practical Fusion 6-TP Operational-output candidate** against the accepted 5-TP Peak-Fission reference.

No production reactor value is changed by the checkpoint definition. The candidate keeps the Main Reactor footprint at 6 Space and changes only Side-A normal Operational Tactical Power from 5 to 6. Reactor condition mapping, overload, efficiency, storage, auxiliary generation, footprint reduction, prerequisites, and reliability remain deferred.

## Native acceptance

Run repository validation first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-83\apply_checkpoint_83.ps1 -RepositoryOnly
```

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-83\apply_checkpoint_83.ps1 -Jobs 24
```

Expected normal workload: 11 runner stages, approximately 863 unit tests, 48 ScenarioRunner self-tests, 96 one-trial smoke executions, and 96 substantive variants / 960,000 default substantive trials.

## Review focus after a clean run

Review the paired 6-TP minus 5-TP deltas by information-control environment and matchup. In particular:

- how much 6 TP reduces insufficient-power prevention;
- whether high-demand Energy/Missile packages benefit more than low-demand clean/direct-fire packages;
- whether the wide old-Sensor + ECCM2 route becomes viable without dominating the contemporary DR1 + ECCM1 route;
- whether -25 degraded fire remains a fallback rather than an ECCM substitute;
- whether the extra TP erases useful power choices in environments where the fifth point was already sufficient;
- whether 6 TP at the same 6-Space footprint represents a meaningful output-density frontier without requiring an arbitrary anti-stacking rule.

Deep Calibration is not required unless normal acceptance exposes a broader regression.
