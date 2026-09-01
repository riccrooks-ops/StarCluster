# Checkpoint 107a - Provisional TL1-TL9 Technology / Component Table Acceptance Hotfix

> Historical unaccepted hotfix. CP107a repaired the CP107 alias collision, but native acceptance then failed in the shared strict-mode dependency precheck because the architecture definition omitted the optional `stages` property. Use Checkpoint 107b.

## Purpose
Checkpoint 107a repairs the native-acceptance defect in the unaccepted CP107 candidate without changing its technology/component design content.

## Root cause
The CP107 contract defined one-letter PowerShell helper functions including `H` and `R`. Windows PowerShell resolves command names case-insensitively and has built-in aliases `h` -> `Get-History` and `r` -> `Invoke-History`. The first CP107 provenance hash call therefore bound the SHA-sums path to `Get-History -Id`, producing the reported `System.Int64` conversion failure.

## Hotfix
- Replace one-letter helpers with descriptive, non-alias function names in the CP107a contract.
- Extend `Test-NativeAcceptanceDependencies.ps1` to AST-scan function definitions and reject any name that collides with an active PowerShell alias.
- Preserve the CP107 Concept v0.7g, technology table JSON/workbook, support catalog, foundation ledger, idea register, Storyboard translation, and numerical boundaries unchanged.

## Retained architecture outcomes
- All 10 visible research disciplines have explicit TL1-TL9 grid rows; family-level quiet TLs remain legal.
- All 214 CP106 Storyboard beats remain preserved and classified.
- Related research remains non-gating and the CP107 architecture promotes zero hard external prerequisites.
- Universal Installation Space remains authoritative for support/AUX installations.
- Starting shuttle = 1; tactical Fuel working scale = 100 / 2 per traversed hex / +1 EvM; TL1 Ablative Armor = 1 Space.
- Zero trials and zero new TL4-TL9 balance values.

## Acceptance status
Do not use the CP107a acceptance command. CP107a is preserved only as failed-candidate provenance. Use the CP107b hotfix instead:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-107b\apply_checkpoint_107b.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-107b\apply_checkpoint_107b.ps1
```

CP107b retains the alias-collision protection and additionally makes optional checkpoint-definition properties safe under strict mode.
