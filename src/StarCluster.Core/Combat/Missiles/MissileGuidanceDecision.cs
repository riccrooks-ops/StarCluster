using System;
using System.Collections.Generic;
using System.Linq;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Deterministic arbitration result for one missile guidance opportunity.
/// </summary>
public sealed class MissileGuidanceDecision
{
    internal MissileGuidanceDecision(
        string targetId,
        MissileGuidanceReportCandidate? selectedCandidate,
        IEnumerable<MissileGuidanceReportCandidate> candidates,
        string reason)
    {
        if (string.IsNullOrWhiteSpace(targetId))
        {
            throw new ArgumentException(
                "A target ID is required.",
                nameof(targetId));
        }

        TargetId = targetId;
        SelectedCandidate = selectedCandidate;
        Candidates = Array.AsReadOnly(candidates.ToArray());
        Reason = string.IsNullOrWhiteSpace(reason)
            ? "No arbitration reason was supplied."
            : reason;
    }

    public string TargetId { get; }

    public MissileGuidanceReportCandidate? SelectedCandidate { get; }

    public IReadOnlyList<MissileGuidanceReportCandidate> Candidates { get; }

    public string Reason { get; }

    public MissileGuidanceReportSource SelectedSource =>
        SelectedCandidate?.Source ?? MissileGuidanceReportSource.None;

    public MissileTargetTrackSnapshot SelectedSnapshot =>
        SelectedCandidate?.Snapshot ?? MissileTargetTrackSnapshot.Lost(TargetId);

    public bool HasUsableReport => SelectedCandidate?.IsUsable == true;
}
