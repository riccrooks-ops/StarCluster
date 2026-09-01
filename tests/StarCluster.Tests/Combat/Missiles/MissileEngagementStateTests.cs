using System;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileEngagementStateTests
{
    [Fact]
    public void AddedSalvoAppearsInActiveAndAllCollections()
    {
        var state = new MissileEngagementState();
        GuidedMissileSalvo salvo = CreateSalvo("friendly", TacticalSide.Player);

        state.Add(salvo);

        Assert.Same(salvo, Assert.Single(state.Salvos));
        Assert.Same(salvo, Assert.Single(state.ActiveSalvos));
        Assert.True(state.HasActiveSalvos);
    }

    [Fact]
    public void DuplicateSalvoIdIsRejected()
    {
        var state = new MissileEngagementState();
        state.Add(CreateSalvo("duplicate", TacticalSide.Player));

        Assert.Throws<ArgumentException>(
            () => state.Add(CreateSalvo("duplicate", TacticalSide.Enemy)));
    }

    [Fact]
    public void FriendlyAndHostileSalvosCanCoexist()
    {
        var state = new MissileEngagementState();
        state.Add(CreateSalvo("friendly", TacticalSide.Player));
        state.Add(CreateSalvo("hostile", TacticalSide.Enemy));

        Assert.Single(state.ForSide(TacticalSide.Player));
        Assert.Single(state.ForSide(TacticalSide.Enemy));
        Assert.Equal(2, state.Salvos.Count);
    }

    [Fact]
    public void TerminalSalvoIsRetainedButExcludedFromActiveQueries()
    {
        var state = new MissileEngagementState();
        GuidedMissileSalvo salvo = CreateSalvo("hostile", TacticalSide.Enemy);
        state.Add(salvo);
        salvo.MarkDestroyed();

        Assert.Single(state.Salvos);
        Assert.Empty(state.ActiveSalvos);
        Assert.False(state.HasActiveSalvos);
        Assert.Same(salvo, state.Find("hostile"));
    }

    [Fact]
    public void ClearRemovesEveryRetainedSalvo()
    {
        var state = new MissileEngagementState();
        state.Add(CreateSalvo("friendly", TacticalSide.Player));
        state.Add(CreateSalvo("hostile", TacticalSide.Enemy));

        state.Clear();

        Assert.Empty(state.Salvos);
        Assert.Empty(state.ActiveSalvos);
    }

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
}
