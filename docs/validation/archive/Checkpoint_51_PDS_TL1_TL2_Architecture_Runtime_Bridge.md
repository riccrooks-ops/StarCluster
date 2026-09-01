# Checkpoint 51 - PDS TL1 Entry Correction and TL1/TL2 Architecture Runtime Bridge

## Purpose

Checkpoint 51 is the first limited runtime use of the reviewed player-technology architecture. It does **not** promote a full TL1-TL9 numerical chart. It corrects the PDS entry floors, proves that the table-driven TL1 profile exactly reproduces the frozen baseline, retains the accepted TL2 standard profile, and runs an architecture-legal one-slot TL1/TL2 Auxiliary study.

## Accepted baseline

Checkpoint 50 is the frozen implementation and capacity baseline. The normal cruiser capacity curve remains:

- AUX Capacity TL1-TL9: `1 / 1 / 2 / 2 / 3 / 3 / 3 / 4 / 4`
- Weapon Bays TL1-TL9: `1 / 1 / 2 / 2 / 2 / 3 / 3 / 3 / 4`

The historical Checkpoint 48 TL2 two-AUX screening allowance remains historical evidence only.

## Checkpoint 51 architecture changes

All three standard PDS sub-families enter at TL1:

- Kinetic Point Defense
- Energy Point Defense
- Anti-Missile Missile Battery

They retain one common PDS family contract: eligible close-range terminal threats, including missile flights and boarding craft when that runtime exists; no anti-ship fire; normal terminal-defense timing and reaction accounting. Sub-family differences are explicit characteristics rather than hidden target restrictions.

The provisional TL1 PDS base chances are 10/12/15 for Kinetic/Energy/AMM. TL2 candidates are 13/16/20. Reaction Capacity is held at one in this pass. These values are review candidates only and are not automatically promoted by a successful run.

## Limited table-driven runtime bridge

The new standard runtime catalog contains only `tl1-production` and `tl2-production`.

- TL1 must reproduce the frozen authoritative baseline exactly; the runner rejects the catalog if it does not.
- TL2 must remain the accepted Checkpoint 48/49/50 production profile.
- No TL3-TL9 runtime profiles are generated in this checkpoint.

The legal combat AUX matrix contains 8 TL1 profiles and 9 TL2 profiles. Every normal profile costs one AUX Capacity. Legal early components that do not yet have an implemented combat effect are omitted rather than assigned a fake zero-value combat profile. `No AUX` remains isolated as a counterfactual diagnostic.

## New Monte Carlo stage

Study: `aux-itc02-architecture-derived-tl1-tl2-pds`

- 867 legal architecture-derived variants
- 108 no-AUX diagnostic variants
- 975 total variants
- TL1v1 legal: 192
- TL2v2 legal: 243
- TL1v2 / TL2v1 legal: 432
- 289 legal variants per same-family Kinetic, Energy, and Missile context

The full checkpoint therefore contains 25 runner stages and 6,988 Monte Carlo variants. At 10,000 trials per variant this is 69.88 million trials.

## Frozen regression boundary

The 53 runtime scenario files present in the Checkpoint 50 snapshot must remain byte-identical. The existing `aux-itc01-single-slot-performance-screening` study remains in the run as historical regression evidence. The new ArchitectureTechnology files are additive.

## Windows validation

Repository/architecture validation only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-51\apply_checkpoint_51.ps1 -RepositoryOnly
```

Full validation at the normal trial count and worker setting:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-51\apply_checkpoint_51.ps1 -Trials 10000 -Jobs 24
```

## Acceptance criteria

Accept Checkpoint 51 only if:

1. Repository manifest and active-file contracts pass.
2. The architecture gate confirms all three PDS entry floors at TL1 and the accepted capacity curves.
3. The new table-derived TL1 profile exactly matches the frozen baseline and TL2 matches the accepted standard.
4. The new AUX catalog contains 8 legal TL1 and 9 legal TL2 one-slot combat profiles plus two counterfactual no-AUX profiles.
5. The new study contains exactly 975 variants with the required partitions and technology bands.
6. All frozen Checkpoint 50 scenario hashes remain unchanged.
7. The clean .NET build has zero warnings and zero errors.
8. All unit tests and ScenarioRunner self-tests pass.
9. All checkpoint stages and gates pass.

Balance dominance, role expression, counter relationships, and compulsory-choice signals in the new study are **review evidence**, not automatic promotion criteria. The results should be assessed before any TL1/TL2 candidate values are accepted.
