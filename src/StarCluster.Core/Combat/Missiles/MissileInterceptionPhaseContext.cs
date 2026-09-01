using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Shared interception state for one Missile / Interception phase. Reaction
/// budgets remain spent across all Missile Flights. Standard PDS receives at
/// most one terminal-entry attempt and one pre-attack attempt against the same
/// flight during a terminal-defense window.
/// </summary>
public sealed class MissileInterceptionPhaseContext
{
    private readonly IReadOnlyList<MissileDefenseSystem> _defenseSystems;
    private readonly IMissileInterceptionResolver _resolver;
    private readonly SystemMap? _map;
    private readonly IMissileDefenseTrackProvider? _trackProvider;
    private readonly Dictionary<string, int> _attemptsUsed =
        new(StringComparer.Ordinal);
    private readonly Dictionary<(string DefenderShipId, string SalvoId), int>
        _pdsTerminalAttemptsUsed = new();
    private readonly HashSet<(
        string DefenseId,
        string SalvoId,
        HexCoord Coordinate,
        MissileInterceptionOpportunity Opportunity)> _resolvedOpportunities =
        new();
    private readonly HashSet<(
        string DefenderShipId,
        string SalvoId,
        MissileInterceptionOpportunity Opportunity)> _resolvedPdsWindows =
        new();

    public MissileInterceptionPhaseContext(
        IEnumerable<MissileDefenseSystem> defenseSystems,
        IMissileInterceptionResolver resolver,
        SystemMap? map = null,
        IMissileDefenseTrackProvider? trackProvider = null)
    {
        ArgumentNullException.ThrowIfNull(defenseSystems);
        _resolver = resolver ?? throw new ArgumentNullException(nameof(resolver));
        _map = map;
        _trackProvider = trackProvider;

        MissileDefenseSystem[] ordered = defenseSystems
            .Select(system => system ?? throw new ArgumentException(
                "Defense-system collections cannot contain null entries.",
                nameof(defenseSystems)))
            .OrderBy(system => system.Priority)
            .ThenBy(system => system.Id, StringComparer.Ordinal)
            .ToArray();

        string? duplicateId = ordered
            .GroupBy(system => system.Id, StringComparer.Ordinal)
            .FirstOrDefault(group => group.Count() > 1)
            ?.Key;

        if (duplicateId is not null)
        {
            throw new ArgumentException(
                $"Duplicate missile-defense system ID '{duplicateId}'.",
                nameof(defenseSystems));
        }

        if (_map is null && ordered.Any(system => system.RequiresLineOfSight))
        {
            throw new ArgumentException(
                "A SystemMap is required when any defense system requires line of sight.",
                nameof(map));
        }

        _defenseSystems = Array.AsReadOnly(ordered);
    }

    public IReadOnlyList<MissileDefenseSystem> DefenseSystems =>
        _defenseSystems;

    public int AttemptsUsed(string defenseSystemId)
    {
        if (string.IsNullOrWhiteSpace(defenseSystemId))
        {
            throw new ArgumentException(
                "A stable non-empty defense-system ID is required.",
                nameof(defenseSystemId));
        }

        return _attemptsUsed.TryGetValue(defenseSystemId, out int used)
            ? used
            : 0;
    }

    /// <summary>
    /// Compatibility overload. A true final-approach flag maps to terminal entry;
    /// new terminal code should use the explicit opportunity overload.
    /// </summary>
    public IReadOnlyList<MissileInterceptionAttemptResult> ResolveAt(
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate,
        bool isFinalApproach) => ResolveAt(
            salvo,
            missileCoordinate,
            isFinalApproach
                ? MissileInterceptionOpportunity.TerminalEntry
                : MissileInterceptionOpportunity.Transit);

    public IReadOnlyList<MissileInterceptionAttemptResult> ResolveAt(
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate,
        MissileInterceptionOpportunity opportunity)
    {
        ArgumentNullException.ThrowIfNull(salvo);
        if (!Enum.IsDefined(opportunity))
        {
            throw new ArgumentOutOfRangeException(nameof(opportunity));
        }

        if (salvo.IsTerminal)
        {
            return Array.Empty<MissileInterceptionAttemptResult>();
        }

        var results = new List<MissileInterceptionAttemptResult>();

        foreach (MissileDefenseSystem defenseSystem in _defenseSystems)
        {
            if (!OpportunityAllowsSystem(defenseSystem, opportunity) ||
                !defenseSystem.CanEngage(salvo, missileCoordinate) ||
                !HasRequiredLineOfSight(defenseSystem, missileCoordinate) ||
                !HasRequiredTacticalTrack(
                    defenseSystem,
                    salvo,
                    missileCoordinate))
            {
                continue;
            }

            var opportunityKey = (
                defenseSystem.Id,
                salvo.Id,
                missileCoordinate,
                opportunity);
            if (_resolvedOpportunities.Contains(opportunityKey))
            {
                continue;
            }

            bool isPointDefense = defenseSystem.SourceType ==
                MissileDefenseSourceType.PointDefenseSystem;
            bool isTerminalPdsWindow =
                isPointDefense && IsTerminalWindow(opportunity);
            var pdsWindowKey = (
                defenseSystem.DefenderShipId,
                salvo.Id,
                opportunity);
            if (isTerminalPdsWindow &&
                _resolvedPdsWindows.Contains(pdsWindowKey))
            {
                continue;
            }

            int used = AttemptsUsed(defenseSystem.Id);
            if (used >= defenseSystem.Profile.MaximumAttemptsPerPhase)
            {
                continue;
            }

            if (isTerminalPdsWindow)
            {
                var terminalKey = (
                    defenseSystem.DefenderShipId,
                    salvo.Id);
                int terminalUsed = _pdsTerminalAttemptsUsed.TryGetValue(
                    terminalKey,
                    out int terminalCount)
                    ? terminalCount
                    : 0;
                if (terminalUsed >= 2)
                {
                    continue;
                }

                _pdsTerminalAttemptsUsed[terminalKey] = terminalUsed + 1;
            }

            _resolvedOpportunities.Add(opportunityKey);
            if (isTerminalPdsWindow)
            {
                _resolvedPdsWindows.Add(pdsWindowKey);
            }
            int attemptNumber = used + 1;
            _attemptsUsed[defenseSystem.Id] = attemptNumber;

            var attempt = new MissileInterceptionAttempt(
                defenseSystem,
                salvo,
                missileCoordinate,
                attemptNumber,
                opportunity);
            MissileInterceptionOutcome outcome = _resolver.Resolve(attempt);

            if (!Enum.IsDefined(outcome))
            {
                throw new InvalidOperationException(
                    $"The interception resolver returned invalid outcome '{outcome}'.");
            }

            var result = new MissileInterceptionAttemptResult(attempt, outcome);
            results.Add(result);

            if (result.Intercepted)
            {
                salvo.MarkIntercepted(defenseSystem.Id);
                break;
            }
        }

        return Array.AsReadOnly(results.ToArray());
    }

    private static bool OpportunityAllowsSystem(
        MissileDefenseSystem defenseSystem,
        MissileInterceptionOpportunity opportunity)
    {
        if (defenseSystem.SourceType ==
            MissileDefenseSourceType.HeldDirectFireWeapon)
        {
            // Held direct-fire weapons are deliberate long-range interceptors.
            // They may engage a moving or stationary Missile Flight, but they
            // do not participate in either automatic terminal-defense window.
            return opportunity is
                MissileInterceptionOpportunity.Transit or
                MissileInterceptionOpportunity.Stationary;
        }

        // Standard PDS is terminal defense. Its two possible reactions are
        // when the hostile Flight enters the defended ship's hex and, after a
        // Firm terminal solution exists, immediately before the attack roll.
        // Held direct-fire weapons remain the ordinary transit interceptor.
        return opportunity is
            MissileInterceptionOpportunity.TerminalEntry or
            MissileInterceptionOpportunity.PreTerminalAttack;
    }

    private static bool IsTerminalWindow(
        MissileInterceptionOpportunity opportunity) => opportunity is
        MissileInterceptionOpportunity.TerminalEntry or
        MissileInterceptionOpportunity.PreTerminalAttack;

    private bool HasRequiredTacticalTrack(
        MissileDefenseSystem defenseSystem,
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate)
    {
        if (!defenseSystem.RequiresFirmTacticalTrack)
        {
            return true;
        }

        return _trackProvider?.HasUsableTrack(
            defenseSystem,
            salvo,
            missileCoordinate) ?? true;
    }

    private bool HasRequiredLineOfSight(
        MissileDefenseSystem defenseSystem,
        HexCoord missileCoordinate)
    {
        if (!defenseSystem.RequiresLineOfSight ||
            defenseSystem.Coordinate == missileCoordinate)
        {
            return true;
        }

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            _map!,
            defenseSystem.Coordinate,
            missileCoordinate);
        return result.Quality != LineOfSightQuality.Blocked;
    }
}
