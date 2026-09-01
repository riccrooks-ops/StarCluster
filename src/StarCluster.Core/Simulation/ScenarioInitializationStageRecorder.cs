using System;

namespace StarCluster.Core.Simulation;

public enum ScenarioInitializationStage
{
    MapCreation,
    StaticObjectPlacement,
    ShipStateCreation,
    PriorTrackSeeding,
    MissileStateCreation,
    TurnAndJournalCreation,
    InitialTrackRefresh,
    InitializationDiagnostics,
    ResultConstruction,
}

public readonly record struct ScenarioInitializationStageToken(
    long AllocatedBytes,
    long Timestamp);

/// <summary>
/// Optional low-overhead stage recorder used by the headless profiling harness.
/// Normal gameplay and deterministic scenarios pass no recorder and preserve
/// the existing initialization path.
/// </summary>
public interface IScenarioInitializationStageRecorder
{
    ScenarioInitializationStageToken StartInitializationStage();

    void StopInitializationStage(
        ScenarioInitializationStage stage,
        ScenarioInitializationStageToken token);
}
