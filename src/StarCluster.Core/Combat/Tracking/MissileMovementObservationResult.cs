using System;
using System.Collections.Generic;
using System.Linq;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Applied per-hex observer checks for one missile action.
/// </summary>
public sealed class MissileMovementObservationResult
{
    internal MissileMovementObservationResult(
        IEnumerable<MissileMovementObservationStep> steps,
        IEnumerable<TacticalTrackUpdateResult> updates,
        long finalSequence)
    {
        Steps = Array.AsReadOnly(new List<MissileMovementObservationStep>(steps).ToArray());
        Updates = Array.AsReadOnly(new List<TacticalTrackUpdateResult>(updates).ToArray());
        FinalSequence = finalSequence;
    }

    public IReadOnlyList<MissileMovementObservationStep> Steps { get; }

    public IReadOnlyList<TacticalTrackUpdateResult> Updates { get; }

    public long FinalSequence { get; }

    public bool AnyDetected => Steps.Any(step => step.Detected);
}
