# Checkpoint 77a - PowerShell 5.1 DOCX Contract Reader Hotfix

## Purpose

Checkpoint 77a is a native-acceptance hotfix over Checkpoint 77. It does **not** change combat mechanics, degraded-fire balance, Tactical Computer architecture, missile behavior, Concept v0.6p content, ScenarioRunner behavior, or validation workload.

The first CP77 `-RepositoryOnly` acceptance stopped during `Validating Concept and missile architecture synchronization...` with:

`You cannot call a method on a null-valued expression.`

The failure occurs in the repository contract's DOCX text helper. CP77 read `word/document.xml` into `System.Xml.XmlDocument` and returned `XmlDocument.InnerText`. Under the native Windows PowerShell 5.1/.NET Framework acceptance path, the document-node `InnerText` value is not a safe cross-runtime assumption. The next `.Contains(...)` assertion therefore attempted to invoke a method on a null value.

## Hotfix

CP77a keeps every CP77 architecture and gameplay artifact frozen and changes only native validation/hotfix packaging:

- DOCX extraction now reads `DocumentElement.InnerText`, which is the actual `w:document` element whose descendant text is required by the contract;
- the helper explicitly verifies the DOCX, `word/document.xml`, parsed XML document element, and extracted text before returning;
- `Add-Type` output is suppressed so helper output cannot be polluted by assembly/type-loading objects;
- plain-text contract reads now use `System.IO.File.ReadAllText` through a guarded `Read-Text` helper, eliminating analogous nullable `Get-Content -Raw` assumptions;
- the CP77a contract validates its own native-dependency path bindings and provides specific assertion messages instead of a generic null-method exception;
- the accepted CP77 architecture-scrub runbook is archived and this hotfix is the sole active validation runbook.

## Frozen architecture and workload

The following remain unchanged from CP77:

- Concept `Star_Cluster_Game_Concept_v0.6p.docx`;
- weapon-specific degraded-fire permission and Tactical-Computer-owned penalty architecture;
- TL1 Tactical Computer degraded-fire working value of -25 percentage points;
- ordinary missile Firm-terminal rules and future Swarmer/volume-saturation concept boundary;
- production exclusion of degraded-fire-enabled weapons;
- all Core/Game/ScenarioRunner mechanics and deterministic behavior tests;
- normal validation: 8 deterministic/architecture stages, 47 ScenarioRunner self-tests, zero Monte Carlo workload;
- optional Deep Calibration: 30 stages and the same retained historical workload as CP77.

No Deep Calibration is required merely for this contract-reader hotfix.

## Native acceptance

Run the repository contract first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-77a\apply_checkpoint_77a.ps1 -RepositoryOnly
```

If it passes, run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-77a\apply_checkpoint_77a.ps1 -Jobs 24
```

Expected normal acceptance remains the CP77 target: pinned .NET SDK 8.0.423, warning-as-error build with zero warnings/errors, approximately 863 unit tests, 8/8 runner stages, 47 ScenarioRunner self-tests, zero Monte Carlo trials, and zero failed deterministic release gates/runner errors.
