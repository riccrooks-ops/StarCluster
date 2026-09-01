# Checkpoint 18b - Headless Scenario Runner and Deterministic Combat Validation

## Purpose

Checkpoint 18b moves detailed mechanical validation out of the Godot client and into an engine-independent, script-driven host. It also restores the previously accepted role of standard Point Defense Systems as terminal defense rather than ordinary transit interception.

The checkpoint addresses two process problems exposed during Checkpoint 18 validation:

- temporary diagnostic UI was consuming development effort that should remain focused on authoritative mechanics; and
- manual Godot procedures depended on hidden state, fixed seeds, rare outcomes, and lengthy log interpretation that were impractical for reliable human validation.

## Authoritative initialization contract

`ScenarioInitializationService` is a Core service. It creates the complete tactical runtime before the first scripted action rather than allowing the runner to manufacture post-initialization results.

Initialization performs these steps in order:

1. create the finite system map and star;
2. place terrain and ships;
3. create ship runtime state;
4. seed any fragmentary prior intelligence;
5. reconstruct optional pre-existing Missile Flights through normal lifetime objects, including travel history, fuel expenditure, retained datalink reports, missile-local reports, and active Search/Wait state;
6. run the existing sensor-contact evaluator and system-entry track initializer for every observer against ships and pre-existing missiles; and
7. create the normal tactical turn cursor and authoritative diagnostic journal.

Only after this contract completes may a runner, AI host, Monte Carlo study, or player-facing client execute actions. The runner does not reimplement sensor, track, movement, datalink, guidance, interception, terminal, or fuel rules.

## Scenario runner

`StarCluster.ScenarioRunner` is a .NET console host that references `StarCluster.Core` directly. Versioned JSON scenarios define:

- map and environment;
- ships and installed tactical profiles;
- prior intelligence;
- optional pre-existing Missile Flights;
- deterministic interception outcomes and terminal d100 rolls;
- phase-legal scripted ship movement, missile actions, and phase changes; and
- declarative expected state, track, interception-window, and event-order assertions.

Scripted ship movement uses the normal turn-scoped planner and commits one entered hex at a time, refreshing missile-local observations and tactical tracks after every edge just as the Godot host does. Scripted missile actions are accepted only in Missile / Interception, and scripted ship movement only in Movement.

The runner supports one scenario or a directory of scenarios. Normal console output is intentionally compact. Each scenario writes a concise `summary.json` plus authoritative JSONL and readable logs. A `failures.txt` file is written only when assertions fail.

## Initial deterministic matrix

Seven scenarios cover the immediate Checkpoint 18 contract:

1. terminal-entry and pre-attack PDS windows followed by one hit;
2. terminal-entry interception;
3. seeker acquisition failure, Search/Wait fuel expenditure, later acquisition, and attack;
4. Search/Wait fuel exhaustion and safe self-destruction;
5. reconstruction and initial observation of a pre-existing Missile Flight;
6. phase-legal per-entered-hex ship movement followed by a command-guided attack using the refreshed live Current/Firm datalink report; and
7. blocked datalink with an aged retained report that cannot masquerade as a Firm terminal solution.

These scenarios are deterministic regression assets, not hard-coded test paths in Core.

## Standard PDS role

Standard PDS is terminal defense:

- it does not react during ordinary `Transit` or `Stationary` opportunities;
- it receives one `TerminalEntry` opportunity when a hostile Flight enters the defended ship's hex; and
- after the Flight obtains a Firm terminal solution, it receives one separate `PreTerminalAttack` opportunity immediately before the attack roll.

Held direct-fire weapons remain the ordinary transit interceptor. Future advanced or extended-range defensive components may add explicit transit capability without changing standard PDS semantics.

## Validation strategy

Star Cluster now uses three validation layers:

1. focused unit tests for individual policies and services;
2. deterministic headless scenarios for complete multi-service behavior; and
3. small Godot smoke checks for input plumbing, rendering, and observer-safe presentation only.

The user is no longer expected to maneuver until a rare mechanical condition occurs or manually reconstruct authoritative sequencing from a large Godot log.

## Future Monte Carlo extension

The scenario schema, deterministic random-source seams, concise summaries, and shared Core initialization are intentionally suitable for later repeated-trial execution. Future passes may add parameter sweeps and aggregate statistics for TL differences, ECM/ECCM, sensors, seekers, PDS, guidance computers, fuel, range, damage, and other balance assumptions without creating a second simulation model.

## Expected acceptance

- solution builds with warnings treated as errors;
- **506/506** engine-independent tests pass;
- all **7/7** deterministic scenarios pass; and
- Godot requires only a brief launch-and-display smoke check rather than detailed mechanical validation.
