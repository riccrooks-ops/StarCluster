# Checkpoint 115a - Weapon-Family Substantive-Gate Hotfix

## Purpose

CP115a corrects an acceptance-harness defect discovered on the first native CP115 substantive invocation. `-RepositoryOnly` passed all 64 Python self-tests, all 25 C#/Python parity fixtures, the complete 4,064-variant one-trial smoke, and the repository/evidence contract. The 8.128-million-engagement invocation then exited nonzero because the CP115 analysis layer treated **natural occurrence of an adaptive payload switch** as a blocking substantive gate.

That gate was invalid. CP115's own checked-in 20-trial authoring evidence contains 384 adaptive-pair rows and **zero natural switch rows** because contemporary GP payloads frequently penetrate enough that observer-safe doctrine correctly remains on GP. A deterministic unit probe already proves that the doctrine switches to the specialist when the permitted observed-Shield/no-penetration trigger is explicitly present.

## Hotfix scope

CP115a changes acceptance/research-analysis validation semantics only:

- removes the stochastic `adaptive-pair-switch-telemetry` blocking gate;
- records adaptive-pair row/switch counts as **information-only telemetry**;
- retains and strengthens the deterministic non-switch/switch doctrine probe;
- adds a pre-substantive AST/static gate-policy check that rejects trial-count-dependent blocking gates in the CP115 weapon-family analysis path;
- verifies the checked-in bounded evidence still contains 384 adaptive rows / 0 natural switch rows and treats that state as valid;
- captures research CLI output to log files and, on failure, prints failed gates/errors plus the output tail instead of hiding the diagnostic behind `Out-Null`.

## Explicit non-changes

CP115a does **not** change:

- the 4,064-variant CP115 population;
- any Missile/Kinetic/Energy candidate profile or target fixture;
- attack, payload, tandem, saturation, movement, Sensor/EW, PDS, Shield/Armor/Hull, or Reactor-overload mechanics;
- the `layered_defense_hull_only` boundary;
- CP109/CP110 numerical candidates;
- Concept v0.7k;
- production C#/Godot source;
- the substantive workload of 2,000 trials/variant = **8,128,000 engagements**.

The CP115 study JSON remains byte-identical to the failed package. CP115a is therefore an acceptance-harness hotfix, not a new balance experiment.

## Failure-class guardrail

Blocking release/acceptance gates must be deterministic structural/integrity requirements or explicit predeclared policy conditions. A stochastic event being *possible* is verified through deterministic trigger probes; the event is not required to occur naturally in a Monte Carlo population unless natural occurrence is itself the scientific hypothesis and is expressed as a non-blocking result metric.

The CP115a preflight AST-inspects the weapon-family analysis for blocking `failures.append(...)` gates conditioned on `trials`, rejects the obsolete switch gate by name, and verifies the deterministic adaptive doctrine trigger test remains present.

## Native validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-115a\apply_checkpoint_115a.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-115a\apply_checkpoint_115a.ps1
```

`-RepositoryOnly` runs repository hygiene, the new substantive-gate preflight, all 64 Python self-tests, all 25 parity fixtures, the complete 4,064-variant one-trial smoke, and the CP115a repository contract.

The normal invocation additionally runs the unchanged 8.128-million-engagement CP115 substantive study. If the research CLI exits nonzero, the wrapper now prints the actual failed gate/error and an output-log tail before raising the PowerShell exception.

No candidate promotes automatically.
