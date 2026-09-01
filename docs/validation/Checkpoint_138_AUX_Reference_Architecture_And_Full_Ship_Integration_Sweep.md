# Checkpoint 138 - AUX Reference Architecture and Full-Ship Integration Sweep

## Purpose

Checkpoint 138 begins the dedicated Auxiliary/support-system phase after native-accepted CP137. It does **not** tune Reactor Tactical Power and does not promote new AUX numerical values. Its job is to cover the entire current AUX/support catalog with references and role philosophies, re-vet Shield-support concepts against the post-CP135 Shield model, and measure already-executable tactical AUX in deliberately designed, exact-fill contemporary cruisers.

## Accepted baseline

CP137 is the accepted mechanics/research-evidence baseline. Kernel v0.4, penetration-hardening-v1, partial Shield recharge, Hull-only Damage Control, finite Armor regeneration reserves, all weapon values, current Reactor TP, PDS, range/track rules, and mainline Armor remain frozen.

Accepted CP137 native-results ZIP SHA-256: `4d4f3edb3dd583024034b8fb61c00960d5ae25c0987c9f2c4a3fbdd4b08972d5`.

## Layer A - whole AUX reference coverage

`auxiliary_component_catalog_v0_4.json` contains all 35 current catalog components. Every component has:

- at least one reference basis;
- at least one role/reference philosophy;
- an explicit CP138 sweep disposition;
- an explicit flag stating whether CP138 executes it in the primary combat sweep.

Ten reference philosophies span the catalog: Combat Generalist, Information Control, Missile-Defense Escort, Shield Specialist, Damage Resilience, Power Flexibility, Expedition/Survey, Industrial/Logistics, Assault/Relief, and Munition Endurance.

ECM and ECCM are treated as integrated standard AUX-slot systems without duplicating them into the 35-item support catalog. Their current accepted numerical progression is held and revalidated only in full-ship context.

## Shield AUX re-vetting

The Shield redesign invalidates blind carry-forward of old support numbers.

- Shield Battery: legacy restore-3 pre-x2 seed would map to 6 current points and risks recreating full-reset Shield behavior. Reject the legacy number and rederive later.
- Shield Booster: legacy +2 SC pre-x2 seed would map to +4 current SC. Reject direct carry-forward and rederive later.
- Shield Hardener: retain the current executable 1-Space, 1-TP sustained, SA2 nonstacking candidate for CP138 integration testing.
- Particle/charged-beam screen: defer until a tagged specialist threat exists.
- Field Stabilizer: defer until a dedicated high-SPEN specialist lane can distinguish it from Shield Hardener.

## Power AUX boundary

Auxiliary Reactor, APU, Combat Battery, Supercapacitor, SMES, Power Stabilizer, and Thermal Suppression are reference-audited but are **not** activated in the primary combat sweep. They would contaminate the demand baseline before Reactor output itself is tested. CP138 measures credible ship demand first; the following phase may then sweep Reactor TP and power-support choices from evidence rather than from underfilled ships.

## Full-ship reference builds

A CP138 reference ship contains one contemporary Main, one Reactor, STL, FTL, Computer, Sensor, Shield, mainline Armor, and one deliberate tactical AUX role. Any remaining Installation Space is recorded as mission/support fill. Every reference ship therefore exactly fills Hull capacity without pretending that every mission/support component already has a combat bonus.

Executable tactical roles are:

1. Mission Control - no tactical AUX, residual Space is mission/support fill.
2. Electronic Attack - ECM.
3. Counter-EW - ECCM.
4. Information Control - ECM + ECCM.
5. AMM Escort - ECCM + AMM PDS.
6. Energy Screen - ECCM + Energy PDS.
7. Kinetic Screen - ECCM + Kinetic PDS.
8. Shield Guard - ECCM + Shield Hardener, TL3+.
9. Combat Generalist - ECM + ECCM + AMM PDS, plus Shield Hardener at TL3+.

This is role selection, not an install-everything model.

## Study geometry

`cp138_aux_reference_full_ship_integration_study_v0_1.json` generates six diagnostic layers:

- 35 role-baseline contexts;
- 273 role-marginal contexts;
- 105 EW-counterplay contexts;
- 204 PDS-threat contexts;
- 86 Combat-Generalist cross-family contexts;
- 84 Shield-Hardener focus contexts.

Total: **787 logical contexts / 1,574 mover-order variants**. The substantive study uses 2,000 trials/variant for **3,148,000 engagements**. Physical symmetry is a blocking gate; balance outcomes are not.

## Telemetry and interpretation

CP138 records Space composition and Tactical Power availability/use by Sensors, ECM, ECCM, PDS, weapons, Shield recharge, Shield Hardener, Armor regeneration, and Damage Control, plus power shortfalls, track changes, PDS outcomes, Shield/Armor/Hull progression, and role/context results.

The key questions are integration questions: whether ECM/ECCM retain meaningful counterplay under real power competition; whether any PDS family becomes compulsory or ineffective; whether Shield Hardener remains a specialist choice after the Shield redesign; and how much Tactical Power credible full ships actually consume. No 50/50 target exists and no component is automatically promoted or nerfed from this study.
