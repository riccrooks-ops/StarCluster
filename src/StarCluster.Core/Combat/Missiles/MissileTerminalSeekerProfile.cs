using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Optional co-located terminal seeker. It supplies terminal acquisition ECCM
/// and a separate accuracy bonus but owns no independent cruise track.
/// </summary>
public sealed class MissileTerminalSeekerProfile
{
    public MissileTerminalSeekerProfile(
        int technologyLevel,
        bool isInstalled,
        int baseAcquisitionChancePercent,
        int terminalEccmStrength,
        int accuracyBonusPercent,
        int minimumAcquisitionChancePercent = 5,
        int maximumAcquisitionChancePercent = 95)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(technologyLevel));
        }

        ValidatePercent(
            baseAcquisitionChancePercent,
            nameof(baseAcquisitionChancePercent));
        ValidatePercent(
            accuracyBonusPercent,
            nameof(accuracyBonusPercent));
        ValidatePercent(
            minimumAcquisitionChancePercent,
            nameof(minimumAcquisitionChancePercent));
        ValidatePercent(
            maximumAcquisitionChancePercent,
            nameof(maximumAcquisitionChancePercent));
        if (terminalEccmStrength < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(terminalEccmStrength));
        }
        if (minimumAcquisitionChancePercent > maximumAcquisitionChancePercent)
        {
            throw new ArgumentException(
                "Minimum acquisition chance cannot exceed maximum acquisition chance.");
        }

        TechnologyLevel = technologyLevel;
        IsInstalled = isInstalled;
        BaseAcquisitionChancePercent = baseAcquisitionChancePercent;
        TerminalEccmStrength = terminalEccmStrength;
        AccuracyBonusPercent = accuracyBonusPercent;
        MinimumAcquisitionChancePercent = minimumAcquisitionChancePercent;
        MaximumAcquisitionChancePercent = maximumAcquisitionChancePercent;
    }

    public static MissileTerminalSeekerProfile None { get; } = new(
        technologyLevel: 0,
        isInstalled: false,
        baseAcquisitionChancePercent: 0,
        terminalEccmStrength: 0,
        accuracyBonusPercent: 0,
        minimumAcquisitionChancePercent: 0,
        maximumAcquisitionChancePercent: 0);

    public int TechnologyLevel { get; }

    public bool IsInstalled { get; }

    public int BaseAcquisitionChancePercent { get; }

    public int TerminalEccmStrength { get; }

    public int AccuracyBonusPercent { get; }

    public int MinimumAcquisitionChancePercent { get; }

    public int MaximumAcquisitionChancePercent { get; }

    public int ClampAcquisitionChance(int chancePercent) => Math.Clamp(
        chancePercent,
        MinimumAcquisitionChancePercent,
        MaximumAcquisitionChancePercent);

    private static void ValidatePercent(int value, string parameterName)
    {
        if (value is < 0 or > 100)
        {
            throw new ArgumentOutOfRangeException(
                parameterName,
                value,
                "Percent values must be from 0 through 100.");
        }
    }
}
