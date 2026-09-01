using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Builds observer-safe trail segments. Explicit segment identifiers are used
/// when available; legacy samples without identifiers retain epoch-gap behavior.
/// </summary>
public static class ObservedTravelTrailService
{
    public static IReadOnlyList<IReadOnlyList<HexCoord>> BuildSegments(
        IEnumerable<ObservedTrackSample> samples)
    {
        ArgumentNullException.ThrowIfNull(samples);

        ObservedTrackSample[] ordered = samples
            .OrderBy(sample => sample.ObservationSequence)
            .ThenBy(sample => sample.ObservationEpoch)
            .ToArray();
        if (ordered.Length == 0)
        {
            return Array.Empty<IReadOnlyList<HexCoord>>();
        }

        var segments = new List<IReadOnlyList<HexCoord>>();
        var current = new List<HexCoord> { ordered[0].Coordinate };
        ObservedTrackSample previous = ordered[0];

        for (int index = 1; index < ordered.Length; index++)
        {
            ObservedTrackSample sample = ordered[index];
            bool explicitSegments = previous.SegmentId > 0 || sample.SegmentId > 0;
            bool continuous = explicitSegments
                ? previous.SegmentId > 0 && previous.SegmentId == sample.SegmentId
                : sample.ObservationEpoch >= previous.ObservationEpoch &&
                  sample.ObservationEpoch <= previous.ObservationEpoch + 1;

            if (!continuous)
            {
                segments.Add(Array.AsReadOnly(current.ToArray()));
                current = new List<HexCoord>();
            }

            if (current.Count == 0 || current[^1] != sample.Coordinate)
            {
                current.Add(sample.Coordinate);
            }

            previous = sample;
        }

        segments.Add(Array.AsReadOnly(current.ToArray()));
        return Array.AsReadOnly(segments.ToArray());
    }
}
