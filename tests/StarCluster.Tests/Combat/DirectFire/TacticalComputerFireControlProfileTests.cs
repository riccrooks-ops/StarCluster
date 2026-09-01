using System;
using StarCluster.Core.Combat.DirectFire;
using Xunit;

namespace StarCluster.Tests.Combat.DirectFire;

public sealed class TacticalComputerFireControlProfileTests
{
    [Fact]
    public void ProfileRejectsNegativeTechnologyLevel()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new TacticalComputerFireControlProfile(-1, 25));
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(101)]
    public void ProfileRejectsOutOfRangeApproximateTrackPenalty(int penalty)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            new TacticalComputerFireControlProfile(1, penalty));
    }

    [Fact]
    public void ZeroLegacyPenaltyReportsNoHistoricalApproximateSupport()
    {
        var profile = new TacticalComputerFireControlProfile(1, 0);

        Assert.False(profile.SupportsApproximateTrackDirectFire);
    }

    [Fact]
    public void LegacyProfileMayRetainTwentyFivePointPenaltyForProvenance()
    {
        var profile = new TacticalComputerFireControlProfile(1, 25);

        Assert.True(profile.SupportsApproximateTrackDirectFire);
        Assert.Equal(25, profile.ApproximateTrackDirectFireAccuracyPenalty);
    }
}
