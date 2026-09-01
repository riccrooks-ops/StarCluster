# Checkpoint 107a - Unaccepted Native Candidate

Checkpoint 107a did not reach native acceptance. Its first `-RepositoryOnly` run stopped in the shared native dependency precheck before the CP107a contract executed.

The failure was caused by a strict-mode schema assumption in `Test-NativeAcceptanceDependencies.ps1`: the guard accessed `$definition.stages` directly, while the CP107a architecture-only definition omitted the optional `stages` property. Under `Set-StrictMode -Version 2.0`, that missing property raises `PropertyNotFoundStrict`.

`CHECKPOINT_107A_SHA256SUMS.txt` is preserved here as exact provenance for the failed candidate. Checkpoint 107b supersedes CP107a as the acceptance-hotfix candidate while preserving the CP107 technology/component design content unchanged.
