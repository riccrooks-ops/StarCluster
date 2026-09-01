# Checkpoint 18 Validation - Unified Missile Terminal Solutions, Search, and Seeker Assistance

## Automated acceptance

Run the checkpoint apply script from the repository root with Godot closed:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-18\apply_checkpoint_18.ps1
```

Expected result:

- .NET SDK 8.0.423 selected;
- complete solution builds with warnings treated as errors;
- **493/493 engine-independent tests pass**;
- Concept v0.3s and archived v0.3r hashes verify;
- the external reference manifest verifies; and
- exactly this Checkpoint 18 file remains active under `docs\validation`.

Record the full console output if any step fails.

## Manual setup

1. Reopen `src\StarCluster.Game\project.godot` in Godot .NET.
2. Run the tactical prototype.
3. Keep **AUTHORITATIVE DEBUG** off for observer-safe checks. Enable it only for the dedicated internal-state comparisons below.
4. Preserve the generated `checkpoint-18` JSONL and readable log pair for any unexpected result.

## A. Target-hex entry is not automatic impact

1. Use a scenario with at least one hostile Missile Flight that can reach the player ship's hex.
2. Advance to Missile / Interception.
3. Observe the Flight entering the target hex.

Confirm:

- entering the hex produces terminal processing rather than unconditional `IMPACT`;
- the first defense attempt, when PDS has capacity and a legal local track, is identified as `TerminalEntry`;
- a missed entry attempt allows acquisition to continue;
- an entry interception removes the active Flight and produces `INTERCEPTED`, not `IMPACT`; and
- the authoritative log orders entry defense before terminal acquisition.

## B. Two distinct PDS windows

Use a seed/run where the entry PDS attempt misses and acquisition succeeds.

Confirm:

- standard PDS still receives ordinary in-envelope transit opportunities before the terminal sequence, subject to its shared per-phase attempt budget;
- the same defending ship receives no more than one standard-PDS attempt in the entry window even if multiple PDS components exist;
- the second standard-PDS opportunity occurs only after Firm acquisition and immediately before the terminal attack roll;
- the second attempt is identified as `PreTerminalAttack`;
- an interception in that window prevents the attack roll; and
- a Flight that fails acquisition does not receive a pre-attack PDS attempt until it later gains Firm.

## C. Report-source-neutral Firm eligibility

With AUTHORITATIVE DEBUG enabled, exercise or inspect fixtures for:

- command-guided plus live Firm datalink;
- command-guided plus blocked/retained report;
- sensor-equipped plus live Firm datalink;
- sensor-equipped plus Current/Firm local report; and
- seeker-only plus an eligible remote cue.

Confirm:

- live Firm remote information can support both command-guided and sensor-equipped Flights;
- a sensor-equipped Flight can instead use its own Firm local report;
- blocked or retained Stale launcher information does not masquerade as a live Firm solution;
- seeker-only acquisition rolls locally before attack; and
- normal observer-safe presentation does not expose hidden hostile source or acquisition arithmetic.

`PeerGuidance` is a code seam only in this checkpoint and has no required Godot scenario.

## D. Search/Wait and fuel

Use a seed or profile that fails terminal acquisition on arrival.

Confirm:

- the Flight remains active and is shown as `SEARCHING` when observable;
- the arrival action adds no stationary-search fuel beyond movement already spent;
- the next stationary Search/Wait activation consumes exactly one whole fuel unit;
- a later successful acquisition proceeds immediately to the pre-attack PDS window and attack in that missile action;
- a better report at another coordinate resumes cruise without refunding prior movement or search fuel; and
- a failed search that exhausts fuel produces `SELF-DESTRUCTED`, not a miss or impact.

Compare the visible remaining range with the authoritative `DistanceTraveled`, `StationarySearchFuelSpent`, and `TotalFuelSpent` values.

## E. Terminal outcomes and cues

Across repeatable seeds or focused fixtures, confirm that the journal and visible cue distinguish:

- acquisition failure / `SEARCHING`;
- entry or pre-attack `INTERCEPTED`;
- natural 01 `DUD`;
- ordinary `MISS`;
- ordinary `IMPACT` for a hit;
- natural 100 critical hit in the authoritative record, while normal presentation remains an impact until damage rules need a distinct cue; and
- `SELF-DESTRUCTED` on fuel exhaustion.

A dud must be terminal and inert. It must not move, sense, retry, or attack again.

## F. Observer-safe and presentation regression

With AUTHORITATIVE DEBUG off:

- unknown hostile Flights do not appear;
- Approximate/Stale hostile contacts do not reveal exact terminal source, rolls, or hidden target coordinates;
- selected-only friendly dashed plans and selected-only solid history remain unchanged;
- dotted hostile threat estimates remain estimates rather than asserted enemy guidance truth;
- searching Flights remain selectable while active;
- terminal cues persist through Damage as established previously; and
- no obsolete `Arrived` status or automatic-impact wording appears in normal status text.

## G. Diagnostic ordering

For one successful attack and one Search/Wait result, inspect the JSONL sequence.

Successful terminal sequence should show:

1. missile movement edge into the target hex;
2. terminal opportunity;
3. terminal-entry interception attempt/result;
4. acquisition resolution;
5. pre-attack interception attempt/result;
6. terminal attack resolution; and
7. batch finalization / observer-safe refresh.

Failed acquisition should stop after acquisition and Search/Wait activation. A later search action should record its fuel expenditure before any new acquisition/attack result.

## Results template

- Apply script: PASS / FAIL
- Automated tests: ___ / 493 passed
- A. Target-hex entry: PASS / FAIL / NOT RUN
- B. Two PDS windows: PASS / FAIL / NOT RUN
- C. Firm source eligibility: PASS / FAIL / NOT RUN
- D. Search/Wait fuel: PASS / FAIL / NOT RUN
- E. Terminal outcomes: PASS / FAIL / NOT RUN
- F. Observer-safe regression: PASS / FAIL / NOT RUN
- G. Diagnostic ordering: PASS / FAIL / NOT RUN
- Godot client size:
- Scenario and seed:
- JSONL log filename:
- Readable log filename:
- Notes / reproduction steps:
