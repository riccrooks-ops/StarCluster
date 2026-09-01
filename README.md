# Star Cluster - Checkpoint 166 Candidate

CP166 begins whole-system testing with pure same-TL ships. The accepted base is CP165 CR3; current Concept/TL/current-working numerical authorities are hash-locked and production mechanics remain unpromoted.

Start with:

- `docs/CURRENT_AUTHORITIES.md` for the current design authority graph;
- `docs/validation/Checkpoint_166_Same_TL_Whole_System_Architecture_And_Tactical_Diagnostic.md` for the CP166 study rationale and execution boundary;
- `docs/validation/evidence/checkpoint-166/cp166_same_tl_whole_system_study_v0_1.json` for the exact study contract.

Native Windows acceptance uses the same fresh extraction for both commands:

```powershell
.\tools\checkpoints\checkpoint-166\apply_checkpoint_166.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-166\apply_checkpoint_166.ps1
```

The substantive run is resumable by TL and defaults to 24 workers. CP166 is diagnostic only: balance/tactics watches do not automatically tune or promote values.
