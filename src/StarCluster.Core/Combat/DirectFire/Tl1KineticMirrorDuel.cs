using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.Core.Combat.DirectFire;

public enum Tl1DuelOutcome
{
    SideAWins,
    SideBWins,
    MutualDestruction,
    MutualMissionKill,
    MixedTerminal,
    Unresolved,
}

public sealed record Tl1DuelTurnResult(
    int Turn,
    int RollA,
    int RollB,
    DirectFireRollOutcome OutcomeA,
    DirectFireRollOutcome OutcomeB,
    int HullA,
    int HullB,
    int ShieldA,
    int ShieldB,
    int AmmunitionA,
    int AmmunitionB);

public sealed record Tl1DuelResult(
    Tl1DuelOutcome Outcome,
    int TurnsResolved,
    IReadOnlyList<Tl1DuelTurnResult> Turns,
    DirectFireCombatant SideA,
    DirectFireCombatant SideB);

public sealed class Tl1KineticMirrorDuel
{
    private readonly int _turnCap;
    private readonly int _rangeHexes;
    private readonly bool _sideAEvasive;
    private readonly bool _sideBEvasive;
    private readonly DirectFireAccuracyProfile _accuracy;

    public Tl1KineticMirrorDuel(
        int turnCap,
        int rangeHexes,
        bool sideAEvasive,
        bool sideBEvasive,
        DirectFireAccuracyProfile accuracy)
    {
        if (turnCap <= 0) throw new ArgumentOutOfRangeException(nameof(turnCap));
        if (rangeHexes < 0) throw new ArgumentOutOfRangeException(nameof(rangeHexes));
        ArgumentNullException.ThrowIfNull(accuracy);
        _turnCap = turnCap;
        _rangeHexes = rangeHexes;
        _sideAEvasive = sideAEvasive;
        _sideBEvasive = sideBEvasive;
        _accuracy = accuracy;
    }

    public Tl1DuelResult Run(IReadOnlyList<int> rollsA, IReadOnlyList<int> rollsB)
    {
        ArgumentNullException.ThrowIfNull(rollsA);
        ArgumentNullException.ThrowIfNull(rollsB);
        if (rollsA.Count < _turnCap || rollsB.Count < _turnCap)
            throw new ArgumentException("Each side must supply one d100 roll per possible turn.");

        DirectFireCombatant a = CreateCombatant("A");
        DirectFireCombatant b = CreateCombatant("B");
        WeaponState wa = CreateWeapon("A-kinetic");
        WeaponState wb = CreateWeapon("B-kinetic");
        var turns = new List<Tl1DuelTurnResult>();

        for (int turn = 1; turn <= _turnCap; turn++)
        {
            a.Power.BeginTurn(5);
            b.Power.BeginTurn(5);
            a.Defense.RestoreShields(1);
            b.Defense.RestoreShields(1);

            bool aCanFire = !a.IsDestroyed && !a.IsCrewMissionKilled && wa.CurrentAmmunition > 0;
            bool bCanFire = !b.IsDestroyed && !b.IsCrewMissionKilled && wb.CurrentAmmunition > 0;
            if (!aCanFire && !bCanFire) break;

            var orders = new List<SimultaneousDirectFireOrder>();
            if (aCanFire)
            {
                orders.Add(new SimultaneousDirectFireOrder(
                    a, b, wa, _accuracy, _rangeHexes,
                    _sideAEvasive, _sideBEvasive, rollsA[turn - 1]));
            }
            if (bCanFire)
            {
                orders.Add(new SimultaneousDirectFireOrder(
                    b, a, wb, _accuracy, _rangeHexes,
                    _sideBEvasive, _sideAEvasive, rollsB[turn - 1]));
            }

            SimultaneousDirectFireBatchResult batch = SimultaneousDirectFireResolver.Resolve(orders);
            DirectFireRollOutcome outcomeA = batch.Attacks.FirstOrDefault(x => x.AttackerId == "A")?.Outcome ?? DirectFireRollOutcome.Miss;
            DirectFireRollOutcome outcomeB = batch.Attacks.FirstOrDefault(x => x.AttackerId == "B")?.Outcome ?? DirectFireRollOutcome.Miss;
            turns.Add(new Tl1DuelTurnResult(
                turn, rollsA[turn - 1], rollsB[turn - 1], outcomeA, outcomeB,
                a.Defense.CurrentHull, b.Defense.CurrentHull,
                a.Defense.CurrentShieldCapacity, b.Defense.CurrentShieldCapacity,
                wa.CurrentAmmunition ?? 0, wb.CurrentAmmunition ?? 0));

            if (IsTerminal(a) || IsTerminal(b))
            {
                return new Tl1DuelResult(DetermineOutcome(a, b), turn, turns.AsReadOnly(), a, b);
            }
        }

        return new Tl1DuelResult(
            DetermineOutcome(a, b), turns.Count, turns.AsReadOnly(), a, b);
    }

    private static bool IsTerminal(DirectFireCombatant side) =>
        side.IsDestroyed || side.IsCrewMissionKilled;

    private static Tl1DuelOutcome DetermineOutcome(DirectFireCombatant a, DirectFireCombatant b)
    {
        bool at = IsTerminal(a);
        bool bt = IsTerminal(b);
        if (a.IsDestroyed && b.IsDestroyed) return Tl1DuelOutcome.MutualDestruction;
        if (a.IsCrewMissionKilled && b.IsCrewMissionKilled) return Tl1DuelOutcome.MutualMissionKill;
        if (at && bt) return Tl1DuelOutcome.MixedTerminal;
        if (at) return Tl1DuelOutcome.SideBWins;
        if (bt) return Tl1DuelOutcome.SideAWins;
        return Tl1DuelOutcome.Unresolved;
    }

    private static DirectFireCombatant CreateCombatant(string id) => new(
        id,
        new LayeredDefenseState(
            2, 2, 0,
            new[] { new ArmorLayerState("primary", 0, 0, 4, 4) },
            12, 12),
        new TacticalPowerLedger(),
        100,
        10);

    private static WeaponState CreateWeapon(string id) => new(
        new WeaponProfile(
            id,
            WeaponFamily.Kinetic,
            "standard",
            new AttackPacket(4, 1, 0),
            1,
            1,
            100));
}
