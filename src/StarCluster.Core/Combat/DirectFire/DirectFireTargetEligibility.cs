using System;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// Centralizes targeting rules used during the Direct Fire phase. Current ship
/// attacks may use either Firm or Approximate tracks. Approximate track applies
/// a universal -25 percentage-point modifier. Fire beyond Standard Range but
/// within Maximum Range applies a universal -10 percentage-point modifier; the
/// two modifiers stack. Missile interception remains Firm-only and does not use
/// the ordinary ship-attack extended-range rule.
/// </summary>
public static class DirectFireTargetEligibility
{
    public const int ApproximateTrackAccuracyPenaltyPp = -25;
    public const int ExtendedRangeAccuracyPenaltyPp = -10;

    public static DirectFireTargetEligibilityResult EvaluateShipAttack(
        TacticalTrackQuality trackQuality,
        HexCoord? trackedCoordinate,
        HexCoord weaponCoordinate,
        DirectFireWeaponProfile weapon,
        bool hasLineOfSight,
        TacticalComputerFireControlProfile? tacticalComputer = null)
    {
        ArgumentNullException.ThrowIfNull(weapon);
        _ = tacticalComputer; // Retained only for source compatibility; current universal rules do not consult it.

        bool approximate = trackQuality == TacticalTrackQuality.Approximate;
        if (trackQuality != TacticalTrackQuality.Firm && !approximate)
        {
            return new DirectFireTargetEligibilityResult(
                DirectFireTargetEligibilityStatus.MissingFirmTrack,
                trackedCoordinate,
                trackedCoordinate.HasValue
                    ? weaponCoordinate.DistanceTo(trackedCoordinate.Value)
                    : null);
        }

        DirectFireTargetEligibilityResult common = EvaluatePhysicalGates(
            trackedCoordinate,
            weaponCoordinate,
            hasLineOfSight,
            usesApproximateTrackFire: approximate,
            accuracyModifier: approximate ? ApproximateTrackAccuracyPenaltyPp : 0,
            usesExtendedRangeFire: false);
        if (common.Status != DirectFireTargetEligibilityStatus.EligibleNow)
        {
            return common;
        }

        int distance = common.DistanceHexes!.Value;
        if (distance > weapon.MaximumRangeHexes)
        {
            return common with
            {
                Status = DirectFireTargetEligibilityStatus.OutOfRange,
            };
        }

        bool extended = distance > weapon.StandardRangeHexes;
        return extended
            ? common with
            {
                UsesExtendedRangeFire = true,
                AccuracyModifier = common.AccuracyModifier + ExtendedRangeAccuracyPenaltyPp,
            }
            : common;
    }

    public static DirectFireTargetEligibilityResult EvaluateSpecificMissileOrder(
        TacticalTrackQuality trackQuality,
        HexCoord? trackedCoordinate,
        HexCoord weaponCoordinate,
        DirectFireWeaponProfile weapon,
        bool hasLineOfSight)
    {
        ArgumentNullException.ThrowIfNull(weapon);

        if (!weapon.CanInterceptMissiles)
        {
            return new DirectFireTargetEligibilityResult(
                DirectFireTargetEligibilityStatus.WeaponCannotInterceptMissiles,
                trackedCoordinate,
                trackedCoordinate.HasValue
                    ? weaponCoordinate.DistanceTo(trackedCoordinate.Value)
                    : null);
        }

        if (trackQuality != TacticalTrackQuality.Firm)
        {
            return new DirectFireTargetEligibilityResult(
                DirectFireTargetEligibilityStatus.MissingFirmTrack,
                trackedCoordinate,
                trackedCoordinate.HasValue
                    ? weaponCoordinate.DistanceTo(trackedCoordinate.Value)
                    : null);
        }

        DirectFireTargetEligibilityResult common = EvaluatePhysicalGates(
            trackedCoordinate,
            weaponCoordinate,
            hasLineOfSight,
            usesApproximateTrackFire: false,
            accuracyModifier: 0,
            usesExtendedRangeFire: false);
        if (common.Status != DirectFireTargetEligibilityStatus.EligibleNow)
        {
            return common;
        }

        return common.DistanceHexes!.Value <= weapon.MaximumRangeHexes
            ? common
            : common with
            {
                Status = DirectFireTargetEligibilityStatus.EligibleForSpecificMissileReserve,
            };
    }

    private static DirectFireTargetEligibilityResult EvaluatePhysicalGates(
        HexCoord? trackedCoordinate,
        HexCoord weaponCoordinate,
        bool hasLineOfSight,
        bool usesApproximateTrackFire,
        int accuracyModifier,
        bool usesExtendedRangeFire)
    {
        if (!trackedCoordinate.HasValue)
        {
            return new DirectFireTargetEligibilityResult(
                DirectFireTargetEligibilityStatus.MissingTrackedCoordinate,
                null,
                null,
                usesApproximateTrackFire,
                accuracyModifier,
                usesExtendedRangeFire);
        }

        int distance = weaponCoordinate.DistanceTo(trackedCoordinate.Value);
        if (!hasLineOfSight)
        {
            return new DirectFireTargetEligibilityResult(
                DirectFireTargetEligibilityStatus.BlockedLineOfSight,
                trackedCoordinate,
                distance,
                usesApproximateTrackFire,
                accuracyModifier,
                usesExtendedRangeFire);
        }

        return new DirectFireTargetEligibilityResult(
            DirectFireTargetEligibilityStatus.EligibleNow,
            trackedCoordinate,
            distance,
            usesApproximateTrackFire,
            accuracyModifier,
            usesExtendedRangeFire);
    }
}
