# Checkpoint 117 - Weapon-Family Simplification and Swarmer Architecture

## Purpose

CP117 is a deliberate KISS consolidation after the broad CP114-CP116 payload characteristic-space studies. It changes the active design expression without promoting numerical weapon values or adding another Monte Carlo study.

## Accepted baseline

Checkpoint 116 native acceptance is embedded under `docs/validation/evidence/checkpoint-116/native-results/` and summarized by `CP116_NATIVE_ACCEPTANCE_SUMMARY.json`:

- 2,976 variants;
- 2,000 trials per variant;
- 5,952,000 engagements;
- zero failed gates;
- 128 adaptive-pair summary rows / 20 rows with natural switches;
- `layered_defense_hull_only` research consumer;
- no automatic promotion.

## CP117 design contract

- Energy retains bounded power/output modes.
- Normal Kinetic ammunition uses one broad pool; compatible projectile/material/smart-guidance improvements auto-mature when they are strict improvements.
- Normal Missile GP payloads auto-mature primarily by energetic yield at major milestones; yield maturation does not silently add SPEN/APEN.
- Swarmer Missile is a distinct Missile Flight family, provisionally centered on TL5-TL7: one Flight counter, one terminal attack roll, lower concentrated packet strength, coverage, and a bounded candidate PDS-saturation trait.
- Shaped/APEN, shield-disruption, radiation/electronics, Kinetic tandem/saturation/dense-selector and similar characteristic-space ideas remain preserved but are not normal standing menus.
- TL1-TL6 drive calibration; TL7 is advanced validation; TL8-TL9 are endpoint/stress checks.

## Frozen boundaries

CP117 changes no production C#/Godot source, no CP109 candidate numerical matrix, no CP110 Reactor profile, and no Python research/combat implementation. The accepted CP116 C#/test and research-executable surfaces are hash-frozen in CP117 evidence.

Concept authority advances to `Star_Cluster_Game_Concept_v0.7l.docx`; Storyboard to v1.4; Component Table to v0.4; Idea Register to v1.5; weapon-ammunition architecture to v0.3.

## Validation commands

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-117\apply_checkpoint_117.ps1 -RepositoryOnly
```

Then:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-117\apply_checkpoint_117.ps1
```

Both paths are deterministic. CP117 intentionally runs **zero substantive Monte Carlo trials**; the normal path explicitly confirms that boundary rather than launching another calibration workload.

## Next pass boundary

After CP117 native acceptance, use a deliberately small TL1-TL7 study to narrow GP Missile yield milestones and a few Swarmer coverage/PDS-saturation candidates. TL8-TL9 remain endpoint sanity/stress checks. No value promotes automatically.
