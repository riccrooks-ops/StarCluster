using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Combat.Weapons;

namespace StarCluster.Core.Combat.DirectFire;

public sealed class DirectFireCombatant
{
    public DirectFireCombatant(string id, LayeredDefenseState defense, TacticalPowerLedger power, int crew, int minimumOperatingCrew)
    {
        if (string.IsNullOrWhiteSpace(id)) throw new ArgumentException("Combatant ID is required.", nameof(id));
        ArgumentNullException.ThrowIfNull(defense);
        ArgumentNullException.ThrowIfNull(power);
        if (crew < 0) throw new ArgumentOutOfRangeException(nameof(crew));
        if (minimumOperatingCrew < 0) throw new ArgumentOutOfRangeException(nameof(minimumOperatingCrew));
        Id = id; Defense = defense; Power = power; Crew = crew; MinimumOperatingCrew = minimumOperatingCrew;
    }
    public string Id { get; }
    public LayeredDefenseState Defense { get; }
    public TacticalPowerLedger Power { get; }
    public int Crew { get; private set; }
    public int MinimumOperatingCrew { get; }
    public bool IsDestroyed => Defense.IsDestroyed;
    public bool IsCrewMissionKilled => Crew < MinimumOperatingCrew;
    public void ApplyCrewCasualties(int casualties)
    {
        if (casualties < 0) throw new ArgumentOutOfRangeException(nameof(casualties));
        Crew = Math.Max(0, Crew - casualties);
    }
}

public sealed record SimultaneousDirectFireOrder(
    DirectFireCombatant Attacker,
    DirectFireCombatant Target,
    WeaponState Weapon,
    DirectFireAccuracyProfile Accuracy,
    int RangeHexes,
    bool AttackerEvasive,
    bool TargetEvasive,
    int Roll,
    int OtherModifiers = 0,
    ComponentCondition TargetStlCondition = ComponentCondition.Operational);

public sealed record SimultaneousDirectFireAttackResult(
    string AttackerId,
    string TargetId,
    string WeaponId,
    int Roll,
    int FinalChance,
    DirectFireRollOutcome Outcome,
    WeaponFireResult FireResult);

public sealed record SimultaneousDirectFireBatchResult(
    IReadOnlyList<SimultaneousDirectFireAttackResult> Attacks,
    bool MutualDestruction,
    bool MutualMissionKill);

public static class SimultaneousDirectFireResolver
{
    public static SimultaneousDirectFireBatchResult Resolve(IReadOnlyList<SimultaneousDirectFireOrder> orders)
    {
        ArgumentNullException.ThrowIfNull(orders);
        var seenWeapons = new HashSet<WeaponState>(ReferenceEqualityComparer.Instance);
        foreach (SimultaneousDirectFireOrder order in orders)
        {
            ArgumentNullException.ThrowIfNull(order.Attacker);
            ArgumentNullException.ThrowIfNull(order.Target);
            ArgumentNullException.ThrowIfNull(order.Weapon);
            ArgumentNullException.ThrowIfNull(order.Accuracy);
            if (order.Attacker.IsDestroyed || order.Attacker.IsCrewMissionKilled)
                throw new InvalidOperationException($"Attacker '{order.Attacker.Id}' cannot commit direct fire.");
            if (!seenWeapons.Add(order.Weapon))
                throw new InvalidOperationException("A weapon cannot be committed to more than one attack in the same window.");
        }

        var results = new List<SimultaneousDirectFireAttackResult>(orders.Count);
        foreach (SimultaneousDirectFireOrder order in orders)
        {
            DirectFireAccuracyResult accuracy = DirectFireAccuracyCalculator.Calculate(
                order.Accuracy, order.RangeHexes, order.TargetEvasive,
                order.AttackerEvasive, order.OtherModifiers,
                order.TargetStlCondition);
            DirectFireRollOutcome outcome = DirectFireHitResolver.Resolve(order.Roll, accuracy.FinalChance);
            WeaponFireResult fire = order.Weapon.Fire(
                order.Attacker.Power, order.Target.Defense,
                DirectFireHitResolver.IsHit(outcome));
            results.Add(new SimultaneousDirectFireAttackResult(
                order.Attacker.Id, order.Target.Id, order.Weapon.Profile.Id,
                order.Roll, accuracy.FinalChance, outcome, fire));
        }

        DirectFireCombatant[] combatants =
            Enumerable.Distinct<DirectFireCombatant>(
                orders.SelectMany(order => new[] { order.Attacker, order.Target }),
                ReferenceEqualityComparer.Instance)
            .ToArray();
        bool mutualDestruction = combatants.Length == 2 && combatants.All(c => c.IsDestroyed);
        bool mutualMissionKill = combatants.Length == 2 && combatants.All(c => c.IsCrewMissionKilled);
        return new SimultaneousDirectFireBatchResult(results.AsReadOnly(), mutualDestruction, mutualMissionKill);
    }
}
