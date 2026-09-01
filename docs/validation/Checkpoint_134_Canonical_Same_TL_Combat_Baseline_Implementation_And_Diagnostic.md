# Checkpoint 134 - Canonical Same-TL Combat Baseline Implementation and Diagnostic

## Purpose

Checkpoint 134 is the first executable calibration pass on the accepted CP133 candidate combat-subsystem baseline. It promotes no balance conclusion automatically. Its job is to synchronize the agreed mechanics into canonical kernel v0.2, prove that production C# and research Python expose the same rule contracts, and run controlled TLx-vs-TLx reference fights that make the revised weapon/Shield/Armor families observable before tuning.

CP132 Corrected Replacement 5 remains the accepted foundation for `penetration-hardening-v1`. CP133 remains the accepted candidate numerical/component baseline. CP134 changes mechanics implementation and Concept wording needed to execute that candidate, then gathers new same-TL evidence under those rules.

## Canonical mechanics added in kernel v0.2

- Direct-fire ship attacks may use Firm or Approximate tracks.
- Firm track has no track-quality penalty; Approximate has the universal provisional -25 pp penalty.
- Direct-fire profiles distinguish Standard Range and Maximum Range.
- Fire beyond Standard but at/below Maximum has the universal provisional -10 pp penalty.
- Approximate + extended range stacks to -35 pp; beyond Maximum is illegal.
- Tactical Computer ordinary targeting assistance remains separate; historical computer-owned Approximate penalty data is provenance only.
- Energy Main output is universal: Low = half Standard TP/DAM rounded up; Standard = listed; Overload = 1.5x Standard TP/DAM rounded up and +1 weapon Strain.
- Armor profiles with tactical regeneration restore 1 AI per TP during Damage Control, up to the listed per-turn cap and pristine AI. A zero cap is a legitimate passive branch.
- Candidate Shield arithmetic retains the intentional invariant that Base Recharge + maximum Tactical Recharge can restore full contemporary SC in one legal recharge window.

## Primary reference population

The baseline population is deliberately narrow. Every reference ship uses one contemporary Main, Reactor, Tactical Computer, Sensor, Shield, and Armor. Shield and Armor are mandatory study controls even though neither is universally mandatory in legal construction. ECM/ECCM and optional tactical auxiliaries are omitted from the primary lanes so the first evidence isolates weapon/defense progression. Unused Installation Space is treated as mission/support filler with no combat effect.

Weapon families:

- TL1: Kinetic, Energy, GP Missile.
- TL2-TL9: Kinetic, Energy, GP Missile, Swarmer.

TL6 explicitly crosses two Armor profiles in both side positions:

- mainline regenerative Armor;
- A_b1 Crystalline Armor seed (AP2 / AI12 / zero tactical-regeneration cap).

## PDS control

Direct-fire-only pairings run once with PDS absent. Any pairing containing GP Missile or Swarmer runs paired contexts:

1. PDS off - isolates the missile delivery/guidance/warhead interaction with Shield/Armor/Hull.
2. Contemporary AMM PDS on - measures the interception/power tax without changing the offensive or defensive baseline.

PDS is a controlled diagnostic stratum, not a claim that every normal ship must install it.

## Study shape

The canonical study definition is `docs/design/testing/cp134_same_tl_candidate_baseline_study_v0_1.json`.

- logical contexts: 196;
- movement-order variants: 392;
- TL6 variants: 136;
- physical-symmetry gate: 50 mirrored comparisons / 100 executions;
- full-matrix smoke: 392 variants x 1 trial;
- substantive workload: 392 variants x 5,000 trials = 1,960,000 engagements;
- mixed-TL ships: none;
- automatic numerical promotion: none;
- 50/50 matchup target: none.

Movement order is mirrored because initiative/geometry effects remain part of the game. The study uses the canonical radius-5 System Map and standard starts/search doctrine from the shared kernel.

## Diagnostic telemetry

The study records outcomes and causal progression rather than only win rate, including direct Firm/Approximate and Standard/extended shots; stacked penalties; Energy Low/Standard/Overload use and Strain; TP spent on weapons, Shield recharge, PDS, and Armor regeneration; Shield/Armor first damage and collapse timing; Shield reconstitution; SPEN/APEN bypass; Armor Integrity and Hull damage; missile launches/arrivals/guidance/hits; PDS attempts/intercepts; and Swarmer packet outcomes available through the canonical telemetry.

Contexts with very high unresolved rate or very long duration are review flags only. A side with zero offensive activity is a mechanics gate because it can indicate illegal movement/acquisition/doctrine routing rather than balance.

## Interpretation boundary

CP134 is not tuned toward 50/50. Families are expected to possess strengths and weaknesses. The review questions are instead:

- Is every family mechanically active and viable in at least meaningful parts of the contemporary defensive envelope?
- Do Kinetic, Energy, GP Missile, and Swarmer display their intended different resource/delivery/penetration identities?
- Do Shield and Armor both materially participate in combat?
- Are TL progression and the TL1 / TL2-4 / TL5-7 / TL8-9 technology leaps reasonable rather than pathological?
- Does TL6 regenerative versus Crystalline Armor create a real trade rather than a strict upgrade?
- Does PDS impose a visible missile tax without making guided weapons categorically irrelevant?
- Are power, duration, unresolved, and delivery pressures pointing to later Reactor/Space rebalance needs?

No CP134 output automatically changes a technology value. Numerical changes require a later reviewed repository change.
