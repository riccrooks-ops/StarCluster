using System;
using System.Collections.Generic;
using System.Linq;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Selects the best missile report by quality, recency, uncertainty, and then
/// local-source preference. The final local tie-breaker avoids depending on an
/// equally good external copy when the missile has immediate local evidence.
/// </summary>
public static class MissileGuidanceArbitrator
{
    public static MissileGuidanceDecision Select(
        string targetId,
        params MissileGuidanceReportCandidate?[] candidates)
    {
        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException(
                "A target ID is required.",
                nameof(targetId));
        }

        ArgumentNullException.ThrowIfNull(candidates);

        MissileGuidanceReportCandidate[] usable = candidates
            .Where(candidate => candidate?.IsUsable == true)
            .Cast<MissileGuidanceReportCandidate>()
            .ToArray();

        if (usable.Length == 0)
        {
            return new MissileGuidanceDecision(
                targetId,
                selectedCandidate: null,
                Array.Empty<MissileGuidanceReportCandidate>(),
                "No usable launcher, retained, or local sensor report was available.");
        }

        MissileGuidanceReportCandidate selected = usable
            .OrderByDescending(candidate => QualityRank(candidate.Snapshot.Quality))
            .ThenByDescending(candidate => candidate.SourceObservationEpoch)
            .ThenBy(candidate => candidate.UncertaintyRadiusHexes)
            .ThenByDescending(candidate =>
                candidate.Source == MissileGuidanceReportSource.LocalSensor)
            .ThenBy(candidate => candidate.Source)
            .First();

        string reason =
            $"Selected {selected.Source}: quality {selected.Snapshot.Quality}, " +
            $"observation epoch {selected.SourceObservationEpoch}, uncertainty " +
            $"{selected.UncertaintyRadiusHexes}; local sensor wins only an otherwise exact tie.";

        return new MissileGuidanceDecision(
            targetId,
            selected,
            usable,
            reason);
    }

    private static int QualityRank(MissileTargetTrackQuality quality) =>
        quality switch
        {
            MissileTargetTrackQuality.Current => 3,
            MissileTargetTrackQuality.Approximate => 2,
            MissileTargetTrackQuality.Stale => 1,
            _ => 0,
        };
}
