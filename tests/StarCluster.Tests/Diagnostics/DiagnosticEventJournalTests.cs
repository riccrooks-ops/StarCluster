using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using StarCluster.Core.Combat;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Diagnostics;

public sealed class DiagnosticEventJournalTests
{
    [Fact]
    public void ConstructorRequiresCheckpointVersion()
    {
        Assert.Throws<ArgumentException>(() =>
            new DiagnosticEventJournal(" ", "session"));
    }

    [Fact]
    public void ConstructorRequiresSessionId()
    {
        Assert.Throws<ArgumentException>(() =>
            new DiagnosticEventJournal("checkpoint-13a", ""));
    }

    [Fact]
    public void RecordAssignsMonotonicSequenceNumbers()
    {
        DiagnosticEventJournal journal = CreateJournal();

        DiagnosticEvent first = Record(journal, "first");
        DiagnosticEvent second = Record(journal, "second");

        Assert.Equal(1, first.Sequence);
        Assert.Equal(2, second.Sequence);
        Assert.Equal(new[] { first, second }, journal.Events.ToArray());
    }

    [Fact]
    public void RecordNormalizesTimestampToUtc()
    {
        DiagnosticEventJournal journal = CreateJournal();
        var localOffset = new DateTimeOffset(
            2026,
            7,
            27,
            7,
            15,
            0,
            TimeSpan.FromHours(-5));

        DiagnosticEvent diagnosticEvent = journal.Record(
            localOffset,
            DiagnosticEventType.DiagnosticNote,
            "normalized");

        Assert.Equal(TimeSpan.Zero, diagnosticEvent.TimestampUtc.Offset);
        Assert.Equal(localOffset.UtcDateTime, diagnosticEvent.TimestampUtc.UtcDateTime);
    }

    [Fact]
    public void RecordCopiesSuppliedData()
    {
        DiagnosticEventJournal journal = CreateJournal();
        var data = new Dictionary<string, string>
        {
            ["status"] = "WaitingForTrack",
        };

        DiagnosticEvent diagnosticEvent = journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.MissileGuidanceResolved,
            "waited",
            data: data);
        data["status"] = "changed";

        Assert.Equal("WaitingForTrack", diagnosticEvent.Data["status"]);
    }

    [Fact]
    public void RecentReturnsOnlyNewestEvents()
    {
        DiagnosticEventJournal journal = CreateJournal();
        Record(journal, "one");
        DiagnosticEvent second = Record(journal, "two");
        DiagnosticEvent third = Record(journal, "three");

        Assert.Equal(new[] { second, third }, journal.Recent(2).ToArray());
    }

    [Fact]
    public void RecentZeroReturnsEmptyCollection()
    {
        DiagnosticEventJournal journal = CreateJournal();
        Record(journal, "one");

        Assert.Empty(journal.Recent(0));
    }

    [Fact]
    public void RecentRejectsNegativeCount()
    {
        DiagnosticEventJournal journal = CreateJournal();

        Assert.Throws<ArgumentOutOfRangeException>(() => journal.Recent(-1));
    }

    [Fact]
    public void RecordRejectsNonPositiveTurnNumber()
    {
        DiagnosticEventJournal journal = CreateJournal();

        Assert.Throws<ArgumentOutOfRangeException>(() => journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.PhaseAdvanced,
            "invalid turn",
            turnNumber: 0));
    }

    [Fact]
    public void TextFormatterIncludesCheckpointTurnPhaseAndData()
    {
        DiagnosticEventJournal journal = CreateJournal();
        DiagnosticEvent diagnosticEvent = journal.Record(
            new DateTimeOffset(2026, 7, 27, 12, 0, 0, TimeSpan.Zero),
            DiagnosticEventType.MissileGuidanceResolved,
            "Missile waited for reacquisition.",
            turnNumber: 2,
            phase: TacticalTurnPhase.MissileAndInterception,
            actorId: "hostile-1",
            targetId: "ship-player",
            data: new[]
            {
                new KeyValuePair<string, string>("status", "WaitingForTrack"),
            });

        string formatted = DiagnosticEventTextFormatter.Format(diagnosticEvent);

        Assert.Contains("checkpoint-13a", formatted);
        Assert.Contains("Turn 2", formatted);
        Assert.Contains("MissileAndInterception", formatted);
        Assert.Contains("status=WaitingForTrack", formatted);
    }

    [Fact]
    public void JsonlFormatterUsesCamelCaseAndStringEnums()
    {
        DiagnosticEventJournal journal = CreateJournal();
        DiagnosticEvent diagnosticEvent = journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.TrackUpdated,
            "track changed",
            turnNumber: 1,
            phase: TacticalTurnPhase.Movement);

        using JsonDocument document = JsonDocument.Parse(
            DiagnosticEventJsonlFormatter.Format(diagnosticEvent));
        JsonElement root = document.RootElement;

        Assert.Equal("TrackUpdated", root.GetProperty("eventType").GetString());
        Assert.Equal("Movement", root.GetProperty("phase").GetString());
        Assert.Equal("checkpoint-13a", root.GetProperty("checkpointVersion").GetString());
    }

    [Fact]
    public void FormattersPreserveBeforeAndAfterCoordinates()
    {
        DiagnosticEventJournal journal = CreateJournal();
        DiagnosticEvent diagnosticEvent = journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.ShipMovementResolved,
            "moved",
            turnNumber: 1,
            phase: TacticalTurnPhase.Movement,
            coordinateBefore: new HexCoord(0, 0),
            coordinateAfter: new HexCoord(2, -1));

        string text = DiagnosticEventTextFormatter.Format(diagnosticEvent);
        using JsonDocument document = JsonDocument.Parse(
            DiagnosticEventJsonlFormatter.Format(diagnosticEvent));

        Assert.Contains("position=(0,0)->(2,-1)", text);
        Assert.Equal(
            2,
            document.RootElement
                .GetProperty("coordinateAfter")
                .GetProperty("q")
                .GetInt32());
    }

    private static DiagnosticEventJournal CreateJournal() =>
        new("checkpoint-13a", "checkpoint-13a-test-session");

    private static DiagnosticEvent Record(
        DiagnosticEventJournal journal,
        string message) => journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.DiagnosticNote,
            message);
}
