# Checkpoint 77 - Architecture, Concept, and Runtime Scrub

## Intent

Checkpoint 77 is a consolidation checkpoint built on accepted Checkpoint 76. It adds no new Monte Carlo balance study and does not assign degraded fire to a production weapon. Its purpose is to make current design ownership explicit in both documentation and Core, remove stale development-era presentation/documentation, and tighten deterministic contracts around the architecture already selected by human review.

## Architecture changes

### Direct-fire degraded-fire ownership

The implementation now follows the current ownership split:

- `DirectFireWeaponProfile` owns only the explicit `AllowsApproximateTrackFire` capability flag.
- `TacticalComputerFireControlProfile` owns the ship fire-control penalty used when an enabled weapon attacks from an Approximate track.
- the TL1 architecture data defines a **25 percentage-point** degraded-fire penalty;
- a compatible weapon plus a supporting computer are both required before Approximate can satisfy ship-target direct-fire eligibility;
- Firm attacks receive no degraded-fire penalty;
- ordinary weapons remain Firm-only even with a supporting computer;
- loss/unavailability of the supporting computer removes the Approximate-track solution without disabling the weapon's ordinary Firm-track local/manual operation;
- main-weapon missile interception remains Firm-only.

No production weapon is enabled for degraded fire by this checkpoint. Exact Tactical Computer Degraded/Disabled/Destroyed behavior remains deferred until computer damage is designed holistically.

### Missile boundary

Ordinary missiles remain on the accepted Firm-terminal architecture. The Concept and missile architecture note now describe a possible Swarmer/volume-saturation direction more precisely: a future profile may expend a larger barrage into an Approximate target volume and accept a substantial missile-specific effectiveness cost. Whether that cost becomes lower terminal accuracy, reduced effective attack strength, larger ammunition/flight expenditure, seeker/search behavior, or a combination remains deferred. No missile Approximate-target attack is implemented here.

### Technology progression guardrail

Tactical Computer, Sensors, ECM, and ECCM evolve independently. Later computer TLs are not assumed to improve degraded fire on a fixed linear schedule. Any later breakpoint must be revalidated in its contemporary Sensor/EW/Tactical Power environment and must preserve the economic/tactical value of restoring Firm through ECCM.

## Documentation/runtime scrub

Checkpoint 77 also:

- promotes Concept `Star_Cluster_Game_Concept_v0.6p.docx` and removes obsolete checkpoint-history wording from current-rule/glossary text in the active Concept while preserving the generic checkpoint-validation process;
- replaces stale Checkpoint-18 Godot README/presentation labeling with stable tactical-prototype language and archives the historical README;
- replaces the accumulated ScenarioRunner checkpoint-command README with a concise current architecture/validation guide and archives the historical command log;
- replaces the accumulated calibration-harness checkpoint chronology with a concise current harness/tier guide and archives the historical README;
- refreshes `docs/design/player_technology/README.md` so it points to current authority rather than an old Checkpoint 69d state;
- adds `docs/design/README.md` as a current authority/navigation map so retained historical design files cannot masquerade as current rules;
- refreshes the AI Doctrine Registry architecture and Technology Calibration architecture with current degraded-fire ownership and explicit current-vs-historical interpretation boundaries;
- moves the accumulated Technology Calibration checkpoint chronology into `docs/archive/design-architecture/Technology_Calibration_And_Simulation_Architecture_historical_checkpoint_evolution.md` and keeps the active calibration architecture concise and current;
- adds `docs/design/testing/README.md` explaining current-vs-historical validation artifacts;
- retains historical study inputs and checkpoint files at stable paths where reproducibility depends on them rather than deleting them merely because they are old;
- removes the obsolete weapon-aware overload of `DirectFireTrackEligibility`; weapon/computer degraded-fire eligibility now has one authoritative resolver in `DirectFireTargetEligibility`;
- removes stale checkpoint identity from active Core/Game presentation comments and names and from current-behavior ScenarioRunner comments while preserving the frozen `checkpoint-19` diagnostic value under an explicitly named compatibility contract so deterministic historical outputs do not change.

The ScenarioRunner's retained integrated-combat penalty fields remain frozen historical study inputs. Current architecture interprets them as Tactical Computer penalty candidates for explicitly enabled study weapons, not as production weapon-profile-owned numbers.

## Normal acceptance

The normal CP77 suite intentionally contains **no Monte Carlo workload**. Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-77\apply_checkpoint_77.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-77\apply_checkpoint_77.ps1 -Jobs 24
```

Expected normal acceptance:

- pinned .NET SDK 8.0.423;
- warning-as-error build with zero warnings/errors;
- approximately **863 unit tests** if no unrelated test-count changes occurred;
- 8 deterministic/architecture runner stages;
- 47 ScenarioRunner self-tests;
- zero Monte Carlo variants/trials;
- zero failed deterministic release gates or runner errors.

## Deep Calibration

Deep Calibration remains opt-in. CP77 deliberately does not rerun CP76's degraded-fire/ECCM Monte Carlo because the accepted -25 TL1 value is being reassigned to its correct owning architecture, not numerically retuned. Run Deep Calibration only if native acceptance exposes a behavioral regression or a later mechanics change invalidates declared evidence dependencies.

