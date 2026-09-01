using System;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileTargetTrackSnapshotTests
{
    [Fact]
    public void CurrentTrackUsesTheCurrentCoordinateForGuidance()
    {
        var coordinate = new HexCoord(2, -1);

        MissileTargetTrackSnapshot track =
            MissileTargetTrackSnapshot.Current("ship-target", coordinate);

        Assert.Equal(MissileTargetTrackQuality.Current, track.Quality);
        Assert.Equal(coordinate, track.CurrentCoordinate);
        Assert.Equal(coordinate, track.LastKnownCoordinate);
        Assert.Equal(coordinate, track.GuidanceCoordinate);
    }

    [Fact]
    public void StaleTrackUsesTheLastKnownCoordinateForGuidance()
    {
        var coordinate = new HexCoord(-1, 3);

        MissileTargetTrackSnapshot track =
            MissileTargetTrackSnapshot.Stale("ship-target", coordinate);

        Assert.Equal(MissileTargetTrackQuality.Stale, track.Quality);
        Assert.Null(track.CurrentCoordinate);
        Assert.Equal(coordinate, track.GuidanceCoordinate);
    }

    [Fact]
    public void LostTrackProvidesNoGuidanceCoordinate()
    {
        MissileTargetTrackSnapshot track =
            MissileTargetTrackSnapshot.Lost("ship-target");

        Assert.Equal(MissileTargetTrackQuality.Lost, track.Quality);
        Assert.False(track.HasGuidanceCoordinate);
        Assert.Null(track.GuidanceCoordinate);
    }

    [Fact]
    public void BlankTargetIdIsRejected()
    {
        Assert.Throws<ArgumentException>(
            () => MissileTargetTrackSnapshot.Lost(" "));
    }
}
