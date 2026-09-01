namespace StarCluster.Core.Combat.Tactics;

public enum EcmActivationHeuristic
{
    Never,
    AlwaysNormal,
    PreserveOffenseAndEccm,
    PreserveCombatPackageAndEccm,
}

public enum EccmActivationHeuristic
{
    Never,
    ReactiveOnFirmDegradation,
}

/// <summary>
/// Player-visible-information inputs for an EW doctrine decision. The policy
/// deliberately consumes only own-ship power/capability data, observed track
/// degradation, and visible threat class. Hidden enemy ECM ratings and the
/// internal Jamming Margin are not policy inputs.
/// </summary>
public sealed record ElectronicWarfareDoctrineContext(
    int SpendableTacticalPower,
    int EcmNormalPowerCost,
    int EccmNormalPowerCost,
    int ReadyOffensivePower,
    int PlannedPdsPower,
    bool EcmAvailable,
    bool EccmAvailable,
    bool FirmTrackWasDegradedByObservedEcm)
{
    public void Validate()
    {
        if (SpendableTacticalPower < 0 || EcmNormalPowerCost < 0 ||
            EccmNormalPowerCost < 0 || ReadyOffensivePower < 0 ||
            PlannedPdsPower < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(SpendableTacticalPower),
                "EW doctrine power inputs must be non-negative.");
        }
    }
}

public static class ElectronicWarfareDoctrineService
{
    public static bool ShouldActivateEcm(
        EcmActivationHeuristic heuristic,
        ElectronicWarfareDoctrineContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        context.Validate();
        if (!context.EcmAvailable || context.EcmNormalPowerCost <= 0 ||
            context.SpendableTacticalPower < context.EcmNormalPowerCost)
        {
            return false;
        }

        int remaining = context.SpendableTacticalPower -
            context.EcmNormalPowerCost;
        int eccmHeadroom = context.EccmAvailable
            ? context.EccmNormalPowerCost
            : 0;

        return heuristic switch
        {
            EcmActivationHeuristic.Never => false,
            EcmActivationHeuristic.AlwaysNormal => true,
            EcmActivationHeuristic.PreserveOffenseAndEccm =>
                remaining >= checked(
                    context.ReadyOffensivePower + eccmHeadroom),
            EcmActivationHeuristic.PreserveCombatPackageAndEccm =>
                remaining >= checked(
                    context.ReadyOffensivePower + context.PlannedPdsPower +
                    eccmHeadroom),
            _ => throw new ArgumentOutOfRangeException(nameof(heuristic)),
        };
    }

    public static bool ShouldActivateEccm(
        EccmActivationHeuristic heuristic,
        ElectronicWarfareDoctrineContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        context.Validate();
        if (!context.EccmAvailable || context.EccmNormalPowerCost <= 0 ||
            context.SpendableTacticalPower < context.EccmNormalPowerCost)
        {
            return false;
        }

        return heuristic switch
        {
            EccmActivationHeuristic.Never => false,
            EccmActivationHeuristic.ReactiveOnFirmDegradation =>
                context.FirmTrackWasDegradedByObservedEcm,
            _ => throw new ArgumentOutOfRangeException(nameof(heuristic)),
        };
    }
}
