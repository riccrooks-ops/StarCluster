using System;
using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// One point-defense installation or held direct-fire interception order
/// positioned on the tactical map for the current Missile / Interception
/// phase.
/// </summary>
public sealed class MissileDefenseSystem
{
    public MissileDefenseSystem(
        string id,
        string defenderShipId,
        TacticalSide ownerSide,
        HexCoord coordinate,
        MissileDefenseProfile profile,
        int priority = 0,
        MissileDefenseSourceType sourceType = MissileDefenseSourceType.PointDefenseSystem,
        string? targetMissileSalvoId = null,
        bool requiresLineOfSight = false,
        bool requiresFirmTacticalTrack = false)
    {
        ValidateId(id, nameof(id));
        ValidateId(defenderShipId, nameof(defenderShipId));

        if (ownerSide == TacticalSide.Unspecified ||
            !Enum.IsDefined(ownerSide))
        {
            throw new ArgumentOutOfRangeException(
                nameof(ownerSide),
                ownerSide,
                "A concrete player or enemy tactical side is required.");
        }

        if (priority < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(priority),
                priority,
                "Interception priority cannot be negative.");
        }

        if (!Enum.IsDefined(sourceType))
        {
            throw new ArgumentOutOfRangeException(
                nameof(sourceType),
                sourceType,
                "A recognized defense source type is required.");
        }

        if (targetMissileSalvoId is not null)
        {
            ValidateId(targetMissileSalvoId, nameof(targetMissileSalvoId));
        }

        Id = id;
        DefenderShipId = defenderShipId;
        OwnerSide = ownerSide;
        Coordinate = coordinate;
        Profile = profile ?? throw new ArgumentNullException(nameof(profile));
        Priority = priority;
        SourceType = sourceType;
        TargetMissileSalvoId = targetMissileSalvoId;
        RequiresLineOfSight = requiresLineOfSight;
        RequiresFirmTacticalTrack = requiresFirmTacticalTrack;
    }

    public string Id { get; }

    public string DefenderShipId { get; }

    public TacticalSide OwnerSide { get; }

    public HexCoord Coordinate { get; }

    public MissileDefenseProfile Profile { get; }

    public int Priority { get; }

    public MissileDefenseSourceType SourceType { get; }

    public string? TargetMissileSalvoId { get; }

    public bool RequiresLineOfSight { get; }

    public bool RequiresFirmTacticalTrack { get; }

    public bool CanEngage(
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate)
    {
        ArgumentNullException.ThrowIfNull(salvo);

        if (salvo.OwnerSide == TacticalSide.Unspecified ||
            salvo.OwnerSide == OwnerSide)
        {
            return false;
        }

        if (TargetMissileSalvoId is not null &&
            !string.Equals(
                TargetMissileSalvoId,
                salvo.Id,
                StringComparison.Ordinal))
        {
            return false;
        }

        return Coordinate.DistanceTo(missileCoordinate) <=
            Profile.InterceptionRangeHexes;
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
