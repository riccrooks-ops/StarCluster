using System;

namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// Data-driven ship-level fire-control capability supplied by the installed
/// Tactical Computer. Current direct-fire architecture uses a universal
/// Approximate-track penalty, so the historical degraded-fire penalty is
/// retained only for compatibility/provenance and is not consulted by current
/// ship-attack eligibility.
/// </summary>
public sealed class TacticalComputerFireControlProfile
{
    public TacticalComputerFireControlProfile(
        int technologyLevel,
        int approximateTrackDirectFireAccuracyPenalty = 0)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(technologyLevel),
                technologyLevel,
                "Technology level cannot be negative.");
        }

        if (approximateTrackDirectFireAccuracyPenalty is < 0 or > 100)
        {
            throw new ArgumentOutOfRangeException(
                nameof(approximateTrackDirectFireAccuracyPenalty),
                approximateTrackDirectFireAccuracyPenalty,
                "Legacy Approximate-track direct-fire accuracy penalty must be between 0 and 100 percentage points.");
        }

        TechnologyLevel = technologyLevel;
        ApproximateTrackDirectFireAccuracyPenalty =
            approximateTrackDirectFireAccuracyPenalty;
    }

    public int TechnologyLevel { get; }

    /// <summary>
    /// Historical positive penalty magnitude retained for old component data
    /// and replay provenance. Current ordinary ship-target direct fire uses the
    /// universal combat modifier in DirectFireTargetEligibility instead.
    /// </summary>
    public int ApproximateTrackDirectFireAccuracyPenalty { get; }

    /// <summary>
    /// Historical compatibility helper only. It does not gate current
    /// Approximate-track direct-fire eligibility.
    /// </summary>
    public bool SupportsApproximateTrackDirectFire =>
        ApproximateTrackDirectFireAccuracyPenalty > 0;
}
