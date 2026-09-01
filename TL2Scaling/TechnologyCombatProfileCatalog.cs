using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Weapons;
using StarCluster.ScenarioRunner.TL1;

namespace StarCluster.ScenarioRunner.TL2Scaling;

internal static class TechnologyCombatProfileCatalog
{
    public static IReadOnlyDictionary<string, TechnologyCombatProfile> Load(
        string candidateStudyPath,
        Tl1BaselineCatalog baseline)
    {
        string json = File.ReadAllText(candidateStudyPath);
        using JsonDocument root = JsonDocument.Parse(json);
        string schemaVersion = root.RootElement.TryGetProperty(
                "schemaVersion", out JsonElement schema)
            ? schema.GetString() ?? string.Empty
            : string.Empty;
        if (string.Equals(
                schemaVersion,
                ArchitectureRuntimeProfileCatalogDocument.SchemaVersion,
                StringComparison.Ordinal))
        {
            return LoadArchitectureRuntimeCatalog(json, baseline);
        }

        CombatScalingStudyDocument study =
            JsonSerializer.Deserialize<CombatScalingStudyDocument>(
                json, JsonOptions()) ?? throw new InvalidOperationException(
                "Technology profile catalog could not be read.");
        ValidateBaselineHash(study.BaselineSha256, baseline);
        var profiles = new Dictionary<string, TechnologyCombatProfile>(
            StringComparer.Ordinal)
        {
            ["tl1-production"] = BuildTl1(baseline),
        };
        foreach (Tl2CandidateDocument candidate in study.Candidates)
        {
            if (!profiles.TryAdd(candidate.Id, BuildCandidate(candidate)))
            {
                throw new InvalidOperationException(
                    $"Duplicate technology profile ID '{candidate.Id}'.");
            }
        }
        return profiles;
    }

    private static IReadOnlyDictionary<string, TechnologyCombatProfile>
        LoadArchitectureRuntimeCatalog(string json, Tl1BaselineCatalog baseline)
    {
        ArchitectureRuntimeProfileCatalogDocument catalog =
            JsonSerializer.Deserialize<ArchitectureRuntimeProfileCatalogDocument>(
                json, JsonOptions()) ?? throw new InvalidOperationException(
                "Architecture runtime profile catalog could not be read.");
        ValidateBaselineHash(catalog.BaselineSha256, baseline);
        if (catalog.Profiles.Count < 2)
        {
            throw new InvalidOperationException(
                "Architecture runtime catalog requires at least the frozen TL1 and accepted TL2 production profiles.");
        }

        var profiles = new Dictionary<string, TechnologyCombatProfile>(
            StringComparer.Ordinal);
        foreach (ArchitectureRuntimeProfileDocument document in catalog.Profiles)
        {
            TechnologyCombatProfile profile = BuildArchitectureProfile(document);
            if (!profiles.TryAdd(profile.Id, profile))
            {
                throw new InvalidOperationException(
                    $"Duplicate technology profile ID '{profile.Id}'.");
            }
        }
        if (!profiles.TryGetValue(
                "tl1-production", out TechnologyCombatProfile? tl1) ||
            !profiles.TryGetValue(
                "tl2-production", out TechnologyCombatProfile? tl2) ||
            tl1.TechnologyLevel != 1 || tl2.TechnologyLevel != 2)
        {
            throw new InvalidOperationException(
                "Architecture runtime catalog must define TL1 and TL2 production profiles at their matching technology levels.");
        }
        if (profiles.Values.Any(profile => profile.TechnologyLevel is < 1 or > 9))
        {
            throw new InvalidOperationException(
                "Architecture runtime profiles must use player technology levels 1 through 9.");
        }
        TechnologyCombatProfile frozenTl1 = BuildTl1(baseline);
        if (tl1 != frozenTl1)
        {
            throw new InvalidOperationException(
                "Table-derived TL1 profile does not exactly reproduce the frozen authoritative TL1 baseline.");
        }
        return profiles;
    }

    private static void ValidateBaselineHash(
        string profileBaselineHash, Tl1BaselineCatalog baseline)
    {
        if (!string.Equals(
                profileBaselineHash,
                baseline.Sha256,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "Technology profile catalog baseline hash does not match the " +
                "authoritative TL1 baseline.");
        }
    }

    public static TechnologyCombatProfile BuildTl1(Tl1BaselineCatalog baseline)
    {
        int effectivePds = Math.Clamp(
            baseline.GetInt("kinetic_pds_chance") +
            baseline.GetInt("targeting_accuracy_bonus"),
            0,
            95);
        return new TechnologyCombatProfile(
            "tl1-production",
            "TL1 Production Control",
            1,
            baseline.GetInt("hull_points"),
            baseline.GetInt("armor_integrity"),
            baseline.GetInt("armor_protection"),
            baseline.GetInt("shield_capacity"),
            baseline.GetInt("shield_base_recharge"),
            0,
            baseline.GetInt("reactor_output"),
            baseline.GetInt("targeting_accuracy_bonus"),
            effectivePds,
            baseline.GetInt("kinetic_pds_power"),
            baseline.GetInt("kinetic_power") + baseline.GetInt("kinetic_pds_power"),
            baseline.GetInt("stl_move"),
            baseline.GetInt("missile_speed"),
            new ScalingWeaponProfile(
                WeaponFamily.Kinetic,
                baseline.GetInt("kinetic_damage"),
                baseline.GetInt("kinetic_spen"),
                baseline.GetInt("kinetic_apen"),
                baseline.GetInt("kinetic_accuracy"),
                0,
                baseline.GetInt("kinetic_range"),
                baseline.GetInt("kinetic_power"),
                baseline.GetInt("kinetic_ammo")),
            new ScalingWeaponProfile(
                WeaponFamily.Energy,
                baseline.GetInt("energy_standard_damage"),
                baseline.GetInt("energy_spen"),
                baseline.GetInt("energy_apen"),
                baseline.GetInt("energy_accuracy"),
                0,
                baseline.GetInt("energy_range"),
                baseline.GetInt("energy_standard_power"),
                null),
            new ScalingWeaponProfile(
                WeaponFamily.Missile,
                baseline.GetInt("missile_warhead_damage"),
                baseline.GetInt("missile_warhead_spen"),
                baseline.GetInt("missile_warhead_apen"),
                0,
                baseline.GetInt("missile_guidance_hit"),
                baseline.GetInt("missile_range"),
                baseline.GetInt("missile_launch_power"),
                baseline.GetInt("missile_ammo")));
    }

    private static TechnologyCombatProfile BuildArchitectureProfile(
        ArchitectureRuntimeProfileDocument profile) => new(
        profile.Id,
        profile.Label,
        profile.TechnologyLevel,
        profile.Defense.Hull,
        profile.Defense.ArmorIntegrity,
        profile.Defense.ArmorProtection,
        profile.Defense.ShieldCapacity,
        profile.Defense.ShieldBaseRecharge,
        profile.Defense.ShieldArmor,
        profile.PowerAndControl.ReactorOutput,
        profile.PowerAndControl.TargetingBonus,
        profile.PowerAndControl.EffectivePdsChance,
        profile.PowerAndControl.PdsPower,
        profile.PowerAndControl.StandardCombatPowerCommitment,
        profile.Movement.ShipMove,
        profile.Movement.MissileMove,
        ScalingWeaponProfile.From(WeaponFamily.Kinetic, profile.Weapons.Kinetic),
        ScalingWeaponProfile.From(WeaponFamily.Energy, profile.Weapons.Energy),
        ScalingWeaponProfile.From(WeaponFamily.Missile, profile.Weapons.Missile));

    public static TechnologyCombatProfile BuildCandidate(
        Tl2CandidateDocument candidate) => new(
        candidate.Id,
        candidate.Label,
        2,
        candidate.Defense.Hull,
        candidate.Defense.ArmorIntegrity,
        candidate.Defense.ArmorProtection,
        candidate.Defense.ShieldCapacity,
        candidate.Defense.ShieldBaseRecharge,
        candidate.Defense.ShieldArmor,
        candidate.PowerAndControl.ReactorOutput,
        candidate.PowerAndControl.TargetingBonus,
        candidate.PowerAndControl.EffectivePdsChance,
        candidate.PowerAndControl.PdsPower,
        candidate.PowerAndControl.StandardCombatPowerCommitment,
        candidate.Movement.ShipMove,
        candidate.Movement.MissileMove,
        ScalingWeaponProfile.From(WeaponFamily.Kinetic, candidate.Weapons.Kinetic),
        ScalingWeaponProfile.From(WeaponFamily.Energy, candidate.Weapons.Energy),
        ScalingWeaponProfile.From(WeaponFamily.Missile, candidate.Weapons.Missile));

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = false,
        Converters = { new JsonStringEnumConverter() },
    };
}

internal sealed class ArchitectureRuntimeProfileCatalogDocument
{
    public const string SchemaVersion =
        "star-cluster-architecture-runtime-profile-catalog-v1";

    [JsonPropertyName("schemaVersion")]
    public string Schema { get; set; } = string.Empty;

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("profiles")]
    public List<ArchitectureRuntimeProfileDocument> Profiles { get; set; } = new();
}

internal sealed class ArchitectureRuntimeProfileDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("label")]
    public string Label { get; set; } = string.Empty;

    [JsonPropertyName("technologyLevel")]
    public int TechnologyLevel { get; set; }

    [JsonPropertyName("defense")]
    public CandidateDefenseDocument Defense { get; set; } = new();

    [JsonPropertyName("powerAndControl")]
    public CandidatePowerAndControlDocument PowerAndControl { get; set; } = new();

    [JsonPropertyName("movement")]
    public CandidateMovementDocument Movement { get; set; } = new();

    [JsonPropertyName("weapons")]
    public CandidateWeaponsDocument Weapons { get; set; } = new();
}
