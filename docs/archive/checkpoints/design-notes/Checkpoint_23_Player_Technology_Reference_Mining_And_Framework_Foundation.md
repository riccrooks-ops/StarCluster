# Checkpoint 23 - Player Technology Reference Mining and Framework Foundation

## Purpose

Checkpoint 23 establishes the game-wide player-only TL 1-9 framework before numerical calibration. It adds a complete named component catalog, compatibility/adaptation schema, reference library and insight ledger, and Concept v0.3t. It changes no combat mechanics and promotes no numerical TL values.

Checkpoint 22d remains the accepted mechanical and performance baseline. Checkpoint 21e remains the frozen behavioral reference.

## Delivered framework

- ten broad player-visible research categories;
- one player-visible Propulsion TL with separate FTL and sublight (STL) standard component families, producing eleven component families overall;
- 99 named standard components with stable IDs;
- independent category advancement rather than lockstep research;
- family-level support profiles, normally no more than two related categories;
- Integrated, Adapted, and Incompatible installation states;
- schema for meaningful-event Adaptation Strain, warnings, workshop adaptation, field jury-rigs, and condition-step failure;
- bounded Skilled/Legendary Chief Engineer bridges that cannot bypass hard blockers;
- complete local reference inventory, including `MOO2_GAME_MANUAL.PDF`;
- paraphrased Reference Insights and Design Reconciliation records; and
- an explicit originality guardrail.

## Stable documentation contracts

The following machine-readable decision markers are intentionally stable. Validation checks these markers rather than depending on incidental prose wording:

- `SC23_PROPULSION_RESEARCH_MODEL=ONE_PLAYER_VISIBLE_TL_TWO_DRIVE_FAMILIES`
- `SC23_ADAPTATION_STRAIN_MODEL=MEANINGFUL_STRESS_EVENTS_ONLY`
- `SC23_REFERENCE_USE_POLICY=INSPIRATION_WITHOUT_COPYING_CORE_MECHANICS`

## Reference-use boundary

External references may influence naming patterns, design questions, subsystem relationships, tradeoffs, presentation, and implementation concepts. They do not override the Concept and may not be used to copy proprietary prose, art, distinctive names, exact technology ladders, construction tables, numerical progressions, formulas, combat matrices, or another game's defining core mechanics.

## Revision 1 compatibility repair

The initial release candidate used `System.IO.Path.GetRelativePath`, which is available under modern .NET but not under Windows PowerShell 5.1's .NET Framework runtime. Revision 1 replaces that call with a prefix-validated relative-path helper built from .NET Framework-compatible APIs and adds a runtime compatibility self-test. The repair changes no technology data, documentation decisions, game mechanics, or accepted Checkpoint 22d behavior.


## Revision 2 full-repository and dirty-tree repair

Revision 2 restores 41 repository-owned files that were present in the accepted working repository but absent from the earlier full-archive lineage. The restored set covers foundational hex geometry, system-map storage, direct-fire line of sight, missile routing, their tests, early checkpoint scripts, and one archived validation record. The internal manifest now locks exactly 466 repository files.

The manifest contract remains strict for unknown files under `src`, `tests`, `tools`, and `docs`, but it now distinguishes those files from normal local/generated state. Visual Studio `.vs` data, Godot `.godot` data, `.uid` sidecars, `bin`/`obj`/`out`, stale root checkpoint identities, and local root ZIP copies do not invalidate an otherwise correct working tree. Duplicate stale active Concept and validation-runbook files are removed when identical to their archive copies; divergent copies are preserved under imported archive names and remain visible to contract review.

The release validator now exercises clean extraction, full acceptance, dirty-tree normalization, local-artifact tolerance, and rejection of a deliberately injected unknown source file. No gameplay, TL data, or numerical balance changed.

## Revision 3 documentation-contract repair

Revision 3 repairs a release-contract defect discovered by native Windows PowerShell validation. The prior validator searched the checkpoint narrative for the incidental phrase `one Propulsion TL`, while the document expressed the same accepted decision as separate FTL and sublight families under Propulsion. The technology data and design decision were correct, but the prose-coupled assertion failed. Revision 3 adds explicit stable decision markers and validates those markers instead of fragile natural-language wording. No technology data, gameplay mechanics, numerical balance, or accepted Checkpoint 22d behavior changed.

## Validation boundary

Checkpoint 23 changes documentation and design data only. Validation therefore requires:

- exact 466-file complete-archive manifest and native PowerShell parsing;
- stale-runbook and stale-Concept normalization;
- explicit local/generated-artifact tolerance with unknown repository-source rejection;
- reference-library and SHA-256 verification;
- CSV row/key/cross-reference contracts;
- XLSX OOXML and sheet contracts, with no structured tables;
- Concept v0.3t and archived v0.3s;
- clean warning-as-error build;
- 506 engine-independent tests;
- seven deterministic scenarios; and
- 46 ScenarioRunner self-tests.

No Monte Carlo recalibration and no mechanical Godot validation are required.

## Next pass

Review names, define the smallest useful foundational numerical schema, and draft TL 1/3/5/7/9 anchors for Hull, Armor, Shields, Power, FTL, and STL. Then fill intermediate TLs and test matched/mixed-TL reference cruisers before independent Missile Flight subsystem decomposition.
