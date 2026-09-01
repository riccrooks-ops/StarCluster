using System.Text.Json;
using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class CombatResourceDoctrineServiceTests
{
    private static CombatResourceDoctrineContext Base(
        int tp = 8,
        ObservedOffensiveCapability capability = ObservedOffensiveCapability.Unknown,
        int imminent = 0,
        int mainBanks = 1,
        bool pds = true,
        int pdsRc = 1,
        bool hardener = true,
        bool opponentEcm = false,
        bool degraded = false) => new(
            tp, 1, true, true, true, "Energy", mainBanks, 3,
            pds, 1, pdsRc, hardener, 1, true, 1, true, 1,
            opponentEcm, degraded, capability, imminent);

    [Fact]
    public void UnknownThreatKeepsCoreBeforeReadiness()
    {
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(Base(tp: 6));
        Assert.True(d.ActiveSensor);
        Assert.Equal(1, d.FundedMainWeaponBanks);
        Assert.True(d.PdsReady);
        Assert.True(d.ShieldHardenerActive);
    }

    [Fact]
    public void KnownKineticSuppressesMissileAndEnergySpecificReadiness()
    {
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(
            Base(capability: ObservedOffensiveCapability.Kinetic));
        Assert.False(d.PdsReady);
        Assert.False(d.ShieldHardenerActive);
        Assert.Equal(1, d.FundedMainWeaponBanks);
    }

    [Fact]
    public void KnownEnergyKeepsShieldHardenerButNotPds()
    {
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(
            Base(capability: ObservedOffensiveCapability.Energy));
        Assert.True(d.ShieldHardenerActive);
        Assert.False(d.PdsReady);
    }

    [Fact]
    public void EccmIsReactiveToObservedMaterialFirmDegradation()
    {
        Assert.False(CombatResourceDoctrineService.Decide(
            Base(opponentEcm: false, degraded: false)).EccmActive);
        Assert.False(CombatResourceDoctrineService.Decide(
            Base(opponentEcm: true, degraded: false)).EccmActive);
        Assert.True(CombatResourceDoctrineService.Decide(
            Base(opponentEcm: true, degraded: true)).EccmActive);
    }

    [Fact]
    public void ActiveSensorFallsBackBeforeStarvingMainWeapon()
    {
        var c = Base(tp: 3) with { PassiveSensorProvidesUsableTrack = true };
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(c);
        Assert.False(d.ActiveSensor);
        Assert.Equal(1, d.FundedMainWeaponBanks);
    }

    [Fact]
    public void SingleMainStaysOffensiveWhenPdsHasCapacity()
    {
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(
            Base(capability: ObservedOffensiveCapability.Missile, imminent: 2));
        Assert.Equal(1, d.FundedMainWeaponBanks);
        Assert.True(d.PdsReady);
        Assert.Equal(0, d.HeldMainWeaponBanks);
    }

    [Fact]
    public void MainWeaponProvidesFallbackMissileDefenseWhenPdsUnavailable()
    {
        var c = Base(capability: ObservedOffensiveCapability.Missile, imminent: 1, pds: false) with
        {
            LegalMainWeaponShipAttack = false,
        };
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(c);
        Assert.Equal(1, d.HeldMainWeaponBanks);
    }

    [Fact]
    public void SingleMainPreservesLegalShipAttackEvenWithoutPds()
    {
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(
            Base(capability: ObservedOffensiveCapability.Missile, imminent: 1, pds: false));
        Assert.Equal(1, d.FundedMainWeaponBanks);
        Assert.Equal(0, d.HeldMainWeaponBanks);
    }

    [Fact]
    public void DualMainMayHoldOneBankForExcessSubflights()
    {
        var c = Base(tp: 10, capability: ObservedOffensiveCapability.Missile,
            imminent: 2, mainBanks: 2, pds: true, pdsRc: 1) with
        {
            MainWeaponPowerPerBank = 2,
        };
        CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(c);
        Assert.Equal(2, d.FundedMainWeaponBanks);
        Assert.Equal(1, d.HeldMainWeaponBanks);
    }

    [Fact]
    public void SharedCp146FixtureMatchesProductionDoctrineContract()
    {
        string fixturePath = FindRepositoryFile(
            "docs", "archive", "testing", "pre-cp165-active", "cp146_combat_resource_doctrine_parity_fixtures_v0_1.json");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(fixturePath));
        foreach (JsonElement row in document.RootElement.GetProperty("cases").EnumerateArray())
        {
            var c = new CombatResourceDoctrineContext(
                row.GetProperty("spendableTacticalPower").GetInt32(),
                row.GetProperty("activeSensorPower").GetInt32(),
                row.GetProperty("passiveSensorProvidesUsableTrack").GetBoolean(),
                row.GetProperty("firmTrackAvailable").GetBoolean(),
                row.GetProperty("legalMainWeaponShipAttack").GetBoolean(),
                row.GetProperty("mainWeaponFamily").GetString()!,
                row.GetProperty("mainWeaponBanks").GetInt32(),
                row.GetProperty("mainWeaponPowerPerBank").GetInt32(),
                row.GetProperty("pdsAvailable").GetBoolean(),
                row.GetProperty("pdsReadinessPower").GetInt32(),
                row.GetProperty("pdsReactionCapacity").GetInt32(),
                row.GetProperty("shieldHardenerAvailable").GetBoolean(),
                row.GetProperty("shieldHardenerPower").GetInt32(),
                row.GetProperty("ecmAvailable").GetBoolean(),
                row.GetProperty("ecmPower").GetInt32(),
                row.GetProperty("eccmAvailable").GetBoolean(),
                row.GetProperty("eccmPower").GetInt32(),
                row.GetProperty("opponentEcmObserved").GetBoolean(),
                row.GetProperty("firmTrackDegradedByObservedEcm").GetBoolean(),
                Enum.Parse<ObservedOffensiveCapability>(row.GetProperty("opponentCapability").GetString()!, false),
                row.GetProperty("imminentMissileSubflights").GetInt32());
            CombatResourceDoctrineDecision d = CombatResourceDoctrineService.Decide(c);
            JsonElement e = row.GetProperty("expected");
            string id = row.GetProperty("id").GetString()!;
            Assert.Equal(e.GetProperty("activeSensor").GetBoolean(), d.ActiveSensor);
            Assert.Equal(e.GetProperty("fundedMainWeaponBanks").GetInt32(), d.FundedMainWeaponBanks);
            Assert.Equal(e.GetProperty("pdsReady").GetBoolean(), d.PdsReady);
            Assert.Equal(e.GetProperty("fundedPdsReactionCapacity").GetInt32(), d.FundedPdsReactionCapacity);
            Assert.Equal(e.GetProperty("shieldHardenerActive").GetBoolean(), d.ShieldHardenerActive);
            Assert.Equal(e.GetProperty("ecmActive").GetBoolean(), d.EcmActive);
            Assert.Equal(e.GetProperty("eccmActive").GetBoolean(), d.EccmActive);
            Assert.Equal(e.GetProperty("heldMainWeaponBanks").GetInt32(), d.HeldMainWeaponBanks);
            Assert.Equal(e.GetProperty("tacticalPowerRemaining").GetInt32(), d.TacticalPowerRemaining);
            _ = id;
        }
    }

    private static string FindRepositoryFile(params string[] parts)
    {
        IEnumerable<string> starts = new[] { Directory.GetCurrentDirectory(), AppContext.BaseDirectory };
        foreach (string start in starts)
        {
            DirectoryInfo? current = new(start);
            while (current is not null)
            {
                string candidate = Path.Combine(new[] { current.FullName }.Concat(parts).ToArray());
                if (File.Exists(candidate))
                {
                    return candidate;
                }
                current = current.Parent;
            }
        }
        throw new FileNotFoundException($"Unable to locate repository fixture: {Path.Combine(parts)}");
    }
}
