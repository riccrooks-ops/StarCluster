# Checkpoint 151 — Offensive/Defensive Point-Scale ×2 Multivariate Response

## Purpose

CP151 uses native-accepted CP150 as its base and changes the **research scale**, not the source Technology Numerical Matrix. It first proves that doubling offensive/defensive point quantities is mechanically equivalent, then uses the additional integer resolution to execute a broad multivariate response surface.

The player-facing motivation is simple: values such as old DAM 7 and 8 become new 14 and 16, exposing the previously unavailable midpoint 15 without introducing half-point player values.

## Conversion boundary

The strict ×2 control doubles only the established point-domain quantities:

- Kinetic, Energy, GP Missile, and Swarmer damage/yield;
- Hull capacity;
- Shield capacity;
- Armor capacity;
- Shield recharge point quantities for the exact-equivalence arm;
- Armor repair point quantities/reserve for the exact-equivalence arm;
- executable alternate Armor capacity such as A_b1 Crystalline Armor.

It does **not** rescale ACC, DEF, RES, APEN, SPEN, TP, range, Space, interception probabilities, reaction capacity, sensor/EW ratings, or ammunition counts.

Hull Damage Control remains outside the approved rescaling scope. For the strict equivalence audit it is disabled in both arms so an intentionally unscaled Hull-repair magnitude cannot contaminate the homogeneity test.

## Research center and fine sweep

Kinetic begins from CP150's supported damage maturation, old scale:

`5 / 5 / 6 / 7 / 7 / 8 / 8 / 10 / 10`

and therefore new-scale centers:

`10 / 10 / 12 / 14 / 14 / 16 / 16 / 20 / 20`.

Every active point factor is sampled at center −1 / center / center +1. This includes weapon damage, Hull/Shield/Armor capacity, Shield recharge, and (TL6+) Armor repair. Shield recharge and Armor repair therefore explicitly test 1 / 2 / 3 around the exact old-scale-equivalent center of 2.

K APEN and Energy SPEN are separate ±1 response dimensions. They are **not doubled**. Missile APEN/SPEN remain zero. K SPEN remains zero. No penetration family identity is invented.

Swarmer packet damage is a special provenance case: the accepted packet yield is fractional. The strict equivalence arm uses the exact doubled float. The substantive research center rounds the doubled value to the nearest integer and samples ±1 around that integer so the new research scale can move toward integer player-facing values without pretending the rounding itself was an equivalence transformation.

## Multivariate design

CP151 uses an OA(243), three-level, strength-2 core at every TL. Each active factor is balanced over −1/0/+1 and every active factor pair contains all nine 3×3 combinations equally. Unique pure axial points not already present in the OA are added explicitly; exact duplicates are not rerun.

Candidate counts:

- TL1: 261
- TL2–TL5: 263 each
- TL6–TL9: 265 each
- total: 2,373 TL-candidates

The candidates cross the exact accepted 6,850 Stage-A contexts at their TL. The substantive study contains 1,807,050 candidate-context cells × 25 matched trials = **45,176,250 combats**.

RepositoryOnly also executes:

- all 6,850 same-seed paired strict-equivalence identities (13,700 combat executions); and
- a 50-context-per-TL panel for every candidate, totaling **118,650 smoke combats**.

## AUX boundary

Only existing executable point-valued mechanics are transformed or swept. CP151 does not invent numeric magnitudes or Stage-A installation behavior for unresolved Shield Booster, Shield Power Stabilizer, Energized Armor Controller, or other catalog/proxy AUX concepts. Shield Hardener remains unchanged because its effect is dimensionless DEF percentage.

## Selection doctrine

CP151 does not automatically promote any candidate. The accepted technology-progression principle remains: an intrinsic technological characteristic should not regress with increasing TL unless an explicit documented tradeoff justifies the regression. CP151 deliberately leaves ACC/range unchanged so the point-scale experiment cannot hide or pre-answer that later ladder-selection constraint.

## Native acceptance intent

CP151 is a research checkpoint. It must preserve accepted CP150 source authority, the CP147 tactical-utility doctrine, the DEF/RES model, and all source numerical files. Native Windows acceptance establishes execution/reproducibility of the ×2 equivalence and the full multivariate surface; numerical promotion remains a later decision based on the evidence.
