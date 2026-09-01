# Checkpoint 135 - Shield Recharge and Damage Control Rebaseline

## Purpose

CP135 makes a deliberately narrow before/after change to the native-accepted CP134 same-TL diagnostic. It does **not** retune weapons, Armor, Hull, Reactor, PDS, Space, movement, track/range modifiers, TL6 A_b1, or study population.

The two numerical changes are:

1. Shield Base/Tactical Recharge is reduced so a fully collapsed contemporary Shield cannot return to full SC in one legal recharge window even at maximum Tactical Recharge.
2. Prepared Damage Control Repair Kits progress `3/3/4/4/5/5/6/6/7` from TL1-TL9. Existing repair chances and Hull-per-success yields are held.

CP135 also closes an implementation gap exposed during preparation: CP134 reported Damage Control telemetry fields but its same-TL full-map consumer did not execute Hull repair. Kernel v0.3 executes one consistent Hull-only Damage Control doctrine in all CP135 lanes.

## Hull-only Damage Control doctrine

- only surviving ships below maximum Hull attempt repair;
- at most one Hull-repair attempt per ship per Damage Control phase;
- every attempt consumes 1 Tactical Power and 1 prepared Repair Kit, success or failure;
- TL-specific Hull repair chance and Hull restored per success come from the candidate table;
- successful repair is queued and becomes active at the following Turn Refresh;
- component repair is not exercised in this diagnostic;
- tactical Armor regeneration remains separate and may use remaining TP after the Hull-repair attempt.

Telemetry must report attempts, successes, kits consumed, TP spent, queued Hull repair, and Hull actually restored.

## Comparison design

CP135 preserves CP134's master seed `134001`, logical context IDs, mover-order variant IDs, reference builds, TL6 Armor strata, PDS strata, and 5,000 trials/variant. This common-random-number design improves attribution of changes to Shield recharge and Hull Damage Control without pretending every diverged combat path will consume identical random draws.

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

The primary comparison against CP134 is pacing and sustained-progress behavior: unresolved rate, mean turns, Shield collapse/reconstitution, Armor/Hull damage, and whether K/E/M/S can make durable progress against contemporary layered defenses. Damage Control is finite endurance, so its attempts/successes/kits/Hull restored must be separated from renewable Shield and Armor recovery.

PDS-off/on Missile comparisons and TL6 mainline/A_b1 comparisons remain diagnostic strata. No result is tuned toward 50/50.

## Native acceptance sequence

Run `tools/checkpoints/checkpoint-135/apply_checkpoint_135.ps1 -RepositoryOnly` first in a fresh extraction. It must pass the deterministic runtimes, repository preflight, complete Python suite, warning-as-error .NET build, xUnit, ScenarioRunner self-tests, deterministic corpora, research parity, CP135-specific tests, plan, symmetry, and full-matrix smoke.

Then run the same wrapper without `-RepositoryOnly` in the unchanged extraction. The final invocation executes the 1.96M substantive rerun and records review diagnostics without automatic balance promotion.
