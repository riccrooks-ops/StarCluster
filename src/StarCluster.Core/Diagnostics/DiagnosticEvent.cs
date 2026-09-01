using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Diagnostics;

/// <summary>
/// One immutable authoritative diagnostic event. The journal is deliberately
/// richer than a future player-visible combat log and may contain hidden truth.
/// </summary>
public sealed class DiagnosticEvent
{
    internal DiagnosticEvent(
        long sequence,
        string checkpointVersion,
        string sessionId,
        DateTimeOffset timestampUtc,
        DiagnosticEventType eventType,
        string message,
        int? turnNumber,
        TacticalTurnPhase? phase,
        string? actorId,
        string? targetId,
        HexCoord? coordinateBefore,
        HexCoord? coordinateAfter,
        IReadOnlyDictionary<string, string> data)
    {
        Sequence = sequence;
        CheckpointVersion = checkpointVersion;
        SessionId = sessionId;
        TimestampUtc = timestampUtc;
        EventType = eventType;
        Message = message;
        TurnNumber = turnNumber;
        Phase = phase;
        ActorId = actorId;
        TargetId = targetId;
        CoordinateBefore = coordinateBefore;
        CoordinateAfter = coordinateAfter;
        Data = data;
    }

    public long Sequence { get; }

    public string CheckpointVersion { get; }

    public string SessionId { get; }

    public DateTimeOffset TimestampUtc { get; }

    public DiagnosticEventType EventType { get; }

    public string Message { get; }

    public int? TurnNumber { get; }

    public TacticalTurnPhase? Phase { get; }

    public string? ActorId { get; }

    public string? TargetId { get; }

    public HexCoord? CoordinateBefore { get; }

    public HexCoord? CoordinateAfter { get; }

    public IReadOnlyDictionary<string, string> Data { get; }
}
