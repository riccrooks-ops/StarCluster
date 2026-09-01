# Checkpoint 105 - Technology Family Architecture Foundation

## Purpose

Checkpoint 105 is an **architecture-only technology deep-dive** following native-accepted Checkpoint 104. It deliberately performs no numerical technology rebalance, no TL-table population, no Monte Carlo study, no C# build, and no Python research simulation.

The checkpoint establishes the conceptual layer that must exist **before** the next full TL1-TL9 working table is populated: each technology family tells its own development story instead of inheriting a universal Mark-I/Mark-II/Mark-III cadence.

## Accepted baseline

Checkpoint 104 remains the gameplay/numerical baseline carried into this architecture pass. Frozen native evidence is preserved under `docs/validation/evidence/checkpoint-104/`.

Accepted CP104 authorities:

- normal definition SHA-256: `ecaa1d598e626d599d8f80c46fbe2b892f62cec06c31e19dbe987845b9bf4ed5`
- repository manifest SHA-256: `03edf5b92afb5f6dc8073040b6e9bd58fb0c73f603f8d5cdc284ae00f6e9ace4`
- native results ZIP SHA-256: `4819182f19f9e5b9248846eacad0cb3a1385cc23dd745a40378062a9f0b37550`
- 876/876 xUnit tests, 20/20 stages, 10/10 Python research tests, 25/25 parity fixtures, 128,000/128,000 substantive CP104 trials, zero failed gates/trial errors.

## Architecture outputs

CP105 creates four coordinated architecture artifacts:

1. `Technology_Family_Storyboard_v1.md` / `technology_family_storyboard_v1.json`
   - 10 visible research disciplines;
   - 31 technology lineages;
   - TL1-TL9 family-specific stories plus explicitly marked Precursor/TL10-shorthand beats;
   - a soft era-tone guide: TL1 slightly futuristic; TL2-4 lower science fiction; TL5-7 higher science fiction; TL8-9 increasingly science fantasy;
   - no requirement that every family populate every TL.
2. `Technology_Idea_Register_v1.md` / `technology_idea_register_v1.json`
   - 120 preserved anchors and ideas;
   - lifecycle/status labels `base`, `existing`, `candidate`, `deferred`, and `exotic`;
   - structural-role tags distinct from adoption status;
   - ordinary candidates, one-off/weird-science ideas, and Precursor concepts kept visible without automatic adoption.
3. `Cross_Pollination_And_Legacy_Revival_Map_v1.md`
   - sparse causal cross-tree enabling relationships;
   - explicit legacy-revival examples, including later Fission derivatives;
   - guardrails against generic synergy bonuses and blanket prerequisites.
4. `CP105_Technology_Architecture_Reference_Synthesis.md`
   - reconciles the current Concept, preserved Spacedock/reference corpus, archived game references, the user-provided Terra Invicta wiki, and selected primary science/engineering references;
   - records inspiration and design questions rather than copying external trees, values, names, or mechanics.

## Lifecycle/status semantics

- **base** - mature starting-world technology or a later derivative/revival of that baseline family. Base does not mean primitive or obsolete.
- **existing** - already expected/established by the current Concept or accepted architecture, even if later numerical implementation is still open.
- **candidate** - a strong proposed addition with a plausible family role; not yet a numerical/table authority.
- **deferred** - worth preserving, but placement, prerequisites, role, or implementation consequences remain unsettled.
- **exotic** - Precursor-grade or deliberately rule-bending technology outside normal player-developed TL1-TL9 research.

`TL10` remains planning shorthand for Precursor provenance only. It is not a researchable tenth normal Technology Level.

## Critical reconciliation with TL1-TL3

CP105 does not invalidate CP104's accepted numbers. It corrects the **story interpretation** around them.

Power is the clearest example:

- TL1: Peak Fission - mature baseline family;
- TL2: Early Practical Fusion - introduction of a different reactor family, not merely "Reactor 1 but better";
- TL3: Mature Compact Fusion - integration/miniaturization;
- TL4: High-Output Fusion - the next Fusion frontier step;
- TL5-7: Antimatter introduction/maturation/high-output, overlapping Peak Fusion;
- TL8-9: matter-conversion family while mature Antimatter may still have a pinnacle role.

Other families may use different rhythms, contain quiet TLs, split into branches, or revive later through causal cross-pollination.

## Deliberate non-changes

CP105 changes none of the following:

- accepted TL1-TL3 numerical values;
- the `tiers` working values in the current Technology Architecture Matrix;
- the technology workbook values;
- C#/Godot game mechanics;
- ScenarioRunner C# research/regression code;
- Python research/simulation engine;
- standing permutation study inputs, seeds, trials, or workloads;
- any automatic production/component promotion.

The Matrix receives only documentation/lifecycle metadata pointing to the new family-story authority and correcting the stale implication that TL3 is a universal maturation endpoint.

## Reference-use boundary

External sources are inspiration only. CP105 adopts **questions, physical relationships, broad technological patterns, and tradeoff ideas**. It does not copy external numerical ladders, prerequisites, formulas, proprietary names, or exact mechanics.

Generic scientific/engineering labels may remain as working labels where appropriate. More game-flavored names such as `Ion Cannon` are explicitly placeholders pending later original naming and mechanic design.

## Validation

Checkpoint 105 validation is deterministic repository/document validation only:

- CP104 evidence/provenance is frozen and recognized;
- exactly one active Concept exists and is v0.7e;
- storyboard/status/role data are internally valid;
- normal-player TL beats are within TL1-TL9 and TL10 beats are Exotic/Precursor-only;
- required established Power-family story beats exist;
- the idea register contains all five requested lifecycle labels and required candidate/exotic anchors;
- cross-pollination/legacy-revival artifacts exist;
- reference synthesis/source index exist and preserve the originality boundary;
- the technology workbook and executable simulation/game surfaces are byte-identical to CP104;
- there is no CP105 calibration definition and no CP105 simulation workload;
- the repository manifest is exact.

## Acceptance procedure

From one clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-105\apply_checkpoint_105.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-105\apply_checkpoint_105.ps1
```

Both paths intentionally run the same deterministic architecture contract. The second command exists to preserve the normal checkpoint handoff rhythm; it does not invoke .NET, Python, or calibration.

## Post-CP105 direction

If the architecture contract passes and the human review accepts the family stories, the next technology checkpoint should translate the accepted stories into a **provisional TL1-TL9 technology/component table**. Numerical assignment and simulation come later, after the conceptual families and branches are coherent.
