using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Diagnostics;

/// <summary>
/// In-memory authoritative event sequence. Persistence is supplied by the host
/// so StarCluster.Core remains independent from Godot and operating-system APIs.
/// </summary>
public sealed class DiagnosticEventJournal
{
    private readonly List<DiagnosticEvent> _events = new();
    private readonly IReadOnlyList<DiagnosticEvent> _eventsView;
    private long _nextSequence = 1;

    public DiagnosticEventJournal(
        string checkpointVersion,
        string sessionId)
    {
        if (string.IsNullOrWhiteSpace(checkpointVersion))
        {
            throw new ArgumentException(
                "A checkpoint version is required.",
                nameof(checkpointVersion));
        }

        if (string.IsNullOrWhiteSpace(sessionId))
        {
            throw new ArgumentException(
                "A session ID is required.",
                nameof(sessionId));
        }

        CheckpointVersion = checkpointVersion;
        SessionId = sessionId;
        _eventsView = _events.AsReadOnly();
    }

    public string CheckpointVersion { get; }

    public string SessionId { get; }

    public IReadOnlyList<DiagnosticEvent> Events => _eventsView;

    public DiagnosticEvent Record(
        DateTimeOffset timestampUtc,
        DiagnosticEventType eventType,
        string message,
        int? turnNumber = null,
        TacticalTurnPhase? phase = null,
        string? actorId = null,
        string? targetId = null,
        HexCoord? coordinateBefore = null,
        HexCoord? coordinateAfter = null,
        IEnumerable<KeyValuePair<string, string>>? data = null)
    {
        if (timestampUtc.Offset != TimeSpan.Zero)
        {
            timestampUtc = timestampUtc.ToUniversalTime();
        }

        if (!Enum.IsDefined(eventType))
        {
            throw new ArgumentOutOfRangeException(
                nameof(eventType),
                eventType,
                null);
        }

        if (string.IsNullOrWhiteSpace(message))
        {
            throw new ArgumentException(
                "A diagnostic message is required.",
                nameof(message));
        }

        if (turnNumber is <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(turnNumber),
                turnNumber,
                "Turn numbers begin at one.");
        }

        var copiedData = new Dictionary<string, string>(StringComparer.Ordinal);
        if (data is not null)
        {
            foreach (KeyValuePair<string, string> pair in data)
            {
                if (string.IsNullOrWhiteSpace(pair.Key))
                {
                    throw new ArgumentException(
                        "Diagnostic data keys must be non-empty.",
                        nameof(data));
                }

                copiedData[pair.Key] = pair.Value ?? string.Empty;
            }
        }

        var diagnosticEvent = new DiagnosticEvent(
            _nextSequence++,
            CheckpointVersion,
            SessionId,
            timestampUtc,
            eventType,
            message,
            turnNumber,
            phase,
            actorId,
            targetId,
            coordinateBefore,
            coordinateAfter,
            copiedData);
        _events.Add(diagnosticEvent);
        return diagnosticEvent;
    }

    public IReadOnlyList<DiagnosticEvent> Recent(int maximumCount)
    {
        if (maximumCount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumCount));
        }

        return Array.AsReadOnly(
            _events
                .Skip(Math.Max(0, _events.Count - maximumCount))
                .ToArray());
    }
}
