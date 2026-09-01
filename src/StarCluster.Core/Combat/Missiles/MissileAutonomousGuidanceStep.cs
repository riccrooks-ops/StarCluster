using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// One auditable local-sensor/arbitration decision during a missile action.
/// </summary>
public sealed class MissileAutonomousGuidanceStep
{
    internal MissileAutonomousGuidanceStep(
        MissileGuidanceObservationOpportunity opportunity,
        HexCoord missileCoordinate,
        MissileLocalSensorObservationResult localObservation,
        MissileGuidanceDecision decision,
        bool guidanceChanged,
        int movementSpentThisAction,
        MissileRouteResult? routePlan)
    {
        if (!Enum.IsDefined(opportunity))
        {
            throw new ArgumentOutOfRangeException(nameof(opportunity));
        }

        Opportunity = opportunity;
        MissileCoordinate = missileCoordinate;
        LocalObservation = localObservation ??
            throw new ArgumentNullException(nameof(localObservation));
        Decision = decision ?? throw new ArgumentNullException(nameof(decision));
        if (movementSpentThisAction < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(movementSpentThisAction));
        }

        GuidanceChanged = guidanceChanged;
        MovementSpentThisAction = movementSpentThisAction;
        RoutePlan = routePlan;
    }

    public MissileGuidanceObservationOpportunity Opportunity { get; }

    public HexCoord MissileCoordinate { get; }

    public MissileLocalSensorObservationResult LocalObservation { get; }

    public MissileGuidanceDecision Decision { get; }

    public bool GuidanceChanged { get; }

    public int MovementSpentThisAction { get; }

    public MissileRouteResult? RoutePlan { get; }
}
