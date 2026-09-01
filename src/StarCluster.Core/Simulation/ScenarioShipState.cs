using System;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Simulation;

/// <summary>
/// Mutable runtime coordinate paired with an immutable ship definition.
/// </summary>
public sealed class ScenarioShipState
{
    internal ScenarioShipState(ScenarioShipDefinition definition)
    {
        Definition = definition ?? throw new ArgumentNullException(nameof(definition));
        Coordinate = definition.Coordinate;
    }

    public ScenarioShipDefinition Definition { get; }

    public HexCoord Coordinate { get; private set; }

    /// <summary>
    /// Updates the host-visible runtime coordinate after an authoritative Core
    /// movement service has committed the same move to the SystemMap.
    /// </summary>
    public void ApplyCommittedMovement(HexCoord coordinate) =>
        Coordinate = coordinate;
}
