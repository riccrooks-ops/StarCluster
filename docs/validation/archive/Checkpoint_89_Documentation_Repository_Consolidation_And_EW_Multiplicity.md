# Checkpoint 89 - Documentation Repository Consolidation and EW Multiplicity

## Purpose

Checkpoint 89 restores a clear current-authority surface before the next generalized legal-build/permutation expansion. It is a documentation/repository architecture pass, not a balance calibration pass.

## Durable changes

1. **Documentation organization.** Active directories contain current authorities and current machine/runtime support only. Superseded studies, old workbooks, older validation policies, prior AI architecture versions, and historical checkpoint design notes are moved under `docs/archive/`. The redundant parallel `docs/checkpoints/` tree is removed.
2. **Component footprint discoverability.** The Technology Architecture Matrix gains a **Component Catalog** sheet and `component_installation_space_catalog_v1.json` as the compact current Installation Space/multiplicity reference.
3. **EW multiplicity rule.** Multiple ECM/ECCM suites may be installed for redundancy when Space permits, but same-type local ratings never add. Use the highest applicable functional rating. Allied Cooperative ECM remains a separate capped rule.
4. **Authority/navigation contracts.** `CHAT_README.md`, `docs/README.md`, design READMEs, and archive navigation make the current/history boundary explicit and contract-enforced.
5. **Accepted CP88 evidence.** The exact accepted CP88 repository manifest and compact native provenance are preserved under `docs/validation/evidence/checkpoint-88/`.

## Repository review summary

The CP88 documentation tree contained 679 files and mixed current authorities, historical checkpoint design notes, old workbook generations, superseded architecture revisions, runtime inputs, and evidence in overlapping locations. CP89 reviewed the documentation by role rather than by age alone.

After consolidation:

- the current/non-historical documentation surface is **57 files** (excluding historical archives and native evidence);
- `docs/design/player_technology/` contains **20** current authority/runtime-support files instead of the former study/workbook accumulation;
- `docs/design/testing/` contains **5** current files;
- `docs/design/ai/` retains **one** active AI Doctrine Architecture plus its current schemas/registries;
- the former parallel `docs/checkpoints/` tree is gone and its **73** unique historical design notes are under `docs/archive/checkpoints/design-notes/`;
- superseded technology material is classified under `docs/archive/player_technology/` as architecture history, studies, workbooks, checkpoint data, historical data, or reference-mining material;
- prior validation runbooks remain clearly historical under `docs/validation/archive/`;
- user-provided external references remain intact under `docs/references/`; and
- one exact duplicate historical checkpoint note (`Checkpoint_58c_PowerShell_Manifest_Format_Hotfix.md`) was removed from the old design-note tree rather than archived twice; the validation-archive copy is retained.

The active TL1 numerical baseline v0.2 remains in the current technology-support directory because the current 35-Space baseline JSON still references it. Historical-looking names are not sufficient reason to archive a file that remains an active machine/runtime dependency.

## Non-goals

- No combat implementation changes.
- No TL2 candidate retuning or promotion.
- No Monte Carlo balance study.
- No attempt to rewrite unrelated Concept material.
- No deletion of user-provided external references.

## Native acceptance

Run from a clean full-repository extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-89\apply_checkpoint_89.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-89\apply_checkpoint_89.ps1 -Jobs 24
```

The first pass validates dependency, repository, documentation, authority, provenance, and production-code-freeze contracts. The normal pass then performs the warning-as-error build, all tests, retained deterministic/mechanics stages, and 54 ScenarioRunner self-tests.

Deep Calibration is not required for this checkpoint.
