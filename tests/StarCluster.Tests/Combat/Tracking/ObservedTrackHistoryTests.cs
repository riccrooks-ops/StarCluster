using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class ObservedTrackHistoryTests
{
    [Fact]
    public void FirstDetectedObservationStartsObservedHistory()
    {
        var repository = new TacticalTrackRepository();
        var coordinate = new HexCoord(1, -1);

        ApplyFirm(repository, coordinate, sequence: 1);

        TacticalTrackRecord record = repository.Get("player", "hostile-1")!;
        Assert.Equal(new[] { coordinate }, record.ObservedCoordinateHistory.ToArray());
    }

    [Fact]
    public void RepeatedObservationAtSameCoordinateDoesNotDuplicateHistory()
    {
        var repository = new TacticalTrackRepository();
        var coordinate = new HexCoord(1, -1);
        ApplyFirm(repository, coordinate, sequence: 1);

        ApplyFirm(repository, coordinate, sequence: 2);

        Assert.Single(repository.Get("player", "hostile-1")!.ObservedCoordinateHistory);
    }

    [Fact]
    public void ChangedDetectedCoordinateExtendsObservedHistory()
    {
        var repository = new TacticalTrackRepository();
        var first = new HexCoord(1, -1);
        var second = new HexCoord(2, -1);
        ApplyFirm(repository, first, sequence: 1);

        ApplyFirm(repository, second, sequence: 2);

        Assert.Equal(
            new[] { first, second },
            repository.Get("player", "hostile-1")!
                .ObservedCoordinateHistory
                .ToArray());
    }

    [Fact]
    public void HostileMissileContactExposesObservedTrailWithoutAuthoritativeRoute()
    {
        var repository = new TacticalTrackRepository();
        var first = new HexCoord(1, -1);
        var second = new HexCoord(2, -1);
        ApplyFirm(repository, first, sequence: 1);
        ApplyFirm(repository, second, sequence: 2);
        var salvo = new GuidedMissileSalvo(
            "hostile-1",
            TacticalSide.Enemy,
            "enemy",
            "player",
            new HexCoord(4, -2),
            new MissileFlightProfile(
                technologyLevel: 2,
                maximumRange: 10,
                speedHexesPerTurn: 2));

        TacticalMissileContact contact = Assert.Single(
            TacticalMissileKnowledgeService.Build(
                new[] { salvo },
                repository,
                "player",
                TacticalSide.Player));

        Assert.Equal(new[] { first, second }, contact.VisibleTravelHistory.ToArray());
        Assert.Null(contact.VisibleLastExecutedRoute);
        Assert.NotEqual(salvo.CurrentCoordinate, contact.Coordinate);
    }

    private static void ApplyFirm(
        TacticalTrackRepository repository,
        HexCoord coordinate,
        long sequence)
    {
        TacticalTrackUpdateService.Apply(
            repository,
            "player",
            TacticalTrackObservation.Firm(
                "hostile-1",
                coordinate,
                TacticalTrackSourceType.TacticalSensors),
            new ComputingProfile(
                technologyLevel: 2,
                staleRetentionUpdates: 2,
                uncertaintyGrowthPerMissedUpdate: 1),
            sequence,
            TrackUpdateTrigger.MissileMovementCompleted);
    }
}
