using System;
using System.Collections.Generic;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Applies the first sensor pass before a system map is presented. This class
/// makes the initialization order explicit and reusable for scenario reset and
/// headless scenario initialization.
/// </summary>
public static class SystemEntryTrackInitializer
{
    public static IReadOnlyList<TacticalTrackUpdateResult> Initialize(
        TacticalTrackRepository repository,
        string observerId,
        IEnumerable<TacticalTrackObservation> observations,
        ComputingProfile computingProfile,
        long sequence,
        TrackUpdateTrigger trigger = TrackUpdateTrigger.SystemEntry) =>
        Initialize(
            repository,
            observerId,
            observations,
            computingProfile,
            sequence,
            observationEpoch: 1,
            trigger: trigger);

    public static IReadOnlyList<TacticalTrackUpdateResult> Initialize(
        TacticalTrackRepository repository,
        string observerId,
        IEnumerable<TacticalTrackObservation> observations,
        ComputingProfile computingProfile,
        long sequence,
        int observationEpoch,
        TrackUpdateTrigger trigger = TrackUpdateTrigger.SystemEntry)
    {
        Validate(repository, observations, computingProfile, observationEpoch);

        var results = new List<TacticalTrackUpdateResult>();
        foreach (TacticalTrackObservation observation in observations)
        {
            results.Add(TacticalTrackUpdateService.Apply(
                repository,
                observerId,
                observation,
                computingProfile,
                sequence,
                trigger,
                observationEpoch));
        }

        return results.AsReadOnly();
    }

    public static void InitializeWithoutResults(
        TacticalTrackRepository repository,
        string observerId,
        IEnumerable<TacticalTrackObservation> observations,
        ComputingProfile computingProfile,
        long sequence,
        int observationEpoch,
        TrackUpdateTrigger trigger = TrackUpdateTrigger.SystemEntry)
    {
        Validate(repository, observations, computingProfile, observationEpoch);

        foreach (TacticalTrackObservation observation in observations)
        {
            TacticalTrackUpdateService.ApplyWithoutResult(
                repository,
                observerId,
                observation,
                computingProfile,
                sequence,
                trigger,
                observationEpoch);
        }
    }

    private static void Validate(
        TacticalTrackRepository repository,
        IEnumerable<TacticalTrackObservation> observations,
        ComputingProfile computingProfile,
        int observationEpoch)
    {
        ArgumentNullException.ThrowIfNull(repository);
        ArgumentNullException.ThrowIfNull(observations);
        ArgumentNullException.ThrowIfNull(computingProfile);
        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }
    }
}
