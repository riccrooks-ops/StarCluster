# Technology Integration Permutation Suite Architecture v0.8

## Authority

This is the current standing integration-suite architecture. It defines reusable coverage and execution rules; it is not a checkpoint evidence log and does not promote gameplay values.

## Current envelope

The current TL1/TL2 working envelope enumerates 512 legal exact-fill 35-Space builds across weapon, reactor, computer, sensor, shield, armor, ECM, and ECCM axes. This corresponds to 262,144 oriented potential pairings. The suite enumerates the envelope deterministically and sends only bounded representative/diagnostic slices to expensive Monte Carlo.

Every legal combat build must contain at least one Main Weapon and at least one Reactor. Additional Main Weapons or Reactors remain optional explicit design choices subject to normal construction rules. Tactical Power overcommitment remains legal and is evaluated operationally.

Multiple ECM/ECCM installations are legal future enumeration choices when Space permits, but same-type ratings are non-additive: the generated ship uses the highest applicable functional ECM rating and highest applicable functional ECCM rating. The current binary exact-fill envelope still contains at most one ECM and one ECCM choice, so redundant EW copies are a required capability of the generalized enumerator rather than a dimension exercised by the current 512-build envelope.

## Current bounded screening slice

The current generated screen retains the prior 64 representative complete/mixed pairings and adds 32 information-control attribution pairings. All 16 Computer 10/12 x Sensor DR0/DR1 x ECM1/2 x ECCM1/2 combinations are tested at Reactor 6 against TL1 Kinetic and current TL2 Energy anchors. With fixed Range-3 and both TrackAware movement orders, the generated study contains 288 variants.

## Execution guards

1. Generator validation and complete legal-build enumeration.
2. Actual-consumer preflight of the generated study.
3. One-trial-per-variant full-pipeline smoke before substantive Monte Carlo.
4. EW affordability uses the accepted preserve-combat-package doctrine and actual rating-scaled ECM/ECCM power cost.
5. Intended-active fixed references must convert nonzero attack opportunities into attacks. Dynamic contexts must preserve each attack type materially active in the healthy fixed reference.
6. Win rates and rankings remain human-review evidence; no automatic candidate promotion/retuning is permitted.

Shared sensitivity and integration axes never imply symmetric technology progression across subsystem families.
