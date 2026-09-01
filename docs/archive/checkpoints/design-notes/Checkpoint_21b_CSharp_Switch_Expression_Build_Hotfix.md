# Checkpoint 21b - C# Switch-Expression Build Hotfix

## Purpose

Checkpoint 21b repairs the compile-time defect found immediately after applying Checkpoint 21a. The full-flight opportunity authority, crossing-weave fixture, endurance-derived operational cap, 24-worker variant scheduler, common-random-number pairing, and statistical acceptance rules remain unchanged.

## Root cause

The crossing-weave selector was written as:

```csharp
CrossingWeavePolicy => (turn - 1) % 4 switch
```

C# parsed that expression as a remainder operation whose right-hand side was the tuple returned by `4 switch { ... }`. This produced CS0019 because `%` cannot combine an `int` and an `(int, int)` tuple.

The corrected expression is:

```csharp
CrossingWeavePolicy => ((turn - 1) % 4) switch
```

The explicit parentheses make the integer remainder the input to the nested switch expression. The switch still returns one deterministic axial movement vector for each step in the four-turn crossing loop.

## Scope

Checkpoint 21b changes only:

- the parenthesization of the crossing-weave switch-expression input;
- source guards that require the corrected form and reject the malformed form;
- active checkpoint and validation documentation; and
- output-directory names for the rerun.

It changes no Core mechanics, calibration data, scenario cardinality, trial seeds, scheduler ceiling, or statistical gate.

## Validation

Checkpoint 21b reruns the complete Checkpoint 21a acceptance sequence:

- 506 engine-independent tests;
- seven deterministic scenarios;
- twenty-nine runner self-tests;
- ordinary stochastic reproducibility at `--jobs 1` and `--jobs 24`;
- full-flight scheduler reproducibility at `--jobs 1` and `--jobs 24`;
- 288 repaired full-flight variants at 1,000 trials each using `--jobs 24`;
- zero terminal-opportunity invariant failures;
- zero unexplained unresolved outcomes;
- 864 paired marginals with common-random-number verification; and
- zero practical, Holm-significant contradictory marginals.

No mechanical Godot validation is required.
