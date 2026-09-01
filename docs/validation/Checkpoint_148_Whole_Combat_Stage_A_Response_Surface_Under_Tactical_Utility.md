# Checkpoint 148 — Whole-Combat Stage-A Response Surface Under Tactical Utility Doctrine

## Status

Candidate pending native Windows acceptance. Checkpoint 147 is the native-accepted baseline. CP148 changes no gameplay/component number and no production C#/Godot combat mechanic.

## Purpose

CP144 produced the first 3.425M-trial whole-combat Stage-A surface, but CP145-CP147 subsequently demonstrated that fixed or insufficiently contextual Tactical Power/action allocation materially confounded important outcomes. CP148 therefore reruns the exact same 6,850 Stage-A scenario identities under the native-accepted `cp147_tactical_utility` doctrine before any numerical tuning resumes.

This is the execution checkpoint, not another doctrine-design pass:

- 6,850 exact accepted Stage-A scenario cells;
- 500 deterministic trials/cell;
- 3,425,000 substantive combats;
- 24 jobs by default;
- resumable 256-cell substantive batches;
- no tuning, automatic promotion, or Stage B.

## TP-load telemetry

CP148 adds the requested base-load measurement for every ship/scenario side.

`base_max_installed_tp_demand` is the Tactical Power required to power all installed **normal** combat TP consumers simultaneously. It deliberately excludes every overload mode. The auditable breakdown includes normal main-weapon demand (Energy Standard, normal K firing, normal Missile launch), Active-Low Sensor, full-strength installed ECM/ECCM, installed PDS readiness, Shield Hardener, maximum normal tactical Shield recharge, mainline Armor tactical regeneration, and one Damage-Control attempt. Normal STL movement is zero TP in the accepted model and therefore adds zero.

For each side CP148 records:

- base Reactor TP;
- base maximum installed TP demand;
- mean TP actually allocated per combat side-turn;
- peak TP actually allocated on any turn;
- mean and peak allocated/max-demand fractions;
- max-demand/base-Reactor ratio;
- the component-level max-demand breakdown.

This makes Reactor pressure directly visible without assuming that every installed system should actually be powered in every tactical context.

## Methodological improvement

Strategic/resource Pareto analysis is now **combat-gated**. At each TL, combat-only non-domination is determined first. A combat-dominated system is not eligible to re-enter the strategic frontier solely because it is TP-efficient, robust, or ammunition-efficient. Resource/robustness metrics compare only candidates that first clear the combat gate.

Role response remains separately visible rather than enforcing global numerical equality:

- Kinetic: Armor Pressure;
- Energy: Shield Pressure;
- GP Missile: Balanced Core / no PDS;
- Swarmer: the three PDS-pressure strata.

This preserves specialization while preventing “efficient at losing” from being labeled strategically viable.

## Authoring evidence

The complete 6,850-cell one-trial CP148 tactical-utility smoke completed with 6,850 resolved, 0 execution errors, 0 resolved fights at 25+ turns, 0 turn-cap sentinels, 0 safe stalemates, and 0 non-standoff Open orders. The focused CP148 test suite is 12/12 in authoring and explicitly checks utility-doctrine selection, TP-load arithmetic/no-overload semantics, CP144 historical-path preservation, role reporting, and combat-gated strategic eligibility.

These are pre-handoff findings only. Native Windows remains acceptance authority, and the 500-trial/cell substantive surface—not the one-trial smoke—is the balance evidence.
