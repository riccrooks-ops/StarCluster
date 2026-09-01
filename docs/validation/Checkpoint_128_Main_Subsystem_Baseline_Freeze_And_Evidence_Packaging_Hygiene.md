# Checkpoint 128 — Main-Subsystem Baseline Freeze and Evidence Packaging Hygiene

**Status:** Candidate pending native Windows acceptance  
**Accepted main-subsystem evidence baseline:** CP127 Corrected Replacement 1  
**Accepted production implementation baseline:** CP122 Corrected Replacement 1

## Purpose

CP128 is a deterministic consolidation checkpoint. It performs no new balance study and changes no gameplay value. Its goals are to:

1. freeze the accepted CP127 TL1-TL9 main-subsystem values into durable current authorities;
2. correct stale STL and Missile descriptive metadata left over from superseded uneven movement candidates;
3. preserve the accepted CP127 findings and predecessor lineage in compact, hash-verifiable form; and
4. prevent future full-repository archives from recursively embedding large raw predecessor native-results ZIPs.

## Numerical boundary

`technology_numerical_matrix_v0_5.json` must be operationally/numerically identical to accepted CP127 `technology_numerical_matrix_v0_4.json`. Permitted profile edits are explanatory `notes` plus the two descriptive Missile-delivery technology labels needed to distinguish held Range/Space architecture from advancing operational Move.

The stabilized rules remain:

- STL Move = Drive TL;
- Missile Move = Drive TL + 1;
- strategic FTL = 1/2/3/4/4/6/7/9/12;
- TL8 Energy = 7/10/12 damage, APEN3;
- strong TL5->TL6 maturation retained;
- no other main-subsystem numerical leaf changes;
- most AUX numerical stabilization deferred.

## Evidence-retention boundary

The large CP125 and CP126 native-results archives previously embedded by CP126/CP127 are externalized. CP128 retains their exact archive SHA-256/size, complete contents hash manifests, acceptance summaries, and decision-relevant aggregate outputs. The accepted CP127 native-results archive is likewise represented by its exact archive/content hashes and compact accepted outputs rather than embedded in full.

Historical checkpoint files remain frozen even when an old wrapper named one of the externalized archives. The evidence directory documents that historical rerun dependency explicitly.

The shared pre-package hygiene checker rejects validation-evidence ZIPs over 5 MiB individually or 16 MiB collectively. `docs/references/` source archives are exempt.

## Native acceptance

Run from a clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-128\apply_checkpoint_128.ps1 -RepositoryOnly
```

The checkpoint must pass:

- exact Python 3.13 acceptance runtime resolution and pinned .NET SDK 8.0.423;
- pre-package hygiene and validation-evidence ZIP budget;
- CP128 deterministic preflight;
- **171/171 Python tests**;
- warning-as-error native build;
- **907/907 xUnit tests**;
- **70/70 ScenarioRunner self-tests**;
- **25/25 accepted C#/Python research-parity fixtures**;
- exact frozen production/research simulation surfaces relative to accepted CP127;
- zero numerical/operational drift between current v0.5 and accepted v0.4;
- Tech Table/workbook/Concept synchronization;
- curated CP125/CP126/CP127 evidence hashes and acceptance provenance;
- exact repository manifest/evidence contract.

There is **no Monte Carlo plan, smoke, symmetry rerun, or substantive study** in CP128. Those accepted CP127 outputs are evidence inputs, not work to repeat for prose/packaging cleanup.
