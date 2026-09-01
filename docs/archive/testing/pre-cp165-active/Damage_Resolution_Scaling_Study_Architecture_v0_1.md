# Damage Resolution Scaling Study Architecture v0.1

## Purpose

Checkpoint 121 asks a narrow architectural question raised by CP120: is Star Cluster's present integer damage/defense ruler too coarse? The study does **not** promote larger damage numbers. It tests an exact research-only x2 conversion first, then uses the newly available odd integers as half-step probes around known cliffs.

The accepted gameplay/numerical baseline remains CP119. CP120 is superseded as a candidate because its combat run was valid but its derived Missile terminal-hit telemetry read the wrong side. CP121 corrects that reporting path and preserves CP120's native combat evidence by reanalysis rather than rerunning it.

## Two-stage design

### Stage A — exact x2 equivalence gate

Every CP120 variant is executed twice with the same variant, seed, and trial index:

1. legacy damage domain;
2. research-only x2 damage domain.

The x2 domain doubles all magnitudes that directly represent damage, protection, penetration, repair/restoration, or Hull endurance in the current Python combat consumer. It leaves percentages, ranges, Tactical Power, Space, ammunition counts, fuel, movement, Sensor/EW ratings, and other non-point quantities unchanged.

The pair must agree exactly on winner, unresolved state, turns, error state, all non-damage telemetry, and final states after unit conversion. Damage-domain telemetry and final Shield/Armor/Hull values must be exactly twice legacy values. **Any mismatch fails the study before half-step outcomes are interpreted.**

The equivalence source is the complete CP120 4,284-variant population. Native CP121 uses 20 paired trials per CP120 variant = 85,680 legacy/x2 trial pairs (171,360 combat executions). Bounded authoring evidence uses 5 paired trials per variant.

### Stage B — odd-point resolution probes

After equivalence passes, the x2 scale makes one new integer point equal to one-half of a legacy point. CP121 tests that resolution rather than assuming it is useful.

Offensive triplets are deliberately adjacent: low / odd midpoint / full legacy step. Legal same-TL targets carry the inference. The main probes are:

- GP Missile D10/D11/D12 around legacy D5→D6;
- GP Missile D12/D13/D14 around D6→D7;
- GP Missile D14/D15/D16 around D7→D8;
- endpoint D16/D17/D18 around D8→D9;
- two-packet Swarmer D4/D5/D6, D6/D7/D8, and D8/D9/D10 packet ladders;
- Kinetic +0/+1/+2 scaled DAM, APEN, and SPEN, where +1 is a half legacy point.

Defense probes use controlled fixtures for +0/+1/+2 scaled Shield Capacity, Shield recharge, Armor Integrity, Armor Protection, and Hull. The +1 case is again a half legacy point. These controlled fixtures diagnose sensitivity; they are not promoted target packages.

The half-step population contains **2,424 mirrored variants**: 1,240 Missile, 832 Kinetic, and 352 Energy-reference variants. Priority weighting is 1,548 TL2–TL6 primary, 420 TL7 advanced, and 456 TL8–TL9 endpoint/stress variants. Native execution uses 2,000 trials/variant = **4,848,000 half-step engagements**.

Total native CP121 research execution is therefore 4,848,000 half-step engagements plus 171,360 equivalence combat executions. This excludes the fast regression smokes.

## What x2 means

The research scale doubles:

- weapon/warhead DAM;
- SPEN and APEN;
- Shield Capacity, base recharge, tactical recharge-per-TP, and Shield Armor;
- Armor Protection and Armor Integrity;
- Hull points;
- any research-only point deltas/overrides that operate on those quantities.

The scale does **not** double ACC, guidance, evasion, PDS percentages/Reaction Capacity, range, movement, Tactical Power, Space, ammunition counts, fuel, Sensor/EW ratings, or condition steps.

`damage_domain_scaling_audit_v0_1.json` is the machine-readable adoption audit. It also records consumers outside the present Python ecology that would have to change before any canonical conversion.

## Hull and internal criticals

Hull is doubled in the CP121 research layer. Failing to double Hull would trivially make doubled weapons twice as lethal and would not be an equivalence test.

Internal H/X criticals are deliberately **not** simulated by this research consumer. However, the current C# internal-damage resolver advances one H/X position per Hull point lost. A future canonical x2 scale cannot keep that literal cadence: doing so would double critical frequency. Exact legacy equivalence requires one legacy H/X advance per **two** new-scale Hull points, with a deterministic remainder carried across packets. This is an adoption requirement, not a CP121 gameplay change.

Damage Control has the same issue in magnitude form: today's 1-Hull repair is equivalent to 2 new-scale Hull points. Again, CP121 records the requirement but does not modify production damage control.

## Other adoption traps

Degraded Energy weapon damage currently uses half-rounded-up integer damage. A naive x2 conversion is not equivalent for odd legacy values. For example, legacy D3 degrades to D2; naively scaling D3→D6 and then halving gives D3, whereas exact equivalence is D4 on the new scale. Canonical adoption therefore needs an explicit scale-aware degradation rule rather than a blind data multiplication.

Natural-100 point bonuses, Shield-Hardener flat protection, Ablative/other point-domain branch bonuses, and active historical calibration simulators must similarly be audited before promotion. CP121's exact Python gate handles the consumers used in this study only.

## Interpretation

A useful x2 scale must satisfy both conditions:

1. exact conversion preserves existing combat when only units change;
2. odd-point probes produce meaningful intermediate behavior often enough to justify the larger visible numbers.

The study does not require every half-step to split an outcome perfectly in half. Layered defense intentionally contains thresholds, and some technologies should make noticeable jumps. The question is whether the extra integer lets designers choose a smaller step when appropriate without fractions.

No win-rate threshold automatically promotes x2, a weapon value, or a defense value. Human review remains required.
