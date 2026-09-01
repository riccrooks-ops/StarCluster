# Checkpoint 85 - TL2 Armor AP/AI and Shield Integration Permutation Suite

## Purpose

Checkpoint 85 carries the accepted CP83 reactor and CP84 shield results forward and tests the next defensive progression dimension without bundling unrelated improvements. Early Practical Fusion remains **6 Operational TP / 6 Space** and Shield Capacity **3 / 3 Space** remains a validated TL2 working candidate. CP85 adds Armor Protection (AP) and Armor Integrity (AI) as independent standing-suite axes.

## Scope

This checkpoint changes ScenarioRunner calibration infrastructure, standing-suite definitions, Technology Architecture Matrix/Concept documentation, and checkpoint tooling. It does **not** change production StarCluster.Core or StarCluster.Game combat mechanics or production TL2 component data.

The TL1 primary-armor reference is **AP 0 / AI 4** at zero additional Installation Space. CP85 tests three Side-A alternatives: **AP 0 / AI 5**, **AP 1 / AI 4**, and **AP 1 / AI 5**. The combined AP1/AI5 package is an upper/integration sensitivity, not an assumed bundle. Side A is crossed against Shield Capacity 2 and the CP84-validated Shield Capacity 3 working candidate. Side A uses the CP83-validated 6-TP reactor; Side B remains Reactor 5, Shield 2, AP0/AI4.

Weapon penetration remains fixed at the accepted reference: Kinetic APEN 0, Energy APEN 1, Missile APEN 2. This deliberately tests whether AP1 creates family-specific counterplay instead of behaving like generic extra hit points.

## Study matrix

`tl2-itc11-armor-ap-ai-shield-integration-permutations` contains 288 variants:

- 2 Side-A weapon families: Kinetic, Energy.
- 3 opponent families: Kinetic, Energy, Missile.
- 3 geometry/order contexts: fixed range 3, dynamic Side A first, dynamic Side B first.
- 2 information-control environments: clean Firm; DR1 + reactive ECCM1 against ECM2.
- 2 Side-A shield capacities: 2, 3.
- 4 Side-A armor packages: AP0/AI4, AP0/AI5, AP1/AI4, AP1/AI5.

Each of 18 combat/geometry comparison groups therefore contains 16 paired environment/shield/armor permutations.

## Diagnostics and review questions

The specialized CP85 review reports expose conditional win share, duration, shield absorption/recharge, armor damage prevention, AI damage, AP damage, hull damage, power pressure, PDS/direct-fire/missile activity, and paired deltas for AI5, AP1, combined AP1/AI5, AP-AI interaction, and Shield3-vs-Shield2.

Human review should answer: whether AI5 is a useful broad durability step; whether AP1 is too narrow or appropriately matchup-specific under APEN0/1/2; whether AP1+AI5 compounds excessively; whether Shield3 plus advanced armor creates unhealthy layered-defense multiplication; and whether combat pacing remains acceptable.

## Acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85\apply_checkpoint_85.ps1 -RepositoryOnly
```

Normal native acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85\apply_checkpoint_85.ps1 -Jobs 24
```

Optional Deep Calibration:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85\apply_checkpoint_85.ps1 -Jobs 24 -DeepCalibration
```

## Promotion boundary

A successful run does not automatically promote an Armor value. AP0/AI5 and AP1/AI4 are independent candidates; AP1/AI5 is an upper/integration sensitivity unless evidence later supports a bundle. Shield3 and Reactor6 remain validated working candidates, not production component data.
