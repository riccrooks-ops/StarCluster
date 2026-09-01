using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Power;

public sealed record ReactorPowerProfile
{
    public ReactorPowerProfile(
        int operationalOutput,
        int degradedOutput,
        int emergencyOutput,
        int overloadOutput,
        int strainLimit,
        int forcedOverloadSuccessPercent)
    {
        if (operationalOutput < 0 || degradedOutput < 0 ||
            emergencyOutput < 0 || overloadOutput < 0 || strainLimit < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(operationalOutput),
                "Reactor output and Strain values cannot be negative.");
        }
        if (forcedOverloadSuccessPercent is < 0 or > 100)
        {
            throw new ArgumentOutOfRangeException(
                nameof(forcedOverloadSuccessPercent));
        }

        OperationalOutput = operationalOutput;
        DegradedOutput = degradedOutput;
        EmergencyOutput = emergencyOutput;
        OverloadOutput = overloadOutput;
        StrainLimit = strainLimit;
        ForcedOverloadSuccessPercent = forcedOverloadSuccessPercent;
    }

    public int OperationalOutput { get; }

    public int DegradedOutput { get; }

    public int EmergencyOutput { get; }

    public int OverloadOutput { get; }

    public int StrainLimit { get; }

    public int ForcedOverloadSuccessPercent { get; }

    public int OutputFor(ComponentCondition condition) => condition switch
    {
        ComponentCondition.Operational => OperationalOutput,
        ComponentCondition.Degraded => DegradedOutput,
        ComponentCondition.Disabled => EmergencyOutput,
        ComponentCondition.Destroyed => 0,
        _ => throw new ArgumentOutOfRangeException(nameof(condition)),
    };
}
