using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class MissileTerminalViewTests
{
    private readonly SystemMap _map = SystemMap.Create(
        5,
        MapObject.CreateStar("star-primary", "Primary Star"));

    [Fact]
    public void TerminalHostileSalvoIsOmittedFromActiveTacticalView()
    {
        GuidedMissileSalvo hostile = CreateSalvo("hostile-1", TacticalSide.Enemy);
        hostile.MarkDestroyed();
        TacticalTrackRepository repository = FirmTrack(hostile.Id);

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { hostile },
            repository,
            hostile.Id);

        Assert.Empty(view.Contacts);
        Assert.Empty(view.Projections);
        Assert.Null(view.SelectedSalvoId);
    }

    [Fact]
    public void MixedTerminalAndActiveSalvosKeepOnlyActiveContact()
    {
        GuidedMissileSalvo terminal = CreateSalvo("hostile-1", TacticalSide.Enemy);
        GuidedMissileSalvo active = CreateSalvo("hostile-2", TacticalSide.Enemy);
        terminal.MarkDestroyed();
        TacticalTrackRepository repository = FirmTrack(terminal.Id, active.Id);

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { terminal, active },
            repository,
            active.Id);

        TacticalMissileContact contact = Assert.Single(view.Contacts);
        Assert.Equal(active.Id, contact.SalvoId);
        Assert.Equal(active.Id, view.SelectedSalvoId);
    }

    [Fact]
    public void TerminalFriendlySalvoIsOmittedFromActiveTacticalView()
    {
        GuidedMissileSalvo friendly = CreateSalvo("friendly-1", TacticalSide.Player);
        friendly.MarkIntercepted("enemy-pds");

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { friendly },
            new TacticalTrackRepository(),
            friendly.Id);

        Assert.Empty(view.Contacts);
        Assert.Null(view.SelectedSalvoId);
    }

    [Fact]
    public void SelectionOfTerminalSalvoNormalizesToNoneWhileActivePeerRemains()
    {
        GuidedMissileSalvo terminal = CreateSalvo("hostile-1", TacticalSide.Enemy);
        GuidedMissileSalvo active = CreateSalvo("hostile-2", TacticalSide.Enemy);
        terminal.MarkDestroyed();
        TacticalTrackRepository repository = FirmTrack(terminal.Id, active.Id);

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { terminal, active },
            repository,
            terminal.Id);

        Assert.Single(view.Contacts);
        Assert.Null(view.SelectedSalvoId);
    }

    private ObserverSafeMissileViewSnapshot Build(
        GuidedMissileSalvo[] salvos,
        TacticalTrackRepository repository,
        string? requestedSelection) =>
        ObserverSafeMissileViewService.Build(
            _map,
            salvos,
            repository,
            "player",
            TacticalSide.Player,
            new HexCoord(0, 0),
            requestedSelection);

    private static TacticalTrackRepository FirmTrack(params string[] salvoIds)
    {
        var repository = new TacticalTrackRepository();
        long sequence = 1;
        foreach (string salvoId in salvoIds)
        {
            TacticalTrackUpdateService.Apply(
                repository,
                "player",
                TacticalTrackObservation.Firm(salvoId, new HexCoord(1, 0)),
                new ComputingProfile(3, 3, 1),
                sequence++,
                TrackUpdateTrigger.MissileMovementCompleted,
                observationEpoch: 1);
        }
        return repository;
    }

    private static GuidedMissileSalvo CreateSalvo(
        string id,
        TacticalSide side) =>
        new(
            id,
            side,
            side == TacticalSide.Player ? "player" : "enemy",
            side == TacticalSide.Player ? "enemy" : "player",
            new HexCoord(1, 0),
            new MissileFlightProfile(2, 10, 2));
}
