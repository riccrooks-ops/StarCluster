# Build-Neighbor / Ablation Architecture v0.1

Checkpoint 112 adds a targeted causal-analysis layer to the CP111 research ecology. It reuses the same instrumented combat consumer and exact-fill construction policy, but replaces broad round-robin inference with controlled one-decision perturbations.

## Design rules

- Same-TL fixed-tech populations remain the primary inference lane.
- Every build fills Hull Installation Space exactly; residual not-yet-numerical mission/AUX capacity has zero tactical effect and remains explicitly reported.
- Mixed-TL/legacy populations remain separate and have zero CP112 inference weight.
- Hardware effects are compared by holding as much of the package constant as practical and changing one component or one family identity at a time.
- Movement-order diagnostics are mirrored and reported separately rather than averaged away.
- Starting-range and turn-horizon controls are explicit variant dimensions.
- All major CP111 telemetry remains available in every targeted variant.
- Balance outcomes are review signals, never automatic gates or promotions.
- Damage scope remains layered Shields/Armor/Hull only; internal critical/subsystem damage is not simulated.

## CP112 populations

### Energy defense ablation

TL3-TL8. Eight exact-fill variants of the Energy defense specialist are tested against the other eleven standard CP111 same-TL builds under both movement orders:

- full package;
- no Shield Hardener;
- no PDS;
- no ECCM;
- no Shield (and therefore no Hardener);
- no Hardener and no PDS;
- Kinetic main with the otherwise identical defensive package;
- Missile main with the otherwise identical defensive package.

This isolates package defense, PDS, Hardener, ECCM, and Main Weapon family contributions without changing the opponent population.

### Movement-order geometry

Three high-signal CP111 Kinetic-versus-Missile pairs are tested at starting ranges 4, 6, 8, and 10 under both movement orders. The purpose is to determine whether the CP111 cliff is specific to edge-to-edge initial geometry or persists across the axial range envelope.

### Missile attrition ablation

TL7-TL9 Missile balanced and dual-main attackers are tested against five exact-fill Missile-defense variants: full, no Hardener, no PDS, no ECCM, and no Shield. Each pairing runs under both movement orders at 60- and 120-turn horizons. This distinguishes timeout effects from sustained defensive equilibrium and attributes the equilibrium among Shield, PDS, Hardener, and ECCM layers.

## Future extensions

This architecture is intentionally compatible with later full-radius-5 2D geometry, mixed-TL overlays, component-replacement neighbors, numerical parameter counterfactuals, and internal-damage consumers once those are parity-validated.
