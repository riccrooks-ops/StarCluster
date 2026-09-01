using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.Core.Combat.DirectFire;

public sealed record Tl1PowerEnvelopeSideProfile
{
    public string Family { get; init; } = "kinetic";
    public string Doctrine { get; init; } = "standard";
    public int Accuracy { get; init; } = 20;
    public int ComputerBonus { get; init; } = 10;
    public bool Evasive { get; init; }
    public int ReactorOutput { get; init; } = 5;
    public int AuxiliaryReactorOutput { get; init; }
    public int Ammunition { get; init; } = 100;
    public int MissileGuidance { get; init; } = 55;
    public int MissileDamage { get; init; } = 5;
    public int MissileShieldPenetration { get; init; } = 1;
    public int MissileArmorPenetration { get; init; } = 2;
    public int MissileSpeed { get; init; } = 1;
    public int MissileRange { get; init; } = 6;
    public int TargetMovePerTurn { get; init; }
    public int MissileLaunchesPerTurn { get; init; } = 1;
    public string PdsFamily { get; init; } = "none";
    public int PdsPowerCost { get; init; }
    public int PdsReactionCapacity { get; init; }
    public int PdsInterceptionChance { get; init; }
    public int PdsAmmunition { get; init; }
    public bool PdsUnlimitedAmmunition { get; init; }
    public bool SensorTrackGateEnabled { get; init; }
    public int PassiveFirmRange { get; init; } = 3;
    public int ActiveFirmRangeAtOnePower { get; init; } = 5;
    public int ActiveFirmRangeAtTwoPower { get; init; } = 6;
    public int SensorPower { get; init; }
    public int EcmPower { get; init; }
    public int EccmPower { get; init; }
    public int ShieldHardenerPower { get; init; }
    public int TacticalShieldRechargePower { get; init; }
    public string PowerPriority { get; init; } = "defense-first";
    public bool HeldInterception { get; init; }
    public string HeldInterceptionMode { get; init; } = "standard";
    public bool ReactorSafeOverload { get; init; }
    public bool EnergySafeBurst { get; init; }
    public bool SensorSafeOverload { get; init; }
    public bool EcmSafeOverload { get; init; }
    public bool EccmSafeOverload { get; init; }
    public bool ShieldHardenerSafeOverload { get; init; }
    public bool ShieldOvercapacitySafeOverload { get; init; }
    public bool ShieldRecoverySafeOverload { get; init; }
    public int SafeOverloadTurnLimit { get; init; } = 2;
    public int CombatBatteryCharges { get; init; }
    public int CombatBatteryGain { get; init; } = 2;
    public string CombatBatteryDoctrine { get; init; } = "none";
    public int CapacitorCapacity { get; init; }
    public int CapacitorStartingCharge { get; init; }
    public int CapacitorChargeRate { get; init; } = 1;
    public int CapacitorDischargeRate { get; init; } = 2;
    public string CapacitorDoctrine { get; init; } = "none";
}

public sealed record Tl1PowerEnvelopeProfile
{
    public int ShieldCapacity { get; init; } = 2;
    public int ShieldArmor { get; init; }
    public int BaseShieldRecharge { get; init; } = 1;
    public int ArmorProtection { get; init; }
    public int ArmorIntegrity { get; init; } = 4;
    public int Hull { get; init; } = 12;
    public int RangeHexes { get; init; } = 2;
    public int RangePenaltyPerHex { get; init; } = 5;
    public int TurnCap { get; init; } = 100;
    public IReadOnlyList<Tl1RelativeRangeChange> RangeSchedule { get; init; } =
        Array.Empty<Tl1RelativeRangeChange>();
    public Tl1PowerEnvelopeSideProfile SideA { get; init; } = new();
    public Tl1PowerEnvelopeSideProfile SideB { get; init; } = new();
}

public sealed record Tl1PowerEnvelopeResult
{
    public Tl1DuelOutcome Outcome { get; init; }
    public int Turns { get; init; }
    public int ShotsA { get; init; }
    public int ShotsB { get; init; }
    public int HitsA { get; init; }
    public int HitsB { get; init; }
    public int LaunchesA { get; init; }
    public int LaunchesB { get; init; }
    public int MissileHitsA { get; init; }
    public int MissileHitsB { get; init; }
    public int AmmunitionA { get; init; }
    public int AmmunitionB { get; init; }
    public DirectFireCombatant SideA { get; init; } = null!;
    public DirectFireCombatant SideB { get; init; } = null!;
    public int PdsAttemptsA { get; init; }
    public int PdsAttemptsB { get; init; }
    public int PdsInterceptsA { get; init; }
    public int PdsInterceptsB { get; init; }
    public int HeldDeclarationsA { get; init; }
    public int HeldDeclarationsB { get; init; }
    public int HeldAttemptsA { get; init; }
    public int HeldAttemptsB { get; init; }
    public int HeldInterceptsA { get; init; }
    public int HeldInterceptsB { get; init; }
    public int HeldUnusedA { get; init; }
    public int HeldUnusedB { get; init; }
    public int HeldPowerEarmarkedA { get; init; }
    public int HeldPowerEarmarkedB { get; init; }
    public int OffensiveWeaponPowerSpentA { get; init; }
    public int OffensiveWeaponPowerSpentB { get; init; }
    public int OffensiveCyclesLostA { get; init; }
    public int OffensiveCyclesLostB { get; init; }
    public int FullPackageTurnsA { get; init; }
    public int FullPackageTurnsB { get; init; }
    public int PartialPackageTurnsA { get; init; }
    public int PartialPackageTurnsB { get; init; }
    public int UnfundedPdsA { get; init; }
    public int UnfundedPdsB { get; init; }
    public int UnfundedSensorsA { get; init; }
    public int UnfundedSensorsB { get; init; }
    public int UnfundedEcmA { get; init; }
    public int UnfundedEcmB { get; init; }
    public int UnfundedEccmA { get; init; }
    public int UnfundedEccmB { get; init; }
    public int UnfundedHardenerA { get; init; }
    public int UnfundedHardenerB { get; init; }
    public int UnfundedEvmA { get; init; }
    public int UnfundedEvmB { get; init; }
    public int UnfundedShieldOverloadA { get; init; }
    public int UnfundedShieldOverloadB { get; init; }
    public int UnfundedRechargeA { get; init; }
    public int UnfundedRechargeB { get; init; }
    public int UnfundedHeldA { get; init; }
    public int UnfundedHeldB { get; init; }
    public int UnfundedWeaponA { get; init; }
    public int UnfundedWeaponB { get; init; }
    public int BaseReactorPowerA { get; init; }
    public int BaseReactorPowerB { get; init; }
    public int AuxiliaryPowerA { get; init; }
    public int AuxiliaryPowerB { get; init; }
    public int ReactorOverloadPowerA { get; init; }
    public int ReactorOverloadPowerB { get; init; }
    public int CombatBatteryPowerA { get; init; }
    public int CombatBatteryPowerB { get; init; }
    public int CombatBatteryChargesUsedA { get; init; }
    public int CombatBatteryChargesUsedB { get; init; }
    public int CapacitorPowerDischargedA { get; init; }
    public int CapacitorPowerDischargedB { get; init; }
    public int CapacitorPowerChargedA { get; init; }
    public int CapacitorPowerChargedB { get; init; }
    public int CapacitorChargeA { get; init; }
    public int CapacitorChargeB { get; init; }
    public int TotalEnvelopeA { get; init; }
    public int TotalEnvelopeB { get; init; }
    public int TotalPoweredA { get; init; }
    public int TotalPoweredB { get; init; }
    public int TotalSpentA { get; init; }
    public int TotalSpentB { get; init; }
    public int TotalUnusedA { get; init; }
    public int TotalUnusedB { get; init; }
    public int PdsPowerCommittedA { get; init; }
    public int PdsPowerCommittedB { get; init; }
    public int SensorPowerCommittedA { get; init; }
    public int SensorPowerCommittedB { get; init; }
    public int EcmPowerCommittedA { get; init; }
    public int EcmPowerCommittedB { get; init; }
    public int EccmPowerCommittedA { get; init; }
    public int EccmPowerCommittedB { get; init; }
    public int ShieldHardenerPowerCommittedA { get; init; }
    public int ShieldHardenerPowerCommittedB { get; init; }
    public int ShieldRechargePowerSpentA { get; init; }
    public int ShieldRechargePowerSpentB { get; init; }
    public int ShieldOvercapacityAddedA { get; init; }
    public int ShieldOvercapacityAddedB { get; init; }
    public int EnergyOverloadShotsA { get; init; }
    public int EnergyOverloadShotsB { get; init; }
    public int ReactorStrainA { get; init; }
    public int ReactorStrainB { get; init; }
    public int EnergyStrainA { get; init; }
    public int EnergyStrainB { get; init; }
    public int SensorStrainA { get; init; }
    public int SensorStrainB { get; init; }
    public int EcmStrainA { get; init; }
    public int EcmStrainB { get; init; }
    public int EccmStrainA { get; init; }
    public int EccmStrainB { get; init; }
    public int HardenerStrainA { get; init; }
    public int HardenerStrainB { get; init; }
    public int ShieldGeneratorStrainA { get; init; }
    public int ShieldGeneratorStrainB { get; init; }
    public int FirmTrackTurnsA { get; init; }
    public int FirmTrackTurnsB { get; init; }
    public int TrackDeniedTurnsA { get; init; }
    public int TrackDeniedTurnsB { get; init; }
    public int RangeExhaustedA { get; init; }
    public int RangeExhaustedB { get; init; }
    public int InitialRangeHexes { get; init; }
    public int FinalRangeHexes { get; init; }
    public int RangeChangesApplied { get; init; }
    public int MissileReroutesA { get; init; }
    public int MissileReroutesB { get; init; }
}

public sealed class Tl1PowerEnvelopeSimulator
{
    private const int SafeStrainLimit = 2;
    private const int ReactorOverloadGain = 1;
    private const int SensorOverloadRangeBonus = 2;
    private const int EwOverloadRatingBonus = 1;
    private const int ShieldHardenerOverloadBonus = 1;
    private const int ShieldOvercapacityAmount = 1;
    private const int ShieldRecoveryBonus = 2;

    private sealed class PendingMissile
    {
        public PendingMissile(
            string owner,
            DirectFireCombatant target,
            Tl1PowerEnvelopeSideProfile profile,
            int distance)
        {
            Owner = owner;
            Target = target;
            Profile = profile;
            Distance = distance;
        }

        public string Owner { get; }
        public DirectFireCombatant Target { get; }
        public Tl1PowerEnvelopeSideProfile Profile { get; }
        public int Distance { get; set; }
        public int Traveled { get; set; }
    }

    private sealed class SideRuntime
    {
        public SideRuntime(
            string id,
            Tl1PowerEnvelopeSideProfile profile,
            DirectFireCombatant combatant,
            WeaponState? kineticWeapon,
            WeaponState? energyLowWeapon,
            WeaponState? energyStandardWeapon,
            WeaponState? energyOverloadWeapon,
            AmmunitionFeedState? missileFeed,
            AmmunitionFeedState? pdsFeed,
            CombatBatteryState? combatBattery,
            CapacitorBankState? capacitor)
        {
            Id = id;
            Profile = profile;
            Combatant = combatant;
            KineticWeapon = kineticWeapon;
            EnergyLowWeapon = energyLowWeapon;
            EnergyStandardWeapon = energyStandardWeapon;
            EnergyOverloadWeapon = energyOverloadWeapon;
            MissileFeed = missileFeed;
            PdsFeed = pdsFeed;
            CombatBattery = combatBattery;
            Capacitor = capacitor;
        }

        public string Id { get; }
        public Tl1PowerEnvelopeSideProfile Profile { get; }
        public DirectFireCombatant Combatant { get; }
        public WeaponState? KineticWeapon { get; }
        public WeaponState? EnergyLowWeapon { get; }
        public WeaponState? EnergyStandardWeapon { get; }
        public WeaponState? EnergyOverloadWeapon { get; }
        public AmmunitionFeedState? MissileFeed { get; }
        public AmmunitionFeedState? PdsFeed { get; }
        public CombatBatteryState? CombatBattery { get; }
        public CapacitorBankState? Capacitor { get; }
        public int PendingShieldRecoveryBonus { get; set; }
        public int Shots { get; set; }
        public int Hits { get; set; }
        public int Launches { get; set; }
        public int MissileHits { get; set; }
        public int RangeExhausted { get; set; }
        public int MissileReroutes { get; set; }
        public int PdsAttempts { get; set; }
        public int PdsIntercepts { get; set; }
        public int HeldDeclarations { get; set; }
        public int HeldAttempts { get; set; }
        public int HeldIntercepts { get; set; }
        public int HeldUnused { get; set; }
        public int HeldPowerEarmarked { get; set; }
        public int OffensiveWeaponPowerSpent { get; set; }
        public int OffensiveCyclesLost { get; set; }
        public int FullPackageTurns { get; set; }
        public int PartialPackageTurns { get; set; }
        public int UnfundedPds { get; set; }
        public int UnfundedSensors { get; set; }
        public int UnfundedEcm { get; set; }
        public int UnfundedEccm { get; set; }
        public int UnfundedHardener { get; set; }
        public int UnfundedEvm { get; set; }
        public int UnfundedShieldOverload { get; set; }
        public int UnfundedRecharge { get; set; }
        public int UnfundedHeld { get; set; }
        public int UnfundedWeapon { get; set; }
        public int BaseReactorPower { get; set; }
        public int AuxiliaryPower { get; set; }
        public int ReactorOverloadPower { get; set; }
        public int CombatBatteryPower { get; set; }
        public int CombatBatteryChargesUsed { get; set; }
        public int CapacitorPowerDischarged { get; set; }
        public int CapacitorPowerCharged { get; set; }
        public int TotalEnvelope { get; set; }
        public int TotalPowered { get; set; }
        public int TotalSpent { get; set; }
        public int TotalUnused { get; set; }
        public int PdsPowerCommitted { get; set; }
        public int SensorPowerCommitted { get; set; }
        public int EcmPowerCommitted { get; set; }
        public int EccmPowerCommitted { get; set; }
        public int ShieldHardenerPowerCommitted { get; set; }
        public int ShieldRechargePowerSpent { get; set; }
        public int ShieldOvercapacityAdded { get; set; }
        public int EnergyOverloadShots { get; set; }
        public int ReactorStrain { get; set; }
        public int EnergyStrain { get; set; }
        public int SensorStrain { get; set; }
        public int EcmStrain { get; set; }
        public int EccmStrain { get; set; }
        public int HardenerStrain { get; set; }
        public int ShieldGeneratorStrain { get; set; }
        public int FirmTrackTurns { get; set; }
        public int TrackDeniedTurns { get; set; }

        public int RemainingAmmunition =>
            KineticWeapon?.CurrentAmmunition ??
            MissileFeed?.TotalPackages ??
            0;
    }

    private sealed record TurnSystemState(
        bool PdsReady,
        bool EvasiveActive,
        int SensorFirmRange,
        int EcmRating,
        int EccmRating,
        int ShieldHardenerStrength,
        WeaponState? OffensiveWeapon,
        string? OffensiveEarmarkId,
        bool HeldReady,
        WeaponState? HeldWeapon,
        string? HeldEarmarkId,
        bool PackageFullyFunded)
    {
        public bool HeldUsed { get; set; }
    }

    private readonly Tl1PowerEnvelopeProfile _profile;

    public Tl1PowerEnvelopeSimulator(Tl1PowerEnvelopeProfile profile)
    {
        _profile = profile ?? throw new ArgumentNullException(nameof(profile));
        Validate(profile);
    }

    public Tl1PowerEnvelopeResult Run(
        Func<int> nextRollA,
        Func<int> nextRollB,
        Func<int>? nextPdsRollA = null,
        Func<int>? nextPdsRollB = null,
        Func<int>? nextHeldRollA = null,
        Func<int>? nextHeldRollB = null)
    {
        ArgumentNullException.ThrowIfNull(nextRollA);
        ArgumentNullException.ThrowIfNull(nextRollB);
        Func<int> pdsRollA = nextPdsRollA ?? nextRollA;
        Func<int> pdsRollB = nextPdsRollB ?? nextRollB;
        Func<int> heldRollA = nextHeldRollA ?? nextRollA;
        Func<int> heldRollB = nextHeldRollB ?? nextRollB;

        SideRuntime a = CreateSide("A", _profile.SideA);
        SideRuntime b = CreateSide("B", _profile.SideB);
        var missiles = new List<PendingMissile>();
        var rangeSchedule = new Tl1RelativeRangeSchedule(
            _profile.RangeHexes,
            _profile.TurnCap,
            _profile.RangeSchedule);
        int currentRangeHexes = rangeSchedule.InitialRangeHexes;
        int rangeChangesApplied = 0;
        int turns = 0;

        for (int turn = 1; turn <= _profile.TurnCap; turn++)
        {
            turns = turn;
            if (rangeSchedule.TryApplyTurn(
                    turn,
                    ref currentRangeHexes,
                    out int rangeDeltaHexes))
            {
                rangeChangesApplied++;
                if (rangeDeltaHexes != 0)
                {
                    foreach (PendingMissile missile in missiles)
                    {
                        missile.Distance = Math.Max(
                            0,
                            missile.Distance + rangeDeltaHexes);
                        SideRuntime owner = missile.Owner == "A" ? a : b;
                        owner.MissileReroutes++;
                    }
                }
            }
            TurnSystemState? systemsA = IsTerminal(a.Combatant)
                ? null
                : BeginTurn(a, turn);
            TurnSystemState? systemsB = IsTerminal(b.Combatant)
                ? null
                : BeginTurn(b, turn);
            int pdsAttemptsThisTurnA = 0;
            int pdsAttemptsThisTurnB = 0;

            bool actionWindow =
                !IsTerminal(a.Combatant) && !IsTerminal(b.Combatant);
            var orders = new List<SimultaneousDirectFireOrder>();
            if (actionWindow)
            {
                CommitSide(
                    a,
                    b,
                    systemsA!,
                    systemsB!,
                    nextRollA,
                    orders,
                    missiles,
                    currentRangeHexes);
                CommitSide(
                    b,
                    a,
                    systemsB!,
                    systemsA!,
                    nextRollB,
                    orders,
                    missiles,
                    currentRangeHexes);
            }

            if (orders.Count > 0)
            {
                SimultaneousDirectFireBatchResult batch =
                    SimultaneousDirectFireResolver.Resolve(orders);
                foreach (SimultaneousDirectFireAttackResult attack in batch.Attacks)
                {
                    SideRuntime attacker = attack.AttackerId == "A" ? a : b;
                    if (DirectFireHitResolver.IsHit(attack.Outcome))
                    {
                        attacker.Hits++;
                    }
                }
            }

            var impacts = new List<PendingMissile>();
            foreach (PendingMissile missile in missiles.ToArray())
            {
                if (missile.Target.IsDestroyed)
                {
                    missiles.Remove(missile);
                    continue;
                }

                int chaseDistance = Math.Max(
                    0,
                    missile.Distance + missile.Profile.TargetMovePerTurn);
                int step = Math.Min(
                    missile.Profile.MissileSpeed,
                    Math.Min(
                        Math.Max(
                            0,
                            missile.Profile.MissileRange - missile.Traveled),
                        chaseDistance));
                missile.Traveled += step;
                missile.Distance = chaseDistance - step;

                if (missile.Distance <= 0)
                {
                    impacts.Add(missile);
                    missiles.Remove(missile);
                }
                else if (missile.Traveled >= missile.Profile.MissileRange)
                {
                    SideRuntime owner = missile.Owner == "A" ? a : b;
                    owner.RangeExhausted++;
                    missiles.Remove(missile);
                }
            }

            foreach (PendingMissile missile in impacts)
            {
                SideRuntime target = ReferenceEquals(missile.Target, a.Combatant)
                    ? a
                    : b;
                SideRuntime owner = missile.Owner == "A" ? a : b;
                TurnSystemState? targetSystems = target.Id == "A"
                    ? systemsA
                    : systemsB;
                if (targetSystems is null)
                {
                    continue;
                }

                ref int attemptsUsedThisTurn = ref (target.Id == "A"
                    ? ref pdsAttemptsThisTurnA
                    : ref pdsAttemptsThisTurnB);
                Func<int> pdsRoll = target.Id == "A" ? pdsRollA : pdsRollB;
                Func<int> holdRoll = target.Id == "A" ? heldRollA : heldRollB;

                // Held Main engages at the longer interception window. PDS is the
                // close defensive layer and only spends ammunition against a Flight
                // that survives the held shot.
                if (ResolveHeldInterception(target, targetSystems, holdRoll))
                {
                    continue;
                }

                if (ResolvePdsAgainstMissile(
                        target,
                        targetSystems,
                        ref attemptsUsedThisTurn,
                        pdsRoll))
                {
                    continue;
                }

                int chance = Math.Clamp(
                    missile.Profile.MissileGuidance -
                    (targetSystems.EvasiveActive ? 10 : 0),
                    5,
                    95);
                int roll = missile.Owner == "A" ? nextRollA() : nextRollB();
                if (DirectFireHitResolver.IsHit(
                        DirectFireHitResolver.Resolve(roll, chance)))
                {
                    LayeredDamageResolver.Resolve(
                        missile.Target.Defense,
                        new AttackPacket(
                            missile.Profile.MissileDamage,
                            missile.Profile.MissileShieldPenetration,
                            missile.Profile.MissileArmorPenetration));
                    owner.MissileHits++;
                }
            }

            if (systemsA is not null)
            {
                EndTurn(a, systemsA);
            }
            if (systemsB is not null)
            {
                EndTurn(b, systemsB);
            }

            if (IsTerminal(a.Combatant) || IsTerminal(b.Combatant))
            {
                bool threatA = missiles.Any(
                    missile => missile.Owner == "A" && !missile.Target.IsDestroyed);
                bool threatB = missiles.Any(
                    missile => missile.Owner == "B" && !missile.Target.IsDestroyed);
                if (!threatA && !threatB)
                {
                    return CreateResult(
                        DetermineOutcome(a.Combatant, b.Combatant),
                        turn,
                        a,
                        b,
                        rangeSchedule.InitialRangeHexes,
                        currentRangeHexes,
                        rangeChangesApplied);
                }
            }

            if (!actionWindow && missiles.Count == 0)
            {
                break;
            }
        }

        return CreateResult(
            DetermineOutcome(a.Combatant, b.Combatant),
            turns,
            a,
            b,
            rangeSchedule.InitialRangeHexes,
            currentRangeHexes,
            rangeChangesApplied);
    }

    private TurnSystemState BeginTurn(SideRuntime side, int turn)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        TacticalPowerLedger power = side.Combatant.Power;
        side.CombatBattery?.BeginTurn();
        side.Capacitor?.BeginTurn();

        power.BeginTurn(profile.ReactorOutput);
        side.BaseReactorPower += profile.ReactorOutput;
        if (profile.AuxiliaryReactorOutput > 0)
        {
            power.AddGeneratedPower(profile.AuxiliaryReactorOutput);
            side.AuxiliaryPower += profile.AuxiliaryReactorOutput;
        }
        if (profile.ReactorSafeOverload &&
            turn <= profile.SafeOverloadTurnLimit &&
            side.ReactorStrain < SafeStrainLimit)
        {
            power.AddGeneratedPower(ReactorOverloadGain);
            side.ReactorOverloadPower += ReactorOverloadGain;
            side.ReactorStrain++;
        }

        LayeredDefenseState defense = side.Combatant.Defense;
        defense.ClearTemporaryShieldOvercapacity();
        defense.ShieldArmor = _profile.ShieldArmor;
        int recharge = _profile.BaseShieldRecharge;
        if (side.PendingShieldRecoveryBonus > 0)
        {
            recharge = checked(recharge + side.PendingShieldRecoveryBonus);
            side.PendingShieldRecoveryBonus = 0;
        }
        defense.RestoreShields(recharge);

        int estimatedDemand = EstimateDemand(side, turn);
        ApplyThresholdPowerSources(side, estimatedDemand);

        bool offenseFirst = profile.PowerPriority.Equals(
            "offense-first",
            StringComparison.OrdinalIgnoreCase);
        bool packageFullyFunded = true;
        WeaponState? offensiveWeapon = null;
        string? offensiveEarmarkId = null;
        bool heldReady = false;
        WeaponState? heldWeapon = null;
        string? heldEarmarkId = null;

        if (offenseFirst)
        {
            ReserveWeaponCycle(
                side,
                turn,
                ref offensiveWeapon,
                ref offensiveEarmarkId,
                ref heldReady,
                ref heldWeapon,
                ref heldEarmarkId,
                ref packageFullyFunded);
        }

        bool pdsReady = RequestPds(side, ref packageFullyFunded);
        int ecmRating = RequestEcm(side, turn, ref packageFullyFunded);
        int eccmRating = RequestEccm(side, turn, ref packageFullyFunded);
        int sensorFirmRange = RequestSensors(side, turn, ref packageFullyFunded);
        int hardenerStrength = RequestHardener(side, turn, ref packageFullyFunded);
        defense.ShieldArmor = checked(_profile.ShieldArmor + hardenerStrength);

        bool evasiveActive = false;
        if (profile.Evasive)
        {
            if (power.SpendablePower > 0)
            {
                power.Spend(1);
                evasiveActive = true;
            }
            else
            {
                side.UnfundedEvm++;
                packageFullyFunded = false;
            }
        }

        RequestShieldGeneratorOverload(
            side,
            turn,
            ref packageFullyFunded);
        RequestTacticalRecharge(side, ref packageFullyFunded);

        if (!offenseFirst)
        {
            ReserveWeaponCycle(
                side,
                turn,
                ref offensiveWeapon,
                ref offensiveEarmarkId,
                ref heldReady,
                ref heldWeapon,
                ref heldEarmarkId,
                ref packageFullyFunded);
        }

        if (packageFullyFunded)
        {
            side.FullPackageTurns++;
        }
        else
        {
            side.PartialPackageTurns++;
        }

        return new TurnSystemState(
            pdsReady,
            evasiveActive,
            sensorFirmRange,
            ecmRating,
            eccmRating,
            hardenerStrength,
            offensiveWeapon,
            offensiveEarmarkId,
            heldReady,
            heldWeapon,
            heldEarmarkId,
            packageFullyFunded);
    }

    private int EstimateDemand(SideRuntime side, int turn)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        int demand = 0;
        if (!profile.PdsFamily.Equals("none", StringComparison.OrdinalIgnoreCase) &&
            profile.PdsReactionCapacity > 0 &&
            HasPdsAmmunition(side))
        {
            demand += profile.PdsPowerCost;
        }
        demand += profile.SensorPower;
        demand += profile.EcmPower;
        demand += profile.EccmPower;
        demand += profile.ShieldHardenerPower;
        demand += profile.Evasive ? 1 : 0;

        bool safeTurn = turn <= profile.SafeOverloadTurnLimit;
        if (safeTurn && profile.SensorSafeOverload && profile.SensorPower > 0)
        {
            demand++;
        }
        if (safeTurn && profile.EcmSafeOverload && profile.EcmPower > 0)
        {
            demand++;
        }
        if (safeTurn && profile.EccmSafeOverload && profile.EccmPower > 0)
        {
            demand++;
        }
        if (safeTurn && profile.ShieldHardenerSafeOverload &&
            profile.ShieldHardenerPower > 0)
        {
            demand++;
        }
        if (safeTurn &&
            (profile.ShieldOvercapacitySafeOverload ||
             profile.ShieldRecoverySafeOverload))
        {
            demand++;
        }

        int missing = side.Combatant.Defense.EffectiveShieldMaximum -
            side.Combatant.Defense.CurrentShieldCapacity;
        demand += Math.Min(profile.TacticalShieldRechargePower, missing);

        if (profile.HeldInterception)
        {
            demand += ResolveHeldWeapon(side).Profile.TacticalPowerCost;
        }
        else if (!profile.Family.Equals("missile", StringComparison.OrdinalIgnoreCase))
        {
            demand += ResolveOffensiveWeapon(side, turn).Profile.TacticalPowerCost;
        }
        return demand;
    }

    private void ApplyThresholdPowerSources(SideRuntime side, int demand)
    {
        TacticalPowerLedger power = side.Combatant.Power;
        int shortfall = Math.Max(0, demand - power.Envelope);
        if (shortfall > 0 &&
            side.Profile.CapacitorDoctrine.Equals(
                "threshold-and-recharge",
                StringComparison.OrdinalIgnoreCase) &&
            side.Capacitor is not null &&
            shortfall <= side.Capacitor.DischargeRate &&
            shortfall <= side.Capacitor.StoredPower)
        {
            int discharged = side.Capacitor.Discharge(power, shortfall);
            side.CapacitorPowerDischarged += discharged;
            shortfall = Math.Max(0, demand - power.Envelope);
        }

        if (shortfall > 0 &&
            side.Profile.CombatBatteryDoctrine.Equals(
                "threshold",
                StringComparison.OrdinalIgnoreCase) &&
            side.CombatBattery is not null &&
            side.CombatBattery.CurrentCharges > 0 &&
            shortfall <= side.CombatBattery.PowerPerCharge)
        {
            int generated = side.CombatBattery.Discharge(power);
            side.CombatBatteryPower += generated;
            side.CombatBatteryChargesUsed++;
        }
    }

    private bool RequestPds(SideRuntime side, ref bool packageFullyFunded)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        bool requested = HasPdsAmmunition(side) &&
            !profile.PdsFamily.Equals("none", StringComparison.OrdinalIgnoreCase) &&
            profile.PdsReactionCapacity > 0;
        if (!requested)
        {
            return false;
        }
        if (!TryPowerSystem(side, "pds", profile.PdsPowerCost))
        {
            side.UnfundedPds++;
            packageFullyFunded = false;
            return false;
        }
        side.PdsPowerCommitted += profile.PdsPowerCost;
        return true;
    }

    private int RequestEcm(
        SideRuntime side,
        int turn,
        ref bool packageFullyFunded)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        if (profile.EcmPower <= 0)
        {
            return 0;
        }
        if (!TryPowerSystem(side, "ecm", profile.EcmPower))
        {
            side.UnfundedEcm++;
            packageFullyFunded = false;
            return 0;
        }
        side.EcmPowerCommitted += profile.EcmPower;
        int rating = profile.EcmPower;
        if (profile.EcmSafeOverload &&
            turn <= profile.SafeOverloadTurnLimit &&
            side.EcmStrain < SafeStrainLimit)
        {
            if (TryIncreaseSystem(side, "ecm", 1))
            {
                side.EcmPowerCommitted++;
                side.EcmStrain++;
                rating += EwOverloadRatingBonus;
            }
            else
            {
                side.UnfundedEcm++;
                packageFullyFunded = false;
            }
        }
        return rating;
    }

    private int RequestEccm(
        SideRuntime side,
        int turn,
        ref bool packageFullyFunded)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        if (profile.EccmPower <= 0)
        {
            return 0;
        }
        if (!TryPowerSystem(side, "eccm", profile.EccmPower))
        {
            side.UnfundedEccm++;
            packageFullyFunded = false;
            return 0;
        }
        side.EccmPowerCommitted += profile.EccmPower;
        int rating = profile.EccmPower;
        if (profile.EccmSafeOverload &&
            turn <= profile.SafeOverloadTurnLimit &&
            side.EccmStrain < SafeStrainLimit)
        {
            if (TryIncreaseSystem(side, "eccm", 1))
            {
                side.EccmPowerCommitted++;
                side.EccmStrain++;
                rating += EwOverloadRatingBonus;
            }
            else
            {
                side.UnfundedEccm++;
                packageFullyFunded = false;
            }
        }
        return rating;
    }

    private int RequestSensors(
        SideRuntime side,
        int turn,
        ref bool packageFullyFunded)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        if (profile.SensorPower <= 0)
        {
            return profile.PassiveFirmRange;
        }
        if (!TryPowerSystem(side, "active-sensors", profile.SensorPower))
        {
            side.UnfundedSensors++;
            packageFullyFunded = false;
            return profile.PassiveFirmRange;
        }
        side.SensorPowerCommitted += profile.SensorPower;
        int range = ResolveFirmRange(profile, profile.SensorPower);
        if (profile.SensorSafeOverload &&
            turn <= profile.SafeOverloadTurnLimit &&
            side.SensorStrain < SafeStrainLimit)
        {
            if (TryIncreaseSystem(side, "active-sensors", 1))
            {
                side.SensorPowerCommitted++;
                side.SensorStrain++;
                range += SensorOverloadRangeBonus;
            }
            else
            {
                side.UnfundedSensors++;
                packageFullyFunded = false;
            }
        }
        return range;
    }

    private int RequestHardener(
        SideRuntime side,
        int turn,
        ref bool packageFullyFunded)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        if (profile.ShieldHardenerPower <= 0)
        {
            return 0;
        }
        if (!TryPowerSystem(side, "shield-hardener", profile.ShieldHardenerPower))
        {
            side.UnfundedHardener++;
            packageFullyFunded = false;
            return 0;
        }
        side.ShieldHardenerPowerCommitted += profile.ShieldHardenerPower;
        int strength = profile.ShieldHardenerPower;
        if (profile.ShieldHardenerSafeOverload &&
            turn <= profile.SafeOverloadTurnLimit &&
            side.HardenerStrain < SafeStrainLimit)
        {
            if (TryIncreaseSystem(side, "shield-hardener", 1))
            {
                side.ShieldHardenerPowerCommitted++;
                side.HardenerStrain++;
                strength += ShieldHardenerOverloadBonus;
            }
            else
            {
                side.UnfundedHardener++;
                packageFullyFunded = false;
            }
        }
        return strength;
    }

    private void RequestShieldGeneratorOverload(
        SideRuntime side,
        int turn,
        ref bool packageFullyFunded)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        if (turn > profile.SafeOverloadTurnLimit ||
            side.ShieldGeneratorStrain >= SafeStrainLimit)
        {
            return;
        }

        LayeredDefenseState defense = side.Combatant.Defense;
        bool recovery = profile.ShieldRecoverySafeOverload &&
            defense.IsShieldCollapsed;
        bool overcapacity = profile.ShieldOvercapacitySafeOverload &&
            !defense.IsShieldCollapsed;
        if (!recovery && !overcapacity)
        {
            return;
        }

        if (side.Combatant.Power.SpendablePower <= 0)
        {
            side.UnfundedShieldOverload++;
            packageFullyFunded = false;
            return;
        }

        side.Combatant.Power.Spend(1);
        side.ShieldGeneratorStrain++;
        if (recovery)
        {
            side.PendingShieldRecoveryBonus = ShieldRecoveryBonus;
        }
        else
        {
            side.ShieldOvercapacityAdded +=
                defense.AddTemporaryShieldOvercapacity(ShieldOvercapacityAmount);
        }
    }

    private void RequestTacticalRecharge(
        SideRuntime side,
        ref bool packageFullyFunded)
    {
        int requested = side.Profile.TacticalShieldRechargePower;
        if (requested <= 0)
        {
            return;
        }
        LayeredDefenseState defense = side.Combatant.Defense;
        int missing = defense.EffectiveShieldMaximum - defense.CurrentShieldCapacity;
        int desired = Math.Min(requested, missing);
        if (desired <= 0)
        {
            return;
        }

        int funded = Math.Min(side.Combatant.Power.SpendablePower, desired);
        if (funded > 0)
        {
            side.Combatant.Power.Spend(funded);
            defense.RestoreShields(funded);
            side.ShieldRechargePowerSpent += funded;
        }
        if (funded < desired)
        {
            side.UnfundedRecharge++;
            packageFullyFunded = false;
        }
    }

    private void ReserveWeaponCycle(
        SideRuntime side,
        int turn,
        ref WeaponState? offensiveWeapon,
        ref string? offensiveEarmarkId,
        ref bool heldReady,
        ref WeaponState? heldWeapon,
        ref string? heldEarmarkId,
        ref bool packageFullyFunded)
    {
        Tl1PowerEnvelopeSideProfile profile = side.Profile;
        if (profile.HeldInterception)
        {
            side.HeldDeclarations++;
            side.OffensiveCyclesLost++;
            heldWeapon = ResolveHeldWeapon(side);
            int cost = heldWeapon.Profile.TacticalPowerCost;
            if (cost > side.Combatant.Power.SpendablePower)
            {
                side.UnfundedHeld++;
                packageFullyFunded = false;
                heldWeapon = null;
                return;
            }
            if (cost > 0)
            {
                heldEarmarkId = $"held-{side.Id}";
                side.Combatant.Power.Earmark(heldEarmarkId, cost);
                side.HeldPowerEarmarked += cost;
            }
            heldReady = true;
            return;
        }

        if (profile.Family.Equals("missile", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        offensiveWeapon = ResolveOffensiveWeapon(side, turn);
        int powerCost = offensiveWeapon.Profile.TacticalPowerCost;
        if (powerCost > side.Combatant.Power.SpendablePower &&
            profile.Family.Equals("energy", StringComparison.OrdinalIgnoreCase) &&
            offensiveWeapon.Profile.Mode.Equals("overload", StringComparison.OrdinalIgnoreCase))
        {
            side.UnfundedWeapon++;
            packageFullyFunded = false;
            offensiveWeapon = side.EnergyStandardWeapon;
            powerCost = offensiveWeapon!.Profile.TacticalPowerCost;
        }
        if (powerCost > side.Combatant.Power.SpendablePower)
        {
            side.UnfundedWeapon++;
            packageFullyFunded = false;
            offensiveWeapon = null;
            return;
        }
        if (powerCost > 0)
        {
            offensiveEarmarkId = $"weapon-{side.Id}";
            side.Combatant.Power.Earmark(offensiveEarmarkId, powerCost);
        }
    }

    private void CommitSide(
        SideRuntime attacker,
        SideRuntime target,
        TurnSystemState attackerSystems,
        TurnSystemState targetSystems,
        Func<int> nextRoll,
        List<SimultaneousDirectFireOrder> orders,
        List<PendingMissile> missiles,
        int currentRangeHexes)
    {
        if (!HasFirmTrack(
                attacker,
                target,
                attackerSystems,
                targetSystems,
                currentRangeHexes))
        {
            attacker.TrackDeniedTurns++;
            return;
        }
        attacker.FirmTrackTurns++;

        if (attacker.Profile.HeldInterception)
        {
            return;
        }

        if (attacker.Profile.Family.Equals("missile", StringComparison.OrdinalIgnoreCase))
        {
            if (attacker.MissileFeed is null ||
                attacker.MissileFeed.TotalPackages <= 0)
            {
                return;
            }

            int launchCount = Math.Min(
                attacker.Profile.MissileLaunchesPerTurn,
                attacker.MissileFeed.TotalPackages);
            for (int launchIndex = 0; launchIndex < launchCount; launchIndex++)
            {
                attacker.MissileFeed.Consume();
                attacker.Launches++;
                missiles.Add(new PendingMissile(
                    attacker.Id,
                    target.Combatant,
                    attacker.Profile,
                    currentRangeHexes));
            }
            return;
        }

        WeaponState? weapon = attackerSystems.OffensiveWeapon;
        if (weapon is null || weapon.CurrentAmmunition is 0)
        {
            return;
        }
        if (attackerSystems.OffensiveEarmarkId is not null)
        {
            attacker.Combatant.Power.ReleaseEarmark(
                attackerSystems.OffensiveEarmarkId);
        }

        var accuracy = new DirectFireAccuracyProfile(
            50,
            attacker.Profile.Accuracy,
            attacker.Profile.ComputerBonus,
            _profile.RangePenaltyPerHex,
            10,
            5);
        attacker.OffensiveWeaponPowerSpent += weapon.Profile.TacticalPowerCost;
        orders.Add(new SimultaneousDirectFireOrder(
            attacker.Combatant,
            target.Combatant,
            weapon,
            accuracy,
            currentRangeHexes,
            attackerSystems.EvasiveActive,
            targetSystems.EvasiveActive,
            nextRoll()));
        attacker.Shots++;
        if (weapon.Profile.Mode.Equals("overload", StringComparison.OrdinalIgnoreCase))
        {
            attacker.EnergyOverloadShots++;
            attacker.EnergyStrain++;
        }
    }

    private static bool ResolvePdsAgainstMissile(
        SideRuntime defender,
        TurnSystemState systems,
        ref int attemptsUsedThisTurn,
        Func<int> nextDefenseRoll)
    {
        if (!systems.PdsReady ||
            attemptsUsedThisTurn >= defender.Profile.PdsReactionCapacity ||
            !HasPdsAmmunition(defender))
        {
            return false;
        }

        attemptsUsedThisTurn++;
        defender.PdsAttempts++;
        if (!defender.Profile.PdsUnlimitedAmmunition)
        {
            defender.PdsFeed!.Consume();
        }

        bool amm = defender.Profile.PdsFamily.Equals(
            "amm",
            StringComparison.OrdinalIgnoreCase);
        int evasivePenalty = systems.EvasiveActive && !amm ? 5 : 0;
        int effectiveChance = Math.Clamp(
            defender.Profile.PdsInterceptionChance +
            defender.Profile.ComputerBonus -
            evasivePenalty,
            0,
            100);
        if (nextDefenseRoll() <= effectiveChance)
        {
            defender.PdsIntercepts++;
            return true;
        }
        return false;
    }

    private bool ResolveHeldInterception(
        SideRuntime defender,
        TurnSystemState systems,
        Func<int> nextHeldRoll)
    {
        if (!systems.HeldReady || systems.HeldUsed || systems.HeldWeapon is null)
        {
            return false;
        }

        systems.HeldUsed = true;
        defender.HeldAttempts++;
        if (systems.HeldEarmarkId is not null)
        {
            defender.Combatant.Power.TriggerEarmark(systems.HeldEarmarkId);
        }
        systems.HeldWeapon.ConsumeAmmunitionForHeldFire();

        var accuracy = new DirectFireAccuracyProfile(
            50,
            defender.Profile.Accuracy,
            defender.Profile.ComputerBonus,
            _profile.RangePenaltyPerHex,
            10,
            5);
        DirectFireAccuracyResult result = DirectFireAccuracyCalculator.Calculate(
            accuracy,
            0,
            targetEvasive: false,
            shooterEvasive: systems.EvasiveActive);
        DirectFireRollOutcome outcome = DirectFireHitResolver.Resolve(
            nextHeldRoll(),
            result.FinalChance);
        if (DirectFireHitResolver.IsHit(outcome))
        {
            defender.HeldIntercepts++;
            return true;
        }
        return false;
    }

    private void EndTurn(SideRuntime side, TurnSystemState systems)
    {
        if (systems.HeldReady && !systems.HeldUsed)
        {
            if (systems.HeldEarmarkId is not null)
            {
                side.Combatant.Power.ReleaseEarmark(systems.HeldEarmarkId);
            }
            side.HeldUnused++;
        }
        else if (systems.OffensiveEarmarkId is not null &&
                 side.Combatant.Power.Snapshot().Earmarks.Any(
                     earmark => earmark.EarmarkId == systems.OffensiveEarmarkId))
        {
            side.Combatant.Power.ReleaseEarmark(systems.OffensiveEarmarkId);
        }

        if (side.Profile.CapacitorDoctrine.Equals(
                "threshold-and-recharge",
                StringComparison.OrdinalIgnoreCase) &&
            side.Capacitor is not null &&
            !side.Capacitor.OperationUsedThisTurn &&
            side.Capacitor.StoredPower < side.Capacitor.Capacity &&
            side.Combatant.Power.SpendablePower > 0)
        {
            int charged = side.Capacitor.Charge(side.Combatant.Power, 1);
            side.CapacitorPowerCharged += charged;
        }

        TacticalPowerSnapshot snapshot = side.Combatant.Power.Snapshot();
        side.TotalEnvelope += snapshot.Envelope;
        side.TotalPowered += snapshot.Powered;
        side.TotalSpent += snapshot.Spent;
        side.TotalUnused += snapshot.Spendable;
    }

    private bool HasFirmTrack(
        SideRuntime attacker,
        SideRuntime target,
        TurnSystemState attackerSystems,
        TurnSystemState targetSystems,
        int currentRangeHexes)
    {
        if (!attacker.Profile.SensorTrackGateEnabled)
        {
            return true;
        }

        int netEcm = Math.Max(
            0,
            targetSystems.EcmRating - attackerSystems.EccmRating);
        int effectiveFirmRange = Math.Max(
            0,
            attackerSystems.SensorFirmRange - netEcm);
        return currentRangeHexes <= effectiveFirmRange;
    }

    private static bool TryPowerSystem(
        SideRuntime side,
        string systemId,
        int requestedPower)
    {
        if (requestedPower <= 0)
        {
            return true;
        }
        if (requestedPower > side.Combatant.Power.SpendablePower)
        {
            return false;
        }
        side.Combatant.Power.IncreasePoweredSystem(systemId, requestedPower);
        return true;
    }

    private static bool TryIncreaseSystem(
        SideRuntime side,
        string systemId,
        int additionalPower)
    {
        if (additionalPower > side.Combatant.Power.SpendablePower)
        {
            return false;
        }
        side.Combatant.Power.IncreasePoweredSystem(systemId, additionalPower);
        return true;
    }

    private static int ResolveFirmRange(
        Tl1PowerEnvelopeSideProfile profile,
        int sensorPower) => sensorPower switch
        {
            <= 0 => profile.PassiveFirmRange,
            1 => profile.ActiveFirmRangeAtOnePower,
            _ => profile.ActiveFirmRangeAtTwoPower,
        };

    private static bool HasPdsAmmunition(SideRuntime side) =>
        side.Profile.PdsUnlimitedAmmunition ||
        (side.PdsFeed is not null && side.PdsFeed.TotalPackages > 0);

    private static WeaponState ResolveHeldWeapon(SideRuntime side)
    {
        if (side.Profile.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase))
        {
            return side.KineticWeapon!;
        }
        if (!side.Profile.Family.Equals("energy", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "Only kinetic and energy weapons may use the current held-interception calibration.");
        }
        return side.Profile.HeldInterceptionMode.Equals(
                "low",
                StringComparison.OrdinalIgnoreCase)
            ? side.EnergyLowWeapon!
            : side.EnergyStandardWeapon!;
    }

    private static WeaponState ResolveOffensiveWeapon(SideRuntime side, int turn)
    {
        if (side.Profile.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase))
        {
            return side.KineticWeapon!;
        }
        if (!side.Profile.Family.Equals("energy", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "Missile launchers do not use direct-fire WeaponState selection.");
        }

        if (side.Profile.EnergySafeBurst &&
            turn <= side.Profile.SafeOverloadTurnLimit &&
            side.EnergyStrain < SafeStrainLimit)
        {
            return side.EnergyOverloadWeapon!;
        }
        return side.Profile.Doctrine.Equals("low", StringComparison.OrdinalIgnoreCase)
            ? side.EnergyLowWeapon!
            : side.EnergyStandardWeapon!;
    }

    private SideRuntime CreateSide(
        string id,
        Tl1PowerEnvelopeSideProfile profile)
    {
        DirectFireCombatant combatant = CreateCombatant(id);
        WeaponState? kineticWeapon = null;
        WeaponState? energyLowWeapon = null;
        WeaponState? energyStandardWeapon = null;
        WeaponState? energyOverloadWeapon = null;
        AmmunitionFeedState? missileFeed = null;

        if (profile.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase))
        {
            kineticWeapon = new WeaponState(new WeaponProfile(
                $"{id}-kinetic",
                WeaponFamily.Kinetic,
                "standard",
                new AttackPacket(4, 1, 0),
                1,
                1,
                profile.Ammunition));
        }
        else if (profile.Family.Equals("energy", StringComparison.OrdinalIgnoreCase))
        {
            energyLowWeapon = new WeaponState(new WeaponProfile(
                $"{id}-energy-low",
                WeaponFamily.Energy,
                "low",
                new AttackPacket(2, 0, 0),
                1,
                0,
                null));
            energyStandardWeapon = new WeaponState(new WeaponProfile(
                $"{id}-energy-standard",
                WeaponFamily.Energy,
                "standard",
                new AttackPacket(3, 1, 1),
                2,
                0,
                null));
            energyOverloadWeapon = new WeaponState(new WeaponProfile(
                $"{id}-energy-overload",
                WeaponFamily.Energy,
                "overload",
                new AttackPacket(4, 1, 1),
                3,
                0,
                null));
        }
        else
        {
            missileFeed = new AmmunitionFeedState(profile.Ammunition);
        }

        AmmunitionFeedState? pdsFeed =
            !profile.PdsUnlimitedAmmunition &&
            !profile.PdsFamily.Equals("none", StringComparison.OrdinalIgnoreCase)
                ? new AmmunitionFeedState(profile.PdsAmmunition)
                : null;
        CombatBatteryState? combatBattery = profile.CombatBatteryCharges > 0
            ? new CombatBatteryState(
                profile.CombatBatteryCharges,
                profile.CombatBatteryGain,
                1)
            : null;
        CapacitorBankState? capacitor = profile.CapacitorCapacity > 0
            ? new CapacitorBankState(
                profile.CapacitorCapacity,
                profile.CapacitorChargeRate,
                profile.CapacitorDischargeRate,
                profile.CapacitorStartingCharge)
            : null;

        return new SideRuntime(
            id,
            profile,
            combatant,
            kineticWeapon,
            energyLowWeapon,
            energyStandardWeapon,
            energyOverloadWeapon,
            missileFeed,
            pdsFeed,
            combatBattery,
            capacitor);
    }

    private DirectFireCombatant CreateCombatant(string id) =>
        new(
            id,
            new LayeredDefenseState(
                _profile.ShieldCapacity,
                _profile.ShieldCapacity,
                _profile.ShieldArmor,
                new[]
                {
                    new ArmorLayerState(
                        "primary",
                        _profile.ArmorProtection,
                        _profile.ArmorProtection,
                        _profile.ArmorIntegrity,
                        _profile.ArmorIntegrity),
                },
                _profile.Hull,
                _profile.Hull),
            new TacticalPowerLedger(),
            100,
            10);

    private static Tl1PowerEnvelopeResult CreateResult(
        Tl1DuelOutcome outcome,
        int turns,
        SideRuntime a,
        SideRuntime b,
        int initialRangeHexes,
        int finalRangeHexes,
        int rangeChangesApplied) => new()
        {
            Outcome = outcome,
            Turns = turns,
            ShotsA = a.Shots,
            ShotsB = b.Shots,
            HitsA = a.Hits,
            HitsB = b.Hits,
            LaunchesA = a.Launches,
            LaunchesB = b.Launches,
            MissileHitsA = a.MissileHits,
            MissileHitsB = b.MissileHits,
            AmmunitionA = a.RemainingAmmunition,
            AmmunitionB = b.RemainingAmmunition,
            SideA = a.Combatant,
            SideB = b.Combatant,
            PdsAttemptsA = a.PdsAttempts,
            PdsAttemptsB = b.PdsAttempts,
            PdsInterceptsA = a.PdsIntercepts,
            PdsInterceptsB = b.PdsIntercepts,
            HeldDeclarationsA = a.HeldDeclarations,
            HeldDeclarationsB = b.HeldDeclarations,
            HeldAttemptsA = a.HeldAttempts,
            HeldAttemptsB = b.HeldAttempts,
            HeldInterceptsA = a.HeldIntercepts,
            HeldInterceptsB = b.HeldIntercepts,
            HeldUnusedA = a.HeldUnused,
            HeldUnusedB = b.HeldUnused,
            HeldPowerEarmarkedA = a.HeldPowerEarmarked,
            HeldPowerEarmarkedB = b.HeldPowerEarmarked,
            OffensiveWeaponPowerSpentA = a.OffensiveWeaponPowerSpent,
            OffensiveWeaponPowerSpentB = b.OffensiveWeaponPowerSpent,
            OffensiveCyclesLostA = a.OffensiveCyclesLost,
            OffensiveCyclesLostB = b.OffensiveCyclesLost,
            FullPackageTurnsA = a.FullPackageTurns,
            FullPackageTurnsB = b.FullPackageTurns,
            PartialPackageTurnsA = a.PartialPackageTurns,
            PartialPackageTurnsB = b.PartialPackageTurns,
            UnfundedPdsA = a.UnfundedPds,
            UnfundedPdsB = b.UnfundedPds,
            UnfundedSensorsA = a.UnfundedSensors,
            UnfundedSensorsB = b.UnfundedSensors,
            UnfundedEcmA = a.UnfundedEcm,
            UnfundedEcmB = b.UnfundedEcm,
            UnfundedEccmA = a.UnfundedEccm,
            UnfundedEccmB = b.UnfundedEccm,
            UnfundedHardenerA = a.UnfundedHardener,
            UnfundedHardenerB = b.UnfundedHardener,
            UnfundedEvmA = a.UnfundedEvm,
            UnfundedEvmB = b.UnfundedEvm,
            UnfundedShieldOverloadA = a.UnfundedShieldOverload,
            UnfundedShieldOverloadB = b.UnfundedShieldOverload,
            UnfundedRechargeA = a.UnfundedRecharge,
            UnfundedRechargeB = b.UnfundedRecharge,
            UnfundedHeldA = a.UnfundedHeld,
            UnfundedHeldB = b.UnfundedHeld,
            UnfundedWeaponA = a.UnfundedWeapon,
            UnfundedWeaponB = b.UnfundedWeapon,
            BaseReactorPowerA = a.BaseReactorPower,
            BaseReactorPowerB = b.BaseReactorPower,
            AuxiliaryPowerA = a.AuxiliaryPower,
            AuxiliaryPowerB = b.AuxiliaryPower,
            ReactorOverloadPowerA = a.ReactorOverloadPower,
            ReactorOverloadPowerB = b.ReactorOverloadPower,
            CombatBatteryPowerA = a.CombatBatteryPower,
            CombatBatteryPowerB = b.CombatBatteryPower,
            CombatBatteryChargesUsedA = a.CombatBatteryChargesUsed,
            CombatBatteryChargesUsedB = b.CombatBatteryChargesUsed,
            CapacitorPowerDischargedA = a.CapacitorPowerDischarged,
            CapacitorPowerDischargedB = b.CapacitorPowerDischarged,
            CapacitorPowerChargedA = a.CapacitorPowerCharged,
            CapacitorPowerChargedB = b.CapacitorPowerCharged,
            CapacitorChargeA = a.Capacitor?.StoredPower ?? 0,
            CapacitorChargeB = b.Capacitor?.StoredPower ?? 0,
            TotalEnvelopeA = a.TotalEnvelope,
            TotalEnvelopeB = b.TotalEnvelope,
            TotalPoweredA = a.TotalPowered,
            TotalPoweredB = b.TotalPowered,
            TotalSpentA = a.TotalSpent,
            TotalSpentB = b.TotalSpent,
            TotalUnusedA = a.TotalUnused,
            TotalUnusedB = b.TotalUnused,
            PdsPowerCommittedA = a.PdsPowerCommitted,
            PdsPowerCommittedB = b.PdsPowerCommitted,
            SensorPowerCommittedA = a.SensorPowerCommitted,
            SensorPowerCommittedB = b.SensorPowerCommitted,
            EcmPowerCommittedA = a.EcmPowerCommitted,
            EcmPowerCommittedB = b.EcmPowerCommitted,
            EccmPowerCommittedA = a.EccmPowerCommitted,
            EccmPowerCommittedB = b.EccmPowerCommitted,
            ShieldHardenerPowerCommittedA = a.ShieldHardenerPowerCommitted,
            ShieldHardenerPowerCommittedB = b.ShieldHardenerPowerCommitted,
            ShieldRechargePowerSpentA = a.ShieldRechargePowerSpent,
            ShieldRechargePowerSpentB = b.ShieldRechargePowerSpent,
            ShieldOvercapacityAddedA = a.ShieldOvercapacityAdded,
            ShieldOvercapacityAddedB = b.ShieldOvercapacityAdded,
            EnergyOverloadShotsA = a.EnergyOverloadShots,
            EnergyOverloadShotsB = b.EnergyOverloadShots,
            ReactorStrainA = a.ReactorStrain,
            ReactorStrainB = b.ReactorStrain,
            EnergyStrainA = a.EnergyStrain,
            EnergyStrainB = b.EnergyStrain,
            SensorStrainA = a.SensorStrain,
            SensorStrainB = b.SensorStrain,
            EcmStrainA = a.EcmStrain,
            EcmStrainB = b.EcmStrain,
            EccmStrainA = a.EccmStrain,
            EccmStrainB = b.EccmStrain,
            HardenerStrainA = a.HardenerStrain,
            HardenerStrainB = b.HardenerStrain,
            ShieldGeneratorStrainA = a.ShieldGeneratorStrain,
            ShieldGeneratorStrainB = b.ShieldGeneratorStrain,
            FirmTrackTurnsA = a.FirmTrackTurns,
            FirmTrackTurnsB = b.FirmTrackTurns,
            TrackDeniedTurnsA = a.TrackDeniedTurns,
            TrackDeniedTurnsB = b.TrackDeniedTurns,
            RangeExhaustedA = a.RangeExhausted,
            RangeExhaustedB = b.RangeExhausted,
            InitialRangeHexes = initialRangeHexes,
            FinalRangeHexes = finalRangeHexes,
            RangeChangesApplied = rangeChangesApplied,
            MissileReroutesA = a.MissileReroutes,
            MissileReroutesB = b.MissileReroutes,
        };

    private static bool IsTerminal(DirectFireCombatant side) =>
        side.IsDestroyed || side.IsCrewMissionKilled;

    private static Tl1DuelOutcome DetermineOutcome(
        DirectFireCombatant a,
        DirectFireCombatant b)
    {
        bool aTerminal = IsTerminal(a);
        bool bTerminal = IsTerminal(b);
        if (a.IsDestroyed && b.IsDestroyed)
        {
            return Tl1DuelOutcome.MutualDestruction;
        }
        if (aTerminal && bTerminal)
        {
            return Tl1DuelOutcome.MixedTerminal;
        }
        if (aTerminal)
        {
            return Tl1DuelOutcome.SideBWins;
        }
        if (bTerminal)
        {
            return Tl1DuelOutcome.SideAWins;
        }
        return Tl1DuelOutcome.Unresolved;
    }

    private static void Validate(Tl1PowerEnvelopeProfile profile)
    {
        _ = new Tl1RelativeRangeSchedule(
            profile.RangeHexes,
            profile.TurnCap,
            profile.RangeSchedule);

        foreach (Tl1PowerEnvelopeSideProfile side in
                 new[] { profile.SideA, profile.SideB })
        {
            if (!new[] { "kinetic", "energy", "missile" }.Contains(
                    side.Family,
                    StringComparer.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "Family must be kinetic, energy, or missile.");
            }
            if (!new[] { "defense-first", "offense-first" }.Contains(
                    side.PowerPriority,
                    StringComparer.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "Power priority must be defense-first or offense-first.");
            }
            if (!new[] { "none", "threshold" }.Contains(
                    side.CombatBatteryDoctrine,
                    StringComparer.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "Combat Battery doctrine must be none or threshold.");
            }
            if (!new[] { "none", "threshold-and-recharge" }.Contains(
                    side.CapacitorDoctrine,
                    StringComparer.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "Capacitor doctrine must be none or threshold-and-recharge.");
            }
            if (side.HeldInterception &&
                side.Family.Equals("missile", StringComparison.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "The current held-interception calibration supports only kinetic and energy weapons.");
            }
            if (side.ReactorOutput < 0 ||
                side.AuxiliaryReactorOutput < 0 ||
                side.Ammunition < 0 ||
                side.MissileSpeed < 0 ||
                side.MissileRange < 0 ||
                side.MissileLaunchesPerTurn <= 0 ||
                side.SafeOverloadTurnLimit < 0 ||
                side.CombatBatteryCharges < 0 ||
                side.CombatBatteryGain <= 0 ||
                side.CapacitorCapacity < 0 ||
                side.CapacitorStartingCharge < 0 ||
                side.CapacitorStartingCharge > side.CapacitorCapacity ||
                side.CapacitorChargeRate <= 0 ||
                side.CapacitorDischargeRate <= 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(profile),
                    "TL1 power-envelope source and weapon values are invalid.");
            }
            if (side.SensorPower is < 0 or > 2 ||
                side.EcmPower is < 0 or > 1 ||
                side.EccmPower is < 0 or > 1 ||
                side.ShieldHardenerPower is < 0 or > 1 ||
                side.TacticalShieldRechargePower is < 0 or > 2)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(profile),
                    "TL1 consumer settings exceed their normal calibration bounds.");
            }
            if (!new[] { "none", "kinetic", "amm", "energy" }.Contains(
                    side.PdsFamily,
                    StringComparer.OrdinalIgnoreCase) ||
                side.PdsPowerCost < 0 ||
                side.PdsReactionCapacity < 0 ||
                side.PdsInterceptionChance is < 0 or > 100 ||
                side.PdsAmmunition < 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(profile),
                    "PDS settings are invalid.");
            }
        }
    }
}
