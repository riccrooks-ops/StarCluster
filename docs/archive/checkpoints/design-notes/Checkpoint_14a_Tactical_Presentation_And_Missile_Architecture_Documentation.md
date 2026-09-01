# Checkpoint 14a — Tactical Presentation and Missile-Architecture Documentation

## Purpose

Checkpoint 14a is a narrow hotfix and documentation pass following local validation of Checkpoint 14. It does not introduce missile onboard sensors, datalinks, seekers, incremental movement, or new combat outcomes.

It addresses five accepted presentation issues while preserving all 440 engine-independent tests and the Checkpoint 14 sensor/EW rules:

- remove right-panel horizontal clipping at the 1280×800 reference viewport and the observed 1274×796 client area;
- show a compact directional sensor/EW calculation for both observer-target relationships;
- clarify the meaning of the four Sensor / EW development controls;
- distinguish Approximate contacts without relying on color alone;
- hide historical missile trails until the specific salvo is selected;
- correct Approximate-versus-Stale missile wait diagnostics.

It also records the detailed accepted future architecture for hybrid ship movement, launcher datalinks, missile onboard sensors, terminal seekers, per-hex reacquisition, same-hex terminal gating, and overshoot tactics.

## Godot presentation changes

### Responsive side panel

- The fixed tactical side-panel host is reduced to 420 pixels.
- Scroll content no longer declares a competing 400-pixel minimum width inside its margins and scrollbar.
- wrapped labels and section headings have zero custom minimum width and do not clip text;
- the scenario selector no longer sizes itself to the longest item and trims only its selected caption if necessary;
- Sensor / EW check boxes use short labels with explanatory tooltips and nearby wrapped directional guidance.

The tactical board remains independent of changing right-panel content.

### Compact directional sensor/EW summary

A new status block displays both relationships explicitly:

- `PLAYER -> ENEMY`
- `ENEMY -> PLAYER`

Each line includes final evaluation, distance, base-to-effective Firm and Approximate ranges, mode modifier, target-signature modifier, environment penalty, and raw/counter/net jamming arithmetic.

### Approximate-contact cue

Approximate ships and missile stacks now display:

- a segmented uncertainty ring; and
- an `APPROX` text tag.

The cue therefore remains identifiable when the amber/red/green color difference is difficult to discern.

### Historical missile trails

Observed historical trails are hidden for unselected salvos. Selecting a salvo reveals all of its observer-confirmed trail segments. Stale selected trails are dimmer. Existing observer-safe rules remain unchanged:

- hidden movement is never reconstructed;
- disconnected segments remain disconnected;
- active projected threat routes remain separate from historical trails;
- terminal salvos leave the active display.

### Guidance wording

A missile that reaches an Approximate estimated coordinate now records `MovedToApproximateCoordinate` and an Approximate-specific wait reason. A missile that reaches a Stale report retains `MovedToLastKnownCoordinate` and a Stale-specific reacquisition reason.

## Documentation changes

- Current concept becomes `Star_Cluster_Game_Concept_v0.3l.docx`.
- Exact v0.3k is preserved under `docs/archive/`.
- `docs/design/Missile_Guidance_Datalink_Sensor_And_Seeker_Architecture.md` records the accepted implementation contract.
- The concept Decision Register adds hybrid movement, datalink, missile-sensor, seeker, same-hex, movement-edge observation, and overshoot decisions.
- The validation runbook adds focused Checkpoint 14a presentation checks.

## Tests

No engine-independent simulation rule changes are introduced. Expected complete suite after application remains **440 tests**.

## Local validation

Close Godot, extract the package into the repository root, then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-14a\apply_checkpoint_14a.ps1
```

Then run the Checkpoint 14a section of `docs\validation\Baseline_Tactical_Regression_Encounter.md`.

## Next implementation sequence

1. Incremental/hybrid tactical ship movement: one-hex steps or any reachable destination, with every intermediate hex resolving authoritatively.
2. Missile datalink, onboard-sensor, seeker, track-arbitration, reacquisition, search, and terminal-lock foundations.
3. TL-specific missile families and balance after the architecture is validated.
