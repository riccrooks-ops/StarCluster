# Checkpoint 47 Validation: TL2 Opponent-Aware Range Control and Promotion Decision

## Command

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-47\apply_checkpoint_47.ps1 -Trials 10000 -Jobs 24
```

## Required release evidence

1. Exact SDK 8.0.423.
2. Clean warning-as-error build and complete test pass.
3. All 23 checkpoint stages pass.
4. Primary study resolves exactly 148 variants: 72 family-only controls, 72 opponent-aware lanes, and 4 fixed Range 5 controls.
5. Each profile resolves 74 variants.
6. Every dynamic policy covers three family pairs, both orientations, and starting ranges 1-6.
7. The opponent-aware policy records requested range and decision basis for every family pairing.
8. Fixed Range 5 Kinetic/Energy controls remain separate from pooled dynamic evidence.
9. Dynamic combat retains meaningful decisive coverage and disengagement remains disabled.
10. Weapon and TL2 component values remain byte-identical to Checkpoint 46.

## Review outputs

Review the complete `out/checkpoint-47/tl2-opponent-aware-range-control-and-promotion-decision` directory, especially:

- `opponent-aware-starting-range-review.csv`
- `pairwise-choice-summary.csv`
- `policy-comparison-summary.csv`
- `policy-decision-telemetry.csv`
- `kinetic-energy-decision.csv`
- `fixed-range5-energy-control.csv`
- `orientation-review.csv`
- `promotion-decision-overview.csv`
- `variants.csv`
- `gates.csv`
- `summary.json`

Exact parity is not required. Assess whether opponent-aware range control restores credible Energy/Kinetic tactical asymmetry without making another family irrelevant. Successful execution does not itself promote the TL2 package.
