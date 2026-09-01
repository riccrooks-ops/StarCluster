# Checkpoint 136 - Armor Regeneration and Crystalline Rebaseline

## Purpose

CP136 makes a deliberately narrow before/after change to the native-accepted CP135 same-TL diagnostic. It does **not** retune Shield recharge, Damage Control, Repair Kits, weapons, Hull, Reactor, PDS, Space, movement, range/track modifiers, or study population.

The numerical changes are confined to Armor:

- TL6 mainline: AP1 / AI9 / 1 AI per TP / cap 1 TP.
- TL7 mainline: AP1 / AI10 / 1 AI per TP / cap 1 TP.
- TL8 mainline: AP2 / AI11 / 1 AI per TP / cap 1 TP.
- TL9 mainline: AP3 / AI12 / 1 AI per TP / cap 2 TP.
- TL6 A_b1 Crystalline: AP2 / AI11 / no regeneration; later progression TBD.
- TL1-TL5 mainline Armor remains unchanged and non-regenerative.

The intent is steady rather than rapid Armor recovery. Regeneration should remain tactically meaningful without creating a hard equilibrium where a contemporary Main's persistent Armor damage is exactly erased every turn.

## Comparison design

CP136 preserves CP135's master seed `134001`, logical context IDs, mover-order variant IDs, reference builds, Shield/DamCon/PDS behavior, TL6 Armor strata, and 5,000 trials/variant.

- logical contexts: 196
- mover-order variants: 392
- TL6 variants: 136
- symmetry gate: 50 mirrored comparisons / 100 executions
- full-matrix smoke: 392 variants x 1 trial
- substantive: 392 variants x 5,000 trials = 1,960,000 engagements
- mixed-TL ships: none
- balance target: none
- automatic promotion: none

## Interpretation

Compare directly against CP135 unresolved rates, combat duration, AI damage versus AI regenerated, first Hull penetration, DamCon use, weapon-family viability, TL6 mainline-vs-Crystalline outcomes, and Missile PDS-off/on effects. A 50/50 result is not a goal. The design target is that items remain viable and reasonable while family identities remain distinct.


## Corrected Replacement 1

The initial CP136 archive contained a packaging-only wrapper regression: `apply_checkpoint_136.ps1` bound `$preflight` and `$contract` to stale CP135 filenames that do not exist in the CP136 directory. Corrected Replacement 1 binds those variables to `preflight_checkpoint_136.py` and `test_checkpoint_136_contract.py`. CP136 preflight now inspects the wrapper itself, requires both CP136 dependency files to exist, requires the exact CP136 bindings, and rejects stale CP135 checkpoint-script filenames before any long-running native gate. No gameplay, technology numerical value, study geometry, Concept semantics, or simulation-kernel behavior changed in this replacement.

## Native acceptance sequence

Run `tools/checkpoints/checkpoint-136/apply_checkpoint_136.ps1 -RepositoryOnly` first in a fresh extraction. It must pass deterministic runtimes, repository preflight, the complete Python suite, warning-as-error .NET build, xUnit, ScenarioRunner self-tests, deterministic corpora, research parity, CP136-specific tests, plan, symmetry, and full-matrix smoke.

Then run the same wrapper without `-RepositoryOnly` in the unchanged extraction. The final invocation executes the 1.96M substantive rerun and records review diagnostics without automatic balance promotion.
