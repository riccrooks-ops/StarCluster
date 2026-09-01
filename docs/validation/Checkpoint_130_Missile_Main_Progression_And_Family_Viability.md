# Checkpoint 130 — Missile Main Progression and Family Viability

## Objective

Measure whether GP Missile warhead progression adequately compensates for Missile's Firm-track, flight-time, PDS, and finite-ammunition constraints across TL1-TL9 without changing the accepted Tech Table during the study.

## Native sequence

From a clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-130\apply_checkpoint_130.ps1 -RepositoryOnly -Jobs 24
```

If and only if RepositoryOnly succeeds, run in the same unchanged extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-130\apply_checkpoint_130.ps1 -Jobs 24
```

`-Jobs` may be any integer from 1 through 61 and controls concurrency only.

## RepositoryOnly acceptance

RepositoryOnly must verify:

1. Python 3.13 and pinned .NET SDK 8.0.423;
2. repository evidence-package hygiene;
3. accepted CP129 native evidence and frozen CP129 production/numerical/pre-existing research surfaces;
4. all Python self-tests (183 expected);
5. warning-as-error native build;
6. 907/907 xUnit tests;
7. 70/70 ScenarioRunner self-tests;
8. 25/25 research parity fixtures;
9. exact CP130 plan: 9,427 legal builds, 240,996 variants, 24,099,600 planned substantive engagements;
10. inherited full-map physical symmetry: 2,250 comparisons / 4,500 executions / zero mismatches;
11. complete 240,996-variant one-trial candidate smoke with zero trial errors;
12. CP130 repository/results contract.

## Substantive acceptance

The substantive phase must consume the valid RepositoryOnly marker from the same extraction and complete 24,099,600 engagements with zero trial errors. It must also reproduce accepted CP129 current-warhead Missile chart metrics exactly at every TL for Missile mirror mean turns/unresolved rate and K/E conditional win rate against Missile.

No result automatically changes the Tech Table. Review must compare +1/+2 TL1-TL7 damage sensitivity and the TL8/TL9 nested maturation candidates using family win share, fight length, unresolved behavior, PDS/Shield context, GP-only results, and single-Main-vs-single-Main diagnostics.
