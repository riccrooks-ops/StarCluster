# Checkpoint 17b validation — combat concept and validation UX hotfixes

This is the only active manual validation procedure for Checkpoint 17b. Completed Checkpoint 09 through 17a procedures are preserved under `docs/validation/archive/Tested_Tactical_Regression_Checkpoints_09_Through_17a.md` and need not be rerun unless a specific regression is suspected.

## A. Apply, build, and test

1. Close the Godot editor and any running Star Cluster debug window.
2. Extract the complete Checkpoint 17b archive into the repository root.
3. From PowerShell, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-17b\apply_checkpoint_17b.ps1
```

4. Confirm the script selects .NET SDK `8.0.423`, builds with warnings treated as errors, and reports **490 passed tests**.
5. Reopen `src\StarCluster.Game\project.godot` and press **F5**.
6. Confirm the title and automatic log filenames use `checkpoint-17b`.

## B. AUTHORITATIVE DEBUG usability hotfix

Use **Missile local-sensor occlusion** or another scenario containing a visible selected hostile missile.

1. Select the hostile missile.
2. Turn on **AUTHORITATIVE DEBUG**.
3. Confirm the detail region has a usable minimum height rather than collapsing to approximately three text lines.
Ric: It changes based upon the space of the region above it.  For example, when I'm in the missile phase, it only has room for 3 lines of text.  Personally, I think the window just needs to be larger than 1280x800.
4. Confirm enabling the option automatically scrolls the detail region to the selected-missile authoritative information.
Ric: I had to scroll for awhile to enable Authoritative Debug, so I started there by default after scrolling to the toggle.
5. Confirm the observation-step list, actual coordinate, lifetime range, datalink state, retained report, local report, selected guidance source, and replan count can be reviewed without slowly scrolling through the entire panel from its top.
Ric: The data appears to be there, but I have to scroll a lot given the 3-4 line limitation.
6. Turn **AUTHORITATIVE DEBUG** off.
7. Confirm all hidden hostile details disappear and the normal observer-safe panel remains.
Ric: Confirmed.

Notes/result: ________________________________________________

Screenshot names: First screenshot captured.

## C. Dedicated friendly Missile Flight route fixture

1. Reset the encounter and select **Friendly missile route validation**.
2. Keep Player sensors Passive, Enemy sensors Passive, Player jammer Off, and Enemy jammer Off.
3. Advance to **Missile / Interception**.
4. Select the enemy ship as the player missile target.
Ric: A dashed green line appears once I click on the target.
5. Select **Launch player missile**.
Ric: My "F" missile, friendly-1, appears in hex -1,3.
6. Confirm one friendly Missile Flight appears and its planned route is **dashed**.
Ric: It has a dashed green line connecting the missile to the target.  Additionally, there seems to be a faint solid green line connecting my ship to the target.  The dashed green line overlays the dim solid line.
7. Confirm the friendly route follows the missile-owned report actually consumed at launch and does not expose hidden hostile state.
Ric: I don't understand.
8. Launch one enemy missile at the player, when the fixture permits it, and confirm the hostile incoming-threat estimate is **dotted**, visually distinct from the friendly dashed plan.
Ric: Confirmed.  Also, the brighter dotted and dashed lines are easily overpowering the faint trails, but that's ok.
9. Confirm help or explanatory text states that the dotted hostile estimate is not proof of an enemy lock, datalink, or actual guidance coordinate.
Ric: I don't understand.
10. Deselect and reselect the Missile Flight. Confirm observed solid history, dashed friendly planning, and dotted hostile estimation remain visually distinct.
Ric: Selecting the f-1 makes the trail bright, but the faint solid green line from the missile to the target stays faint.  Likewise, selecting hostile-1 makes its trail bright.

Notes/result: ________________________________________________

Screenshot names: ___________________________________________

## D. Documentation and information-boundary checks

1. Confirm `docs/Star_Cluster_Game_Concept_v0.3q.docx` is the only current Concept document in `docs/`.
Ric: Confirmed
2. Confirm `docs/archive/Star_Cluster_Game_Concept_v0.3p.docx` preserves the accepted prior Concept.
Ric: Confirmed
3. Confirm the active validation folder contains this Checkpoint 17b procedure and the tested historical procedure is under `docs/validation/archive/`.
Ric: Confirmed
4. Confirm normal hostile tooltips may reveal ECM Active/Off, qualitative interference, and resulting track quality, but do not reveal exact hostile ECM, Cooperative ECM Screen, ECCM, or net arithmetic.
Ric: Not confirmed.
5. Confirm no normal player-facing view exposes hidden hostile missile coordinates, reports, datalink state, local-sensor state, arbitration, or replan truth.
Ric: Not confirmed.

Notes/result: ________________________________________________

## Checkpoint 17b acceptance summary

- [ ] Complete Checkpoint 17b overlay applies successfully.
- [ ] 490/490 engine-independent tests pass.
- [ ] Godot title and logs identify `checkpoint-17b`.
- [ ] AUTHORITATIVE DEBUG has a usable minimum-height scroll region.
- [ ] Enabling AUTHORITATIVE DEBUG automatically brings selected-missile details into view.
- [ ] Disabling AUTHORITATIVE DEBUG restores the observer-safe information boundary.
- [ ] The dedicated friendly Missile Flight fixture is selectable.
- [ ] Friendly planned routes are dashed.
- [ ] Hostile incoming-threat estimates are dotted and explicitly non-authoritative.
- [ ] Concept v0.3q is current and Concept v0.3p is archived.
- [ ] Only current-checkpoint validation remains active; completed procedures are archived.

## Evidence to preserve

- the matching `checkpoint-17b` `.log` and `.jsonl` pair;
- one screenshot of the usable AUTHORITATIVE DEBUG region after automatic scrolling;
- one screenshot after debug is disabled;
- one screenshot showing a dashed friendly route; and
- one screenshot showing dashed friendly and dotted hostile route semantics together, when available.
