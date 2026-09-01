# Checkpoint 38 - Integrated Cross-Family Combat and Tactical Order Policies

## Purpose

Checkpoint 38 reconnects the accepted weapon-family and changing-range studies to the internal-damage model completed in Checkpoints 36b and 37. It also establishes a production-facing tactical-decision seam rather than embedding movement choices inside individual calibration scenarios.

## Architectural rule

Scenarios and AI policies may request tactical intent. Only shared combat services may convert that intent into legal movement and range changes.

`ITacticalOrderPolicy` receives an immutable `TacticalDecisionContext` and returns a `TacticalOrderPlan`. `RangeOrderResolver` then resolves both ships' plans simultaneously from actual STL condition. Policies do not mutate ships, range, missiles, Tactical Power, or component state.

## Initial orders and policies

The shared range order set is Hold, Close, Open, and Maintain Preferred Range. A plan may name a desired separation so the resolver can throttle movement before ships overshoot the intended band. Maintain Preferred Range counters only the opponent's actual resolved movement, including desired-range throttling.

`ScriptedTacticalOrderPolicy` is the deterministic fixture implementation. `PreferredRangeTacticalPolicy` is the first reusable decision routine for later enemy AI work. Its range bands are provisional calibration doctrine:

- kinetic: prefer 1-2 hexes, maximum useful range 6;
- energy: prefer 3-4 hexes, maximum useful range 6;
- missile: prefer 4-6 hexes, maximum useful range 6.

## Movement and missile geometry

TL1 STL movement is 4 hexes when Operational, 2 when Degraded, and 0 when Disabled or Destroyed. Drive damage suffered after movement does not retroactively cancel that turn's movement. The following turn's decision and Immobile Target snapshot see the new condition.

A launched missile owns its position, cumulative distance traveled, and maximum travel budget. Later launcher movement does not pull the missile. Target movement causes a new route projection from the missile's actual position while retaining all distance already traveled.

## Integrated study

The 90-variant `tl1-itc01-cross-family-dynamic-range` study covers all nine ordered kinetic, energy, and missile pairings. Fixed Range 2, Fixed Range 4, and Scripted Pursuit run with Damage Control off/on. Preferred Range adds ordinary and Protected Compartmentation placement with Damage Control off/on.

Every ship uses 33 1/3% internal critical density and the normal TL1 three-kit Damage Control profile. The study includes layered defenses, component-conditioned weapon/recycle/power/STL/PDS/Evasive performance, simultaneous direct fire, independent missile flight, PDS, mission kills, and following-turn Immobile Target accuracy.

The historical weapon matrix and scripted range-control study remain unchanged as isolated arithmetic and geometry regression controls.
