# Checkpoint 137 - Finite In-Combat Armor Regeneration Reserve

## Purpose

CP137 is a one-mechanic common-random-number comparison against native-accepted CP136. CP136 showed that lower Armor Integrity and smaller per-turn regeneration caps did not eliminate high-TL stalemates because unlimited 1-AI-per-turn recovery could still match persistent damage. CP137 therefore leaves every numerical characteristic unchanged and limits only total in-combat Armor regeneration.

## Candidate rule

- TL6: 1 AI/TP, max 1 TP/turn, **3 AI total combat reserve**.
- TL7: 1 AI/TP, max 1 TP/turn, **4 AI total combat reserve**.
- TL8: 1 AI/TP, max 1 TP/turn, **5 AI total combat reserve**.
- TL9: 1 AI/TP, max 2 TP/turn, **6 AI total combat reserve**.
- One reserve point is consumed per AI actually restored.
- Once reserve reaches zero, no further in-combat Armor regeneration occurs during that engagement.
- Out-of-combat self-healing is separate; exact recovery time/resources/facilities and reserve replenishment are deferred.
- TL6 A_b1 Crystalline remains AP2/AI11 with no regeneration/reserve.

Reactor TP is explicitly **not** changed in CP137. TP pressure will be evaluated after this isolated regeneration test.

## Comparison design

CP137 preserves CP136's master seed `134001`, logical context IDs, mover-order variant IDs, reference builds, Shield/DamCon/PDS behavior, TL6 Armor strata, and 5,000 trials/variant.

- logical contexts: 196
- mover-order variants: 392
- TL6 variants: 136
- symmetry gate: 50 mirrored comparisons / 100 executions
- full-matrix smoke: 392 variants x 1 trial
- substantive: 392 variants x 5,000 trials = 1,960,000 engagements
- mixed-TL ships: none
- balance target: none
- automatic promotion: none

New telemetry records initial combat regeneration reserve, reserve spent, exhaustion events, and turns where damaged Armor could not regenerate because its reserve was exhausted.

## Native acceptance sequence

Run `tools/checkpoints/checkpoint-137/apply_checkpoint_137.ps1 -RepositoryOnly` first in a fresh extraction. It must pass wrapper dependency preflight, accepted CP136 evidence checks, the complete Python suite, warning-as-error .NET build, xUnit, ScenarioRunner self-tests, deterministic corpora, research parity, CP137-specific tests, plan, symmetry, and full-matrix smoke.

Then run the same wrapper without `-RepositoryOnly` in the unchanged extraction. The final invocation executes the 1.96M substantive rerun and records review diagnostics without automatic balance promotion.
