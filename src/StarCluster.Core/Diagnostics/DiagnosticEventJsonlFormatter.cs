using System;
using System.Text.Json;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Diagnostics;

/// <summary>
/// Deterministic one-event-per-line JSON representation.
/// </summary>
public static class DiagnosticEventJsonlFormatter
{
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false,
    };

    public static string Format(DiagnosticEvent diagnosticEvent)
    {
        ArgumentNullException.ThrowIfNull(diagnosticEvent);

        var payload = new
        {
            diagnosticEvent.Sequence,
            diagnosticEvent.CheckpointVersion,
            diagnosticEvent.SessionId,
            diagnosticEvent.TimestampUtc,
            EventType = diagnosticEvent.EventType.ToString(),
            diagnosticEvent.Message,
            diagnosticEvent.TurnNumber,
            Phase = diagnosticEvent.Phase?.ToString(),
            diagnosticEvent.ActorId,
            diagnosticEvent.TargetId,
            CoordinateBefore = ToPayload(diagnosticEvent.CoordinateBefore),
            CoordinateAfter = ToPayload(diagnosticEvent.CoordinateAfter),
            diagnosticEvent.Data,
        };

        return JsonSerializer.Serialize(payload, Options);
    }

    private static CoordinatePayload? ToPayload(HexCoord? coordinate) =>
        coordinate.HasValue
            ? new CoordinatePayload(coordinate.Value.Q, coordinate.Value.R)
            : null;

    private sealed record CoordinatePayload(int Q, int R);
}
