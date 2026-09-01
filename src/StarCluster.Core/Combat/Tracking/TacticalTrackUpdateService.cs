using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Deterministically creates, refreshes, degrades, and loses observer-specific
/// tracks from supplied observations. Visibility may be reevaluated after every
/// relevant event, while missed-track aging advances at most once per supplied
/// observation epoch.
/// </summary>
public static class TacticalTrackUpdateService
{
    /// <summary>
    /// Backward-compatible overload. Callers that do not supply an epoch retain
    /// the former one-age-step-per-call behavior by treating the sequence as the
    /// epoch identifier.
    /// </summary>
    public static TacticalTrackUpdateResult Apply(
        TacticalTrackRepository repository,
        string observerId,
        TacticalTrackObservation observation,
        ComputingProfile computingProfile,
        long sequence,
        TrackUpdateTrigger trigger) =>
        Apply(
            repository,
            observerId,
            observation,
            computingProfile,
            sequence,
            trigger,
            checked((int)sequence));

    public static TacticalTrackUpdateResult Apply(
        TacticalTrackRepository repository,
        string observerId,
        TacticalTrackObservation observation,
        ComputingProfile computingProfile,
        long sequence,
        TrackUpdateTrigger trigger,
        int observationEpoch)
    {
        TacticalTrackRecord? record = ApplyCore(
            repository,
            observerId,
            observation,
            computingProfile,
            sequence,
            observationEpoch,
            out TacticalTrackQuality? previousQuality,
            out bool created,
            out bool ageAdvanced);

        return new TacticalTrackUpdateResult(
            observerId,
            observation.TargetId,
            trigger,
            previousQuality,
            record,
            created,
            observationEpoch,
            ageAdvanced);
    }

    /// <summary>
    /// Applies the identical authoritative track mutation without allocating a
    /// diagnostic result object. This is intended for high-volume simulations
    /// that do not consume per-refresh presentation diagnostics.
    /// </summary>
    public static void ApplyWithoutResult(
        TacticalTrackRepository repository,
        string observerId,
        TacticalTrackObservation observation,
        ComputingProfile computingProfile,
        long sequence,
        TrackUpdateTrigger trigger,
        int observationEpoch)
    {
        _ = trigger;
        _ = ApplyCore(
            repository,
            observerId,
            observation,
            computingProfile,
            sequence,
            observationEpoch,
            out _,
            out _,
            out _);
    }

    private static TacticalTrackRecord? ApplyCore(
        TacticalTrackRepository repository,
        string observerId,
        TacticalTrackObservation observation,
        ComputingProfile computingProfile,
        long sequence,
        int observationEpoch,
        out TacticalTrackQuality? previousQuality,
        out bool created,
        out bool ageAdvanced)
    {
        ArgumentNullException.ThrowIfNull(repository);
        ArgumentNullException.ThrowIfNull(observation);
        ArgumentNullException.ThrowIfNull(computingProfile);

        if (string.IsNullOrWhiteSpace(observerId))
        {
            throw new ArgumentException("An observer ID is required.", nameof(observerId));
        }

        if (sequence < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(sequence));
        }

        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }

        TacticalTrackRecord? existing = repository.Get(observerId, observation.TargetId);
        previousQuality = existing?.Quality;
        created = existing is null && observation.Detected;
        ageAdvanced = false;

        return observation.Detected
            ? repository.UpsertDetected(
                observerId,
                observation,
                sequence,
                observationEpoch)
            : repository.ApplyMissed(
                observerId,
                observation.TargetId,
                computingProfile,
                sequence,
                observationEpoch,
                out ageAdvanced);
    }
}
