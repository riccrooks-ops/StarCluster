using StarCluster.Core.Combat.Missiles;

namespace StarCluster.ScenarioRunner;

public sealed class ProbabilityMissileInterceptionProfile
{
    private readonly IReadOnlyDictionary<string, int> _chanceByDefenseId;

    public ProbabilityMissileInterceptionProfile(
        IEnumerable<DefenseDocument> defenses)
    {
        ArgumentNullException.ThrowIfNull(defenses);
        _chanceByDefenseId = defenses.ToDictionary(
            defense => defense.Id,
            defense => ValidateChance(
                defense.InterceptionChancePercent,
                defense.Id),
            StringComparer.Ordinal);
    }

    internal IReadOnlyDictionary<string, int> ChanceByDefenseId =>
        _chanceByDefenseId;

    private static int ValidateChance(int chancePercent, string defenseId)
    {
        if (chancePercent is < 0 or > 100)
        {
            throw new InvalidOperationException(
                $"Defense '{defenseId}' has invalid interception chance " +
                $"{chancePercent}; expected 0 through 100.");
        }

        return chancePercent;
    }
}

public sealed class ProbabilityMissileInterceptionResolver : IMissileInterceptionResolver
{
    private readonly IReadOnlyDictionary<string, int> _chanceByDefenseId;
    private readonly DeterministicRandomStream _stream;

    public ProbabilityMissileInterceptionResolver(
        IEnumerable<DefenseDocument> defenses,
        ulong seed)
        : this(new ProbabilityMissileInterceptionProfile(defenses), seed)
    {
    }

    public ProbabilityMissileInterceptionResolver(
        ProbabilityMissileInterceptionProfile profile,
        ulong seed)
    {
        ArgumentNullException.ThrowIfNull(profile);
        _chanceByDefenseId = profile.ChanceByDefenseId;
        _stream = new DeterministicRandomStream(seed);
    }

    public MissileInterceptionOutcome Resolve(MissileInterceptionAttempt attempt)
    {
        ArgumentNullException.ThrowIfNull(attempt);
        if (!_chanceByDefenseId.TryGetValue(
                attempt.DefenseSystem.Id,
                out int chancePercent))
        {
            throw new InvalidOperationException(
                $"No stochastic interception chance was configured for defense " +
                $"'{attempt.DefenseSystem.Id}'.");
        }

        int roll = _stream.NextD100();
        return roll <= chancePercent
            ? MissileInterceptionOutcome.Intercepted
            : MissileInterceptionOutcome.Missed;
    }
}
