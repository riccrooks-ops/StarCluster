# Checkpoint 27 - Revised TL1 Defensive Envelope and Kinetic Interaction Calibration

Checkpoint 27 replaces the provisional TL1 defense and ammunition assumptions that made the prior kinetic duel too defensive and too short-lived logistically. It preserves the accepted simultaneous-fire and accuracy contracts while adding the first broad stochastic interaction study.

## Implemented

- revised exact provisional baseline: SI 2, Shield Armor 0, recharge 1, AI 4, AP 0, Hull 12;
- kinetic DAM 3, SPEN 1, APEN 0, and 100 attack packages;
- missile magazine 24;
- parameterized kinetic duel simulator;
- deterministic common-random-number trial streams;
- 29 kinetic calibration variants and 10,000 default trials per variant;
- mirror side-bias and asymmetric side-swap gates;
- CSV and JSON summaries for outcome rates with Wilson 95% intervals, pace, every defensive layer, Hull-damage and Armor-depletion rates, and ammunition;
- eight focused deterministic calibration tests;
- Concept v0.3y decisions D-245 through D-249;
- technology workbook v0.7.

## Scope limits

Checkpoint 27 does not lock final TL1 balance. It does not add critical damage, component hits, personnel casualties, movement geometry, energy-family doctrines, missile salvos, PDS, surrender, or retreat. This Phase B calibration subpass is a kinetic interaction surface intended to expose thresholds and stalls before cross-family balance work.

## Checkpoint 27c Phase A fixture, compiler, and validator hotfix

Checkpoint 27a corrects an idempotence defect in `apply_checkpoint_27.ps1`. A repository-only preflight intentionally removes the stale active Checkpoint 26 validation runbook, but the original full-validation required-file list incorrectly required that removable fixture on the next invocation. The corrected validator requires the archived Checkpoint 26 copy and its normalization self-test expects Checkpoint 27 to remain active. No mechanics, baseline values, scenarios, tests, workbook content, or Concept decisions changed. Checkpoint 27c updates only the Phase A recharge fixture data by explicitly declaring pristine Shield Capacity 6 in its six mechanics cases, preventing the revised TL1 baseline Shield Capacity 2 from changing those legacy fixture expectations. Checkpoint 27b also adds the missing `StarCluster.Core.Combat.Damage` import required by `ArmorLayerState` in the calibration runner.
