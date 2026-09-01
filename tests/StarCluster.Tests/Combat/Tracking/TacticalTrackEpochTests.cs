using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class TacticalTrackEpochTests
{
    private readonly ComputingProfile _computing = new(3, 2, 1);

    [Fact]
    public void RepeatedMissesInOneEpochAdvanceAgeOnlyOnce()
    {
        var repository = CreateFirmRepository(epoch: 1);

        TacticalTrackUpdateResult first = Miss(repository, sequence: 2, epoch: 2);
        TacticalTrackUpdateResult second = Miss(repository, sequence: 3, epoch: 2);
        TacticalTrackUpdateResult third = Miss(repository, sequence: 4, epoch: 2);

        Assert.True(first.AgeAdvanced);
        Assert.False(second.AgeAdvanced);
        Assert.False(third.AgeAdvanced);
        Assert.Equal(1, third.Record!.MissedUpdateCount);
        Assert.Equal(1, third.Record.UncertaintyRadiusHexes);
    }

    [Fact]
    public void DifferentEventTriggersInOneTurnDoNotAgeTrackRepeatedly()
    {
        var repository = CreateFirmRepository(epoch: 1);

        TacticalTrackUpdateResult movement = Apply(
            repository,
            TacticalTrackObservation.Missed("target"),
            sequence: 2,
            epoch: 2,
            TrackUpdateTrigger.ShipMovementCommitted);
        TacticalTrackUpdateResult launch = Apply(
            repository,
            TacticalTrackObservation.Missed("target"),
            sequence: 3,
            epoch: 2,
            TrackUpdateTrigger.MissileLaunched);
        TacticalTrackUpdateResult missileMove = Apply(
            repository,
            TacticalTrackObservation.Missed("target"),
            sequence: 4,
            epoch: 2,
            TrackUpdateTrigger.MissileMovementCompleted);

        Assert.True(movement.AgeAdvanced);
        Assert.False(launch.AgeAdvanced);
        Assert.False(missileMove.AgeAdvanced);
        Assert.Equal(1, missileMove.Record!.MissedUpdateCount);
    }

    [Fact]
    public void NewTurnPermitsOneAdditionalAgeStep()
    {
        var repository = CreateFirmRepository(epoch: 1);
        Miss(repository, sequence: 2, epoch: 2);

        TacticalTrackUpdateResult result = Miss(
            repository,
            sequence: 3,
            epoch: 3);

        Assert.True(result.AgeAdvanced);
        Assert.Equal(2, result.Record!.MissedUpdateCount);
        Assert.Equal(2, result.Record.UncertaintyRadiusHexes);
    }

    [Fact]
    public void SameEpochVisibilityLossBecomesStaleWithoutAdvancingAge()
    {
        var repository = CreateFirmRepository(epoch: 1);
        TacticalTrackUpdateResult observed = Apply(
            repository,
            TacticalTrackObservation.Firm("target", new HexCoord(3, 0)),
            sequence: 2,
            epoch: 2,
            TrackUpdateTrigger.ShipMovementCommitted);
        TacticalTrackUpdateResult missed = Miss(
            repository,
            sequence: 3,
            epoch: 2);

        Assert.False(missed.AgeAdvanced);
        Assert.Equal(TacticalTrackQuality.Stale, missed.CurrentQuality);
        Assert.Equal(new HexCoord(3, 0), missed.Record!.EstimatedCoordinate);
        Assert.Equal(0, missed.Record.MissedUpdateCount);
        Assert.Equal(1, missed.Record.UncertaintyRadiusHexes);
        Assert.Equal(2, observed.Record!.LastObservedEpoch);
    }

    [Fact]
    public void LaterSameEpochMissRetainsTheMostRecentObservedCoordinate()
    {
        var repository = CreateFirmRepository(epoch: 1);
        Apply(
            repository,
            TacticalTrackObservation.Firm("target", new HexCoord(2, -1)),
            sequence: 2,
            epoch: 3,
            TrackUpdateTrigger.ShipMovementStepCommitted);

        TacticalTrackUpdateResult result = Apply(
            repository,
            TacticalTrackObservation.Missed("target"),
            sequence: 3,
            epoch: 3,
            TrackUpdateTrigger.ShipMovementStepCommitted);

        Assert.Equal(TacticalTrackQuality.Stale, result.CurrentQuality);
        Assert.Equal(new HexCoord(2, -1), result.Record!.EstimatedCoordinate);
        Assert.False(result.AgeAdvanced);
        Assert.Equal(0, result.Record.MissedUpdateCount);
    }

    [Fact]
    public void ReacquisitionResetsAgeAndUncertainty()
    {
        var repository = CreateFirmRepository(epoch: 1);
        Miss(repository, sequence: 2, epoch: 2);
        Miss(repository, sequence: 3, epoch: 3);

        TacticalTrackUpdateResult result = Apply(
            repository,
            TacticalTrackObservation.Firm("target", new HexCoord(1, 1)),
            sequence: 4,
            epoch: 4,
            TrackUpdateTrigger.ShipMovementCommitted);

        Assert.Equal(TacticalTrackQuality.Firm, result.CurrentQuality);
        Assert.Equal(0, result.Record!.MissedUpdateCount);
        Assert.Equal(0, result.Record.UncertaintyRadiusHexes);
        Assert.Equal(4, result.Record.LastObservedEpoch);
        Assert.Equal(3, result.Record.LastAgedEpoch);
    }

    [Fact]
    public void TrackBecomesLostAfterMissesAcrossDistinctTurns()
    {
        var repository = CreateFirmRepository(epoch: 1);
        Miss(repository, sequence: 2, epoch: 2);
        Miss(repository, sequence: 3, epoch: 3);
        TacticalTrackUpdateResult result = Miss(
            repository,
            sequence: 4,
            epoch: 4);

        Assert.Equal(TacticalTrackQuality.Lost, result.CurrentQuality);
        Assert.Equal(3, result.Record!.MissedUpdateCount);
        Assert.Null(result.Record.EstimatedCoordinate);
    }

    [Fact]
    public void ExtraEventsCannotAccelerateLossWithinOneTurn()
    {
        var repository = CreateFirmRepository(epoch: 1);
        for (long sequence = 2; sequence <= 20; sequence++)
        {
            Miss(repository, sequence, epoch: 2);
        }

        TacticalTrackRecord record = repository.Get("observer", "target")!;
        Assert.Equal(TacticalTrackQuality.Stale, record.Quality);
        Assert.Equal(1, record.MissedUpdateCount);
    }

    [Fact]
    public void DifferentTargetsHaveIndependentEpochBudgets()
    {
        var repository = new TacticalTrackRepository();
        Apply(repository, TacticalTrackObservation.Firm("a", new HexCoord(1, 0)), 1, 1);
        Apply(repository, TacticalTrackObservation.Firm("b", new HexCoord(2, 0)), 1, 1);

        TacticalTrackUpdateResult a = Apply(
            repository,
            TacticalTrackObservation.Missed("a"),
            2,
            2);
        TacticalTrackUpdateResult b = Apply(
            repository,
            TacticalTrackObservation.Missed("b"),
            3,
            2);

        Assert.True(a.AgeAdvanced);
        Assert.True(b.AgeAdvanced);
        Assert.Equal(1, a.Record!.MissedUpdateCount);
        Assert.Equal(1, b.Record!.MissedUpdateCount);
    }

    [Fact]
    public void DifferentObserversHaveIndependentEpochBudgets()
    {
        var repository = new TacticalTrackRepository();
        Apply(repository, "observer-a", TacticalTrackObservation.Firm("target", new HexCoord(1, 0)), 1, 1);
        Apply(repository, "observer-b", TacticalTrackObservation.Firm("target", new HexCoord(1, 0)), 1, 1);

        TacticalTrackUpdateResult a = Apply(
            repository,
            "observer-a",
            TacticalTrackObservation.Missed("target"),
            2,
            2);
        TacticalTrackUpdateResult b = Apply(
            repository,
            "observer-b",
            TacticalTrackObservation.Missed("target"),
            3,
            2);

        Assert.True(a.AgeAdvanced);
        Assert.True(b.AgeAdvanced);
    }

    [Fact]
    public void ResultReportsObservationEpochAndWhetherAgeAdvanced()
    {
        var repository = CreateFirmRepository(epoch: 1);

        TacticalTrackUpdateResult result = Miss(
            repository,
            sequence: 2,
            epoch: 7);

        Assert.Equal(7, result.ObservationEpoch);
        Assert.True(result.AgeAdvanced);
        Assert.Equal(7, result.Record!.LastAgedEpoch);
    }

    private TacticalTrackRepository CreateFirmRepository(int epoch)
    {
        var repository = new TacticalTrackRepository();
        Apply(
            repository,
            TacticalTrackObservation.Firm("target", new HexCoord(2, 0)),
            sequence: 1,
            epoch: epoch);
        return repository;
    }

    private TacticalTrackUpdateResult Miss(
        TacticalTrackRepository repository,
        long sequence,
        int epoch) =>
        Apply(
            repository,
            TacticalTrackObservation.Missed("target"),
            sequence,
            epoch);

    private TacticalTrackUpdateResult Apply(
        TacticalTrackRepository repository,
        TacticalTrackObservation observation,
        long sequence,
        int epoch,
        TrackUpdateTrigger trigger = TrackUpdateTrigger.ShipMovementCommitted) =>
        Apply(repository, "observer", observation, sequence, epoch, trigger);

    private TacticalTrackUpdateResult Apply(
        TacticalTrackRepository repository,
        string observer,
        TacticalTrackObservation observation,
        long sequence,
        int epoch,
        TrackUpdateTrigger trigger = TrackUpdateTrigger.ShipMovementCommitted) =>
        TacticalTrackUpdateService.Apply(
            repository,
            observer,
            observation,
            _computing,
            sequence,
            trigger,
            epoch);
}
