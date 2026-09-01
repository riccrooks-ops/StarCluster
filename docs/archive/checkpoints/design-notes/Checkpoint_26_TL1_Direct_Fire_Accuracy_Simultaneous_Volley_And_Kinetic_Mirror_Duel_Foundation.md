# Checkpoint 26 - TL1 Direct-Fire Accuracy, Simultaneous Volley, and Kinetic Mirror Duel Foundation

Checkpoint 26 is the first executable Phase B pass. It preserves all Checkpoint 25 mechanics and adds an exact TL1 roll-high accuracy model, Targeting Computer condition behavior, EvM attack modifiers, simultaneous direct-fire batching, and a minimal deterministic kinetic mirror duel.

## Implemented
- 50% raw direct-fire baseline.
- Kinetic +20 and energy +25 weapon accuracy.
- Targeting Computer +10 / +5 / +0 by condition.
- Common -5 percentage points per direct-fire hex.
- Target and shooter EvM penalties of -10 each.
- Final chance bounded to 5-95%.
- Natural 01 Critical Miss and natural 100 Critical Hit tagging.
- Same-window committed return fire after attacker destruction.
- Mutual destruction outcome.
- Fixed-geometry kinetic mirror duel with base Shield recharge, finite ammunition, turn cap, and explicit terminal outcomes.
- Seven Phase B documents and 36 deterministic cases.

## Explicitly deferred
No weapon-balance conclusion, Monte Carlo calibration, critical damage effect, surrender, retreat, or race doctrine is accepted in this checkpoint.

## Checkpoint 26a compiler hotfix

Checkpoint 26a changes no mechanics, data, scenarios, or balance assumptions. It corrects the simultaneous-fire combatant collection so C# generic inference retains `DirectFireCombatant[]`, and imports `Xunit` in `Tl1DirectFireAccuracyTests.cs` so `[Fact]`, `[Theory]`, and `[InlineData]` compile. All Checkpoint 26 acceptance totals and contracts remain unchanged.
