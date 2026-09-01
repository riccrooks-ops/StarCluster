# Checkpoint 146 — Combat Resource Doctrine and Contextual System Activation

**Status:** candidate pending native Windows validation  
**Base checkpoint:** CP145 — Stage-A Diagnostic Attribution and Strategic Viability  
**Checkpoint type:** logic-only combat doctrine / cross-language semantic parity  
**Gameplay numerical changes:** none  
**Technology Numerical Matrix changes:** none  
**Automatic promotion:** disabled  
**Automatic Stage B:** disabled

## Purpose

CP145 is the native-accepted diagnostic baseline, but its accepted evidence exposed an important confounder: the whole-combat research policy can spend Tactical Power on installed support/defensive systems while denying the primary weapon for most or all of a fight. CP146 corrects that decision policy **before any weapon, Reactor, PDS, Sensor, EW, defense, or AUX value is tuned**.

The CP146 doctrine is information-limited. It may use own-ship capability, current geometry, current track state, observed enemy emissions/actions, inbound threats, and future scan information when such scans are eventually implemented. It may **not** inspect hidden opponent build data merely because the simulator has access to it.

The core doctrine is:

1. established combat prefers Active Sensor, with Passive fallback when that preserves a useful combat package;
2. a legal, useful main-weapon package is core Tactical Power demand rather than the final residual consumer;
3. unknown enemy capability can justify residual defensive readiness, but cannot indefinitely starve useful main-weapon operation;
4. observed capability narrows optional-system activation: ECCM is reactive to consequential observed ECM, PDS to unresolved/imminent Missile threat, Shield Hardener to unresolved/Energy threat, and other optional systems follow the same contextual principle;
5. Kinetic/Energy main weapons retain their accepted anti-missile role. A legal single-main ship attack is not automatically sacrificed to defensive hold; Held Main covers otherwise-unserved missile opportunity when there is no legal ship-fire opportunity, while a dual-main ship may dedicate one bank to excess missile defense;
6. finite-ammo main weapons and PDS cease drawing Tactical Power after ammunition exhaustion.

## Why CP146 is required before another balance sweep

CP145's native diagnostic selected TL2 EW Contest and Power Crisis hotspots in which main-weapon TP was denied on roughly 92–99% of turns while other combat demands continued to receive power. Those outcomes accurately described the existing policy, but they cannot safely be interpreted as evidence that Reactor, weapon, or AUX numerical values are wrong.

CP146 therefore treats combat-resource doctrine itself as the experimental variable. The source Technology Numerical Matrix remains byte-frozen.

## Information boundary

At combat start, opponent offensive capability is **Unknown**. The contextual controller does not inspect the opponent's hidden weapon family.

Capability becomes known only through player-observable combat events currently modeled by the kernel:

- direct Kinetic/Energy fire reveals that family after the observable attack occurs;
- a missile launch or already-observed inbound missile reveals Missile capability and the observed missile profile;
- ECM decisions use observed emission/degradation state rather than hidden installation data.

The same knowledge-state architecture is intentionally suitable for future combat sensor scans. A future scan can populate knowledge earlier without requiring a separate omniscient AI path.

## Contextual Tactical Power doctrine

### Core combat package

Once combat is established, Active Sensor is the default. The controller may deliberately fall back to Passive if Passive still provides the required track and Active Sensor would prevent useful main-weapon operation.

A functioning main weapon with a legal useful opportunity is then protected as core demand. Optional defenses and AUX consume remaining TP according to current knowledge and tactical relevance. This does not mean the weapon can never be displaced by a future higher-value survival decision; it means optional installed systems cannot create an indefinite no-fire loop merely by requesting power.

### ECCM

ECCM activates only when hostile ECM has been observed, that ECM materially degrades the Firm track needed for the intended action, and ECCM can restore the needed track without defeating the core package.

### PDS

Before the opponent's offensive family is known, residual PDS readiness is reasonable if PDS is installed and power is available. Once a known non-Missile capability is established, PDS readiness is suppressed. When an imminent Missile threat exists, PDS is powered from residual TP when ammunition/capacity remain useful.

### Shield Hardener and future contextual AUX

Shield Hardener may consume residual TP while the enemy threat is unresolved, and remains relevant when Energy capability is known. It is suppressed after a known non-Energy capability. This establishes the general CP146 rule for future optional AUX: activation follows known/unresolved tactical need rather than installation alone.

### K/E Held Main missile defense

CP146 restores the already-established K/E Held Main anti-missile role to the Python whole-combat research kernel. The accepted C# mechanics provide the parity authority: one held bank may make one Firm-track missile-interception attempt within the weapon's missile-interception range, using the ordinary direct-fire accuracy stack (`50 + weapon accuracy + Tactical Computer`, clamped by the standing hit bounds).

CP146 deliberately avoids a new defensive deadlock:

- a **single-main** K/E ship preserves a legal ship attack even when PDS cannot cover all missile subflights;
- if the main weapon has **no legal ship-fire opportunity**, one K/E bank may be held for an otherwise-unserved missile threat;
- a **dual-main** K/E ship may hold one bank while retaining another offensive bank when funded PDS cannot cover the imminent subflight count.

A dedicated focused fixture exercises the actual Python Held Main resolver with a Firm-tracked incoming missile because the inherited 252-scenario CP145 diagnostic population does not naturally enter the refined no-legal-ship-shot branch.

## PDS terminology correction

CP145's aggregate PDS telemetry used the word `flight` for both magazine Flights and PDS-visible Swarmer subflights. CP146 makes the distinction explicit:

- `terminal_magazine_flights`;
- `pds_visible_subflights`;
- magazine Flights with any/full/partial PDS coverage;
- subflights with zero/one/two attempts.

This preserves the intended Swarmer model. One Swarmer magazine Flight produces two PDS-visible subflights sharing the same Reaction Capacity pool. Under Energy PDS RC1, every Swarmer magazine Flight can receive an interception action while only one of its two child subflights can be covered by that RC point.

## Versioned doctrine and historical reproducibility

CP146 does not rewrite CP145 history. The canonical Python kernel exposes two explicit doctrine versions:

- `cp145_legacy` — reproduces the native-accepted CP145 combat/resource policy;
- `cp146_contextual` — candidate information-limited contextual doctrine.

The existing default remains the legacy doctrine for historical checkpoint fixtures that do not opt into CP146. The CP146 study explicitly selects both versions.

The study replays the exact CP145 diagnostic population:

- 252 accepted scenario identities;
- 25 exact CP144/CP145 trial indices per identity;
- master seed `140001`;
- 6,300 legacy combats;
- 6,300 contextual combats;
- **12,600 total**.

The legacy half is required to reproduce the retained native-accepted CP145 diagnostic CSV field-for-field. Only after that gate passes are before/after doctrine deltas interpreted.

## Cross-language semantic contract

`docs/design/testing/cp146_combat_resource_doctrine_parity_fixtures_v0_1.json` is a shared C#/Python semantic fixture for the contextual resource policy.

Python evaluates the fixture through `combat_resource_doctrine.py`. Production C# contains `CombatResourceDoctrineService`, with xUnit coverage reading the same JSON fixture. This service establishes executable C# semantics for the resource doctrine without retroactively altering prior ScenarioRunner/calibration histories. Existing CP145-owned C# files remain byte-frozen; CP146 adds the new service and its tests rather than modifying accepted legacy mechanics.

The existing C# Held Main mechanics remain the authority for direct-fire missile interception; the Python whole-combat kernel now restores that accepted behavior in its contextual doctrine path.

## Accepted CP145 provenance

CP146 retains only the compact accepted evidence it needs under `docs/validation/evidence/checkpoint-146/accepted-cp145/`:

- `CP145_NATIVE_ACCEPTANCE_SUMMARY.json`;
- `CP145_ACCEPTED_DIAGNOSTIC_SUMMARY.json`;
- `CP145_ACCEPTED_DIAGNOSTIC_REPLAY_RESULTS.csv`.

Pinned hashes are recorded in `cp146_combat_resource_doctrine_study_v0_1.json`. The submitted CP145 native-results archive remains external provenance by SHA-256:

`dada2c5120fb65e9c340ce6f9a5bbc40b32a195f98d89fcec9eba2382005aafa`

The Technology Numerical Matrix remains:

`3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194`

## Authoring evidence — not native acceptance

The final pre-handoff authoring validation completed the full Python regression at **328 / 328 passed** in four isolated process groups (124 + 47 + 40 + 117), including **18 / 18 CP146-focused tests**. The complete 6,850-cell CP144 legacy smoke replay also reproduced the accepted signature exactly: 6,785 resolved, 9 resolved at 25+ turns, 65 turn-cap sentinels, zero safe stalemates, zero non-standoff Open orders, and zero errors. The final matched doctrine replay completed **12,600 / 12,600 combats** with zero failed gates:

- CP145 legacy half: 6,300 combats;
- contextual half: 6,300 combats;
- accepted CP145 legacy field mismatches: **0**;
- source numerical matrix modified: **no**;
- TL2 selected EW + Power Crisis turn caps: **400 legacy -> 0 contextual**;
- TL2 mean weapon-denial turn rate: approximately **95.6% -> 0%**;
- contextual legal main-weapon core funded turns: **118,201**;
- contextual legal main-weapon core starved turns: **0**;
- newly saturated 25/25 turn-cap cells: **0**;
- unknown-opponent turns observed: **29,925**;
- known-opponent turns observed: **105,601**.

The inherited 252-scenario diagnostic population records zero final Held Main declarations after the deadlock-safe refinement; that is a population-coverage fact, not evidence that Held Main is inactive. The focused deterministic resolver test separately exercises the actual anti-missile branch under a legal no-ship-shot/Firm-missile-track condition.

These authoring results are diagnostic only. Native Windows acceptance remains authoritative.

## Frozen numerical boundary

CP146 promotes no numerical value. In particular it does **not** alter:

- weapon DAM/APEN/SPEN/accuracy/range/TP;
- Missile movement, guidance, cadence, warhead, magazine, or Swarmer structure;
- PDS accuracy, RC, attempts/flight, range, ammo, or TP;
- Reactor TP;
- Sensor, ECM, ECCM values;
- Shield/Armor/DEF/RES values;
- AUX numerical characteristics;
- map geometry or turn sentinel;
- Technology Numerical Matrix or Concept authority.

Any combat-outcome change under `cp146_contextual` is therefore evidence about doctrine/decision logic, not a hidden balance-number promotion.

## Native Windows acceptance sequence

Use a fresh CP146 extraction and run both commands in the **same unchanged tree**:

```powershell
.\tools\checkpoints\checkpoint-146\apply_checkpoint_146.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-146\apply_checkpoint_146.ps1
```

RepositoryOnly is expected to verify the complete inherited regression chain, the CP146 focused/shared-doctrine tests, numerical/ownership contracts, and the legacy CP144 smoke signature. The normal invocation then executes the 252 × 25 × 2 = 12,600 before/after doctrine study, requires exact accepted-CP145 legacy reproduction, validates the contextual behavior gates, writes the native acceptance summary, and packages the timestamped results ZIP.

## Promotion rule and next step

CP146 itself promotes **no gameplay number**.

If native CP146 validates the contextual doctrine, exact legacy reproducibility, and behavior gates, the next research step is to rerun a broad whole-combat response surface **under the accepted contextual doctrine** before returning to K/E/Missile/PDS/Reactor/AUX numerical tuning or Stage B. Historical CP144/CP145 balance outcomes remain evidence under the legacy resource policy and must not be numerically mixed with post-CP146 outcomes as if doctrine were unchanged.
