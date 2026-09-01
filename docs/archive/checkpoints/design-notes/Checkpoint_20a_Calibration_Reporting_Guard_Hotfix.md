# Checkpoint 20a - Calibration Reporting Guard Hotfix

## Purpose

Checkpoint 20a repairs a source-text guard in the Checkpoint 20 apply script.
The calibration runner's runtime output correctly reports the count of
statistically contradictory marginals, but the C# source constructs that phrase
across adjacent string literals. The original preflight searched for the full
contiguous phrase in the source file and therefore stopped before compilation.

## Correction

The hotfix changes the source-text guard to require the stable semantic fragment
`contradictory marginals`, which is present in the calibration reporter source.
The runtime acceptance check remains strict and still requires:

- 108 calibration variants passed;
- zero failed variants; and
- zero statistically contradictory adjacent-TL marginals.

## Scope

Checkpoint 20 mechanics are unchanged. The representative profiles, provisional
TL values, analytical model, random streams, scenario corpus, tests, calibration
matrix, output formats, and 216,000-trial acceptance study are identical to
Checkpoint 20.

## Validation

The Checkpoint 20a apply script reruns the complete Checkpoint 20 acceptance
sequence: build, 506 tests, seven deterministic scenarios, twelve runner
self-tests, worker-count reproducibility, and all 108 calibration variants.
