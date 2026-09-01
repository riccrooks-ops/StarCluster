using System;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class GuidedMissileSalvoTests
{
    [Fact]
    public void ConstructorInitializesLifetimeStateAtTheLaunchCoordinate()
    {
        var launch = new HexCoord(-3, 3);
        var profile = new MissileFlightProfile(2, 9, 2);

        var salvo = new GuidedMissileSalvo(
            "salvo",
            "ship-launcher",
            "ship-target",
            launch,
            profile);

        Assert.Equal(launch, salvo.LaunchCoordinate);
        Assert.Equal(launch, salvo.CurrentCoordinate);
        Assert.Equal(0, salvo.DistanceTraveled);
        Assert.Equal(9, salvo.RemainingRange);
        Assert.Equal(GuidedMissileStatus.InFlight, salvo.Status);
        Assert.False(salvo.IsTerminal);
    }

    [Fact]
    public void BlankStableIdIsRejected()
    {
        Assert.Throws<ArgumentException>(
            () => new GuidedMissileSalvo(
                string.Empty,
                "launcher",
                "target",
                new HexCoord(0, 1),
                new MissileFlightProfile(1, 1, 1)));
    }

    [Fact]
    public void InterceptionMarksTheSalvoTerminal()
    {
        GuidedMissileSalvo salvo = CreateSalvo();

        salvo.MarkIntercepted();

        Assert.Equal(GuidedMissileStatus.Intercepted, salvo.Status);
        Assert.True(salvo.IsTerminal);
    }

    [Fact]
    public void LaterDestructionDoesNotReplaceAnExistingTerminalOutcome()
    {
        GuidedMissileSalvo salvo = CreateSalvo();
        salvo.MarkIntercepted();

        salvo.MarkDestroyed();

        Assert.Equal(GuidedMissileStatus.Intercepted, salvo.Status);
    }

    private static GuidedMissileSalvo CreateSalvo() =>
        new(
            "salvo",
            "launcher",
            "target",
            new HexCoord(-2, 2),
            new MissileFlightProfile(2, 6, 2));
}
