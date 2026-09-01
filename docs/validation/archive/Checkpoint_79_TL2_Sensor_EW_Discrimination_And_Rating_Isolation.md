# Checkpoint 79 - TL2 Sensor/EW Discrimination and Rating Isolation

## Purpose

Checkpoint 79 is the first substantive validation pass derived from Technology Architecture Matrix v1. It isolates the TL2 Sensor Discrimination Resistance 1 and normal ECM/ECCM rating-2 candidates while keeping the accepted TL1 combat foundation, Tactical Computer values, sensor reach, overload rules, and missile architecture fixed.

No TL2 production value is promoted by this checkpoint. The operational study is diagnostic and outcome gates do not encode target win percentages.

## Architecture changes required only to execute the study

- Integrated tactical-combat variants may select Sensor/EW profiles independently for Side A and Side B. Existing shared-profile studies retain their legacy behavior.
- Integrated tactical-combat variants may request a normal ECM/ECCM rating independently per side. The default remains rating 1.
- Normal EW power scales with normal rating at the existing power-per-rating cost; CP79 uses 1 TP/rating.
- The reactive pre-combat EW resolver receives each side's actual Sensor/EW profile.
- New schema v0.19 records those optional diagnostic fields.

These are generalized actual-consumer capabilities, not TL2 production assignments.

## CP79 study contract

- Study: `tl2-itc06-sensor-ew-discrimination-isolation`.
- Sensor catalog: `tl2-sew01-sensor-discrimination-isolation`.
- 54 variants = 6 contexts x 9 packages.
- 10,000 substantive trials per variant by default = 540,000 substantive trials.
- 54 one-trial full-pipeline smoke executions precede the substantive stage.
- Kinetic-vs-Missile and Energy-vs-Missile are tested at fixed range 3 and in four dynamic movement-order contexts.
- Side A varies between TL1 DR 0 and TL2 candidate DR 1; Side B always retains the TL1 Balanced-0 sensor control.
- ECM/ECCM rating 2 consumes 2 TP at the candidate 1 TP/rating cost.
- No STL, Sensor, ECM, or ECCM overload is requested.
- The legacy TL2 Tactical Computer +12 targeting candidate is excluded.
- Direct-fire degraded fire appears only in the explicit Side-A -25 diagnostic fallback package.
- Missile degraded fire remains unimplemented.

## Native validation

First run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-79\apply_checkpoint_79.ps1 -RepositoryOnly
```

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-79\apply_checkpoint_79.ps1 -Jobs 24
```

Expected normal workload:

- pinned .NET SDK 8.0.423;
- warning-as-error build with zero warnings/errors;
- approximately 863 unit tests if no unrelated test-count changes occurred;
- 11/11 runner stages;
- 47 ScenarioRunner self-tests;
- 54 preflight variants;
- 54 one-trial full-pipeline smoke executions;
- 54 substantive variants / 540,000 substantive trials at the default trial count;
- zero failed release gates and zero trial errors.

## Deep Calibration

Do not run Deep Calibration by default. CP79's normal suite contains the actual consumer, full-pipeline smoke, and substantive study needed to assess this isolated TL2 hypothesis. Deep Calibration remains available only if native acceptance exposes a regression that needs broad historical comparison.

## Review questions after acceptance

Review the resulting `tl2-sensor-ew-discrimination-isolation-review.csv` before promoting anything. In particular assess whether Sensor DR 1 provides meaningful tall-research value, whether ECCM 2 provides a viable wide-research alternative at its TP cost, whether contemporary ECM 2 remains effective, whether PDS/offense opportunity costs remain meaningful, and whether -25 degraded fire remains a significantly inferior fallback to a restored Firm solution.
