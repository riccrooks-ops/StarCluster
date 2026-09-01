using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Movement;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

public static class ScenarioDocumentMapper
{
    public static ScenarioInitializationRequest ToInitializationRequest(
        ScenarioDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);
        if (document.SchemaVersion != 1)
        {
            throw new InvalidOperationException(
                $"Unsupported scenario schema version {document.SchemaVersion}; expected 1.");
        }

        ScenarioShipDefinition[] ships = document.Ships
            .Select(ToShipDefinition)
            .ToArray();
        ScenarioMapObjectDefinition[] mapObjects = document.Map.Objects
            .Select(item => new ScenarioMapObjectDefinition(
                Required(item.Id, "map object ID"),
                Required(item.Name, "map object name"),
                ParseEnum<ScenarioMapObjectKind>(item.Kind, "map object kind"),
                ToCoordinate(item.Position)))
            .ToArray();
        ScenarioPriorTrackDefinition[] priorTracks = document.PriorTracks
            .Select(item => new ScenarioPriorTrackDefinition(
                Required(item.ObserverId, "prior-track observer ID"),
                Required(item.TargetId, "prior-track target ID"),
                ToCoordinate(item.LastKnownPosition),
                item.UncertaintyRadius))
            .ToArray();
        ScenarioMissileDefinition[] missiles = document.Missiles
            .Select(ToMissileDefinition)
            .ToArray();

        return new ScenarioInitializationRequest(
            Required(document.Id, "scenario ID"),
            Required(document.Name, "scenario name"),
            document.Map.Radius,
            Required(document.Map.StarId, "star ID"),
            Required(document.Map.StarName, "star name"),
            ships,
            new SensorEnvironmentProfile(
                Required(document.Map.EnvironmentId, "environment ID"),
                document.Map.EnvironmentRangePenalty),
            new SensorSignatureProfile(
                "default-missile-signature",
                baselineRangeModifierHexes: 1),
            mapObjects,
            priorTracks,
            missiles,
            initialTurnNumber: document.InitialTurnNumber,
            initialPhase: ParseEnum<TacticalTurnPhase>(
                document.InitialPhase,
                "initial tactical phase"),
            observationEpoch: document.ObservationEpoch,
            initialSequence: document.InitialSequence,
            randomSeed: document.RandomSeed);
    }

    public static IReadOnlyList<MissileDefenseSystem> CreateDefenses(
        ScenarioDocument document,
        ScenarioInitializationResult runtime)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(runtime);

        return Array.AsReadOnly(document.Defenses.Select(item =>
        {
            string defenderId = Required(item.DefenderShipId, "defender ship ID");
            if (!runtime.Ships.TryGetValue(defenderId, out ScenarioShipState? ship))
            {
                throw new InvalidOperationException(
                    $"Defense '{item.Id}' references unknown ship '{defenderId}'.");
            }

            return new MissileDefenseSystem(
                Required(item.Id, "defense ID"),
                defenderId,
                ParseEnum<TacticalSide>(item.Side, "defense side"),
                ship.Coordinate,
                new MissileDefenseProfile(
                    item.TechnologyLevel,
                    item.Range,
                    item.MaximumAttemptsPerPhase),
                item.Priority,
                ParseEnum<MissileDefenseSourceType>(
                    item.SourceType,
                    "defense source type"),
                targetMissileSalvoId: null,
                requiresLineOfSight: item.RequiresLineOfSight,
                requiresFirmTacticalTrack: item.RequiresFirmTrack);
        }).ToArray());
    }

    public static HexCoord ToCoordinate(CoordinateDocument coordinate)
    {
        ArgumentNullException.ThrowIfNull(coordinate);
        return new HexCoord(coordinate.Q, coordinate.R);
    }

    private static ScenarioShipDefinition ToShipDefinition(ShipDocument item) =>
        new(
            Required(item.Id, "ship ID"),
            Required(item.Name, "ship name"),
            ParseEnum<TacticalSide>(item.Side, "ship side"),
            ToCoordinate(item.Position),
            new SublightMovementProfile(
                item.Movement.TechnologyLevel,
                item.Movement.MaximumHexesPerTurn),
            new SensorProfile(
                item.Sensor.TechnologyLevel,
                item.Sensor.FirmRange,
                item.Sensor.ApproximateRange,
                item.Sensor.RequiresLineOfSight,
                item.Sensor.ActiveModeBonus),
            new ComputingProfile(
                item.Computing.TechnologyLevel,
                item.Computing.StaleRetentionUpdates,
                item.Computing.UncertaintyGrowthPerMissedUpdate),
            new SensorSignatureProfile(
                Required(item.Signature.Id, "ship signature ID"),
                item.Signature.BaselineRangeModifier,
                item.Signature.ActiveEmissionRangeModifier),
            new ElectronicWarfareProfile(
                item.ElectronicWarfare.TechnologyLevel,
                item.ElectronicWarfare.JammingRangePenalty,
                item.ElectronicWarfare.CounterJammingStrength),
            ParseEnum<SensorMode>(item.SensorMode, "ship sensor mode"),
            item.JammingEnabled);

    private static ScenarioMissileDefinition ToMissileDefinition(
        MissileDocument item)
    {
        var guidance = new MissileGuidanceComputerProfile(
            item.Terminal.GuidanceComputer.TechnologyLevel,
            item.Terminal.GuidanceComputer.BaseHitChance,
            item.Terminal.GuidanceComputer.MinimumHitChance,
            item.Terminal.GuidanceComputer.MaximumHitChance);
        var seeker = new MissileTerminalSeekerProfile(
            item.Terminal.Seeker.TechnologyLevel,
            item.Terminal.Seeker.IsInstalled,
            item.Terminal.Seeker.BaseAcquisitionChance,
            item.Terminal.Seeker.TerminalEccmStrength,
            item.Terminal.Seeker.AccuracyBonus,
            item.Terminal.Seeker.MinimumAcquisitionChance,
            item.Terminal.Seeker.MaximumAcquisitionChance);

        return new ScenarioMissileDefinition(
            Required(item.Id, "missile ID"),
            ParseEnum<TacticalSide>(item.Side, "missile side"),
            Required(item.LauncherId, "launcher ID"),
            Required(item.TargetId, "target ID"),
            ToCoordinate(item.LaunchPosition),
            new MissileFlightProfile(
                item.Flight.TechnologyLevel,
                item.Flight.MaximumRange,
                item.Flight.Speed),
            new MissileDatalinkProfile(
                item.Datalink.TechnologyLevel,
                item.Datalink.IsInstalled,
                item.Datalink.RequiresLineOfSight,
                item.Datalink.MaximumRetainedReportAgePhases),
            new MissileSensorProfile(
                item.Sensor.TechnologyLevel,
                item.Sensor.IsInstalled,
                item.Sensor.FirmRange,
                item.Sensor.ApproximateRange,
                item.Sensor.RequiresLineOfSight,
                item.Sensor.ActiveModeBonus,
                item.Sensor.AllowsActiveMode,
                item.Sensor.MaximumLocalTrackAgeEpochs),
            new MissileTerminalProfile(
                guidance,
                seeker,
                item.Terminal.AcquisitionPenaltyPerNetEcm,
                item.Terminal.StationarySearchFuelCost),
            new SensorSignatureProfile(
                Required(item.Signature.Id, "missile signature ID"),
                item.Signature.BaselineRangeModifier,
                item.Signature.ActiveEmissionRangeModifier),
            item.EnteredCoordinates.Select(ToCoordinate),
            ToRetainedDatalink(item.RetainedDatalink),
            ToLocalTrack(item.LocalTrack),
            ParseEnum<GuidedMissileStatus>(item.InitialStatus, "missile initial status"),
            Math.Max(
                item.GuidancePhaseCount,
                item.RetainedDatalink?.ReceivedGuidancePhase ?? 0));
    }

    private static ScenarioRetainedDatalinkDefinition? ToRetainedDatalink(
        RetainedDatalinkDocument? item) => item is null
            ? null
            : new ScenarioRetainedDatalinkDefinition(
                ParseEnum<MissileDatalinkState>(item.LinkState, "datalink state"),
                ParseEnum<MissileTargetTrackQuality>(item.Quality, "datalink quality"),
                ToCoordinate(item.GuidancePosition),
                item.SourceObservationEpoch,
                item.ReceivedGuidancePhase,
                item.UncertaintyRadius,
                item.AgePhases);

    private static ScenarioLocalTrackDefinition? ToLocalTrack(
        LocalTrackDocument? item) => item is null
            ? null
            : new ScenarioLocalTrackDefinition(
                ParseEnum<MissileTargetTrackQuality>(item.Quality, "local-track quality"),
                ToCoordinate(item.GuidancePosition),
                item.SourceObservationEpoch,
                item.UncertaintyRadius,
                ParseEnum<SensorMode>(item.SensorMode, "local sensor mode"),
                item.AgeEpochs,
                item.LastAgedObservationEpoch);

    public static T ParseEnum<T>(string value, string description)
        where T : struct, Enum
    {
        if (!Enum.TryParse(value, ignoreCase: true, out T parsed) ||
            !Enum.IsDefined(parsed))
        {
            throw new InvalidOperationException(
                $"Invalid {description} '{value}'.");
        }

        return parsed;
    }

    private static string Required(string value, string description)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"A {description} is required.");
        }

        return value;
    }
}
