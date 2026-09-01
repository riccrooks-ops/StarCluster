# Checkpoint 110 - Power / Reactor First-Pass Calibration

## Purpose

Checkpoint 110 is the first substantive numerical calibration pass against the complete native-accepted CP109 TL1-TL9 candidate matrix. It calibrates **Primary Main Reactor Generation** in contextual legal ship designs while leaving Energy Storage and auxiliary generation for separate later studies.

The study is diagnostic and evidence-driven. It does not use target win rates, does not require one Reactor to power every installed system simultaneously, and cannot automatically promote a value into the production C#/Godot runtime.

## Candidate decision under test

Retain the CP109 Reactor ladder unless the evidence exposes a concrete pathology:

- TL1 5/3/1 at 6 Space
- TL2 7/3/0 at 6 Space
- TL3 7/4/1 at 5 Space
- TL4 9/5/1 at 5 Space
- TL5 12/4/0 at 5 Space
- TL6 12/7/1 at 4 Space
- TL7 15/8/1 at 4 Space
- TL8 17/6/0 at 4 Space
- TL9 20/12/2 at 3 Space

## Native acceptance

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-110\apply_checkpoint_110.ps1 -RepositoryOnly
```

Expected: deterministic CP109 provenance, frozen C#/test surface, CP110 study/evidence, Concept/document, production-boundary, and manifest validation. No stochastic workload is rerun.

Then:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-110\apply_checkpoint_110.ps1
```

Expected additional stages:

1. Python research self-tests pass.
2. 25 deterministic parity cases pass.
3. The full Power/Reactor study completes with zero trial errors and zero failed gates.
4. The result contains 18,006 exhaustive legal standard builds, 72 representatives, 288 stochastic variants, at least the configured 20,000 samples per variant, and the expected Reactor/branch/stacking evidence surfaces.
5. No production promotion occurs.

## Local reference evidence

The checked-in CP110 evidence was generated with CPython 3.13 and the repository-owned deterministic RNG. It contains:

- 7,025,000 actual adaptive turn-demand samples.
- 14,400,000 equivalent safe-overload encounter turns represented by a closed-form bounded-use calculation over the sampled demand probabilities.
- 11 Reactor candidates including two Fission revival alternatives.
- 9 TL-specific exhaustive legal-build populations.
- 9 branch-heavy maximum-demand records.
- 9 current-Reactor two-installation Space tests.
- 88 legacy-Reactor stacking comparisons.

## Acceptance interpretation

A successful CP110 run means the **first-pass calibration evidence is reproducible** and supports retaining the current Reactor candidates as working candidates. It does not make them immutable and does not alter production values. Revalidation is required after material changes to Reactor stats, Hull/Space budgets, major Tactical Power consumers, numerical AUX/mission systems, Energy Storage, auxiliary generation, or Reactor overload/Strain behavior.
