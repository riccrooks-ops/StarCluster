# Checkpoint 62 Validation Tiers

Checkpoint 62 continues the scrubbed validation model: the normal acceptance suite contains only repository/build/unit/core-regression gates plus the stochastic study that is actually under review.

## Must always run

The normal suite has **8 stages**. It retains deterministic/core TL1 checks, the 35-Space construction envelope, resource semantics, runner self-tests, and replaces the now-accepted Checkpoint 61 broad composed-build matrix with the current **108-variant Tactical Power doctrine/reactor sensitivity study**.

At 10,000 trials per variant the normal stochastic workload is **1,080,000 trials**.

## Deep Calibration

Deep Calibration is optional. It adds the accepted Checkpoint 61 54-variant composed-build matrix plus the twelve older stochastic TL1 calibration stages, for **21 stages / 1,188 variants / 11,880,000 default trials**.

Checkpoint 62 does not require Deep Calibration because the new controls are opt-in per-variant fields and old studies default to the Checkpoint 61 DefenseFirst/production-reactor behavior. Run Deep Calibration only if normal evidence or a later mechanical change calls for broad stochastic requalification.

## Interpretation boundary

The 4/5/6 reactor values are a sensitivity axis. They do not modify the production profile, which remains 5 TP. Likewise, a weapon statistic that has little leverage against the present TL1 control is not automatically low-value: Energy APEN is specifically retained as latent capability because the current primary armor has AP 0.
