using System.Diagnostics;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

public enum ScenarioAllocationStage
{
    TrialTotal,
    SeedDerivation,
    TrialSetup,
    ExecutorConstruction,
    RuntimeInitialization,
    InitializationMapCreation,
    InitializationStaticObjectPlacement,
    InitializationShipStateCreation,
    InitializationPriorTrackSeeding,
    InitializationMissileStateCreation,
    InitializationTurnAndJournalCreation,
    InitializationInitialTrackRefresh,
    InitializationDiagnostics,
    InitializationResultConstruction,
    ShipMovement,
    ShipMovementPlanning,
    ShipMovementStepExecution,
    TargetMovementObservation,
    TrackRefreshAfterShipMovement,
    MissileAdvancement,
    MissileInterceptionContext,
    MissileDatalinkUpdate,
    MissileGuidanceAdvance,
    MissileOutcomeCapture,
    TrackRefreshAfterMissileMovement,
    PhaseAdvancement,
    ScenarioFinalization,
    ResultProjection,
}

public readonly record struct ScenarioAllocationToken(
    long AllocatedBytes,
    long Timestamp);

public readonly record struct ScenarioAllocationMeasurement(
    long AllocatedBytes,
    long ElapsedTicks,
    int InvocationCount);

/// <summary>
/// Per-trial, single-thread allocation and elapsed-time attribution. The
/// scenario runner executes each trial synchronously on one worker thread, so
/// GC.GetAllocatedBytesForCurrentThread can measure nested stages without
/// introducing allocation-heavy tracing. One profile instance may be reset and
/// reused for many sequential trials.
/// </summary>
public sealed class ScenarioAllocationProfile : IScenarioInitializationStageRecorder
{
    private static readonly int StageCount =
        Enum.GetValues<ScenarioAllocationStage>().Length;

    private readonly long[] _allocatedBytes = new long[StageCount];
    private readonly long[] _elapsedTicks = new long[StageCount];
    private readonly int[] _invocationCounts = new int[StageCount];

    public void Reset()
    {
        Array.Clear(_allocatedBytes, 0, _allocatedBytes.Length);
        Array.Clear(_elapsedTicks, 0, _elapsedTicks.Length);
        Array.Clear(_invocationCounts, 0, _invocationCounts.Length);
    }

    public ScenarioAllocationToken Start() => new(
        GC.GetAllocatedBytesForCurrentThread(),
        Stopwatch.GetTimestamp());

    public void Stop(
        ScenarioAllocationStage stage,
        ScenarioAllocationToken token)
    {
        int index = (int)stage;
        long allocated = GC.GetAllocatedBytesForCurrentThread() -
            token.AllocatedBytes;
        long elapsed = Stopwatch.GetTimestamp() - token.Timestamp;
        _allocatedBytes[index] += Math.Max(0, allocated);
        _elapsedTicks[index] += Math.Max(0, elapsed);
        _invocationCounts[index]++;
    }

    public ScenarioAllocationMeasurement Get(ScenarioAllocationStage stage)
    {
        int index = (int)stage;
        return new ScenarioAllocationMeasurement(
            _allocatedBytes[index],
            _elapsedTicks[index],
            _invocationCounts[index]);
    }
    ScenarioInitializationStageToken
        IScenarioInitializationStageRecorder.StartInitializationStage() => new(
            GC.GetAllocatedBytesForCurrentThread(),
            Stopwatch.GetTimestamp());

    void IScenarioInitializationStageRecorder.StopInitializationStage(
        ScenarioInitializationStage stage,
        ScenarioInitializationStageToken token)
    {
        ScenarioAllocationStage allocationStage = stage switch
        {
            ScenarioInitializationStage.MapCreation =>
                ScenarioAllocationStage.InitializationMapCreation,
            ScenarioInitializationStage.StaticObjectPlacement =>
                ScenarioAllocationStage.InitializationStaticObjectPlacement,
            ScenarioInitializationStage.ShipStateCreation =>
                ScenarioAllocationStage.InitializationShipStateCreation,
            ScenarioInitializationStage.PriorTrackSeeding =>
                ScenarioAllocationStage.InitializationPriorTrackSeeding,
            ScenarioInitializationStage.MissileStateCreation =>
                ScenarioAllocationStage.InitializationMissileStateCreation,
            ScenarioInitializationStage.TurnAndJournalCreation =>
                ScenarioAllocationStage.InitializationTurnAndJournalCreation,
            ScenarioInitializationStage.InitialTrackRefresh =>
                ScenarioAllocationStage.InitializationInitialTrackRefresh,
            ScenarioInitializationStage.InitializationDiagnostics =>
                ScenarioAllocationStage.InitializationDiagnostics,
            ScenarioInitializationStage.ResultConstruction =>
                ScenarioAllocationStage.InitializationResultConstruction,
            _ => throw new InvalidOperationException(
                $"Unsupported initialization stage '{stage}'."),
        };
        Stop(
            allocationStage,
            new ScenarioAllocationToken(token.AllocatedBytes, token.Timestamp));
    }

}
