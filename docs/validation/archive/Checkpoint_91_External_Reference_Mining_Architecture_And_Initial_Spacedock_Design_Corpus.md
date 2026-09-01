# Checkpoint 91 - External Reference Mining Architecture and Initial Spacedock Design Corpus

## Purpose

Checkpoint 91 pauses substantive calibration work to preserve the external reference-mining workflow developed in the current design discussion. It establishes a controlled corpus for user-supplied external references without promoting mined ideas into Star Cluster game authority.

This is a **documentation/reference-infrastructure checkpoint**. It does not retune technology, change combat mechanics, alter ScenarioRunner behavior, modify tests, revise the Concept, or change the Technology Architecture Matrix/Component Catalog/AI doctrine/standing permutation suite.

## Accepted baseline

Checkpoint 90a is the native-validated baseline carried into CP91:

- .NET SDK 8.0.423 matched.
- Warning-as-error build: 0 warnings / 0 errors.
- Unit tests: 863 / 863 passed.
- Runner stages: 13 / 13 passed.
- ScenarioRunner self-tests: 56.
- CP90 generalized screen: 432 variants, 432 one-trial smoke executions, 4,320,000 substantive trials.
- Failed gates/trial errors: 0.
- CP90a repository manifest SHA-256: `8637eb74b97b2f6e5bea67e2c727b5650b6e5e2b1ca80a7b7b9cd54ac6c0ce2c`.
- CP90a definition SHA-256: `eabd5d18f695b5a7244e23dd4d1f85a76d2719bb2d010d4ea530d9ee71c3f7af`.
- CP90a substantive screening summary SHA-256: `0d9a66194c18ca7897405bd34d2190038df75531ba8060430666ea6b39a88854`.

Compact native provenance and the accepted CP90a manifest are embedded under `docs/validation/evidence/checkpoint-90a/`.

## Reference-mining architecture

Checkpoint 91 adds `docs/references/reference-mining/` with:

- `README.md` - workflow, authority boundary, relationship/disposition vocabulary, deduplication rule.
- `source-index.json` - six mined sources and the user's remaining 24-video queue.
- `observation-index.json` - 70 stable timestamped/paraphrased observations with project tags/assessments.
- `cross-source-themes.md` - recurring themes and discussion clusters; reference synthesis only.
- `spacedock/transcripts/` - exact user-supplied transcript files for the six mined videos.
- `spacedock/notes/` - one compact mining note per analyzed video.
- `SHA256SUMS.txt` - hash manifest for the reference-mining corpus itself.

The six mined sources are:

1. Damage Control.
2. Nuclear Lasers.
3. Energy Weapons.
4. Spinal Mounts.
5. Space Weapons (long compilation).
6. Spin Gravity.

## Authority rule

The reference-mining lifecycle is:

**Source -> Mined Observation -> Candidate Discussion -> Human Design Decision -> Appropriate Authority**

A transcript, observation, note, tag, theme, or candidate is not a gameplay rule. `adopted` may be used only after an explicit human decision and a deliberate update to the document that owns the result.

This checkpoint therefore preserves promising avenues such as maintainability/Hazards, qualitative Damage Control progression, Energy focusing/tunability/reactor coupling, spinal mount tradeoffs, modular missile/PDS/EW directions, possible Particle weapons, strategic mines, and gravity/habitation architecture **without adopting any of them**.

## Deduplication rule

The long Space Weapons source is a compilation containing material that likely overlaps many queued standalone videos. The source index marks likely overlap. When those standalone transcripts are provided, compare against the compilation chapter and create only genuinely new observations rather than duplicating the same source material.

## Validation strategy

CP91 uses dependency-driven validation:

- native/archive pre-check of runtime dependencies and the checkpoint-wrapper-to-harness interface, locking the proven direct named-parameter invocation and rejecting splatted wrapper forwarding;
- active-runbook command-text sanity, including rejection of unexpected control characters in the native command block;
- repository/contract checks;
- pinned SDK warning-as-error build;
- all 863 unit tests;
- accepted deterministic runner stages;
- 56 ScenarioRunner self-tests;
- reference-mining schema/count/hash/authority checks;
- exact CP90a hash freeze for runtime/tests/game authorities/standing simulation assets.

No Monte Carlo is run because no gameplay/runtime/simulation dependency changed. Deep Calibration is not applicable.

## Native commands

Repository-only first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-91\apply_checkpoint_91.ps1 -RepositoryOnly
```

Then the normal deterministic acceptance pass:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-91\apply_checkpoint_91.ps1 -Jobs 24
```

`-DeepCalibration` is intentionally unnecessary and adds no study workload.

## After acceptance

Resume reference mining from the queued source list. Prioritize genuinely new subject areas (for example Range/Accuracy, Kinetic vs Energy, Sensors, Power, Stealth, Radiation, Radiators, Space Exploration, FTL/Design FTL, Biomechanical Ships) before re-mining standalone sources that duplicate compilation chapters. Later, resume the CP90a generalized-screening methodology improvements as a separate substantive checkpoint.
