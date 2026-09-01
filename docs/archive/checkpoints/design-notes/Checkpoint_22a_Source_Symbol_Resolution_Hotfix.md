# Checkpoint 22a - Source-Symbol Resolution Hotfix

## Purpose

Checkpoint 22a repairs two source-symbol mistakes that prevented the Checkpoint
22 acceptance build from compiling `StarCluster.ScenarioRunner`. No simulation,
Monte Carlo, scheduler, allocation, random-stream, statistical, or Godot behavior
changes.

## SensorMode namespace repair

`ScenarioExecutionMetrics` referenced `SensorMode.Active` through
`StarCluster.Core.Combat`, but `SensorMode` is declared in
`StarCluster.Core.Combat.Tracking`. The metric now uses the authoritative fully
qualified symbol:

```csharp
StarCluster.Core.Combat.Tracking.SensorMode.Active
```

## Serializer option repair

The compact-versus-diagnostic parity self-test retained the obsolete
`ScenarioDocumentSerialization.WriteOptions` member name after serialization
options were split into compact and indented forms. Both canonical trial
serializations now use:

```csharp
ScenarioDocumentSerialization.CompactWriteOptions
```

This preserves the test's intended compact canonical representation.

## Prevention gate

The corrected Checkpoint 22 apply script now checks both valid symbols and
rejects the two stale forms before beginning the solution build. This gives a
clear source-contract error if the wrong files are present.

For future checkpoint authoring, the definitive prevention step is a clean
compiler preflight against a disposable copy of the accepted baseline after the
candidate overlay is applied and before the archive is released:

1. delete `bin`, `obj`, and Godot Mono temporary output;
2. run `dotnet build .\StarCluster.sln --nologo -warnaserror` with the pinned SDK;
3. run the engine-independent tests and runner self-tests; and
4. package only the exact tree that passed those checks.

Namespace and renamed-member defects are compiler-resolved facts, so a clean
warning-as-error build is more general and reliable than a list of textual
namespace checks. The textual guards remain useful defense in depth for known
regressions.

## Validation

Checkpoint 22a delegates to the complete corrected Checkpoint 22 acceptance
sequence: warning-as-error solution build, 506 engine-independent tests, seven
deterministic scenarios, forty-one runner self-tests, reproducibility and
compact-mode parity proofs, allocation and scaling gates, and the unchanged
288-variant calibration.

No mechanical Godot validation is required.
