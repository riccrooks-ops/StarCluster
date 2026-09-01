namespace StarCluster.Core.Combat.DirectFire;

public sealed record DirectFireAccuracyResult(
    int BaseChance,
    int WeaponAccuracy,
    int TargetingComputerBonus,
    int RangePenalty,
    int TargetEvasivePenalty,
    int ShooterEvasivePenalty,
    int TargetMobilityBonus,
    int OtherModifiers,
    int UnboundedChance,
    int FinalChance);
