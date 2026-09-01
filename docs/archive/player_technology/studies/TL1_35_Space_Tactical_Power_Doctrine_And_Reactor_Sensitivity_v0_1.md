# TL1 35-Space Tactical Power Doctrine and Reactor Output Sensitivity v0.1

Checkpoint 62 follows the accepted Checkpoint 61 composed-ship study. It does **not** rebalance TL1 components. It isolates how player-facing Tactical Power allocation doctrine and modest reactor-output sensitivity affect four power-sensitive legal 35-Space builds.

## Questions

1. How much of Checkpoint 61's five-PDS failure is a ship-design consequence versus the automatic defense-first allocation doctrine?
2. How sensitive are the same builds to a one-point lower or higher per-main-reactor Tactical Power output?
3. Does preserving weapon power trade terminal-defense coverage for offense in a coherent, player-understandable way?

## Matrix

Side A uses four legal Checkpoint 60/61 builds: balanced generalist, PDS saturator, dual-main/dual-PDS, and shielded PDS fortress. Each uses Kinetic, Energy, or Missile main armament. Dual-main variants duplicate the same family in both bays. Side B is the balanced-generalist Missile control.

For every build/family lane, Side A is tested with reactor output 4, 5, and 6 TP per operational main reactor and three doctrines:

- **DefenseFirst**: arm as many eligible PDS reactions as possible first. This reproduces the Checkpoint 61 behavior.
- **PrimaryFireFirst**: reserve power for the ready primary main weapon, then arm PDS. A second main is opportunistic.
- **FullVolleyFirst**: reserve power for all ready main weapons, then arm PDS.

This yields 4 × 3 × 3 × 3 = **108 variants**. All nine doctrine/reactor settings within one build/family lane use the same comparison group so the Monte Carlo streams are paired.

## Reactor-output interpretation

The accepted TL1 production reactor remains **5 Tactical Power**. Values 4 and 6 are sensitivity probes, not silent production-stat changes. If a later decision changes the production output, that will be an explicit component/progression change with construction and combinatorial revalidation.

## Weapon-family interpretation

Current-TL performance is not the same thing as total design value. A statistic may be latent when the present opponent does not expose its target layer. In particular, TL1 Energy's APEN advantage is not "worthless" merely because the retained TL1 primary armor currently has Protection 0. Armor-bearing later-TL or specialized opponents can make that advantage consequential. Checkpoint 62 therefore reports family outcomes but does not promote, demote, or retune weapon families from this study alone.

The same principle applies to other contextual capabilities: sensing, EW, range, logistics, penetration, and specialized defense must be judged in scenarios that actually exercise them.

## Isolation limits

Checkpoint 62 keeps the Checkpoint 61 established-Firm-track combat isolation. Sensorless builds are therefore still not globally validated cruiser designs. Sensor acquisition/EW consequences are a later dedicated study.

## Release gates

Blocking gates verify study shape, no trial errors, doctrine/reactor coverage, actual Tactical Power pressure, and observed PDS-allocation sensitivity. **No target win rate is a blocking gate.**
