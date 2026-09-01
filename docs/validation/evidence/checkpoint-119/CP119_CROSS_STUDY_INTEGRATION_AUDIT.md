# CP119 Cross-Study Integration Audit

**Checkpoint:** 119  
**Purpose:** verify that the CP119 shared research-CLI extension does not invalidate accepted earlier research consumers.

## Frozen baseline

CP119 is derived from the accepted CP118 repository. Accepted CP118 checkpoint authority files were restored byte-for-byte after the CP119 authoring integration work; CP119 does not rewrite CP118's historical checkpoint contract or manifest.

The following production/player surfaces remain frozen:

- all 561 C#/test files in the inherited frozen surface;
- Concept v0.7l and the 11 CP117/CP118 player-technology authority files;
- CP109 numerical matrix and CP110 Reactor candidate authority;
- accepted CP118 native evidence archive and summary.

## Shared research CLI regression smokes

After adding the `weapon-integration-study` command, one-trial smokes were rerun through the same shared CLI:

| Study | Variants | Result |
|---|---:|---|
| CP114 payload characteristic space | 3,184 | zero failed gates |
| CP115a weapon-family study | 4,064 | zero failed gates |
| CP116 warhead-generation study | 2,976 | zero failed gates |
| CP118 simplified-weapon study | 1,824 | zero failed gates |
| CP119 campaign weapon integration | 1,152 | zero failed gates |

The CP119 extension therefore adds a new study route without changing the accepted earlier study definitions or their variant reconstruction.

## CP119 integration boundaries

CP119 introduces only:

- one new study JSON;
- one new analysis module;
- one new test module;
- one shared-CLI parser/dispatch extension;
- CP119 evidence/documentation/checkpoint infrastructure.

It does not change combat resolution, the Candidate Matrix, production C#/Godot code, or player-facing weapon authority.

## Acceptance implication

A CP119 native acceptance failure should be diagnosed as a CP119 study/integration/checkpoint issue unless a regression smoke or parity fixture also fails. Earlier accepted Monte Carlo evidence remains authoritative for the mechanics it exercised.
