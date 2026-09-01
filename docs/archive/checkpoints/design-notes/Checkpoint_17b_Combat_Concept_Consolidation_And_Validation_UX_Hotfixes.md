# Checkpoint 17b — Combat concept consolidation and validation UX hotfixes

## Purpose

Checkpoint 17b is a narrow consolidation and corrective checkpoint between the accepted Checkpoint 17a missile foundation and the next substantive terminal-seeker implementation. It captures the combat architecture agreed during the design review and resolves the two validation obstacles identified during Checkpoint 17a.

## Delivered hotfixes

### 1. Usable AUTHORITATIVE DEBUG region

The right-side detail `ScrollContainer` now has a minimum height of 190 pixels. Turning on **AUTHORITATIVE DEBUG** defers one layout frame and automatically scrolls the selected-missile authoritative label into view. The panel remains development-only and default-off; disabling it restores the normal observer-safe information boundary.

### 2. Dedicated friendly Missile Flight route fixture

`DemoScenarioFactory` adds **Friendly missile route validation**, a clear Firm-track arrangement dedicated to launching a player Missile Flight and validating the dashed friendly route grammar. This removes the ambiguity in the Checkpoint 17a runbook, which requested a friendly route without providing a purpose-built fixture.

## Concept v0.3q consolidation

Concept v0.3q records the accepted direction developed after Checkpoint 17a, including:

- deterministic hard eligibility followed by bounded seeded roll-high d100 resolution;
- natural 01/100 outcomes and component-TL probability bounds;
- one attack package per installed direct-fire battery, fixed bay order, simultaneous commitment, initiative, voluntary delay, and overkill;
- range 0 at no penalty, provisional -5 percentage points per hex thereafter, and one Maximum Range gate;
- Evasive posture and component-specific Evasive Compensation;
- detection-versus-discrimination ECM, full non-consumable ECCM, and capped Cooperative ECM Screen support;
- observer-safe ECM presentation without hostile arithmetic disclosure;
- Missile Flight, search/wait, fuel, dud, seeker-assistance, and terminal-solution concepts;
- finite automatic PDS, low-TL Reaction Capacity 1, seeded overload selection, and a two-attempt-per-flight cap;
- deterministic shields, armor, hull/internal damage, critical outcomes, and hidden internal damage tracks;
- Operational, Disabled, and Destroyed ship states, including continued committed fire against Disabled ships, boarding, capture, suppression, and salvage direction; and
- one active current-checkpoint validation artifact with completed procedures moved to a tested archive.

These rules are documented current direction. Checkpoint 17b does not prematurely replace the existing deterministic combat demonstration with the full probabilistic combat and damage implementation.

## Validation-document policy

The previously cumulative `Baseline_Tactical_Regression_Encounter.md` is preserved as:

`docs/validation/archive/Tested_Tactical_Regression_Checkpoints_09_Through_17a.md`

The only active manual procedure is:

`docs/validation/archive/Checkpoint_17b_Partial_Validation_Results.md` (partial results; superseded by the active Checkpoint 17c runbook)

Historical regressions remain available but are rerun only when a relevant change or failure warrants them.

## Architecture

- `StarCluster.Core` remains authoritative and Godot-independent.
- `StarCluster.Tests` remains the engine-independent regression suite.
- `StarCluster.Game` owns only presentation, input, fixture selection, and development diagnostics.
- The hotfix does not transfer combat authority into Godot presentation code.

## Expected verification

- .NET SDK: `8.0.423`
- Expected complete suite: **490 tests**
- No new Core behavior or test-count change is expected.
- Godot manual validation follows the short Checkpoint 17b active runbook.

## Next substantive checkpoint

Checkpoint 18 should implement the unified Current/Firm terminal-solution gate and seeker-assisted terminal acquisition on top of the accepted launcher, retained-report, and onboard-navigation-sensor foundation. Probabilistic combat and complete layered damage should follow only after that terminal contract is stable.


## Superseded validation note

The 1280x800 Godot run showed that the 190-pixel minimum did not remain usable during the missile phase and that persistent friendly planning/history clutter remained ambiguous. Checkpoint 17c supersedes those presentation details while preserving this checkpoint as historical context.
