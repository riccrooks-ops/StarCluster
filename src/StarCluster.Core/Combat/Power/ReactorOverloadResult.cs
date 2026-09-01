using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Power;

public enum ReactorOverloadOutcome
{
    SafeSuccess,
    ForcedSuccess,
    CriticalSuccess,
    Failure,
    CriticalFailure,
}

public sealed record ReactorOverloadResult(
    ReactorOverloadOutcome Outcome,
    bool WasForced,
    int? Roll,
    bool BenefitApplied,
    int PowerGained,
    int StrainGained,
    int FinalStrain,
    ComponentCondition FinalCondition);
