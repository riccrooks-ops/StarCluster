# Checkpoint 139 — Combat-Model DEF/RES Reconciliation Foundation

CP139 is a research-mechanics reconciliation checkpoint on the CP138 full repository. It does **not** promote new production numbers or replace the production C#/Godot damage path.

The default/production damage model remains `penetration-hardening-v1`. The opt-in Python canonical research path adds `def-res-v1`: Shield DEF is stochastic whole-packet deflection after SPEN reduction (45 pp effective cap); Armor RES is fractional mitigation after APEN reduction (95 pp cap), with unspent raw damage carried inward after Armor collapse.

The research candidate also carries the latest K/E/GP offense centers, v19 PDS centers, +10 DEF Shield Hardener interpretation, and the two independently guided/PDS-visible Swarmer sub-Flight structure. CP138 movement, range, Sensors/EW, Tactical Power allocation, Damage Control, construction, and other whole-ship mechanics remain the surrounding context unless explicitly superseded.

CP139 is intentionally not Stage-A ready. Blocking follow-on work is: (1) v22C reactor/TP resource environments, (2) dynamic TP-conflict counterfactual telemetry, and (3) executable bindings for the ten Stage-A combat strata.

One-trial reconciliation smoke outcomes are mechanics/execution evidence only, never balance evidence.
