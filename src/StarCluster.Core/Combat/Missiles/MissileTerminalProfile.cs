using System;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Terminal-resolution equipment and provisional conversion constants for one
/// Missile Flight design.
/// </summary>
public sealed class MissileTerminalProfile
{
    public MissileTerminalProfile(
        MissileGuidanceComputerProfile guidanceComputer,
        MissileTerminalSeekerProfile? seeker = null,
        int acquisitionPenaltyPercentPerNetEcmStrength = 10,
        int stationarySearchFuelCost = 1,
        bool allowsPeerTerminalGuidance = false)
    {
        GuidanceComputer = guidanceComputer ??
            throw new ArgumentNullException(nameof(guidanceComputer));
        Seeker = seeker ?? MissileTerminalSeekerProfile.None;
        if (acquisitionPenaltyPercentPerNetEcmStrength < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(acquisitionPenaltyPercentPerNetEcmStrength));
        }
        if (stationarySearchFuelCost <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(stationarySearchFuelCost));
        }

        AcquisitionPenaltyPercentPerNetEcmStrength =
            acquisitionPenaltyPercentPerNetEcmStrength;
        StationarySearchFuelCost = stationarySearchFuelCost;
        AllowsPeerTerminalGuidance = allowsPeerTerminalGuidance;
    }

    public static MissileTerminalProfile Prototype { get; } = new(
        new MissileGuidanceComputerProfile(
            technologyLevel: 2,
            baseHitChancePercent: 65,
            minimumHitChancePercent: 5,
            maximumHitChancePercent: 95),
        new MissileTerminalSeekerProfile(
            technologyLevel: 2,
            isInstalled: true,
            baseAcquisitionChancePercent: 65,
            terminalEccmStrength: 2,
            accuracyBonusPercent: 15));

    public static MissileTerminalProfile PrototypeWithoutSeeker { get; } = new(
        new MissileGuidanceComputerProfile(
            technologyLevel: 2,
            baseHitChancePercent: 65,
            minimumHitChancePercent: 5,
            maximumHitChancePercent: 95));

    public MissileGuidanceComputerProfile GuidanceComputer { get; }

    public MissileTerminalSeekerProfile Seeker { get; }

    public int AcquisitionPenaltyPercentPerNetEcmStrength { get; }

    public int StationarySearchFuelCost { get; }

    /// <summary>
    /// Explicit capability gate for a live Current/Firm peer report to authorize
    /// a terminal attack. The baseline command-guided and prototype profiles do
    /// not gain cooperative terminal guidance merely because a peer report exists.
    /// </summary>
    public bool AllowsPeerTerminalGuidance { get; }
}
