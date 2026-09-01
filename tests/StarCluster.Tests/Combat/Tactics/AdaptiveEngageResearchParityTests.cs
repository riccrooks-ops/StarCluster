using System.Text.Json;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Tactics;
using StarCluster.Core.Combat.Tracking;
using Xunit;

namespace StarCluster.Tests.Combat.Tactics;

public sealed class AdaptiveEngageResearchParityTests
{
    [Fact]
    public void SharedCp144FixtureMatchesProductionAdaptiveEngagePolicy()
    {
        string fixturePath = FindRepositoryFile(
            "docs", "archive", "testing", "pre-cp165-active", "cp144_engage_adaptive_policy_parity_fixtures_v0_1.json");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(fixturePath));
        JsonElement root = document.RootElement;
        int ownMaximum = root.GetProperty("ownMaximumWeaponRange").GetInt32();
        var policy = new AdaptiveEngageTacticalPolicy();

        foreach (JsonElement row in root.GetProperty("cases").EnumerateArray())
        {
            int range = row.GetProperty("currentRange").GetInt32();
            var memory = new TacticalCombatBlackboard("B");
            memory.EstablishContact(1);

            JsonElement lastTrack = row.GetProperty("lastTrack");
            if (lastTrack.ValueKind != JsonValueKind.Null)
            {
                string value = lastTrack.GetString()!;
                var quality = Enum.Parse<TacticalTrackQuality>(value, ignoreCase: false);
                memory.RecordTrackObservation(
                    row.GetProperty("lastTrackRange").GetInt32(),
                    quality,
                    false,
                    false,
                    false);
            }

            JsonElement ownDemo = row.GetProperty("ownDemonstrated");
            if (ownDemo.ValueKind != JsonValueKind.Null)
            {
                memory.RecordOwnAttack(ownDemo.GetInt32());
            }
            JsonElement oppDemo = row.GetProperty("opponentDemonstrated");
            if (oppDemo.ValueKind != JsonValueKind.Null)
            {
                memory.RecordObservedOpponentAttack(oppDemo.GetInt32());
            }

            var own = new TacticalShipDecisionSnapshot(
                "A", ComponentCondition.Operational, 4, true, 1, ownMaximum);
            var target = new ObservedTargetSnapshot("B", true, false, true);
            var context = new TacticalDecisionContext(
                1,
                own,
                target,
                range,
                Array.Empty<ObservedMissileTrack>(),
                TacticalObjective.Engage,
                new RangeDecisionDoctrine(0, ownMaximum, ownMaximum),
                TacticalPreviousTurnOutcome.None,
                memory);

            TacticalOrderPlan plan = policy.ChooseOrders(context);
            RangeOrder expected = Enum.Parse<RangeOrder>(row.GetProperty("expectedOrder").GetString()!, false);
            Assert.Equal(expected, plan.RangeOrder);
            Assert.Equal(row.GetProperty("expectedDesiredRange").GetInt32(), plan.DesiredRangeHexes);
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
