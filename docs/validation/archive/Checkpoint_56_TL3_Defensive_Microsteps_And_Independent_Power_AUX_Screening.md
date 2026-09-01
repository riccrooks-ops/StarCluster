# Checkpoint 56 - TL3 Defensive Microsteps and Independent Power AUX Screening

## Acceptance intent

Checkpoint 56 is a **screening** checkpoint. It does not automatically promote a final TL3 profile or any Battery/Capacitor candidate. Accepted Checkpoint 55b evidence remains frozen.

## Repository-only gate

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-56\apply_checkpoint_56.ps1 -RepositoryOnly
```

The gate verifies the three-generation capacity curves, all 79 frozen Checkpoint 55b ScenarioRunner JSON hashes, the complete integrated-combat study envelopes, TL3 single-main legality, microstep values, power-component independence, equal-capacity profile counts, workbook formula caches, Concept decisions, and checkpoint accounting before the calibration harness proceeds.

## Full native validation

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-56\apply_checkpoint_56.ps1 -Trials 10000 -Jobs 24
```

Expected workload: **45 stages / 12,691 Monte Carlo variants / 126.91 million trials**.

## New studies

- `tl3-itc04-defensive-microstep-screening` - 108 variants.
- `tl3-aux04-offense-base-two-capacity-screening` - 585 variants.
- `tl3-aux05-shield-breakpoint-screening` - 72 variants.
- `tl3-aux06-tl2-tl3-production-progression` - 702 variants.
- `tl3-pwr03-component-characteristic-sweep` - 168 variants.
- `tl3-pwr04-equal-capacity-power-loadouts` - 360 variants.

## Review questions

1. Does offense-only TL3 need no defensive increase, Hull +1, Armor Integrity +1, or Shield Capacity +1?
2. Do Shield Booster/Stabilizer remain outliers after the rejected bundled defensive base is removed?
3. Does the real TL2-one-AUX to TL3-two-AUX production step remain meaningful without becoming compulsory regardless of loadout?
4. Which Battery characteristic matters: charge count, magnitude, or both?
5. Which Capacitor characteristic matters: stored capacity, discharge magnitude, or both, with charge rate fixed at 1?
6. At equal two-AUX opportunity cost, does Auxiliary Reactor earn its sustained role against Battery/Battery, Capacitor/Capacitor, and Battery/Capacitor alternatives?
7. Do duplicated power AUX systems remain independent in resource state, per-turn operation, and damage condition?

TL4-TL9 runtime generation remains deferred until these questions are reviewed.
