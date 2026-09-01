using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Simulation;

/// <summary>
/// One Missile Flight present when a headless scenario begins. Travel history,
/// copied datalink state, and missile-local track state are applied before the
/// first scripted action, without bypassing normal runtime state objects.
/// </summary>
public sealed class ScenarioMissileDefinition
{
    private readonly IReadOnlyList<HexCoord> _enteredCoordinates;

    public ScenarioMissileDefinition(
        string id,
        TacticalSide ownerSide,
        string launcherId,
        string targetId,
        HexCoord launchCoordinate,
        MissileFlightProfile flightProfile,
        MissileDatalinkProfile datalinkProfile,
        MissileSensorProfile sensorProfile,
        MissileTerminalProfile terminalProfile,
        SensorSignatureProfile signatureProfile,
        IEnumerable<HexCoord>? enteredCoordinates = null,
        ScenarioRetainedDatalinkDefinition? retainedDatalink = null,
        ScenarioLocalTrackDefinition? localTrack = null,
        GuidedMissileStatus initialStatus = GuidedMissileStatus.InFlight,
        int guidancePhaseCount = 0)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("A stable missile ID is required.", nameof(id));
        }

        if (ownerSide is TacticalSide.Unspecified || !Enum.IsDefined(ownerSide))
        {
            throw new ArgumentOutOfRangeException(nameof(ownerSide));
        }

        if (string.IsNullOrWhiteSpace(launcherId))
        {
            throw new ArgumentException("A launcher ID is required.", nameof(launcherId));
        }

        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException("A target ID is required.", nameof(targetId));
        }

        if (!Enum.IsDefined(initialStatus) || initialStatus is
            GuidedMissileStatus.Expended or
            GuidedMissileStatus.Dud or
            GuidedMissileStatus.Intercepted or
            GuidedMissileStatus.SelfDestructed or
            GuidedMissileStatus.Destroyed or
            GuidedMissileStatus.RangeExhausted)
        {
            throw new ArgumentOutOfRangeException(
                nameof(initialStatus),
                initialStatus,
                "Scenario initialization accepts only active Missile Flight states.");
        }

        if (guidancePhaseCount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(guidancePhaseCount));
        }

        HexCoord[] history = enteredCoordinates?.ToArray() ?? Array.Empty<HexCoord>();
        HexCoord previous = launchCoordinate;
        foreach (HexCoord coordinate in history)
        {
            if (previous.DistanceTo(coordinate) != 1)
            {
                throw new ArgumentException(
                    "Every pre-simulation missile travel-history coordinate must be adjacent.",
                    nameof(enteredCoordinates));
            }

            previous = coordinate;
        }

        Id = id;
        OwnerSide = ownerSide;
        LauncherId = launcherId;
        TargetId = targetId;
        LaunchCoordinate = launchCoordinate;
        FlightProfile = flightProfile ?? throw new ArgumentNullException(nameof(flightProfile));
        DatalinkProfile = datalinkProfile ?? throw new ArgumentNullException(nameof(datalinkProfile));
        SensorProfile = sensorProfile ?? throw new ArgumentNullException(nameof(sensorProfile));
        TerminalProfile = terminalProfile ?? throw new ArgumentNullException(nameof(terminalProfile));
        SignatureProfile = signatureProfile ?? throw new ArgumentNullException(nameof(signatureProfile));
        _enteredCoordinates = Array.AsReadOnly(history);
        RetainedDatalink = retainedDatalink;
        LocalTrack = localTrack;
        InitialStatus = initialStatus;
        GuidancePhaseCount = guidancePhaseCount;
    }

    public string Id { get; }

    public TacticalSide OwnerSide { get; }

    public string LauncherId { get; }

    public string TargetId { get; }

    public HexCoord LaunchCoordinate { get; }

    public MissileFlightProfile FlightProfile { get; }

    public MissileDatalinkProfile DatalinkProfile { get; }

    public MissileSensorProfile SensorProfile { get; }

    public MissileTerminalProfile TerminalProfile { get; }

    public SensorSignatureProfile SignatureProfile { get; }

    public IReadOnlyList<HexCoord> EnteredCoordinates => _enteredCoordinates;

    public ScenarioRetainedDatalinkDefinition? RetainedDatalink { get; }

    public ScenarioLocalTrackDefinition? LocalTrack { get; }

    public GuidedMissileStatus InitialStatus { get; }

    public int GuidancePhaseCount { get; }
}
