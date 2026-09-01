# Checkpoint 26 Validation Runbook

From the repository root, close Godot and run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-26\apply_checkpoint_26.ps1 `
  -RepositoryContractOnly

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-26\apply_checkpoint_26.ps1
```

The full run verifies the manifest, active documents, exact 126-value baseline, seven Phase B scenario documents and 36 unique cases, a clean warnings-as-errors build, the full unit-test suite, seven accepted moving-missile scenarios, 12 Phase A documents / 54 cases, seven Phase B documents / 36 cases, and 46 ScenarioRunner self-tests.
