# Checkpoint 17c validation — presentation correction, Concept v0.3r, and reference handoff

This is the only active manual validation procedure for Checkpoint 17c. The partially completed Checkpoint 17b results are preserved under `docs/validation/archive/Checkpoint_17b_Partial_Validation_Results.md`; completed Checkpoint 09 through 17a procedures remain in the tested archive.

## A. Apply, build, and test

1. Close the Godot editor and any running Star Cluster debug window.
2. Extract the complete Checkpoint 17c archive into the repository root.
3. Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-17c\apply_checkpoint_17c.ps1
```

4. Confirm .NET SDK `8.0.423`, a warning-free build, and **490 passed tests**.
5. Reopen `src\StarCluster.Game\project.godot` and press **F5**.
6. Confirm the title and automatic log filenames use `checkpoint-17c`.
7. Confirm the default window is approximately `1440x900` and remains fully visible on the current desktop.

## B. AUTHORITATIVE DEBUG correction

Use **Missile local-sensor occlusion** or another scenario with a visible hostile missile.

1. Advance to Missile / Interception and select the hostile missile.
2. Confirm the **AUTHORITATIVE DEBUG** toggle is visible above the scrollable detail pane without scrolling to find it.
3. Enable the toggle.
4. Confirm the detail pane remains substantially taller than the three-to-four-line Checkpoint 17b result.
5. Confirm the pane automatically scrolls to the selected missile's authoritative section after the layout update.
6. Review actual coordinate, lifetime range, datalink state, retained report, local report, selected guidance source, replan count, and observation-step sequence.
7. Disable the toggle and confirm all authoritative hostile details disappear.

Notes/result: ________________________________________________

Screenshot names: ___________________________________________

## C. Friendly Missile Flight decluttering

Use **Friendly missile route validation**.

1. Keep sensors Passive and jammers Off; advance to Missile / Interception.
2. Select the enemy ship and launch one player Missile Flight.
3. Deselect the friendly Missile Flight. Confirm no persistent dashed friendly future route and no historical trail are drawn.
4. Hover the friendly Missile Flight. Confirm the player-owned summary includes its status, assigned target, and remaining/max range.
5. Select the friendly Missile Flight. Confirm its current future plan appears as a dashed green targeting/guidance line.
6. Confirm any solid green line depicts only completed historical travel between entered hexes, not a second future path to the target.
7. Deselect it again and confirm the dashed plan and selected-only trail disappear.
8. Launch one hostile Missile Flight. Confirm its incoming-threat estimate remains dotted and visually distinct.
9. Confirm normal text explains that the hostile dotted estimate does not prove enemy lock, datalink, or actual guidance coordinate.

Notes/result: ________________________________________________

Screenshot names: ___________________________________________

## D. Observer-safe boundary checks carried from 17b

1. With AUTHORITATIVE DEBUG off, inspect a hostile missile and confirm normal player-facing text does **not** reveal actual hidden coordinate, retained report, datalink state, local-sensor truth, arbitration candidates, selected authoritative source, or replan truth.
2. Use a scenario with enemy ECM/jamming active. Confirm the normal UI may show active/off state, qualitative interference, and resulting track quality, but does **not** reveal exact hostile ECM rating, Cooperative ECM Screen, observer ECCM, emitter count, or net arithmetic.
3. Enable AUTHORITATIVE DEBUG only long enough to confirm the hidden values exist there, then disable it and confirm they disappear again.

Notes/result: ________________________________________________

Screenshot names: ___________________________________________

## E. Concept and reference handoff

1. Confirm `docs/Star_Cluster_Game_Concept_v0.3r.docx` is the only current Concept document in `docs/`.
2. Confirm `docs/archive/Star_Cluster_Game_Concept_v0.3q.docx` preserves the prior accepted revision.
3. Open the current Concept and spot-check:
   - Hull TL versus Armor TL;
   - Tactical Power and reactor states;
   - Damage Control and 40% base Hull repair;
   - Ready Packages and magazine families;
   - Integrated / Adapted / Incompatible installations;
   - selected-only friendly missile guidance; and
   - Decision Register entries D-143 through D-167.
4. Confirm `docs/references/README.md` and `docs/references/SHA256SUMS.txt` exist.
5. Confirm all twelve packaged reference files are present under `docs/references/`.
6. Confirm only this Checkpoint 17c runbook remains active under `docs/validation/` and prior results are under `docs/validation/archive/`.

Notes/result: ________________________________________________

## Checkpoint 17c acceptance summary

- [ ] Complete overlay applies successfully.
- [ ] 490/490 engine-independent tests pass.
- [ ] Godot title/logs identify `checkpoint-17c`.
- [ ] Default window is 1440x900 and usable.
- [ ] AUTHORITATIVE DEBUG toggle is immediately accessible.
- [ ] Debug detail pane is usable and auto-scrolls correctly.
- [ ] Debug-off view restores the observer-safe boundary.
- [ ] Unselected friendly Missile Flights do not clutter the map with future routes or trails.
- [ ] Selected friendly Missile Flights show dashed targeting and useful own-unit information.
- [ ] Hostile threat estimates remain dotted and explicitly non-authoritative.
- [ ] Concept v0.3r is current and v0.3q is archived.
- [ ] Complete indexed reference library is present and hash-verified.
- [ ] Only the current-checkpoint validation runbook is active.

## Evidence to preserve

- the matching `checkpoint-17c` `.log` and `.jsonl` pair;
- one screenshot showing the immediately accessible debug toggle and expanded detail pane;
- one screenshot after debug is disabled;
- one screenshot with the friendly Missile Flight unselected and uncluttered;
- one screenshot with the friendly Missile Flight selected and its dashed plan visible; and
- one screenshot showing a dotted hostile threat estimate.
