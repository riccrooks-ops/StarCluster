using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

/// <summary>
/// Compact, allocation-conscious observations captured directly while the
/// authoritative scenario executor invokes StarCluster.Core mechanics. This
/// avoids reconstructing Monte Carlo facts by materializing and scanning the
/// full diagnostic journal for every trial.
/// </summary>
public sealed class ScenarioExecutionMetrics
{
    public bool AcquisitionAttempted { get; internal set; }
    public bool SearchActivated { get; internal set; }
    public int TerminalOpportunityCount { get; internal set; }
    public int DiagnosticTerminalOpportunityCount { get; internal set; }
    public bool MissileEnteredTargetHexOpportunity { get; internal set; }
    public bool TargetEnteredMissileHexOpportunity { get; internal set; }
    public bool ActionBeganColocatedOpportunity { get; internal set; }
    public bool StationarySearchRetryOpportunity { get; internal set; }
    public bool DatalinkUpdateAttempted { get; internal set; }
    public bool DatalinkBlockedObserved { get; internal set; }
    public bool DatalinkLiveObserved { get; internal set; }
    public bool RetainedReportExpiredObserved { get; internal set; }
    public bool UsedFreshDatalinkGuidance { get; internal set; }
    public bool UsedRetainedDatalinkGuidance { get; internal set; }
    public bool UsedLocalSensorGuidance { get; internal set; }
    public bool ActiveSensorUsed { get; internal set; }
    public int MissileActions { get; internal set; }
    public int ReplanCount { get; internal set; }
    public int MaximumObservedTurnNumber { get; internal set; } = 1;

    internal void ObserveTurn(int turnNumber)
    {
        if (turnNumber > MaximumObservedTurnNumber)
        {
            MaximumObservedTurnNumber = turnNumber;
        }
    }

    internal void ObserveDatalink(MissileDatalinkUpdateResult update)
    {
        DatalinkUpdateAttempted = true;
        DatalinkBlockedObserved |= update.State == MissileDatalinkState.Blocked;
        DatalinkLiveObserved |= update.State == MissileDatalinkState.Live;
        RetainedReportExpiredObserved |= update.RetainedReportExpired;
    }

    internal void ObserveGuidance(GuidedMissileSalvo salvo, int replanCount)
    {
        MissileActions++;
        ReplanCount += replanCount;
        UsedFreshDatalinkGuidance |=
            salvo.LastGuidanceSource == MissileGuidanceReportSource.FreshDatalink;
        UsedRetainedDatalinkGuidance |=
            salvo.LastGuidanceSource == MissileGuidanceReportSource.RetainedDatalink;
        UsedLocalSensorGuidance |=
            salvo.LastGuidanceSource == MissileGuidanceReportSource.LocalSensor;
        ActiveSensorUsed |= salvo.LocalSensorTrack?.SensorMode ==
            StarCluster.Core.Combat.Tracking.SensorMode.Active;
    }

    internal void ObserveOpportunity(ScenarioTerminalOpportunitySource source)
    {
        TerminalOpportunityCount++;
        DiagnosticTerminalOpportunityCount++;
        switch (source)
        {
            case ScenarioTerminalOpportunitySource.MissileEnteredTargetHex:
                MissileEnteredTargetHexOpportunity = true;
                break;
            case ScenarioTerminalOpportunitySource.TargetEnteredMissileHex:
                TargetEnteredMissileHexOpportunity = true;
                break;
            case ScenarioTerminalOpportunitySource.ActionBeganColocated:
                ActionBeganColocatedOpportunity = true;
                break;
            case ScenarioTerminalOpportunitySource.StationarySearchRetry:
                StationarySearchRetryOpportunity = true;
                break;
            default:
                throw new ArgumentOutOfRangeException(nameof(source), source, null);
        }
    }
}
