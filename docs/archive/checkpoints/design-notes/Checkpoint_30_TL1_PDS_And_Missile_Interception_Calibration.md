# Checkpoint 30 - TL1 PDS and Missile-Interception Calibration

Checkpoint 30 preserves Checkpoint 29e as the accepted stripped-down kinetic/energy/missile no-counter control and adds the first isolated missile-defense subsystem.

The executable layer implements three provisional TL1 point-defense families already present in the numerical baseline:

- Kinetic PDS: 1 Powered Tactical Power, Reaction Capacity 1, 35% equal-TL interception chance, 12 attack packages.
- AMM PDS: 1 Powered Tactical Power, Reaction Capacity 1, 50% equal-TL interception chance, 6 interceptors.
- Energy PDS: 2 Powered Tactical Power, Reaction Capacity 1, 40% equal-TL interception chance, no conventional ammunition.

PDS readiness is committed at Turn Refresh before EvM and main-weapon fire. Individual attempts spend no additional Tactical Power. Kinetic PDS and AMM consume one package per attempt, successful or not. PDS uses self-contained local tracking and does not receive the main Targeting Computer bonus. Own EvM applies the accepted -5 percentage-point firing penalty to PDS.

Standard PDS may act at terminal entry and again immediately before a terminal attack when Reaction Capacity remains. Reaction Capacity is shared across all incoming Missile Flights and both windows in the turn. The baseline value of 1 therefore permits only one total attempt per turn. A successful interception removes the Missile Flight before terminal Guidance and damage.

The 59-variant study covers no-threat readiness, all three PDS families against ordinary missiles at ranges 0/2/4, PDS on kinetic and energy ships, two-launch saturation, chance/Reaction Capacity/ammunition/power/EvM sensitivities, and missile mirrors with PDS on both ships or one ship. Every asymmetric matchup has a reciprocal side swap.

Checkpoint 30 deliberately does not add ECM, ECCM, held main-weapon interception, multiple installed PDS components, player-selectable defensive allocation, component damage, or final balance rulings.

## Acceptance totals

- 627 engine-independent tests.
- 7 accepted deterministic moving-missile scenarios.
- 12 Phase A documents / 54 cases.
- 7 Phase B documents / 36 cases.
- 29 kinetic calibration variants at 10,000 trials each.
- 31 energy calibration variants at 10,000 trials each.
- 48 no-counter weapon-matrix variants at 10,000 trials each.
- 59 PDS/interception variants at 10,000 trials each.
- 46 ScenarioRunner self-tests.

## Release discipline

Checkpoint 30 includes a dedicated static preflight that must pass before and after archive creation. It verifies every environment-independent release contract, including literal content assertions, Concept and workbook markers, exact corpus/test/study counts, normalized active-document state, manifest integrity, clean extraction, hashes, and unauthorized-file rejection. The user's Windows run remains authoritative for compiler and runtime/idempotence validation.
