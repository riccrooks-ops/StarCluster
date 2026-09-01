using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class ObserverSafeMissileViewTests
{
    private readonly SystemMap _map = SystemMap.Create(
        5,
        MapObject.CreateStar("star-primary", "Primary Star"));

    [Fact]
    public void UnknownHostileMissileCannotRenderOrRemainSelected()
    {
        GuidedMissileSalvo hostile = CreateSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            new HexCoord(2, 1));

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { hostile },
            new TacticalTrackRepository(),
            requestedSelection: hostile.Id);

        Assert.Empty(view.Contacts);
        Assert.Empty(view.Projections);
        Assert.Null(view.SelectedSalvoId);
    }

    [Fact]
    public void OwnMissileIsAlwaysVisibleAndSelectable()
    {
        GuidedMissileSalvo friendly = CreateSalvo(
            "friendly-1",
            TacticalSide.Player,
            new HexCoord(1, 1));

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { friendly },
            new TacticalTrackRepository(),
            requestedSelection: friendly.Id);

        Assert.Single(view.Contacts);
        Assert.Equal(friendly.Id, view.SelectedSalvoId);
    }

    [Fact]
    public void StaleHostileContactIsVisibleButExactRouteIsWithheld()
    {
        GuidedMissileSalvo hostile = CreateSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            new HexCoord(2, 1));
        var repository = new TacticalTrackRepository();
        repository.SeedPriorIntelligence(
            "player",
            hostile.Id,
            new HexCoord(2, 1),
            sequence: 1);

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { hostile },
            repository,
            requestedSelection: hostile.Id);

        Assert.Single(view.Contacts);
        MissileRouteProjection projection = Assert.Single(view.Projections);
        Assert.Equal(
            MissileRouteProjectionStatus.WithheldByObserverUncertainty,
            projection.Status);
        Assert.Null(projection.RoutePlan);
    }

    [Fact]
    public void ApproximateHostileContactDoesNotExposeExactRoute()
    {
        GuidedMissileSalvo hostile = CreateSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            new HexCoord(2, 1));
        var repository = new TacticalTrackRepository();
        ApplyTrack(
            repository,
            TacticalTrackObservation.Approximate(
                hostile.Id,
                new HexCoord(2, 1)));

        MissileRouteProjection projection = Assert.Single(Build(
            new[] { hostile },
            repository,
            requestedSelection: null).Projections);

        Assert.Equal(
            MissileRouteProjectionStatus.WithheldByObserverUncertainty,
            projection.Status);
    }

    [Fact]
    public void FirmHostileContactPermitsObserverSideThreatProjection()
    {
        GuidedMissileSalvo hostile = CreateSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            new HexCoord(2, 1));
        var repository = new TacticalTrackRepository();
        ApplyTrack(
            repository,
            TacticalTrackObservation.Firm(
                hostile.Id,
                new HexCoord(2, 1)));

        MissileRouteProjection projection = Assert.Single(Build(
            new[] { hostile },
            repository,
            requestedSelection: null).Projections);

        Assert.Equal(MissileRouteProjectionStatus.Available, projection.Status);
        Assert.True(projection.HasRoute);
        Assert.Equal(new HexCoord(0, 2), projection.GuidanceCoordinate!.Value);
    }

    [Fact]
    public void FriendlyProjectionUsesTheMissilesConsumedDatalinkReport()
    {
        var launchCoordinate = new HexCoord(-2, 2);
        var copiedGuidanceCoordinate = new HexCoord(2, 2);
        var newerObserverCoordinate = new HexCoord(3, 2);
        var friendly = new GuidedMissileSalvo(
            "friendly-1",
            TacticalSide.Player,
            "player",
            "enemy",
            launchCoordinate,
            new MissileFlightProfile(2, 10, 1));
        var datalinkProfile = new MissileDatalinkProfile(
            technologyLevel: 2,
            maximumRetainedReportAgePhases: 3);

        MissileDatalinkUpdateResult update =
            MissileDatalinkService.UpdateForGuidancePhase(
                _map,
                friendly,
                datalinkProfile,
                launchCoordinate,
                MissileTargetTrackSnapshot.Current(
                    "enemy",
                    copiedGuidanceCoordinate),
                sourceObservationEpoch: 1);
        _ = MissileGuidanceService.AdvanceOnePhase(
            _map,
            friendly,
            update.GuidanceSnapshot);

        var repository = new TacticalTrackRepository();
        ApplyTrack(
            repository,
            TacticalTrackObservation.Firm(
                "enemy",
                newerObserverCoordinate));

        MissileRouteProjection projection = Assert.Single(Build(
            new[] { friendly },
            repository,
            requestedSelection: friendly.Id).Projections);

        Assert.Equal(MissileRouteProjectionStatus.Available, projection.Status);
        Assert.Equal(copiedGuidanceCoordinate, projection.GuidanceCoordinate!.Value);
        Assert.NotEqual(newerObserverCoordinate, projection.GuidanceCoordinate.Value);
    }

    [Fact]
    public void InvalidSelectionFallsBackToNoSelectionWithoutChangingContacts()
    {
        GuidedMissileSalvo friendly = CreateSalvo(
            "friendly-1",
            TacticalSide.Player,
            new HexCoord(1, 1));

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { friendly },
            new TacticalTrackRepository(),
            requestedSelection: "hidden-or-removed");

        Assert.Single(view.Contacts);
        Assert.Null(view.SelectedSalvoId);
    }

    [Fact]
    public void HiddenHostileMissileCannotAffectVisibleStackCount()
    {
        GuidedMissileSalvo visible = CreateSalvo(
            "hostile-visible",
            TacticalSide.Enemy,
            new HexCoord(2, 1));
        GuidedMissileSalvo hidden = CreateSalvo(
            "hostile-hidden",
            TacticalSide.Enemy,
            new HexCoord(2, 1));
        var repository = new TacticalTrackRepository();
        ApplyTrack(
            repository,
            TacticalTrackObservation.Firm(
                visible.Id,
                new HexCoord(2, 1)));

        ObserverSafeMissileViewSnapshot view = Build(
            new[] { visible, hidden },
            repository,
            requestedSelection: null);
        TacticalMissileContactStack stack = Assert.Single(
            TacticalMissileStackService.Build(view.Contacts));

        Assert.Equal(1, stack.Count);
        Assert.Equal(visible.Id, Assert.Single(stack.Contacts).SalvoId);
    }

    [Fact]
    public void ViewConstructionDoesNotMutateAuthoritativeSalvoState()
    {
        GuidedMissileSalvo hostile = CreateSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            new HexCoord(2, 1));
        var repository = new TacticalTrackRepository();
        ApplyTrack(
            repository,
            TacticalTrackObservation.Firm(
                hostile.Id,
                new HexCoord(2, 1)));

        _ = Build(new[] { hostile }, repository, requestedSelection: null);

        Assert.Equal(0, hostile.DistanceTraveled);
        Assert.Equal(GuidedMissileStatus.InFlight, hostile.Status);
        Assert.Null(hostile.LastRoutePlan);
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
            new HexCoord(0, 2),
            requestedSelection);

    private static void ApplyTrack(
        TacticalTrackRepository repository,
        TacticalTrackObservation observation)
    {
        TacticalTrackUpdateService.Apply(
            repository,
            "player",
            observation,
            new ComputingProfile(3, 3, 1),
            sequence: 1,
            TrackUpdateTrigger.MissileMovementCompleted,
            observationEpoch: 1);
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
