using System;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// Immutable direct-fire commitment. A weapon may attack a ship, reserve its
/// shot for one known hostile salvo, reserve its shot for the first eligible
/// hostile salvo, or explicitly hold fire. Missile-interception commitments
/// can be converted into one phase-scoped defensive system.
/// </summary>
public sealed class DirectFireOrder
{
    private DirectFireOrder(
        string id,
        string weaponId,
        string defenderShipId,
        TacticalSide ownerSide,
        HexCoord originCoordinate,
        DirectFireWeaponProfile weaponProfile,
        DirectFireOrderType orderType,
        string? targetShipId,
        string? targetMissileSalvoId)
    {
        ValidateId(id, nameof(id));
        ValidateId(weaponId, nameof(weaponId));
        ValidateId(defenderShipId, nameof(defenderShipId));

        if (ownerSide == TacticalSide.Unspecified || !Enum.IsDefined(ownerSide))
        {
            throw new ArgumentOutOfRangeException(
                nameof(ownerSide),
                ownerSide,
                "A concrete player or enemy tactical side is required.");
        }

        Id = id;
        WeaponId = weaponId;
        DefenderShipId = defenderShipId;
        OwnerSide = ownerSide;
        OriginCoordinate = originCoordinate;
        WeaponProfile = weaponProfile ??
            throw new ArgumentNullException(nameof(weaponProfile));
        OrderType = orderType;
        TargetShipId = targetShipId;
        TargetMissileSalvoId = targetMissileSalvoId;
    }

    public string Id { get; }

    public string WeaponId { get; }

    public string DefenderShipId { get; }

    public TacticalSide OwnerSide { get; }

    public HexCoord OriginCoordinate { get; }

    public DirectFireWeaponProfile WeaponProfile { get; }

    public DirectFireOrderType OrderType { get; }

    public string? TargetShipId { get; }

    public string? TargetMissileSalvoId { get; }

    public bool CreatesHeldInterception =>
        OrderType is DirectFireOrderType.InterceptSpecificMissile or
            DirectFireOrderType.HoldForAnyMissile;

    public static DirectFireOrder FireAtShip(
        string id,
        string weaponId,
        string defenderShipId,
        TacticalSide ownerSide,
        HexCoord originCoordinate,
        DirectFireWeaponProfile weaponProfile,
        string targetShipId)
    {
        ValidateId(targetShipId, nameof(targetShipId));
        return new DirectFireOrder(
            id,
            weaponId,
            defenderShipId,
            ownerSide,
            originCoordinate,
            weaponProfile,
            DirectFireOrderType.FireAtShip,
            targetShipId,
            targetMissileSalvoId: null);
    }

    public static DirectFireOrder InterceptSpecificMissile(
        string id,
        string weaponId,
        string defenderShipId,
        TacticalSide ownerSide,
        HexCoord originCoordinate,
        DirectFireWeaponProfile weaponProfile,
        string targetMissileSalvoId)
    {
        ArgumentNullException.ThrowIfNull(weaponProfile);

        if (!weaponProfile.CanInterceptMissiles)
        {
            throw new ArgumentException(
                "The supplied direct-fire weapon cannot intercept missiles.",
                nameof(weaponProfile));
        }

        ValidateId(targetMissileSalvoId, nameof(targetMissileSalvoId));
        return new DirectFireOrder(
            id,
            weaponId,
            defenderShipId,
            ownerSide,
            originCoordinate,
            weaponProfile,
            DirectFireOrderType.InterceptSpecificMissile,
            targetShipId: null,
            targetMissileSalvoId: targetMissileSalvoId);
    }

    public static DirectFireOrder HoldForAnyMissile(
        string id,
        string weaponId,
        string defenderShipId,
        TacticalSide ownerSide,
        HexCoord originCoordinate,
        DirectFireWeaponProfile weaponProfile)
    {
        ArgumentNullException.ThrowIfNull(weaponProfile);

        if (!weaponProfile.CanInterceptMissiles)
        {
            throw new ArgumentException(
                "The supplied direct-fire weapon cannot intercept missiles.",
                nameof(weaponProfile));
        }

        return new DirectFireOrder(
            id,
            weaponId,
            defenderShipId,
            ownerSide,
            originCoordinate,
            weaponProfile,
            DirectFireOrderType.HoldForAnyMissile,
            targetShipId: null,
            targetMissileSalvoId: null);
    }

    public static DirectFireOrder HoldFire(
        string id,
        string weaponId,
        string defenderShipId,
        TacticalSide ownerSide,
        HexCoord originCoordinate,
        DirectFireWeaponProfile weaponProfile) => new(
            id,
            weaponId,
            defenderShipId,
            ownerSide,
            originCoordinate,
            weaponProfile,
            DirectFireOrderType.HoldFire,
            targetShipId: null,
            targetMissileSalvoId: null);

    public MissileDefenseSystem CreateHeldDefenseSystem(
        string defenseSystemId,
        int priority = 0)
    {
        if (!CreatesHeldInterception)
        {
            throw new InvalidOperationException(
                "Only missile-interception commitments create held defenses.");
        }

        return new MissileDefenseSystem(
            defenseSystemId,
            DefenderShipId,
            OwnerSide,
            OriginCoordinate,
            WeaponProfile.ToInterceptionProfile(),
            priority,
            MissileDefenseSourceType.HeldDirectFireWeapon,
            TargetMissileSalvoId,
            requiresLineOfSight: true,
            requiresFirmTacticalTrack: true);
    }

    private static void ValidateId(string value, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException(
                "A stable non-empty ID is required.",
                parameterName);
        }
    }
}
