# Star Cluster - Checkpoint 09a: Godot Layout Hotfix

## Purpose

Checkpoint 09 proved that the Godot presentation can consume the independently
tested `StarCluster.Core` results. The first live run also exposed two
presentation defects at the prototype's 1280 x 800 logical resolution:

- the right-side content imposed a minimum height larger than the window,
  causing the board control to become taller than the visible viewport and
  clipping the lower map rows;
- hover information was updated in a label near the bottom of that same
  oversized panel, so it was not visible without scrolling.

Checkpoint 09a fixes those defects without changing any authoritative game
rules.

## Changes

### Scrollable right panel

The information panel now uses a Godot `ScrollContainer`. Its contents can be
longer than the current window without increasing the height of the main
`HBoxContainer`.

This keeps the map control within the visible viewport and makes the missile
buttons, pointer details, and long grazing/blockage reports reachable at modest
window sizes.

### Responsive board fitting

`HexBoardView` now:

- reserves a small status area at the top of the board;
- calculates the complete pixel bounds of all 91 system-map hexes;
- selects the largest hex radius that fits both the available width and height;
- centers the board in the remaining rectangle;
- removes the old minimum hex-size clamp that could force geometry outside the
  control;
- clips drawing and pointer input to the board control;
- hides coordinate labels automatically only when the fitted hex size becomes
  too small to read.

The board recalculates its layout whenever the Godot control is resized.

### Always-visible pointer status

The board now draws a status banner across its top edge. Hovering a hex shows:

- axial coordinate;
- terrain;
- occupants.

When the pointer leaves the map, the banner retains the most recently selected
hex summary when one exists. The same information remains available in the
scrollable side panel.

### Godot configuration corrections

The delivered `project.godot` now explicitly contains:

```ini
[dotnet]

project/assembly_name="StarCluster.Game"
```

The display name remains `Star Cluster Prototype`; the managed assembly name
must match `StarCluster.Game.dll`.

The project also explicitly uses `canvas_items` stretch mode with `expand`
aspect behavior so the Control layout can make use of varying desktop window
sizes and aspect ratios.

### Conservative scene-script namespace

The scene-attached `Main.cs` class remains in the global namespace for this
hotfix. Supporting presentation classes remain under `StarCluster.Game`. This
avoids reintroducing a second variable while validating the corrected assembly
registration and layout behavior. A later cleanup may restore the entry class
to the project namespace after a dedicated verification.

### Installation verification

The Checkpoint 09a script:

- verifies the corrected assembly name in both the project and MSBuild output;
- uses `dotnet sln ... list` for solution-membership verification rather than
  parsing the raw `.sln` text;
- clears generated Godot managed metadata before rebuilding;
- builds all three projects;
- reruns the existing 208 engine-independent tests;
- verifies that `StarCluster.Core` still has no Godot dependency.

## Expected visual result

At 1280 x 800:

- all 91 hexes should be visible;
- the board should be centered below the hover banner;
- the panel should show a vertical scrollbar when needed;
- the missile buttons should be reachable by scrolling;
- hover information should update immediately at the top of the board;
- clicking a hex should still apply the light selection fill and update the
  detailed side-panel text.

The same layout should remain usable when the embedded game window is resized
or maximized on a 4K display.

## Acceptance criteria

- The complete solution builds with zero errors.
- Preferably, zero warnings are reported.
- All 208 existing tests pass.
- Godot launches without the C# class-association error.
- The lower map rows are no longer clipped at 1280 x 800.
- Excessive blank space above the board is removed.
- The right panel scrolls vertically.
- `Launch / reset` and `Advance turn` are reachable.
- Hovering visibly reports the correct coordinate, terrain, and occupants in
  the board banner.
- Clicking a hex continues to select and inspect it.
- The four LOS scenarios still report their prior results.
- Missile route and turn advancement still work.
- `StarCluster.Core` remains independent of Godot.

Concept v0.3a remains current because this hotfix changes presentation and
project configuration, not the game design.
