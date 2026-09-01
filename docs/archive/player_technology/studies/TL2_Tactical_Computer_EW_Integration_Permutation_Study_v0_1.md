# TL2 Tactical Computer / EW Integration Permutation Study v0.1

## Question

Does the legacy **+12 percentage-point ordinary Tactical Computer targeting** candidate remain a useful, bounded TL2 maturation step when placed inside the contemporary CP80 Sensor/EW and Tactical-Power environment, without simultaneously weakening the -25 degraded-fire guardrail or introducing Evasive Compensation?

## Isolation

Only Side-A ordinary Tactical Computer assistance varies between +10 and +12. The actual-consumer override preserves the existing PDS local fire-control base and changes only the external main-computer assistance by the same +2 delta. Missile guidance remains governed by the missile Guidance Computer; an Operational launcher's +10/+12 main-computer value does not increase ordinary missile terminal guidance.

The study holds reactor output at 5 TP, degraded-fire penalty at -25, Evasive Compensation at 0, Sensor reach and overload unchanged, EW overload unchanged, and all TL1 weapon/defense/movement values fixed.

## 96-variant matrix

The block is 2 Side-A direct-fire families x 2 opponent families x 3 geometries x 4 EW response packages x 2 computer values = **96 variants**. The four response packages are:

1. clean Firm reference;
2. old TL1 Sensor + ECCM2 against ECM2;
3. TL2 Sensor DR1 + ECCM1 against ECM2;
4. explicit study-only degraded fire at -25 against ECM2 with no ECCM.

Each +10/+12 pair shares a common random stream through the same `comparisonGroup`.

## Interpretation

Release gates verify coverage, consumer mechanics, frozen dependencies, Firm restoration, degraded-fire isolation, and production exclusions. They do not require a target win-rate improvement. Review the paired deltas in ordinary hit chance, direct-hit rate, pacing, conditional win share, and PDS behavior. The +12 candidate should be meaningful but should not erase EW power tradeoffs, make degraded fire an ECCM substitute, or create an outsized offensive spike.

No value is automatically promoted by a green study.
