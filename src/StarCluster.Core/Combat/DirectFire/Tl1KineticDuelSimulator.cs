using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.Core.Combat.DirectFire;

public sealed record Tl1CalibrationDuelResult(
    Tl1DuelOutcome Outcome,
    int Turns,
    int ShotsA,
    int ShotsB,
    int HitsA,
    int HitsB,
    DirectFireCombatant SideA,
    DirectFireCombatant SideB,
    int AmmunitionA,
    int AmmunitionB);

public sealed class Tl1KineticDuelSimulator
{
    private readonly Tl1DuelCalibrationProfile _profile;
    private readonly DirectFireAccuracyProfile _accuracyA;
    private readonly DirectFireAccuracyProfile _accuracyB;

    public Tl1KineticDuelSimulator(Tl1DuelCalibrationProfile profile)
    {
        ArgumentNullException.ThrowIfNull(profile);
        if (profile.ShieldCapacity < 0 || profile.ShieldArmor < 0 || profile.ShieldRecharge < 0 ||
            profile.ArmorProtection < 0 || profile.ArmorIntegrity < 0 || profile.Hull <= 0 ||
            profile.WeaponDamage <= 0 || profile.ShieldPenetration < 0 || profile.ArmorPenetration < 0 ||
            profile.WeaponPower < 0 || profile.Ammunition <= 0 ||
            profile.ReactorOutput < profile.WeaponPower ||
            profile.BaseChance is < 0 or > 100 || profile.WeaponAccuracy < 0 ||
            profile.RangePenaltyPerHex < 0 || profile.TargetEvasivePenalty < 0 ||
            profile.ShooterEvasivePenalty < 0 ||
            profile.MinimumChance is < 0 or > 100 ||
            profile.MaximumChance is < 0 or > 100 ||
            profile.MaximumChance < profile.MinimumChance ||
            profile.RangeHexes < 0 || profile.TurnCap <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(profile));
        }
        _profile = profile;
        _accuracyA = new DirectFireAccuracyProfile(
            profile.BaseChance,
            profile.WeaponAccuracy,
            profile.SideAComputerBonus,
            profile.RangePenaltyPerHex,
            profile.TargetEvasivePenalty,
            profile.ShooterEvasivePenalty,
            profile.MinimumChance,
            profile.MaximumChance);
        _accuracyB = new DirectFireAccuracyProfile(
            profile.BaseChance,
            profile.WeaponAccuracy,
            profile.SideBComputerBonus,
            profile.RangePenaltyPerHex,
            profile.TargetEvasivePenalty,
            profile.ShooterEvasivePenalty,
            profile.MinimumChance,
            profile.MaximumChance);
    }

    public Tl1CalibrationDuelResult Run(Func<int> nextRollA, Func<int> nextRollB)
    {
        ArgumentNullException.ThrowIfNull(nextRollA);
        ArgumentNullException.ThrowIfNull(nextRollB);
        DirectFireCombatant a = CreateCombatant("A");
        DirectFireCombatant b = CreateCombatant("B");
        WeaponState wa = CreateWeapon("A-kinetic");
        WeaponState wb = CreateWeapon("B-kinetic");
        int shotsA = 0, shotsB = 0, hitsA = 0, hitsB = 0;
        int turns = 0;

        for (int turn = 1; turn <= _profile.TurnCap; turn++)
        {
            turns = turn;
            a.Power.BeginTurn(_profile.ReactorOutput);
            b.Power.BeginTurn(_profile.ReactorOutput);
            a.Defense.RestoreShields(_profile.ShieldRecharge);
            b.Defense.RestoreShields(_profile.ShieldRecharge);
            bool canA = !a.IsDestroyed && !a.IsCrewMissionKilled && wa.CurrentAmmunition is > 0;
            bool canB = !b.IsDestroyed && !b.IsCrewMissionKilled && wb.CurrentAmmunition is > 0;
            if (!canA && !canB) break;
            var orders = new List<SimultaneousDirectFireOrder>();
            if (canA)
            {
                shotsA++;
                orders.Add(new SimultaneousDirectFireOrder(a, b, wa, _accuracyA, _profile.RangeHexes,
                    _profile.SideAEvasive, _profile.SideBEvasive, nextRollA()));
            }
            if (canB)
            {
                shotsB++;
                orders.Add(new SimultaneousDirectFireOrder(b, a, wb, _accuracyB, _profile.RangeHexes,
                    _profile.SideBEvasive, _profile.SideAEvasive, nextRollB()));
            }
            SimultaneousDirectFireBatchResult batch = SimultaneousDirectFireResolver.Resolve(orders);
            foreach (SimultaneousDirectFireAttackResult attack in batch.Attacks)
            {
                bool hit = attack.Outcome is DirectFireRollOutcome.Hit or DirectFireRollOutcome.CriticalHit;
                if (!hit) continue;
                if (attack.AttackerId == "A") hitsA++; else if (attack.AttackerId == "B") hitsB++;
            }
            if (IsTerminal(a) || IsTerminal(b))
            {
                return Result(DetermineOutcome(a, b), turn);
            }
        }
        return Result(DetermineOutcome(a, b), turns);

        Tl1CalibrationDuelResult Result(Tl1DuelOutcome outcome, int resolvedTurns) => new(
            outcome, resolvedTurns, shotsA, shotsB, hitsA, hitsB, a, b,
            wa.CurrentAmmunition ?? 0, wb.CurrentAmmunition ?? 0);
    }

    private DirectFireCombatant CreateCombatant(string id) => new(
        id,
        new LayeredDefenseState(
            _profile.ShieldCapacity, _profile.ShieldCapacity, _profile.ShieldArmor,
            new[] { new ArmorLayerState("primary", _profile.ArmorProtection, _profile.ArmorProtection,
                _profile.ArmorIntegrity, _profile.ArmorIntegrity) },
            _profile.Hull, _profile.Hull),
        new TacticalPowerLedger(), 100, 10);

    private WeaponState CreateWeapon(string id) => new(new WeaponProfile(
        id, WeaponFamily.Kinetic, "standard",
        new AttackPacket(_profile.WeaponDamage, _profile.ShieldPenetration, _profile.ArmorPenetration),
        _profile.WeaponPower, 1, _profile.Ammunition));

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
}
