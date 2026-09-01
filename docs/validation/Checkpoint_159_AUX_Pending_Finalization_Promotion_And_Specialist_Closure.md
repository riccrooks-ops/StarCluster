# Checkpoint 159 — AUX Pending-Finalization Promotion and Specialist Closure

Status: native-accepted on 2026-08-30.

## Native acceptance

Native Windows acceptance completed on 2026-08-30 with 604/604 Python tests, 934/934 xUnit tests, 70/70 ScenarioRunner self-tests, 25/25 research-parity cases, 30/30 CP159 focused tests, 3,390,000 substantive combats, and 1,728,000 Damage-Control microtrials. Substantive errors and turn-cap sentinels were both zero. CP160 consumes this evidence for zero-combat PF4 promotion.

## Purpose

CP159 is the intentionally small closure pass after accepted CP158. It first advances the research execution baseline to **CP159-PF3** without changing the accepted PF2 main, PDS, core-defense, movement, EW, or provisional Reactor/TP execution values. PF3 promotes the well-bracketed CP158 AUX trajectories to **Pending Finalization**, preserves their full CP158 response surfaces, and explicitly supersedes the CP158 Repair Drone percentage-bonus placeholder.

New substantive work is restricted to three remaining AUX questions:

1. **Field Stabilizer specialist closure** — test substantially larger incoming-SPEN reduction so the system can be judged in its intended high-SPEN niche rather than by ordinary average uplift.
2. **Damage-Control Drone closure** — validate the adopted mechanic of one additional Damage Control action per phase, at normal target rules/costs, against a *different* repair target; no same-target reroll. Sweep additional Repair Kits from +0 through +100% of the ship's normal prepared kit reserve.
3. **Crystalline Armor late-TL headroom** — a narrow TL8–TL9 boundary extension only; no repeat of the CP158 broad AUX sweep.

Final Reactor/TP scarcity and power-supply AUX remain explicitly out of scope.

## PF3 pending-finalization AUX promotion

The CP158 technology-coherent `RISING_FULL` execution trajectories are promoted as current pending-finalization research centers for:

- Shield Battery
- Shield Booster
- Shield Hardener
- Ablative Armor
- Energized Armor

Crystalline Armor's CP158 rising trajectory is retained as **boundary-supported pending finalization** pending the TL8–9 headroom check. Kinetic/Missile Magazine +25 remains an endurance/logistics reference rather than a duel-balance lever.

Field Stabilizer's *mechanic* is retained, but its magnitude is not promoted as closed. Repair Drone's CP158 chance-bonus/finite-kit placeholder is explicitly superseded by the new parallel-action mechanic.

## Field Stabilizer specialist sweep

The Field Stabilizer reduces incoming SPEN before effective Shield DEF is resolved. It does **not** add Shield DEF. Therefore it should be modest against low/no-SPEN attacks and become valuable specifically against high-SPEN threats.

CP159 tests TL7–TL9 Energy attacks, where the accepted E7 SPEN values are 19/20/22. Candidate reduction extends from **4 through 24 in steps of 2**, crossed with **0/1/2 TP**, one Space. This intentionally reaches complete SPEN nullification and beyond so the response surface is bracketed rather than ending at the old 1–4 boundary.

Deep trajectories include low/center/high/max reduction, passive/high, expensive/high, plus the promoted Shield Hardener comparator. A focused Field Stabilizer × Shield Hardener layer tests whether the specialist and general shield defenses stack benignly.

## Damage-Control Drone + Repair Kits

Adopted semantic:

> A Damage-Control Drone grants one additional Damage Control action during each Damage Control phase. The crew and Drone must target different eligible repair targets during that phase. The Drone uses normal target-specific Damage Control success rules, TP cost, and Repair Kit consumption. It never grants a same-target reroll.

The accepted full-map Python combat corpus currently simplifies Damage Control to Hull-only, while the game/ScenarioRunner includes component-first Damage Control states. CP159 therefore does **not** create a fake full-combat bonus by rerolling Hull repair. Instead it uses a dedicated multi-target Damage-Control microstudy with disabled, degraded, Hull, mixed, and sustained-attrition workloads.

At TL2–TL9, every integer additional-kit count from **+0 through +100% of the normal prepared Repair Kit reserve** is evaluated. Two TP availability controls (1 and 2) distinguish a ship that can only support the normal crew action from one that can support crew + Drone in parallel. The microstudy uses 3,000 trials per cell.

This closes the Drone's action semantics and kit-endurance response. Its final whole-ship economic value remains subject to the final Reactor/TP pass and later integrated component-damage execution; CP159 does not pretend the Hull-only full-map model can answer that unavailable question.

## Crystalline Armor headroom

Only TL8–TL9 are reopened. Candidate capacity bonus is **+8/+10/+12/+14/+16** and RES bonus **+15/+20/+25/+30 pp**. Six technology-coherent deep trajectories cover the accepted strong boundary through substantially stronger headroom. The prior CP158 broad surface remains authoritative and is not rerun.

## Planned scale

- Matched PF3 baseline: 2,400 contexts × 50 = **120,000 combats**.
- Field Stabilizer broad specialist screen: 17,820 cells × 50 = **891,000 combats**.
- Crystalline TL8–9 headroom screen: 32,000 cells × 30 = **960,000 combats**.
- Field Stabilizer deep: 3,780 cells × 100 = **378,000 combats**.
- Crystalline deep: 9,600 cells × 100 = **960,000 combats**.
- Field Stabilizer × Shield Hardener interactions: 1,620 cells × 50 = **81,000 combats**.
- **Total substantive full-combat contract: 3,390,000 combats.**
- Damage-Control Drone microstudy: 576 cells × 3,000 = **1,728,000 non-combat microtrials**.

## Guardrails

- CP159-PF3 is the mandatory execution baseline; raw production v0.9 is not a legal substantive-research starting point.
- Balance means distinct viable choices, not equality.
- No global 50-percent target or inter-family equalization objective.
- No resweep of K/E/GP/Swarmer, K/E/AMM PDS, or core Hull/Shield/Armor/DEF/RES.
- CP158 AUX response surfaces remain preserved; this pass only closes the unresolved specialist/boundary questions.
- Repair Drone cannot reroll the same target in one Damage Control phase.
- Repair Kit sweep is endurance analysis, not an instruction to consume all kits every fight.
- No Reactor/TP supply tuning or power-supply AUX tuning.
- No automatic numerical promotion from post-study results. If closure succeeds, a subsequent zero-combat PF4 checkpoint performs the final AUX pending-finalization promotion with explicit provenance.

## Native workflow

```powershell
.\tools\checkpoints\checkpoint-159\apply_checkpoint_159.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-159\apply_checkpoint_159.ps1
```

Default substantive parallelism is 24 jobs. Full-combat stages are independently resume-safe; the Drone microstudy is deterministic and inexpensive relative to the combat corpus.
