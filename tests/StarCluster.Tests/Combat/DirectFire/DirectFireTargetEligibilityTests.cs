using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class DirectFireTargetEligibilityTests
{
    private static readonly HexCoord WeaponCoordinate = new(0, 0);

    [Fact]
    public void ShipAttackRequiresFirmTrack()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Stale,
                new HexCoord(1, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.MissingFirmTrack,
            result.Status);
        Assert.False(result.CanCommitNow);
    }

    [Fact]
    public void ShipAttackRequiresTrackedCoordinate()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Firm,
                null,
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.MissingTrackedCoordinate,
            result.Status);
    }

    [Fact]
    public void ShipAttackRequiresCurrentLineOfSight()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Firm,
                new HexCoord(1, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: false);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.BlockedLineOfSight,
            result.Status);
        Assert.False(result.CanCommitNow);
    }

    [Fact]
    public void ShipAttackRequiresCurrentRange()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Firm,
                new HexCoord(5, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.OutOfRange,
            result.Status);
        Assert.False(result.CanCommitNow);
    }

    [Fact]
    public void ShipAttackIsEligibleWhenAllCurrentRequirementsPass()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Firm,
                new HexCoord(3, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.EligibleNow,
            result.Status);
        Assert.True(result.CanCommitNow);
    }

    [Fact]
    public void ApproximateShipTrackUsesUniversalPenaltyWithoutComputerOrWeaponTrait()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Approximate,
                new HexCoord(2, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(DirectFireTargetEligibilityStatus.EligibleNow, result.Status);
        Assert.True(result.CanCommitNow);
        Assert.True(result.UsesApproximateTrackFire);
        Assert.False(result.UsesExtendedRangeFire);
        Assert.Equal(-25, result.AccuracyModifier);
    }

    [Fact]
    public void TacticalComputerPenaltyDoesNotOwnCurrentApproximateFireRule()
    {
        DirectFireTargetEligibilityResult noSupport =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Approximate,
                new HexCoord(2, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true,
                tacticalComputer: Computer(penalty: 0));
        DirectFireTargetEligibilityResult legacyDifferentPenalty =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Approximate,
                new HexCoord(2, 0),
                WeaponCoordinate,
                Weapon(range: 4, allowsApproximate: true),
                hasLineOfSight: true,
                tacticalComputer: Computer(penalty: 10));

        Assert.True(noSupport.CanCommitNow);
        Assert.Equal(-25, noSupport.AccuracyModifier);
        Assert.True(legacyDifferentPenalty.CanCommitNow);
        Assert.Equal(-25, legacyDifferentPenalty.AccuracyModifier);
    }

    [Fact]
    public void ExtendedRangeUsesUniversalTenPointPenalty()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Firm,
                new HexCoord(4, 0),
                WeaponCoordinate,
                Weapon(range: 5, standardRange: 3),
                hasLineOfSight: true);

        Assert.True(result.CanCommitNow);
        Assert.False(result.UsesApproximateTrackFire);
        Assert.True(result.UsesExtendedRangeFire);
        Assert.Equal(-10, result.AccuracyModifier);
    }

    [Fact]
    public void ApproximateAndExtendedRangePenaltiesStack()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Approximate,
                new HexCoord(4, 0),
                WeaponCoordinate,
                Weapon(range: 5, standardRange: 3),
                hasLineOfSight: true);

        Assert.True(result.CanCommitNow);
        Assert.True(result.UsesApproximateTrackFire);
        Assert.True(result.UsesExtendedRangeFire);
        Assert.Equal(-35, result.AccuracyModifier);
    }

    [Fact]
    public void FirmTrackInsideStandardRangeUsesNoPenalty()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateShipAttack(
                TacticalTrackQuality.Firm,
                new HexCoord(3, 0),
                WeaponCoordinate,
                Weapon(range: 5, standardRange: 3),
                hasLineOfSight: true);

        Assert.True(result.CanCommitNow);
        Assert.False(result.UsesApproximateTrackFire);
        Assert.False(result.UsesExtendedRangeFire);
        Assert.Equal(0, result.AccuracyModifier);
    }

    [Fact]
    public void MissileInterceptionRemainsFirmOnlyEvenForTraitWeapon()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateSpecificMissileOrder(
                TacticalTrackQuality.Approximate,
                new HexCoord(1, 0),
                WeaponCoordinate,
                Weapon(range: 4, allowsApproximate: true),
                hasLineOfSight: true);

        Assert.Equal(DirectFireTargetEligibilityStatus.MissingFirmTrack, result.Status);
        Assert.False(result.CanCommitSpecificMissileOrder);
    }

    [Fact]
    public void SpecificMissileOrderRequiresInterceptCapableWeapon()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateSpecificMissileOrder(
                TacticalTrackQuality.Firm,
                new HexCoord(1, 0),
                WeaponCoordinate,
                Weapon(range: 4, canIntercept: false),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.WeaponCannotInterceptMissiles,
            result.Status);
        Assert.False(result.CanCommitSpecificMissileOrder);
    }

    [Fact]
    public void SpecificMissileOrderRequiresFirmTrack()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateSpecificMissileOrder(
                TacticalTrackQuality.Approximate,
                new HexCoord(1, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.MissingFirmTrack,
            result.Status);
        Assert.False(result.CanCommitSpecificMissileOrder);
    }

    [Fact]
    public void SpecificMissileOrderRequiresCurrentLineOfSight()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateSpecificMissileOrder(
                TacticalTrackQuality.Firm,
                new HexCoord(1, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: false);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.BlockedLineOfSight,
            result.Status);
        Assert.False(result.CanCommitSpecificMissileOrder);
    }

    [Fact]
    public void SpecificMissileOrderFiresImmediatelyWhenCurrentlyInRange()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateSpecificMissileOrder(
                TacticalTrackQuality.Firm,
                new HexCoord(2, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.EligibleNow,
            result.Status);
        Assert.True(result.CanCommitSpecificMissileOrder);
        Assert.False(result.IsReserveOnly);
    }

    [Fact]
    public void SpecificMissileOrderMayReserveOnlyForCurrentRangeShortfall()
    {
        DirectFireTargetEligibilityResult result =
            DirectFireTargetEligibility.EvaluateSpecificMissileOrder(
                TacticalTrackQuality.Firm,
                new HexCoord(5, 0),
                WeaponCoordinate,
                Weapon(range: 4),
                hasLineOfSight: true);

        Assert.Equal(
            DirectFireTargetEligibilityStatus.EligibleForSpecificMissileReserve,
            result.Status);
        Assert.True(result.CanCommitSpecificMissileOrder);
        Assert.True(result.IsReserveOnly);
    }

    private static DirectFireWeaponProfile Weapon(
        int range,
        bool canIntercept = true,
        bool allowsApproximate = false,
        int? standardRange = null) => new(
        technologyLevel: 2,
        maximumRangeHexes: range,
        canInterceptMissiles: canIntercept,
        allowsApproximateTrackFire: allowsApproximate,
        standardRangeHexes: standardRange);

    private static TacticalComputerFireControlProfile Computer(int penalty) => new(
        technologyLevel: 1,
        approximateTrackDirectFireAccuracyPenalty: penalty);
}
