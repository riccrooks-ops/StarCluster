# TL1 Main-Weapon Power and Interception Correction Plan v0.1

## Purpose

Checkpoint 33 corrects four TL1 Tactical Power boundaries exposed by the Checkpoint 32 reactor-envelope assessment. It does not add adaptive tactics. The study continues to use fixed doctrines to measure hard affordability, ordering, ammunition, and overload edges.

## Accepted corrections

- The TL1 Kinetic Cannon spends 1 Tactical Power per attack for loading, stabilization, recoil control, cooling, and other internal firing systems.
- The TL1 Missile Launcher retains zero launch Tactical Power. The Missile Flight carries its own propulsion, guidance, and terminal power while the launcher consumes one Ready Flight.
- Kinetic Held Interception earmarks 1 TP. It becomes Spent only when the shot triggers and releases unused when the window closes; the offensive cycle remains reserved either way.
- Held Main resolves before PDS because the main weapon engages at the longer interception distance. A successful held shot preserves finite PDS ammunition; a surviving Flight proceeds to PDS.
- TL1 Shield overcapacity spends 1 TP and adds 1 temporary Shield Point per safe activation. With the existing two-activation safe limit, the static fixture can add at most 2 temporary Shield Points before returning to ordinary operation.
- The early Auxiliary Reactor comparison contributes +1 TP while Operational and 0 TP while Degraded, Disabled, or Destroyed. Higher-TL systems may later provide larger or degraded output.
- One installed main Missile Launcher still launches at most one Flight per turn, and TL1 PDS Reaction Capacity remains 1.

## Focused evaluation matrix

The executable study contains 294 variants at 10,000 trials each:

| Category | Variants | Purpose |
|---|---:|---|
| Accepted controls | 6 | Rebaseline Kinetic, Energy, and Missile mirrors under the corrected Kinetic cost. |
| Reactor sweep | 40 | Five offense packages at renewable outputs 3-6 with reciprocal swaps. |
| Single consumers | 64 | Eight individual power-demand packages at outputs 3-6. |
| Layered sweep | 64 | Eight multi-system packages at outputs 3-6. |
| Power-source overlays | 60 | Reassess Capacitors, Combat Batteries, +1 Auxiliary Reactor, and Reactor overload. |
| Overload boundaries | 30 | Reassess Shield overcapacity and retain other static overload edges. |
| Held Interception | 30 | Reassess Kinetic cost, Held-before-PDS order, and saturation. |

The previously accepted 0-2 and 7-8 reactor boundaries remain historical controls. Checkpoint 33 concentrates repeated sweeps on 3-6 TP because those outputs can change the provisional TL1 Reactor decision.

## Required interpretation

- A green run proves contract fidelity and reciprocal determinism, not final balance.
- Kinetic should remain cheaper than standard Energy but should no longer receive an entirely free offensive cycle.
- Missile launch remains power-light but pays through finite stores, delayed impact, interception exposure, guidance, range, and pursuit.
- An early Auxiliary Reactor should cross one nearby threshold rather than erase the power-allocation problem.
- Held Main should conserve PDS ammunition only by sacrificing the main offensive cycle.
- Shield overcapacity should provide a meaningful emergency buffer without supplying several ordinary hits for one point.

## Deferred

- Adaptive power-allocation AI and realistic tactical doctrines.
- Movement-dependent Held Interception range windows beyond the ordering contract.
- Tractor Beam and STL Drive overload valuation.
- Higher-TL Auxiliary Reactor progression.
- Multi-launcher and multi-weapon hull balance.
