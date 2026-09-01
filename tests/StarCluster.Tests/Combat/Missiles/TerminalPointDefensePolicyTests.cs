using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class TerminalPointDefensePolicyTests
{
    [Fact]
    public void StandardPointDefenseIgnoresTransitAndStationaryOpportunities()
    {
        MissileInterceptionPhaseContext context = CreateContext(
            MissileInterceptionOutcome.Missed,
            MissileInterceptionOutcome.Missed);
        GuidedMissileSalvo salvo = CreateSalvo();

        Assert.Empty(context.ResolveAt(
            salvo,
            new HexCoord(1, 2),
            MissileInterceptionOpportunity.Transit));
        Assert.Empty(context.ResolveAt(
            salvo,
            new HexCoord(0, 2),
            MissileInterceptionOpportunity.Stationary));
        Assert.Equal(0, context.AttemptsUsed("pds"));
    }

    [Fact]
    public void StandardPointDefenseReceivesEntryAndPreAttackWindows()
    {
        MissileInterceptionPhaseContext context = CreateContext(
            MissileInterceptionOutcome.Missed,
            MissileInterceptionOutcome.Missed);
        GuidedMissileSalvo salvo = CreateSalvo();

        MissileInterceptionAttemptResult entry = Assert.Single(context.ResolveAt(
            salvo,
            new HexCoord(0, 2),
            MissileInterceptionOpportunity.TerminalEntry));
        MissileInterceptionAttemptResult preAttack = Assert.Single(context.ResolveAt(
            salvo,
            new HexCoord(0, 2),
            MissileInterceptionOpportunity.PreTerminalAttack));

        Assert.Equal(MissileInterceptionOpportunity.TerminalEntry, entry.Opportunity);
        Assert.Equal(MissileInterceptionOpportunity.PreTerminalAttack, preAttack.Opportunity);
        Assert.Equal(2, context.AttemptsUsed("pds"));
    }

    [Fact]
    public void QueuedResolverConsumesOutcomesAndRepeatsFinalValue()
    {
        var resolver = new QueuedMissileInterceptionResolver(
            MissileInterceptionOutcome.Missed,
            MissileInterceptionOutcome.Intercepted);
        MissileInterceptionPhaseContext first = CreateContext(resolver);
        GuidedMissileSalvo salvoOne = CreateSalvo("one");
        GuidedMissileSalvo salvoTwo = CreateSalvo("two");
        GuidedMissileSalvo salvoThree = CreateSalvo("three");

        Assert.Equal(
            MissileInterceptionOutcome.Missed,
            Assert.Single(first.ResolveAt(
                salvoOne,
                new HexCoord(0, 2),
                MissileInterceptionOpportunity.TerminalEntry)).Outcome);

        MissileInterceptionPhaseContext second = CreateContext(resolver);
        Assert.Equal(
            MissileInterceptionOutcome.Intercepted,
            Assert.Single(second.ResolveAt(
                salvoTwo,
                new HexCoord(0, 2),
                MissileInterceptionOpportunity.TerminalEntry)).Outcome);

        MissileInterceptionPhaseContext third = CreateContext(resolver);
        Assert.Equal(
            MissileInterceptionOutcome.Intercepted,
            Assert.Single(third.ResolveAt(
                salvoThree,
                new HexCoord(0, 2),
                MissileInterceptionOpportunity.TerminalEntry)).Outcome);
        Assert.Equal(3, resolver.OutcomesConsumed);
    }

    private static MissileInterceptionPhaseContext CreateContext(
        params MissileInterceptionOutcome[] outcomes) =>
        CreateContext(new QueuedMissileInterceptionResolver(outcomes));

    private static MissileInterceptionPhaseContext CreateContext(
        IMissileInterceptionResolver resolver) => new(
        new[]
        {
            new MissileDefenseSystem(
                "pds",
                "ship-player",
                TacticalSide.Player,
                new HexCoord(0, 2),
                new MissileDefenseProfile(2, 1, 2)),
        },
        resolver);

    private static GuidedMissileSalvo CreateSalvo(string id = "hostile") => new(
        id,
        TacticalSide.Enemy,
        "ship-enemy",
        "ship-player",
        new HexCoord(1, 2),
        new MissileFlightProfile(2, 5, 1));
}
