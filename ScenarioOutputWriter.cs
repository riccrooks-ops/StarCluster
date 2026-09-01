using System.Text.Json;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Diagnostics;

namespace StarCluster.ScenarioRunner;

public static class ScenarioOutputWriter
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true,
    };

    public static void Write(ScenarioRunResult result, string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(result);
        if (string.IsNullOrWhiteSpace(outputDirectory))
        {
            throw new ArgumentException("An output directory is required.", nameof(outputDirectory));
        }

        string scenarioDirectory = Path.Combine(outputDirectory, result.Document.Id);
        Directory.CreateDirectory(scenarioDirectory);

        File.WriteAllLines(
            Path.Combine(scenarioDirectory, "events.jsonl"),
            result.Runtime.Journal.Events.Select(DiagnosticEventJsonlFormatter.Format));
        File.WriteAllLines(
            Path.Combine(scenarioDirectory, "events.log"),
            result.Runtime.Journal.Events.Select(DiagnosticEventTextFormatter.Format));

        var summary = new
        {
            result.Document.SchemaVersion,
            ScenarioId = result.Document.Id,
            result.Document.Name,
            Passed = result.Passed,
            Failures = result.Failures,
            InterceptionOpportunities = result.InterceptionOpportunities
                .Select(item => item.ToString())
                .ToArray(),
            TerminalOpportunities = result.TerminalOpportunities
                .Select(item => new
                {
                    item.MissileId,
                    item.TargetId,
                    Coordinate = new { item.Coordinate.Q, item.Coordinate.R },
                    Source = item.Source.ToString(),
                    item.TurnNumber,
                })
                .ToArray(),
            Ships = result.Runtime.Ships.Values
                .OrderBy(ship => ship.Definition.Id, StringComparer.Ordinal)
                .Select(ship => new
                {
                    ship.Definition.Id,
                    ship.Definition.Name,
                    Side = ship.Definition.Side.ToString(),
                    Position = new { ship.Coordinate.Q, ship.Coordinate.R },
                })
                .ToArray(),
            Missiles = result.Runtime.MissileEngagement.Salvos.Select(salvo => new
            {
                salvo.Id,
                Status = salvo.Status.ToString(),
                TerminalState = salvo.TerminalState.ToString(),
                TerminalOutcome = salvo.LastTerminalResolution?.Outcome.ToString(),
                Position = new { salvo.CurrentCoordinate.Q, salvo.CurrentCoordinate.R },
                salvo.DistanceTraveled,
                salvo.StationarySearchFuelSpent,
                salvo.TotalFuelSpent,
                salvo.RemainingRange,
                AcquisitionRoll = salvo.LastTerminalResolution?.AcquisitionRoll,
                AttackRoll = salvo.LastTerminalResolution?.AttackRoll,
            }).ToArray(),
            EventCount = result.Runtime.Journal.Events.Count,
        };

        File.WriteAllText(
            Path.Combine(scenarioDirectory, "summary.json"),
            JsonSerializer.Serialize(summary, JsonOptions) + Environment.NewLine);
        string failuresPath = Path.Combine(scenarioDirectory, "failures.txt");
        if (!result.Passed)
        {
            File.WriteAllLines(failuresPath, result.Failures);
        }
        else if (File.Exists(failuresPath))
        {
            File.Delete(failuresPath);
        }

        string runnerErrorPath = Path.Combine(scenarioDirectory, "runner-error.txt");
        if (File.Exists(runnerErrorPath))
        {
            File.Delete(runnerErrorPath);
        }
    }
}
