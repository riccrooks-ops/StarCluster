using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

public static class ScenarioAssertionEvaluator
{
    public static IReadOnlyList<string> Evaluate(
        ScenarioDocument document,
        ScenarioInitializationResult runtime,
        IReadOnlyList<MissileInterceptionOpportunity> opportunities)
    {
        var failures = new List<string>();

        foreach (ShipExpectationDocument expected in document.Expect.Ships)
        {
            if (!runtime.Ships.TryGetValue(expected.Id, out ScenarioShipState? ship))
            {
                failures.Add($"Expected ship '{expected.Id}' does not exist.");
                continue;
            }

            if (expected.Position is not null)
            {
                Equal(
                    failures,
                    $"{expected.Id}.position",
                    ScenarioDocumentMapper.ToCoordinate(expected.Position),
                    ship.Coordinate);
            }
        }

        foreach (MissileExpectationDocument expected in document.Expect.Missiles)
        {
            GuidedMissileSalvo? salvo = runtime.MissileEngagement.Find(expected.Id);
            if (salvo is null)
            {
                failures.Add($"Expected Missile Flight '{expected.Id}' does not exist.");
                continue;
            }

            if (expected.Status is not null)
            {
                GuidedMissileStatus status = ScenarioDocumentMapper.ParseEnum<GuidedMissileStatus>(
                    expected.Status,
                    "expected missile status");
                Equal(failures, $"{expected.Id}.status", status, salvo.Status);
            }

            if (expected.TerminalOutcome is not null)
            {
                MissileTerminalOutcome outcome =
                    ScenarioDocumentMapper.ParseEnum<MissileTerminalOutcome>(
                        expected.TerminalOutcome,
                        "expected terminal outcome");
                Equal(
                    failures,
                    $"{expected.Id}.terminalOutcome",
                    outcome,
                    salvo.LastTerminalResolution?.Outcome);
            }

            if (expected.Position is not null)
            {
                Equal(
                    failures,
                    $"{expected.Id}.position",
                    ScenarioDocumentMapper.ToCoordinate(expected.Position),
                    salvo.CurrentCoordinate);
            }

            OptionalEqual(failures, $"{expected.Id}.distanceTraveled", expected.DistanceTraveled, salvo.DistanceTraveled);
            OptionalEqual(failures, $"{expected.Id}.stationarySearchFuelSpent", expected.StationarySearchFuelSpent, salvo.StationarySearchFuelSpent);
            OptionalEqual(failures, $"{expected.Id}.totalFuelSpent", expected.TotalFuelSpent, salvo.TotalFuelSpent);
            OptionalEqual(failures, $"{expected.Id}.attackRoll", expected.AttackRoll, salvo.LastTerminalResolution?.AttackRoll);
            OptionalEqual(failures, $"{expected.Id}.acquisitionRoll", expected.AcquisitionRoll, salvo.LastTerminalResolution?.AcquisitionRoll);
        }

        foreach (TrackExpectationDocument expected in document.Expect.Tracks)
        {
            TacticalTrackRecord? track = runtime.Tracks.Get(
                expected.ObserverId,
                expected.TargetId);
            TacticalTrackQuality quality =
                ScenarioDocumentMapper.ParseEnum<TacticalTrackQuality>(
                    expected.Quality,
                    "expected track quality");
            Equal(
                failures,
                $"track {expected.ObserverId}->{expected.TargetId}.quality",
                quality,
                track?.Quality);
            if (expected.Position is not null)
            {
                Equal(
                    failures,
                    $"track {expected.ObserverId}->{expected.TargetId}.position",
                    ScenarioDocumentMapper.ToCoordinate(expected.Position),
                    track?.EstimatedCoordinate);
            }
        }

        MissileInterceptionOpportunity[] expectedOpportunities =
            document.Expect.InterceptionOpportunities
                .Select(value => ScenarioDocumentMapper.ParseEnum<MissileInterceptionOpportunity>(
                    value,
                    "expected interception opportunity"))
                .ToArray();
        if (!expectedOpportunities.SequenceEqual(opportunities))
        {
            failures.Add(
                "interception opportunities expected [" +
                string.Join(", ", expectedOpportunities) +
                "] but were [" + string.Join(", ", opportunities) + "].");
        }

        EvaluateEventOrder(document, runtime.Journal.Events, failures);
        return failures.AsReadOnly();
    }

    private static void EvaluateEventOrder(
        ScenarioDocument document,
        IReadOnlyList<DiagnosticEvent> events,
        ICollection<string> failures)
    {
        int searchStart = 0;
        var matched = new List<(DiagnosticEventType EventType, int Index)>();
        foreach (string required in document.Expect.RequiredEventsInOrder)
        {
            if (!Enum.TryParse(required, ignoreCase: true, out DiagnosticEventType eventType))
            {
                failures.Add($"Unknown required event type '{required}'.");
                continue;
            }

            int found = -1;
            for (int index = searchStart; index < events.Count; index++)
            {
                if (events[index].EventType == eventType)
                {
                    found = index;
                    break;
                }
            }

            if (found < 0)
            {
                string matchedText = matched.Count == 0
                    ? "none"
                    : string.Join(
                        ", ",
                        matched.Select(item => $"{item.EventType}@{item.Index}"));
                int[] allIndexes = events
                    .Select((item, index) => new { item.EventType, Index = index })
                    .Where(item => item.EventType == eventType)
                    .Select(item => item.Index)
                    .ToArray();
                string allIndexesText = allIndexes.Length == 0
                    ? "none"
                    : string.Join(", ", allIndexes);

                failures.Add(
                    $"Required event '{eventType}' was not found after event index " +
                    $"{searchStart - 1}. Matched required events: [{matchedText}]. " +
                    $"All '{eventType}' event indexes: [{allIndexesText}].");
                return;
            }

            matched.Add((eventType, found));
            searchStart = found + 1;
        }
    }

    private static void OptionalEqual<T>(
        ICollection<string> failures,
        string label,
        T? expected,
        T? actual)
        where T : struct
    {
        if (expected.HasValue &&
            (!actual.HasValue ||
             !EqualityComparer<T>.Default.Equals(expected.Value, actual.Value)))
        {
            failures.Add(
                $"{label} expected {expected.Value} but was " +
                $"{(actual.HasValue ? actual.Value.ToString() : "null")}.");
        }
    }

    private static void Equal<T>(
        ICollection<string> failures,
        string label,
        T expected,
        object? actual)
    {
        if (actual is not T typed ||
            !EqualityComparer<T>.Default.Equals(expected, typed))
        {
            failures.Add($"{label} expected {expected} but was {actual?.ToString() ?? "null"}.");
        }
    }
}
