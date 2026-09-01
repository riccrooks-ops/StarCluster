# Checkpoint 43 - Auxiliary Component Foundation and Availability Gating

## Objective

Close the installation and standard-availability foundation for optional Auxiliary systems without changing accepted combat mechanics. Checkpoint 43 separates Dedicated Core, Weapon Bay, and Auxiliary Capacity; makes the cost of core integration explicit; preserves the stripped TL1 fixture as an isolation tool; and places 27 standard-player AUX families behind candidate-only research, Hull, capacity, compatibility, and balance-entry gates.

## Authoritative command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .	ools\checkpoints\checkpoint-43pply_checkpoint_43.ps1 `
  -Trials 10000 `
  -Jobs 24
```

Run from a clean full-repository extraction. Preserve the complete `out/checkpoint-43` directory.

## Repository-only command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .	ools\checkpoints\checkpoint-43pply_checkpoint_43.ps1 `
  -RepositoryOnly
```

## Required closure

- Clean complete-repository manifest and PowerShell parsing.
- Clean warning-as-error .NET build.
- 800 compiled tests pass.
- All 19 configured stages pass; the retained 1,350 Monte Carlo variants and 46 ScenarioRunner self-tests remain unchanged.
- The deterministic `auxiliary-component-foundation` stage reports exactly three installation classes and 27 unique candidate AUX families.
- `coreMeansFree`, `standardAuxiliaryResearchTree`, and `existingCombatMechanicsRevisedByThisCheckpoint` are all false.
- Dedicated Core does not consume generic AUX capacity, while the AUX class does.
- The zero-AUX stripped fixture remains allowed and the normal player exact AUX capacity remains unpromoted.
- Every catalog family consumes 1-3 AUX capacity, has no more than two support floors, and remains `candidate_only` / `not_promoted`.
- Every candidate floor is upward-only until explicit promotion.
- All high-risk entries begin at TL2 or later; Shield Hardener, Energized Armor Controller, Tractor Projector, and Auxiliary Hangar Bay begin at TL3 or later.
- ECM and ECCM share the same candidate starting floor.
- Standard cloak is absent and explicitly excluded.
- The retained Checkpoint 42 analytical and candidate Monte Carlo stages still pass.

## Expected new output

`out/checkpoint-43/auxiliary-component-foundation` should contain:

- `summary.json`
- `installation-classes.csv`
- `catalog.csv`
- `availability-gates.csv`
- `gates.csv`
- `result.sha256.txt`

`summary.json` must report 27 families, zero failed gates, no mechanics revision, no visible AUX research tree, and `coreMeansFree: false`.

## Interpretation

The catalog is not a production shop list. A TL1 fixture proves implementation behavior, not standard TL1 availability. The proposed starting TL is the first point worth testing. If the item is overpowered there, raise its starting TL before reducing its established identity. A later checkpoint must still test capacity opportunity cost, Tactical Power or finite stores, counters, stacking, pacing, and compulsory-choice risk before promotion.
