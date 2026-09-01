# Checkpoint 113 - Weapon Ammunition / Warhead Architecture and Documentation Hygiene

## Purpose
Reconcile the already-preserved Kinetic ammunition and Missile warhead technology axes before payload/Shield calibration, and restore a clear active-vs-archived documentation boundary.

## Authority changes
- Concept advances to v0.7k for ammunition/warhead expression, compatibility, generic inventory, observer-safe combat assessment, and sparse auto-unlocking prerequisites.
- Storyboard advances to v1.3 without changing the 10-discipline / 32-lineage / 214-beat structure.
- Idea Register advances to v1.4 with 137 ideas: the Antimatter-Catalyzed Warhead remains distinct and a missing Fusion Microcharge GP anchor is added.
- Foundation Audit advances to v1.3; qualitative Technology Table advances to v0.3.
- CP109 numerical matrix and CP110 Reactor candidate values remain unchanged. Several uncalibrated CP109 payload branch candidates are explicitly suspended from balance inference rather than silently rewritten.

## Ammunition / warhead contracts
- Energy flexibility remains power/output-mode driven.
- Strictly superior compatible Kinetic ammunition matures automatically; selectable Kinetic modes require a real tradeoff.
- Missile warheads may remain mission-specific selectable payloads; a normal warhead is committed at launch.
- Compatibility is explicit by weapon/flight family.
- Normal Kinetic and Missile variants use broad generic magazines; no pre-battle subtype quantities. Rare/Exotic ammunition may be individually counted when scarcity is gameplay.
- Observer-safe Firm-track combat assessment may reveal qualitative shield absorption/collapse, armor contact, Hull penetration, or lack of observed penetration, but never exact hidden defense arithmetic. AI receives the same derived information.
- Anti-shield payload calibration must test cumulative shield pressure/recharge and contextual tradeoffs, not paper SPEN alone.
- Internal-effect/radiation payloads remain deferred until the internal critical/subsystem research consumer exists.

## Documentation hygiene
Superseded Concepts, validation runbooks, human-facing technology versions, completed study reports/workbooks, and old validation-tier documents are archived under `docs/archive/`. Active directories retain current authority, reusable executable study definitions, and explicitly documented compatibility/runtime-consumed machine-readable snapshots.

## Validation
Both commands run deterministic Python architecture validation only; CP113 has no substantive simulation stage.

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-113\apply_checkpoint_113.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-113\apply_checkpoint_113.ps1
```

Expected result: zero Monte Carlo trials, no numerical promotion, no C#/Godot or simulation-source drift, and a verified full-repository manifest.
