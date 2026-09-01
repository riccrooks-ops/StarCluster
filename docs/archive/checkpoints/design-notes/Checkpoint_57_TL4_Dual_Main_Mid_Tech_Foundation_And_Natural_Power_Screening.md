# Checkpoint 57 - TL4 Dual-Main Mid-Tech Foundation and Natural Power Screening

## Acceptance intent

Checkpoint 57 is a **screening** checkpoint. Checkpoint 56 is accepted and freezes TL1-TL3. The checkpoint does not automatically promote dual-main TL4 or any new TL4 component statistics.

TL4 is deliberately tested with accepted TL3 component numbers. Its provisional foundational change is two unrestricted main weapons instead of one, while AUX Capacity remains two. If this architecture broadly invalidates mature specialized TL3 ships, the preferred fallback is one main weapon throughout TL1-TL9 rather than a special firing restriction.

## Repository-only gate

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-57\apply_checkpoint_57.ps1 -RepositoryOnly
```

The gate verifies the three-generation capacity curves, all 88 frozen Checkpoint 56 ScenarioRunner JSON hashes, the unrelated source/test/reference freeze list, TL3 production values, exact TL3/TL4 component-stat equality, Battery B4G1 and Capacitor C2D1, independent two-component power builds, complete integrated-combat study envelopes, absence of synthetic background Tactical Power in new TL4 studies, workbook formula caches, Concept decisions, and checkpoint accounting.

## Full native validation

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-57\apply_checkpoint_57.ps1 -Trials 10000 -Jobs 24
```

Expected workload: **50 stages / 13,846 Monte Carlo variants / 138.46 million trials**.

## New studies

- `tl4-itc01-foundation-transition` - 180 variants: 18 exact single-main controls plus 162 dual-main TL4-vs-TL3 transition variants.
- `tl4-itc02-two-bay-loadout-screening` - 243 variants: all nine ordered TL4 two-bay loadouts across ranges 3/4/5.
- `tl4-itc03-tl3-specialization-resistance` - 468 variants: naked TL4 dual-main ships versus 13 specialized mature TL3 two-AUX loadouts.
- `tl4-pwr01-natural-two-bay-power` - 120 variants: Auxiliary Reactor, Battery+Battery, Capacitor+Capacitor, and Battery+Capacitor under natural two-bay demand.
- `tl4-pwr02-mixed-power-flexibility` - 144 variants: one-slot Battery/Capacitor paired with Evasion, AMM, or Energy PDS, compared with Reactor and no-AUX controls.

## Review questions

1. Does the exact single-main TL4 control remain 50/50 with TL3, proving the technology label itself adds no hidden combat advantage?
2. How large is the TL3 single-main -> TL4 dual-main jump when component statistics are otherwise identical?
3. Does a naked TL4 ship broadly defeat fully specialized mature TL3 ships, or do TL3 specialization and favorable loadouts remain relevant?
4. Are any of the nine ordered TL4 two-bay weapon combinations compulsory or severely noncompetitive?
5. Does the natural two-bay power envelope create meaningful differences among Auxiliary Reactor, dual Batteries, dual Capacitors, and Battery+Capacitor without synthetic stress?
6. Does the capacity-2 Auxiliary Reactor earn its sustained role while mixed one-slot power builds retain useful flexibility?
7. Is unrestricted multi-main scaling viable as the mid-tech foundation, or should normal player cruisers retain one main weapon throughout TL1-TL9?

Do not tune TL4 weapon damage, accuracy, defenses, or other component statistics until these questions are reviewed.
