using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileInterceptionPhaseContextTests
{
    [Fact]
    public void FriendlyDefenseIgnoresFriendlyMissile()
    {
        MissileDefenseSystem defense = CreateDefense(
            "player-pd",
            TacticalSide.Player,
            new HexCoord(0, 0));
        GuidedMissileSalvo salvo = CreateSalvo("friendly", TacticalSide.Player);
        MissileInterceptionPhaseContext context = CreateContext(
            defense,
            MissileInterceptionOutcome.Intercepted);

        IReadOnlyList<MissileInterceptionAttemptResult> results =
            context.ResolveAt(salvo, new HexCoord(0, 1), MissileInterceptionOpportunity.TerminalEntry);

        Assert.Empty(results);
        Assert.Equal(GuidedMissileStatus.InFlight, salvo.Status);
    }

    [Fact]
    public void HostileMissileInsideEnvelopeCreatesAttempt()
    {
        MissileDefenseSystem defense = CreateDefense(
            "player-pd",
            TacticalSide.Player,
            new HexCoord(0, 0));
        GuidedMissileSalvo salvo = CreateSalvo("hostile", TacticalSide.Enemy);
        MissileInterceptionPhaseContext context = CreateContext(
            defense,
            MissileInterceptionOutcome.Missed);

        MissileInterceptionAttemptResult result = Assert.Single(
            context.ResolveAt(salvo, new HexCoord(0, 1), MissileInterceptionOpportunity.TerminalEntry));

        Assert.Equal("player-pd", result.DefenseSystemId);
        Assert.Equal(MissileInterceptionOutcome.Missed, result.Outcome);
        Assert.Equal(1, context.AttemptsUsed("player-pd"));
    }

    [Fact]
    public void MissileOutsideEnvelopeCreatesNoAttempt()
    {
        MissileDefenseSystem defense = CreateDefense(
            "player-pd",
            TacticalSide.Player,
            new HexCoord(0, 0));
        GuidedMissileSalvo salvo = CreateSalvo("hostile", TacticalSide.Enemy);
        MissileInterceptionPhaseContext context = CreateContext(
            defense,
            MissileInterceptionOutcome.Intercepted);

        Assert.Empty(context.ResolveAt(salvo, new HexCoord(0, 3), MissileInterceptionOpportunity.TerminalEntry));
        Assert.Equal(0, context.AttemptsUsed("player-pd"));
    }

    [Fact]
    public void AttemptBudgetIsSharedAcrossDifferentSalvos()
    {
        MissileDefenseSystem defense = CreateDefense(
            "player-pd",
            TacticalSide.Player,
            new HexCoord(0, 0),
            attempts: 1);
        MissileInterceptionPhaseContext context = CreateContext(
            defense,
            MissileInterceptionOutcome.Missed);

        Assert.Single(context.ResolveAt(
            CreateSalvo("hostile-1", TacticalSide.Enemy),
            new HexCoord(0, 1),
            MissileInterceptionOpportunity.TerminalEntry));
        Assert.Empty(context.ResolveAt(
            CreateSalvo("hostile-2", TacticalSide.Enemy),
            new HexCoord(1, 0),
            MissileInterceptionOpportunity.TerminalEntry));
    }

    [Fact]
    public void LowerPriorityValueAttemptsFirst()
    {
        MissileDefenseSystem later = CreateDefense(
            "later",
            TacticalSide.Player,
            new HexCoord(0, 0),
            priority: 5);
        MissileDefenseSystem earlier = CreateDefense(
            "earlier",
            TacticalSide.Player,
            new HexCoord(0, 0),
            priority: 1);
        var resolver = new RecordingResolver(MissileInterceptionOutcome.Missed);
        var context = new MissileInterceptionPhaseContext(
            new[] { later, earlier },
            resolver);

        context.ResolveAt(
            CreateSalvo("hostile", TacticalSide.Enemy),
            new HexCoord(0, 1),
            MissileInterceptionOpportunity.TerminalEntry);

        Assert.Equal(new[] { "earlier" }, resolver.DefenseSystemIds);
    }

    [Fact]
    public void SuccessfulInterceptionStopsLaterDefenseSystems()
    {
        MissileDefenseSystem first = CreateDefense(
            "first",
            TacticalSide.Player,
            new HexCoord(0, 0),
            priority: 0);
        MissileDefenseSystem second = CreateDefense(
            "second",
            TacticalSide.Player,
            new HexCoord(0, 0),
            priority: 1);
        GuidedMissileSalvo salvo = CreateSalvo("hostile", TacticalSide.Enemy);
        var context = new MissileInterceptionPhaseContext(
            new[] { first, second },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Intercepted));

        IReadOnlyList<MissileInterceptionAttemptResult> results =
            context.ResolveAt(salvo, new HexCoord(0, 1), MissileInterceptionOpportunity.TerminalEntry);

        Assert.Single(results);
        Assert.Equal(GuidedMissileStatus.Intercepted, salvo.Status);
        Assert.Equal("first", salvo.InterceptedByDefenseSystemId);
        Assert.Equal(0, context.AttemptsUsed("second"));
    }

    [Fact]
    public void OnePdsAttemptIsAllowedPerDefenderPerTerminalWindow()
    {
        MissileDefenseSystem first = CreateDefense(
            "first",
            TacticalSide.Player,
            new HexCoord(0, 0),
            priority: 0);
        MissileDefenseSystem second = CreateDefense(
            "second",
            TacticalSide.Player,
            new HexCoord(0, 0),
            priority: 1);
        var context = new MissileInterceptionPhaseContext(
            new[] { first, second },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Missed));

        IReadOnlyList<MissileInterceptionAttemptResult> results =
            context.ResolveAt(
                CreateSalvo("hostile", TacticalSide.Enemy),
                new HexCoord(0, 1),
                MissileInterceptionOpportunity.TerminalEntry);

        MissileInterceptionAttemptResult result = Assert.Single(results);
        Assert.Equal("first", result.DefenseSystemId);
        Assert.Equal(0, context.AttemptsUsed("second"));
    }

    [Fact]
    public void PdsCanSpendTwoAttemptsAcrossTheTwoTerminalWindows()
    {
        MissileDefenseSystem defense = CreateDefense(
            "player-pd",
            TacticalSide.Player,
            new HexCoord(0, 0),
            attempts: 2);
        MissileInterceptionPhaseContext context = CreateContext(
            defense,
            MissileInterceptionOutcome.Missed);
        GuidedMissileSalvo salvo = CreateSalvo("hostile", TacticalSide.Enemy);

        Assert.Single(context.ResolveAt(
            salvo,
            new HexCoord(0, 1),
            MissileInterceptionOpportunity.TerminalEntry));
        Assert.Single(context.ResolveAt(
            salvo,
            new HexCoord(0, 1),
            MissileInterceptionOpportunity.PreTerminalAttack));
        Assert.Empty(context.ResolveAt(
            salvo,
            new HexCoord(0, 1),
            MissileInterceptionOpportunity.PreTerminalAttack));
        Assert.Equal(2, context.AttemptsUsed("player-pd"));
    }

    [Fact]
    public void DuplicateDefenseSystemIdsAreRejected()
    {
        MissileDefenseSystem first = CreateDefense(
            "duplicate",
            TacticalSide.Player,
            new HexCoord(0, 0));
        MissileDefenseSystem second = CreateDefense(
            "duplicate",
            TacticalSide.Enemy,
            new HexCoord(2, 0));

        Assert.Throws<ArgumentException>(
            () => new MissileInterceptionPhaseContext(
                new[] { first, second },
                new FixedMissileInterceptionResolver(
                    MissileInterceptionOutcome.Missed)));
    }

    [Fact]
    public void DefenseSystemRequiresConcreteOwnership()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new MissileDefenseSystem(
                "pd",
                "ship",
                TacticalSide.Unspecified,
                new HexCoord(0, 0),
                new MissileDefenseProfile(1, 1, 1)));
    }

    private static MissileInterceptionPhaseContext CreateContext(
        MissileDefenseSystem defense,
        MissileInterceptionOutcome outcome) =>
        new(
            new[] { defense },
            new FixedMissileInterceptionResolver(outcome));

    private static MissileDefenseSystem CreateDefense(
        string id,
        TacticalSide side,
        HexCoord coordinate,
        int attempts = 1,
        int priority = 0) =>
        new(
            id,
            side == TacticalSide.Player ? "ship-player" : "ship-enemy",
            side,
            coordinate,
            new MissileDefenseProfile(2, 1, attempts),
            priority);

    private static GuidedMissileSalvo CreateSalvo(
        string id,
        TacticalSide side) =>
        new(
            id,
            side,
            side == TacticalSide.Player ? "ship-player" : "ship-enemy",
            side == TacticalSide.Player ? "ship-enemy" : "ship-player",
            new HexCoord(-2, 2),
            new MissileFlightProfile(2, 8, 2));

    private sealed class RecordingResolver : IMissileInterceptionResolver
    {
        private readonly MissileInterceptionOutcome _outcome;
        private readonly List<string> _defenseSystemIds = new();

        public RecordingResolver(MissileInterceptionOutcome outcome)
        {
            _outcome = outcome;
        }

        public IReadOnlyList<string> DefenseSystemIds => _defenseSystemIds;

        public MissileInterceptionOutcome Resolve(
            MissileInterceptionAttempt attempt)
        {
            _defenseSystemIds.Add(attempt.DefenseSystem.Id);
            return _outcome;
        }
    }
}
