# Checkpoint 58 - Single-Main TL4 Subsystem Foundation and Powered Defense Screening

## Purpose

Checkpoint 58 keeps TL1-TL3 frozen and accepts Checkpoint 57a as negative evidence against normal player multi-main progression. The standard player cruiser has one main weapon at every TL. The TL4 mid-tech foundation is screened through subsystem capability, natural Tactical Power demand, and new powered defensive AUX concepts rather than weapon-count growth.

The 75-80% conditional TL4-over-mature-TL3 region is a starting review target for a genuine generation jump, not a blocking gate or a value to force by construction. The prior-generation specialization-resistance lane remains part of the decision.

## Repository-only gate

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58\apply_checkpoint_58.ps1 -RepositoryOnly
```

Expected high-level results:

- repository manifest verifies with no unexpected repository-owned files;
- PowerShell parser succeeds;
- pinned SDK is 8.0.423;
- clean warnings-as-errors build succeeds;
- StarCluster.Tests succeeds;
- Checkpoint 57a frozen ScenarioRunner JSON hashes remain unchanged;
- Checkpoint 58 architecture/runtime/study contracts succeed.

Do not start the Monte Carlo workload if repository-only validation fails.

## Full run

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58\apply_checkpoint_58.ps1 -Trials 10000 -Jobs 24
```

Checkpoint 58 contains 56 runner stages and 14,746 Monte Carlo variants, or 147.46 million trials at the default 10,000 trials per variant.

Results are written to `out/checkpoint-58`.

## New evidence lanes

1. **TL4 single-main subsystem-axis screening** - exact TL3-equivalent control plus isolated fire-control, higher-output/higher-power weapons, reactor, structure, armor protection, shields, and mobility candidates.
2. **TL4 composed foundation packages** - conservative combinations built from those isolated axes; no candidate is auto-promoted.
3. **Mature TL3 specialization resistance** - naked TL4 packages versus the 13 mature TL3 two-AUX specializations.
4. **Powered-defense AUX isolation** - Shield Hardener and Energized Armor strength/power candidates.
5. **Powered-defense + compact-power pairings** - Shield Hardener/Energized Armor paired with mature TL3 Battery B4G1 or Capacitor C2D1.
6. **Single-main natural power screen** - Auxiliary Reactor versus Battery+Battery, Capacitor+Capacitor, and Battery+Capacitor under both frozen-reactor and +1-reactor TL4 weapon-demand envelopes, with no synthetic background TP.

## Interpretation priorities

- Confirm the exact TL4 single-main control remains 50/50 versus frozen TL3.
- Identify which isolated TL4 axes create useful generational value without producing integer-breakpoint domination.
- Prefer a composed TL4 package near the 75-80% conditional review region only if mature TL3 specialization remains meaningfully relevant.
- Track `mean_prevented_insufficient_power` and other Tactical Power telemetry when judging reactor growth and higher-power subsystems.
- Do not make reactor output increases merely because TL increased; added output should have actual demand.
- Evaluate Shield Hardener and Energized Armor as sustained powered systems whose benefits disappear when unpowered; passive shields/armor remain governed by their normal rules.
- Do not promote any TL4 powered-defense candidate solely because it wins an isolated duel lane; power opportunity cost and mixed-AUX flexibility matter.

## Acceptance handoff

Return the complete `out/checkpoint-58` directory (ZIP is fine). Assessment should compare the new six result directories against the frozen Checkpoint 57a evidence and identify a TL4 package only if the generation jump and specialization-resistance evidence are both healthy.
