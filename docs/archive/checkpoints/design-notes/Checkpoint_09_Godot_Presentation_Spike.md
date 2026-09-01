# Star Cluster - Checkpoint 09: Godot Presentation Spike

## Purpose

Checkpoint 09 performs the first integration between the tested,
engine-independent `StarCluster.Core` library and Godot 4.7.1 .NET.

The checkpoint deliberately uses only simple procedural shapes, lines, text,
and standard Godot controls. It introduces no sprites, art pipeline,
animations, sound, physics, or duplicated game rules. The purpose is to test
whether the selected engine and C# workflow are comfortable before additional
combat systems are built.

## Architecture

The dependency remains one-way:

```text
StarCluster.Game  ->  StarCluster.Core
StarCluster.Core  ->  no Godot dependency
```

`StarCluster.Core` decides:

- which hexes exist;
- which objects occupy them;
- whether direct fire is Clear, Grazing, or Blocked;
- how many separate grazings occur;
- which body blocks a shot;
- whether a missile route exists;
- routed distance and launch range status;
- missile travel speed, position, and arrival state.

Godot only:

- converts axial coordinates to screen positions;
- draws the 11-across system map;
- draws simple stars, planets, ships, lines, and route overlays;
- converts mouse positions back to axial coordinates for inspection;
- displays results returned by the core library;
- represents an in-flight logical missile salvo with an asterisk.

## Prototype display

The main scene provides four repeatable layouts:

1. Clear direct fire
2. Single grazing
3. Multiple grazings
4. Direct fire blocked by the central star with a legal indirect missile route

The right-side controls allow the user to:

- select a demonstration layout;
- switch between direct-fire and missile-route overlays;
- show or hide axial coordinates;
- launch or reset a logical missile salvo;
- advance the salvo one missile-movement turn at a time;
- hover over a hex to see its coordinate;
- click a hex to inspect logical terrain and occupants.

## Prototype symbols

No external assets are required.

```text
Star             filled circle and ring
Planet           smaller circle
Player ship      green triangle and ring
Enemy ship       red triangle and ring
Missile salvo    asterisk (*)
Direct-fire line color reflects Clear, Grazing, or Blocked
Missile path     connected route through axial cell centers
```

These symbols are explicitly temporary. Their purpose is to make the logical
state visible without prematurely creating final presentation assets.

## Godot project

The checkpoint adds:

```text
src\StarCluster.Game\
    StarCluster.Game.csproj
    project.godot
    Scenes\Main.tscn
    Scripts\Main.cs
    Scripts\HexBoardView.cs
    Scripts\DemoScenario.cs
    Scripts\DemoScenarioFactory.cs
    Scripts\TargetingMode.cs
```

`StarCluster.Game.csproj` targets .NET 8, uses `Godot.NET.Sdk/4.7.1`, and
references `StarCluster.Core` through a normal project reference.

## Installation

Extract the archive directly into:

`E:\dev\star-cluster`

Allow it to merge with the existing `src`, `tools`, and `docs` folders. Then
run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-09\apply_checkpoint_09.ps1
```

The script:

1. verifies Checkpoint 08;
2. confirms the pinned .NET 8 SDK;
3. verifies the Godot project files;
4. adds `StarCluster.Game` to `StarCluster.sln` when needed;
5. builds the complete solution, including the Godot C# project;
6. runs the existing 208 engine-independent tests;
7. confirms the one-way project reference and documentation state.

The first build may take longer than prior checkpoints because NuGet may need
to restore the Godot .NET SDK package.

## First launch in Godot

After the script succeeds:

1. Start the Godot 4.7.1 .NET editor.
2. In the Project Manager, select **Import**.
3. Browse to:

   `E:\dev\star-cluster\src\StarCluster.Game\project.godot`

4. Import and open the project.
5. Allow Godot to scan and build the C# project if prompted.
6. Press **F6** only when the open scene is `Main.tscn`, or press **F5** to run
   the configured main scene.
7. Exercise all four scenarios and both overlay modes.
8. Launch the missile in the blocked scenario and advance turns. The asterisk
   should follow the core-generated route around the star.

## Visual Studio workflow

Godot should remain configured to use Visual Studio 2022 as the external C#
editor.

After the project is imported:

1. Open `StarCluster.sln` in Visual Studio 2022.
2. Confirm `StarCluster.Game` appears under the `src` solution folder.
3. Set a breakpoint in `Main.LoadScenario` or
   `HexBoardView._GuiInput`.
4. Run the Godot project from the editor.
5. For a later debugging exercise, attach Visual Studio to the running Godot
   process if direct launch debugging is not yet configured.

The immediate checkpoint only requires that scripts open in Visual Studio and
that normal C# build errors are visible there. A polished debug-launch profile
is not required yet.

## Expected command-line result

A successful installation should end with:

```text
Checkpoint 09 completed successfully.
Existing core tests passed: 208 expected.
Next step: import src\StarCluster.Game\project.godot in Godot 4.7.1 .NET.
```

## Acceptance criteria

- `StarCluster.Game` is present in `StarCluster.sln` under `src`.
- The complete solution builds with zero errors.
- Preferably, zero compiler warnings are reported.
- All 208 existing tests pass.
- Godot imports the project without C# errors.
- Running the project displays an 11-across pointy-top hex map.
- The central star is at axial `(0,0)`.
- Hovering resolves to the correct axial coordinate.
- Clicking a hex reports its core terrain and occupants.
- The four preset layouts report the expected core LOS result.
- The multiple-grazing scenario reports two grazings.
- The blocked scenario shows direct fire blocked by the star.
- The blocked scenario shows a longer missile route around the star.
- Launching creates a logical missile salvo at the player ship.
- Each turn moves the asterisk by at most the profile speed.
- The asterisk eventually reaches the target coordinate.
- No sprite, sound, animation, physics, or final asset work is introduced.
- `StarCluster.Core` still contains no Godot dependency.

## Deliberately deferred

- tactical ship movement commands;
- turn sequencing beyond advancing a missile flight;
- movement costs and propulsion TL;
- target selection beyond fixed prototype endpoints;
- sensor contacts and target tracks;
- point-defense and energy-weapon interception;
- missile guidance replanning;
- attack rolls and damage;
- final visual design, sprites, animation, audio, and effects.

## Next likely checkpoint

After the Godot spike is reviewed, the likely next pass is an
engine-independent tactical ship-movement model with legal destinations,
propulsion allowance, command results, and a Godot overlay driven by those
results.

Concept v0.3a remains current. The use of simple shapes and an asterisk is a
prototype implementation choice rather than a material change to the game
concept.
