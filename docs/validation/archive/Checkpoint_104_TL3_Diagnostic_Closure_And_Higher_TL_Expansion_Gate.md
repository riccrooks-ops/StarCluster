# Checkpoint 104 — TL3 Diagnostic Closure and Higher-TL Expansion Gate

## Purpose

CP104 is intentionally the **last planned TL3-focused diagnostic checkpoint** before Star Cluster resumes filling the higher Technology-Level subsystem chart. It does not change the accepted CP103 game/mechanics baseline or any TL3 value.

CP103 established that TL3 advancement is useful but not universally dominant, while exposing four questions worth one focused follow-up: legacy dual-main stacking, Kinetic/Missile mover-order cliffs, Energy TL3 synergy, and Tactical Power/population-weight sensitivity.

## Accepted baseline

Checkpoint 103 Corrected Replacement 6 is native-accepted. Its accepted evidence is embedded under `docs/validation/evidence/checkpoint-103/`, including the native acceptance summary and the exact primary substantive `variants.csv` used for CP104 reweight sensitivity.

Authoritative CP103 hashes:

- normal definition: `f9fa4ae6bb2063f504d8a347757ae503a8d7594167c19ba92b185ba71db92caf`;
- repository manifest: `ecc3b0c4db276f8302d320143cfee9e9e649d8ad601efb193aa5e600414a4ae2`;
- native results ZIP: `6247ffcdc9a8b5cfcb56f44621800021e9562bc7ab303bc206d8d4ee9d9eafff`.

## New study

`cross-tl-build-permutation-foundation-v1_3.json` uses schema v8 diagnostic-overlay mode.

Deterministic contract:

- declared option product: 124,002,900;
- 56 named recipes resolving to 52 unique legal builds;
- Space classes: 12 exact-fill / 14 near-fill / 26 underfilled;
- 128 mirrored logical pairings;
- 2 Adaptive Engage movement-order geometries;
- 256 generated variants;
- 500 trials per variant;
- 128,000 substantive trials;
- population-inference weight: zero.

### A. Legacy-frontier response

Sixteen comparisons revisit CP103's dual K1/K2 and E1/E2 signals against contemporary K3/E3 responses that actually spend more of the 36-Space envelope: dual frontier mains, compact dual-reactor + Hardener packages, and a 35-Space balanced EW/PDS/Hardener package. The original 30/36 single-frontier control remains present.

### B. Mover-order decomposition

Ten Kinetic/Missile comparisons isolate four states: complete TL2, TL2 with STL3 only, TL3 package held to STL2, and full TL3. Review must separate the higher-capability side moving first versus second rather than relying only on mover-neutral averages.

### C. Energy synergy decomposition

Twenty-two comparisons isolate E3, Reactor3, Computer3, Sensor3, Armor3, STL3, Hull3, selected two-/three-way combinations, a four-component offense core, and complete TL3/no-STL controls. The purpose is diagnosis, not tuning the Energy family until every marginal comparison is 50/50.

### D. Power hot spots and CP103 weighting sensitivity

Fourteen controlled hot-spot comparisons start from CP103 high-shortfall builds and change one relevant power/Space decision at a time where legal. Separately, the accepted CP103 statistical bundles are reviewed under combinatorial-population, equal-bundle, equal-cell, equal-composition, equal-progression, and equal-Space-pair weighting. These are sensitivity lenses, not claimed player-build priors.

## Release gates

Blocking gates cover repository integrity, native build/tests, deterministic mechanics, Python environment/unit/parity, exact study shape, exact accepted-CP103 reweight source shape, trial completion, and output completeness.

**No matchup win-rate is a release gate.** No result automatically changes TL3 values.

## Higher-TL handoff

If CP104 passes and review finds no architectural defect, the next major phase is explicitly:

> **continue filling the basic subsystem Technology-Level chart beyond TL3, then use the standing cross-TL research architecture to evaluate interactions across nonadjacent and mixed Technology Levels.**

Further TL3 calibration requires a concrete reason that would invalidate that broader work, not merely a desire to make every current matchup locally tidy.

## Native acceptance

From one clean extraction, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-104\apply_checkpoint_104.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-104\apply_checkpoint_104.ps1
```

Run the full command immediately after RepositoryOnly in the same extracted tree.
