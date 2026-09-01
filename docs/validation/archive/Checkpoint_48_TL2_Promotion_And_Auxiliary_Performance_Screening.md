# Checkpoint 48 Validation: TL2 Promotion and Auxiliary Performance Screening

## Command

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-48\apply_checkpoint_48.ps1 -Trials 10000 -Jobs 24
```

## Required release evidence

1. Exact SDK 8.0.423.
2. Clean warning-as-error build and complete test pass.
3. All 24 checkpoint stages pass.
4. The accepted `tl2-production` profile resolves to Armor Step plus Conservative Direct Fire.
5. The primary AUX study resolves exactly 1,455 variants.
6. The legal matrix resolves exactly 1,323 variants: 147 TL1v1, 588 TL2v2, and 588 TL1v2.
7. Counterfactual no-AUX diagnostics resolve exactly 132 variants and remain excluded from legal balance aggregates.
8. The legal catalog contains 7 TL1 and 14 TL2 combat-evaluable AUX profiles.
9. Every legal matrix ship has exactly one non-counterfactual AUX profile.
10. Kinetic, Energy, and Missile same-family contexts are all complete.
11. Same-AUX mirrors, both cross-TL orientations, decisive coverage, and outcome accounting pass.
12. Retained studies preserve their legacy integrated AUX behavior.
13. Successful execution does not automatically promote an AUX family or screening value.

## Primary review outputs

Review `out/checkpoint-48/auxiliary-single-slot-performance-screening`, especially:

- `auxiliary-profiles.csv`
- `matrix-coverage.csv`
- `pairwise-auxiliary-summary.csv`
- `auxiliary-choice-overview.csv`
- `same-aux-mirror-review.csv`
- `no-aux-mirror-review.csv`
- `cross-tl-auxiliary-effect-space.csv`
- `no-aux-diagnostics.csv`
- `auxiliary-entry-floor-review.csv`
- `variants.csv`
- `gates.csv`
- `summary.json`

No-AUX rows are counterfactual diagnostics only. Standard conclusions must come from legal one-AUX comparisons. Exact parity is not required; assess role expression, alternatives, counters, dominance, irrelevance, and whether a candidate starting TL is appropriate.
