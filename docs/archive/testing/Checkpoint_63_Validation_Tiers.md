# Checkpoint 63 Validation Tiers

Checkpoint 63 keeps the scrubbed validation model established by Checkpoints 60-62. The normal acceptance suite contains repository/build/unit/core-regression checks plus only the stochastic study currently under review.

## Must always run

The normal suite has **8 stages**. It retains deterministic/core TL1 checks, the frozen 35-Space construction envelope, resource semantics, and runner self-tests, while replacing the now-accepted Checkpoint 62 doctrine/reactor matrix with the current **72-variant operational sensor/acquisition/EW study**.

At 10,000 trials per variant the normal stochastic workload is **720,000 trials**.

## Deep Calibration

Deep Calibration is optional. It adds the accepted Checkpoint 62 108-variant doctrine/reactor study, the accepted Checkpoint 61 54-variant composed-build study, and the twelve older stochastic TL1 calibration stages, for **22 stages / 1,260 Monte Carlo variants / 12,600,000 default trials**.

Deep Calibration is not required for Checkpoint 63 acceptance because the new operational-track fields default to `EstablishedFirm`; historical studies therefore preserve their accepted behavior. Run Deep Calibration only if the normal result exposes a broader regression or a later mechanical change requires full stochastic requalification.

## Interpretation boundary

Production reactor output remains 5 TP and the current study uses FullVolleyFirst to isolate sensing from known allocation pathologies. Side B remains established-Firm so only Side A acquisition changes. The EW1 regime is a range-pressure sensitivity input rather than an ECM/ECCM component valuation.

No target win rate is blocking. Contextual capabilities remain valid design value when the present matchup does not exercise them; Energy APEN remains the standing example.
