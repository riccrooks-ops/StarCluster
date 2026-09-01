using System;
using System.Linq;
using System.Text;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Diagnostics;

/// <summary>
/// Compact human-readable representation synchronized with the JSONL journal.
/// </summary>
public static class DiagnosticEventTextFormatter
{
    public static string Format(DiagnosticEvent diagnosticEvent)
    {
        ArgumentNullException.ThrowIfNull(diagnosticEvent);

        var text = new StringBuilder();
        text.Append('[')
            .Append(diagnosticEvent.Sequence.ToString("D5"))
            .Append("] ")
            .Append(diagnosticEvent.TimestampUtc.ToString("O"))
            .Append(" | ")
            .Append(diagnosticEvent.CheckpointVersion)
            .Append(" | ")
            .Append(diagnosticEvent.SessionId);

        if (diagnosticEvent.TurnNumber.HasValue)
        {
            text.Append(" | Turn ")
                .Append(diagnosticEvent.TurnNumber.Value);
        }

        if (diagnosticEvent.Phase.HasValue)
        {
            text.Append(" | ")
                .Append(diagnosticEvent.Phase.Value);
        }

        text.Append(" | ")
            .Append(diagnosticEvent.EventType)
            .Append(" | ")
            .Append(diagnosticEvent.Message);

        if (!string.IsNullOrWhiteSpace(diagnosticEvent.ActorId))
        {
            text.Append(" | actor=")
                .Append(diagnosticEvent.ActorId);
        }

        if (!string.IsNullOrWhiteSpace(diagnosticEvent.TargetId))
        {
            text.Append(" | target=")
                .Append(diagnosticEvent.TargetId);
        }

        if (diagnosticEvent.CoordinateBefore.HasValue ||
            diagnosticEvent.CoordinateAfter.HasValue)
        {
            text.Append(" | position=")
                .Append(FormatCoordinate(diagnosticEvent.CoordinateBefore))
                .Append("->")
                .Append(FormatCoordinate(diagnosticEvent.CoordinateAfter));
        }

        if (diagnosticEvent.Data.Count > 0)
        {
            text.Append(" | ")
                .Append(string.Join(
                    "; ",
                    diagnosticEvent.Data
                        .OrderBy(pair => pair.Key, StringComparer.Ordinal)
                        .Select(pair => $"{pair.Key}={pair.Value}")));
        }

        return text.ToString();
    }

    private static string FormatCoordinate(HexCoord? coordinate) =>
        coordinate.HasValue
            ? $"({coordinate.Value.Q},{coordinate.Value.R})"
            : "-";
}
