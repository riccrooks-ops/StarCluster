using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class TacticalMissileStackTests
{
    [Fact]
    public void EmptyContactSetProducesNoStacks()
    {
        Assert.Empty(TacticalMissileStackService.Build(
            System.Array.Empty<TacticalMissileContact>()));
    }

    [Fact]
    public void CollocatedFriendlyMissilesProduceOneCountedStack()
    {
        TacticalMissileContact[] contacts = BuildContacts(
            CreateSalvo("friendly-2", TacticalSide.Player, new HexCoord(1, 0)),
            CreateSalvo("friendly-1", TacticalSide.Player, new HexCoord(1, 0)));

        TacticalMissileContactStack stack = Assert.Single(
            TacticalMissileStackService.Build(contacts));

        Assert.Equal(2, stack.Count);
        Assert.True(stack.IsStacked);
        Assert.Equal("F", stack.DisplaySymbol);
        Assert.Equal(new[] { "friendly-1", "friendly-2" },
            stack.Contacts.Select(contact => contact.SalvoId).ToArray());
    }

    [Fact]
    public void DifferentCoordinatesProduceSeparateStacks()
    {
        TacticalMissileContact[] contacts = BuildContacts(
            CreateSalvo("friendly-1", TacticalSide.Player, new HexCoord(1, 0)),
            CreateSalvo("friendly-2", TacticalSide.Player, new HexCoord(2, 0)));

        Assert.Equal(2, TacticalMissileStackService.Build(contacts).Count);
    }

    [Fact]
    public void FriendlyAndEnemyMissilesAtSameCoordinateRemainSeparateStacks()
    {
        GuidedMissileSalvo friendly = CreateSalvo(
            "friendly-1",
            TacticalSide.Player,
            new HexCoord(1, 0));
        GuidedMissileSalvo enemy = CreateSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            new HexCoord(1, 0));
        TacticalMissileContact[] contacts = BuildPlayerVisibleContacts(
            friendly,
            enemy);

        TacticalMissileContactStack[] stacks =
            TacticalMissileStackService.Build(contacts).ToArray();

        Assert.Equal(2, stacks.Length);
        Assert.Contains(stacks, stack => stack.OwnerSide == TacticalSide.Player);
        Assert.Contains(stacks, stack => stack.OwnerSide == TacticalSide.Enemy);
    }

    [Fact]
    public void StackPreservesEverySalvoIdentity()
    {
        TacticalMissileContact[] contacts = BuildContacts(
            CreateSalvo("friendly-1", TacticalSide.Player, new HexCoord(1, 0)),
            CreateSalvo("friendly-2", TacticalSide.Player, new HexCoord(1, 0)),
            CreateSalvo("friendly-3", TacticalSide.Player, new HexCoord(1, 0)));

        TacticalMissileContactStack stack = Assert.Single(
            TacticalMissileStackService.Build(contacts));

        Assert.Equal(3, stack.Contacts.Select(contact => contact.SalvoId).Distinct().Count());
    }

    [Fact]
    public void SingleContactStackIsNotMarkedStacked()
    {
        TacticalMissileContact contact = Assert.Single(BuildContacts(
            CreateSalvo("friendly-1", TacticalSide.Player, new HexCoord(1, 0))));

        TacticalMissileContactStack stack = Assert.Single(
            TacticalMissileStackService.Build(new[] { contact }));

        Assert.False(stack.IsStacked);
        Assert.Equal(1, stack.Count);
    }

    private static TacticalMissileContact[] BuildContacts(
        params GuidedMissileSalvo[] salvos) =>
        TacticalMissileKnowledgeService.Build(
            salvos,
            new TacticalTrackRepository(),
            "player",
            TacticalSide.Player).ToArray();

    private static TacticalMissileContact[] BuildPlayerVisibleContacts(
        GuidedMissileSalvo friendly,
        GuidedMissileSalvo enemy)
    {
        var repository = new TacticalTrackRepository();
        TacticalTrackUpdateService.Apply(
            repository,
            "player",
            TacticalTrackObservation.Firm(enemy.Id, enemy.CurrentCoordinate),
            new ComputingProfile(3, 2, 1),
            sequence: 1,
            TrackUpdateTrigger.MissileMovementCompleted,
            observationEpoch: 1);
        return TacticalMissileKnowledgeService.Build(
            new[] { friendly, enemy },
            repository,
            "player",
            TacticalSide.Player).ToArray();
    }

    private static GuidedMissileSalvo CreateSalvo(
        string id,
        TacticalSide side,
        HexCoord coordinate) =>
        new(
            id,
            side,
            side == TacticalSide.Player ? "player" : "enemy",
            side == TacticalSide.Player ? "enemy" : "player",
            coordinate,
            new MissileFlightProfile(2, 10, 2));
}
