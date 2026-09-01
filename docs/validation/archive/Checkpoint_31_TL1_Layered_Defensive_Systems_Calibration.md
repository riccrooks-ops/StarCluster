# Checkpoint 31 Validation

## Authoritative Windows command

Close Godot and run from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-31\apply_checkpoint_31.ps1
```

A repository-contract-only pass is available before the full execution:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-31\apply_checkpoint_31.ps1 `
  -RepositoryContractOnly
```

The second command must not alter tracked repository content. Running repository-contract-only validation followed by full validation must be idempotent.

## Expected acceptance totals

- 642 engine-independent tests.
- 7 legacy deterministic moving-missile scenarios.
- 12 Phase A documents / 54 cases / 127-value baseline.
- 7 Phase B documents / 36 cases under revised EvM.
- 29 kinetic calibration variants / 10,000 trials each / zero failed gates.
- 31 energy calibration variants / 10,000 trials each / zero failed gates.
- 48 complete no-counter weapon-matrix variants / 10,000 trials each / zero failed gates.
- 59 corrected PDS/interception variants / 10,000 trials each / zero failed gates.
- 171 layered defensive-system variants / 10,000 trials each / zero failed gates.
- 46 ScenarioRunner self-tests.

## Repository-contract gates

The preflight verifies:

1. the complete-repository SHA-256 manifest and rejection of unexpected repository-owned files;
2. native PowerShell parser success for every packaged script;
3. exactly one active validation runbook and one active Concept document after normalization;
4. the 127-row TL1 numerical baseline and SHA-256 `624c46e991022b187fb01804d6e094389fcce5996d2b91589277d0bde94c55f5`;
5. 25 main Missile Flights, 50 Kinetic PDS packages, 25 AMMs, and one Ready Package included in total capacity;
6. every retained Phase A/B and calibration document carrying the new baseline hash;
7. the corrected 59-variant PDS corpus and its reciprocal-pair controls;
8. the 171-variant defensive study, exact category counts, reciprocal pairs, schema validation, and representative boundary variants;
9. the Concept v0.4c markers, Decisions D-262 through D-269, and `END OF DRAFT v0.4c`;
10. workbook v0.11 sheets and markers, including `Checkpoint 30 PDS`, `Checkpoint 31 Defense`, D-269, and no structured table parts;
11. static test cardinality of 562 facts, 20 theories, 80 InlineData rows, and 642 discovered cases;
12. clean extraction, archive checksum, and unauthorized-file rejection.

## Full execution gates

The full Windows validator additionally performs:

- a clean restore and build with warnings as errors under .NET SDK 8.0.423;
- all engine-independent tests;
- every retained deterministic and Monte Carlo lane before the new study;
- the defensive study with a 24-worker ceiling;
- all ScenarioRunner self-tests.

No mechanical Godot validation is required because Checkpoint 31 changes the engine-independent simulation, data, tests, documentation, and calibration host without changing presentation or input behavior.

## Required review after execution

A green run proves mechanical fidelity, determinism, reciprocal fairness, and contract integrity. It does not by itself promote provisional PDS, EW, shield, ammunition, or reactor values to final balance. Review the generated `summary.json`, `variants.csv`, paired-gate report, power commitments, Firm-denial rates, PDS ammunition use, shield restoration, and unresolved cases before deciding the next balance pass.
