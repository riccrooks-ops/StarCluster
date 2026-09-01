# Checkpoint 20b - Paired Calibration and Statistical Gate Repair

## Purpose

Checkpoint 20b repairs the comparative statistical gate revealed by the first
Checkpoint 20 calibration run. All 108 variants individually matched their
analytical probabilities, but one of 63 analytically flat comparisons was
flagged because independent Monte Carlo streams happened to fluctuate in
opposite directions. The old non-overlapping-Wilson-interval rule did not
account for the size of the comparison family and discarded the opportunity to
pair trials directly.

This checkpoint changes the experiment and reporting layer only. It does not
change `StarCluster.Core` combat mechanics, the representative component
profiles, the provisional TL values, or the analytical terminal model.

## Common random numbers

Every calibration variant now uses the same study-level random-seed namespace.
For a given trial index, all variants receive identical trial, interception,
and terminal stream seeds. Variant identity remains part of the run and output
identity, but no longer changes calibration random quantiles.

This common-random-numbers design makes adjacent variants paired experiments:

- flat variants with identical probability thresholds replay the same outcomes;
- monotonic threshold changes are measured against the same random draws; and
- paired deltas have substantially less sampling noise than independent
  proportion differences.

Per-variant manifests and execution records preserve the random-seed namespace.
The compact calibration result records it once for the whole study. Each
marginal also records a SHA-256 fingerprint of its paired trial streams and must
verify that both variants used the same streams.

## Paired marginal statistics

For each adjacent-TL comparison, the runner records the four paired effective-hit
cells:

- neither variant hits;
- only the lower/from variant hits;
- only the higher/to variant hits; and
- both variants hit.

The observed marginal is the mean paired difference. The report includes a 95%
paired-difference interval and a continuity-corrected McNemar normal
approximation p-value. Directional comparisons use the appropriate one-sided
alternative; analytically flat comparisons use a two-sided alternative.

All marginal p-values are adjusted together with the Holm step-down procedure,
controlling the familywise error rate across the full 216-comparison matrix.
The configured familywise alpha is 0.05.

## Practical effect threshold

Statistical detection alone is not a failure. A marginal is contradictory only
when both conditions hold:

1. its observed effect opposes the analytical direction by more than the
   configured practical threshold; and
2. its Holm-adjusted p-value is below the configured familywise alpha.

The Checkpoint 20 study uses a one-percentage-point minimum practical marginal
delta. The original per-variant maximum absolute-error gate remains unchanged
at four percentage points.

## Output schema

`calibration-summary.json` advances to result schema version 2. The marginal
JSON and CSV output now includes paired counts, paired confidence bounds, raw
and Holm-adjusted p-values, the practical threshold, familywise alpha, the
pairing fingerprint, and explicit common-random-numbers verification.

Trial journals remain optional and are discarded by the compact acceptance run.
The paired outcome vectors exist only in memory while the calibration summary is
constructed.

## Validation

Checkpoint 20b reruns:

- the unchanged 506 engine-independent tests;
- seven deterministic headless scenarios;
- sixteen runner self-tests, including common-random-numbers, paired-difference,
  Holm-adjustment, and practical-effect contracts;
- the Checkpoint 19 worker-count reproducibility gate; and
- all 108 calibration variants at 2,000 trials each with `--jobs 24`.

Acceptance requires all 216 marginals to verify shared random streams and zero
practical, Holm-significant contradictions. No Godot mechanical validation is
required.
