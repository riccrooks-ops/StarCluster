# TL1 35-Space Operational Sensor, Acquisition, and EW Study v0.1

Checkpoint 63 restores operational target-acquisition consequences to the accepted TL1 35-Installation-Space composed ships. Checkpoints 61 and 62 deliberately assumed an established Firm track so construction and Tactical Power doctrine could be isolated first. This pass asks what happens when Side A must obtain and maintain a Firm solution with the retained TL1 sensor envelope.

## Fixed controls

- Production reactor output remains **5 Tactical Power per operational main reactor**.
- Both sides use **FullVolleyFirst** so avoidable weapon starvation does not contaminate the sensor comparison.
- Side B is always the accepted balanced-generalist Missile opponent and retains an **EstablishedFirm** track. Only Side A acquisition changes.
- Initial range is 4 hexes with `OpponentAwareRange` movement and `ComponentFirstReserveOne` Damage Control.
- No target win rate is a release gate.

## Sensor architecture

Every cruiser retains core passive/navigation sensing. The 3-Space `active_sensor` installation is the optional powered suite; omitting it does **not** make a ship blind.

The study reuses the accepted TL1 numerical baseline:

| Mode | Power | Firm | Approximate |
|---|---:|---:|---:|
| Core passive | 0 TP | 3 | 5 |
| Active level 1 | 1 TP | 5 | 7 |
| Active level 2 | 2 TP | 6 | 9 |

Power changes range, not intrinsic hit probability. A Firm solution authorizes the normal weapon attack; it is not an additional accuracy bonus. This study conservatively requires Firm authorization for all three main-weapon families. Missile-specific Approximate-cue, datalink, onboard-sensor, and seeker exceptions remain separate missile-guidance questions and are not silently assumed here.

## Operational power ordering

For Checkpoint 63 operational lanes, movement resolves first. The automatic sensor policy then selects the minimum useful active setting for the resulting range, subject to available Tactical Power. It protects the ready **full main-weapon volley** before committing sensor power. PDS readiness is allocated afterward from the remaining pool.

This ordering intentionally asks whether the optional sensor can support the intended offensive package without reintroducing Checkpoint 61's self-sabotaging power doctrine. It is a diagnostic policy, not a final player-UI restriction.

## Four paired acquisition regimes

Each build/family lane uses one shared `comparisonGroup`, so all four regimes use paired random streams.

1. **established-firm-control** — reproduces the Checkpoint 61/62 combat isolation; no sensor power is committed and Side A always has Firm authorization.
2. **operational-passive-clear** — Side A uses only core passive sensing, even if an active suite is installed.
3. **operational-auto-active-clear** — an installed active suite may commit 1 or 2 TP automatically when passive Firm is insufficient.
4. **operational-auto-active-ew1** — the same automatic policy operates under one point of net EW range pressure.

The EW1 lane is an abstract stress input. It represents an opposing ECM advantage after any cancellation, reducing the effective Side-A Firm/Approximate ranges by one hex. It does not price a specific ECM/ECCM component, consume a separate EW installation's power, or apply an additional hit penalty.

## Matrix

The study covers all six accepted Checkpoint 60 legal packages as Side A:

- balanced generalist;
- dual-main striker;
- dual-reactor power core;
- five-PDS saturator;
- dual-main / dual-PDS;
- shielded three-PDS fortress.

Each uses Kinetic, Energy, and Missile main armament. Dual-main builds use two copies of the same family in this isolation pass. Six builds x three families x four acquisition regimes = **72 variants** / **720,000 default trials**.

## Mechanical sanity gates

Release gates verify study shape and implementation behavior, not balance outcomes:

- established-Firm controls must record zero Side-A sensor power and zero track-denial events;
- active-sensor-equipped AutoActive cases must actually commit sensor power somewhere in the matrix;
- ships without the optional active suite must still record passive Firm/Approximate observations;
- because paired randomness is shared, `AutoActive` must collapse exactly to `PassiveOnly` for builds that have no active suite;
- the EW1 lane must measurably pressure track quality somewhere;
- Side B must remain an established-Firm control;
- no target win share is blocking.

## Interpretation boundaries

A sensorless odd build that looked excellent under Checkpoint 61/62 established-Firm isolation paid no acquisition cost there. Checkpoint 63 measures that missing consequence. Conversely, an active sensor's value is contextual: if the fight remains inside passive Firm range, the 3-Space suite may correctly contribute little in that particular engagement.

The same contextual-value rule continues to apply to weapons. Energy APEN is not worthless because the current TL1 AP0 armor control underuses it. Later armor-bearing opposition must exercise that property before Energy is promoted, demoted, or retuned.

Checkpoint 63 is therefore a diagnostic of the operational acquisition envelope, not a license to force all designs toward one win percentage or to erase specialized technology whose advantage belongs to another matchup.
