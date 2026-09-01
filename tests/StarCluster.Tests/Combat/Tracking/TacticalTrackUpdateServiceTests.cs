using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class TacticalTrackUpdateServiceTests
{
    private readonly ComputingProfile _computing = new(3, 2, 1);

    [Fact]
    public void MissedUnknownContactRemainsUnknown()
    {
        var repository = new TacticalTrackRepository();
        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Missed("target"),
            sequence: 1);

        Assert.True(result.RemainsUnknown);
        Assert.Null(repository.Get("observer", "target"));
    }

    [Fact]
    public void FirmObservationCreatesFirmTrack()
    {
        var repository = new TacticalTrackRepository();
        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Firm("target", new HexCoord(2, 0)),
            sequence: 1);

        Assert.True(result.Created);
        Assert.Equal(TacticalTrackQuality.Firm, result.CurrentQuality);
        Assert.True(result.Record!.SupportsPrecisionDirectFire);
    }

    [Fact]
    public void ApproximateObservationCreatesApproximateTrack()
    {
        var repository = new TacticalTrackRepository();
        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Approximate(
                "target",
                new HexCoord(2, 0),
                uncertaintyRadiusHexes: 2),
            sequence: 1);

        Assert.Equal(TacticalTrackQuality.Approximate, result.CurrentQuality);
        Assert.Equal(2, result.Record!.UncertaintyRadiusHexes);
        Assert.False(result.Record.SupportsPrecisionDirectFire);
    }

    [Fact]
    public void MissedFirmTrackBecomesStale()
    {
        var repository = CreateFirmRepository();
        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Missed("target"),
            sequence: 2);

        Assert.Equal(TacticalTrackQuality.Firm, result.PreviousQuality);
        Assert.Equal(TacticalTrackQuality.Stale, result.CurrentQuality);
        Assert.Equal(new HexCoord(2, 0), result.Record!.EstimatedCoordinate);
    }

    [Fact]
    public void EachMissedUpdateGrowsUncertainty()
    {
        var repository = CreateFirmRepository();
        Apply(repository, "observer", TacticalTrackObservation.Missed("target"), 2);
        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Missed("target"),
            sequence: 3);

        Assert.Equal(2, result.Record!.UncertaintyRadiusHexes);
    }

    [Fact]
    public void TrackRemainsStaleThroughConfiguredRetention()
    {
        var repository = CreateFirmRepository();
        Apply(repository, "observer", TacticalTrackObservation.Missed("target"), 2);
        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Missed("target"),
            sequence: 3);

        Assert.Equal(TacticalTrackQuality.Stale, result.CurrentQuality);
        Assert.True(result.Record!.IsVisibleOnTacticalMap);
    }

    [Fact]
    public void TrackBecomesLostAfterRetentionIsExceeded()
    {
        var repository = CreateFirmRepository();
        Apply(repository, "observer", TacticalTrackObservation.Missed("target"), 2);
        Apply(repository, "observer", TacticalTrackObservation.Missed("target"), 3);
        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Missed("target"),
            sequence: 4);

        Assert.Equal(TacticalTrackQuality.Lost, result.CurrentQuality);
        Assert.Null(result.Record!.EstimatedCoordinate);
        Assert.False(result.Record.IsVisibleOnTacticalMap);
    }

    [Fact]
    public void LostTrackCanBeReacquiredAsFirm()
    {
        var repository = CreateFirmRepository();
        Apply(repository, "observer", TacticalTrackObservation.Missed("target"), 2);
        Apply(repository, "observer", TacticalTrackObservation.Missed("target"), 3);
        Apply(repository, "observer", TacticalTrackObservation.Missed("target"), 4);

        TacticalTrackUpdateResult result = Apply(
            repository,
            "observer",
            TacticalTrackObservation.Firm("target", new HexCoord(1, 1)),
            sequence: 5);

        Assert.Equal(TacticalTrackQuality.Firm, result.CurrentQuality);
        Assert.Equal(0, result.Record!.MissedUpdateCount);
        Assert.Equal(new HexCoord(1, 1), result.Record.EstimatedCoordinate);
    }

    [Fact]
    public void TracksAreObserverSpecific()
    {
        var repository = new TacticalTrackRepository();
        Apply(
            repository,
            "observer-a",
            TacticalTrackObservation.Firm("target", new HexCoord(1, 0)),
            1);
        Apply(
            repository,
            "observer-b",
            TacticalTrackObservation.Approximate("target", new HexCoord(2, 0)),
            1);

        Assert.Equal(
            TacticalTrackQuality.Firm,
            repository.Get("observer-a", "target")!.Quality);
        Assert.Equal(
            TacticalTrackQuality.Approximate,
            repository.Get("observer-b", "target")!.Quality);
    }

    [Fact]
    public void PriorIntelligenceCreatesStaleTrackWithoutCurrentDetection()
    {
        var repository = new TacticalTrackRepository();
        TacticalTrackRecord record = repository.SeedPriorIntelligence(
            "observer",
            "target",
            new HexCoord(3, -1),
            sequence: 0);

        Assert.Equal(TacticalTrackQuality.Stale, record.Quality);
        Assert.Equal(
            TacticalTrackSourceType.PreviousIntelligence,
            record.SourceType);
    }

    private TacticalTrackUpdateResult Apply(
        TacticalTrackRepository repository,
        string observer,
        TacticalTrackObservation observation,
        long sequence) =>
        TacticalTrackUpdateService.Apply(
            repository,
            observer,
            observation,
            _computing,
            sequence,
            TrackUpdateTrigger.ShipMovementCommitted);

    private TacticalTrackRepository CreateFirmRepository()
    {
        var repository = new TacticalTrackRepository();
        Apply(
            repository,
            "observer",
            TacticalTrackObservation.Firm("target", new HexCoord(2, 0)),
            sequence: 1);
        return repository;
    }
}
