using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

public enum ScenarioActionKind
{
    MoveShip,
    AdvanceMissile,
    AdvancePhase,
}

/// <summary>
/// Immutable materialization shared by all Monte Carlo trials for one variant.
/// The authoritative runtime state is still recreated for every trial; only
/// document parsing, initialization-request construction, defense parsing, and
/// action-kind parsing are reused.
/// </summary>
public sealed class ScenarioExecutionPlan
{
    private sealed class PreparedDefense
    {
        public required string Id { get; init; }
        public required string DefenderShipId { get; init; }
        public required TacticalSide Side { get; init; }
        public required MissileDefenseProfile Profile { get; init; }
        public required int Priority { get; init; }
        public required MissileDefenseSourceType SourceType { get; init; }
        public required bool RequiresLineOfSight { get; init; }
        public required bool RequiresFirmTrack { get; init; }

        public MissileDefenseSystem Materialize(ScenarioInitializationResult runtime)
        {
            if (!runtime.Ships.TryGetValue(
                    DefenderShipId,
                    out ScenarioShipState? ship))
            {
                throw new InvalidOperationException(
                    $"Defense '{Id}' references unknown ship '{DefenderShipId}'.");
            }

            return new MissileDefenseSystem(
                Id,
                DefenderShipId,
                Side,
                ship.Coordinate,
                Profile,
                Priority,
                SourceType,
                targetMissileSalvoId: null,
                requiresLineOfSight: RequiresLineOfSight,
                requiresFirmTacticalTrack: RequiresFirmTrack);
        }
    }

    private readonly PreparedDefense[] _defenses;

    private ScenarioExecutionPlan(
        ScenarioDocument document,
        ScenarioInitializationRequest initializationRequest,
        ProbabilityMissileInterceptionProfile interceptionProfile,
        IReadOnlyList<ScenarioActionKind> actionKinds,
        PreparedDefense[] defenses)
    {
        Document = document;
        InitializationRequest = initializationRequest;
        InterceptionProfile = interceptionProfile;
        ActionKinds = actionKinds;
        _defenses = defenses;
    }

    public ScenarioDocument Document { get; }

    public ScenarioInitializationRequest InitializationRequest { get; }

    public ProbabilityMissileInterceptionProfile InterceptionProfile { get; }

    public IReadOnlyList<ScenarioActionKind> ActionKinds { get; }

    public IReadOnlyList<MissileDefenseSystem> CreateDefenses(
        ScenarioInitializationResult runtime)
    {
        ArgumentNullException.ThrowIfNull(runtime);
        var systems = new MissileDefenseSystem[_defenses.Length];
        for (int index = 0; index < _defenses.Length; index++)
        {
            systems[index] = _defenses[index].Materialize(runtime);
        }

        return systems;
    }

    public static ScenarioExecutionPlan Prepare(ScenarioDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);
        ScenarioActionKind[] actionKinds = document.Actions
            .Select(ParseActionKind)
            .ToArray();
        PreparedDefense[] defenses = document.Defenses
            .Select(PrepareDefense)
            .ToArray();
        return new ScenarioExecutionPlan(
            document,
            ScenarioDocumentMapper.ToInitializationRequest(document),
            new ProbabilityMissileInterceptionProfile(document.Defenses),
            Array.AsReadOnly(actionKinds),
            defenses);
    }

    private static PreparedDefense PrepareDefense(DefenseDocument defense)
    {
        ArgumentNullException.ThrowIfNull(defense);
        return new PreparedDefense
        {
            Id = Required(defense.Id, "defense ID"),
            DefenderShipId = Required(
                defense.DefenderShipId,
                "defender ship ID"),
            Side = ScenarioDocumentMapper.ParseEnum<TacticalSide>(
                defense.Side,
                "defense side"),
            Profile = new MissileDefenseProfile(
                defense.TechnologyLevel,
                defense.Range,
                defense.MaximumAttemptsPerPhase),
            Priority = defense.Priority,
            SourceType = ScenarioDocumentMapper.ParseEnum<MissileDefenseSourceType>(
                defense.SourceType,
                "defense source type"),
            RequiresLineOfSight = defense.RequiresLineOfSight,
            RequiresFirmTrack = defense.RequiresFirmTrack,
        };
    }

    private static ScenarioActionKind ParseActionKind(ActionDocument action)
    {
        ArgumentNullException.ThrowIfNull(action);
        return action.Type.Trim().ToLowerInvariant() switch
        {
            "moveship" => ScenarioActionKind.MoveShip,
            "advancemissile" => ScenarioActionKind.AdvanceMissile,
            "advancephase" => ScenarioActionKind.AdvancePhase,
            _ => throw new InvalidOperationException(
                $"Unsupported scenario action type '{action.Type}'."),
        };
    }

    private static string Required(string value, string description)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"A {description} is required.");
        }

        return value;
    }
}
