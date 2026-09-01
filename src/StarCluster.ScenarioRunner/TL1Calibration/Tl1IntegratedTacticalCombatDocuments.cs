using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.ScenarioRunner.TL1Calibration;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1IntegratedMovementMode
{
    HoldRange2,
    HoldRange3,
    HoldRange4,
    HoldRange5,
    ScriptedPursuit,
    PreferredRange,
    OpponentAwareRange,
    TrackAwareOpponentRange,
    EngageAdaptive,
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1IntegratedDamageControlMode
{
    None,
    ComponentFirstReserveOne,
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1TacticalPowerDoctrine
{
    DefenseFirst,
    PrimaryFireFirst,
    FullVolleyFirst,
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1OperationalTrackPolicy
{
    EstablishedFirm,
    PassiveOnly,
    AutoActive,
    AcquisitionFirstAutoActive,
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1IntegratedMovementOrder
{
    Simultaneous,
    SideAFirst,
    SideBFirst,
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1IntegratedStlOverloadPolicy
{
    None,
    SafeRangePressure,
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1IntegratedSensorOverloadPolicy
{
    None,
    SafeWhenNeeded,
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum Tl1IntegratedEwPowerPolicy
{
    None,
    Normal,
    ReactiveNormal,
    SafeOverload,
}

public sealed class Tl1IntegratedTacticalCombatStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } =
        "star-cluster-tl1-integrated-tactical-combat-v2";

    [JsonPropertyName("id")]
    public string Id { get; set; } =
        "tl1-itc01-cross-family-dynamic-range";

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("masterSeed")]
    public ulong MasterSeed { get; set; } = 390100UL;

    [JsonPropertyName("trialsPerVariant")]
    public int TrialsPerVariant { get; set; } = 10000;

    [JsonPropertyName("technologyProfileCatalog")]
    public string? TechnologyProfileCatalog { get; set; }

    [JsonPropertyName("auxiliaryProfileCatalog")]
    public string? AuxiliaryProfileCatalog { get; set; }

    [JsonPropertyName("sensorEwProfileCatalog")]
    public string? SensorEwProfileCatalog { get; set; }

    [JsonPropertyName("aiDoctrineCatalog")]
    public string? AiDoctrineCatalog { get; set; }

    [JsonPropertyName("builds")]
    public List<Tl1IntegratedShipBuildDocument> Builds { get; set; } = new();

    [JsonPropertyName("variants")]
    public List<Tl1IntegratedTacticalCombatVariantDocument> Variants { get; set; } = new();
}

public sealed class Tl1IntegratedShipBuildDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("mainWeaponCount")]
    public int MainWeaponCount { get; set; } = 1;

    [JsonPropertyName("mainReactorCount")]
    public int MainReactorCount { get; set; } = 1;

    [JsonPropertyName("activeSensor")]
    public bool ActiveSensor { get; set; } = true;

    [JsonPropertyName("shieldGenerator")]
    public bool ShieldGenerator { get; set; } = true;

    [JsonPropertyName("kineticPdsCount")]
    public int KineticPdsCount { get; set; }

    [JsonPropertyName("pdsFamily")]
    public string? PdsFamily { get; set; }

    [JsonPropertyName("pdsBaseChance")]
    public int? PdsBaseChance { get; set; }

    [JsonPropertyName("pdsPowerCost")]
    public int? PdsPowerCost { get; set; }

    [JsonPropertyName("pdsReactionCapacity")]
    public int? PdsReactionCapacity { get; set; }

    [JsonPropertyName("pdsFallbackPowerCost")]
    public int? PdsFallbackPowerCost { get; set; }

    [JsonPropertyName("pdsFallbackReactionCapacity")]
    public int? PdsFallbackReactionCapacity { get; set; }

    [JsonPropertyName("pdsAmmunition")]
    public int? PdsAmmunition { get; set; }

    [JsonPropertyName("shieldHardener")]
    public bool ShieldHardener { get; set; }

    [JsonPropertyName("shieldHardenerArmor")]
    public int ShieldHardenerArmor { get; set; }

    [JsonPropertyName("shieldHardenerPowerCost")]
    public int ShieldHardenerPowerCost { get; set; }

    [JsonPropertyName("tacticalComputerEvasiveCompensation")]
    public int TacticalComputerEvasiveCompensation { get; set; }

    [JsonPropertyName("standardOnboardMissileNavigationSensor")]
    public bool StandardOnboardMissileNavigationSensor { get; set; }

    [JsonPropertyName("ftlStrategicMove")]
    public int? FtlStrategicMove { get; set; }

    [JsonPropertyName("ecmSuite")]
    public bool EcmSuite { get; set; }

    [JsonPropertyName("ecmSuiteRatings")]
    public List<int> EcmSuiteRatings { get; set; } = new();

    [JsonPropertyName("eccmSuite")]
    public bool EccmSuite { get; set; }

    [JsonPropertyName("eccmSuiteRatings")]
    public List<int> EccmSuiteRatings { get; set; } = new();

    [JsonPropertyName("usedSpace")]
    public int UsedSpace { get; set; }

    [JsonPropertyName("freeSupportSpace")]
    public int FreeSupportSpace { get; set; }

    [JsonPropertyName("advancedComponentCount")]
    public int? AdvancedComponentCount { get; set; }

    [JsonPropertyName("crossTlCompositionClass")]
    public string? CrossTlCompositionClass { get; set; }
}


public sealed class Tl1IntegratedTacticalCombatVariantDocument
{
    [JsonPropertyName("sideABuildId")]
    public string? SideABuildId { get; set; }

    [JsonPropertyName("sideBBuildId")]
    public string? SideBBuildId { get; set; }

    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("comparisonGroup")]
    public string? ComparisonGroup { get; set; }

    [JsonPropertyName("profileLabel")]
    public string? ProfileLabel { get; set; }

    [JsonPropertyName("sideAEngagementReadinessClass")]
    public string? SideAEngagementReadinessClass { get; set; }

    [JsonPropertyName("sideBEngagementReadinessClass")]
    public string? SideBEngagementReadinessClass { get; set; }

    [JsonPropertyName("sideAMaximumReadyRangeHexes")]
    public int? SideAMaximumReadyRangeHexes { get; set; }

    [JsonPropertyName("sideBMaximumReadyRangeHexes")]
    public int? SideBMaximumReadyRangeHexes { get; set; }

    [JsonPropertyName("sideAProfileId")]
    public string? SideAProfileId { get; set; }

    [JsonPropertyName("sideBProfileId")]
    public string? SideBProfileId { get; set; }

    [JsonPropertyName("sideAAuxiliaryProfileId")]
    public string? SideAAuxiliaryProfileId { get; set; }

    [JsonPropertyName("sideBAuxiliaryProfileId")]
    public string? SideBAuxiliaryProfileId { get; set; }

    [JsonPropertyName("sideAFamily")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public WeaponFamily SideAFamily { get; set; }

    [JsonPropertyName("sideBFamily")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public WeaponFamily SideBFamily { get; set; }

    [JsonPropertyName("sideASecondaryFamily")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public WeaponFamily? SideASecondaryFamily { get; set; }

    [JsonPropertyName("sideBSecondaryFamily")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public WeaponFamily? SideBSecondaryFamily { get; set; }

    [JsonPropertyName("movementMode")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedMovementMode MovementMode { get; set; }

    [JsonPropertyName("initialRangeHexes")]
    public int? InitialRangeHexes { get; set; }

    [JsonPropertyName("protectedCompartmentation")]
    public bool ProtectedCompartmentation { get; set; }

    [JsonPropertyName("damageControl")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedDamageControlMode DamageControl { get; set; }

    [JsonPropertyName("sideAStlMovementHexes")]
    public int? SideAStlMovementHexes { get; set; }

    [JsonPropertyName("sideBStlMovementHexes")]
    public int? SideBStlMovementHexes { get; set; }

    [JsonPropertyName("missileSpeedHexesPerTurn")]
    public int? MissileSpeedHexesPerTurn { get; set; }

    [JsonPropertyName("sideAMissileSpeedHexesPerTurnOverride")]
    public int? SideAMissileSpeedHexesPerTurnOverride { get; set; }

    [JsonPropertyName("sideBMissileSpeedHexesPerTurnOverride")]
    public int? SideBMissileSpeedHexesPerTurnOverride { get; set; }

    [JsonPropertyName("missileMaximumTravelHexes")]
    public int? MissileMaximumTravelHexes { get; set; }

    [JsonPropertyName("kineticDamage")]
    public int? KineticDamage { get; set; }

    [JsonPropertyName("kineticArmorPenetration")]
    public int? KineticArmorPenetration { get; set; }

    [JsonPropertyName("primaryArmorProtection")]
    public int? PrimaryArmorProtection { get; set; }

    [JsonPropertyName("baseShieldRechargeEnabled")]
    public bool? BaseShieldRechargeEnabled { get; set; }

    [JsonPropertyName("evasiveManeuversEnabled")]
    public bool? EvasiveManeuversEnabled { get; set; }

    [JsonPropertyName("pdsEnabled")]
    public bool? PdsEnabled { get; set; }

    [JsonPropertyName("escapeDisengagementEnabled")]
    public bool? EscapeDisengagementEnabled { get; set; }

    [JsonPropertyName("sideABackgroundTacticalPowerCommitment")]
    public int SideABackgroundTacticalPowerCommitment { get; set; }

    [JsonPropertyName("sideBBackgroundTacticalPowerCommitment")]
    public int SideBBackgroundTacticalPowerCommitment { get; set; }


    [JsonPropertyName("sideATacticalPowerDoctrine")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1TacticalPowerDoctrine SideATacticalPowerDoctrine { get; set; } =
        Tl1TacticalPowerDoctrine.DefenseFirst;

    [JsonPropertyName("sideBTacticalPowerDoctrine")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1TacticalPowerDoctrine SideBTacticalPowerDoctrine { get; set; } =
        Tl1TacticalPowerDoctrine.DefenseFirst;

    [JsonPropertyName("sideAReactorOutputOverride")]
    public int? SideAReactorOutputOverride { get; set; }

    [JsonPropertyName("sideBReactorOutputOverride")]
    public int? SideBReactorOutputOverride { get; set; }

    [JsonPropertyName("sideAPrimaryWeaponDamageOverride")]
    public int? SideAPrimaryWeaponDamageOverride { get; set; }

    [JsonPropertyName("sideBPrimaryWeaponDamageOverride")]
    public int? SideBPrimaryWeaponDamageOverride { get; set; }

    [JsonPropertyName("sideAPrimaryWeaponPowerCostOverride")]
    public int? SideAPrimaryWeaponPowerCostOverride { get; set; }

    [JsonPropertyName("sideBPrimaryWeaponPowerCostOverride")]
    public int? SideBPrimaryWeaponPowerCostOverride { get; set; }

    [JsonPropertyName("sideAPrimaryWeaponAccuracyBonusOverride")]
    public int? SideAPrimaryWeaponAccuracyBonusOverride { get; set; }

    [JsonPropertyName("sideBPrimaryWeaponAccuracyBonusOverride")]
    public int? SideBPrimaryWeaponAccuracyBonusOverride { get; set; }

    [JsonPropertyName("sideAShieldCapacityOverride")]
    public int? SideAShieldCapacityOverride { get; set; }

    [JsonPropertyName("sideBShieldCapacityOverride")]
    public int? SideBShieldCapacityOverride { get; set; }

    [JsonPropertyName("sideAPrimaryArmorIntegrityOverride")]
    public int? SideAPrimaryArmorIntegrityOverride { get; set; }

    [JsonPropertyName("sideBPrimaryArmorIntegrityOverride")]
    public int? SideBPrimaryArmorIntegrityOverride { get; set; }

    [JsonPropertyName("sideAPrimaryArmorProtectionOverride")]
    public int? SideAPrimaryArmorProtectionOverride { get; set; }

    [JsonPropertyName("sideBPrimaryArmorProtectionOverride")]
    public int? SideBPrimaryArmorProtectionOverride { get; set; }

    [JsonPropertyName("sideAWeaponShieldPenetrationOverride")]
    public int? SideAWeaponShieldPenetrationOverride { get; set; }

    [JsonPropertyName("sideBWeaponShieldPenetrationOverride")]
    public int? SideBWeaponShieldPenetrationOverride { get; set; }

    [JsonPropertyName("sideAWeaponArmorPenetrationOverride")]
    public int? SideAWeaponArmorPenetrationOverride { get; set; }

    [JsonPropertyName("sideBWeaponArmorPenetrationOverride")]
    public int? SideBWeaponArmorPenetrationOverride { get; set; }

    [JsonPropertyName("sideATacticalComputerTargetingBonusOverride")]
    public int? SideATacticalComputerTargetingBonusOverride { get; set; }

    [JsonPropertyName("sideBTacticalComputerTargetingBonusOverride")]
    public int? SideBTacticalComputerTargetingBonusOverride { get; set; }

    [JsonPropertyName("sideATrackPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1OperationalTrackPolicy SideATrackPolicy { get; set; } =
        Tl1OperationalTrackPolicy.EstablishedFirm;

    [JsonPropertyName("sideBTrackPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1OperationalTrackPolicy SideBTrackPolicy { get; set; } =
        Tl1OperationalTrackPolicy.EstablishedFirm;

    [JsonPropertyName("sideANetEwRangePenalty")]
    public int SideANetEwRangePenalty { get; set; }

    [JsonPropertyName("sideBNetEwRangePenalty")]
    public int SideBNetEwRangePenalty { get; set; }

    [JsonPropertyName("sideASensorPassiveFirmRangeOverride")]
    public int? SideASensorPassiveFirmRangeOverride { get; set; }

    [JsonPropertyName("sideASensorPassiveApproximateRangeOverride")]
    public int? SideASensorPassiveApproximateRangeOverride { get; set; }

    [JsonPropertyName("sideASensorActiveLowFirmRangeOverride")]
    public int? SideASensorActiveLowFirmRangeOverride { get; set; }

    [JsonPropertyName("sideASensorActiveLowApproximateRangeOverride")]
    public int? SideASensorActiveLowApproximateRangeOverride { get; set; }

    [JsonPropertyName("sideASensorActiveLowPowerCostOverride")]
    public int? SideASensorActiveLowPowerCostOverride { get; set; }

    [JsonPropertyName("sideASensorActiveHighFirmRangeOverride")]
    public int? SideASensorActiveHighFirmRangeOverride { get; set; }

    [JsonPropertyName("sideASensorActiveHighApproximateRangeOverride")]
    public int? SideASensorActiveHighApproximateRangeOverride { get; set; }

    [JsonPropertyName("sideASensorActiveHighPowerCostOverride")]
    public int? SideASensorActiveHighPowerCostOverride { get; set; }

    [JsonPropertyName("sideBSensorPassiveFirmRangeOverride")]
    public int? SideBSensorPassiveFirmRangeOverride { get; set; }

    [JsonPropertyName("sideBSensorPassiveApproximateRangeOverride")]
    public int? SideBSensorPassiveApproximateRangeOverride { get; set; }

    [JsonPropertyName("sideBSensorActiveLowFirmRangeOverride")]
    public int? SideBSensorActiveLowFirmRangeOverride { get; set; }

    [JsonPropertyName("sideBSensorActiveLowApproximateRangeOverride")]
    public int? SideBSensorActiveLowApproximateRangeOverride { get; set; }

    [JsonPropertyName("sideBSensorActiveLowPowerCostOverride")]
    public int? SideBSensorActiveLowPowerCostOverride { get; set; }

    [JsonPropertyName("sideBSensorActiveHighFirmRangeOverride")]
    public int? SideBSensorActiveHighFirmRangeOverride { get; set; }

    [JsonPropertyName("sideBSensorActiveHighApproximateRangeOverride")]
    public int? SideBSensorActiveHighApproximateRangeOverride { get; set; }

    [JsonPropertyName("sideBSensorActiveHighPowerCostOverride")]
    public int? SideBSensorActiveHighPowerCostOverride { get; set; }

    [JsonPropertyName("sensorEwProfileId")]
    public string? SensorEwProfileId { get; set; }

    [JsonPropertyName("sideASensorEwProfileId")]
    public string? SideASensorEwProfileId { get; set; }

    [JsonPropertyName("sideBSensorEwProfileId")]
    public string? SideBSensorEwProfileId { get; set; }

    [JsonPropertyName("sideAStlOverloadPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedStlOverloadPolicy SideAStlOverloadPolicy { get; set; } =
        Tl1IntegratedStlOverloadPolicy.None;

    [JsonPropertyName("sideBStlOverloadPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedStlOverloadPolicy SideBStlOverloadPolicy { get; set; } =
        Tl1IntegratedStlOverloadPolicy.None;

    [JsonPropertyName("sideASensorOverloadPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedSensorOverloadPolicy SideASensorOverloadPolicy { get; set; } =
        Tl1IntegratedSensorOverloadPolicy.None;

    [JsonPropertyName("sideBSensorOverloadPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedSensorOverloadPolicy SideBSensorOverloadPolicy { get; set; } =
        Tl1IntegratedSensorOverloadPolicy.None;

    [JsonPropertyName("sideAAiDoctrineId")]
    public string? SideAAiDoctrineId { get; set; }

    [JsonPropertyName("sideBAiDoctrineId")]
    public string? SideBAiDoctrineId { get; set; }

    [JsonPropertyName("sideAEcmPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedEwPowerPolicy SideAEcmPolicy { get; set; } =
        Tl1IntegratedEwPowerPolicy.None;

    [JsonPropertyName("sideBEcmPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedEwPowerPolicy SideBEcmPolicy { get; set; } =
        Tl1IntegratedEwPowerPolicy.None;

    [JsonPropertyName("sideAEccmPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedEwPowerPolicy SideAEccmPolicy { get; set; } =
        Tl1IntegratedEwPowerPolicy.None;

    [JsonPropertyName("sideBEccmPolicy")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedEwPowerPolicy SideBEccmPolicy { get; set; } =
        Tl1IntegratedEwPowerPolicy.None;

    [JsonPropertyName("sideAEcmNormalPowerCostOverride")]
    public int? SideAEcmNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideBEcmNormalPowerCostOverride")]
    public int? SideBEcmNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideAEccmNormalPowerCostOverride")]
    public int? SideAEccmNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideBEccmNormalPowerCostOverride")]
    public int? SideBEccmNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideAEcmFullStrengthNormalPowerCostOverride")]
    public int? SideAEcmFullStrengthNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideBEcmFullStrengthNormalPowerCostOverride")]
    public int? SideBEcmFullStrengthNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideAEccmFullStrengthNormalPowerCostOverride")]
    public int? SideAEccmFullStrengthNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideBEccmFullStrengthNormalPowerCostOverride")]
    public int? SideBEccmFullStrengthNormalPowerCostOverride { get; set; }

    [JsonPropertyName("sideAEcmNormalRatingOverride")]
    public int? SideAEcmNormalRatingOverride { get; set; }

    [JsonPropertyName("sideBEcmNormalRatingOverride")]
    public int? SideBEcmNormalRatingOverride { get; set; }

    [JsonPropertyName("sideAEccmNormalRatingOverride")]
    public int? SideAEccmNormalRatingOverride { get; set; }

    [JsonPropertyName("sideBEccmNormalRatingOverride")]
    public int? SideBEccmNormalRatingOverride { get; set; }

    [JsonPropertyName("sideAAllowsApproximateDirectFire")]
    public bool SideAAllowsApproximateDirectFire { get; set; }

    [JsonPropertyName("sideBAllowsApproximateDirectFire")]
    public bool SideBAllowsApproximateDirectFire { get; set; }

    [JsonPropertyName("sideAApproximateDirectFireAccuracyPenalty")]
    public int SideAApproximateDirectFireAccuracyPenalty { get; set; }

    [JsonPropertyName("sideBApproximateDirectFireAccuracyPenalty")]
    public int SideBApproximateDirectFireAccuracyPenalty { get; set; }

    [JsonPropertyName("tacticalMapRadius")]
    public int? TacticalMapRadius { get; set; }

    [JsonPropertyName("movementOrder")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1IntegratedMovementOrder MovementOrder { get; set; } =
        Tl1IntegratedMovementOrder.Simultaneous;

    [JsonPropertyName("startingFuel")]
    public int? StartingFuel { get; set; }

    [JsonPropertyName("movementFuelPerHex")]
    public int? MovementFuelPerHex { get; set; }

    [JsonPropertyName("evasiveManeuverFuelCost")]
    public int? EvasiveManeuverFuelCost { get; set; }
}
