# Checkpoint 44 - TL2 Package Attribution and Identity-Preserving Refinement

## Objective

Attribute the Checkpoint 43 integrated TL2 overmatch before promoting or broadly weakening any package. Checkpoint 44 retains all accepted stages, adds seven bidirectional improvement-group probes, verifies an exact TL1 null-vector control, tests three moderated identity-preserving refinement probes, and adds movement-aware evidence without changing combat mechanics.

## Authoritative command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-44\apply_checkpoint_44.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Run from a clean full-repository extraction. Preserve the complete `out/checkpoint-44` directory.

## Repository-only command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-44\apply_checkpoint_44.ps1 `
  -RepositoryOnly
```

## Required closure

- Clean complete-repository manifest and PowerShell parsing.
- Clean warning-as-error .NET build.
- All compiled tests pass with no skips or failures.
- All 20 configured stages pass.
- The retained 1,350 Monte Carlo variants and 46 ScenarioRunner self-tests remain unchanged.
- The new attribution stage contains exactly 1,764 variants and 19 TL2 diagnostic profiles.
- The checkpoint therefore resolves exactly 3,114 Monte Carlo variants at the requested trial count.
- The profile catalog validates against schema v0.1 and contains exactly seven attribution groups, seven additive probes, seven leave-one-out probes, one null control, one identity source, and three refinement probes.
- The null control exactly matches the TL1 combat vector and produces a fixed-range conditional win share between 49 and 51 percent.
- Every profile has 72 paired fixed-range cross-TL variants.
- The seven movement-aware profiles each have 36 paired Scripted Pursuit and Preferred Range variants.
- The identity source and three refinement probes each have 36 same-TL fixed-range variants.
- All attribution lanes retain the minimal-tactics contract and change no accepted combat mechanic.
- Aggressive Balanced Control and Specialization-Forward Control remain present in the retained Checkpoint 42/43 stage.
- No TL2 diagnostic or refinement profile is promoted automatically.

## Expected new output

`out/checkpoint-44/tl2-package-attribution-and-refinement` should contain:

- `summary.json`
- `variants.csv`
- `technology-profiles.csv`
- `attribution-review.csv`
- `group-effects.csv`
- `refinement-review.csv`
- `range-and-policy-breakdown.csv`
- `gates.csv`
- `result.sha256.txt`

## Interpretation

A green checkpoint means the attribution experiment executed correctly; it does not mean that the numerically closest refinement is production-ready. The preferred next candidate must show convergent fixed-range and movement-aware behavior, acceptable pacing and resolution, preserved same-TL identity, and enough remaining design space for TL3. Range 5 reach asymmetry must remain separately visible rather than being mistaken for a general balance result.

## Integrated-study schema capacity

Schema v0.4 preserves the accepted integrated tactical-combat variant contract while raising the documented study-size ceiling from 400 to 2,500 variants. This is a packaging/schema-capacity change only; it does not alter simulation mechanics.
