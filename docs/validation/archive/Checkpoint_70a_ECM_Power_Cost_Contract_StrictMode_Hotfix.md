# Checkpoint 70a - ECM Power-Cost Contract StrictMode Hotfix

## Scope

Checkpoint 70a is a packaging/validation hotfix for Checkpoint 70. It does not change the CP70 ECM/ECCM study, Sensor/EW resolver, combat simulation, candidate ranges, Tactical Power costs, seeds, or balance gates.

The CP70 contract ran under PowerShell StrictMode and directly accessed `sideBEcmNormalPowerCostOverride` on all variants. The nine clear-control variants intentionally omit that optional property, so RepositoryOnly validation stopped before native build/test work. CP70a replaces direct access to optional JSON fields with an explicit PSObject property lookup and validates the intended omission pattern: 90 variants carry an ECM-cost override and nine clear controls omit it; only the 45 matched ECCM-counter variants carry the 1-TP ECCM-cost override.

## Normal acceptance

From a clean extraction on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-70a\apply_checkpoint_70a.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-70a\apply_checkpoint_70a.ps1 -Jobs 24
```

Expected workload is unchanged from CP70: 11 runner stages, 924 deterministic Sensor/EW rows, 99 actual-consumer preflight variants, 99 one-trial smoke executions, and 99 substantive variants / 990,000 default Monte Carlo trials.

## Acceptance intent

1. RepositoryOnly must pass under StrictMode without requiring optional override properties on clear controls.
2. Native build/tests remain warnings-as-errors with the pinned .NET SDK 8.0.423.
3. The actual-consumer preflight and 99-variant one-trial smoke must pass before the substantive study.
4. CP70's experimental semantics remain frozen: normal ECM cost sweep 1-5 TP, matched normal ECCM fixed at 1 TP, Balanced-0 fixed sensor fixture, 5-TP reactor, same-hex LOS unoccludable, and causal ECM/ECCM discrimination unchanged.
5. Deep Calibration remains optional unless normal acceptance reveals an interacting regression.
