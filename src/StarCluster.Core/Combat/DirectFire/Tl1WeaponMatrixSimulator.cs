using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.Core.Combat.DirectFire;

public sealed record Tl1WeaponMatrixSideProfile(
    string Family,
    string Doctrine,
    int Accuracy,
    int ComputerBonus,
    bool Evasive,
    int ReactorOutput,
    int Ammunition,
    int MissileGuidance,
    int MissileDamage,
    int MissileShieldPenetration,
    int MissileArmorPenetration,
    int MissileSpeed,
    int MissileRange,
    int TargetMovePerTurn = 0,
    int MissileLaunchesPerTurn = 1,
    string PdsFamily = "none",
    int PdsPowerCost = 0,
    int PdsReactionCapacity = 0,
    int PdsInterceptionChance = 0,
    int PdsAmmunition = 0,
    bool PdsUnlimitedAmmunition = false,
    bool SensorTrackGateEnabled = false,
    int PassiveFirmRange = 3,
    int ActiveFirmRangeAtOnePower = 5,
    int ActiveFirmRangeAtTwoPower = 6,
    int SensorPower = 0,
    int EcmPower = 0,
    int EccmPower = 0,
    int ShieldHardenerPower = 0,
    int TacticalShieldRechargePower = 0,
    int ShieldBatteryCharges = 0,
    int ShieldBatteryRestore = 0);

public sealed record Tl1WeaponMatrixProfile(
    int ShieldCapacity,
    int ShieldArmor,
    int BaseShieldRecharge,
    int ArmorProtection,
    int ArmorIntegrity,
    int Hull,
    int RangeHexes,
    int RangePenaltyPerHex,
    int TurnCap,
    Tl1WeaponMatrixSideProfile SideA,
    Tl1WeaponMatrixSideProfile SideB,
    IReadOnlyList<Tl1RelativeRangeChange>? RangeSchedule = null);

public sealed record Tl1WeaponMatrixResult(
    Tl1DuelOutcome Outcome,
    int Turns,
    int ShotsA,
    int ShotsB,
    int HitsA,
    int HitsB,
    int LaunchesA,
    int LaunchesB,
    int MissileHitsA,
    int MissileHitsB,
    int RangeExhaustedA,
    int RangeExhaustedB,
    int AmmunitionA,
    int AmmunitionB,
    DirectFireCombatant SideA,
    DirectFireCombatant SideB,
    int PdsAttemptsA,
    int PdsAttemptsB,
    int PdsInterceptsA,
    int PdsInterceptsB,
    int PdsEntryAttemptsA,
    int PdsEntryAttemptsB,
    int PdsPreAttackAttemptsA,
    int PdsPreAttackAttemptsB,
    int PdsAmmunitionA,
    int PdsAmmunitionB,
    int PdsPowerCommittedA,
    int PdsPowerCommittedB,
    int MissilesReachedGuidanceA,
    int MissilesReachedGuidanceB,
    int ReadyAmmunitionA,
    int ReadyAmmunitionB,
    int ReserveAmmunitionA,
    int ReserveAmmunitionB,
    int PdsReadyAmmunitionA,
    int PdsReadyAmmunitionB,
    int PdsReserveAmmunitionA,
    int PdsReserveAmmunitionB,
    int FirmTrackTurnsA,
    int FirmTrackTurnsB,
    int TrackDeniedTurnsA,
    int TrackDeniedTurnsB,
    int SensorPowerCommittedA,
    int SensorPowerCommittedB,
    int EcmPowerCommittedA,
    int EcmPowerCommittedB,
    int EccmPowerCommittedA,
    int EccmPowerCommittedB,
    int ShieldHardenerPowerCommittedA,
    int ShieldHardenerPowerCommittedB,
    int ShieldRechargePowerSpentA,
    int ShieldRechargePowerSpentB,
    int ShieldBatteryChargesUsedA,
    int ShieldBatteryChargesUsedB,
    int InitialRangeHexes,
    int FinalRangeHexes,
    int RangeChangesApplied,
    int MissileReroutesA,
    int MissileReroutesB);

public sealed class Tl1WeaponMatrixSimulator
{
    private sealed class PendingMissile
    {
        public PendingMissile(
            string owner,
            DirectFireCombatant target,
            Tl1WeaponMatrixSideProfile profile,
            int distance)
        {
            Owner = owner;
            Target = target;
            Profile = profile;
            Distance = distance;
        }

        public string Owner { get; }

        public DirectFireCombatant Target { get; }

        public Tl1WeaponMatrixSideProfile Profile { get; }

        public int Distance { get; set; }

        public int Traveled { get; set; }
    }

    private sealed class SideRuntime
    {
        public SideRuntime(
            string id,
            Tl1WeaponMatrixSideProfile profile,
            DirectFireCombatant combatant,
            WeaponState? directFireWeapon,
            AmmunitionFeedState? missileFeed,
            AmmunitionFeedState? pdsFeed)
        {
            Id = id;
            Profile = profile;
            Combatant = combatant;
            DirectFireWeapon = directFireWeapon;
            MissileFeed = missileFeed;
            PdsFeed = pdsFeed;
            ShieldBatteryCharges = profile.ShieldBatteryCharges;
        }

        public string Id { get; }

        public Tl1WeaponMatrixSideProfile Profile { get; }

        public DirectFireCombatant Combatant { get; }

        public WeaponState? DirectFireWeapon { get; }

        public AmmunitionFeedState? MissileFeed { get; }

        public AmmunitionFeedState? PdsFeed { get; }

        public int ShieldBatteryCharges { get; set; }

        public int Shots { get; set; }

        public int Hits { get; set; }

        public int Launches { get; set; }

        public int MissileHits { get; set; }

        public int RangeExhausted { get; set; }

        public int MissileReroutes { get; set; }

        public int PdsAttempts { get; set; }

        public int PdsIntercepts { get; set; }

        public int PdsEntryAttempts { get; set; }

        public int PdsPreAttackAttempts { get; set; }

        public int PdsPowerCommitted { get; set; }

        public int MissilesReachedGuidance { get; set; }

        public int FirmTrackTurns { get; set; }

        public int TrackDeniedTurns { get; set; }

        public int SensorPowerCommitted { get; set; }

        public int EcmPowerCommitted { get; set; }

        public int EccmPowerCommitted { get; set; }

        public int ShieldHardenerPowerCommitted { get; set; }

        public int ShieldRechargePowerSpent { get; set; }

        public int ShieldBatteryChargesUsed { get; set; }

        public int RemainingAmmunition =>
            DirectFireWeapon?.CurrentAmmunition ??
            MissileFeed?.TotalPackages ??
            0;

        public int ReadyAmmunition =>
            DirectFireWeapon?.ReadyAmmunition ??
            MissileFeed?.ReadyPackages ??
            0;

        public int ReserveAmmunition =>
            DirectFireWeapon?.ReserveAmmunition ??
            MissileFeed?.ReservePackages ??
            0;

        public int RemainingPdsAmmunition =>
            Profile.PdsUnlimitedAmmunition ? 0 : PdsFeed?.TotalPackages ?? 0;

        public int ReadyPdsAmmunition =>
            Profile.PdsUnlimitedAmmunition ? 0 : PdsFeed?.ReadyPackages ?? 0;

        public int ReservePdsAmmunition =>
            Profile.PdsUnlimitedAmmunition ? 0 : PdsFeed?.ReservePackages ?? 0;
    }

    private sealed record TurnSystemState(
        bool PdsReady,
        bool EvasiveActive,
        int SensorPower,
        int SensorFirmRange,
        int EcmRating,
        int EccmRating,
        int ShieldHardenerStrength)
    {
        public static TurnSystemState Inactive { get; } = new(
            false,
            false,
            0,
            0,
            0,
            0,
            0);
    }

    private readonly Tl1WeaponMatrixProfile _profile;

    public Tl1WeaponMatrixSimulator(Tl1WeaponMatrixProfile profile)
    {
        _profile = profile ?? throw new ArgumentNullException(nameof(profile));
        Validate(profile);
    }

    public Tl1WeaponMatrixResult Run(
        Func<int> nextRollA,
        Func<int> nextRollB,
        Func<int>? nextPdsRollA = null,
        Func<int>? nextPdsRollB = null)
    {
        ArgumentNullException.ThrowIfNull(nextRollA);
        ArgumentNullException.ThrowIfNull(nextRollB);
        Func<int> pdsRollA = nextPdsRollA ?? nextRollA;
        Func<int> pdsRollB = nextPdsRollB ?? nextRollB;

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
            TurnSystemState systemsA = IsTerminal(a.Combatant)
                ? TurnSystemState.Inactive
                : BeginTurn(a);
            TurnSystemState systemsB = IsTerminal(b.Combatant)
                ? TurnSystemState.Inactive
                : BeginTurn(b);
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
                    systemsA,
                    systemsB,
                    nextRollA,
                    orders,
                    missiles,
                    currentRangeHexes);
                CommitSide(
                    b,
                    a,
                    systemsB,
                    systemsA,
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
                TurnSystemState targetSystems = target.Id == "A"
                    ? systemsA
                    : systemsB;
                ref int attemptsUsedThisTurn = ref (target.Id == "A"
                    ? ref pdsAttemptsThisTurnA
                    : ref pdsAttemptsThisTurnB);

                bool intercepted = ResolvePdsAgainstMissile(
                    target,
                    targetSystems,
                    ref attemptsUsedThisTurn,
                    target.Id == "A" ? pdsRollA : pdsRollB);
                if (intercepted)
                {
                    continue;
                }

                owner.MissilesReachedGuidance++;
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

            if (IsTerminal(a.Combatant) || IsTerminal(b.Combatant))
            {
                bool threatA = missiles.Any(
                    missile =>
                        missile.Owner == "A" && !missile.Target.IsDestroyed);
                bool threatB = missiles.Any(
                    missile =>
                        missile.Owner == "B" && !missile.Target.IsDestroyed);
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

        if (attacker.Profile.Family.Equals(
                "missile",
                StringComparison.OrdinalIgnoreCase))
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

        WeaponState? weapon = attacker.DirectFireWeapon;
        if (weapon is null ||
            attacker.Combatant.Power.SpendablePower <
            weapon.Profile.TacticalPowerCost ||
            weapon.CurrentAmmunition is 0)
        {
            return;
        }

        var accuracy = new DirectFireAccuracyProfile(
            50,
            attacker.Profile.Accuracy,
            attacker.Profile.ComputerBonus,
            _profile.RangePenaltyPerHex,
            10,
            5);
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
    }

    private TurnSystemState BeginTurn(SideRuntime side)
    {
        Tl1WeaponMatrixSideProfile profile = side.Profile;
        DirectFireCombatant combatant = side.Combatant;
        combatant.Power.BeginTurn(profile.ReactorOutput);

        bool collapsedAtTurnStart = combatant.Defense.IsShieldCollapsed;
        combatant.Defense.ClearTemporaryShieldOvercapacity();
        combatant.Defense.ShieldArmor = _profile.ShieldArmor;
        combatant.Defense.RestoreShields(_profile.BaseShieldRecharge);

        if (collapsedAtTurnStart &&
            side.ShieldBatteryCharges > 0 &&
            profile.ShieldBatteryRestore > 0)
        {
            side.ShieldBatteryCharges--;
            side.ShieldBatteryChargesUsed++;
            combatant.Defense.RestoreShields(profile.ShieldBatteryRestore);
        }

        bool pdsReady = HasPdsAmmunition(side) &&
            !profile.PdsFamily.Equals("none", StringComparison.OrdinalIgnoreCase) &&
            profile.PdsReactionCapacity > 0 &&
            profile.PdsPowerCost <= combatant.Power.SpendablePower;
        if (pdsReady && profile.PdsPowerCost > 0)
        {
            combatant.Power.IncreasePoweredSystem("pds", profile.PdsPowerCost);
            side.PdsPowerCommitted += profile.PdsPowerCost;
        }

        int ecmPower = CommitPoweredSystem(
            combatant.Power,
            "ecm",
            profile.EcmPower);
        side.EcmPowerCommitted += ecmPower;

        int eccmPower = CommitPoweredSystem(
            combatant.Power,
            "eccm",
            profile.EccmPower);
        side.EccmPowerCommitted += eccmPower;

        int sensorPower = CommitPoweredSystem(
            combatant.Power,
            "active-sensors",
            profile.SensorPower);
        side.SensorPowerCommitted += sensorPower;

        int hardenerPower = CommitPoweredSystem(
            combatant.Power,
            "shield-hardener",
            profile.ShieldHardenerPower);
        side.ShieldHardenerPowerCommitted += hardenerPower;
        combatant.Defense.ShieldArmor = checked(
            _profile.ShieldArmor + hardenerPower);

        bool evasiveActive = profile.Evasive &&
            combatant.Power.SpendablePower > 0;
        if (evasiveActive)
        {
            combatant.Power.Spend(1);
        }

        int missingShield =
            combatant.Defense.EffectiveShieldMaximum -
            combatant.Defense.CurrentShieldCapacity;
        int rechargePower = Math.Min(
            profile.TacticalShieldRechargePower,
            Math.Min(combatant.Power.SpendablePower, missingShield));
        if (rechargePower > 0)
        {
            combatant.Power.Spend(rechargePower);
            combatant.Defense.RestoreShields(rechargePower);
            side.ShieldRechargePowerSpent += rechargePower;
        }

        return new TurnSystemState(
            pdsReady,
            evasiveActive,
            sensorPower,
            ResolveFirmRange(profile, sensorPower),
            ecmPower,
            eccmPower,
            hardenerPower);
    }

    private static int CommitPoweredSystem(
        TacticalPowerLedger power,
        string systemId,
        int requestedPower)
    {
        if (requestedPower <= 0 || requestedPower > power.SpendablePower)
        {
            return 0;
        }

        power.IncreasePoweredSystem(systemId, requestedPower);
        return requestedPower;
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

    private static int ResolveFirmRange(
        Tl1WeaponMatrixSideProfile profile,
        int sensorPower) => sensorPower switch
        {
            <= 0 => profile.PassiveFirmRange,
            1 => profile.ActiveFirmRangeAtOnePower,
            _ => profile.ActiveFirmRangeAtTwoPower,
        };

    private static bool ResolvePdsAgainstMissile(
        SideRuntime defender,
        TurnSystemState systems,
        ref int attemptsUsedThisTurn,
        Func<int> nextDefenseRoll)
    {
        if (!systems.PdsReady)
        {
            return false;
        }

        if (AttemptPds(
                defender,
                systems,
                ref attemptsUsedThisTurn,
                nextDefenseRoll,
                terminalEntry: true))
        {
            defender.PdsIntercepts++;
            return true;
        }

        if (AttemptPds(
                defender,
                systems,
                ref attemptsUsedThisTurn,
                nextDefenseRoll,
                terminalEntry: false))
        {
            defender.PdsIntercepts++;
            return true;
        }

        return false;
    }

    private static bool AttemptPds(
        SideRuntime defender,
        TurnSystemState systems,
        ref int attemptsUsedThisTurn,
        Func<int> nextDefenseRoll,
        bool terminalEntry)
    {
        if (attemptsUsedThisTurn >= defender.Profile.PdsReactionCapacity ||
            !HasPdsAmmunition(defender))
        {
            return false;
        }

        attemptsUsedThisTurn++;
        defender.PdsAttempts++;
        if (terminalEntry)
        {
            defender.PdsEntryAttempts++;
        }
        else
        {
            defender.PdsPreAttackAttempts++;
        }

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
        return nextDefenseRoll() <= effectiveChance;
    }

    private static bool HasPdsAmmunition(SideRuntime side) =>
        side.Profile.PdsUnlimitedAmmunition ||
        (side.PdsFeed is not null && side.PdsFeed.TotalPackages > 0);

    private SideRuntime CreateSide(
        string id,
        Tl1WeaponMatrixSideProfile profile)
    {
        DirectFireCombatant combatant = CreateCombatant(id);
        WeaponState? directFireWeapon = CreateDirectFireWeapon(id, profile);
        AmmunitionFeedState? missileFeed = profile.Family.Equals(
                "missile",
                StringComparison.OrdinalIgnoreCase)
            ? new AmmunitionFeedState(profile.Ammunition)
            : null;
        AmmunitionFeedState? pdsFeed =
            !profile.PdsUnlimitedAmmunition &&
            !profile.PdsFamily.Equals("none", StringComparison.OrdinalIgnoreCase)
                ? new AmmunitionFeedState(profile.PdsAmmunition)
                : null;
        return new SideRuntime(
            id,
            profile,
            combatant,
            directFireWeapon,
            missileFeed,
            pdsFeed);
    }

    private static WeaponState? CreateDirectFireWeapon(
        string id,
        Tl1WeaponMatrixSideProfile side)
    {
        if (side.Family.Equals("missile", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        WeaponProfile weapon;
        if (side.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase))
        {
            weapon = new WeaponProfile(
                $"{id}-kinetic",
                WeaponFamily.Kinetic,
                "standard",
                new AttackPacket(4, 1, 0),
                1,
                1,
                side.Ammunition);
        }
        else if (side.Doctrine.Equals("low", StringComparison.OrdinalIgnoreCase))
        {
            weapon = new WeaponProfile(
                $"{id}-energy-low",
                WeaponFamily.Energy,
                "low",
                new AttackPacket(2, 0, 0),
                1,
                0,
                null);
        }
        else
        {
            weapon = new WeaponProfile(
                $"{id}-energy",
                WeaponFamily.Energy,
                "standard",
                new AttackPacket(3, 1, 1),
                2,
                0,
                null);
        }

        return new WeaponState(weapon);
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

    private static Tl1WeaponMatrixResult CreateResult(
        Tl1DuelOutcome outcome,
        int turns,
        SideRuntime a,
        SideRuntime b,
        int initialRangeHexes,
        int finalRangeHexes,
        int rangeChangesApplied) => new(
            outcome,
            turns,
            a.Shots,
            b.Shots,
            a.Hits,
            b.Hits,
            a.Launches,
            b.Launches,
            a.MissileHits,
            b.MissileHits,
            a.RangeExhausted,
            b.RangeExhausted,
            a.RemainingAmmunition,
            b.RemainingAmmunition,
            a.Combatant,
            b.Combatant,
            a.PdsAttempts,
            b.PdsAttempts,
            a.PdsIntercepts,
            b.PdsIntercepts,
            a.PdsEntryAttempts,
            b.PdsEntryAttempts,
            a.PdsPreAttackAttempts,
            b.PdsPreAttackAttempts,
            a.RemainingPdsAmmunition,
            b.RemainingPdsAmmunition,
            a.PdsPowerCommitted,
            b.PdsPowerCommitted,
            a.MissilesReachedGuidance,
            b.MissilesReachedGuidance,
            a.ReadyAmmunition,
            b.ReadyAmmunition,
            a.ReserveAmmunition,
            b.ReserveAmmunition,
            a.ReadyPdsAmmunition,
            b.ReadyPdsAmmunition,
            a.ReservePdsAmmunition,
            b.ReservePdsAmmunition,
            a.FirmTrackTurns,
            b.FirmTrackTurns,
            a.TrackDeniedTurns,
            b.TrackDeniedTurns,
            a.SensorPowerCommitted,
            b.SensorPowerCommitted,
            a.EcmPowerCommitted,
            b.EcmPowerCommitted,
            a.EccmPowerCommitted,
            b.EccmPowerCommitted,
            a.ShieldHardenerPowerCommitted,
            b.ShieldHardenerPowerCommitted,
            a.ShieldRechargePowerSpent,
            b.ShieldRechargePowerSpent,
            a.ShieldBatteryChargesUsed,
            b.ShieldBatteryChargesUsed,
            initialRangeHexes,
            finalRangeHexes,
            rangeChangesApplied,
            a.MissileReroutes,
            b.MissileReroutes);

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

    private static void Validate(Tl1WeaponMatrixProfile profile)
    {
        _ = new Tl1RelativeRangeSchedule(
            profile.RangeHexes,
            profile.TurnCap,
            profile.RangeSchedule);

        foreach (Tl1WeaponMatrixSideProfile side in
                 new[] { profile.SideA, profile.SideB })
        {
            if (!new[] { "kinetic", "energy", "missile" }.Contains(
                    side.Family,
                    StringComparer.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "Family must be kinetic, energy, or missile.");
            }

            if (side.Ammunition < 0 ||
                side.ReactorOutput < 0 ||
                side.MissileSpeed < 0 ||
                side.MissileRange < 0 ||
                side.MissileLaunchesPerTurn <= 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(profile),
                    "Weapon, power, and missile values must be non-negative, " +
                    "and missile launches per turn must be positive.");
            }

            if (!new[] { "none", "kinetic", "amm", "energy" }.Contains(
                    side.PdsFamily,
                    StringComparer.OrdinalIgnoreCase))
            {
                throw new ArgumentException(
                    "PDS family must be none, kinetic, amm, or energy.");
            }

            if (side.PdsPowerCost < 0 ||
                side.PdsReactionCapacity < 0 ||
                side.PdsInterceptionChance is < 0 or > 100 ||
                side.PdsAmmunition < 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(profile),
                    "PDS power, reaction, chance, and ammunition values are invalid.");
            }

            if (!side.PdsFamily.Equals("none", StringComparison.OrdinalIgnoreCase) &&
                side.PdsReactionCapacity == 0)
            {
                throw new ArgumentException(
                    "An installed PDS requires positive reaction capacity.");
            }

            if (side.PassiveFirmRange < 0 ||
                side.ActiveFirmRangeAtOnePower < side.PassiveFirmRange ||
                side.ActiveFirmRangeAtTwoPower < side.ActiveFirmRangeAtOnePower ||
                side.SensorPower is < 0 or > 2 ||
                side.EcmPower is < 0 or > 1 ||
                side.EccmPower is < 0 or > 1 ||
                side.ShieldHardenerPower is < 0 or > 1 ||
                side.TacticalShieldRechargePower is < 0 or > 2 ||
                side.ShieldBatteryCharges < 0 ||
                side.ShieldBatteryRestore < 0)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(profile),
                    "TL1 sensor, EW, Shield Hardener, recharge, or battery values are invalid.");
            }
        }
    }
}
