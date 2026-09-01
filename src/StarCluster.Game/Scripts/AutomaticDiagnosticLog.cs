using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using StarCluster.Core.Combat;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Geometry;

namespace StarCluster.Game;

/// <summary>
/// Automatically persists one authoritative encounter journal as synchronized
/// JSONL and readable text files. Every append is flushed immediately so a
/// crash or forced close preserves the latest completed event.
/// </summary>
public sealed class AutomaticDiagnosticLog : IDisposable
{
    private const int MaximumRecentLines = 6;

    private readonly DiagnosticEventJournal _journal;
    private readonly StreamWriter _jsonlWriter;
    private readonly StreamWriter _textWriter;
    private readonly Queue<string> _recentLines = new();
    private bool _disposed;

    public AutomaticDiagnosticLog(
        string logDirectory,
        string checkpointVersion,
        DateTimeOffset startedUtc,
        int encounterNumber)
    {
        if (string.IsNullOrWhiteSpace(logDirectory))
        {
            throw new ArgumentException(
                "A log directory is required.",
                nameof(logDirectory));
        }

        if (encounterNumber <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(encounterNumber));
        }

        Directory.CreateDirectory(logDirectory);

        string timestamp = startedUtc
            .ToUniversalTime()
            .ToString("yyyyMMdd'T'HHmmssfff'Z'");
        string safeCheckpoint = SanitizeFileComponent(checkpointVersion);
        SessionId = $"{safeCheckpoint}-{timestamp}-encounter-{encounterNumber:D3}";
        BaseFileName = $"star-cluster-{SessionId}";
        JsonlPath = Path.Combine(logDirectory, BaseFileName + ".jsonl");
        TextPath = Path.Combine(logDirectory, BaseFileName + ".log");

        _journal = new DiagnosticEventJournal(checkpointVersion, SessionId);
        _jsonlWriter = CreateWriter(JsonlPath);
        _textWriter = CreateWriter(TextPath);
    }

    public string SessionId { get; }

    public string BaseFileName { get; }

    public string JsonlPath { get; }

    public string TextPath { get; }

    public IReadOnlyList<string> RecentLines =>
        Array.AsReadOnly(_recentLines.ToArray());

    public DiagnosticEvent Record(
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
        if (_disposed)
        {
            throw new ObjectDisposedException(nameof(AutomaticDiagnosticLog));
        }

        DiagnosticEvent diagnosticEvent = _journal.Record(
            DateTimeOffset.UtcNow,
            eventType,
            message,
            turnNumber,
            phase,
            actorId,
            targetId,
            coordinateBefore,
            coordinateAfter,
            data);

        string jsonLine = DiagnosticEventJsonlFormatter.Format(diagnosticEvent);
        string textLine = DiagnosticEventTextFormatter.Format(diagnosticEvent);
        _jsonlWriter.WriteLine(jsonLine);
        _textWriter.WriteLine(textLine);
        _jsonlWriter.Flush();
        _textWriter.Flush();

        _recentLines.Enqueue(textLine);
        while (_recentLines.Count > MaximumRecentLines)
        {
            _recentLines.Dequeue();
        }

        return diagnosticEvent;
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }

        _disposed = true;
        _jsonlWriter.Dispose();
        _textWriter.Dispose();
    }

    private static StreamWriter CreateWriter(string path) => new(
        new FileStream(
            path,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.Read),
        new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));

    private static string SanitizeFileComponent(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException(
                "A checkpoint version is required.",
                nameof(value));
        }

        char[] invalid = Path.GetInvalidFileNameChars();
        char[] sanitized = value
            .Trim()
            .ToLowerInvariant()
            .Select(character =>
                invalid.Contains(character) || char.IsWhiteSpace(character)
                    ? '-'
                    : character)
            .ToArray();
        return new string(sanitized);
    }
}
