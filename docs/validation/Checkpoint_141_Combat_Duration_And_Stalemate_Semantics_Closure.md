# Checkpoint 141 — Combat Duration and Stalemate Semantics Closure

## Status

Candidate pending native Windows acceptance. CP140 CR1 is the native-accepted Stage-A integration baseline. CP141 changes no production C#/Godot mechanics and promotes no numerical values.

## Purpose

CP141 closes the gameplay-duration measurement semantics required before the substantive v22C Stage-A combat study.

The design rule is gameplay-first:

- combat is **not** made acceptable by extending the simulation until something eventually dies;
- 60 turns is a hard runaway/stalemate sentinel, not a desirable fight length;
- resolved combat at **25 or more turns** is explicitly retained as a gameplay-duration concern;
- genuine no-path-to-victory states may terminate as stalemates, but temporary range, track, TP, recharge, repair, or tactical conditions are never sufficient by themselves to auto-declare a stalemate.

CP141 therefore standardizes every Stage-A stratum to the same 60-turn sentinel. CP140's `RECOVERY_ATTRITION` 90-turn exception is removed from the CP141 measurement binding; the frozen CP140 source study remains unchanged for provenance.

## Conservative automatic stalemate rule

The canonical Python research kernel gains one deliberately narrow early-termination rule:

> `STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION` occurs only when both installed primary weapons have permanently exhausted finite primary ammunition **and** no already-launched missile Flight remains live.

Energy weapons never satisfy finite-ammunition exhaustion. One exhausted ship facing an opponent with a live offensive path does not create a stalemate. Pending missile Flights prevent early termination until they hit, are intercepted, or exhaust their travel range.

No recovery loop, EW deadlock, TP shortfall, range condition, or slow attritional state is automatically terminated by CP141. Those remain diagnostics because treating them as provable stalemates could conceal a mechanics or tactical-policy defect.

## Termination causes

Full-map research results now carry explicit termination causes:

- `SIDE_A_DESTROYED`
- `SIDE_B_DESTROYED`
- `MUTUAL_DESTRUCTION`
- `STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION`
- `TURN_CAP_SENTINEL`
- `ERROR`

The existing winner/unresolved fields remain backward-compatible.

## Turn-cap diagnostics

For every `TURN_CAP_SENTINEL`, CP141 records a transparent dominant diagnostic signal. This is a descriptive partition, not an automatic termination rule or numerical tuning instruction. The priority is:

1. `NO_OFFENSIVE_ACTION`
2. `OFFENSE_WITHOUT_DAMAGE_CONNECTION`
3. `NO_RECENT_WEAPON_DEMAND`
4. `ACTIVE_ATTRITION_AT_CAP`
5. `DEFENSIVE_RECOVERY_LOOP`
6. `TRACK_DEADLOCK`
7. `TP_PRESSURE_DEADLOCK`
8. `NO_NET_STRUCTURAL_PROGRESS`

`DEFENSIVE_RECOVERY_LOOP` requires no net Hull+Armor structural progress over the final ten turns and total recorded recovery at least 75% of gross recorded damage. The 75% boundary is diagnostic only and its raw components are persisted so later analysis need not depend on the category label.

## Duration viability outputs

CP141 makes combat duration a first-class response dimension. For overall, TL, combat-stratum, ordered weapon-pair, and resource-environment groups it records:

- resolved count;
- safe stalemate count;
- turn-cap sentinel count;
- resolved-under-25 and resolved-at-25-or-more counts;
- resolution by turns 10, 15, and 20; and
- median, P75, P90, and P95 resolved-combat turns.

These measures will be carried into the later substantive Stage-A viability analysis alongside combat performance, TP pressure, counter sensitivity, regret/Pareto participation, and TL evolution.

## Authoring result

The exact 8,220-scenario one-trial Stage-A matrix completed with zero execution errors under the common 60-turn sentinel.

Authoring observations are diagnostics only, not final balance rates:

- 7,382 scenarios resolved by destruction/mutual destruction;
- 5,979 resolved before turn 25;
- 1,403 resolved at turn 25 or later (19.0% of resolved one-trial cases);
- 838 reached the 60-turn sentinel;
- no naturally occurring mutual-primary-ammunition exhaustion stalemate appeared in this one-trial matrix;
- 2,241 scenarios were therefore a one-trial gameplay-duration concern (`resolved >=25` or turn-cap), 27.3% of the matrix;
- 1,330 of the 1,403 long-resolved cases were Missile-vs-Missile matchups;
- the 838 turn-cap diagnostics partitioned as 599 defensive-recovery loops, 109 no-recent-weapon-demand, 85 active attrition, 30 no offensive action, 7 no-net-structural-progress, 6 TP-pressure deadlock, and 2 offense-without-damage-connection.

The recovery signal is overwhelmingly Shield-driven in the cap-hit set: recorded Shield base + tactical restoration dominates Armor regeneration and Hull repair. This is a response-surface diagnostic to investigate with substantive evidence; CP141 changes no Shield, weapon, Reactor, PDS, or other numerical value.

CP140 had allowed `RECOVERY_ATTRITION` to continue to turn 90. In the accepted CP140 smoke, all 59 cases that were still unresolved at turn 60 remained unresolved at turn 90; **the extra 30 turns produced zero additional resolutions**. CP141 therefore loses no successful outcome by returning that stratum to the common 60-turn sentinel.

## Scope boundary

CP141 executes 8,220 one-trial duration/stalemate closure cases only. It performs **zero substantive combat/balance trials** and cannot promote numerical values. The planned multi-million-trial Stage A remains a later checkpoint.
