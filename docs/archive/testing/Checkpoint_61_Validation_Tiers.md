# Checkpoint 61 Validation Tiers

Checkpoint 61 preserves the Checkpoint 60 test-suite scrub. The default release gate remains deliberately small, but it now includes the checkpoint's own composed-ship Monte Carlo study because that study is the new implementation being accepted.

## Must always run

The normal definition has **8 runner stages**. Seven are the accepted deterministic/core stages from Checkpoint 60. The eighth is `tl1-composed-ship-odd-build-combat`, containing 54 variants at the requested trial count (540,000 trials at the 10,000 default).

This tier is the authoritative Checkpoint 61 acceptance run.

## Deep Calibration

`-DeepCalibration` adds the 12 retained historical stochastic studies. With the new 54-variant study included, the deep definition has **20 stages**, **1,080 Monte Carlo variants**, and **10.8 million trials** at the 10,000 default.

Deep Calibration is not required merely because it exists. Use it when a later checkpoint changes a dependency covered by those historical stochastic studies or when a specific result warrants broad requalification.

## Checkpoint 61 isolation boundary

The new composed-build execution path is explicit and does not change the historical legacy-side fixture. Historical studies still use their prior implicit integrated suite and one-PDS path. Explicit Checkpoint 61 builds use installed reactors, shields, sensors, main weapons, and PDS counts from the build document and use the zero-effect TL1 AUX control.

This isolation is why normal Checkpoint 61 acceptance plus core tests is sufficient for this pass. Deep Calibration remains available as a diagnostic, not a ritual release cost.
