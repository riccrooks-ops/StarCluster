using System.Text.Json;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Tactics;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using Xunit;

namespace StarCluster.Tests.Combat.Damage;

/// <summary>
/// Shared CP132 fixture contract. The same JSON is consumed by the Python
/// research kernel so damage semantics, standard map starts/search movement,
/// and visible turn order cannot drift independently.
/// </summary>
public sealed class CanonicalCombatKernelFixtureTests
{
    [Fact]
    public void SharedFixtureMatchesCanonicalLayeredDamageContract()
    {
        JsonElement root = LoadFixture();
        foreach (JsonElement row in root.GetProperty("damageCases").EnumerateArray())
        {
            JsonElement initial = row.GetProperty("initial");
            JsonElement packet = row.GetProperty("packet");
            JsonElement expected = row.GetProperty("expected");

            int shield = initial.GetProperty("shield").GetInt32();
            int armorIntegrity = initial.GetProperty("armorIntegrity").GetInt32();
            int armorProtection = initial.GetProperty("armorProtection").GetInt32();
            int hull = initial.GetProperty("hull").GetInt32();
            var defense = new LayeredDefenseState(
                pristineShieldCapacity: shield,
                currentShieldCapacity: shield,
                shieldArmor: initial.GetProperty("shieldArmor").GetInt32(),
                armorLayers: new[]
                {
                    new ArmorLayerState(
                        "primary",
                        pristineProtection: armorProtection,
                        currentProtection: armorProtection,
                        pristineIntegrity: armorIntegrity,
                        currentIntegrity: armorIntegrity),
                },
                pristineHull: hull,
                currentHull: hull);

            LayeredDamageResolution result = LayeredDamageResolver.Resolve(
                defense,
                new AttackPacket(
                    packet.GetProperty("damage").GetInt32(),
                    packet.GetProperty("spen").GetInt32(),
                    packet.GetProperty("apen").GetInt32()));

            string id = row.GetProperty("id").GetString()!;
            Assert.Equal(expected.GetProperty("effectiveSpen").GetInt32(), result.EffectiveShieldPenetration);
            Assert.Equal(expected.GetProperty("shieldPenetrationResisted").GetInt32(), result.ShieldPenetrationResisted);
            Assert.Equal(expected.GetProperty("shieldBypass").GetInt32(), result.ShieldBypass);
            Assert.Equal(expected.GetProperty("shieldAbsorbed").GetInt32(), result.ShieldAbsorption);
            int expectedDamageToArmor = expected.GetProperty("damageToArmor").GetInt32();
            Assert.Equal(expectedDamageToArmor, result.DamageToArmor);

            if (expectedDamageToArmor == 0)
            {
                // The resolver emits armor-layer diagnostics only when damage actually
                // reaches that layer. Hardening must not manufacture a synthetic
                // zero-damage armor-resolution record merely for fixture reporting.
                Assert.Empty(result.ArmorLayers);
                Assert.Equal(0, expected.GetProperty("effectiveApen").GetInt32());
                Assert.Equal(0, expected.GetProperty("armorPenetrationResisted").GetInt32());
                Assert.Equal(0, expected.GetProperty("armorBypass").GetInt32());
                Assert.Equal(0, expected.GetProperty("armorIntegrityDamage").GetInt32());
            }
            else
            {
                ArmorLayerDamageResolution armor = Assert.Single(result.ArmorLayers);
                Assert.Equal(expected.GetProperty("effectiveApen").GetInt32(), armor.EffectiveArmorPenetration);
                Assert.Equal(expected.GetProperty("armorPenetrationResisted").GetInt32(), armor.ArmorPenetrationResisted);
                Assert.Equal(expected.GetProperty("armorBypass").GetInt32(), armor.ArmorBypass);
                Assert.Equal(expected.GetProperty("armorIntegrityDamage").GetInt32(), armor.IntegrityDamage);
            }

            Assert.Equal(expected.GetProperty("hullDamage").GetInt32(), result.HullDamage);
            Assert.Equal(expected.GetProperty("finalShield").GetInt32(), defense.CurrentShieldCapacity);
            Assert.Equal(expected.GetProperty("finalArmorIntegrity").GetInt32(), defense.ArmorLayers[0].CurrentIntegrity);
            Assert.Equal(expected.GetProperty("finalArmorProtection").GetInt32(), defense.ArmorLayers[0].CurrentProtection);
            Assert.Equal(expected.GetProperty("finalHull").GetInt32(), defense.CurrentHull);
            Assert.True(result.OverkillDamage >= 0, $"Negative overkill in fixture {id}.");
        }
    }

    [Fact]
    public void SharedFixtureMatchesStandardMapSearchAndVisibleTurnOrder()
    {
        JsonElement root = LoadFixture();
        int radius = root.GetProperty("mapRadius").GetInt32();
        HexMap map = HexMap.CreateHexagon(radius);
        Assert.Equal(root.GetProperty("expectedCellCount").GetInt32(), map.CellCount);

        HexCoord startA = ReadCoord(root.GetProperty("standardStartA"));
        HexCoord startB = ReadCoord(root.GetProperty("standardStartB"));
        Assert.Equal(root.GetProperty("standardStartRange").GetInt32(), startA.DistanceTo(startB));

        int searchHexes = root.GetProperty("preContactSearchHexesPerActivation").GetInt32();
        EncounterSearchMove aMove = EncounterSearchMovementResolver.ResolveTowardCenter(map, startA, availableMovementHexes: 9);
        EncounterSearchMove bMove = EncounterSearchMovementResolver.ResolveTowardCenter(map, startB, availableMovementHexes: 9);
        Assert.Equal(searchHexes, aMove.MovementHexes);
        Assert.Equal(searchHexes, bMove.MovementHexes);
        Assert.Equal(startA.DistanceTo(HexCoord.Zero) - searchHexes, aMove.Destination.DistanceTo(HexCoord.Zero));
        Assert.Equal(startB.DistanceTo(HexCoord.Zero) - searchHexes, bMove.Destination.DistanceTo(HexCoord.Zero));

        string[] expectedPhases = root.GetProperty("visibleTurnPhases")
            .EnumerateArray()
            .Select(item => item.GetString()!)
            .ToArray();
        var state = new TacticalTurnState();
        var actual = new List<string> { state.Phase.ToString() };
        for (int i = 1; i < expectedPhases.Length; i++)
        {
            state.AdvancePhase();
            actual.Add(state.Phase.ToString());
        }
        Assert.Equal(expectedPhases, actual);
        state.AdvancePhase();
        Assert.Equal(2, state.TurnNumber);
        Assert.Equal(TacticalTurnPhase.Movement, state.Phase);
    }

    private static JsonElement LoadFixture()
    {
        string fixturePath = FindRepositoryFile(
            "docs", "archive", "testing", "pre-cp165-active", "canonical_combat_kernel_fixtures_v0_1.json");
        using JsonDocument document = JsonDocument.Parse(File.ReadAllText(fixturePath));
        return document.RootElement.Clone();
    }

    private static HexCoord ReadCoord(JsonElement element)
    {
        int[] values = element.EnumerateArray().Select(item => item.GetInt32()).ToArray();
        return new HexCoord(values[0], values[1]);
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

        throw new FileNotFoundException(
            $"Unable to locate repository fixture: {Path.Combine(parts)}");
    }
}
