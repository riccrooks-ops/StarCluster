# Checkpoint 80 Validation Tiers

## Must always run

Checkpoint 80 extends the accepted CP79a Sensor/EW candidate study into a focused power-pressure and tall-viability diagnostic. Normal acceptance therefore includes the deterministic TL1 foundation, actual-consumer preflight, a 72-variant one-trial full-pipeline smoke, and the substantive 72-variant operational study.

The release path must run repository/manifest and native-dependency validation, warning-as-error build and unit tests, deterministic moving-missile scenarios, TL1 Phase A/B, the 35-Space construction envelope, the accepted deterministic Sensor/EW foundation, CP80 actual-consumer preflight, the one-trial full-pipeline smoke, the substantive CP80 study, deterministic resource semantics, and ScenarioRunner self-tests.

CP80 release gates remain **mechanical and semantic**. They prove variant coverage, the Firm reference, the wide old-Sensor + ECCM2 path, the tall DR1 + ECCM1 path, the explicit -25 degraded-fire fallback, both missile-pressure and direct-fire-pressure coverage, the 5-TP production reference versus 6-TP diagnostic sensitivity, and the absence of production promotion. Combat outcomes remain human-review evidence rather than target win-rate gates.

The normal study contains 72 substantive variants at 10,000 trials each (720,000 substantive trials) plus 72 one-trial smoke executions. Half of the variants use missile opposition to expose PDS/offense/ECCM competition; half use direct-fire opposition to separate EW power demand from PDS pressure. The 6-TP cases are **diagnostic sensitivity only** and do not change the accepted TL1 production reactor output of 5 TP.

Checkpoint 80 explicitly tests the technology-progression guardrail that advanced equipment may legitimately require more Tactical Power, while tall/skewed research must not become a systematic self-trap. The study compares brute-force TL1 Sensor + ECCM2 against the more contemporary DR1 + ECCM1 path before any Sensor DR1, ECM2, ECCM2, reactor-output, or power-efficiency value is promoted.

## Deep Calibration

Deep Calibration remains opt-in and dependency-driven. It adds the retained historical stochastic corpus to the normal CP80 study: 33 stages, 1,670 substantive variants, 16,700,000 substantive trials, plus 126 one-trial smoke executions at default settings.

Do not run Deep Calibration merely because CP80 uses Monte Carlo. The focused normal study is the evidence required for the current power-pressure/tall-viability question. Use Deep Calibration only if normal acceptance reveals a broader regression or a later design decision deliberately changes a dependency shared with the historical stochastic corpus.
