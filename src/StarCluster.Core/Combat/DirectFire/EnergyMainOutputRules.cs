using System;

namespace StarCluster.Core.Combat.DirectFire;

public enum EnergyMainOutputMode
{
    Low,
    Standard,
    Overload,
}

/// <summary>
/// Universal Energy-main output relationship. Low output uses half Standard
/// TP/DAM rounded up. Overload uses 1.5x Standard TP/DAM rounded up and always
/// applies one point of weapon Strain. Forced-overload consequences beyond a
/// weapon's Strain limit remain a separate overload-resolution concern.
/// </summary>
public sealed record EnergyMainOutputResult(
    EnergyMainOutputMode Mode,
    int TacticalPowerCost,
    int Damage,
    int StrainGained);

public static class EnergyMainOutputRules
{
    public static EnergyMainOutputResult Resolve(
        int standardTacticalPower,
        int standardDamage,
        EnergyMainOutputMode mode)
    {
        if (standardTacticalPower <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(standardTacticalPower));
        }
        if (standardDamage <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(standardDamage));
        }

        return mode switch
        {
            EnergyMainOutputMode.Low => new(
                mode,
                DivideByTwoRoundedUp(standardTacticalPower),
                DivideByTwoRoundedUp(standardDamage),
                0),
            EnergyMainOutputMode.Standard => new(
                mode,
                standardTacticalPower,
                standardDamage,
                0),
            EnergyMainOutputMode.Overload => new(
                mode,
                MultiplyByThreeHalvesRoundedUp(standardTacticalPower),
                MultiplyByThreeHalvesRoundedUp(standardDamage),
                1),
            _ => throw new ArgumentOutOfRangeException(nameof(mode)),
        };
    }

    private static int DivideByTwoRoundedUp(int value) => checked((value + 1) / 2);

    private static int MultiplyByThreeHalvesRoundedUp(int value) =>
        checked((checked(value * 3) + 1) / 2);
}
