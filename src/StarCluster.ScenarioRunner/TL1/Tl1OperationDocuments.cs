using System.Text.Json;

namespace StarCluster.ScenarioRunner.TL1;

public sealed class Tl1ArmorLayerFixture
{
    public string Id { get; set; } = "armor-1";

    public int? PristineProtection { get; set; }

    public int? CurrentProtection { get; set; }

    public int? PristineIntegrity { get; set; }

    public int? CurrentIntegrity { get; set; }
}

public sealed class Tl1DefenseFixture
{
    public int? PristineShieldCapacity { get; set; }

    public int? CurrentShieldCapacity { get; set; }

    public int ShieldArmor { get; set; }

    public int TemporaryShieldOvercapacity { get; set; }

    public List<Tl1ArmorLayerFixture>? ArmorLayers { get; set; }

    public int? PristineHull { get; set; }

    public int? CurrentHull { get; set; }
}

public sealed class Tl1AttackPacketFixture
{
    public int Damage { get; set; }

    public int ShieldPenetration { get; set; }

    public int ArmorPenetration { get; set; }
}

public sealed class Tl1ResolveDamageInput
{
    public Tl1DefenseFixture Defense { get; set; } = new();

    public Tl1AttackPacketFixture Packet { get; set; } = new();
}

public sealed class Tl1TurnStartRechargeInput
{
    public Tl1DefenseFixture Defense { get; set; } = new();

    public string ShieldCondition { get; set; } = "operational";

    public string ReactorCondition { get; set; } = "operational";

    public int RequestedTacticalRechargePower { get; set; }
}

public sealed class Tl1PowerScriptInput
{
    public int? Envelope { get; set; }

    public List<Tl1PowerCommand> Commands { get; set; } = new();
}

public sealed class Tl1PowerCommand
{
    public string Action { get; set; } = string.Empty;

    public string Id { get; set; } = string.Empty;

    public int Amount { get; set; }

    public bool ExpectFailure { get; set; }
}

public sealed class Tl1HeldInterceptionInput
{
    public int? Envelope { get; set; }

    public string HoldId { get; set; } = "held-interception";

    public int PowerCost { get; set; }

    public int StartingAmmunition { get; set; }

    public int AmmunitionCost { get; set; }

    public bool Triggered { get; set; }
}

public sealed class Tl1ReactorEnvelopeInput
{
    public string StartingCondition { get; set; } = "operational";

    public string MidTurnCondition { get; set; } = "degraded";

    public int PoweredBeforeDamage { get; set; }

    public int SpentBeforeDamage { get; set; }
}

public sealed class Tl1ReactorOverloadInput
{
    public string StartingCondition { get; set; } = "operational";

    public int StartingStrain { get; set; }

    public List<Tl1ReactorOverloadAttempt> Attempts { get; set; } = new();
}

public sealed class Tl1ReactorOverloadAttempt
{
    public bool BeginNewTurn { get; set; }

    public int? Roll { get; set; }
}

public sealed class Tl1ResetStateInput
{
    public string Reset { get; set; } = "turnRefresh";

    public string ReactorCondition { get; set; } = "operational";

    public int ReactorStrain { get; set; }

    public int Crew { get; set; }

    public int Marines { get; set; }

    public int Ammunition { get; set; }

    public int Fuel { get; set; }

    public int BatteryCharges { get; set; }

    public int CapacitorCharge { get; set; }

    public int CurrentShieldCapacity { get; set; }

    public int TemporaryShieldOvercapacity { get; set; }

    public int PoweredPower { get; set; }

    public int SpentPower { get; set; }

    public int EarmarkedPower { get; set; }

    public bool EvasiveManeuvering { get; set; }

    public bool HeldFire { get; set; }

    public bool TractorLock { get; set; }

    public bool OverloadUsed { get; set; }

    public int ChargeProgress { get; set; }

    public bool WeaponReady { get; set; }

    public int RetentionTurns { get; set; }
}

public sealed class Tl1WeaponFireInput
{
    public string Weapon { get; set; } = "kinetic";

    public string Mode { get; set; } = "standard";

    public bool Hit { get; set; } = true;

    public int? Envelope { get; set; }

    public int? StartingAmmunition { get; set; }

    public Tl1DefenseFixture Defense { get; set; } = new();
}

public sealed class Tl1ChargedWeaponScriptInput
{
    public int RequiredChargeTurns { get; set; }

    public int ChargePowerPerTurn { get; set; }

    public bool RetentionAllowed { get; set; }

    public int RetentionUpkeep { get; set; }

    public int? MaximumRetentionTurns { get; set; }

    public List<Tl1ChargedWeaponStep> Steps { get; set; } = new();
}

public sealed class Tl1ChargedWeaponStep
{
    public string Action { get; set; } = string.Empty;

    public int? Envelope { get; set; }

    public string Condition { get; set; } = string.Empty;

    public int ChargeProgress { get; set; }

    public bool IsReady { get; set; }

    public bool ReadyPowerPaidThisTurn { get; set; }

    public int RetentionTurns { get; set; }

    public bool ExpectFailure { get; set; }
}

public sealed record Tl1OperationExecution(
    JsonElement Actual,
    IReadOnlyList<string> Events);
