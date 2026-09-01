using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Missiles;

public sealed class MissileTerminalResolutionTests
{
    private const string TargetId = "target";
    private static readonly HexCoord TerminalHex = new(0, 2);

    [Fact]
    public void CommandGuidedMissileAcceptsLiveFirmDatalink()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            range: 6,
            speed: 2,
            terminalProfile: MissileTerminalProfile.PrototypeWithoutSeeker);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.True(result.HasFirmSolution);
        Assert.False(result.UsedSeekerAcquisition);
    }

    [Fact]
    public void CommandGuidedMissileRejectsBlockedDatalink()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.PrototypeWithoutSeeker);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.False(result.HasFirmSolution);
        Assert.Equal(MissileTerminalOutcome.AcquisitionFailed, result.Outcome);
    }

    [Fact]
    public void RetainedLauncherReportDoesNotCountAsLiveFirmDatalink()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.PrototypeWithoutSeeker);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.RetainedDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.False(result.HasFirmSolution);
    }

    [Fact]
    public void PeerGuidanceCannotAuthorizeBaselineCommandGuidedTerminalAttack()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.PrototypeWithoutSeeker);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.PeerGuidance,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Unavailable,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.False(result.HasFirmSolution);
    }

    [Fact]
    public void PeerGuidanceCanAuthorizeTerminalAttackWhenProfileExplicitlyAllowsIt()
    {
        var profile = new MissileTerminalProfile(
            new MissileGuidanceComputerProfile(
                technologyLevel: 2,
                baseHitChancePercent: 65,
                minimumHitChancePercent: 5,
                maximumHitChancePercent: 95),
            allowsPeerTerminalGuidance: true);
        GuidedMissileSalvo salvo = CreateSalvo(TerminalHex, 6, 2, profile);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.PeerGuidance,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Unavailable,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.True(result.HasFirmSolution);
        Assert.False(result.UsedSeekerAcquisition);
    }

    [Fact]
    public void SensorEquippedMissileMayUseLiveFirmDatalink()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.PrototypeWithoutSeeker);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardSensor: true,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.True(result.HasFirmSolution);
    }

    [Fact]
    public void SensorEquippedMissileMayUseOwnCurrentFirmReport()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.PrototypeWithoutSeeker);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.LocalSensor,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: true,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.True(result.HasFirmSolution);
    }

    [Fact]
    public void LocalReportRequiresInstalledNavigationSensor()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.PrototypeWithoutSeeker);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.LocalSensor,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.False(result.HasFirmSolution);
    }

    [Fact]
    public void SeekerOnlyMissileMustAcquireLocallyEvenWithFirmRemoteCue()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(40));

        Assert.True(result.HasFirmSolution);
        Assert.True(result.UsedSeekerAcquisition);
        Assert.Equal(40, result.AcquisitionRoll);
    }

    [Fact]
    public void SeekerOnlyMissileCanUseRemoteApproximateCueForCoLocatedAcquisition()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.RetainedDatalink,
            MissileTargetTrackSnapshot.Approximate(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.True(result.HasFirmSolution);
        Assert.True(result.UsedSeekerAcquisition);
    }

    [Fact]
    public void SensorPlusSeekerRejectsRemoteApproximateCueWithoutLocalNavigationTrack()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.RetainedDatalink,
            MissileTargetTrackSnapshot.Approximate(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: true,
            random: new FixedMissileTerminalRandomSource(1));

        Assert.False(result.HasFirmSolution);
        Assert.False(result.UsedSeekerAcquisition);
        Assert.Null(result.AcquisitionRoll);
    }

    [Fact]
    public void SensorPlusSeekerCanRefineLocalApproximateNavigationTrackIntoFirm()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.LocalSensor,
            MissileTargetTrackSnapshot.Approximate(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: true,
            random: new FixedMissileTerminalRandomSource(50));

        Assert.True(result.HasFirmSolution);
        Assert.True(result.UsedSeekerAcquisition);
        Assert.Equal(MissileGuidanceReportSource.LocalSensor, result.ReportSource);
        Assert.Equal(MissileTargetTrackQuality.Approximate, result.ReportQuality);
    }

    [Fact]
    public void SeekerCannotAttemptFromStaleCue()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);

        MissileTerminalResolution result = Acquire(
            salvo,
            MissileGuidanceReportSource.RetainedDatalink,
            MissileTargetTrackSnapshot.Stale(TargetId, TerminalHex),
            MissileDatalinkState.Blocked,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(1));

        Assert.False(result.HasFirmSolution);
        Assert.False(result.UsedSeekerAcquisition);
        Assert.Null(result.AcquisitionRoll);
    }

    [Fact]
    public void SeekerEccmReducesTerminalEcmPenalty()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);

        MissileTerminalResolution result = MissileTerminalResolutionService.EvaluateAcquisition(
            salvo,
            TerminalHex,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardNavigationSensorInstalled: false,
            targetTerminalEcmStrength: 4,
            randomSource: new FixedMissileTerminalRandomSource(45));

        Assert.Equal(45, result.AcquisitionChancePercent);
        Assert.True(result.HasFirmSolution);
    }

    [Fact]
    public void SeekerAccuracyBonusIsAppliedAfterFirmSolutionExists()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);
        MissileTerminalResolution acquisition = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(40));

        MissileTerminalResolution attack =
            MissileTerminalResolutionService.ResolveAttack(
                salvo,
                acquisition,
                new FixedMissileTerminalRandomSource(80));

        Assert.True(attack.SeekerAccuracyApplied);
        Assert.Equal(80, attack.EffectiveHitChancePercent);
        Assert.Equal(MissileTerminalOutcome.Hit, attack.Outcome);
    }


    [Theory]
    [InlineData(ComponentCondition.Operational, 80)]
    [InlineData(ComponentCondition.Degraded, 80)]
    [InlineData(ComponentCondition.Disabled, 90)]
    [InlineData(ComponentCondition.Destroyed, 90)]
    public void Terminal_attack_applies_immobile_target_bonus(
        ComponentCondition stlCondition,
        int expectedChance)
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);
        MissileTerminalResolution acquisition = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(40));

        MissileTerminalResolution result =
            MissileTerminalResolutionService.ResolveAttack(
                salvo,
                acquisition,
                new FixedMissileTerminalRandomSource(50),
                stlCondition);

        Assert.Equal(expectedChance, result.EffectiveHitChancePercent);
    }

    [Fact]
    public void Terminal_missile_uses_committed_then_following_turn_mobility_snapshots()
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);
        MissileTerminalResolution acquisition = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(40));
        var committedSnapshot = new ShipCombatTurnSnapshot(
            ComponentCondition.Operational);
        var followingSnapshot = new ShipCombatTurnSnapshot(
            ComponentCondition.Disabled);

        MissileTerminalResolution committed =
            MissileTerminalResolutionService.ResolveAttack(
                salvo,
                acquisition,
                new FixedMissileTerminalRandomSource(50),
                committedSnapshot.StlCondition);
        MissileTerminalResolution following =
            MissileTerminalResolutionService.ResolveAttack(
                salvo,
                acquisition,
                new FixedMissileTerminalRandomSource(50),
                followingSnapshot.StlCondition);

        Assert.Equal(80, committed.EffectiveHitChancePercent);
        Assert.Equal(90, following.EffectiveHitChancePercent);
    }

    [Fact]
    public void NaturalOneCreatesRecoverableDud()
    {
        MissileTerminalResolution result = ResolveAttack(1);

        Assert.Equal(MissileTerminalOutcome.Dud, result.Outcome);
        Assert.True(result.IsDud);
    }

    [Fact]
    public void NaturalOneHundredCreatesCriticalHit()
    {
        MissileTerminalResolution result = ResolveAttack(100);

        Assert.Equal(MissileTerminalOutcome.CriticalHit, result.Outcome);
        Assert.True(result.IsCriticalHit);
    }

    [Fact]
    public void RollAboveBoundedChanceMisses()
    {
        MissileTerminalResolution result = ResolveAttack(96);

        Assert.Equal(MissileTerminalOutcome.Miss, result.Outcome);
        Assert.False(result.IsHit);
    }

    [Fact]
    public void RollWithinBoundedChanceHits()
    {
        MissileTerminalResolution result = ResolveAttack(50);

        Assert.Equal(MissileTerminalOutcome.Hit, result.Outcome);
        Assert.True(result.IsHit);
    }

    [Fact]
    public void PdsReceivesTerminalEntryAndPreAttackOpportunities()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(-1, 2),
            6,
            2,
            MissileTerminalProfile.Prototype);
        MissileInterceptionPhaseContext context = CreatePdsContext(
            new FixedMissileInterceptionResolver(MissileInterceptionOutcome.Missed),
            attempts: 2);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            context,
            new FixedMissileTerminalRandomSource(40, 50));

        Assert.Equal(2, result.InterceptionAttempts.Count);
        Assert.Equal(
            new[]
            {
                MissileInterceptionOpportunity.TerminalEntry,
                MissileInterceptionOpportunity.PreTerminalAttack,
            },
            result.InterceptionAttempts.Select(attempt => attempt.Opportunity));
        Assert.Equal(MissileTerminalOutcome.Hit, result.TerminalResolution!.Outcome);
    }

    [Fact]
    public void TerminalEntryInterceptionPreventsAcquisitionAndAttack()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(-1, 2),
            6,
            2,
            MissileTerminalProfile.Prototype);
        MissileInterceptionPhaseContext context = CreatePdsContext(
            new FixedMissileInterceptionResolver(MissileInterceptionOutcome.Intercepted),
            attempts: 2);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            context,
            new FixedMissileTerminalRandomSource(40, 50));

        Assert.Equal(GuidedMissileStatus.Intercepted, result.Status);
        Assert.Single(result.InterceptionAttempts);
        Assert.Equal(
            MissileInterceptionOpportunity.TerminalEntry,
            result.InterceptionAttempts[0].Opportunity);
        Assert.Equal(
            MissileTerminalOutcome.Intercepted,
            result.TerminalResolution!.Outcome);
    }

    [Fact]
    public void PreAttackInterceptionOccursAfterSuccessfulAcquisition()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(-1, 2),
            6,
            2,
            MissileTerminalProfile.Prototype);
        var resolver = new SequenceInterceptionResolver(
            MissileInterceptionOutcome.Missed,
            MissileInterceptionOutcome.Intercepted);
        MissileInterceptionPhaseContext context = CreatePdsContext(
            resolver,
            attempts: 2);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            context,
            new FixedMissileTerminalRandomSource(40, 50));

        Assert.Equal(GuidedMissileStatus.Intercepted, result.Status);
        Assert.Equal(2, result.InterceptionAttempts.Count);
        Assert.True(result.TerminalResolution!.HasFirmSolution);
        Assert.False(result.TerminalResolution.AttackWasResolved);
        Assert.Equal(MissileTerminalOutcome.Intercepted, result.TerminalResolution.Outcome);
    }

    [Fact]
    public void FailedArrivalAcquisitionDoesNotSpendStationarySearchFuel()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(-1, 2),
            6,
            2,
            MissileTerminalProfile.Prototype);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            interceptionContext: null,
            terminalRandomSource: new FixedMissileTerminalRandomSource(100));

        Assert.Equal(GuidedMissileStatus.Searching, result.Status);
        Assert.Equal(0, salvo.StationarySearchFuelSpent);
        Assert.Equal(0, result.StationarySearchFuelSpentThisPhase);
    }

    [Fact]
    public void LaterStationarySearchConsumesOneFuelAndCanAttackImmediately()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(-1, 2),
            6,
            2,
            MissileTerminalProfile.Prototype);
        MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            interceptionContext: null,
            terminalRandomSource: new FixedMissileTerminalRandomSource(100));

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            interceptionContext: null,
            terminalRandomSource: new FixedMissileTerminalRandomSource(40, 50));

        Assert.Equal(1, result.StationarySearchFuelSpentThisPhase);
        Assert.Equal(1, salvo.StationarySearchFuelSpent);
        Assert.Equal(GuidedMissileStatus.Expended, result.Status);
        Assert.Equal(MissileTerminalOutcome.Hit, result.TerminalResolution!.Outcome);
    }

    [Fact]
    public void FailedTerminalOpportunityWithNoFuelSelfDestructsSafely()
    {
        SystemMap map = CreateMap();
        GuidedMissileSalvo salvo = CreateSalvo(
            new HexCoord(-1, 2),
            range: 1,
            speed: 1,
            terminalProfile: MissileTerminalProfile.Prototype);

        GuidedMissileAdvanceResult result = MissileGuidanceService.AdvanceOnePhase(
            map,
            salvo,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            interceptionContext: null,
            terminalRandomSource: new FixedMissileTerminalRandomSource(100));

        Assert.Equal(GuidedMissileStatus.SelfDestructed, result.Status);
        Assert.Equal(MissileTerminalOutcome.SelfDestructed, result.TerminalResolution!.Outcome);
        Assert.Equal(0, salvo.RemainingRange);
    }

    private static MissileTerminalResolution ResolveAttack(int attackRoll)
    {
        GuidedMissileSalvo salvo = CreateSalvo(
            TerminalHex,
            6,
            2,
            MissileTerminalProfile.Prototype);
        MissileTerminalResolution acquisition = Acquire(
            salvo,
            MissileGuidanceReportSource.FreshDatalink,
            MissileTargetTrackSnapshot.Current(TargetId, TerminalHex),
            MissileDatalinkState.Live,
            onboardSensor: false,
            random: new FixedMissileTerminalRandomSource(40));
        return MissileTerminalResolutionService.ResolveAttack(
            salvo,
            acquisition,
            new FixedMissileTerminalRandomSource(attackRoll));
    }

    private static MissileTerminalResolution Acquire(
        GuidedMissileSalvo salvo,
        MissileGuidanceReportSource source,
        MissileTargetTrackSnapshot report,
        MissileDatalinkState datalinkState,
        bool onboardSensor,
        IMissileTerminalRandomSource random) =>
        MissileTerminalResolutionService.EvaluateAcquisition(
            salvo,
            TerminalHex,
            source,
            report,
            datalinkState,
            onboardSensor,
            targetTerminalEcmStrength: 0,
            randomSource: random);

    private static GuidedMissileSalvo CreateSalvo(
        HexCoord coordinate,
        int range,
        int speed,
        MissileTerminalProfile terminalProfile) =>
        new(
            "salvo",
            TacticalSide.Enemy,
            "launcher",
            TargetId,
            coordinate,
            new MissileFlightProfile(2, range, speed),
            terminalProfile);

    private static MissileInterceptionPhaseContext CreatePdsContext(
        IMissileInterceptionResolver resolver,
        int attempts)
    {
        var pds = new MissileDefenseSystem(
            "pds",
            "defender",
            TacticalSide.Player,
            TerminalHex,
            new MissileDefenseProfile(
                2,
                interceptionRangeHexes: 0,
                maximumAttemptsPerPhase: attempts),
            sourceType: MissileDefenseSourceType.PointDefenseSystem);
        return new MissileInterceptionPhaseContext(new[] { pds }, resolver);
    }

    private static SystemMap CreateMap() =>
        SystemMap.Create(
            radius: 5,
            MapObject.CreateStar("star", "Primary Star"));

    private sealed class SequenceInterceptionResolver : IMissileInterceptionResolver
    {
        private readonly Queue<MissileInterceptionOutcome> _outcomes;

        public SequenceInterceptionResolver(
            params MissileInterceptionOutcome[] outcomes)
        {
            _outcomes = new Queue<MissileInterceptionOutcome>(outcomes);
        }

        public MissileInterceptionOutcome Resolve(
            MissileInterceptionAttempt attempt)
        {
            Assert.NotNull(attempt);
            return _outcomes.Dequeue();
        }
    }
}
