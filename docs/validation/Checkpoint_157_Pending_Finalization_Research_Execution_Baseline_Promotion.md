# Checkpoint 157 — Pending-Finalization Research Execution Baseline Promotion

> **CR1 handoff correction:** the initial CP157 archive invoked the package-internal `starcluster_research/cli.py` directly during the parity gate, causing Python relative-import failure before parity execution. CR1 restores the established package-safe `tools/simulation/run_starcluster_research.py` entrypoint and adds a preflight/focused-test guard. CP157-PF1, all numerical values, authority boundaries, and the zero-combat contract are unchanged.

CP157 is a zero-combat authority-boundary checkpoint. It promotes selected native-validated research findings into a canonical **Pending-Finalization Research Execution Baseline** (`CP157-PF1`) while preserving `technology_numerical_matrix_v0_9.json` as the separate production numerical authority.

## Purpose

Future substantive balance studies must not reconstruct the current state from an old production matrix plus an implicit chain of overlays. CP157 materializes the exact current research execution state as one matrix and makes that matrix the mandatory starting point for subsequent balance work.

## Selected execution center

- Kinetic Main: K1
- Energy Main: E7
- GP Missile: M2 (M3 retained as required alternate)
- Swarmer: SW2
- Kinetic PDS: K155P06 (K155P03 retained as required economic/strength alternate)
- Energy PDS: E155P08 (E155P07 retained as required SL1 alternate)
- AMM: A155P07 (A155P09 retained as a later-RC3 alternate)
- Defensive core: CP142 combat reconciliation carried through the CP151 x2 point scale
- Reactor/TP: CP144 central resource environment, explicitly provisional scaffolding pending the final TP pass
- AUX: current executable/proxy environment; lifecycle viability remains the next substantive task

## Authority rule

`technology_research_execution_baseline_pending_finalization_v0_1.json` is research execution authority, not final production authority. All post-CP157 substantive balance studies must load it through `research_execution_baseline.load_research_execution_baseline`. Raw `technology_numerical_matrix_v0_9.json` is permitted only for historical/control validation unless a checkpoint explicitly declares and validates a controlled exception.

## No combat / no finalization

CP157 performs zero substantive combats and does not claim final balance. It changes the research execution authority only. Final production promotion remains deferred until AUX lifecycle viability and Reactor/TP whole-ship equilibrium are closed.
