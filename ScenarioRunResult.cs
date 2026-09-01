using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

public sealed class ScenarioRunResult
{
    public ScenarioRunResult(
        ScenarioDocument document,
        ScenarioInitializationResult runtime,
        IReadOnlyList<MissileInterceptionOpportunity> interceptionOpportunities,
        IReadOnlyList<MissileInterceptionAttemptResult> interceptionAttempts,
        IReadOnlyList<ScenarioTerminalOpportunity> terminalOpportunities,
        IReadOnlyList<string> failures,
        ScenarioExecutionMetrics? executionMetrics = null)
    {
        Document = document;
        Runtime = runtime;
        InterceptionOpportunities = interceptionOpportunities;
        InterceptionAttempts = interceptionAttempts;
        TerminalOpportunities = terminalOpportunities;
        Failures = failures;
        ExecutionMetrics = executionMetrics;
    }

    public ScenarioDocument Document { get; }

    public ScenarioInitializationResult Runtime { get; }

    public IReadOnlyList<MissileInterceptionOpportunity> InterceptionOpportunities { get; }

    public IReadOnlyList<MissileInterceptionAttemptResult> InterceptionAttempts { get; }

    public IReadOnlyList<ScenarioTerminalOpportunity> TerminalOpportunities { get; }

    public IReadOnlyList<string> Failures { get; }

    public ScenarioExecutionMetrics? ExecutionMetrics { get; }

    public bool Passed => Failures.Count == 0;
}
