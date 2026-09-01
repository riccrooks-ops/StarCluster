using System.Text.Json;
using StarCluster.Core.Combat.Tactics;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class TacticalPackageUtilityServiceTests
{
    private static TacticalPackageCandidate C(
        string id, int tp, int offense, int defense, int funded = 1, int held = 0,
        int pds = 0, bool active = true, bool firm = true) =>
        new(id, tp, offense, defense, funded, held, pds, active, firm);

    [Fact]
    public void HighestFeasibleTotalUtilityWins()
    {
        TacticalPackageCandidate selected = TacticalPackageUtilityService.Choose(
            new[] { C("direct", 4, 3000, 0), C("defend", 4, 0, 3500), C("too-expensive", 6, 9000, 0) }, 5);
        Assert.Equal("defend", selected.Id);
    }

    [Fact]
    public void ExactTotalUtilityTieFavorsOffense()
    {
        TacticalPackageCandidate selected = TacticalPackageUtilityService.Choose(
            new[] { C("direct", 5, 3000, 1000), C("held", 5, 2000, 2000, held: 1) }, 5);
        Assert.Equal("direct", selected.Id);
    }

    [Fact]
    public void ExactUtilityTieFavorsFundedMainThenActiveFirmAndLowerPower()
    {
        TacticalPackageCandidate selected = TacticalPackageUtilityService.Choose(
            new[]
            {
                C("no-main", 3, 2000, 1000, funded: 0, pds: 1),
                C("passive", 4, 2000, 1000, active: false),
                C("approx", 4, 2000, 1000, firm: false),
                C("cost5", 5, 2000, 1000),
                C("cost4", 4, 2000, 1000),
            }, 5);
        Assert.Equal("cost4", selected.Id);
    }

    [Fact]
    public void ExactTieFavorsFewerHeldBanks()
    {
        TacticalPackageCandidate selected = TacticalPackageUtilityService.Choose(
            new[] { C("held", 4, 2000, 1000, held: 1), C("direct", 4, 2000, 1000) }, 4);
        Assert.Equal("direct", selected.Id);
    }

    [Fact]
    public void InvalidCandidateIsRejected()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            TacticalPackageUtilityService.Choose(new[] { C("bad", -1, 1, 1) }, 4));
        Assert.Throws<ArgumentException>(() =>
            TacticalPackageUtilityService.Choose(new[] { C("bad-held", 1, 1, 1, funded: 0, held: 1) }, 4));
    }

    [Fact]
    public void NegativeBudgetAndNoFeasiblePackageAreRejected()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            TacticalPackageUtilityService.Choose(new[] { C("ok", 1, 1, 1) }, -1));
        Assert.Throws<InvalidOperationException>(() =>
            TacticalPackageUtilityService.Choose(new[] { C("costly", 5, 1, 1) }, 4));
    }

    [Fact]
    public void IdentifierProvidesDeterministicFinalTieBreak()
    {
        TacticalPackageCandidate selected = TacticalPackageUtilityService.Choose(
            new[] { C("alpha", 4, 2000, 1000), C("beta", 4, 2000, 1000) }, 4);
        Assert.Equal("beta", selected.Id);
    }

    [Fact]
    public void SharedCp147FixtureMatchesProductionSelectorContract()
    {
        string fixturePath = FindRepositoryFile(
            "docs", "archive", "testing", "pre-cp165-active", "cp147_tactical_package_utility_parity_fixtures_v0_1.json");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(fixturePath));
        foreach (JsonElement row in document.RootElement.GetProperty("cases").EnumerateArray())
        {
            var candidates = row.GetProperty("candidates").EnumerateArray().Select(c => new TacticalPackageCandidate(
                c.GetProperty("id").GetString()!,
                c.GetProperty("tacticalPower").GetInt32(),
                c.GetProperty("offenseUtilityMilli").GetInt32(),
                c.GetProperty("defenseUtilityMilli").GetInt32(),
                c.GetProperty("fundedMainBanks").GetInt32(),
                c.GetProperty("heldMainBanks").GetInt32(),
                c.GetProperty("pdsReactionCapacity").GetInt32(),
                c.GetProperty("activeSensor").GetBoolean(),
                c.GetProperty("firmTrack").GetBoolean())).ToArray();
            TacticalPackageCandidate selected = TacticalPackageUtilityService.Choose(
                candidates, row.GetProperty("spendableTacticalPower").GetInt32());
            Assert.Equal(row.GetProperty("expectedSelectedId").GetString(), selected.Id);
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
                if (File.Exists(candidate)) return candidate;
                current = current.Parent;
            }
        }
        throw new FileNotFoundException($"Unable to locate repository fixture: {Path.Combine(parts)}");
    }
}
