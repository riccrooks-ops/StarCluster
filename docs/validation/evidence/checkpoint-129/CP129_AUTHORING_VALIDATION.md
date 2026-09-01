# CP129 Corrected Replacement 1 Authoring Validation

Authoring validation was performed against the CP128-based candidate before packaging.

Passed locally:

- CP129 stdlib-only preflight;
- frozen CP128 production/numerical/current-authority surface verification (620 files);
- deterministic plan reconstruction: 14,112 raw / 9,427 legal builds, 70,034 whole-ladder pairings, 626,028 total variants, 45,665,000 substantive engagements;
- six new CP129 permanent Python tests, including actual-consumer micro-smoke and transition-local holdback checks;
- full radius-5 physical symmetry: 2,250 comparisons / 4,500 combat executions / 0 mismatches;
- packaging-hygiene validation.

The authoring environment did not complete the full 626,028-variant one-trial smoke within its execution ceiling. No reduced smoke is substituted for that gate. The complete all-variant smoke remains mandatory during native Windows `-RepositoryOnly` acceptance before the substantive study can run. The 171 pre-CP129 Python tests remain byte-frozen from native-accepted CP128; the six new CP129 tests bring the native expected total to 177.

## Corrected Replacement 1

Original-candidate native failure reproduced from the Windows log: RepositoryOnly stage 9 reached the all-variant smoke and then failed in the smoke-summary CSV writer because later holdback rows contained `changed_fields` while the first baseline row did not declare that field. The corrected writer path uses a uniform row shape and an explicit `lane,variants,trial_errors,elapsed_seconds,changed_fields` schema. A permanent unit regression constructs baseline and holdback rows and writes/reads the mixed summary, reproducing the exact serialization boundary without running the full 626,028 variants.

The wrapper additionally exposes validated `-Jobs` range 1-61 with default 24; all four CP129 research invocations consume the parameter rather than a hard-coded worker count.
