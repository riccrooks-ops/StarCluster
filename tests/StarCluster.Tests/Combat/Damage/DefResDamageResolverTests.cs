using StarCluster.Core.Combat.Damage;
using Xunit;

namespace StarCluster.Tests.Combat.Damage;

public sealed class DefResDamageResolverTests
{
    [Fact]
    public void ShieldDeflectionUsesWholePacketBoundaryAndSpenReduction()
    {
        var deflected = DefResDamageResolver.Resolve(8, 6, 12, 4, 0, 0, 20, 20, 20);
        Assert.True(deflected.Deflected);
        Assert.Equal(8, deflected.FinalShield);

        var coupled = DefResDamageResolver.Resolve(4, 6, 12, 6, 5, 0, 20, 20, 16);
        Assert.False(coupled.Deflected);
        Assert.Equal(15, coupled.EffectiveDefPp);
        Assert.Equal(4.4, coupled.FinalArmorIntegrity, 10);
    }

    [Fact]
    public void ArmorResIsFractionalAndCarriesUnusedRawDamageAfterCollapse()
    {
        var result = DefResDamageResolver.Resolve(0, 1, 12, 2, 0, 0, 0, 25, 100);
        Assert.Equal(25, result.EffectiveResPp);
        Assert.Equal(0, result.FinalArmorIntegrity, 10);
        Assert.Equal(11.333333333333334, result.FinalHull, 10);

        var capped = DefResDamageResolver.Resolve(1, 10, 12, 3, 0, 0, 100, 100, 46);
        Assert.Equal(45, capped.EffectiveDefPp);
        Assert.Equal(95, capped.EffectiveResPp);
        Assert.Equal(9.9, capped.FinalArmorIntegrity, 10);
    }
}
