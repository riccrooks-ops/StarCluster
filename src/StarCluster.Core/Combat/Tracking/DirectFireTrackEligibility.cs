namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Generic precision direct fire requires a Firm track. Weapon-specific
/// degraded-fire eligibility is resolved by DirectFireTargetEligibility because
/// it also depends on the weapon capability and the current Tactical Computer
/// fire-control profile.
/// </summary>
public static class DirectFireTrackEligibility
{
    public static bool CanTarget(TacticalTrackRecord? record) =>
        record is { SupportsPrecisionDirectFire: true };
}
