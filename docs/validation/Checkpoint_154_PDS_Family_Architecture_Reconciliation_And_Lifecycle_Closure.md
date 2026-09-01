# Checkpoint 154 — PDS Family Architecture Reconciliation and Lifecycle Closure

Status: **corrected replacement CR1 pending native Windows acceptance**.

**CR1 correction (2026-08-29):** the first native substantive run completed all 126 broad-screen batches and all 12 deep-confirmation batches, then failed only in the post-combat deep merge. The finalizer correctly populated the response dimension as `scenario_stratum` but the selection-score expression referenced the nonexistent key `stratum`, producing `KeyError: 'stratum'`. CR1 changes only that lookup to `scenario_stratum` and hardens the PowerShell captured-command wrapper so native stderr reaches the explicit exit-code/tail handler. The PDS architecture, candidate population, seeds, contexts, combat kernel, ladder synthesis, substantive results, numerical authority, Concept, and production C# are unchanged. Existing valid CP154 candidate/deep batch outputs are resumable and must not be discarded merely because this post-processing defect occurred.

For a native tree that already completed the first CP154 substantive run, install/overwrite the CR1 repository-owned files **without deleting `out/checkpoint-154`**, then rerun the normal wrapper (not `-RepositoryOnly`). The wrapper revalidates the repository and existing RepositoryOnly summary, deterministically rebuilds the plan/merged candidate evidence/ladder synthesis, validates all 126 candidate batches and all 12 deep batches, reuses valid batches, and reruns only the corrected deep merge/final acceptance/package path.

CP154 follows native-accepted CP153 and is the dedicated point-defense closure checkpoint. It makes **no production numerical promotion**. The active Technology Numerical Matrix, Concept authority, production C#, current CP153 main-weapon evidence, Shield/Armor/DEF/RES values, current AUX environment, EW/Sensor rules, movement/missile cadence, and provisional Reactor/TP supply remain frozen while Kinetic PDS, Energy PDS, and AMM are reconciled and overswept.

## Reconciliation finding

The active numerical-matrix lineage v0.1 through v0.9 keeps Kinetic PDS at RC1. The current matrix gives Energy PDS scalable RC1/RC2 readiness in later TLs and gives AMM range 1 in later TLs, but it does not encode the intended AMM RC3/range-1 third-opportunity semantics. The active Concept and production terminal phase likewise define the standard two local terminal windows but do not yet implement the complete candidate architecture studied here.

CP154 therefore treats all revised PDS progression as **research evidence**, not as an assumed restoration. A matrix-history audit is emitted by the planner so the provenance remains inspectable.

## PDS architecture under test

Reaction Capacity (RC) is a per-turn pool of interception attempts. Attempts remain committed to the first arriving Missile Flight until that Flight is destroyed or all legal engagement opportunities against it are exhausted. Only then may unused RC spill to a later Flight.

- **Kinetic PDS:** local/same-hex terminal defense; RC1 or RC2 only; ammunition-fed; no range-1 opportunity; no Energy-style Strain overcharge.
- **Energy PDS:** local/same-hex terminal defense; RC1 or RC2 only; ammunition-free; can trade Tactical Power for RC2. Candidate RC2 states include both safe operation and an overcharged state in which the extra reaction adds one persistent PDS Strain **only if that extra reaction actually fires**. Normal research AI is safe-only and falls back to a legal lower readiness state at its Strain Limit rather than using Forced Overload as routine defense.
- **AMM:** ammunition-limited specialized interceptor. RC1/RC2 use the local terminal windows. Candidate RC3 is qualitatively different: it is available only with the AMM range-1 architecture and represents **one range-1 pre-terminal opportunity plus the two local terminal opportunities**. Kinetic and Energy candidates cannot acquire RC3 or range 1.

For the current research kernel, the range-1 AMM shot attacks the magazine Flight before terminal Swarmer subflights are individually exposed. If it misses, the remaining RC stays committed to that first Flight for its terminal windows; if it destroys the Flight, later RC may remain for another eligible Flight.

## Deliberate single-arrival scope

The accepted research cadence generally produces one arriving Flight per turn. CP154 does **not** manufacture simultaneous-Flight balance weighting merely to make spare RC measurable. Likewise, the fleet-defense value of a range-1 AMM shooting at a Flight aimed at another nearby ship is deferred. These are mechanics/integration values to validate when the full combat environment exposes them naturally, not invented balance weights for this closure pass.

The architecture itself remains future-proof: RC is a per-turn pool and is not defined as “number of Flights.”

## Oversweep population

Every TL is evaluated against the native-accepted CP153 offensive environment: K1, E7, GP Missile M2/M3, and Swarmer SW2 where unlocked. Current defenses/AUX and provisional TP supply are held fixed.

The broad candidate space is intentionally larger than the prior PDS studies:

- **Kinetic:** base chance 5–45 pp in 5-pp increments plus any exact current value; RC1/RC2; readiness TP 1/2/3; ammo 15/25/35/50/60/75/100.
- **Energy:** the same broad chance grid; RC1/RC2; RC1 TP 1/2/3; RC2 incremental TP 0/1/2; safe and overcharged RC2; Strain Limit 1/2/3/4 for overcharged states; no ammunition.
- **AMM:** the broad chance grid; RC1/RC2/RC3; ammo 6/12/18/25/35/50; broad tiered TP profiles; RC3 candidates begin as early as TL5 specifically to oversweep the unlock boundary and always require the range-1 architecture.

The resulting tested population is **14,748 candidate-TL points**.

## Broad screen and whole-ladder synthesis

The screen uses six existing combat strata: Balanced Core/no PDS, Shield Pressure, Armor Pressure, EW Contest, Recovery Attrition, and Power Crisis. At each TL it crosses eligible missile attackers with representative CP153 defender mains and rotates all five accepted resource ensembles across those cells. This produces **612 broad contexts** overall and **1,015,416 candidate-context cells**.

At 25 matched trials/cell the broad closure contains **25,385,400 substantive combats**.

The merged evidence then synthesizes **eight coherent TL1–TL9 ladders per PDS family** from actually tested candidates only. RC and base interception chance may hold or improve but not regress; Energy may mature from strained RC2 to safe RC2 but not regress from safe RC2 to strain-requiring RC2; AMM range-1/RC3, once acquired, does not regress. Distinct RC/Strain/range-one trajectories are preserved before duplicate-equivalent candidates fill remaining slots.

## Deep confirmation

All **24 whole-ladder finalists** receive the full 3,060-context PDS surface: every eligible attacker × defender-main × six-stratum × five-resource combination at every TL. At 100 matched trials/cell this adds **7,344,000 combats**.

Total substantive CP154 scale is therefore **32,729,400 combats**.

The deep merge reports family/lifecycle response surfaces and an offline 8×8×8 triad shortlist. The triad table is only an index over independently confirmed family surfaces; it does not invent an unmeasured three-PDS interaction term.

## What CP154 is intended to close

CP154 is deliberately broad enough that, if the response surfaces are healthy, no further dedicated PDS parameter sweep should be necessary. It should answer:

- whether/when Kinetic naturally earns RC2;
- whether Energy's TP-purchased RC2 should be safe, overcharged/Strain-producing, or mature from one into the other;
- the useful Energy Strain Limit region;
- when AMM should unlock RC3/range-1;
- the viable chance, TP, and ammunition/endurance trajectories for all three families;
- whether all three retain distinct, rational roles throughout their TL lifecycles against both GP Missile and Swarmer pressure.

## Deferred deliberately

CP154 does not tune PDS Space/AUX opportunity cost, simultaneous multi-Flight arrival value, cross-target fleet-defense value, the remaining Shield/Armor/AUX lifetime ecosystem, or final Reactor/TP supply. The intended sequence remains:

1. accept/select PDS lifecycle evidence;
2. sweep remaining defense/AUX lifetime viability;
3. perform the final whole-ship Reactor/TP scarcity pass;
4. promote production numerical/mechanics authority only when the integrated evidence supports it.

No CP154 result automatically edits the active Concept, numerical matrix, or production C#.
