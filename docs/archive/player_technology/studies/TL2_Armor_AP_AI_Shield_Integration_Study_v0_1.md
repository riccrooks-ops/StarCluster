# TL2 Armor AP/AI and Shield Integration Study v0.1

## Purpose

Checkpoint 85 extends the standing Technology Integration Permutation Suite with **primary Armor Integrity (AI)** and **Armor Protection (AP)** as separate progression dimensions. It asks which kind of early TL2 armor maturation is useful under the accepted layered-damage rules, and whether that armor compounds reasonably with the Checkpoint 84 Shield Capacity 3 working candidate.

This is a sensitivity and attribution study. It does **not** promote production armor data automatically.

## Accepted inputs held constant

- TL1 primary armor reference: **AP 0 / AI 4**, hull-integrated at **0 additional Installation Space**.
- CP83 TL2 Power/Reactor working candidate on Side A: **6 Operational TP / 6 Space**. Side B remains at the TL1 5-TP reference.
- CP84 TL2 Shield working candidate: **Capacity 3 / 3 Space**. Shield 2 remains the paired TL1 control.
- Shield Base Recharge 1, tactical recharge 1 Shield per TP, tactical recharge cap 2 TP, and Shield Armor 0 remain unchanged.
- TL2 information-control working values remain +12 pp Tactical Computer targeting, Sensor DR1, ECM/ECCM ceiling 2 at 1 TP/rating, with the established Firm-reference and DR1 + reactive-ECCM1 environments.
- Current weapon packets and penetration are unchanged. The accepted reference APEN values are **Kinetic 0, Energy 1, Missile 2**.
- No Sensor/EW overload, STL overload, Evasive Compensation, new armor repair rule, ablative behavior, armor footprint change, shield hardening, or degraded-fire production assignment is introduced.

## Armor packages under test

| Package | AP | AI | Role |
|---|---:|---:|---|
| TL1 control | 0 | 4 | Accepted reference |
| Integrity-only | 0 | 5 | Primary TL2 sensitivity: one additional sacrificial armor point |
| Protection-only | 1 | 4 | Primary TL2 sensitivity: persistent flat reduction where APEN does not cancel it |
| Combined | 1 | 5 | Upper/integration sensitivity; **not** an assumed TL2 bundle |

AP and AI are intentionally separated. A higher-TL armor family need not improve both at the same level.

## Why APEN makes this study important

Under the current resolver, effective Armor Protection is reduced by the attack package's APEN before damage reaches Armor Integrity. That makes AP1 qualitatively different from AI5:

- against **Kinetic APEN 0**, AP1 remains effective and can reduce armor-facing damage;
- against **Energy APEN 1**, the standard AP1 sensitivity is cancelled;
- against **Missile APEN 2**, the standard AP1 sensitivity is also cancelled.

Those relationships are expected counterplay, not stochastic pass/fail targets. The study is designed to measure whether they create a healthy weapon-family identity and whether AI5 supplies a broader but less specialized alternative.

## Activated factorial

The CP85 slice uses:

- 2 Side-A direct-fire families: Kinetic and Energy;
- 3 opponent families: Kinetic, Energy, Missile;
- 3 geometry/order contexts: fixed range 3, dynamic Side A first, dynamic Side B first;
- 2 information-control environments: clean Firm reference and contemporary DR1 + reactive ECCM1 against ECM2;
- 2 Side-A Shield capacities: 2 and 3;
- 4 Side-A armor packages: AP0/AI4, AP0/AI5, AP1/AI4, AP1/AI5.

That is **2 x 3 x 3 x 2 x 2 x 4 = 288 variants**. Each 16-variant combat/geometry comparison group shares common random streams across the environment/shield/armor permutations where practical.

Side A is held at Reactor 6; Side B remains Reactor 5, Shield 2, AP0/AI4. This prevents CP85 from re-running the CP83 reactor sensitivity while still testing armor inside the accepted TL2 power envelope.

## Primary review questions

1. How much does **AI5 alone** improve survivability, hull exposure, and conditional outcome across each incoming weapon family?
2. How much does **AP1 alone** improve those same outcomes, and does the effect follow the expected APEN 0/1/2 counterplay?
3. Does **AP1/AI5 combined** behave approximately additively, show diminishing returns, or create an undesirable defensive breakpoint?
4. Does Shield 3 amplify either armor property beyond a healthy layered-defense interaction?
5. Do larger defensive packages materially extend combat duration or unresolved outcomes?
6. Does armor progression preserve meaningful distinctions among Energy, Kinetic, and Missile attack packages rather than producing a universal best-in-slot defense?

## Telemetry and reports

The study uses the existing authoritative layer telemetry and emits CP85 review files containing conditional outcomes, turn count, Shield absorption, Armor damage prevented, AI damage, AP damage, Hull damage, Tactical Shield recharge power, insufficient-power prevention, PDS activity, direct shots, and missile launches.

The paired-delta report includes:

- AI5 minus AP0/AI4 control;
- AP1 minus AP0/AI4 control;
- AP1/AI5 minus AP0/AI4 control;
- a win-rate AP/AI interaction term;
- Shield 3 minus Shield 2 for every armor package.

## Promotion boundary

Release gates validate configuration, isolation, consumer routing, and deterministic architecture invariants only. Statistical outcomes remain human-review evidence.

A successful native run does **not** automatically promote AP1, AI5, or AP1/AI5. After the run, promote only the armor property or package supported by the evidence. If one axis is healthy and the other is not, keep them separated rather than forcing a combined TL2 armor upgrade.
