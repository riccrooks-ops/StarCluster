# Checkpoint 22d - Accepted Baseline Closure and Checkpoint 23 Handoff

## Status

**Accepted repository baseline.** Checkpoint 22d contains no gameplay or
simulation-mechanics change. It promotes the successful Checkpoint 22c
implementation and reviewed evidence, closes the Checkpoint 22 performance
program, and establishes the complete-archive release contract for subsequent
work.

Packaging revision 2 retains the revision-1 interpolation/parser repair and
adds runtime validation of the active-runbook lifecycle. Complete archives do
not delete files when extracted over an existing working tree, so the 22d
script now archives stale top-level `Checkpoint_*.md` validation runbooks,
self-tests both collision and normalization behavior, and exposes a
`-RepositoryContractOnly` native-PowerShell preflight. This is a packaging and
validation repair only.

Checkpoint 21e remains the frozen behavioral reference. Checkpoints 22 and 22a
are superseded failed/intermediate implementations; Checkpoint 22b remains the
diagnostic evidence that selected the final repair; Checkpoint 22c is the
accepted implementation and performance result.

## Accepted Checkpoint 22c evidence

The accepted local run established:

- clean warning-as-error compilation under .NET SDK 8.0.423;
- 506 engine-independent tests;
- seven deterministic headless scenarios;
- 46 ScenarioRunner self-tests;
- 288/288 optimized maps matching radius-192 reference variants;
- an optimized radius range of 30 through 102 and average cell retention of
  4.71 percent;
- 93.97 percent profiled compact allocation reduction versus Checkpoint 22b;
- 4.95x jobs-24 compact scheduler-proof speedup;
- 93.72 percent full-run allocation reduction versus Checkpoint 21e;
- 91.13 percent full-run Gen 2 collection reduction;
- exact Checkpoint 21e summary and marginal CSV reproduction;
- 288 passing full-flight variants, 720 verified inferential paired marginals,
  144 descriptive relative-motion marginals, and zero mechanical failures; and
- canonical result hash
  `226677d3b9d2fded9e529ab5b897f6ec0e5251eb27937208f571cbb9b184ee28`.

The reviewed console output and complete result archive are preserved under
`docs/validation/evidence/checkpoint-22c-accepted/`.

## Accepted implementation contract

Generated full-flight calibration scenarios use a deterministic per-variant map
radius derived from the complete explicit coordinate envelope plus two hexes.
Ordinary gameplay map sizing is unchanged. Radius 192 remains a parity-only
reference mode.

High-volume full-flight calibration uses compact direct metrics with fresh
mutable authoritative state per trial. Diagnostic execution remains the semantic
reference. Immutable preparation may be shared; maps, ships, tracks, Missile
Flights, turn state, and interception context may not be shared between trials.

The frozen Checkpoint 22b compact baseline is 20,863,918 bytes/trial. Future
performance changes must keep compact allocation at or below 4,172,784
bytes/trial unless an explicitly reviewed successor gate replaces it. Accepted
behavioral summary and marginal CSV hashes remain locked to the Checkpoint 21e
references.

## Complete-archive release contract

Beginning with Checkpoint 22d, every checkpoint and hotfix must be delivered as
a complete repository archive rather than an overlay-only package. Each archive
must contain:

- `StarCluster.sln`, `global.json`, and every project file;
- the complete `src/`, `tests/`, `docs/`, and `tools/` trees;
- the current concept and archived concept documents;
- the complete reference library and its checksum file;
- exactly one active validation runbook directly under `docs/validation/`;
- the checkpoint application/validation script; and
- a repository SHA-256 manifest.

Release preparation must extract the candidate into an empty staging directory,
verify the manifest, parse every packaged `.ps1` with the native PowerShell
parser, execute the checkpoint script through its repository-contract preflight,
run a stale-runbook normalization self-test, reject ambiguous interpolations such
as `$variable:` unless the variable is delimited as `${variable}:`, delete
generated `bin`, `obj`, and Godot Mono temporary state, and pass a clean
warning-as-error solution build before handoff. Archive validation must also test
an extraction-over-existing-tree case because ZIP extraction does not remove
stale files.
A package that depends on an earlier overlay chain is not a valid checkpoint
archive.

## Checkpoint 23 handoff

Checkpoint 23 will decompose the provisional bundled Missile Flight TL into
independently controlled study inputs for:

- flight propulsion and endurance;
- launcher datalink;
- onboard navigation sensor;
- Guidance Computer; and
- terminal seeker.

The first study will use a controlled one-factor-at-a-time matrix around the
provisional TL-4 package with TL 2, 4, and 6 values, plus only selected
mechanically justified interactions. A locked legacy-parity lane must reproduce
the Checkpoint 22d bundled-TL behavior before any new sensitivity result is
interpreted. Component absence remains absence rather than receiving a synthetic
TL.

Checkpoint 23 is an evidence and decomposition pass. It must identify dead
levels, cliffs, dominant effects, and interactions without prematurely promoting
provisional TL values to production rules.

## Validation

Run the sole active procedure:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22d\apply_checkpoint_22d.ps1
```

No mechanical Godot validation is required because Checkpoint 22d changes only
repository closure, documentation, packaging, and validation status.

## Packaging revision 2 validation repair

Revision 2 corrects the false assumption that extracting a complete archive over
an existing repository removes the previous active validation runbook. The
script now preserves nonidentical stale runbooks under `docs/validation/archive/`
with a unique imported suffix, removes exact duplicates already archived, and
then verifies that only the Checkpoint 22d runbook remains active.

The lightweight runtime path is:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22d\apply_checkpoint_22d.ps1 -RepositoryContractOnly
```

## Native release-candidate validator

The complete repository includes:

```text
tools/checkpoints/checkpoint-22d/validate_checkpoint_22d_release.ps1
```

Run it against the finished ZIP on Windows PowerShell before handoff. It extracts
the archive into a disposable directory, executes `-RepositoryContractOnly` on
the clean extraction, injects a stale Checkpoint 22c active runbook, repeats the
preflight, and requires normalization back to the sole Checkpoint 22d runbook.
This runtime gate is distinct from parser-only validation.
