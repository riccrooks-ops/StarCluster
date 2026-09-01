# Checkpoint 18c - Headless Runner Policy and Initialization Hotfix

## Purpose

Checkpoint 18c corrects three defects found by the first clean Checkpoint 18b build-and-test run. The headless runner architecture, scenario schema, deterministic matrix, and Godot separation remain unchanged.

## Corrections

### Held direct-fire opportunity policy

Held direct-fire weapons are deliberate non-terminal interceptors. They may react during `Transit` and `Stationary` opportunities, subject to range, line of sight, tactical-track requirements, order targeting, priority, and the shared per-phase attempt budget. They do not participate in `TerminalEntry` or `PreTerminalAttack`.

Standard PDS remains terminal defense only:

- one `TerminalEntry` opportunity when a hostile Missile Flight enters the defended ship's hex; and
- one `PreTerminalAttack` opportunity after Firm acquisition and before the attack roll.

This prevents a held main weapon and standard PDS from both firing in the same terminal-entry window.

### Waiting-for-route interception regression test

The legacy waiting/no-route test previously used standard PDS to intercept a stationary Missile Flight. That expectation was obsolete after terminal-only PDS was restored. The test now uses a held direct-fire weapon and continues to prove that a non-moving, non-terminal Missile Flight can be intercepted at its current coordinate without spending missile fuel.

### Retained datalink initialization chronology

A pre-existing retained datalink report records the guidance phase in which it was received. Scenario initialization now restores the Missile Flight's guidance-phase counter to at least that recorded phase before applying the retained report. An omitted/default counter therefore cannot create a report from a future guidance phase, while an explicitly higher counter remains preserved.

## Acceptance

- solution builds with warnings treated as errors;
- **506/506** engine-independent tests pass;
- all **7/7** deterministic headless scenarios pass; and
- no detailed Godot mechanical validation is required.
