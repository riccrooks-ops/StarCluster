namespace StarCluster.Core.Combat.InternalDamage;

public enum InternalCriticalDensity
{
    Percent15 = 15,
    Percent20 = 20,
    Percent25 = 25,
    Percent33 = 33,
    Percent50 = 50,
}

public static class Tl1InternalDamageDefaults
{
    public const InternalCriticalDensity OrdinaryDensity =
        InternalCriticalDensity.Percent33;
}

public static class InternalCriticalDensityExtensions
{
    public static string DisplayName(this InternalCriticalDensity density) => density switch
    {
        InternalCriticalDensity.Percent15 => "15%",
        InternalCriticalDensity.Percent20 => "20%",
        InternalCriticalDensity.Percent25 => "25%",
        InternalCriticalDensity.Percent33 => "33 1/3%",
        InternalCriticalDensity.Percent50 => "50%",
        _ => throw new ArgumentOutOfRangeException(nameof(density), density, null),
    };

    public static IReadOnlyList<int> StratumCycle(this InternalCriticalDensity density) => density switch
    {
        InternalCriticalDensity.Percent15 => Array.AsReadOnly(new[] { 7, 6, 7 }),
        InternalCriticalDensity.Percent20 => Array.AsReadOnly(new[] { 5 }),
        InternalCriticalDensity.Percent25 => Array.AsReadOnly(new[] { 4 }),
        InternalCriticalDensity.Percent33 => Array.AsReadOnly(new[] { 3 }),
        InternalCriticalDensity.Percent50 => Array.AsReadOnly(new[] { 2 }),
        _ => throw new ArgumentOutOfRangeException(nameof(density), density, null),
    };
}
