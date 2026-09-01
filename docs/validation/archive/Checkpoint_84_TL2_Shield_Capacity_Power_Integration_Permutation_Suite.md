# Checkpoint 84 — TL2 Shield Capacity and Power Integration Permutation Suite

## Purpose

Checkpoint 84 folds the accepted CP83 Power/Reactor result into current documentation and immediately spends the next acceptance cycle on a substantive defensive-progression question. It carries **Early Practical Fusion = 6 Operational TP / 6 Space** as a validated TL2 working candidate while testing Shield Capacity 2/3/4 across Reactor 5/6.

## Scope

This checkpoint changes ScenarioRunner calibration infrastructure, standing-suite definitions, Technology Architecture Matrix/Concept documentation, and checkpoint tooling. It does **not** change production StarCluster.Core or StarCluster.Game combat mechanics, production TL2 component data, the missile Firm-terminal rule, or the accepted armor model.

The Shield experiment changes only Side-A pristine Shield Capacity. Shield recharge values, Shield Armor/hardening, shield-generator Installation Space, condition behavior, overload, sustained maintenance, and prerequisites are held. Side B remains at the TL1 Shield 2 / Reactor 5 reference.

## Study matrix

`tl2-itc10-shield-capacity-power-integration-permutations` contains 216 variants:

- 2 Side-A weapon families: Kinetic, Energy.
- 3 opponent families: Kinetic, Energy, Missile.
- 3 geometry/order contexts: fixed range 3, dynamic Side A first, dynamic Side B first.
- 2 information-control environments: clean Firm; DR1 + reactive ECCM1 against ECM2.
- 3 Side-A shield capacities: 2, 3, 4.
- 2 Side-A reactor outputs: 5, 6.

Each combat geometry shares a `comparisonGroup`; the twelve environment/shield/reactor permutations therefore use common random streams where the runner supports them.

## New diagnostics

CP84 routes through the existing stateful turn-power planner so ordinary tactical shield recharge can compete with planned offense/PDS and the later reactive-ECCM decision. The integrated summary adds:

- mean Side-A/B tactical shield recharge opportunities;
- mean Side-A/B Tactical Power spent on tactical shield recharge;
- mean Side-A/B tactical recharge opportunities denied by prospective power reservation.

The specialized review reports emit these values along with paired Shield-capacity and Reactor deltas.

## Acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-84\apply_checkpoint_84.ps1 -RepositoryOnly
```

Normal native acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-84\apply_checkpoint_84.ps1 -Jobs 24
```

Optional Deep Calibration:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-84\apply_checkpoint_84.ps1 -Jobs 24 -DeepCalibration
```

## Review boundary

A successful run does not automatically promote Shield 3 or Shield 4. The results should be reviewed for discrete damage breakpoints, survivability/pacing, Tactical Power competition, PDS/offense/ECCM opportunity costs, and interaction with the 6-TP reactor. Shield 3 is the intended primary candidate; Shield 4 is an upper sensitivity. Armor AP/AI progression remains a separate later experiment.
