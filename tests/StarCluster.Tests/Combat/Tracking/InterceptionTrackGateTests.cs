using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using Xunit;

namespace StarCluster.Tests.Combat.Tracking;

public sealed class InterceptionTrackGateTests
{
    [Fact]
    public void HeldWeaponRequiresFirmTacticalTrack()
    {
        MissileDefenseSystem defense = CreateDefense(
            "held",
            MissileDefenseSourceType.HeldDirectFireWeapon,
            requiresFirmTrack: true);
        GuidedMissileSalvo salvo = CreateSalvo();
        var context = new MissileInterceptionPhaseContext(
            new[] { defense },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Intercepted),
            map: null,
            trackProvider: new FixedMissileDefenseTrackProvider(false));

        Assert.Empty(context.ResolveAt(
            salvo,
            salvo.CurrentCoordinate,
            isFinalApproach: false));
        Assert.False(salvo.IsTerminal);
    }

    [Fact]
    public void HeldWeaponFiresWhenFirmTrackIsAvailable()
    {
        MissileDefenseSystem defense = CreateDefense(
            "held",
            MissileDefenseSourceType.HeldDirectFireWeapon,
            requiresFirmTrack: true);
        GuidedMissileSalvo salvo = CreateSalvo();
        var context = new MissileInterceptionPhaseContext(
            new[] { defense },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Intercepted),
            map: null,
            trackProvider: new FixedMissileDefenseTrackProvider(true));

        Assert.Single(context.ResolveAt(
            salvo,
            salvo.CurrentCoordinate,
            isFinalApproach: false));
        Assert.Equal(GuidedMissileStatus.Intercepted, salvo.Status);
    }

    [Fact]
    public void PointDefenseUsesIndependentLocalAcquisition()
    {
        MissileDefenseSystem defense = CreateDefense(
            "pds",
            MissileDefenseSourceType.PointDefenseSystem,
            requiresFirmTrack: false);
        GuidedMissileSalvo salvo = CreateSalvo();
        var context = new MissileInterceptionPhaseContext(
            new[] { defense },
            new FixedMissileInterceptionResolver(
                MissileInterceptionOutcome.Intercepted),
            map: null,
            trackProvider: new FixedMissileDefenseTrackProvider(false));

        Assert.Single(context.ResolveAt(
            salvo,
            salvo.CurrentCoordinate,
            MissileInterceptionOpportunity.TerminalEntry));
        Assert.Equal(GuidedMissileStatus.Intercepted, salvo.Status);
    }

    private static MissileDefenseSystem CreateDefense(
        string id,
        MissileDefenseSourceType sourceType,
        bool requiresFirmTrack) => new(
        id,
        "ship-player",
        TacticalSide.Player,
        new HexCoord(0, 0),
        new MissileDefenseProfile(2, 2, 1),
        sourceType: sourceType,
        requiresFirmTacticalTrack: requiresFirmTrack);

    private static GuidedMissileSalvo CreateSalvo() => new(
        "hostile",
        TacticalSide.Enemy,
        "ship-enemy",
        "ship-player",
        new HexCoord(1, 0),
        new MissileFlightProfile(2, 5, 1));
}
