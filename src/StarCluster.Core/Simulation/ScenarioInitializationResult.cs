using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Simulation;

/// <summary>
/// Fully initialized authoritative runtime. Hosts may now execute scripted,
/// AI, Monte Carlo, or player-driven actions against the same Core state.
/// </summary>
public sealed class ScenarioInitializationResult
{
    internal ScenarioInitializationResult(
        ScenarioInitializationRequest request,
        SystemMap map,
        IReadOnlyDictionary<string, ScenarioShipState> ships,
        TacticalTrackRepository tracks,
        MissileEngagementState missileEngagement,
        IReadOnlyDictionary<string, ScenarioMissileDefinition> missileDefinitions,
        TacticalTurnState turnState,
        DiagnosticEventJournal journal,
        long sequence,
        int observationEpoch)
    {
        Request = request ?? throw new ArgumentNullException(nameof(request));
        Map = map ?? throw new ArgumentNullException(nameof(map));
        Ships = ships ?? throw new ArgumentNullException(nameof(ships));
        Tracks = tracks ?? throw new ArgumentNullException(nameof(tracks));
        MissileEngagement = missileEngagement ??
            throw new ArgumentNullException(nameof(missileEngagement));
        MissileDefinitions = missileDefinitions ??
            throw new ArgumentNullException(nameof(missileDefinitions));
        TurnState = turnState ?? throw new ArgumentNullException(nameof(turnState));
        Journal = journal ?? throw new ArgumentNullException(nameof(journal));
        Sequence = sequence;
        ObservationEpoch = observationEpoch;
    }

    public ScenarioInitializationRequest Request { get; }

    public SystemMap Map { get; }

    public IReadOnlyDictionary<string, ScenarioShipState> Ships { get; }

    public TacticalTrackRepository Tracks { get; }

    public MissileEngagementState MissileEngagement { get; }

    public IReadOnlyDictionary<string, ScenarioMissileDefinition> MissileDefinitions { get; }

    public TacticalTurnState TurnState { get; }

    public DiagnosticEventJournal Journal { get; }

    public long Sequence { get; internal set; }

    public int ObservationEpoch { get; internal set; }
}
