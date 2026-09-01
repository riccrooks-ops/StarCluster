# Checkpoint 64 Validation Tiers

Checkpoint 64 keeps the scrubbed validation model established by Checkpoints 60-63b. The normal acceptance suite contains repository/build/unit/core-regression checks plus only the stochastic study currently under review.

## Must always run

The normal suite has **8 stages**. It retains deterministic/core TL1 checks, the frozen 35-Space construction envelope, resource semantics, and runner self-tests, while replacing the accepted Checkpoint 63b study with the current **90-variant track-aware movement/acquisition study**.

At 10,000 trials per variant the normal stochastic workload is **900,000 trials**.

## Deep Calibration

Deep Calibration is optional. It adds the accepted Checkpoint 63b 72-variant sensor study, Checkpoint 62 108-variant doctrine/reactor study, Checkpoint 61 54-variant composed-build study, and the twelve older stochastic TL1 calibration stages, for **23 stages / 1,350 Monte Carlo variants / 13,500,000 default trials**.

Deep Calibration is not required for Checkpoint 64 acceptance because `TrackAwareOpponentRange` and `AcquisitionFirstAutoActive` are opt-in. Historical variants retain their prior movement and sensor-power behavior.

## Interpretation boundary

Production reactor output remains **5 TP** and FullVolleyFirst remains the power doctrine. Checkpoint 64 asks whether movement and acquisition behave coherently, not whether a target balance percentage is reached.

A track-aware sensorless ship may still remain outside Firm if an equal-or-faster opponent successfully preserves standoff. That is valid operational disadvantage and must not be converted into a release failure. Likewise, a contextual capability such as Energy APEN remains legitimate design value even when the current opponent does not exercise it.
