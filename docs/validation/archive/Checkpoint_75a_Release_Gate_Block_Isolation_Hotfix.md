# Checkpoint 75a - Release-Gate Block Isolation Hotfix

## Intent

Checkpoint 75a is a contract-test-only hotfix for Checkpoint 75. The first native `-RepositoryOnly` acceptance attempt stopped before the checkpoint harness and before any build, unit test, smoke, or Monte Carlo stage. The failing assertion reported that the CP75 release-gate block did not contain exactly one `tl1-c75-variant-coverage` gate.

The ScenarioRunner source does contain exactly one instance of each of the six CP75 study-specific release gates inside `BuildGates`. The failure was caused by the PowerShell contract audit itself: it searched the full C# source for the first text occurrence of `if (study.Id == Tl1AppliedDegradedFireFamilyCandidateStudyId)`. That text is also contained inside an earlier `else if (study.Id == Tl1AppliedDegradedFireFamilyCandidateStudyId)` branch used outside `BuildGates`. The contract therefore sliced the wrong C# region and then looked for release-gate names in a non-gate block.

CP75a anchors the search at the `BuildGates` method before locating the CP75 study branch. It then verifies each required CP75 gate by ordinal first/last occurrence within that isolated block. No gameplay code, study input, ScenarioRunner behavior, missile terminal behavior, direct-fire behavior, Concept content, AI doctrine, or production data changes.

## Hotfix scope

The substantive change is limited to the Checkpoint 75a native contract/audit path:

- add `tools/checkpoints/checkpoint-75a/apply_checkpoint_75a.ps1`;
- add `tools/checkpoints/checkpoint-75a/test_checkpoint_75a_contract.ps1`;
- add Checkpoint 75a normal and Deep Calibration definitions;
- anchor the CP75 release-gate block audit inside `BuildGates`;
- require each of the six CP75 gate identifiers to occur exactly once in that block;
- freeze the accepted CP75 ScenarioRunner, missile mechanics/tests, applied-study input, schema, policy, doctrine registry, missile architecture note, and Concept v0.6n by SHA-256;
- archive the original CP75 validation runbook and expose this CP75a runbook as the single active checkpoint validation document;
- regenerate the full-repository Checkpoint 75a manifest.

The six audited CP75 release gates remain:

1. `tl1-c75-variant-coverage`;
2. `tl1-c75-firm-reference-clean`;
3. `tl1-c75-firm-only-approx-blocked`;
4. `tl1-c75-family-package-wiring`;
5. `tl1-c75-no-missile-degraded-fire`;
6. `tl1-c75-outcomes-review-only`.

## CP75 mechanics and evidence remain unchanged

Checkpoint 75a does not modify the 40-variant applied degraded-fire study. It remains four Kinetic/Energy range/orientation contexts with ten profiles per context, evaluating -20 and -25 percentage-point Approximate-track direct-fire penalties. Production direct-fire weapons remain Firm-only and study outcomes remain human-review evidence rather than automatic promotion gates.

Missiles and torpedoes remain outside degraded direct fire. Baseline command-guided terminal attack still requires a live Current/Firm launcher datalink; peer terminal guidance remains explicitly capability-gated; sensor-plus-seeker refinement of Approximate information still requires a missile-local navigation track; seeker-only co-located acquisition remains distinct; and co-location alone is not an impact.

Concept `Star_Cluster_Game_Concept_v0.6n.docx` is byte-for-byte frozen from CP75.

## Native acceptance

Extract this complete repository over the repository root, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-75a\apply_checkpoint_75a.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-75a\apply_checkpoint_75a.ps1 -Jobs 24
```

Expected normal workload after repository validation:

- warning-as-error build using pinned .NET SDK 8.0.423;
- approximately 856 unit tests if no unrelated test-count changes occurred;
- 11 runner stages;
- 47 ScenarioRunner self-tests;
- 40-variant actual-consumer applied degraded-fire preflight;
- 40 one-trial full-pipeline smoke executions;
- 40 substantive variants / 400,000 substantive trials;
- zero failed release gates and zero trial errors.

The failed CP75 `-RepositoryOnly` attempt did not reach the build or simulation workload, so no CP75 study results need to be discarded or reconciled.

## Deep Calibration

Do not run by default. CP75a changes only the native contract audit used to locate the already-existing CP75 release-gate block. It does not change a declared Monte Carlo dependency or introduce a competing doctrine/mechanics candidate.
