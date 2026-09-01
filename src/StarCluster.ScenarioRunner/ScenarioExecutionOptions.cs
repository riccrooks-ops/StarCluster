using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public sealed class ScenarioExecutionOptions
{
    public IMissileInterceptionResolver? InterceptionResolver { get; init; }

    public IMissileTerminalRandomSource? TerminalRandomSource { get; init; }

    public bool EvaluateAssertions { get; init; } = true;

    public bool RecordCompletionEvent { get; init; } = true;

    /// <summary>
    /// Preserve the complete human-readable diagnostic journal. Deterministic
    /// validation and Godot hosts leave this enabled. High-volume Monte Carlo
    /// trials disable it and capture compact execution metrics instead.
    /// </summary>
    public bool RecordDiagnostics { get; init; } = true;

    public bool CaptureExecutionMetrics { get; init; }

    /// <summary>
    /// Optional allocation profiler used only by the Checkpoint 22b
    /// single-worker attribution corpus. Normal deterministic and Monte Carlo
    /// execution leaves this null.
    /// </summary>
    public ScenarioAllocationProfile? AllocationProfile { get; init; }
}
