# Checkpoint 158 — Defense/AUX Lifetime Viability and PF2 Classification

Status: candidate pending native Windows acceptance.

## Purpose

CP158 is the first substantive balance pass that is required to execute from the materialized pending-finalization research authority rather than reconstructing a historical overlay chain. It supersedes CP157-PF1 for research execution with **CP158-PF2** without changing any executable PF1 numerical value. PF2 only refines provenance classification and stale explanatory notes before the AUX study begins.

The pass then maps broad response surfaces for currently open defensive/support AUX families against the fixed CP157 main/PDS/core-defense environment. It does **not** reopen the closed main-weapon or PDS searches and does not perform final Reactor/TP tuning.

## PF2 classification precision

The former generic `PROVISIONAL_RESEARCH_SCAFFOLD` class is split so future work cannot accidentally treat established mechanics as tunable economic scaffolding:

- `FROZEN_RESEARCH_MECHANIC` — 73 fields, covering established Swarmer and Missile-guidance mechanics.
- `PROVISIONAL_RESOURCE_SCAFFOLD` — 63 fields, covering Reactor/TP/Space/resource quantities that remain subject to later economic closure.
- `PENDING_FINALIZATION_SELECTED` — 348 selected main/PDS research fields.
- `PENDING_FINALIZATION_VALIDATED_ENVIRONMENT` — 54 validated defense/environment fields.

PF2 keeps K1/E7/M2/SW2 and K155P06/E155P08/A155P07 as the primary execution center, retains M3/K155P03/E155P07/A155P09 as required alternatives, and retains production v0.9 as a separate historical/runtime authority. The PF2 conformance report is a hard preflight gate.

## Broad AUX sweep

The candidate population is **703 candidate-TL points**:

| Family | TL window | Broad dimensions | Candidate-TL points |
|---|---|---|---:|
| Shield Hardener | TL3–9 | DEF +5/+10/+15/+20 pp × TP 1/2 | 56 |
| Shield Battery | TL1–9 | restore 2/4/6/8 × charges 1/2/3 × Space 1/2 | 216 |
| Shield Booster | TL2–9 | Shield capacity +2/+4/+6/+8 × Space 1/2 | 64 |
| Ablative Armor | TL1–9 | outer AI 2/4/6/8/10 | 45 |
| Crystalline Armor | TL6–9 | Armor capacity +2/+4/+6/+8 × RES +0/+5/+10/+15 pp | 64 |
| Energized Armor | TL5–9 | RES +5/+10/+15/+20 pp × TP 1/2/3 × Space 1/2 | 120 |
| Field Stabilizer | TL7–9 | incoming SPEN reduction 1/2/3/4 × TP 1/2 × Space 1/2 | 48 |
| Repair Drone | TL4–6 | DC chance +5/+10/+15/+20 pp × extra kits 0/1/2 × Space 1/2 | 72 |
| Kinetic Magazine | TL1–9 | fixed +25 audit only | 9 |
| Missile Magazine | TL1–9 | fixed +25 audit only | 9 |

General power-generation/storage AUX remain deferred to the final Reactor/TP pass. Noncombat/campaign AUX are preserved architecturally rather than assigned invented combat effects. ECM/ECCM and PDS reuse the closed integrated findings.

## Study structure

The fixed Stage-A environment is the accepted 6,850-context whole-combat surface with five executable resource environments.

- Matched PF2 no-candidate baseline: 6,850 cells × 50 = **342,500 combats**.
- Broad single-AUX screen: 497,555 legal candidate/context cells × 25 = **12,438,875 combats**.
- Architecture-stratified deep confirmation: 64 whole-lifecycle ladders and 277,160 legal cells × 100 = **27,716,000 combats**.
- CENTER/HIGH pairwise interactions: 169,040 legal cells × 25 = **4,226,000 combats**.
- **Total substantive contract: 44,723,375 combats**.

The eight deep trajectories per swept family deliberately include flat economy/center/high/max envelopes, resource-stress cases where applicable, and rising technology-maturation paths. They are not selected by a hidden 50-percent or equality objective. Pairwise interaction is evaluated at both CENTER and HIGH anchors and measured as combined uplift minus the corresponding two single-family anchor uplifts.

## Guardrails

- Balance means diverse viable choices, not numerical equality.
- No global 50-percent target or inter-family equalization objective.
- K/E/GP/Swarmer and K/E/AMM PDS response surfaces are reused, not broadly reopened.
- Core Hull/Shield/Armor/DEF/RES remain fixed to PF2.
- Ammo is an endurance audit, not a fine tuning axis.
- Power-supply/storage AUX and final Reactor/TP scarcity remain deferred.
- All broad/deep/pairwise surfaces are preserved; automatic numerical promotion is forbidden.
- Any future change to PF2 must explicitly supersede the baseline with provenance rather than silently mixing old and new values.

## Native workflow

```powershell
.\tools\checkpoints\checkpoint-158\apply_checkpoint_158.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-158\apply_checkpoint_158.ps1
```

Default substantive parallelism is 24 jobs and may be overridden with `-Jobs`. The baseline, 66 family/TL broad batches, 32 deep batches, and nine pairwise TL batches are independently resumable.
