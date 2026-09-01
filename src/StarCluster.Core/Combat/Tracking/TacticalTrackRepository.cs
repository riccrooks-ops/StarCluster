using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Stores independent observer-target tracks. Absence means Unknown; it is not
/// equivalent to a Lost record.
/// </summary>
public sealed class TacticalTrackRepository
{
    private readonly Dictionary<(string ObserverId, string TargetId), TacticalTrackRecord>
        _records = new();

    public IReadOnlyList<TacticalTrackRecord> Records =>
        Array.AsReadOnly(_records.Values.ToArray());

    public TacticalTrackRecord? Get(string observerId, string targetId)
    {
        ValidateId(observerId, nameof(observerId));
        ValidateId(targetId, nameof(targetId));
        return _records.TryGetValue((observerId, targetId), out TacticalTrackRecord? record)
            ? record
            : null;
    }

    public IReadOnlyList<TacticalTrackRecord> ForObserver(string observerId)
    {
        ValidateId(observerId, nameof(observerId));
        return Array.AsReadOnly(
            _records.Values
                .Where(record => string.Equals(
                    record.ObserverId,
                    observerId,
                    StringComparison.Ordinal))
                .ToArray());
    }

    public TacticalTrackRecord SeedPriorIntelligence(
        string observerId,
        string targetId,
        HexCoord lastKnownCoordinate,
        long sequence,
        int uncertaintyRadiusHexes = 1)
    {
        ValidateId(observerId, nameof(observerId));
        ValidateId(targetId, nameof(targetId));

        if (sequence < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(sequence));
        }

        if (uncertaintyRadiusHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(uncertaintyRadiusHexes));
        }

        var record = new TacticalTrackRecord(
            observerId,
            targetId,
            TacticalTrackSourceType.PreviousIntelligence,
            TacticalTrackQuality.Stale,
            lastKnownCoordinate,
            lastKnownCoordinate,
            sequence,
            missedUpdateCount: 0,
            uncertaintyRadiusHexes: uncertaintyRadiusHexes);
        _records[(observerId, targetId)] = record;
        return record;
    }

    internal TacticalTrackRecord UpsertDetected(
        string observerId,
        TacticalTrackObservation observation,
        long sequence,
        int observationEpoch)
    {
        HexCoord coordinate = observation.EstimatedCoordinate!.Value;
        TacticalTrackQuality quality = observation.Precise
            ? TacticalTrackQuality.Firm
            : TacticalTrackQuality.Approximate;

        if (!_records.TryGetValue(
                (observerId, observation.TargetId),
                out TacticalTrackRecord? record))
        {
            record = new TacticalTrackRecord(
                observerId,
                observation.TargetId,
                observation.SourceType,
                quality,
                coordinate,
                coordinate,
                sequence,
                missedUpdateCount: 0,
                uncertaintyRadiusHexes: observation.UncertaintyRadiusHexes,
                lastObservedEpoch: observationEpoch,
                lastAgedEpoch: null);
            record.RecordObservedCoordinate(coordinate, observationEpoch, sequence);
            _records[(observerId, observation.TargetId)] = record;
            return record;
        }

        record.SourceType = observation.SourceType;
        record.Quality = quality;
        record.EstimatedCoordinate = coordinate;
        record.LastObservedCoordinate = coordinate;
        record.LastUpdatedSequence = sequence;
        record.MissedUpdateCount = 0;
        record.UncertaintyRadiusHexes = observation.UncertaintyRadiusHexes;
        record.LastObservedEpoch = observationEpoch;
        record.RecordObservedCoordinate(coordinate, observationEpoch, sequence);
        return record;
    }

    internal TacticalTrackRecord? ApplyMissed(
        string observerId,
        string targetId,
        ComputingProfile computingProfile,
        long sequence,
        int observationEpoch,
        out bool ageAdvanced)
    {
        ageAdvanced = false;
        if (!_records.TryGetValue((observerId, targetId), out TacticalTrackRecord? record))
        {
            return null;
        }

        record.LastUpdatedSequence = sequence;
        record.CloseObservedSegment();

        // Losing visibility after a successful observation in the same epoch
        // must immediately make the track Stale at the last observed
        // coordinate. This is an event-driven visibility transition, not a
        // tactical-time age step, so it does not increment missed age or
        // uncertainty repeatedly.
        if (record.LastObservedEpoch == observationEpoch)
        {
            record.Quality = TacticalTrackQuality.Stale;
            record.EstimatedCoordinate = record.LastObservedCoordinate;
            record.UncertaintyRadiusHexes = Math.Max(
                1,
                record.UncertaintyRadiusHexes);
            return record;
        }

        // Repeated missed reevaluations can consume only one age step in an
        // observation epoch.
        if (record.LastAgedEpoch == observationEpoch)
        {
            return record;
        }

        ageAdvanced = true;
        record.LastAgedEpoch = observationEpoch;
        record.MissedUpdateCount++;

        if (record.MissedUpdateCount > computingProfile.StaleRetentionUpdates)
        {
            record.Quality = TacticalTrackQuality.Lost;
            record.EstimatedCoordinate = null;
            return record;
        }

        record.Quality = TacticalTrackQuality.Stale;
        record.EstimatedCoordinate = record.LastObservedCoordinate;
        record.UncertaintyRadiusHexes +=
            computingProfile.UncertaintyGrowthPerMissedUpdate;
        return record;
    }

    public void Clear() => _records.Clear();

    private static void ValidateId(string value, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException("A stable non-empty ID is required.", parameterName);
        }
    }
}
