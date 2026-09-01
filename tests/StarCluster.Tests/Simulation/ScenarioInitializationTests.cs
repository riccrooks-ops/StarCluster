using System;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Movement;
using StarCluster.Core.Simulation;
using Xunit;

namespace StarCluster.Tests.Simulation;

public sealed class ScenarioInitializationTests
{
    [Fact]
    public void InitializationRunsNormalSystemEntryTrackPass()
    {
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest());

        TacticalTrackRecord? track = result.Tracks.Get("ship-player", "ship-enemy");
        Assert.NotNull(track);
        Assert.Equal(TacticalTrackQuality.Firm, track.Quality);
        Assert.Equal(new HexCoord(2, 2), track.EstimatedCoordinate);
    }

    [Fact]
    public void PreExistingMissileRestoresTravelHistoryAndFuelUse()
    {
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest(withMissile: true));

        GuidedMissileSalvo missile = Assert.Single(result.MissileEngagement.Salvos);
        Assert.Equal(new HexCoord(1, 2), missile.CurrentCoordinate);
        Assert.Equal(1, missile.DistanceTraveled);
        Assert.Equal(1, missile.TotalFuelSpent);
        Assert.Equal(2, missile.TravelHistory.Count);
    }

    [Fact]
    public void PreExistingMissileParticipatesInInitialObservationPass()
    {
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest(withMissile: true));

        TacticalTrackRecord? track = result.Tracks.Get("ship-player", "hostile-1");
        Assert.NotNull(track);
        Assert.Equal(TacticalTrackQuality.Firm, track.Quality);
        Assert.Equal(new HexCoord(1, 2), track.EstimatedCoordinate);
    }

    [Fact]
    public void RetainedDatalinkSeedIsCopiedIntoNormalMissileState()
    {
        ScenarioMissileDefinition missile = CreateMissile(
            retained: new ScenarioRetainedDatalinkDefinition(
                MissileDatalinkState.Blocked,
                MissileTargetTrackQuality.Current,
                new HexCoord(0, 2),
                agePhases: 1));
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest(missile));

        GuidedMissileSalvo initialized = Assert.Single(result.MissileEngagement.Salvos);
        Assert.Equal(MissileDatalinkState.Blocked, initialized.DatalinkState);
        Assert.NotNull(initialized.RetainedDatalinkReport);
        Assert.Equal(1, initialized.RetainedDatalinkReport.AgePhases);
        Assert.Equal(1, initialized.GuidancePhaseCount);
    }

    [Fact]
    public void LocalTrackSeedIsCopiedIntoNormalMissileState()
    {
        ScenarioMissileDefinition missile = CreateMissile(
            local: new ScenarioLocalTrackDefinition(
                MissileTargetTrackQuality.Current,
                new HexCoord(0, 2)));
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest(missile));

        GuidedMissileSalvo initialized = Assert.Single(result.MissileEngagement.Salvos);
        Assert.NotNull(initialized.LocalSensorTrack);
        Assert.Equal(MissileTargetTrackQuality.Current, initialized.LocalSensorTrack.Quality);
    }

    [Fact]
    public void SearchingSeedBeginsAsActiveSearchWait()
    {
        ScenarioMissileDefinition missile = CreateMissile(
            initialStatus: GuidedMissileStatus.Searching);
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest(missile));

        GuidedMissileSalvo initialized = Assert.Single(result.MissileEngagement.ActiveSalvos);
        Assert.Equal(GuidedMissileStatus.Searching, initialized.Status);
        Assert.Equal(MissileTerminalState.SearchWait, initialized.TerminalState);
    }

    [Fact]
    public void InitialTurnAndPhaseAreAdvancedWithoutHostInput()
    {
        ScenarioInitializationRequest request = CreateRequest(
            initialTurn: 3,
            initialPhase: TacticalTurnPhase.MissileAndInterception);
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(request);

        Assert.Equal(3, result.TurnState.TurnNumber);
        Assert.Equal(TacticalTurnPhase.MissileAndInterception, result.TurnState.Phase);
    }

    [Fact]
    public void DuplicateEntityIdsAreRejectedBeforeInitialization()
    {
        ScenarioShipDefinition[] ships =
        {
            CreateShip("duplicate", TacticalSide.Player, new HexCoord(0, 2)),
            CreateShip("duplicate", TacticalSide.Enemy, new HexCoord(2, 2)),
        };

        Assert.Throws<ArgumentException>(() => new ScenarioInitializationRequest(
            "duplicate-test",
            "Duplicate test",
            6,
            "star",
            "Primary",
            ships,
            SensorEnvironmentProfile.ClearSpace,
            new SensorSignatureProfile("missile")));
    }

    [Fact]
    public void RefreshAllTracksUsesRequestedObservationEpoch()
    {
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest());

        ScenarioInitializationService.RefreshAllTracks(
            result,
            TrackUpdateTrigger.SensorStateChanged,
            observationEpoch: 4);

        Assert.Equal(4, result.ObservationEpoch);
        Assert.Equal(4, result.Tracks.Get("ship-player", "ship-enemy")?.LastObservedEpoch);
    }

    [Fact]
    public void JournalRecordsInitializationBeforeScriptedActions()
    {
        ScenarioInitializationResult result =
            ScenarioInitializationService.Initialize(CreateRequest(withMissile: true));

        Assert.Equal(DiagnosticEventType.SessionStarted, result.Journal.Events[0].EventType);
        Assert.Contains(
            result.Journal.Events,
            item => item.EventType == DiagnosticEventType.ScenarioInitialized);
        Assert.Contains(
            result.Journal.Events,
            item => item.EventType == DiagnosticEventType.TrackUpdated &&
                item.TargetId == "hostile-1");
    }

    private static ScenarioInitializationRequest CreateRequest(
        bool withMissile = false,
        int initialTurn = 1,
        TacticalTurnPhase initialPhase = TacticalTurnPhase.Movement) =>
        CreateRequest(
            withMissile ? CreateMissile() : null,
            initialTurn,
            initialPhase);

    private static ScenarioInitializationRequest CreateRequest(
        ScenarioMissileDefinition? missile,
        int initialTurn = 1,
        TacticalTurnPhase initialPhase = TacticalTurnPhase.Movement)
    {
        ScenarioShipDefinition[] ships =
        {
            CreateShip("ship-player", TacticalSide.Player, new HexCoord(0, 2)),
            CreateShip("ship-enemy", TacticalSide.Enemy, new HexCoord(2, 2)),
        };
        return new ScenarioInitializationRequest(
            "initialization-test",
            "Initialization test",
            6,
            "star",
            "Primary",
            ships,
            SensorEnvironmentProfile.ClearSpace,
            new SensorSignatureProfile("missile-plume", 1),
            priorTracks: new[]
            {
                new ScenarioPriorTrackDefinition(
                    "ship-player",
                    "ship-enemy",
                    new HexCoord(2, 2)),
            },
            missiles: missile is null
                ? Array.Empty<ScenarioMissileDefinition>()
                : new[] { missile },
            initialTurnNumber: initialTurn,
            initialPhase: initialPhase);
    }

    private static ScenarioShipDefinition CreateShip(
        string id,
        TacticalSide side,
        HexCoord coordinate) => new(
        id,
        id,
        side,
        coordinate,
        new SublightMovementProfile(3, 3),
        new SensorProfile(3, 6, 10, true, 2),
        new ComputingProfile(3, 3, 1),
        new SensorSignatureProfile("standard-ship", 0, 2),
        new ElectronicWarfareProfile(3, 3, 1));

    private static ScenarioMissileDefinition CreateMissile(
        ScenarioRetainedDatalinkDefinition? retained = null,
        ScenarioLocalTrackDefinition? local = null,
        GuidedMissileStatus initialStatus = GuidedMissileStatus.InFlight) => new(
        "hostile-1",
        TacticalSide.Enemy,
        "ship-enemy",
        "ship-player",
        new HexCoord(2, 2),
        new MissileFlightProfile(2, 8, 1),
        new MissileDatalinkProfile(2, true, true, 3),
        new MissileSensorProfile(2, true, 3, 5, true, 2, true, 2),
        MissileTerminalProfile.Prototype,
        new SensorSignatureProfile("missile-plume", 1),
        new[] { new HexCoord(1, 2) },
        retained,
        local,
        initialStatus);
}
