# Star Cluster Canonical TL1-TL9 Numerical Technology Matrix v0.2

**Status:** canonical x2 point-domain migration of the CP109 v0.1 candidate; no balance change is intended.

CP122 changes the integer ruler only. One legacy damage/defense point equals two canonical points. Non-point quantities such as Space, Tactical Power, range, movement, accuracy/guidance percentages, ammunition, fuel, PDS Reaction Capacity, Sensor/EW ratings, and TL are unchanged.

A successful production Damage Control Hull repair intentionally remains **1 canonical Hull point per Repair Kit**. Exact migration parity uses an artificial 2-Hull repair only inside the CP122 parity suite. Critical/H-X cadence migration is deferred until the critical system is fully implemented.

## Point-domain progression

| TL | Hull | Armor | Shield | Kinetic main | Energy main L/S/H | Missile GP |
|---:|---:|---|---|---|---|---|
| 1 | 24 | AP0 / AI8 | Cap4 / R2 / 2/TP / SA0 | D8 SP2 AP0 | D4/6/8 SP2 AP2 | D10 SP2 AP4 |
| 2 | 24 | AP0 / AI10 | Cap6 / R2 / 2/TP / SA0 | D8 SP2 AP2 | D4/6/8 SP2 AP2 | D10 SP2 AP4 |
| 3 | 24 | AP2 / AI10 | Cap6 / R2 / 2/TP / SA0 | D8 SP2 AP2 | D4/6/8 SP2 AP2 | D10 SP2 AP4 |
| 4 | 24 | AP2 / AI12 | Cap8 / R2 / 2/TP / SA0 | D10 SP2 AP2 | D4/8/10 SP2 AP2 | D10 SP2 AP4 |
| 5 | 24 | AP4 / AI12 | Cap10 / R2 / 2/TP / SA0 | D10 SP2 AP2 | D4/8/10 SP2 AP2 | D10 SP2 AP4 |
| 6 | 24 | AP4 / AI14 | Cap10 / R4 / 2/TP / SA0 | D10 SP4 AP2 | D6/8/10 SP2 AP4 | D10 SP2 AP4 |
| 7 | 24 | AP4 / AI14 | Cap14 / R4 / 2/TP / SA2 | D10 SP4 AP2 | D6/8/10 SP2 AP4 | D10 SP2 AP4 |
| 8 | 24 | AP4 / AI14 | Cap18 / R4 / 4/TP / SA2 | D12 SP4 AP4 | D8/10/12 SP4 AP4 | D10 SP2 AP4 |
| 9 | 24 | AP6 / AI16 | Cap24 / R6 / 4/TP / SA2 | D14 SP6 AP6 | D8/12/14 SP4 AP6 | D10 SP2 AP4 |

## Scaled optional/specialist point effects

| Branch | Canonical numerical expression |
|---|---|
| `ablative-armor` | AP0 / AI4 expendable outer layer |
| `kinetic-dense-penetrator` | DAM -2; APEN +2 relative to current standard Kinetic package |
| `kinetic-submunition` | candidate 2 x DAM6 packets; standard SPEN/APEN per packet |
| `kinetic-helical` | DAM8 / R4 / Acc25 / SPEN2 / APEN2 / 0 TP; candidate high-rate/efficiency identity |
| `kinetic-macron` | candidate saturation weapon; 2 x DAM6 packets / R5 / Acc20 / SPEN2 / APEN2 / 2 TP |
| `armor-powered-reactive` | 1 TP sustained; candidate +2 Protection against first eligible physical packet each turn |
| `armor-adaptive-reactive` | 1 TP sustained; candidate +2 Protection against up to 2 eligible physical packets each turn |
| `armor-field-assisted` | 2 TP sustained; candidate reduce post-penetration DAM by 2 (minimum 2) for eligible packets |
| `shield-hardener` | 1 TP sustained -> Shield Armor 2; nonstacking |
| `shield-particle-screen` | 1 TP sustained; candidate Shield Armor +2 only vs particle/charged-beam-tagged attacks |
| `shield-field-stabilizer` | 1 TP sustained; candidate reduce incoming SPEN by 2 (minimum 0) before Shield Armor check |
| `energy-fel` | R7 / Acc30 / Standard 3 TP DAM8; choose SPEN4/APEN2 or SPEN2/APEN4 before firing |
| `energy-ion` | R5 / Acc25 / 3 TP / DAM8 / SPEN4 / APEN2 |
| `energy-neutral-particle` | R6 / Acc25 / 3 TP / DAM10 / SPEN2 / APEN4 |
| `energy-plasma` | R3 / Acc20 / 3 TP / DAM12 / SPEN2 / APEN4 |
| `energy-extreme-frequency` | R9 / Acc30 / 4 TP / DAM12 / SPEN4 / APEN4 |
| `missile-shaped-warhead` | DAM10 / SPEN2 / APEN6 |
| `missile-nuclear-shaped` | DAM14 / SPEN4 / APEN6 |
| `missile-fusion-warhead` | DAM16 / SPEN4 / APEN6 |
| `missile-antimatter-warhead` | DAM20 / SPEN6 / APEN8 |

## Historical compatibility

- `technology_numerical_matrix_v0_1.json` and its companion CP109 artifacts remain unchanged for historical checkpoint reproducibility.
- CP122 introduces `technology_numerical_matrix_v0_2.json` as the canonical numerical ruler for new work.
- No odd half-step value from CP121 is promoted by this migration. Existing values are doubled exactly.
- Future progression checkpoints may use odd canonical integers where a validated half-step is desirable.
