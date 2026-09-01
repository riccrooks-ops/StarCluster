using System;
using System.Collections.Generic;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Observer-specific knowledge about one contact. The record never exposes the
/// target's authoritative coordinate unless a supplied observation supports it.
/// Track aging is epoch-based, while observed-trail continuity is segment-based.
/// </summary>
public sealed class TacticalTrackRecord
{
    private readonly List<HexCoord> _observedCoordinateHistory = new();
    private readonly List<ObservedTrackSample> _observedSamples = new();
    private readonly IReadOnlyList<HexCoord> _observedCoordinateHistoryView;
    private readonly IReadOnlyList<ObservedTrackSample> _observedSamplesView;
    private int _nextObservedSegmentId = 1;
    private int? _activeObservedSegmentId;

    internal TacticalTrackRecord(
        string observerId,
        string targetId,
        TacticalTrackSourceType sourceType,
        TacticalTrackQuality quality,
        HexCoord? estimatedCoordinate,
        HexCoord? lastObservedCoordinate,
        long lastUpdatedSequence,
        int missedUpdateCount,
        int uncertaintyRadiusHexes,
        int? lastObservedEpoch = null,
        int? lastAgedEpoch = null)
    {
        if (string.IsNullOrWhiteSpace(observerId))
        {
            throw new ArgumentException("An observer ID is required.", nameof(observerId));
        }

        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException("A target ID is required.", nameof(targetId));
        }

        ObserverId = observerId;
        TargetId = targetId;
        SourceType = sourceType;
        Quality = quality;
        EstimatedCoordinate = estimatedCoordinate;
        LastObservedCoordinate = lastObservedCoordinate;
        LastUpdatedSequence = lastUpdatedSequence;
        MissedUpdateCount = missedUpdateCount;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
        LastObservedEpoch = lastObservedEpoch;
        LastAgedEpoch = lastAgedEpoch;
        _observedCoordinateHistoryView = _observedCoordinateHistory.AsReadOnly();
        _observedSamplesView = _observedSamples.AsReadOnly();
    }

    public string ObserverId { get; }

    public string TargetId { get; }

    public TacticalTrackSourceType SourceType { get; internal set; }

    public TacticalTrackQuality Quality { get; internal set; }

    public HexCoord? EstimatedCoordinate { get; internal set; }

    public HexCoord? LastObservedCoordinate { get; internal set; }

    public long LastUpdatedSequence { get; internal set; }

    public int MissedUpdateCount { get; internal set; }

    public int UncertaintyRadiusHexes { get; internal set; }

    public int? LastObservedEpoch { get; internal set; }

    public int? LastAgedEpoch { get; internal set; }

    public IReadOnlyList<HexCoord> ObservedCoordinateHistory =>
        _observedCoordinateHistoryView;

    public IReadOnlyList<ObservedTrackSample> ObservedSamples =>
        _observedSamplesView;

    public bool HasOpenObservedSegment => _activeObservedSegmentId.HasValue;

    public int? ActiveObservedSegmentId => _activeObservedSegmentId;

    public bool IsVisibleOnTacticalMap =>
        Quality != TacticalTrackQuality.Lost && EstimatedCoordinate.HasValue;

    public bool SupportsPrecisionDirectFire =>
        Quality == TacticalTrackQuality.Firm && EstimatedCoordinate.HasValue;

    internal void RecordObservedCoordinate(
        HexCoord coordinate,
        int observationEpoch,
        long observationSequence)
    {
        if (!_activeObservedSegmentId.HasValue)
        {
            _activeObservedSegmentId = _nextObservedSegmentId++;
        }

        if (_observedCoordinateHistory.Count == 0 ||
            _observedCoordinateHistory[^1] != coordinate)
        {
            _observedCoordinateHistory.Add(coordinate);
        }

        bool duplicateSample = _observedSamples.Count > 0 &&
            _observedSamples[^1].Coordinate == coordinate &&
            _observedSamples[^1].SegmentId == _activeObservedSegmentId.Value;
        if (!duplicateSample)
        {
            _observedSamples.Add(new ObservedTrackSample(
                coordinate,
                observationEpoch,
                _activeObservedSegmentId.Value,
                observationSequence));
        }
    }

    internal void CloseObservedSegment() => _activeObservedSegmentId = null;
}
