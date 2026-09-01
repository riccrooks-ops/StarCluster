# Checkpoint 12 — Missile Ownership and Interception Foundations

## Purpose

Checkpoint 12 replaces the remaining single-incoming-missile presentation assumptions with explicit combat ownership, player and enemy launch flows, a retained multi-salvo engagement, and engine-independent interception foundations.

The pass deliberately does **not** finalize interception probabilities or technology-level balance. It establishes the state, ordering, and policy seams needed to add those rules without changing missile movement again.

## Accepted prerequisites

- Checkpoint 10 authoritative routed ship movement and tactical phase cursor.
- Checkpoint 11 moving-target guidance, cumulative lifetime range, and no-route waiting.
- Checkpoint 11a one-guidance-phase launch behavior with no hidden fast-forward.

## Engine-independent additions

### Explicit tactical ownership

`TacticalSide` identifies player, enemy, or legacy-unspecified ownership. New missile launches record:

- stable salvo ID;
- owning side;
- launching ship ID;
- intended target ID;
- launch coordinate;
- missile flight profile;
- current coordinate and lifetime status;
- cumulative traveled distance and complete travel history;
- defense system responsible for an interception, when applicable.

The compatibility constructor remains available for older tests and callers, but new combat code supplies a concrete side.

### Multi-salvo engagement state

`MissileEngagementState` retains every salvo created during the encounter. Friendly and hostile salvos can coexist. Active queries exclude terminal salvos, while terminal records remain available for combat history and presentation until the scenario is reset.

### Interception data and policy seam

`MissileDefenseProfile` supplies provisional, data-driven values for:

- technology level;
- interception range in hexes;
- maximum attempts per Missile / Interception phase.

`MissileDefenseSystem` adds the defending ship, side, current coordinate, and deterministic priority. It rejects friendly and unspecified missiles.

`IMissileInterceptionResolver` is the policy seam for later hit probability, technology contests, Sensors & Computing, damage, electronic warfare, and officer effects. `FixedMissileInterceptionResolver` supplies deterministic outcomes for tests and the Godot demonstration.

### Shared phase budgets

`MissileInterceptionPhaseContext` is created once per Missile / Interception phase. It:

- orders defensive systems by priority and stable ID;
- shares each system's attempt budget across every salvo in that phase;
- ignores friendly missiles and missiles outside the envelope;
- stops later defensive attempts after a successful interception;
- records structured attempt results.

### Per-hex defensive reactions

`MissileGuidanceService` now advances one route hex at a time. After each entered hex it offers eligible defenses an interception opportunity. A final-approach attempt is resolved before the missile is marked as having arrived.

This prevents a high-speed missile from entering and leaving a short defensive envelope between phase endpoints. Waiting missiles can also be intercepted at their current coordinate while no route or usable track exists.

Range already spent before interception remains spent. Interception terminates only the engaged salvo.

## Godot demonstration

The right panel now distinguishes the two launch flows:

- **Launch player missile** — requires selecting the red enemy ship as the explicit target while using the Missile route overlay.
- **Launch enemy at player** — explicitly states the hostile launcher and target.
- **Advance unresolved salvos once** — advances every active salvo that has not yet received its one movement advance in the current missile phase.

Each side may launch once in the demonstration phase. Existing salvos and newly launched salvos share the same point-defense attempt budgets.

### Visual ownership

- Player/friendly salvos use green routes and a green `F` marker.
- Enemy/hostile salvos use red routes and a red `E` marker.
- A subdued owner-colored trail shows distance already traveled.
- A brighter owner-colored line shows the current planned route.
- A yellow ring identifies the selected salvo.
- Text always identifies launcher, target, range state, status, and interception result so color is not the only ownership cue.

### Deterministic interception control

The **Demonstration interception succeeds** toggle chooses a fixed hit or miss result for the first action in that missile phase. The setting locks after missile actions begin, preserving one consistent resolver and shared budgets for the phase.

The prototype gives each ship one TL-2 point-defense system with range 1 and one attempt per phase. These values are fixtures, not final balance decisions.

### Reset behavior

**Reset map / scenario** restores:

- both ships and all map objects;
- turn 1 Movement;
- target and salvo selection;
- movement previews and command state;
- empty multi-salvo engagement state;
- point-defense budgets and launch counters.

## Tests

Checkpoint 12 adds 32 engine-independent tests:

- 4 ownership and travel-history tests;
- 4 defense-profile validation tests;
- 5 multi-salvo engagement-state tests;
- 10 interception-context, priority, hostility, and budget tests;
- 9 stepwise guidance, final-approach, waiting, range, and launch-integration tests.

Expected complete suite after application: **293 tests**.

## Local validation

Close Godot, extract the package into the repository root, then run:

```powershell
Set-Location E:\dev\star-cluster
Set-ExecutionPolicy -Scope Process Bypass
.\tools\checkpoints\checkpoint-12\apply_checkpoint_12.ps1
```

Then press F5 in Godot and exercise these cases:

1. Select Missile route, click the red ship, and launch a green player missile.
2. Launch the explicitly labeled red enemy missile at the player.
3. Confirm both salvos can coexist and advance at most once per missile phase.
4. With deterministic interception set to miss, confirm a final approach can impact.
5. Reset, set deterministic interception to succeed, and confirm the first eligible hostile salvo is stopped inside the opposing defense envelope.
6. Confirm friendly point defense never attacks a friendly missile.
7. Confirm traveled trails, remaining routes, launcher/target text, and range totals remain coherent after replanning.
8. Reset from several phases and confirm all salvos, selections, and attempt budgets are cleared.

## Deferred from this checkpoint

- probabilistic interception and final TL formulas;
- held energy weapons versus dedicated point defense;
- player selection among multiple missile weapons;
- ammunition, payload, damage, and salvo size;
- sensor-track degradation, reacquisition, spoofing, and electronic warfare;
- autonomous target search after track loss;
- AI launch and interception policy;
- permanent-impossibility missile termination.

## Next candidate checkpoint

After local acceptance, the strongest next candidate is **target-track quality and sensor/electronic-warfare foundations**, because explicit ownership, multiple retained salvos, and an interception policy seam now exist. A smaller interception-resolution pass remains an alternative if playtesting first exposes issues in defensive ordering or attempt presentation.
