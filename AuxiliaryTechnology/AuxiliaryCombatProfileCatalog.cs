using System.Text.Json;
using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.AuxiliaryTechnology;

internal static class AuxiliaryCombatProfileCatalog
{
    private const string ExpectedSchemaVersion =
        "star-cluster-auxiliary-combat-screening-catalog-v1";

    public static IReadOnlyDictionary<string, AuxiliaryCombatProfile> Load(
        string path)
    {
        AuxiliaryCombatProfileCatalogDocument document =
            JsonSerializer.Deserialize<AuxiliaryCombatProfileCatalogDocument>(
                File.ReadAllText(path),
                JsonOptions()) ?? throw new InvalidOperationException(
                "Auxiliary combat profile catalog could not be read.");
        if (!string.Equals(
                document.SchemaVersion,
                ExpectedSchemaVersion,
                StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "Unexpected Auxiliary combat profile catalog schema.");
        }
        var profiles = new Dictionary<string, AuxiliaryCombatProfile>(
            StringComparer.Ordinal)
        {
            [AuxiliaryCombatProfile.Legacy.Id] = AuxiliaryCombatProfile.Legacy,
        };
        foreach (AuxiliaryCombatProfileDocument profile in document.Profiles)
        {
            AuxiliaryCombatProfile built = profile.ToProfile();
            if (!profiles.TryAdd(built.Id, built))
            {
                throw new InvalidOperationException(
                    $"Duplicate Auxiliary combat profile ID '{built.Id}'.");
            }
        }
        return profiles;
    }

    public static IReadOnlyDictionary<string, AuxiliaryCombatProfile> LegacyOnly() =>
        new Dictionary<string, AuxiliaryCombatProfile>(StringComparer.Ordinal)
        {
            [AuxiliaryCombatProfile.Legacy.Id] = AuxiliaryCombatProfile.Legacy,
        };

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = false,
        Converters = { new JsonStringEnumConverter() },
    };
}

internal sealed class AuxiliaryCombatProfileCatalogDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } = string.Empty;

    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("checkpoint")]
    public int Checkpoint { get; set; }

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("profiles")]
    public List<AuxiliaryCombatProfileDocument> Profiles { get; set; } = new();
}

internal sealed class AuxiliaryCombatProfileDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("familyId")] public string FamilyId { get; set; } = string.Empty;
    [JsonPropertyName("displayName")] public string DisplayName { get; set; } = string.Empty;
    [JsonPropertyName("technologyLevel")] public int TechnologyLevel { get; set; }
    [JsonPropertyName("capacityCost")] public int CapacityCost { get; set; }
    [JsonPropertyName("valuationClass")] public string ValuationClass { get; set; } = string.Empty;
    [JsonPropertyName("counterfactual")] public bool Counterfactual { get; set; }
    [JsonPropertyName("pdsBaseChance")] public int PdsBaseChance { get; set; }
    [JsonPropertyName("pdsPower")] public int PdsPower { get; set; }
    [JsonPropertyName("pdsAmmunition")] public int? PdsAmmunition { get; set; }
    [JsonPropertyName("auxiliaryReactorOutput")] public int AuxiliaryReactorOutput { get; set; }
    [JsonPropertyName("combatBatteryGain")] public int CombatBatteryGain { get; set; }
    [JsonPropertyName("combatBatteryCharges")] public int CombatBatteryCharges { get; set; }
    [JsonPropertyName("capacitorCapacity")] public int CapacitorCapacity { get; set; }
    [JsonPropertyName("capacitorChargeRate")] public int CapacitorChargeRate { get; set; }
    [JsonPropertyName("capacitorDischargeRate")] public int CapacitorDischargeRate { get; set; }
    [JsonPropertyName("shieldBatteryRestore")] public int ShieldBatteryRestore { get; set; }
    [JsonPropertyName("shieldBatteryCharges")] public int ShieldBatteryCharges { get; set; }
    [JsonPropertyName("shieldCapacityBonus")] public int ShieldCapacityBonus { get; set; }
    [JsonPropertyName("shieldRechargePerPower")] public int ShieldRechargePerPower { get; set; }
    [JsonPropertyName("shieldRechargePowerCap")] public int ShieldRechargePowerCap { get; set; }
    [JsonPropertyName("shieldHardenerStrength")] public int ShieldHardenerStrength { get; set; }
    [JsonPropertyName("shieldHardenerPower")] public int ShieldHardenerPower { get; set; }
    [JsonPropertyName("energizedArmorProtectionBonus")] public int EnergizedArmorProtectionBonus { get; set; }
    [JsonPropertyName("energizedArmorPower")] public int EnergizedArmorPower { get; set; }
    [JsonPropertyName("ablativeProtection")] public int AblativeProtection { get; set; }
    [JsonPropertyName("ablativeIntegrity")] public int AblativeIntegrity { get; set; }
    [JsonPropertyName("evasiveManeuvers")] public bool EvasiveManeuvers { get; set; }
    [JsonPropertyName("damageControlChanceBonus")] public int DamageControlChanceBonus { get; set; }
    [JsonPropertyName("extraRepairKits")] public int ExtraRepairKits { get; set; }
    [JsonPropertyName("kineticAmmunitionBonus")] public int KineticAmmunitionBonus { get; set; }
    [JsonPropertyName("missileAmmunitionBonus")] public int MissileAmmunitionBonus { get; set; }
    [JsonPropertyName("powerComponents")] public List<AuxiliaryPowerComponentDocument> PowerComponents { get; set; } = new();

    public AuxiliaryCombatProfile ToProfile()
    {
        if (string.IsNullOrWhiteSpace(Id) || string.IsNullOrWhiteSpace(FamilyId) ||
            string.IsNullOrWhiteSpace(DisplayName) || TechnologyLevel is < 1 or > 9 ||
            CapacityCost is < 0 or > 3 || PdsBaseChance is < 0 or > 100 ||
            PdsPower < 0 || PdsAmmunition is < 0 || AuxiliaryReactorOutput < 0 ||
            CombatBatteryGain < 0 || CombatBatteryCharges < 0 ||
            CapacitorCapacity < 0 || CapacitorChargeRate < 0 ||
            CapacitorDischargeRate < 0 ||
            ShieldBatteryRestore < 0 || ShieldBatteryCharges < 0 ||
            ShieldCapacityBonus < 0 || ShieldRechargePerPower < 0 ||
            ShieldRechargePowerCap < 0 || ShieldHardenerStrength < 0 ||
            ShieldHardenerPower < 0 || EnergizedArmorProtectionBonus < 0 ||
            EnergizedArmorPower < 0 ||
            (ShieldHardenerStrength > 0) != (ShieldHardenerPower > 0) ||
            (EnergizedArmorProtectionBonus > 0) != (EnergizedArmorPower > 0) ||
            AblativeProtection < 0 ||
            AblativeIntegrity < 0 || DamageControlChanceBonus is < 0 or > 50 ||
            ExtraRepairKits < 0 || KineticAmmunitionBonus < 0 ||
            MissileAmmunitionBonus < 0)
        {
            throw new InvalidOperationException(
                $"Auxiliary combat profile '{Id}' contains invalid values.");
        }
        AuxiliaryPowerComponentProfile[] powerComponents = PowerComponents
            .Select(component => component.ToProfile())
            .ToArray();
        if (powerComponents.Select(component => component.Id)
            .Distinct(StringComparer.Ordinal).Count() != powerComponents.Length)
        {
            throw new InvalidOperationException(
                $"Auxiliary combat profile '{Id}' contains duplicate power-component IDs.");
        }
        if (powerComponents.Length > CapacityCost)
        {
            throw new InvalidOperationException(
                $"Auxiliary combat profile '{Id}' contains more independent power components than its AUX capacity cost.");
        }

        return new AuxiliaryCombatProfile(
            Id,
            FamilyId,
            DisplayName,
            TechnologyLevel,
            CapacityCost,
            ValuationClass,
            Counterfactual,
            false,
            PdsBaseChance,
            PdsPower,
            PdsAmmunition,
            AuxiliaryReactorOutput,
            CombatBatteryGain,
            CombatBatteryCharges,
            CapacitorCapacity,
            CapacitorChargeRate,
            CapacitorDischargeRate,
            ShieldBatteryRestore,
            ShieldBatteryCharges,
            ShieldCapacityBonus,
            ShieldRechargePerPower,
            ShieldRechargePowerCap,
            ShieldHardenerStrength,
            ShieldHardenerPower,
            EnergizedArmorProtectionBonus,
            EnergizedArmorPower,
            AblativeProtection,
            AblativeIntegrity,
            EvasiveManeuvers,
            DamageControlChanceBonus,
            ExtraRepairKits,
            KineticAmmunitionBonus,
            MissileAmmunitionBonus,
            powerComponents);
    }
}

internal enum AuxiliaryPowerComponentKind
{
    CombatBattery,
    PowerCapacitor,
}

internal sealed class AuxiliaryPowerComponentDocument
{
    [JsonPropertyName("id")] public string Id { get; set; } = string.Empty;
    [JsonPropertyName("kind")] public AuxiliaryPowerComponentKind Kind { get; set; }
    [JsonPropertyName("combatBatteryGain")] public int CombatBatteryGain { get; set; }
    [JsonPropertyName("combatBatteryCharges")] public int CombatBatteryCharges { get; set; }
    [JsonPropertyName("capacitorCapacity")] public int CapacitorCapacity { get; set; }
    [JsonPropertyName("capacitorChargeRate")] public int CapacitorChargeRate { get; set; }
    [JsonPropertyName("capacitorDischargeRate")] public int CapacitorDischargeRate { get; set; }

    public AuxiliaryPowerComponentProfile ToProfile()
    {
        if (string.IsNullOrWhiteSpace(Id))
        {
            throw new InvalidOperationException(
                "Independent AUX power components require stable IDs.");
        }
        bool valid = Kind switch
        {
            AuxiliaryPowerComponentKind.CombatBattery =>
                CombatBatteryGain > 0 && CombatBatteryCharges > 0 &&
                CapacitorCapacity == 0 && CapacitorChargeRate == 0 &&
                CapacitorDischargeRate == 0,
            AuxiliaryPowerComponentKind.PowerCapacitor =>
                CombatBatteryGain == 0 && CombatBatteryCharges == 0 &&
                CapacitorCapacity > 0 && CapacitorChargeRate > 0 &&
                CapacitorDischargeRate > 0 &&
                CapacitorDischargeRate <= CapacitorCapacity,
            _ => false,
        };
        if (!valid)
        {
            throw new InvalidOperationException(
                $"Independent AUX power component '{Id}' contains invalid values for {Kind}.");
        }
        return new AuxiliaryPowerComponentProfile(
            Id, Kind, CombatBatteryGain, CombatBatteryCharges,
            CapacitorCapacity, CapacitorChargeRate, CapacitorDischargeRate);
    }
}

internal sealed record AuxiliaryPowerComponentProfile(
    string Id,
    AuxiliaryPowerComponentKind Kind,
    int CombatBatteryGain,
    int CombatBatteryCharges,
    int CapacitorCapacity,
    int CapacitorChargeRate,
    int CapacitorDischargeRate);

internal sealed record AuxiliaryCombatProfile(
    string Id,
    string FamilyId,
    string DisplayName,
    int TechnologyLevel,
    int CapacityCost,
    string ValuationClass,
    bool Counterfactual,
    bool LegacyIntegratedSuite,
    int PdsBaseChance,
    int PdsPower,
    int? PdsAmmunition,
    int AuxiliaryReactorOutput,
    int CombatBatteryGain,
    int CombatBatteryCharges,
    int CapacitorCapacity,
    int CapacitorChargeRate,
    int CapacitorDischargeRate,
    int ShieldBatteryRestore,
    int ShieldBatteryCharges,
    int ShieldCapacityBonus,
    int ShieldRechargePerPower,
    int ShieldRechargePowerCap,
    int ShieldHardenerStrength,
    int ShieldHardenerPower,
    int EnergizedArmorProtectionBonus,
    int EnergizedArmorPower,
    int AblativeProtection,
    int AblativeIntegrity,
    bool EvasiveManeuvers,
    int DamageControlChanceBonus,
    int ExtraRepairKits,
    int KineticAmmunitionBonus,
    int MissileAmmunitionBonus,
    IReadOnlyList<AuxiliaryPowerComponentProfile> PowerComponents)
{
    public const string LegacyId = "legacy-integrated-aux-suite";

    public static AuxiliaryCombatProfile Legacy { get; } = new(
        Id: LegacyId,
        FamilyId: LegacyId,
        DisplayName: "Legacy Integrated Calibration Suite",
        TechnologyLevel: 1,
        CapacityCost: 0,
        ValuationClass: "legacy_calibration",
        Counterfactual: true,
        LegacyIntegratedSuite: true,
        PdsBaseChance: 0,
        PdsPower: 0,
        PdsAmmunition: null,
        AuxiliaryReactorOutput: 1,
        CombatBatteryGain: 0,
        CombatBatteryCharges: 0,
        CapacitorCapacity: 0,
        CapacitorChargeRate: 0,
        CapacitorDischargeRate: 0,
        ShieldBatteryRestore: 0,
        ShieldBatteryCharges: 0,
        ShieldCapacityBonus: 0,
        ShieldRechargePerPower: 0,
        ShieldRechargePowerCap: 0,
        ShieldHardenerStrength: 0,
        ShieldHardenerPower: 0,
        EnergizedArmorProtectionBonus: 0,
        EnergizedArmorPower: 0,
        AblativeProtection: 0,
        AblativeIntegrity: 0,
        EvasiveManeuvers: true,
        DamageControlChanceBonus: 0,
        ExtraRepairKits: 0,
        KineticAmmunitionBonus: 0,
        MissileAmmunitionBonus: 0,
        PowerComponents: Array.Empty<AuxiliaryPowerComponentProfile>());

    public bool HasPds => LegacyIntegratedSuite || PdsBaseChance > 0;
    public bool HasAuxiliaryReactor => LegacyIntegratedSuite || AuxiliaryReactorOutput > 0;
    public bool HasIndependentPowerComponents => PowerComponents.Count > 0;
    public bool HasCombatBattery =>
        (CombatBatteryGain > 0 && CombatBatteryCharges > 0) ||
        PowerComponents.Any(component =>
            component.Kind == AuxiliaryPowerComponentKind.CombatBattery);
    public bool HasPowerCapacitor =>
        (CapacitorCapacity > 0 && CapacitorDischargeRate > 0) ||
        PowerComponents.Any(component =>
            component.Kind == AuxiliaryPowerComponentKind.PowerCapacitor);
    public bool HasShieldBattery => ShieldBatteryRestore > 0 && ShieldBatteryCharges > 0;
    public bool HasShieldBooster => ShieldCapacityBonus > 0;
    public bool HasShieldStabilizer =>
        ShieldRechargePerPower > 0 && ShieldRechargePowerCap > 0;
    public bool HasShieldHardener => ShieldHardenerStrength > 0 && ShieldHardenerPower > 0;
    public bool HasEnergizedArmor => EnergizedArmorProtectionBonus > 0 && EnergizedArmorPower > 0;
    public bool HasAblativeArmor => AblativeIntegrity > 0;
    public bool HasRepairDrones => DamageControlChanceBonus > 0 || ExtraRepairKits > 0;
    public bool HasLegacySelectedPowerComponent =>
        !HasIndependentPowerComponents &&
        ((CombatBatteryGain > 0 && CombatBatteryCharges > 0) ||
         (CapacitorCapacity > 0 && CapacitorDischargeRate > 0));
    public bool UsesSelectedComponent => HasLegacySelectedPowerComponent ||
        HasShieldBattery || HasShieldBooster || HasShieldStabilizer ||
        HasShieldHardener || HasEnergizedArmor || HasRepairDrones;
}
