using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.Core.Combat.DirectFire;

public sealed record Tl1EnergyDuelResult(
    Tl1DuelOutcome Outcome,
    int Turns,
    int ShotsA,
    int ShotsB,
    int HitsA,
    int HitsB,
    int TacticalPowerSpentA,
    int TacticalPowerSpentB,
    int TacticalShieldRestoredA,
    int TacticalShieldRestoredB,
    int SafeOverloadShotsA,
    int SafeOverloadShotsB,
    DirectFireCombatant SideA,
    DirectFireCombatant SideB,
    int AmmunitionA,
    int AmmunitionB);

public sealed class Tl1EnergyDuelSimulator
{
    private readonly Tl1EnergyCalibrationProfile _profile;

    public Tl1EnergyDuelSimulator(Tl1EnergyCalibrationProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);
        Validate(profile);
        _profile = profile;
    }

    public Tl1EnergyDuelResult Run(Func<int> nextRollA, Func<int> nextRollB)
    {
        ArgumentNullException.ThrowIfNull(nextRollA);
        ArgumentNullException.ThrowIfNull(nextRollB);
        DirectFireCombatant a = CreateCombatant("A");
        DirectFireCombatant b = CreateCombatant("B");
        int shotsA = 0, shotsB = 0, hitsA = 0, hitsB = 0;
        int powerA = 0, powerB = 0, rechargeA = 0, rechargeB = 0;
        int safeOverloadsA = 0, safeOverloadsB = 0;
        int ammunitionA = _profile.SideA.Ammunition;
        int ammunitionB = _profile.SideB.Ammunition;
        int turns = 0;

        for (int turn = 1; turn <= _profile.TurnCap; turn++)
        {
            turns = turn;
            BeginTurn(a, _profile.SideA, turn, ref powerA, ref rechargeA);
            BeginTurn(b, _profile.SideB, turn, ref powerB, ref rechargeB);

            WeaponProfile? profileA = SelectWeapon(_profile.SideA, turn);
            WeaponProfile? profileB = SelectWeapon(_profile.SideB, turn);
            bool canA = CanFire(a, _profile.SideA, profileA, ammunitionA);
            bool canB = CanFire(b, _profile.SideB, profileB, ammunitionB);
            if (!canA && !canB) break;
            if (canA && IsSafeOverloadTurn(_profile.SideA, turn)) safeOverloadsA++;
            if (canB && IsSafeOverloadTurn(_profile.SideB, turn)) safeOverloadsB++;

            var orders = new List<SimultaneousDirectFireOrder>(2);
            WeaponState? weaponA = null;
            WeaponState? weaponB = null;
            if (canA && profileA is not null)
            {
                weaponA = CreateWeapon(profileA, ammunitionA);
                shotsA++;
                orders.Add(CreateOrder(a, b, weaponA, _profile.SideA, _profile.SideB, nextRollA()));
            }
            if (canB && profileB is not null)
            {
                weaponB = CreateWeapon(profileB, ammunitionB);
                shotsB++;
                orders.Add(CreateOrder(b, a, weaponB, _profile.SideB, _profile.SideA, nextRollB()));
            }

            SimultaneousDirectFireBatchResult batch = SimultaneousDirectFireResolver.Resolve(orders);
            foreach (SimultaneousDirectFireAttackResult attack in batch.Attacks)
            {
                bool hit = attack.Outcome is DirectFireRollOutcome.Hit or DirectFireRollOutcome.CriticalHit;
                if (attack.AttackerId == "A")
                {
                    powerA += attack.FireResult.TacticalPowerSpent;
                    if (weaponA?.CurrentAmmunition is int remaining) ammunitionA = remaining;
                    if (hit) hitsA++;
                }
                else
                {
                    powerB += attack.FireResult.TacticalPowerSpent;
                    if (weaponB?.CurrentAmmunition is int remaining) ammunitionB = remaining;
                    if (hit) hitsB++;
                }
            }
            if (IsTerminal(a) || IsTerminal(b))
                return MakeResult(DetermineOutcome(a, b), turn);
        }
        return MakeResult(DetermineOutcome(a, b), turns);

        Tl1EnergyDuelResult MakeResult(Tl1DuelOutcome outcome, int resolvedTurns) => new(
            outcome, resolvedTurns, shotsA, shotsB, hitsA, hitsB,
            powerA, powerB, rechargeA, rechargeB, safeOverloadsA, safeOverloadsB,
            a, b, ammunitionA, ammunitionB);
    }

    private void BeginTurn(DirectFireCombatant side, Tl1EnergySideProfile profile, int turn, ref int totalPower, ref int tacticalRestored)
    {
        side.Power.BeginTurn(profile.ReactorOutput);
        side.Defense.RestoreShields(_profile.BaseShieldRecharge);
        if (profile.Evasive)
        {
            side.Power.Spend(1);
            totalPower++;
        }
        int weaponReserve = WeaponCostForTurn(profile, turn);
        int missing = Math.Max(0, _profile.ShieldCapacity - side.Defense.CurrentShieldCapacity);
        int requested = Math.Min(profile.TacticalShieldRecharge, missing);
        int affordable = Math.Max(0, side.Power.SpendablePower - weaponReserve);
        int recharge = Math.Min(requested, affordable);
        if (recharge > 0)
        {
            side.Power.Spend(recharge);
            side.Defense.RestoreShields(recharge);
            totalPower += recharge;
            tacticalRestored += recharge;
        }
    }

    private static int WeaponCostForTurn(Tl1EnergySideProfile profile, int turn) => profile.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase)
        ? 1
        : profile.Doctrine.Equals("low", StringComparison.OrdinalIgnoreCase) ? 1
        : profile.Doctrine.Equals("safe-burst", StringComparison.OrdinalIgnoreCase) && turn <= 2 ? 3
        : 2;

    private static WeaponProfile? SelectWeapon(Tl1EnergySideProfile side, int turn)
    {
        if (side.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase))
            return new WeaponProfile("kinetic", WeaponFamily.Kinetic, "standard", new AttackPacket(4, 1, 0), 1, 1, side.Ammunition);
        if (side.Doctrine.Equals("low", StringComparison.OrdinalIgnoreCase))
            return new WeaponProfile("energy-low", WeaponFamily.Energy, "low", new AttackPacket(2, 0, 0), 1, 0, null);
        if (side.Doctrine.Equals("safe-burst", StringComparison.OrdinalIgnoreCase) && turn <= 2)
        {
            return new WeaponProfile("energy-overload", WeaponFamily.Energy, "overload", new AttackPacket(4, 1, 1), 3, 0, null);
        }
        return new WeaponProfile("energy-standard", WeaponFamily.Energy, "standard", new AttackPacket(3, 1, 1), 2, 0, null);
    }


    private static bool IsSafeOverloadTurn(Tl1EnergySideProfile side, int turn) =>
        side.Family.Equals("energy", StringComparison.OrdinalIgnoreCase) &&
        side.Doctrine.Equals("safe-burst", StringComparison.OrdinalIgnoreCase) && turn <= 2;

    private bool CanFire(DirectFireCombatant side, Tl1EnergySideProfile profile, WeaponProfile? weapon, int ammunition)
    {
        if (weapon is null || side.IsDestroyed || side.IsCrewMissionKilled) return false;
        if (profile.Family.Equals("kinetic", StringComparison.OrdinalIgnoreCase) && ammunition <= 0) return false;
        return side.Power.SpendablePower >= weapon.TacticalPowerCost;
    }

    private SimultaneousDirectFireOrder CreateOrder(DirectFireCombatant attacker, DirectFireCombatant target, WeaponState weapon,
        Tl1EnergySideProfile attackerProfile, Tl1EnergySideProfile targetProfile, int roll)
    {
        var accuracy = new DirectFireAccuracyProfile(50, attackerProfile.Accuracy, attackerProfile.ComputerBonus,
            _profile.RangePenaltyPerHex, 10, 5);
        return new SimultaneousDirectFireOrder(attacker, target, weapon, accuracy, _profile.RangeHexes,
            attackerProfile.Evasive, targetProfile.Evasive, roll);
    }

    private static WeaponState CreateWeapon(WeaponProfile profile, int ammunition) =>
        profile.PristineAmmunition is null ? new WeaponState(profile) : new WeaponState(profile, ammunition);

    private DirectFireCombatant CreateCombatant(string id) => new(
        id,
        new LayeredDefenseState(_profile.ShieldCapacity, _profile.ShieldCapacity, _profile.ShieldArmor,
            new[] { new ArmorLayerState("primary", _profile.ArmorProtection, _profile.ArmorProtection, _profile.ArmorIntegrity, _profile.ArmorIntegrity) },
            _profile.Hull, _profile.Hull),
        new TacticalPowerLedger(), 100, 10);

    private static bool IsTerminal(DirectFireCombatant side) => side.IsDestroyed || side.IsCrewMissionKilled;
    private static Tl1DuelOutcome DetermineOutcome(DirectFireCombatant a, DirectFireCombatant b)
    {
        bool at = IsTerminal(a), bt = IsTerminal(b);
        if (a.IsDestroyed && b.IsDestroyed) return Tl1DuelOutcome.MutualDestruction;
        if (a.IsCrewMissionKilled && b.IsCrewMissionKilled) return Tl1DuelOutcome.MutualMissionKill;
        if (at && bt) return Tl1DuelOutcome.MixedTerminal;
        if (at) return Tl1DuelOutcome.SideBWins;
        if (bt) return Tl1DuelOutcome.SideAWins;
        return Tl1DuelOutcome.Unresolved;
    }

    private static void Validate(Tl1EnergyCalibrationProfile p)
    {
        if (p.ShieldCapacity < 0 || p.ShieldArmor < 0 || p.BaseShieldRecharge < 0 || p.ArmorProtection < 0 ||
            p.ArmorIntegrity < 0 || p.Hull <= 0 || p.RangeHexes < 0 || p.RangePenaltyPerHex < 0 || p.TurnCap <= 0)
            throw new ArgumentOutOfRangeException(nameof(p));
        foreach (Tl1EnergySideProfile side in new[] { p.SideA, p.SideB })
        {
            if (side.ReactorOutput < 0 || side.TacticalShieldRecharge < 0 || side.Accuracy < 0 || side.ComputerBonus < 0)
                throw new ArgumentOutOfRangeException(nameof(p));
            if (!new[] { "energy", "kinetic" }.Contains(side.Family, StringComparer.OrdinalIgnoreCase))
                throw new ArgumentException("Family must be energy or kinetic.", nameof(p));
            if (side.Family.Equals("energy", StringComparison.OrdinalIgnoreCase) &&
                !new[] { "low", "standard", "safe-burst" }.Contains(side.Doctrine, StringComparer.OrdinalIgnoreCase))
                throw new ArgumentException("Energy doctrine must be low, standard, or safe-burst.", nameof(p));
        }
    }
}
