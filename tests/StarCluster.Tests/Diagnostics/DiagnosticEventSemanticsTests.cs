using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Diagnostics;

public sealed class DiagnosticEventSemanticsTests
{
    [Fact]
    public void GuidanceLifecycleCanBeRecordedInCausalOrder()
    {
        var journal = new DiagnosticEventJournal("checkpoint-13b", "session");
        DateTimeOffset timestamp = DateTimeOffset.UtcNow;

        var start = new HexCoord(2, 1);
        var entered = new HexCoord(1, 1);
        journal.Record(timestamp, DiagnosticEventType.MissileDatalinkUpdated, "link", 2, TacticalTurnPhase.MissileAndInterception);
        journal.Record(timestamp, DiagnosticEventType.MissileLocalSensorUpdated, "action-start sensor", 2, TacticalTurnPhase.MissileAndInterception, coordinateAfter: start);
        journal.Record(timestamp, DiagnosticEventType.MissileGuidanceArbitrated, "action-start arbitration", 2, TacticalTurnPhase.MissileAndInterception, coordinateAfter: start);
        journal.Record(timestamp, DiagnosticEventType.MissileGuidanceStarted, "start", 2, TacticalTurnPhase.MissileAndInterception, coordinateBefore: start);
        journal.Record(timestamp, DiagnosticEventType.MissileMovementEdgeResolved, "edge", 2, TacticalTurnPhase.MissileAndInterception, coordinateBefore: start, coordinateAfter: entered);
        journal.Record(timestamp, DiagnosticEventType.MissileLocalSensorUpdated, "post-entry sensor", 2, TacticalTurnPhase.MissileAndInterception, coordinateAfter: entered);
        journal.Record(timestamp, DiagnosticEventType.MissileGuidanceArbitrated, "post-entry arbitration", 2, TacticalTurnPhase.MissileAndInterception, coordinateAfter: entered);
        journal.Record(timestamp, DiagnosticEventType.MissileGuidanceReplanned, "replan", 2, TacticalTurnPhase.MissileAndInterception, coordinateAfter: entered);
        journal.Record(timestamp, DiagnosticEventType.InterceptionTargetAcquired, "acquire", 2, TacticalTurnPhase.MissileAndInterception, coordinateAfter: entered);
        journal.Record(timestamp, DiagnosticEventType.MissileInterceptionAttempted, "attempt", 2, TacticalTurnPhase.MissileAndInterception, coordinateAfter: entered);
        journal.Record(timestamp, DiagnosticEventType.MissileMoved, "aggregate movement", 2, TacticalTurnPhase.MissileAndInterception, coordinateBefore: start, coordinateAfter: entered);
        journal.Record(timestamp, DiagnosticEventType.MissileGuidanceCompleted, "complete", 2, TacticalTurnPhase.MissileAndInterception, coordinateBefore: start, coordinateAfter: entered);

        Assert.Collection(
            journal.Events,
            item => Assert.Equal(DiagnosticEventType.MissileDatalinkUpdated, item.EventType),
            item =>
            {
                Assert.Equal(DiagnosticEventType.MissileLocalSensorUpdated, item.EventType);
                Assert.Equal(start, item.CoordinateAfter);
            },
            item => Assert.Equal(DiagnosticEventType.MissileGuidanceArbitrated, item.EventType),
            item => Assert.Equal(DiagnosticEventType.MissileGuidanceStarted, item.EventType),
            item =>
            {
                Assert.Equal(DiagnosticEventType.MissileMovementEdgeResolved, item.EventType);
                Assert.Equal(start, item.CoordinateBefore);
                Assert.Equal(entered, item.CoordinateAfter);
            },
            item =>
            {
                Assert.Equal(DiagnosticEventType.MissileLocalSensorUpdated, item.EventType);
                Assert.Equal(entered, item.CoordinateAfter);
            },
            item => Assert.Equal(DiagnosticEventType.MissileGuidanceArbitrated, item.EventType),
            item => Assert.Equal(DiagnosticEventType.MissileGuidanceReplanned, item.EventType),
            item => Assert.Equal(DiagnosticEventType.InterceptionTargetAcquired, item.EventType),
            item => Assert.Equal(DiagnosticEventType.MissileInterceptionAttempted, item.EventType),
            item => Assert.Equal(DiagnosticEventType.MissileMoved, item.EventType),
            item => Assert.Equal(DiagnosticEventType.MissileGuidanceCompleted, item.EventType));
    }

    [Fact]
    public void MovementEventCanPreservePlannedAndActualPaths()
    {
        var journal = new DiagnosticEventJournal("checkpoint-13b", "session");
        DiagnosticEvent item = journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.MissileMoved,
            "movement",
            turnNumber: 2,
            phase: TacticalTurnPhase.MissileAndInterception,
            data: new Dictionary<string, string>
            {
                ["plannedRoute"] = "(1,0) -> (2,0) -> (3,0)",
                ["actualMovementPath"] = "(2,0) -> (3,0)",
            });

        Assert.Equal("(1,0) -> (2,0) -> (3,0)", item.Data["plannedRoute"]);
        Assert.Equal("(2,0) -> (3,0)", item.Data["actualMovementPath"]);
    }

    [Fact]
    public void StackChangeEventPreservesVisibleCountAndIds()
    {
        var journal = new DiagnosticEventJournal("checkpoint-13b", "session");
        DiagnosticEvent item = journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.MissileStackChanged,
            "stacked",
            turnNumber: 3,
            phase: TacticalTurnPhase.MissileAndInterception,
            coordinateAfter: new HexCoord(3, -1),
            data: new Dictionary<string, string>
            {
                ["visibleCount"] = "2",
                ["salvoIds"] = "hostile-1,hostile-2",
            });

        Assert.Equal("2", item.Data["visibleCount"]);
        Assert.Equal("hostile-1,hostile-2", item.Data["salvoIds"]);
        Assert.Equal(new HexCoord(3, -1), item.CoordinateAfter);
    }

    [Fact]
    public void TacticalFeedbackIsAStableDiagnosticCategory()
    {
        var journal = new DiagnosticEventJournal("checkpoint-13b", "session");
        DiagnosticEvent item = journal.Record(
            DateTimeOffset.UtcNow,
            DiagnosticEventType.TacticalFeedback,
            "PDS fired and missed.",
            turnNumber: 1,
            phase: TacticalTurnPhase.MissileAndInterception);

        Assert.Equal(DiagnosticEventType.TacticalFeedback, item.EventType);
    }
}
