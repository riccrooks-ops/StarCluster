# Checkpoint 17c — Presentation correction, Concept v0.3r, and complete reference handoff

## Purpose

Checkpoint 17c closes the two presentation problems exposed by the partial Checkpoint 17b Godot validation, consolidates the subsequent ship-design and combat-support decisions in Concept v0.3r, and packages the complete external design-reference library for reliable handoff to a later chat or developer.

This is still a narrow presentation/documentation checkpoint. It does not prematurely implement the full tactical-power, layered-damage, Damage Control, ammunition, Hull-TL, or installation-compatibility systems documented in v0.3r.

## Presentation corrections

### AUTHORITATIVE DEBUG usability

- The default prototype window increases from `1280x800` to `1440x900`.
- The detail pane minimum height increases from 190 to 280 pixels.
- The **AUTHORITATIVE DEBUG** toggle moves into the always-visible command region above the detail pane.
- Enabling the toggle still defers scrolling until layout is complete and brings the selected missile's authoritative detail into view.
- The debug view remains development-only, default-off, and excluded from normal player knowledge.

### Friendly Missile Flight decluttering

- Friendly Missile Flights are treated as player-owned units rather than persistent route overlays.
- A friendly dashed guidance/targeting plan is drawn only while that Missile Flight is selected.
- Historical missile trails are selected-only and show completed observed movement, not future plans.
- The misleading faint solid rendering of `VisibleLastExecutedRoute` is removed from normal play.
- Friendly hover text adds assigned target and remaining range; hostile text remains observer-safe.
- Hostile dotted lines remain incoming-threat estimates and do not disclose authoritative enemy guidance.

## Concept v0.3r consolidation

Concept v0.3r records the current direction for:

- cruiser-lineage progression driven by staggered Hull TL rather than scout-to-battleship class escalation;
- separate Hull and Armor technology categories;
- a compact visible technology set including Shields and separate Projectile, Energy, and Missile Weapon categories;
- unique support items without requiring a dedicated Auxiliary research tree;
- item-specific prerequisites and Integrated, Adapted, and Incompatible installation states;
- matched Precursor components and the story-generating choice between preserving or cannibalizing rare technology;
- Tactical Power Capacity, core power, reactor damage states, emergency output, batteries, energized armor, and Shield Boosters;
- current-turn power commitment, next-turn reactor consequences, and immediate damage to the affected component itself;
- uncertain material-consuming Damage Control, assistance allocation, provisional 70/50/40 repair chances, and drydock limits;
- Repair Supplies, Salvage, Minerals, Radioactives, Advanced Resources, and specialized materials;
- Ready Packages, automatic loaders, weapon-specific internal magazines, shared magazine families, and resupply;
- individualized major internal systems, grouped support exposure, and bounded hidden-track density; and
- an emergent roleplaying and exploration story-generator objective.

All numeric values remain data-driven and provisional until representative ships and encounters are implemented and tested.

## Reference library

`docs/references/` now contains every external rules or ship-design reference available during this design pass, plus an index and SHA-256 manifest. These files are carried for private project continuity. They inform design but do not override the Concept document or Decision Register.

Future complete checkpoints should preserve the reference folder unless the user deliberately adds, removes, or replaces a source.

## Validation and archive policy

- `docs/validation/Checkpoint_17c_Presentation_Concept_And_Reference_Handoff.md` is the only active manual procedure.
- The user's partially completed Checkpoint 17b runbook is preserved as `docs/validation/archive/Checkpoint_17b_Partial_Validation_Results.md`.
- The matching screenshot and authoritative log pairs are preserved under `docs/validation/evidence/checkpoint-17b-partial/`.
- Tested Checkpoint 09 through 17a procedures remain in the existing tested archive.

## Architecture and expected verification

- `StarCluster.Core` remains authoritative and Godot-independent.
- `StarCluster.Tests` remains the engine-independent regression suite.
- `StarCluster.Game` owns presentation, input, scenarios, and development diagnostics only.
- .NET SDK: `8.0.423`
- Expected complete suite: **490 tests**
- No Core behavior or test-count change is expected.

## Next substantive checkpoint

After Checkpoint 17c acceptance, Checkpoint 18 should implement unified Current/Firm terminal solutions and seeker-assisted terminal acquisition. The larger v0.3r power, repair, ammunition, hull, and installation designs should follow as focused checkpoints after the missile terminal contract is stable.
