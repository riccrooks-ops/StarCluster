# Checkpoint 18a - Application and PDS Regression Hotfix

> **Superseded policy note:** Checkpoint 18b restores the previously accepted rule that standard PDS is terminal defense only. The 18a transit-PDS compatibility interpretation is retained below as historical defect context, not current behavior.

## Purpose

Checkpoint 18a repairs application and compatibility defects found while applying Checkpoint 18. It does not change the accepted terminal sequence, source-neutral Firm eligibility, seeker roles, Search/Wait fuel rules, or d100 terminal outcomes.

## Corrected defects

### Superseded overlay files

Historical extract-over-existing workflows could leave three pre-guidance files in the repository:

- `src/StarCluster.Core/Combat/Missiles/MissileAdvanceResult.cs`
- `src/StarCluster.Core/Combat/Missiles/MissileSalvo.cs`
- `tests/StarCluster.Tests/Combat/Missiles/MissileSalvoTests.cs`

Those files were superseded at Checkpoint 11. The apply script now removes them before scanning canonical source and tests for the obsolete `Arrived`/`HasArrived` shortcut. Generated `bin` and `obj` trees are excluded from that semantic scan, and any remaining canonical match is printed with its path and line number.

### Terminal test-name guard

The implementation test is named `PdsReceivesTerminalEntryAndPreAttackOpportunities`. The initial package checked an earlier proposed name and stopped before compilation. The guard now checks the delivered test name.

### Preserved layered PDS behavior

Checkpoint 18 initially restricted standard PDS to `Stationary`, `TerminalEntry`, and `PreTerminalAttack`. That accidentally removed the ordinary in-envelope `Transit` reaction established by Checkpoints 12 and 12a.

Checkpoint 18a restores the intended layered contract:

- held direct-fire weapons may react during transit/entry but not in the separate pre-attack PDS window;
- standard PDS may react during `Transit`, `Stationary`, `TerminalEntry`, and `PreTerminalAttack` when otherwise eligible;
- ordinary transit opportunities remain coordinate-specific and consume the installed system's shared per-phase attempt budget;
- only the two terminal windows collapse multiple PDS components on the same defending ship into one attempt per Flight per window; and
- a successful earlier layer still prevents redundant later shots.

### Correct clean-suite total

The accepted Checkpoint 17c run reported 490 tests because an obsolete `MissileSalvoTests.cs` file from the pre-guidance model remained in the working tree and contributed 19 historical test cases. The clean canonical Checkpoint 17c baseline is therefore 471 tests. Checkpoint 18 adds 22 focused terminal tests, producing the correct total of **493 tests**.

## Expected result

The corrected Checkpoint 18 apply script should build without warnings and report **493/493 passing tests**. The four previously failing layered-interception tests are expected to pass after transit PDS eligibility is restored.
