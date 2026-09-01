namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Diagnostic outcome of one sensor contact evaluation.
/// </summary>
public enum SensorContactEvaluationStatus
{
    Firm,
    Approximate,
    MissedOutOfRange,
    MissedOccluded,
    MissedByPolicy,
}
