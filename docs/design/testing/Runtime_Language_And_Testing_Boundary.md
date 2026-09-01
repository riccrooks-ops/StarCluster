# Runtime Language and Testing Boundary

**Status:** Current development architecture direction, introduced for CP108.

## Production boundary
Star Cluster's shipped game and gameplay/runtime implementation remains **C# for Godot**. `StarCluster.Game` and `StarCluster.Core` must not require a Python interpreter or Python embedding library to run the game.

## Development/testing boundary
Python is explicitly permitted for:
- Monte Carlo and research simulation;
- deterministic and stochastic analysis tooling;
- test fixtures and research-engine unit tests;
- checkpoint/repository validation;
- offline data generation that produces checked-in game data or evidence.

A Python tool may validate or generate development artifacts without becoming part of the production runtime. Where generated data is consumed by the game, the checked-in schema/data contract must remain independently consumable by C#.

## Acceptance consequence
Future checkpoint guards should test the **production/runtime boundary**, not reject Python merely because a test or validation tool uses it. Historical checkpoints retain their original accepted rules and scripts for provenance.
