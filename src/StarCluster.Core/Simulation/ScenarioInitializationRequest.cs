using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Tracking;

namespace StarCluster.Core.Simulation;

/// <summary>
/// Complete engine-independent input for creating one authoritative tactical
/// runtime before its first scripted action.
/// </summary>
public sealed class ScenarioInitializationRequest
{
    private readonly IReadOnlyList<ScenarioMapObjectDefinition> _mapObjects;
    private readonly IReadOnlyList<ScenarioShipDefinition> _ships;
    private readonly IReadOnlyList<ScenarioPriorTrackDefinition> _priorTracks;
    private readonly IReadOnlyList<ScenarioMissileDefinition> _missiles;

    public ScenarioInitializationRequest(
        string scenarioId,
        string name,
        int mapRadius,
        string starId,
        string starName,
        IEnumerable<ScenarioShipDefinition> ships,
        SensorEnvironmentProfile environmentProfile,
        SensorSignatureProfile missileSignatureProfile,
        IEnumerable<ScenarioMapObjectDefinition>? mapObjects = null,
        IEnumerable<ScenarioPriorTrackDefinition>? priorTracks = null,
        IEnumerable<ScenarioMissileDefinition>? missiles = null,
        int initialTurnNumber = 1,
        TacticalTurnPhase initialPhase = TacticalTurnPhase.Movement,
        int observationEpoch = 1,
        long initialSequence = 0,
        int randomSeed = 180100)
    {
        if (string.IsNullOrWhiteSpace(scenarioId))
        {
            throw new ArgumentException("A scenario ID is required.", nameof(scenarioId));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("A scenario name is required.", nameof(name));
        }

        if (mapRadius < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(mapRadius));
        }

        if (string.IsNullOrWhiteSpace(starId))
        {
            throw new ArgumentException("A star ID is required.", nameof(starId));
        }

        if (string.IsNullOrWhiteSpace(starName))
        {
            throw new ArgumentException("A star name is required.", nameof(starName));
        }

        if (initialTurnNumber <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(initialTurnNumber));
        }

        if (!Enum.IsDefined(initialPhase))
        {
            throw new ArgumentOutOfRangeException(nameof(initialPhase));
        }

        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }

        if (initialSequence < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(initialSequence));
        }

        ScenarioShipDefinition[] materializedShips = ships?.ToArray() ??
            throw new ArgumentNullException(nameof(ships));
        if (materializedShips.Length == 0)
        {
            throw new ArgumentException("At least one ship is required.", nameof(ships));
        }

        EnsureUniqueIds(materializedShips.Select(ship => ship.Id), nameof(ships));

        ScenarioMapObjectDefinition[] materializedObjects =
            mapObjects?.ToArray() ?? Array.Empty<ScenarioMapObjectDefinition>();
        ScenarioPriorTrackDefinition[] materializedTracks =
            priorTracks?.ToArray() ?? Array.Empty<ScenarioPriorTrackDefinition>();
        ScenarioMissileDefinition[] materializedMissiles =
            missiles?.ToArray() ?? Array.Empty<ScenarioMissileDefinition>();

        EnsureUniqueIds(materializedObjects.Select(item => item.Id), nameof(mapObjects));
        EnsureUniqueIds(materializedMissiles.Select(item => item.Id), nameof(missiles));
        EnsureUniqueIds(
            new[] { starId }
                .Concat(materializedShips.Select(ship => ship.Id))
                .Concat(materializedObjects.Select(item => item.Id))
                .Concat(materializedMissiles.Select(item => item.Id)),
            "scenario entity IDs");

        var shipIds = new HashSet<string>(
            materializedShips.Select(ship => ship.Id),
            StringComparer.Ordinal);
        var trackableIds = new HashSet<string>(shipIds, StringComparer.Ordinal);
        trackableIds.UnionWith(materializedMissiles.Select(missile => missile.Id));
        foreach (ScenarioPriorTrackDefinition prior in materializedTracks)
        {
            if (!shipIds.Contains(prior.ObserverId))
            {
                throw new ArgumentException(
                    $"Prior track observer '{prior.ObserverId}' is not a scenario ship.",
                    nameof(priorTracks));
            }

            if (!trackableIds.Contains(prior.TargetId))
            {
                throw new ArgumentException(
                    $"Prior track target '{prior.TargetId}' is not a scenario ship or Missile Flight.",
                    nameof(priorTracks));
            }
        }

        ScenarioId = scenarioId;
        Name = name;
        MapRadius = mapRadius;
        StarId = starId;
        StarName = starName;
        _ships = Array.AsReadOnly(materializedShips);
        EnvironmentProfile = environmentProfile ??
            throw new ArgumentNullException(nameof(environmentProfile));
        MissileSignatureProfile = missileSignatureProfile ??
            throw new ArgumentNullException(nameof(missileSignatureProfile));
        _mapObjects = Array.AsReadOnly(materializedObjects);
        _priorTracks = Array.AsReadOnly(materializedTracks);
        _missiles = Array.AsReadOnly(materializedMissiles);
        InitialTurnNumber = initialTurnNumber;
        InitialPhase = initialPhase;
        ObservationEpoch = observationEpoch;
        InitialSequence = initialSequence;
        RandomSeed = randomSeed;
    }

    public string ScenarioId { get; }

    public string Name { get; }

    public int MapRadius { get; }

    public string StarId { get; }

    public string StarName { get; }

    public IReadOnlyList<ScenarioMapObjectDefinition> MapObjects => _mapObjects;

    public IReadOnlyList<ScenarioShipDefinition> Ships => _ships;

    public SensorEnvironmentProfile EnvironmentProfile { get; }

    public SensorSignatureProfile MissileSignatureProfile { get; }

    public IReadOnlyList<ScenarioPriorTrackDefinition> PriorTracks => _priorTracks;

    public IReadOnlyList<ScenarioMissileDefinition> Missiles => _missiles;

    public int InitialTurnNumber { get; }

    public TacticalTurnPhase InitialPhase { get; }

    public int ObservationEpoch { get; }

    public long InitialSequence { get; }

    public int RandomSeed { get; }

    private static void EnsureUniqueIds(IEnumerable<string> ids, string parameterName)
    {
        string? duplicate = ids
            .GroupBy(id => id, StringComparer.Ordinal)
            .FirstOrDefault(group => group.Count() > 1)
            ?.Key;
        if (duplicate is not null)
        {
            throw new ArgumentException(
                $"Duplicate scenario entity ID '{duplicate}'.",
                parameterName);
        }
    }
}
