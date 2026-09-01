using System;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class SensorAndComputingProfileTests
{
    [Fact]
    public void SensorProfileRejectsNegativeTechnologyLevel()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SensorProfile(-1, 2, 4));
    }

    [Fact]
    public void ApproximateRangeCannotBeLessThanFirmRange()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new SensorProfile(2, 4, 3));
    }

    [Fact]
    public void ComputingProfileRejectsNegativeRetention()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => new ComputingProfile(2, -1));
    }

    [Fact]
    public void ClearCloseContactProducesFirmObservation()
    {
        SystemMap map = CreateMap();
        TacticalTrackObservation observation = SensorContactEvaluator.Observe(
            map,
            "target",
            new HexCoord(-2, 2),
            new HexCoord(0, 2),
            new SensorProfile(2, 2, 5));

        Assert.True(observation.Detected);
        Assert.True(observation.Precise);
        Assert.Equal(new HexCoord(0, 2), observation.EstimatedCoordinate);
    }

    [Fact]
    public void ClearDistantContactProducesApproximateObservation()
    {
        SystemMap map = CreateMap();
        TacticalTrackObservation observation = SensorContactEvaluator.Observe(
            map,
            "target",
            new HexCoord(-3, 3),
            new HexCoord(2, 3),
            new SensorProfile(2, 3, 6));

        Assert.True(observation.Detected);
        Assert.False(observation.Precise);
        Assert.Equal(1, observation.UncertaintyRadiusHexes);
    }

    [Fact]
    public void CentralStarBlocksTacticalSensorObservation()
    {
        SystemMap map = CreateMap();
        TacticalTrackObservation observation = SensorContactEvaluator.Observe(
            map,
            "target",
            new HexCoord(-4, 0),
            new HexCoord(4, 0),
            new SensorProfile(2, 8, 10));

        Assert.False(observation.Detected);
        Assert.Null(observation.EstimatedCoordinate);
    }

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            5,
            MapObject.CreateStar("star-primary", "Primary Star"));
}
