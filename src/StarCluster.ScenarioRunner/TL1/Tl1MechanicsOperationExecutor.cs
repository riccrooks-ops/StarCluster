using System.Text.Json;
using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.ScenarioRunner.TL1;

public sealed class Tl1MechanicsOperationExecutor
{
    private readonly Tl1BaselineCatalog _baseline;

    public Tl1MechanicsOperationExecutor(Tl1BaselineCatalog baseline)
    {
        ArgumentNullException.ThrowIfNull(baseline);
        _baseline = baseline;
    }

    public Tl1OperationExecution Execute(
        string operation,
        JsonElement input)
    {
        if (string.IsNullOrWhiteSpace(operation))
        {
            throw new ArgumentException("Operation is required.", nameof(operation));
        }
        return operation.Trim().ToLowerInvariant() switch
        {
            "resolvedamage" => ResolveDamage(input),
            "turnstartrecharge" => TurnStartRecharge(input),
            "powerscript" => PowerScript(input),
            "heldinterception" => HeldInterception(input),
            "reactorenvelope" => ReactorEnvelope(input),
            "reactoroverload" => ReactorOverload(input),
            "resetstate" => ResetState(input),
            "weaponfire" => WeaponFire(input),
            "chargedweaponscript" => ChargedWeaponScript(input),
            _ => throw new InvalidOperationException(
                $"Unknown TL1 Phase A operation '{operation}'."),
        };
    }

    private Tl1OperationExecution ResolveDamage(JsonElement input)
    {
        Tl1ResolveDamageInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1ResolveDamageInput>(input);
        LayeredDefenseState defense = Tl1BaselineFactory.CreateDefense(
            _baseline,
            document.Defense);
        AttackPacket packet = CreatePacket(document.Packet);
        LayeredDamageResolution resolution = LayeredDamageResolver.Resolve(
            defense,
            packet);
        return Result(
            new
            {
                resolution,
                defense = DefenseSnapshot(defense),
            },
            $"Resolved DAM {packet.Damage}, SPEN {packet.ShieldPenetration}, " +
            $"APEN {packet.ArmorPenetration}.");
    }

    private Tl1OperationExecution TurnStartRecharge(JsonElement input)
    {
        Tl1TurnStartRechargeInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1TurnStartRechargeInput>(input);
        LayeredDefenseState defense = Tl1BaselineFactory.CreateDefense(
            _baseline,
            document.Defense);
        ReactorState reactor = Tl1BaselineFactory.CreateReactor(
            _baseline,
            document.ReactorCondition);
        var power = new TacticalPowerLedger();
        power.BeginTurn(reactor.CurrentOutput);
        ShieldRechargeResult recharge = ShieldRechargeService.ApplyTurnStart(
            defense,
            Tl1BaselineFactory.ParseCondition(document.ShieldCondition),
            Tl1BaselineFactory.CreateShieldRechargeProfile(_baseline),
            power,
            document.RequestedTacticalRechargePower);

        return Result(
            new
            {
                temporaryCapacityLost = recharge.TemporaryCapacityLost,
                baseRestored = recharge.BaseRestored,
                tacticalPowerSpent = recharge.TacticalPowerSpent,
                tacticalRestored = recharge.TacticalRestored,
                defense = DefenseSnapshot(defense),
                power = recharge.Power,
            },
            $"Turn-start recharge restored " +
            $"{recharge.BaseRestored + recharge.TacticalRestored} shields.");
    }

    private Tl1OperationExecution PowerScript(JsonElement input)
    {
        Tl1PowerScriptInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1PowerScriptInput>(input);
        var power = new TacticalPowerLedger();
        power.BeginTurn(document.Envelope ?? _baseline.GetInt("reactor_output"));
        var steps = new List<object>();
        var events = new List<string>();

        foreach (Tl1PowerCommand command in document.Commands)
        {
            bool succeeded = true;
            string? error = null;
            try
            {
                ApplyPowerCommand(power, command);
            }
            catch (Exception exception) when (command.ExpectFailure)
            {
                succeeded = false;
                error = exception.Message;
            }

            steps.Add(new
            {
                action = command.Action,
                id = command.Id,
                amount = command.Amount,
                succeeded,
                error,
                power = power.Snapshot(),
            });
            events.Add(
                $"{command.Action} {command.Id} {command.Amount}: " +
                (succeeded ? "succeeded" : "rejected"));
        }

        return Result(
            new
            {
                steps,
                finalPower = power.Snapshot(),
            },
            events);
    }

    private Tl1OperationExecution HeldInterception(JsonElement input)
    {
        Tl1HeldInterceptionInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1HeldInterceptionInput>(input);
        var power = new TacticalPowerLedger();
        power.BeginTurn(document.Envelope ?? _baseline.GetInt("reactor_output"));
        if (document.PowerCost > 0)
        {
            power.Earmark(document.HoldId, document.PowerCost);
        }
        TacticalPowerSnapshot afterDeclaration = power.Snapshot();

        int ammunition = document.StartingAmmunition;
        bool attackOpportunityReserved = true;
        bool attackOpportunityUsed = false;
        if (document.Triggered)
        {
            if (document.PowerCost > 0)
            {
                power.TriggerEarmark(document.HoldId);
            }
            if (ammunition < document.AmmunitionCost)
            {
                throw new InvalidOperationException(
                    "Held weapon lacks the reserved ammunition package.");
            }
            ammunition -= document.AmmunitionCost;
            attackOpportunityUsed = true;
        }
        else
        {
            if (document.PowerCost > 0)
            {
                power.ReleaseEarmark(document.HoldId);
            }
        }

        return Result(
            new
            {
                triggered = document.Triggered,
                attackOpportunityReserved,
                attackOpportunityUsed,
                afterDeclaration,
                finalPower = power.Snapshot(),
                remainingAmmunition = ammunition,
            },
            document.Triggered
                ? "Held interception triggered; earmarked power became Spent."
                : "Held interception expired; earmarked power returned to spendable Available power.");
    }

    private Tl1OperationExecution ReactorEnvelope(JsonElement input)
    {
        Tl1ReactorEnvelopeInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1ReactorEnvelopeInput>(input);
        ReactorState reactor = Tl1BaselineFactory.CreateReactor(
            _baseline,
            document.StartingCondition);
        var power = new TacticalPowerLedger();
        power.BeginTurn(reactor.CurrentOutput);
        if (document.PoweredBeforeDamage > 0)
        {
            power.IncreasePoweredSystem(
                "pre-damage-powered-system",
                document.PoweredBeforeDamage);
        }
        if (document.SpentBeforeDamage > 0)
        {
            power.Spend(document.SpentBeforeDamage);
        }
        TacticalPowerSnapshot beforeDamage = power.Snapshot();

        reactor.SetCondition(Tl1BaselineFactory.ParseCondition(
            document.MidTurnCondition));
        TacticalPowerSnapshot afterDamage = power.Snapshot();

        reactor.ResetTurn();
        power.BeginTurn(reactor.CurrentOutput);
        TacticalPowerSnapshot nextTurn = power.Snapshot();

        return Result(
            new
            {
                beforeDamage,
                afterDamage,
                nextTurn,
                reactorCondition = reactor.Condition.ToString(),
            },
            "Mid-turn reactor condition change preserved the current Turn Power Envelope and applied on the next turn.");
    }

    private Tl1OperationExecution ReactorOverload(JsonElement input)
    {
        Tl1ReactorOverloadInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1ReactorOverloadInput>(input);
        ReactorState reactor = Tl1BaselineFactory.CreateReactor(
            _baseline,
            document.StartingCondition,
            document.StartingStrain);
        var power = new TacticalPowerLedger();
        power.BeginTurn(reactor.CurrentOutput);
        var attempts = new List<object>();
        var events = new List<string>();

        foreach (Tl1ReactorOverloadAttempt attempt in document.Attempts)
        {
            if (attempt.BeginNewTurn)
            {
                reactor.ResetTurn();
                power.BeginTurn(reactor.CurrentOutput);
            }
            ReactorOverloadResult result = reactor.AttemptOverload(
                power,
                attempt.Roll);
            attempts.Add(new
            {
                result,
                power = power.Snapshot(),
                overloadUsed = reactor.OverloadUsedThisTurn,
            });
            events.Add(
                $"Reactor overload: {result.Outcome}; Strain {result.FinalStrain}; " +
                $"condition {result.FinalCondition}.");
        }

        return Result(
            new
            {
                attempts,
                finalStrain = reactor.CurrentStrain,
                finalCondition = reactor.Condition.ToString(),
                finalPower = power.Snapshot(),
            },
            events);
    }

    private Tl1OperationExecution ResetState(JsonElement input)
    {
        Tl1ResetStateInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1ResetStateInput>(input);
        ReactorState reactor = Tl1BaselineFactory.CreateReactor(
            _baseline,
            document.ReactorCondition,
            document.ReactorStrain);
        var power = new TacticalPowerLedger();
        power.BeginTurn(reactor.CurrentOutput);
        if (document.PoweredPower > 0)
        {
            power.IncreasePoweredSystem("temporary-system", document.PoweredPower);
        }
        if (document.SpentPower > 0)
        {
            power.Spend(document.SpentPower);
        }
        if (document.EarmarkedPower > 0)
        {
            power.Earmark("held-power", document.EarmarkedPower);
        }

        var capacitor = new CapacitorBankState(
            _baseline.GetInt("capacitor_capacity"),
            _baseline.GetInt("capacitor_charge_rate"),
            _baseline.GetInt("capacitor_discharge_rate"),
            document.CapacitorCharge);
        var charged = new ChargedWeaponState(
            requiredChargeTurns: 2,
            chargePowerPerTurn: 1,
            retentionAllowed: true,
            retentionUpkeep: 1);
        charged.LoadState(
            document.ChargeProgress,
            document.WeaponReady,
            document.RetentionTurns);
        LayeredDefenseState defense = Tl1BaselineFactory.CreateDefense(
            _baseline,
            new Tl1DefenseFixture
            {
                CurrentShieldCapacity = document.CurrentShieldCapacity,
                TemporaryShieldOvercapacity = document.TemporaryShieldOvercapacity,
            });

        bool evasive = document.EvasiveManeuvering;
        bool heldFire = document.HeldFire;
        bool tractorLock = document.TractorLock;
        if (document.OverloadUsed)
        {
            reactor.AttemptOverload(power);
        }

        string reset = document.Reset.Trim().ToLowerInvariant();
        switch (reset)
        {
            case "turnrefresh":
                defense.ClearTemporaryShieldOvercapacity();
                charged.BeginTurn();
                reactor.ResetTurn();
                power.BeginTurn(reactor.CurrentOutput);
                evasive = false;
                heldFire = false;
                tractorLock = false;
                break;
            case "ftltransition":
                defense.ClearTemporaryShieldOvercapacity();
                charged.ResetForFtlTransition();
                capacitor.CompleteFtlTransition();
                reactor.ResetTurn();
                power.ClearForFtlTransition();
                evasive = false;
                heldFire = false;
                tractorLock = false;
                break;
            default:
                throw new InvalidOperationException(
                    $"Unknown reset type '{document.Reset}'.");
        }

        return Result(
            new
            {
                reset = document.Reset,
                persistent = new
                {
                    crew = document.Crew,
                    marines = document.Marines,
                    ammunition = document.Ammunition,
                    fuel = document.Fuel,
                    batteryCharges = document.BatteryCharges,
                    capacitorCharge = capacitor.StoredPower,
                    reactorStrain = reactor.CurrentStrain,
                    currentShieldCapacity = defense.CurrentShieldCapacity,
                },
                temporary = new
                {
                    power = power.Snapshot(),
                    evasiveManeuvering = evasive,
                    heldFire,
                    tractorLock,
                    overloadUsed = reactor.OverloadUsedThisTurn,
                    temporaryShieldOvercapacity =
                        defense.TemporaryShieldOvercapacity,
                },
                chargedWeapon = ChargedWeaponSnapshot(charged),
            },
            reset == "turnrefresh"
                ? "Turn Refresh cleared turn-local state while retaining persistent resources and weapon charge state."
                : "FTL transition cleared encounter-specific and charged-weapon state, refilled the installed Capacitor Bank, and did not repair or replenish other persistent resources.");
    }

    private Tl1OperationExecution WeaponFire(JsonElement input)
    {
        Tl1WeaponFireInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1WeaponFireInput>(input);
        WeaponProfile profile = Tl1BaselineFactory.CreateWeaponProfile(
            _baseline,
            document.Weapon,
            document.Mode);
        var weapon = new WeaponState(profile, document.StartingAmmunition);
        var power = new TacticalPowerLedger();
        power.BeginTurn(document.Envelope ?? _baseline.GetInt("reactor_output"));
        LayeredDefenseState defense = Tl1BaselineFactory.CreateDefense(
            _baseline,
            document.Defense);
        WeaponFireResult fire = weapon.Fire(power, defense, document.Hit);
        return Result(
            new
            {
                fire,
                defense = DefenseSnapshot(defense),
            },
            $"Fired {document.Weapon}/{document.Mode}; hit={document.Hit}.");
    }

    private Tl1OperationExecution ChargedWeaponScript(JsonElement input)
    {
        Tl1ChargedWeaponScriptInput document =
            Tl1ScenarioSerialization.ReadInput<Tl1ChargedWeaponScriptInput>(input);
        var charged = new ChargedWeaponState(
            document.RequiredChargeTurns,
            document.ChargePowerPerTurn,
            document.RetentionAllowed,
            document.RetentionUpkeep,
            document.MaximumRetentionTurns);
        var power = new TacticalPowerLedger();
        power.BeginTurn(_baseline.GetInt("reactor_output"));
        var steps = new List<object>();
        var events = new List<string>();

        foreach (Tl1ChargedWeaponStep step in document.Steps)
        {
            bool succeeded = true;
            string? error = null;
            try
            {
                ApplyChargedWeaponStep(charged, power, step);
            }
            catch (Exception exception) when (step.ExpectFailure)
            {
                succeeded = false;
                error = exception.Message;
            }

            steps.Add(new
            {
                action = step.Action,
                succeeded,
                error,
                chargedWeapon = ChargedWeaponSnapshot(charged),
                power = power.Snapshot(),
            });
            events.Add(
                $"{step.Action}: {(succeeded ? "succeeded" : "rejected")}; " +
                $"progress {charged.ChargeProgress}/{charged.RequiredChargeTurns}; " +
                $"Ready={charged.IsReady}.");
        }

        return Result(
            new
            {
                steps,
                finalChargedWeapon = ChargedWeaponSnapshot(charged),
                finalPower = power.Snapshot(),
            },
            events);
    }

    private static void ApplyPowerCommand(
        TacticalPowerLedger power,
        Tl1PowerCommand command)
    {
        string action = command.Action.Trim().ToLowerInvariant();
        switch (action)
        {
            case "powersystem":
                power.IncreasePoweredSystem(command.Id, command.Amount);
                break;
            case "spend":
                power.Spend(command.Amount);
                break;
            case "earmark":
                power.Earmark(command.Id, command.Amount);
                break;
            case "trigger":
                power.TriggerEarmark(command.Id);
                break;
            case "release":
                power.ReleaseEarmark(command.Id);
                break;
            case "shutdown":
                power.ShutdownSystem(command.Id);
                break;
            case "disable":
                power.DisableSystem(command.Id);
                break;
            case "addgenerated":
                power.AddGeneratedPower(command.Amount);
                break;
            default:
                throw new InvalidOperationException(
                    $"Unknown Tactical Power command '{command.Action}'.");
        }
    }

    private static void ApplyChargedWeaponStep(
        ChargedWeaponState charged,
        TacticalPowerLedger power,
        Tl1ChargedWeaponStep step)
    {
        string action = step.Action.Trim().ToLowerInvariant();
        switch (action)
        {
            case "beginturn":
                charged.BeginTurn();
                power.BeginTurn(step.Envelope ?? power.Envelope);
                break;
            case "charge":
                charged.PayCharge(power);
                break;
            case "retain":
                charged.PayRetention(power);
                break;
            case "fire":
                charged.Fire();
                break;
            case "stopretention":
                charged.StopRetention();
                break;
            case "applycondition":
                charged.ApplyCondition(
                    Tl1BaselineFactory.ParseCondition(step.Condition));
                break;
            case "ftltransition":
                charged.ResetForFtlTransition();
                power.ClearForFtlTransition();
                break;
            case "loadstate":
                charged.LoadState(
                    step.ChargeProgress,
                    step.IsReady,
                    step.RetentionTurns,
                    step.ReadyPowerPaidThisTurn);
                break;
            default:
                throw new InvalidOperationException(
                    $"Unknown charged-weapon step '{step.Action}'.");
        }
    }

    private static AttackPacket CreatePacket(Tl1AttackPacketFixture packet) => new(
        packet.Damage,
        packet.ShieldPenetration,
        packet.ArmorPenetration);

    private static object DefenseSnapshot(LayeredDefenseState defense) => new
    {
        pristineShieldCapacity = defense.PristineShieldCapacity,
        temporaryShieldOvercapacity = defense.TemporaryShieldOvercapacity,
        effectiveShieldMaximum = defense.EffectiveShieldMaximum,
        currentShieldCapacity = defense.CurrentShieldCapacity,
        shieldArmor = defense.ShieldArmor,
        armorLayers = defense.ArmorLayers.Select(layer => new
        {
            id = layer.Id,
            pristineProtection = layer.PristineProtection,
            currentProtection = layer.CurrentProtection,
            pristineIntegrity = layer.PristineIntegrity,
            currentIntegrity = layer.CurrentIntegrity,
        }).ToArray(),
        pristineHull = defense.PristineHull,
        currentHull = defense.CurrentHull,
        isDestroyed = defense.IsDestroyed,
        isShieldCollapsed = defense.IsShieldCollapsed,
    };

    private static object ChargedWeaponSnapshot(ChargedWeaponState charged) => new
    {
        requiredChargeTurns = charged.RequiredChargeTurns,
        chargePowerPerTurn = charged.ChargePowerPerTurn,
        retentionAllowed = charged.RetentionAllowed,
        retentionUpkeep = charged.RetentionUpkeep,
        maximumRetentionTurns = charged.MaximumRetentionTurns,
        chargeProgress = charged.ChargeProgress,
        isReady = charged.IsReady,
        retentionTurns = charged.RetentionTurns,
        requiresRetentionPayment = charged.RequiresRetentionPayment,
    };

    private static Tl1OperationExecution Result(object actual, params string[] events) =>
        Result(actual, (IReadOnlyList<string>)events);

    private static Tl1OperationExecution Result(
        object actual,
        IReadOnlyList<string> events) => new(
        Tl1ScenarioSerialization.ToElement(actual),
        events);
}
