using StarCluster.Core.Combat.Power;
using Xunit;

namespace StarCluster.Tests.Combat.Power;

public sealed class TacticalPowerLedgerTests
{
    [Fact]
    public void BeginTurnCreatesAvailableEnvelope()
    {
        var ledger = new TacticalPowerLedger();

        ledger.BeginTurn(5);

        Assert.Equal(5, ledger.AvailablePower);
        Assert.Equal(5, ledger.SpendablePower);
    }

    [Fact]
    public void PoweredSystemLocksPowerForTheTurn()
    {
        TacticalPowerLedger ledger = CreateLedger();

        ledger.IncreasePoweredSystem("ecm", 2);

        Assert.Equal(2, ledger.PoweredPower);
        Assert.Equal(3, ledger.AvailablePower);
    }

    [Fact]
    public void PoweredSystemCanIncreaseUsingRemainingPower()
    {
        TacticalPowerLedger ledger = CreateLedger();

        ledger.IncreasePoweredSystem("ecm", 1);
        ledger.IncreasePoweredSystem("ecm", 1);

        Assert.Equal(2, ledger.PoweredPower);
        Assert.Equal(2, Assert.Single(ledger.Snapshot().Systems).LockedPower);
    }

    [Fact]
    public void SpentPowerCannotBeReused()
    {
        TacticalPowerLedger ledger = CreateLedger();

        ledger.Spend(3);

        Assert.Equal(2, ledger.AvailablePower);
        Assert.Throws<InvalidOperationException>(() => ledger.Spend(3));
    }

    [Fact]
    public void EarmarkRemainsAvailableButReducesSpendablePower()
    {
        TacticalPowerLedger ledger = CreateLedger();

        ledger.Earmark("hold", 2);

        Assert.Equal(5, ledger.AvailablePower);
        Assert.Equal(3, ledger.SpendablePower);
        Assert.Equal(2, ledger.EarmarkedPower);
    }

    [Fact]
    public void TriggerEarmarkConvertsItToSpentPower()
    {
        TacticalPowerLedger ledger = CreateLedger();
        ledger.Earmark("hold", 2);

        int triggered = ledger.TriggerEarmark("hold");

        Assert.Equal(2, triggered);
        Assert.Equal(2, ledger.SpentPower);
        Assert.Equal(3, ledger.AvailablePower);
        Assert.Equal(0, ledger.EarmarkedPower);
    }

    [Fact]
    public void ReleaseEarmarkReturnsItToSpendablePower()
    {
        TacticalPowerLedger ledger = CreateLedger();
        ledger.Earmark("hold", 2);

        ledger.ReleaseEarmark("hold");

        Assert.Equal(5, ledger.SpendablePower);
        Assert.Equal(0, ledger.EarmarkedPower);
    }

    [Fact]
    public void ShutdownEndsEffectWithoutReleasingLockedPower()
    {
        TacticalPowerLedger ledger = CreateLedger();
        ledger.IncreasePoweredSystem("ecm", 2);

        ledger.ShutdownSystem("ecm");

        PoweredSystemSnapshot system = Assert.Single(ledger.Snapshot().Systems);
        Assert.False(system.IsActive);
        Assert.True(system.ReactivationProhibited);
        Assert.Equal(2, ledger.PoweredPower);
    }

    [Fact]
    public void ShutdownPreventsSameTurnReactivation()
    {
        TacticalPowerLedger ledger = CreateLedger();
        ledger.IncreasePoweredSystem("ecm", 1);
        ledger.ShutdownSystem("ecm");

        Assert.Throws<InvalidOperationException>(() =>
            ledger.IncreasePoweredSystem("ecm", 1));
    }

    [Fact]
    public void DisableAlsoRetainsLockedPower()
    {
        TacticalPowerLedger ledger = CreateLedger();
        ledger.IncreasePoweredSystem("pds", 1);

        ledger.DisableSystem("pds");

        Assert.Equal(1, ledger.PoweredPower);
        Assert.False(Assert.Single(ledger.Snapshot().Systems).IsActive);
    }

    [Fact]
    public void GeneratedPowerExpandsCurrentTurnEnvelope()
    {
        TacticalPowerLedger ledger = CreateLedger();

        ledger.AddGeneratedPower(1);

        Assert.Equal(6, ledger.Envelope);
        Assert.Equal(6, ledger.AvailablePower);
    }

    [Fact]
    public void NextTurnClearsPoweredSpentAndEarmarkedState()
    {
        TacticalPowerLedger ledger = CreateLedger();
        ledger.IncreasePoweredSystem("ecm", 1);
        ledger.Spend(1);
        ledger.Earmark("hold", 1);

        ledger.BeginTurn(3);

        Assert.Equal(3, ledger.AvailablePower);
        Assert.Equal(0, ledger.PoweredPower);
        Assert.Equal(0, ledger.SpentPower);
        Assert.Equal(0, ledger.EarmarkedPower);
    }

    [Fact]
    public void FtlTransitionClearsEntireTurnLedger()
    {
        TacticalPowerLedger ledger = CreateLedger();
        ledger.Spend(2);

        ledger.ClearForFtlTransition();

        Assert.Equal(0, ledger.Envelope);
        Assert.Equal(0, ledger.AvailablePower);
        Assert.Equal(0, ledger.SpentPower);
    }

    private static TacticalPowerLedger CreateLedger()
    {
        var ledger = new TacticalPowerLedger();
        ledger.BeginTurn(5);
        return ledger;
    }
}
