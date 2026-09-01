namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// Describes whether a direct-fire commitment is legal at the time the player
/// issues it. A specific missile may be reserved only when it is positively
/// identified and currently visible to the weapon; only range may become valid
/// later during missile movement.
/// </summary>
public enum DirectFireTargetEligibilityStatus
{
    EligibleNow,
    EligibleForSpecificMissileReserve,
    MissingFirmTrack,
    MissingTrackedCoordinate,
    BlockedLineOfSight,
    OutOfRange,
    WeaponCannotInterceptMissiles,
}
