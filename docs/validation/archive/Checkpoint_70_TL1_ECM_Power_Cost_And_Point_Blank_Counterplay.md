# Checkpoint 70 - TL1 ECM Power-Cost and Point-Blank Counterplay

## Scope

Checkpoint 69d is accepted as the implementation/validation baseline. CP70 does not change the causal ECM/ECCM discrimination rule or production equipment values. It adds calibration-only normal ECM power-cost overrides and tests whether opportunity cost under the accepted 5-TP reactor is sufficient to prevent uncountered TL1 ECM from becoming practical point-blank immunity to direct fire.

The active study holds Balanced-0 as a fixed sensor fixture, sweeps Side-B normal ECM cost from **1 through 5 TP**, holds matched Side-A normal ECCM at **1 TP**, and runs both ordinary range-control engagements and fixed same-hex engagements.

## Normal acceptance

From a clean extraction on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-70\apply_checkpoint_70.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-70\apply_checkpoint_70.ps1 -Jobs 24
```

Expected normal workload:

- pinned .NET SDK 8.0.423;
- warning-as-error build;
- existing engine-independent C# tests;
- 11 runner stages;
- 924 deterministic Sensor/EW rows;
- actual-consumer validation of all 99 CP70 variants;
- 99 one-trial smoke executions through the full pipeline;
- 99 substantive variants / 990,000 default Monte Carlo trials;
- ScenarioRunner self-tests.

## Review priorities

1. Inspect the 33 fixed range-zero variants first. A direct-fire Side A should not be judged solely by wins; inspect Firm-track evaluations and track-unavailable preventions as the direct eligibility signal.
2. Compare ECM costs 1-5 without ECCM to determine how quickly power opportunity cost harms the jammer's own offense, sensing, shields, or PDS.
3. Compare the Missile, Energy, and Kinetic jammer contexts. Missile's zero launch-power cost makes the 5-TP endpoint especially diagnostic.
4. Compare matched 1-TP ECCM lanes to confirm that Firm discrimination is restored when funded and to measure the counter's power burden.
5. Do not promote an ECM cost from this checkpoint alone. Production ECM remains 1 TP until the evidence is reviewed.
6. If cost 5 still permits strategically dominant point-blank denial, do not continue escalating TP cost; the next study should test a principled same-hex/discrimination mechanic instead.

Deep Calibration remains optional unless the normal suite identifies an interacting regression.
