# Checkpoint 161 — Reactor/TP Scarcity and Whole-Ship Equilibrium Diagnostic

Status: candidate pending native Windows acceptance.

## Purpose

CP161 is the broad diagnostic pass for the final major balance dependency after native-accepted CP160. It begins from **CP160-PF4** and asks a whole-ship question rather than trying to confirm the current Reactor ladder:

> At each TL, what Reactor output and subsystem Tactical Power economy preserves meaningful tactical scarcity, multiple viable ship architectures, and useful degraded/emergency behavior without chronic starvation or effectively unlimited power?

The current PF4 Reactor ladder is explicitly a **provisional scaffold**, not the expected answer. CP161 performs no numerical promotion, no production-authority change, and no automatic tuning.

## Accepted base

CP160 is native-accepted. Its native results archive is hash-locked as:

`a15271ce19677b152c6181306354c0c3e204a2c3d36ec7a5d02e8a22df1d1fbf`

CP161 must execute against CP160-PF4, SHA-256:

`7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155`

Production `technology_numerical_matrix_v0_9.json`, production C#/Godot mechanics, and the Concept remain frozen.

## Evidence layers

CP161 deliberately separates three kinds of evidence.

### 1. Exact architecture and deterministic demand surface

At the current 6-Space Reactor assumption, CP161 enumerates **22,482 space-legal powered architectures** before applying Reactor-supply feasibility as a result variable:

- 16,741 one-Reactor architectures;
- 5,741 two-Reactor architectures.

The architecture space includes Kinetic, Energy, GP Missile and available Swarmer mains; one/two mains; one/two Reactors; Shield; ECM/ECCM; K/E/AMM/no PDS; Crystalline Armor; and the powered PF4 AUX choices whose prerequisites are satisfied.

The deterministic demand states are `core`, `routine`, `offense`, `defense`, `recovery`, and `full`. `full` is a deliberate stress diagnostic. **No design requirement says every installed system must be powered simultaneously.**

Absolute Operational supply is swept from **2 through 30 TP per Reactor** at every TL. This is intentionally much broader than PF4's current 5–13 scaffold and reaches beyond the older high-output CP110 region.

Reactor Space is independently swept at **4, 5, 6, 7, and 8 Space** to quantify the opportunity cost of a second Reactor and the relationship between power supply and AUX/design capacity. This does not promote Reactor miniaturization.

### 2. Stochastic tactical demand/allocation surface

CP161 selects **12 diverse one-Reactor representatives per TL = 108 ships** and exercises six demand doctrines:

- OFFENSE;
- EW_CONTEST;
- MISSILE_DEFENSE;
- DAMAGE_CRISIS;
- PURSUIT_BURST; and
- MIXED.

Each of the 648 representative/doctrine variants receives **12,000 deterministic stochastic turn samples**, for **7,776,000 turn-demand samples**. The study records demand percentiles, raw shortfall, allocated/funded TP, denied TP, component request/funding rates, and Energy fallback behavior.

This layer distinguishes normal, conditional and emergency/burst demand. It does not pretend that all installed equipment requests TP every turn.

### 3. Full-map combat sensitivity

CP161 uses the accepted `cp147_tactical_utility` whole-combat allocator and PF4 combat ecology. Operational Reactor output is evaluated at seven matched offsets from the current PF4 ladder:

`-4, -2, 0, +2, +4, +6, +8 TP per Reactor`

The combat layer has **36 contexts per TL**, including main-family, PDS, Crystalline, dual-main/high-demand, and **mirrored one-Reactor versus two-Reactor Kinetic/Energy/Missile contests**. Each cell receives 2,000 common-random-number trials:

- 324 contexts across TL1–TL9;
- 2,268 context/supply cells;
- **4,536,000 substantive full-map combats**.

Turn-cap sentinels are retained as evidence rather than automatically treated as checkpoint failures. Combat execution errors remain blocking.

## Supply-side variables

CP161 measures:

- Operational Reactor output broadly;
- current Degraded and Emergency output against the exact/stochastic demand distributions;
- optional second-Reactor value and Space opportunity cost; and
- Reactor Space 4–8 as a construction sensitivity.

The current full-map Python ecology does not transition Reactor component state during battle, so Degraded/Emergency outputs are evaluated analytically/stochastically rather than falsely claiming integrated Reactor-damage combat evidence.

## Demand-side variables

PF4 subsystem magnitudes and mechanics are frozen. CP161 measures the current TP economy and performs one-factor ±1 TP/cap sensitivity for:

- Kinetic main firing;
- Energy Standard and Overload firing;
- Missile launch;
- Active Sensor;
- ECM;
- ECCM;
- PDS readiness;
- Shield tactical recharge cap;
- Armor tactical regeneration cap;
- Shield Hardener;
- Energized Armor;
- Field Stabilizer; and
- Damage Control, including Repair Drone parallel-action demand where installed.

These are **sensitivity variables**, not automatic candidate changes.

## Repair Drone boundary

The stochastic whole-ship layer includes the second distinct-target Damage Control TP request established by CP160. Full integrated component-damage Repair Drone combat execution remains deferred because the current Python combat ecology exposes hull-only Damage Control targets. CP161 must not fabricate target diversity that the combat kernel does not yet model.

## Interpretation guardrails

CP161 must not optimize to a 50% win rate, a universal Reactor-utilization percentage, or a requirement to power all installed systems simultaneously. A viable region should instead preserve multiple rational allocations and architectures, maintain distinct K/E/M TP identities, make specialist powered AUX carry opportunity cost, retain usefulness for overload/emergency operation, avoid chronic starvation, and avoid a high-TL state where Tactical Power ceases to matter.

A second Reactor is not automatically desirable or undesirable. Its additional power must be interpreted together with the Space/AUX capability displaced by installing it.

Isolated AUX magnitude/architecture remains closed unless whole-ship integration supplies evidence of a dependency invalidation.

## Native workflow

Use one fresh extraction and run both commands in the same unchanged tree:

```powershell
.\tools\checkpoints\checkpoint-161\apply_checkpoint_161.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-161\apply_checkpoint_161.ps1
```

The normal run is resumable by TL combat batch. Console output is also captured into `out/checkpoint-161/CP161_console_output.txt` and included in the native-results ZIP for easier upload/review.

CP161 is diagnostic only. After native results are reviewed, a later checkpoint may refine/select Reactor/TP values or establish a PF5 candidate; CP161 itself cannot do so.
