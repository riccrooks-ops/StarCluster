# Checkpoint 71 - Sensor Discrimination Resistance and Burn-through

## Scope

Checkpoint 71 builds on the accepted Checkpoint 70a baseline. CP70a established that ECM Tactical Power cost alone does not solve same-hex Firm-track denial. CP71 changes the Sensor/EW discrimination model without changing physical sensor range, normal ECM/ECCM cost, weapon power, missile guidance, or direct-fire Firm eligibility.

The new profile fields are intrinsic Sensor Discrimination Resistance and Point-Blank Burn-through Resistance. The CP71 TL1 catalog sets these to 0 and +1 respectively. Old catalogs omit both fields and therefore remain at zero, preserving historical CP69/CP70 behavior.

The Concept also records degraded fire as a future weapon-specific trait; it is not implemented here.

## Normal acceptance

From a clean extraction on native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-71\apply_checkpoint_71.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-71\apply_checkpoint_71.ps1 -Jobs 24
```

Expected normal workload: 11 runner stages, 924 deterministic Sensor/EW rows, 27 actual-consumer preflight variants, 27 one-trial smoke executions, and 27 substantive variants / 270,000 Monte Carlo trials.

## Acceptance intent

1. Repository/native dependency/build/unit/core regressions remain clean.
2. The CP71 deterministic sweep proves TL1 same-hex burn-through cancels ECM 1 while range-one ECM 1 still degrades a Firm observation.
3. Unit tests prove intrinsic Discrimination Resistance can defeat weaker ECM without ECCM and stronger ECM can still defeat the +1 point-blank burn-through term.
4. The actual-consumer preflight and 27-trial smoke must pass before the substantive study.
5. Fixed point-blank jammed lanes must regain Firm/direct-fire opportunity; ordinary operational ECM must still be exercised.
6. No target win percentage is a blocking release gate.
7. Deep Calibration remains optional unless normal acceptance exposes an interacting regression.
