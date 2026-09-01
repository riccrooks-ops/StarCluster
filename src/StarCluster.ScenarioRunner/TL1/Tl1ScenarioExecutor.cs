using System.Text.Json;

namespace StarCluster.ScenarioRunner.TL1;

public sealed class Tl1ScenarioExecutor
{
    private readonly Tl1BaselineCatalog _baseline;
    private readonly Tl1MechanicsOperationExecutor _operations;

    public Tl1ScenarioExecutor(Tl1BaselineCatalog baseline)
    {
        ArgumentNullException.ThrowIfNull(baseline);
        _baseline = baseline;
        _operations = new Tl1MechanicsOperationExecutor(baseline);
    }

    public Tl1ScenarioRunResult Execute(
        Tl1MechanicsScenarioDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);
        var results = new List<Tl1CaseRunResult>();
        foreach (Tl1MechanicsCaseDocument testCase in document.Cases)
        {
            try
            {
                JsonElement resolvedInput =
                    Tl1ScenarioValueResolver.ResolveInput(
                        testCase.Input,
                        _baseline);
                Tl1OperationExecution execution = _operations.Execute(
                    testCase.Operation,
                    resolvedInput);
                JsonElement resolvedExpected =
                    Tl1ScenarioValueResolver.ResolveExpected(
                        testCase.Expected,
                        _baseline,
                        resolvedInput,
                        execution.Actual);
                IReadOnlyList<string> failures =
                    Tl1ExpectedSubsetComparer.Compare(
                        resolvedExpected,
                        execution.Actual);
                results.Add(new Tl1CaseRunResult(
                    testCase.Id,
                    testCase.Name,
                    testCase.Operation,
                    failures.Count == 0,
                    failures,
                    execution.Actual,
                    execution.Events));
            }
            catch (Exception exception)
            {
                results.Add(new Tl1CaseRunResult(
                    testCase.Id,
                    testCase.Name,
                    testCase.Operation,
                    false,
                    new[] { $"Operation threw {exception.GetType().Name}: {exception.Message}" },
                    Tl1ScenarioSerialization.ToElement(new
                    {
                        exception = exception.GetType().Name,
                        message = exception.Message,
                    }),
                    Array.Empty<string>()));
            }
        }
        return new Tl1ScenarioRunResult(document, results.AsReadOnly());
    }
}
