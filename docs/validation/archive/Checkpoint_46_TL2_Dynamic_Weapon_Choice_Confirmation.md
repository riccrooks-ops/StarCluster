# Checkpoint 46 Validation: TL2 Dynamic Weapon-Choice Confirmation

## Command

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-46\apply_checkpoint_46.ps1 -Trials 10000 -Jobs 24
```

## Required release evidence

1. Exact SDK 8.0.423.
2. Clean warning-as-error build and complete test pass.
3. All 22 checkpoint stages pass.
4. Primary study resolves exactly 108 variants: 36 fixed controls and 72 Preferred Range lanes.
5. Each profile resolves 54 variants.
6. Starting ranges 1-6 and both orientations are present for every family pair.
7. Dynamic lanes exercise Preferred Range policy and observe movement.
8. Fixed controls retain at least 80 percent decisive coverage.
9. Disengagement remains disabled throughout the study.
10. Family identity and minimal-tactics contracts pass.

## Review outputs

Review the complete `out/checkpoint-46/tl2-dynamic-weapon-choice-confirmation` directory, especially:

- `starting-range-choice-review.csv`
- `pairwise-choice-summary.csv`
- `family-role-expression.csv`
- `orientation-review.csv`
- `fixed-mutual-control.csv`
- `profile-choice-overview.csv`
- `variants.csv`
- `gates.csv`
- `summary.json`

Dominance and irrelevance classifications are diagnostic. Exact family parity is not a release gate and no candidate is promoted by successful execution alone.
