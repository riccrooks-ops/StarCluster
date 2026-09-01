# Checkpoint 32 Validation

## Authoritative Windows command

Close Godot and run from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-32\apply_checkpoint_32.ps1
```

Repository-contract-only validation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-32\apply_checkpoint_32.ps1 `
  -RepositoryContractOnly
```

Both paths must be idempotent and must not modify manifest-controlled repository content.

## Expected acceptance totals

- 668 engine-independent tests.
- 7 legacy deterministic moving-missile scenarios.
- 12 Phase A documents / 54 cases / 127-value baseline.
- 7 Phase B documents / 36 cases.
- 29 kinetic variants / 10,000 trials each / zero failed gates.
- 31 energy variants / 10,000 trials each / zero failed gates.
- 48 no-counter weapon-matrix variants / 10,000 trials each / zero failed gates.
- 59 corrected PDS variants / 10,000 trials each / zero failed gates.
- 171 layered defensive-system variants / 10,000 trials each / zero failed gates.
- 504 Tactical Power/reactor-envelope variants / 10,000 trials each / zero failed gates.
- 46 ScenarioRunner self-tests.

## Repository-contract gates

The preflight verifies:

1. the complete repository SHA-256 manifest and rejection of unexpected repository-owned files;
2. native PowerShell parser success for every packaged script;
3. exactly one active validation runbook and one active Concept document;
4. the 127-row TL1 baseline and its current SHA-256;
5. every retained Phase A/B and calibration document carrying the same baseline hash;
6. FTL transition refilling an installed Capacitor Bank to full capacity while not restoring ammunition, Combat Batteries, shields, fuel, repairs, or Strain;
7. Combat Battery, Capacitor Bank, Auxiliary Reactor, energy-overload, and held-ammunition source contracts;
8. the 504-variant study, exact category counts, reactor outputs 0-8, exact reciprocal pairs, required representative variants, and schema validation;
9. 26 focused Checkpoint 32 facts in addition to all retained test-source contracts;
10. Concept v0.4d, Decisions D-270 through D-278, and `END OF DRAFT v0.4d`;
11. workbook v0.12 with the retained Checkpoint 29-31 sheets and new `Checkpoint 32 Power` sheet;
12. clean extraction, archive checksum, and unauthorized-file rejection.

## Full execution gates

The full validator additionally performs:

- clean restore/build with warnings as errors under .NET SDK 8.0.423;
- all engine-independent tests;
- all retained deterministic and calibration lanes;
- the 504-variant power-envelope study with a 24-worker ceiling;
- all ScenarioRunner self-tests.

No mechanical Godot validation is required because Checkpoint 32 changes only engine-independent mechanics, data, tests, documentation, and calibration tools.

## Review after execution

A green run closes the mechanical implementation, not the reactor balance decision. Review the affordability thresholds, full-package rates, unused power, source substitution, energy firing rates, finite-store depletion, held-fire opportunity costs, and overload Strain before selecting a provisional normal Reactor output.
