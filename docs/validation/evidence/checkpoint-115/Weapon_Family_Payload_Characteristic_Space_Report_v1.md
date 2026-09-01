# CP115 Weapon-Family Payload Characteristic-Space Report v1

## Status

Checkpoint 115 is a diagnostic characteristic-space refinement layered on native-accepted CP114. The checked-in authoring pass executed **4,064 variants at 20 trials each = 81,280 engagements** with zero failed gates. The small authoring sample validates mechanics, routing, and the existence of candidate niches; it is not calibration authority and promotes no value.

The native acceptance workload is 4,064 variants at 2,000 trials each = **8,128,000 engagements**.

## Missile findings from the bounded authoring pass

### Energetic GP maturation remains the strongest signal

The contemporary GP envelopes frequently outperform static specialist+GP combinations against ordinary legal Shield packages. This is not evidence that specialists are conceptually invalid; it is evidence that once a GP packet is sufficiently energetic to cross the layered threshold, replacing half of a dual-launcher salvo with a low-structural specialist has a large opportunity cost.

Representative dual-main bounded examples against `shield-heavy-legal`:

- TL4 Fission C GP is about 39% conditional wins; static specialist pairs are generally lower.
- TL5 Fusion C GP is about 74%; static specialist pairs are generally much lower.
- Higher-TL Antimatter candidates likewise make ordinary Shield packages less dependent on a specialist opening.

The authoring sample is too small for numerical selection, but it reinforces CP114's architectural conclusion: normal GP warheads should mature by energetic generation rather than keeping the TL1 Damage-5 packet indefinitely.

### Anti-Shield specialists demonstrably affect Shields but currently struggle to earn a launcher slot

The new `shield-overmatch-fixture` deliberately increases Shield capacity and regeneration while removing PDS. Static recharge-suppression pairs visibly suppress recharge—for example, bounded high-TL lanes remove roughly 9-14 points of recharge over an engagement—but dual contemporary GP still usually performs better.

This is useful negative evidence. The tested specialist mechanics are not fake: they change Shield behavior. Their current opportunity cost is simply high relative to a mature GP missile. If the native run confirms this, the next question is not "increase the specialist until it wins," but whether the specialist needs a different tradeoff, a different tactical context, or should remain a narrower branch.

### Observer-safe adaptive pairs often decline to switch

With mature GP payloads, the attacker often observes actual Armor/Hull penetration rather than the repeated Shield-only/no-penetration evidence required to trigger a specialist. In those cases an adaptive pair correctly stays on GP. This is desirable information behavior: advanced doctrine is not forced to use a specialist merely because it exists.

## Kinetic findings from the bounded authoring pass

### Accuracy-enhanced submunitions now have a real coverage niche

The CP115 saturation model adds +ACC while preserving one attack roll per battery and smaller resolved packets. The result is qualitatively different from CP114.

Against `light-fixture`, several saturation candidates become competitive or leading. For example, bounded TL8 dual-main saturation A/B reach 100% conditional wins in the small sample, compared with about 78% for GP and 86% for the +10 ACC smart-projectile control.

Against `armor-heavy-fixture`, those same small packets are generally stopped completely by flat protection. Against Shield-heavy legal targets they are also usually poor. That is exactly the intended characteristic-space shape: coverage/hit probability against lightly protected targets in exchange for weak packet penetration.

### Tandem packets exhibit genuine order-dependent layered behavior

The tandem unit tests prove that reversing otherwise identical packet budgets can change resulting Hull damage. The bounded combat results also show TL-specific niches rather than universal dominance.

Representative dual-main `armor-heavy-fixture` authoring examples:

- TL6: GP about 79%; Tandem B about 97%; reverse about 86%.
- TL7: GP about 35%; Tandem B/reverse about 61-62%.
- TL8: GP about 44%; Tandem B/reverse about 25-30%.
- TL9: GP about 84%; Tandem B/reverse about 25-26%.

These samples are not calibration estimates, but the direction is valuable: an ordered package can create a specific mid-TL niche without becoming a universal late-TL upgrade.

### Dense penetrators remain TL- and target-dependent

Dense profiles are not consistently better than GP against the Armor-heavy fixture. Some TLs improve, others regress, and the SPEN-sacrificing profile remains appropriately poor into Shields. This argues against treating the sampled dense profiles as final automatic upgrades. Native scale should determine whether any envelope represents a stable specialist niche or whether the underlying progression should instead be automatic maturation.

## Energy reference

Existing Energy profiles are references only. The bounded controlled Armor-heavy fixture shows that current Energy can still perform strongly there; this does not trigger a CP115 correction because family asymmetry is a design lens, not a rule that every current numeric profile must already satisfy.

The severe Shield-overmatch fixture can strongly suppress Energy as well, confirming that it is an intentionally extreme characteristic probe rather than an ordinary legal balance target.

## Family-identity interpretation

CP115 should not be judged by whether Kinetic, Energy, and Missile averages converge. The useful questions are:

- does a Kinetic specialist create value against an Armor/light-target problem without erasing Shield weakness?
- does a Missile specialist create a meaningful mission role without becoming a universal GP replacement?
- does GP Missile maturation keep the delivery family structurally relevant while retaining PDS, flight-time, guidance, and magazine costs?
- are any candidate modes strict upgrades that should become automatic progression instead of player-facing choices?

## Recommendation pending native CP115

Do not promote a numerical profile from the 20-trial authoring pass. Run the 8.128-million-engagement native study and compare the same niche patterns at lower Monte Carlo error.

If reproduced, the likely architectural direction is:

1. continue normal Missile GP maturation by energetic generation;
2. retain anti-Shield specialists only if a real niche survives the opportunity cost of contemporary GP;
3. preserve accuracy-enhanced Kinetic saturation as a light-target/coverage candidate rather than an Armor breaker;
4. preserve ordered tandem Kinetic packages only if their niche remains bounded and intelligible;
5. avoid forcing family-wide 50/50 balance across every defense;
6. keep all production/C# values unchanged until a later explicit promotion checkpoint.
