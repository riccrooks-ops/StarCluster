using System;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Movement;

namespace StarCluster.Core.Simulation;

/// <summary>
/// Authoritative starting state and installed tactical profiles for one ship.
/// </summary>
public sealed class ScenarioShipDefinition
{
    public ScenarioShipDefinition(
        string id,
        string name,
        TacticalSide side,
        HexCoord coordinate,
        SublightMovementProfile movementProfile,
        SensorProfile sensorProfile,
        ComputingProfile computingProfile,
        SensorSignatureProfile signatureProfile,
        ElectronicWarfareProfile electronicWarfareProfile,
        SensorMode sensorMode = SensorMode.Passive,
        bool jammingEnabled = false)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("A stable ship ID is required.", nameof(id));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("A ship name is required.", nameof(name));
        }

        if (side is TacticalSide.Unspecified || !Enum.IsDefined(side))
        {
            throw new ArgumentOutOfRangeException(nameof(side));
        }

        if (!Enum.IsDefined(sensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(sensorMode));
        }

        Id = id;
        Name = name;
        Side = side;
        Coordinate = coordinate;
        MovementProfile = movementProfile ?? throw new ArgumentNullException(nameof(movementProfile));
        SensorProfile = sensorProfile ?? throw new ArgumentNullException(nameof(sensorProfile));
        ComputingProfile = computingProfile ?? throw new ArgumentNullException(nameof(computingProfile));
        SignatureProfile = signatureProfile ?? throw new ArgumentNullException(nameof(signatureProfile));
        ElectronicWarfareProfile = electronicWarfareProfile ??
            throw new ArgumentNullException(nameof(electronicWarfareProfile));
        SensorMode = sensorMode;
        JammingEnabled = jammingEnabled;
    }

    public string Id { get; }

    public string Name { get; }

    public TacticalSide Side { get; }

    public HexCoord Coordinate { get; }

    public SublightMovementProfile MovementProfile { get; }

    public SensorProfile SensorProfile { get; }

    public ComputingProfile ComputingProfile { get; }

    public SensorSignatureProfile SignatureProfile { get; }

    public ElectronicWarfareProfile ElectronicWarfareProfile { get; }

    public SensorMode SensorMode { get; }

    public bool JammingEnabled { get; }
}
