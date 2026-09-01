namespace StarCluster.Core.Combat.Tactics;

/// <summary>
/// Information available to adaptive combat-resource doctrine about the
/// opponent's demonstrated offensive capability. Unknown is deliberate: the
/// doctrine must not inspect hidden enemy build data.
/// </summary>
public enum ObservedOffensiveCapability
{
    Unknown,
    Kinetic,
    Energy,
    Missile,
}

/// <summary>
/// Pure CP146 doctrine input. These values describe own-ship capability and
/// player-observable threat state only; hidden opponent component ratings are
/// intentionally absent.
/// </summary>
public sealed record CombatResourceDoctrineContext(
    int SpendableTacticalPower,
    int ActiveSensorPower,
    bool PassiveSensorProvidesUsableTrack,
    bool FirmTrackAvailable,
    bool LegalMainWeaponShipAttack,
    string MainWeaponFamily,
    int MainWeaponBanks,
    int MainWeaponPowerPerBank,
    bool PdsAvailable,
    int PdsReadinessPower,
    int PdsReactionCapacity,
    bool ShieldHardenerAvailable,
    int ShieldHardenerPower,
    bool EcmAvailable,
    int EcmPower,
    bool EccmAvailable,
    int EccmPower,
    bool OpponentEcmObserved,
    bool FirmTrackDegradedByObservedEcm,
    ObservedOffensiveCapability OpponentCapability,
    int ImminentMissileSubflights)
{
    public void Validate()
    {
        if (SpendableTacticalPower < 0 || ActiveSensorPower < 0 ||
            MainWeaponBanks < 0 || MainWeaponPowerPerBank < 0 ||
            PdsReadinessPower < 0 || PdsReactionCapacity < 0 ||
            ShieldHardenerPower < 0 || EcmPower < 0 || EccmPower < 0 ||
            ImminentMissileSubflights < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(SpendableTacticalPower),
                "Combat-resource doctrine power/capacity inputs must be non-negative.");
        }
        if (string.IsNullOrWhiteSpace(MainWeaponFamily))
        {
            throw new ArgumentException("Main weapon family is required.", nameof(MainWeaponFamily));
        }
    }
}

public sealed record CombatResourceDoctrineDecision(
    bool ActiveSensor,
    int FundedMainWeaponBanks,
    bool PdsReady,
    int FundedPdsReactionCapacity,
    bool ShieldHardenerActive,
    bool EcmActive,
    bool EccmActive,
    int HeldMainWeaponBanks,
    int TacticalPowerRemaining);

/// <summary>
/// CP146 contextual activation doctrine. The ordering encodes policy, not new
/// equipment values: preserve a usable sensor/main-weapon combat package;
/// react to observed EW; then use residual TP for defenses that are relevant to
/// known or unresolved threats. A legal single-main K/E ship attack remains
/// offensive even when PDS is unavailable. Held Main covers otherwise-unserved
/// imminent missile capacity when no legal ship-fire opportunity exists, while a
/// dual-main ship may hold one bank to supplement excess subflights.
/// </summary>
public static class CombatResourceDoctrineService
{
    public static CombatResourceDoctrineDecision Decide(
        CombatResourceDoctrineContext context)
    {
        ArgumentNullException.ThrowIfNull(context);
        context.Validate();

        int remaining = context.SpendableTacticalPower;
        int minimumWeaponPackage = checked(
            context.MainWeaponBanks * context.MainWeaponPowerPerBank);

        bool activeSensor = false;
        if (context.ActiveSensorPower <= remaining &&
            remaining - context.ActiveSensorPower >= minimumWeaponPackage)
        {
            activeSensor = true;
            remaining -= context.ActiveSensorPower;
        }
        else if (!context.PassiveSensorProvidesUsableTrack &&
            context.ActiveSensorPower <= remaining)
        {
            activeSensor = true;
            remaining -= context.ActiveSensorPower;
        }

        bool eccm = false;
        if (context.EccmAvailable && context.OpponentEcmObserved &&
            context.FirmTrackDegradedByObservedEcm &&
            context.EccmPower <= remaining &&
            remaining - context.EccmPower >= minimumWeaponPackage)
        {
            eccm = true;
            remaining -= context.EccmPower;
        }

        int fundedBanks = 0;
        for (int i = 0; i < context.MainWeaponBanks; i++)
        {
            if (context.MainWeaponPowerPerBank <= remaining)
            {
                remaining -= context.MainWeaponPowerPerBank;
                fundedBanks++;
            }
        }

        bool unknownThreat = context.OpponentCapability ==
            ObservedOffensiveCapability.Unknown;
        bool missileRelevant = context.ImminentMissileSubflights > 0;
        bool pdsReady = false;
        int fundedRc = 0;
        if (context.PdsAvailable && (unknownThreat || missileRelevant) &&
            context.PdsReadinessPower <= remaining)
        {
            pdsReady = true;
            fundedRc = context.PdsReactionCapacity;
            remaining -= context.PdsReadinessPower;
        }

        bool hardenerRelevant = unknownThreat ||
            context.OpponentCapability == ObservedOffensiveCapability.Energy;
        bool hardener = false;
        if (context.ShieldHardenerAvailable && hardenerRelevant &&
            context.ShieldHardenerPower <= remaining)
        {
            hardener = true;
            remaining -= context.ShieldHardenerPower;
        }

        bool ecm = false;
        if (context.EcmAvailable && context.EcmPower <= remaining)
        {
            ecm = true;
            remaining -= context.EcmPower;
        }

        bool canHold = context.FirmTrackAvailable && fundedBanks > 0 &&
            (context.MainWeaponFamily.Equals("Kinetic", StringComparison.OrdinalIgnoreCase) ||
             context.MainWeaponFamily.Equals("Energy", StringComparison.OrdinalIgnoreCase));
        int held = 0;
        int excessThreat = Math.Max(0, context.ImminentMissileSubflights - fundedRc);
        if (canHold && excessThreat > 0 &&
            (!context.LegalMainWeaponShipAttack || fundedBanks >= 2))
        {
            held = 1;
        }

        return new CombatResourceDoctrineDecision(
            activeSensor,
            fundedBanks,
            pdsReady,
            fundedRc,
            hardener,
            ecm,
            eccm,
            held,
            remaining);
    }
}
