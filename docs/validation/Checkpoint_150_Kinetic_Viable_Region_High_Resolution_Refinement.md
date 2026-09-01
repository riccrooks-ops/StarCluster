# Checkpoint 150 - Kinetic Viable-Region High-Resolution Refinement

## Status

Candidate pending native Windows validation. Base checkpoint: native-accepted CP149 CR1.

## Purpose

CP149 executed 42,380,000 Kinetic multivariate combats and established a broad response surface. Its accepted evidence shows:

- Kinetic damage is the dominant combat lever;
- accuracy is the strongest secondary lever where K accuracy remains below Energy;
- standard/extended range matters at specific TL breakpoints and interacts positively with damage;
- APEN is usually weak but retains measurable role leverage at selected TLs;
- firing TP changes are nearly non-binding because K is already highly funded;
- ammunition above the accepted 100-round magazine is non-binding in viable fights;
- Space is strategically relevant to construction but the fixed Stage-A templates cannot convert freed Space into invented combat capability;
- the coarse CP149 +2 DAM / +10 ACC points bracket the useful region but often overshoot at early TLs, while TL4 and TL8 remain weak at +2 DAM.

CP150 therefore resolves the viable Kinetic region rather than repeating the full seven-factor cube.

## Authority boundary

CP150 changes no production C#, Godot mechanics, combat doctrine, Concept, Technology Numerical Matrix, non-K value, Reactor value, defense/AUX value, or Stage-A scenario identity.

The executable combat doctrine remains `cp147_tactical_utility` / canonical kernel v0.7.

Kinetic SPEN remains exactly 0. Kinetic firing TP remains the accepted resource-environment value. Kinetic ammunition is fixed at 100. Kinetic Space remains unchanged. No source numerical table is written.

## Accepted CP149 evidence retained

CP150 retains only the specific accepted CP149 native tables needed to justify and audit the refinement design, not the predecessor native-results ZIP:

- CP149 native acceptance summary;
- Kinetic axial effects;
- pairwise interactions;
- candidate TL response;
- opponent response;
- Armor-role response;
- combat Pareto table;
- candidate ledger.

Every retained evidence file is SHA-256 locked by the CP150 research module. The submitted CP149 native-results archive is referenced by SHA-256 `18b60851e5138b8cb44f76b5f0e2bad533dbf8935d88c70a64565bcd1c46f565`.

## TL-specific high-resolution design

All declared levels are fully crossed within each TL. Accuracy and range may equal but never exceed contemporary Energy values. Equality is retained as an explicit identity-boundary diagnostic.

| TL | Candidates | Refined dimensions |
|---:|---:|---|
| 1 | 18 | DAM 0/+1/+2; ACC 0/+2/+5; base or +1 extended band |
| 2 | 81 | DAM 0/+1/+2; ACC 0/+5/+10; APEN 0/+1/+2; base / +1 standard / +1 extended range |
| 3 | 27 | DAM 0/+1/+2; ACC 0/+5/+10; base / +1 standard / +1 extended range |
| 4 | 72 | DAM 0/+1/+2/+3; ACC 0/+2/+5; six identity-preserving standard/extended range profiles up to Energy ceilings |
| 5 | 81 | DAM 0/+1/+2; ACC 0/+2/+5; APEN 0/+1/+2; base / +1 standard / +1 extended range |
| 6 | 4 | DAM 0/+1/+2/+3 only; CP149 found the other dimensions flat or identity-limited |
| 7 | 9 | DAM 0/+1/+2 x APEN 0/+1/+2 |
| 8 | 45 | DAM 0/+1/+2/+3/+4 x APEN 0/+1/+2 x base / +1 standard / +1 extended range |
| 9 | 12 | DAM 0/+1/+2/+3 x APEN 0/+1/+2 |

Total: **349 TL-candidates**.

## Combat population and statistical design

CP150 reuses the exact accepted K-vs-non-K Stage-A contexts:

- TL1: 200 contexts;
- TL2-TL9: 300 contexts per TL;
- total accepted Kinetic contexts: **2,600**;
- both side assignments preserved;
- five resource environments preserved;
- ten combat/counter strata preserved;
- Energy, GP Missile and Swarmer opponents retained wherever available.

This yields **102,900 candidate-context cells**.

The substantive study executes **200 common-random-number trials per cell**, for:

**102,900 x 200 = 20,580,000 combats.**

Common scenario identities, master seed, and trial indices are preserved across candidates.

RepositoryOnly executes every CP150 candidate against the inherited representative CP149 smoke panel, totaling **10,290 smoke combats** before the substantive run is allowed.

The substantive run is resumable in **32 TL/candidate batches** of at most 12 candidates each.

## Analysis products

The merged native study produces:

- candidate-context response surface;
- candidate TL response;
- opponent response;
- stratum response;
- resource response;
- dedicated K-vs-E Armor-role response;
- identity-preserving combat Pareto surface;
- parameter marginal response;
- pairwise refinement-grid response;
- final candidate ledger and TL design summary.

The Pareto surface evaluates overall K win rate, worst-opponent win rate, Armor-role win rate, and damage advantage. It does not automatically select or promote a candidate.

## Interpretation boundary

CP150 is intended to identify a bounded, identity-preserving Kinetic viable region and to show whether a coherent TL1-TL9 ladder can be selected from that region.

It is not an automatic optimizer and it cannot promote numerical values. A later checkpoint must select a bounded ladder candidate from the native evidence and confirm that ladder against the complete whole-combat response surface before any numerical authority changes.

## Native handoff

Use a fresh extraction and run in the same unchanged tree:

```powershell
.\tools\checkpoints\checkpoint-150\apply_checkpoint_150.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-150\apply_checkpoint_150.ps1
```

The second invocation resumes valid completed substantive batches if interrupted and packages `StarCluster_CP150_native_results_<timestamp>.zip` after all 20,580,000 combats and merged response surfaces pass the contract.
