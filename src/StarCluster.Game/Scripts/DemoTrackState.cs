using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Game;

/// <summary>
/// Demonstration orchestration for the tactical prototype. It performs the initial
/// system-entry update before presentation, refreshes tracks after movement,
/// missile, and sensor-state events, and exposes only observer-safe contacts to
/// Godot drawing.
/// </summary>
public sealed class DemoTrackState
{
    private readonly DemoScenario _scenario;
    private readonly SensorProfile _sensorProfile;
    private readonly ComputingProfile _computingProfile;
    private readonly SensorSignatureProfile _shipSignatureProfile;
    private readonly SensorSignatureProfile _missileSignatureProfile;
    private readonly ElectronicWarfareProfile _playerElectronicWarfare;
    private readonly ElectronicWarfareProfile _enemyElectronicWarfare;
    private readonly SensorEnvironmentProfile _environmentProfile;
    private readonly TacticalTrackRepository _repository = new();
    private readonly NavigationKnowledge _navigationKnowledge;
    private readonly Dictionary<(string ObserverId, string TargetId),
        SensorContactEvaluationResult> _lastSensorEvaluations = new();
    private long _sequence;
    private int _observationEpoch = 1;
    private SensorMode _playerSensorMode;
    private SensorMode _enemySensorMode;
    private bool _playerJammingEnabled;
    private bool _enemyJammingEnabled;
    private IReadOnlyList<TacticalTrackUpdateResult> _initialUpdateResults =
        Array.Empty<TacticalTrackUpdateResult>();

    public DemoTrackState(
        DemoScenario scenario,
        SensorProfile sensorProfile,
        ComputingProfile computingProfile,
        TrackUpdateTrigger initialTrigger = TrackUpdateTrigger.SystemEntry)
        : this(
            scenario,
            sensorProfile,
            computingProfile,
            SensorSignatureProfile.Neutral,
            SensorSignatureProfile.Neutral,
            ElectronicWarfareProfile.None,
            ElectronicWarfareProfile.None,
            SensorEnvironmentProfile.ClearSpace,
            SensorMode.Passive,
            SensorMode.Passive,
            playerJammingEnabled: false,
            enemyJammingEnabled: false,
            initialTrigger: initialTrigger)
    {
    }

    public DemoTrackState(
        DemoScenario scenario,
        SensorProfile sensorProfile,
        ComputingProfile computingProfile,
        SensorSignatureProfile shipSignatureProfile,
        SensorSignatureProfile missileSignatureProfile,
        ElectronicWarfareProfile playerElectronicWarfare,
        ElectronicWarfareProfile enemyElectronicWarfare,
        SensorEnvironmentProfile environmentProfile,
        SensorMode playerSensorMode,
        SensorMode enemySensorMode,
        bool playerJammingEnabled,
        bool enemyJammingEnabled,
        TrackUpdateTrigger initialTrigger = TrackUpdateTrigger.SystemEntry)
    {
        _scenario = scenario ?? throw new ArgumentNullException(nameof(scenario));
        _sensorProfile = sensorProfile ??
            throw new ArgumentNullException(nameof(sensorProfile));
        _computingProfile = computingProfile ??
            throw new ArgumentNullException(nameof(computingProfile));
        _shipSignatureProfile = shipSignatureProfile ??
            throw new ArgumentNullException(nameof(shipSignatureProfile));
        _missileSignatureProfile = missileSignatureProfile ??
            throw new ArgumentNullException(nameof(missileSignatureProfile));
        _playerElectronicWarfare = playerElectronicWarfare ??
            throw new ArgumentNullException(nameof(playerElectronicWarfare));
        _enemyElectronicWarfare = enemyElectronicWarfare ??
            throw new ArgumentNullException(nameof(enemyElectronicWarfare));
        _environmentProfile = environmentProfile ??
            throw new ArgumentNullException(nameof(environmentProfile));

        SetSensorState(
            playerSensorMode,
            enemySensorMode,
            playerJammingEnabled,
            enemyJammingEnabled);

        string[] chartedObjects = scenario.Map.Cells
            .SelectMany(cell => cell.Occupants)
            .Where(mapObject => mapObject.Kind is
                MapObjectKind.Planet or MapObjectKind.Station)
            .Select(mapObject => mapObject.Id)
            .Distinct(StringComparer.Ordinal)
            .ToArray();
        _navigationKnowledge = NavigationKnowledge.FromSystemMap(
            scenario.Map,
            chartedObjects);

        // The presentation fixtures begin with fragmentary prior intelligence
        // so the blocked scenario can demonstrate a Stale contact rather than
        // leaking truth or hiding the only opponent entirely.
        _repository.SeedPriorIntelligence(
            scenario.PlayerShipId,
            scenario.EnemyShipId,
            scenario.EnemyPosition,
            sequence: 0);
        _repository.SeedPriorIntelligence(
            scenario.EnemyShipId,
            scenario.PlayerShipId,
            scenario.PlayerPosition,
            sequence: 0);

        _initialUpdateResults = Refresh(
            initialTrigger,
            Array.Empty<GuidedMissileSalvo>(),
            observationEpoch: 1);
    }

    public long Sequence => _sequence;

    public int ObservationEpoch => _observationEpoch;

    public IReadOnlyList<TacticalTrackUpdateResult> InitialUpdateResults =>
        _initialUpdateResults;

    public SensorProfile SensorProfile => _sensorProfile;

    public ComputingProfile ComputingProfile => _computingProfile;

    public SensorMode PlayerSensorMode => _playerSensorMode;

    public SensorMode EnemySensorMode => _enemySensorMode;

    public bool PlayerJammingEnabled => _playerJammingEnabled;

    public bool EnemyJammingEnabled => _enemyJammingEnabled;

    public TacticalMapKnowledgeSnapshot PlayerMapSnapshot =>
        TacticalMapKnowledgeService.Build(
            _scenario.Map,
            _navigationKnowledge,
            _repository,
            _scenario.PlayerShipId,
            new[] { _scenario.PlayerShipId },
            _sequence);

    public TacticalTrackRecord? PlayerTrackOnEnemy =>
        _repository.Get(_scenario.PlayerShipId, _scenario.EnemyShipId);

    public TacticalTrackRecord? PlayerTrackOn(string targetId) =>
        _repository.Get(_scenario.PlayerShipId, targetId);

    public TacticalTrackRecord? GetTrackForSide(
        TacticalSide side,
        string targetId)
    {
        string observerId = side switch
        {
            TacticalSide.Player => _scenario.PlayerShipId,
            TacticalSide.Enemy => _scenario.EnemyShipId,
            _ => string.Empty,
        };

        return string.IsNullOrEmpty(observerId)
            ? null
            : _repository.Get(observerId, targetId);
    }

    public SensorContactEvaluationResult? GetLastSensorEvaluation(
        string observerId,
        string targetId) =>
        _lastSensorEvaluations.TryGetValue(
            (observerId, targetId),
            out SensorContactEvaluationResult? evaluation)
            ? evaluation
            : null;

    public void SetSensorState(
        SensorMode playerSensorMode,
        SensorMode enemySensorMode,
        bool playerJammingEnabled,
        bool enemyJammingEnabled)
    {
        if (!Enum.IsDefined(playerSensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(playerSensorMode));
        }

        if (!Enum.IsDefined(enemySensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(enemySensorMode));
        }

        _playerSensorMode = playerSensorMode;
        _enemySensorMode = enemySensorMode;
        _playerJammingEnabled = playerJammingEnabled;
        _enemyJammingEnabled = enemyJammingEnabled;
    }

    public SensorContactEvaluationContext CreatePlayerMissileEvaluationContext() =>
        CreateEvaluationContext(
            _scenario.PlayerShipId,
            _missileSignatureProfile,
            SensorMode.Passive,
            ElectronicWarfareProfile.None,
            targetJammingEnabled: false);

    public MissileTargetTrackSnapshot CreateGuidanceSnapshot(
        GuidedMissileSalvo salvo) =>
        MissileTargetTrackSnapshot.FromTacticalTrack(
            salvo.TargetId,
            GetTrackForSide(salvo.OwnerSide, salvo.TargetId));

    public int GetGuidanceSourceObservationEpoch(
        TacticalSide side,
        string targetId)
    {
        TacticalTrackRecord? record = GetTrackForSide(side, targetId);
        return record?.LastObservedEpoch ?? 1;
    }

    public int GetGuidanceSourceObservationEpoch(
        GuidedMissileSalvo salvo)
    {
        ArgumentNullException.ThrowIfNull(salvo);
        return GetGuidanceSourceObservationEpoch(
            salvo.OwnerSide,
            salvo.TargetId);
    }

    public ObserverSafeMissileViewSnapshot BuildPlayerMissileView(
        MissileEngagementState engagement,
        string? requestedSelectedSalvoId)
    {
        ArgumentNullException.ThrowIfNull(engagement);
        return ObserverSafeMissileViewService.Build(
            _scenario.Map,
            engagement.Salvos,
            _repository,
            _scenario.PlayerShipId,
            TacticalSide.Player,
            _scenario.PlayerPosition,
            requestedSelectedSalvoId);
    }

    public MissileMovementObservationResult ObservePlayerMissileMovement(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result,
        TrackUpdateTrigger trigger,
        bool launchObservedAtOrigin)
    {
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(result);

        MissileMovementObservationResult observation =
            MissileMovementObservationService.Apply(
                _scenario.Map,
                _repository,
                _scenario.PlayerShipId,
                _scenario.PlayerPosition,
                salvo,
                result.EnteredCoordinates,
                _sensorProfile,
                _computingProfile,
                _sequence,
                trigger,
                _observationEpoch,
                launchObservedAtOrigin,
                CreatePlayerMissileEvaluationContext());
        _sequence = observation.FinalSequence;
        return observation;
    }

    public IReadOnlyList<TacticalMissileContact> PlayerMissileContacts(
        IEnumerable<GuidedMissileSalvo> salvos) =>
        TacticalMissileKnowledgeService.Build(
            salvos,
            _repository,
            _scenario.PlayerShipId,
            TacticalSide.Player);

    public IReadOnlyList<MissileRouteProjection> ProjectRoutes(
        IEnumerable<TacticalMissileContact> contacts,
        MissileEngagementState engagement)
    {
        ArgumentNullException.ThrowIfNull(contacts);
        ArgumentNullException.ThrowIfNull(engagement);
        return BuildPlayerMissileView(engagement, null).Projections;
    }

    public IReadOnlyList<TacticalTrackUpdateResult> Refresh(
        TrackUpdateTrigger trigger,
        IEnumerable<GuidedMissileSalvo> salvos) =>
        Refresh(trigger, salvos, _observationEpoch);

    public IReadOnlyList<TacticalTrackUpdateResult> Refresh(
        TrackUpdateTrigger trigger,
        IEnumerable<GuidedMissileSalvo> salvos,
        int observationEpoch)
    {
        ArgumentNullException.ThrowIfNull(salvos);
        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }

        _observationEpoch = observationEpoch;
        _sequence++;

        var results = new List<TacticalTrackUpdateResult>
        {
            ApplyShipObservation(
                _scenario.PlayerShipId,
                _scenario.PlayerPosition,
                _scenario.EnemyShipId,
                _scenario.EnemyPosition,
                trigger,
                observationEpoch),
            ApplyShipObservation(
                _scenario.EnemyShipId,
                _scenario.EnemyPosition,
                _scenario.PlayerShipId,
                _scenario.PlayerPosition,
                trigger,
                observationEpoch),
        };

        foreach (GuidedMissileSalvo salvo in salvos)
        {
            results.Add(UpdateMissileTrackForObserver(
                _scenario.PlayerShipId,
                _scenario.PlayerPosition,
                TacticalSide.Player,
                salvo,
                trigger));
            results.Add(UpdateMissileTrackForObserver(
                _scenario.EnemyShipId,
                _scenario.EnemyPosition,
                TacticalSide.Enemy,
                salvo,
                trigger));
        }

        return Array.AsReadOnly(results.ToArray());
    }

    private TacticalTrackUpdateResult ApplyShipObservation(
        string observerId,
        HexCoord observerCoordinate,
        string targetId,
        HexCoord targetCoordinate,
        TrackUpdateTrigger trigger,
        int observationEpoch)
    {
        SensorContactEvaluationResult evaluation = SensorContactEvaluator.Evaluate(
            _scenario.Map,
            targetId,
            observerCoordinate,
            targetCoordinate,
            _sensorProfile,
            CreateShipEvaluationContext(observerId, targetId));
        _lastSensorEvaluations[(observerId, targetId)] = evaluation;

        return TacticalTrackUpdateService.Apply(
            _repository,
            observerId,
            evaluation.Observation,
            _computingProfile,
            _sequence,
            trigger,
            observationEpoch);
    }

    private TacticalTrackUpdateResult UpdateMissileTrackForObserver(
        string observerId,
        HexCoord observerCoordinate,
        TacticalSide observerSide,
        GuidedMissileSalvo salvo,
        TrackUpdateTrigger trigger)
    {
        TacticalTrackObservation observation;
        if (salvo.OwnerSide == observerSide)
        {
            observation = TacticalTrackObservation.Firm(
                salvo.Id,
                salvo.CurrentCoordinate,
                TacticalTrackSourceType.MissileSeeker);
            _lastSensorEvaluations.Remove((observerId, salvo.Id));
        }
        else
        {
            SensorContactEvaluationResult evaluation =
                SensorContactEvaluator.Evaluate(
                    _scenario.Map,
                    salvo.Id,
                    observerCoordinate,
                    salvo.CurrentCoordinate,
                    _sensorProfile,
                    CreateEvaluationContext(
                        observerId,
                        _missileSignatureProfile,
                        SensorMode.Passive,
                        ElectronicWarfareProfile.None,
                        targetJammingEnabled: false));
            _lastSensorEvaluations[(observerId, salvo.Id)] = evaluation;
            observation = evaluation.Observation;
        }

        return TacticalTrackUpdateService.Apply(
            _repository,
            observerId,
            observation,
            _computingProfile,
            _sequence,
            trigger,
            _observationEpoch);
    }

    private SensorContactEvaluationContext CreateShipEvaluationContext(
        string observerId,
        string targetId)
    {
        bool targetIsPlayer = string.Equals(
            targetId,
            _scenario.PlayerShipId,
            StringComparison.Ordinal);
        return CreateEvaluationContext(
            observerId,
            _shipSignatureProfile,
            targetIsPlayer ? _playerSensorMode : _enemySensorMode,
            targetIsPlayer
                ? _playerElectronicWarfare
                : _enemyElectronicWarfare,
            targetIsPlayer
                ? _playerJammingEnabled
                : _enemyJammingEnabled);
    }

    private SensorContactEvaluationContext CreateEvaluationContext(
        string observerId,
        SensorSignatureProfile targetSignature,
        SensorMode targetSensorMode,
        ElectronicWarfareProfile targetElectronicWarfare,
        bool targetJammingEnabled)
    {
        bool observerIsPlayer = string.Equals(
            observerId,
            _scenario.PlayerShipId,
            StringComparison.Ordinal);
        return new SensorContactEvaluationContext(
            observerIsPlayer ? _playerSensorMode : _enemySensorMode,
            targetSignature,
            targetSensorMode,
            observerIsPlayer
                ? _playerElectronicWarfare
                : _enemyElectronicWarfare,
            targetElectronicWarfare,
            targetJammingEnabled,
            _environmentProfile);
    }
}
