using System.Text.Json;

namespace StarCluster.ScenarioRunner.TL1;

public static class Tl1ScenarioOutputWriter
{
    public static void Write(
        Tl1ScenarioRunResult result,
        Tl1BaselineCatalog baseline,
        string outputDirectory)
    {
        ArgumentNullException.ThrowIfNull(result);
        ArgumentNullException.ThrowIfNull(baseline);
        string scenarioDirectory = Path.Combine(
            outputDirectory,
            Sanitize(result.Document.Id));
        Directory.CreateDirectory(scenarioDirectory);

        object summary = new
        {
            schemaVersion = result.Document.SchemaVersion,
            scenarioId = result.Document.Id,
            matrixScenarioId = result.Document.MatrixScenarioId,
            name = result.Document.Name,
            baselineVersion = result.Document.BaselineVersion,
            declaredBaselineSha256 = result.Document.BaselineSha256,
            baselinePath = baseline.SourcePath,
            baselineSha256 = baseline.Sha256,
            passed = result.Passed,
            caseCount = result.Cases.Count,
            passedCases = result.Cases.Count(item => item.Passed),
            failedCases = result.Cases.Count(item => !item.Passed),
            failures = result.Failures,
            cases = result.Cases.Select(item => new
            {
                item.Id,
                item.Name,
                item.Operation,
                item.Passed,
                item.Failures,
            }).ToArray(),
        };
        File.WriteAllText(
            Path.Combine(scenarioDirectory, "summary.json"),
            JsonSerializer.Serialize(summary, Tl1ScenarioSerialization.WriteOptions) +
            Environment.NewLine);

        File.WriteAllText(
            Path.Combine(scenarioDirectory, "cases.json"),
            JsonSerializer.Serialize(result.Cases, Tl1ScenarioSerialization.WriteOptions) +
            Environment.NewLine);

        var lines = new List<string>();
        lines.Add(
            $"{(result.Passed ? "PASS" : "FAIL")} {result.Document.Id}: " +
            $"{result.Cases.Count(item => item.Passed)}/{result.Cases.Count} cases passed.");
        foreach (Tl1CaseRunResult testCase in result.Cases)
        {
            lines.Add(
                $"{(testCase.Passed ? "PASS" : "FAIL")} {testCase.Id} - {testCase.Name}");
            foreach (string eventText in testCase.Events)
            {
                lines.Add($"  EVENT {eventText}");
            }
            foreach (string failure in testCase.Failures)
            {
                lines.Add($"  FAILURE {failure}");
            }
        }
        File.WriteAllLines(
            Path.Combine(scenarioDirectory, "results.log"),
            lines);
    }

    public static void WriteRunnerError(
        string outputDirectory,
        string scenarioId,
        string message)
    {
        string scenarioDirectory = Path.Combine(
            outputDirectory,
            Sanitize(scenarioId));
        Directory.CreateDirectory(scenarioDirectory);
        File.WriteAllText(
            Path.Combine(scenarioDirectory, "runner-error.txt"),
            message + Environment.NewLine);
    }

    private static string Sanitize(string value)
    {
        char[] invalid = Path.GetInvalidFileNameChars();
        return new string(value.Select(character =>
            invalid.Contains(character) ? '_' : character).ToArray());
    }
}
