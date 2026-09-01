# StarCluster.Game

`StarCluster.Game` is the Godot 4.7.1 .NET presentation/input host for Star Cluster. Engine-independent combat, tracking, missile, damage, and rules logic belongs in `StarCluster.Core`; mechanical acceptance belongs primarily in `StarCluster.Tests` and `StarCluster.ScenarioRunner`.

## Current role

The Godot project is a tactical prototype and observer-safe presentation layer, not the source of design authority. Open `project.godot` in the Godot .NET editor. The project references `../StarCluster.Core/StarCluster.Core.csproj`.

The current system-combat sequence is:

1. Movement
2. Electronic Warfare
3. Direct Fire
4. Missile / Interception
5. Damage
6. Damage Control

Track Update is event-driven rather than a player action phase. The active Concept document under `docs/` and focused architecture notes under `docs/design/` define the current rules when this prototype has not yet exposed a newer mechanic in the UI.

The prototype uses the stable diagnostic identifier `tactical-prototype` rather than presenting an old development checkpoint number as if it were current rules authority. Automatic JSONL/readable logs remain under Godot `user://logs`.

## Architecture boundaries

- Direct-fire eligibility is owned by Core. Ordinary ship attacks require Firm; a specific weapon may explicitly support Approximate-track degraded fire, but its numerical penalty is supplied by an eligible Tactical Computer/fire-control profile.
- Main-weapon missile interception remains Firm-only.
- Launcher datalink, missile navigation sensor, terminal seeker, and missile terminal authority are separate Core capabilities.
- Friendly missile routes and detailed diagnostics are presentation/debug information; the Core missile state remains authoritative.
- Player-visible information must remain observer-safe and must not expose hidden enemy EW ratings or internal equations.

## Validation

Do not treat Godot smoke behavior as sufficient mechanical acceptance. Use the current checkpoint script under `tools/checkpoints/` for repository, build, unit-test, deterministic ScenarioRunner, and applicable calibration validation. Historical per-checkpoint presentation notes and commands are retained in `docs/archive/source-readmes/StarCluster.Game_README_checkpoint18_history.md`.
