# Checkpoint 121 — Damage Resolution Scaling and CP120 Correction

## Status

**Native accepted on 2026-08-16.** CP121 supersedes the unaccepted CP120 candidate and is the accepted baseline for Checkpoint 122. CP122 is the active migration candidate; CP121 remains the authoritative native evidence for the x2 equivalence/resolution decision.

**Corrected replacement 1:** the original CP121 handoff failed `-RepositoryOnly` at CP120 correction-summary byte reproducibility because `Path.write_text()` translated LF to CRLF on Windows. The JSON content was semantically identical and no combat/study result was affected. Replacement 1 emits canonical UTF-8/LF bytes and moves an actual native-platform regenerate-and-byte-compare check into CP121 preflight, before inherited regression smokes.

## Scope

CP121 contains two causally related corrections/diagnostics:

1. correct CP120 Missile terminal telemetry summarization and reproducibly reanalyze the preserved native CP120 output without rerunning combat;
2. test a research-only x2 damage/defense point domain with a hard same-seed equivalence gate, then measure odd-point half-steps around the largest CP120 offensive cliffs and selected defense axes.

Production C#/Godot numerical values, player-facing technology authority, and Concept mechanics remain unchanged.

## Native acceptance sequence

`apply_checkpoint_121.ps1 -RepositoryOnly` must perform repository hygiene, CP121 preflight, the complete Python unit suite, 25 C#/Python parity fixtures, inherited CP114/115a/116/118/119/120 regression smokes, CP120-native telemetry reanalysis provenance checks, and a complete one-trial CP121 smoke including one paired equivalence trial per CP120 variant.

The normal command additionally executes:

- exact x2 equivalence: 4,284 CP120 variants × 20 paired trials = 85,680 paired trials = 171,360 combat executions;
- half-step study: 2,424 variants × 2,000 trials = **4,848,000 engagements**.

Only mechanical/repository/integration failures fail the checkpoint. Outcome magnitudes remain review evidence.

## Acceptance gates

- CP120 original native archive SHA-256 and raw `variants.csv` SHA-256 match the preserved provenance.
- Corrected CP120 summaries read Missile launches from the attacker and terminal guidance attempts/hits from the target.
- The standalone CP120 reanalysis helper must resolve the research package and expose its CLI without relying on a caller-provided `PYTHONPATH`; preflight checks this exact wrapper dependency.
- CP120 corrected Swarmer-accuracy comparisons expose nonzero terminal guidance-hit deltas; the +10 guidance controls must remain approximately +10 percentage points in the preserved native evidence.
- All 4,284 CP120 variants exist in the x2 equivalence population.
- No paired legacy/x2 trial may differ after damage-unit normalization.
- Hull is part of the x2 point domain.
- The half-step population contains 2,424 variants with the declared family and priority counts.
- Odd values exist on both offense and defense axes.
- No trial errors; all active build templates remain exact-fill.
- No production numerical table, Concept authority, or player-facing weapon authority is automatically modified.

## Critical-damage boundary

CP121's Python research consumer remains `layered_defense_hull_only`. Internal H/X criticals are not simulated. The scaling audit nevertheless makes the future requirement explicit: a canonical x2 scale must preserve legacy H/X cadence by advancing one old H/X position per two new-scale Hull points, with deterministic cross-packet remainder semantics, unless a later design checkpoint deliberately changes critical frequency.
