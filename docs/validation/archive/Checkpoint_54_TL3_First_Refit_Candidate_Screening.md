# Checkpoint 54 - TL3 First-Refit Candidate Screening

## Purpose

Checkpoint 54 begins executable TL3 work after Checkpoint 53a accepted and froze the TL1/TL2 standard and AUX technology baseline. TL3 is the first major cruiser refit: **2 Weapon Bays and 2 AUX Capacity**. This checkpoint screens that structural step before any TL3 profile is promoted.

## Frozen boundary

Every ScenarioRunner JSON file present in the accepted Checkpoint 53a repository is SHA-256 locked. The new TL3 studies are additive. Existing TL1/TL2 one-bay variants retain their original variant salt and execution path.

## TL3 standard-profile screen

Three provisional vectors are evaluated:

1. **Capacity-only control** - accepted TL2 numerical values with TL3 installation capacity. This isolates the value of the second Weapon Bay and second AUX Capacity.
2. **Balanced candidate** - modest improvements across durability, reactor/fire control, movement, range, and weapon characteristics.
3. **Output-forward sensitivity control** - a stronger numerical vector used to detect whether extra output plus extra capacity overshoots the desired TL step.

No vector is promoted automatically.

## Two Weapon Bays

Checkpoint 54 evaluates all nine ordered primary/secondary combinations across Kinetic, Energy, and Missile. Each bay is one attack package. The primary bay drives the opponent-aware range policy for this screening pass; the secondary bay fires opportunistically when legal. That policy is an evaluation abstraction, not the final tactical UI/doctrine contract.

Same-family ammunition-fed bays draw from the same shipwide family reserve.

## Two AUX Capacity

Thirteen curated capacity-2 packages cover representative defensive, power, shield-support, ammunition/endurance, and mixed-role combinations. They are runtime screening abstractions. They do not imply that two installed AUX components collapse into one hidden internal-damage exposure entry in the final ship model.

## Tactical Power envelope

The power-envelope study compares Combat Battery, Power Capacitor, and a TL3 Auxiliary Reactor candidate under normal and sustained two-bay demand. Accepted Battery and Capacitor semantics remain unchanged. The Auxiliary Reactor candidate consumes both AUX Capacity and supplies +1 renewable Tactical Power.

## Workload

Checkpoint 54 adds 870 Monte Carlo variants:

- 72 standard-profile variants;
- 141 two-bay loadout variants;
- 585 two-AUX-capacity variants; and
- 72 power-envelope variants.

Combined with the frozen Checkpoint 53a corpus, the checkpoint contains **35 stages / 9,877 Monte Carlo variants / 98.77 million trials** at 10,000 trials per variant.

## Acceptance questions

Execution success is necessary but not sufficient. Review must answer:

- Does the second Weapon Bay alone create a meaningful but not overwhelming TL2->TL3 progression?
- Which standard TL3 vector, if any, is healthy enough to promote?
- Do mixed and same-family two-bay loadouts retain meaningful identities and opportunity costs?
- Are any two-AUX packages compulsory or effectively dead?
- Do Battery, Capacitor, and Auxiliary Reactor occupy distinct and useful roles under actual TL3 power stress?
- Can TL3 be promoted without reopening accepted TL1/TL2 values?

TL4-TL9 executable generation remains deferred until TL3 is explicitly accepted.
