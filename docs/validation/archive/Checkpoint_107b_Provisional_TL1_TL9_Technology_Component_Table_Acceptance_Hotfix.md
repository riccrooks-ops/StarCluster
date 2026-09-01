# Checkpoint 107b - Provisional TL1-TL9 Technology / Component Table Acceptance Hotfix

## Purpose
Checkpoint 107b repairs the two native-acceptance defects exposed by the unaccepted CP107 and CP107a candidates without changing the CP107 technology/component design content.

## Failure sequence and root causes
1. **CP107:** one-letter PowerShell helper functions (`H`, `R`, and similar) collided case-insensitively with built-in Windows PowerShell aliases. The first provenance hash call was therefore routed to `Get-History -Id` and failed parameter conversion.
2. **CP107a:** the alias-safe contract reached the strengthened shared native precheck, but `Test-NativeAcceptanceDependencies.ps1` accessed `$definition.stages` directly while running under `Set-StrictMode -Version 2.0`. The CP107a architecture definition omitted that optional property, causing `PropertyNotFoundStrict` before contract execution.

## CP107b repair
- Keep descriptive, non-alias helper names in the active checkpoint contract.
- Make optional checkpoint-definition and stage-property access strict-mode safe through `PSObject.Properties` lookup rather than direct property dereference.
- Normalize the CP107b architecture definition with an explicit `"stages": []` field.
- Retain AST-based rejection of alias-colliding function names.
- Add native regression fixtures that prove the guard accepts both missing and empty `stages`, while still rejecting an explicitly blocked Python stage.
- Preserve the failed CP107 and CP107a manifests under `docs/validation/evidence/` for exact provenance.

## Retained architecture outcomes
- All 10 visible research disciplines have explicit TL1-TL9 grid rows; family-level quiet TLs remain legal.
- All 214 CP106 Storyboard beats remain preserved and classified.
- Related research remains non-gating and the CP107 architecture promotes zero hard external prerequisites.
- Universal Installation Space remains authoritative for support/AUX installations.
- Starting shuttle = 1; tactical Fuel working scale = 100 / 2 per traversed hex / +1 EvM; TL1 Ablative Armor = 1 Space.
- Zero trials and zero new TL4-TL9 balance values.

## Runtime-dependency policy
The active user-facing Windows acceptance path remains PowerShell plus the pinned .NET SDK and carries no Python runtime dependency. Python may be used during checkpoint authoring/linting outside the shipped native acceptance path, but is not required to validate or use the checkpoint.

## Native validation
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-107b\apply_checkpoint_107b.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-107b\apply_checkpoint_107b.ps1
```

Both paths remain deterministic architecture-only validation. No Deep Calibration is applicable.
