# Campaign-Weighted Weapon Integration Study Architecture v0.1

**Checkpoint:** 119  
**Status:** Working-candidate same-TL integration study; no automatic numerical promotion  
**Accepted baseline:** Checkpoint 118 simplified weapon progression

## Purpose

CP119 stops broad characteristic-space exploration and asks whether a deliberately small working weapon set remains coherent when Energy, Kinetic, GP Missile, and Swarmer Missile builds are returned to the same legal exact-fill combat ecology.

The study answers four bounded questions:

1. Does the simple GP Missile yield ladder remain plausible when compared with the other weapon families rather than only with Missile controls?
2. Does a TL2-introduced two-packet Swarmer retain a recognizable lifecycle and PDS-saturation niche without becoming a universal Missile choice?
3. Does a restrained +5 ACC automatic Kinetic smart-projectile step improve Kinetic performance without requiring a normal ammunition selector or erasing family identity?
4. Do these candidates behave coherently across the campaign-weighted TL range without allowing TL8-TL9 endpoint behavior to dictate whole-game complexity?

## Evidence weighting

| Band | TLs | Role in inference |
|---|---|---|
| Primary campaign | TL1-TL6 | Drives candidate review and future narrowing. |
| Advanced | TL7 | Important late-campaign validation. |
| Endpoint/stress | TL8-TL9 | Detects collapse/runaway interactions; does not by itself drive whole-game mechanics. |

CP119 has 720 primary variants, 144 advanced variants, and 288 endpoint/stress variants. Primary evidence therefore exceeds the two secondary bands combined.

## Working weapon set

### Energy

Energy uses the native CP109/CP117 same-TL weapon profile and existing output-mode doctrine. CP119 does not change or tune Energy; it is a shared-ecology reference.

### Kinetic

Kinetic keeps the current same-TL projectile at TL1-TL3. At TL4+, the only working integration candidate is **+5 ACC** from automatic smart/maneuvering projectile maturation. The candidate changes no DAM, SPEN, APEN, packet count, or ammunition-selection rule.

### GP Missile

GP Missile maturation is yield-only in CP119:

- TL1-TL2: current D5 GP reference;
- TL3-TL4: working D6 mature-fission candidate;
- TL5-TL6: working D7 Fusion candidate;
- TL7-TL9: working D8 Antimatter candidate.

All explicit working GP profiles retain the diagnostic SP1/AP2 baseline and one packet. CP119 does not promote SP1/AP2 as final GP penetration authority.

### Swarmer Missile

The working Swarmer branch starts at **TL2** and remains one Flight, one terminal roll, one ammunition expenditure, and one existing PDS reaction sequence. Every CP119 Swarmer has exactly two internal packets:

- TL2-TL3: 2 x D2, +10 guidance, -10 pp PDS interception;
- TL4-TL5: 2 x D3, +10 guidance, -10 pp PDS interception;
- TL6-TL9: 2 x D4, +15 guidance, -15 pp PDS interception.

The TL8-TL9 profile is an endpoint carry-forward, not an assertion that Swarmer must remain competitive indefinitely.

## Shared legal target ecology

Every target fixture is a legal exact-fill same-TL primary build:

- Energy balanced;
- Energy defense specialist;
- Kinetic balanced;
- Kinetic EW specialist;
- Missile balanced;
- Missile defense specialist.

No controlled diagnostic fixture contributes to CP119. This intentionally trades some mechanistic isolation for a cleaner integration/ecology confirmation after CP118 already isolated the characteristic axes.

## Variant construction

- 108 exact-fill underlying builds.
- 1,152 mirrored variants.
  - 576 Missile variants.
  - 360 Kinetic variants.
  - 216 Energy reference variants.
- 50 authoring trials per variant = 57,600 checked-in diagnostic engagements.
- 2,000 native trials per variant = 2,304,000 substantive engagements.

Movement order remains mirrored. Outcome thresholds are information only; no win-rate or ranking result is a blocking gate.

## Blocking gates

Only mechanics/integration failures block acceptance:

- invalid study/schema or KISS contract;
- Python self-test or parity failure;
- CP114/CP115a/CP116/CP118 regression smoke failure;
- trial errors;
- non-exact-fill underlying builds;
- missing Energy/Kinetic/Missile activity telemetry;
- missing Swarmer/PDS telemetry;
- missing primary/advanced/endpoint TL coverage;
- repository, manifest, provenance, or prepackage-hygiene failure.

## Interpretation guardrails

- Weapon families are intentionally asymmetric. Equal all-target win rates are not a design objective.
- CP119 working profiles are integration candidates, not production promotion.
- TL1-TL6 drives conclusions. TL7 is advanced validation; TL8-TL9 is endpoint/stress evidence.
- Internal critical/subsystem damage remains outside the research consumer.
- Known movement-order sensitivity is reported but is not corrected by weapon-stat changes in this checkpoint.
