# Checkpoint 96 - Readiness Cohort Semantics Closure

## Purpose

Checkpoint 96 continues from **native-accepted Checkpoint 95** and closes the current narrow instrumentation sequence. It does not change gameplay, component values, legal-build enumeration, sampling, AI doctrine, or technology promotion.

CP95 native acceptance is embedded under `docs/validation/evidence/checkpoint-95/`:

- checkpoint definition SHA-256: `de57c2069e7e20cf1fb8e4ec6af26f32f9d18df3fae4e758cbc5c406e7e091d3`;
- repository manifest SHA-256: `3753fb2b41ff55027eef0bd37ba5ab2304f3022c67cd7fdda43da18041c3dcdf`;
- accepted full-repository ZIP SHA-256: `df057daf4d431b104447032d905628ba902b758b2b0efbd8c5e8d66c0a7f94d2`;
- native results ZIP SHA-256: `dcbe31976263bb70a8ba3c04a67a08452471d619989356f4ff6931de17b29026`;
- substantive summary SHA-256: `8292cac5ac145aae8e205028d9b7a4fc095abb5a0e26f289a53ae182706893d8`;
- SDK 8.0.423, 0 build warnings/errors, 863 tests, 13/13 stages, 59 self-tests, 1,440 smoke executions, 2,160,000 substantive trials, zero failed gates.

## Why CP96 exists

CP95 proved that its static ready range is a **reference-context screening estimate**, not an absolute runtime legality boundary. In the accepted dynamic screen:

- reference-context mutual readiness covers about 84.371549% of the legal-pair population;
- an actual post-Movement window satisfying both static reference-ready ranges is observed for about 56.576220%;
- the legacy CP95 `observed_active` cohort covers about 58.727128%; and
- true runtime bilateral activity covers about 60.648377%.

The difference is meaningful: four weighted statistical bundles, about 1.921249% of the legal population, are bilaterally active at runtime despite the static reference context saying mutual engagement is not expected. Fixed Range-3 also contains a smaller 1.230124% reference-not-expected/runtime-active population. These are legal runtime outcomes, not gate failures.

## CP96 semantics

CP96 reports three independent observables:

1. **Reference-context mutual readiness** - the precomputed Firm-track/physical-weapon readiness estimate under the declared reference context.
2. **Observed reference-ready firing window** - whether the simulation actually reached at least one post-Movement firing window satisfying both sides' static reference ready ranges.
3. **Runtime bilateral activity** - whether both ships actually produced family-appropriate legal main-weapon actions, independent of the static reference estimate.

The CP95 `observed_active` definition is retained only as the explicitly named compatibility cohort `legacy_cp95_reference_expected_runtime_active` so CP95/CP96 comparisons remain auditable.

CP96 also reports `reference_runtime_relation` values:

- `reference_expected_runtime_active`;
- `reference_expected_runtime_inactive`;
- `reference_not_expected_runtime_active`; and
- `reference_not_expected_runtime_inactive`.

## Causal replay

CP96 reuses the accepted CP95 `cross-tl-build-permutation-foundation-v0_6.json` unchanged. The legal envelope, 192 statistical base pairs, 24 zero-weight diversity pairs, 48 named logical pairings, three geometries, 1,440 generated variants, pair-selection seed `940177`, combat master seed `940100`, and 1,500-trial substantive workload remain unchanged. No RNG calls are added to combat resolution.

## Required CP96 outputs

- `cross-tl-cp96-paired-review.csv`;
- `cross-tl-cp96-population-weighted-review.csv`;
- `cross-tl-cp96-activity-review.csv`;
- `cross-tl-cp96-mover-neutral-review.csv`;
- `cross-tl-cp96-mover-neutral-summary.csv`; and
- `cross-tl-cp96-outlier-review.csv`.

The population-weighted and mover-neutral summaries must include `all_legal`, `reference_context_mutual_ready`, `observed_reference_ready_window`, `runtime_bilateral_active`, and `legacy_cp95_reference_expected_runtime_active` cohorts.

## Native workload

- 1,440 one-trial smoke executions;
- 1,440 variants x 1,500 substantive trials = 2,160,000 substantive trials;
- 2,161,440 total trial executions including smoke;
- 59 ScenarioRunner self-tests expected.

Deep Calibration is not applicable.

## Native acceptance commands

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-96\apply_checkpoint_96.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-96\apply_checkpoint_96.ps1
```

## Completion boundary

After CP96 acceptance and review, resume broader Star Cluster development: overall mechanics, mixed-TL progression, cross-subsystem interactions, and the technology tree. Do not continue creating narrow instrumentation checkpoints unless later substantive evidence identifies a genuine measurement blocker.
