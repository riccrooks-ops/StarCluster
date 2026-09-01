using System;
using StarCluster.Core.Combat.Missiles;

namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// Data supplied by a direct-fire weapon for ordinary attacks and optional
/// missile interception. Current direct-fire architecture distinguishes a
/// Standard Range, where no range penalty applies, from a Maximum Range, where
/// the universal extended-range penalty applies. Approximate-track ship fire
/// is a universal combat capability and is no longer a weapon-specific trait.
/// </summary>
public sealed class DirectFireWeaponProfile
{
    public DirectFireWeaponProfile(
        int technologyLevel,
        int maximumRangeHexes,
        bool canInterceptMissiles = true,
        bool allowsApproximateTrackFire = false,
        int? standardRangeHexes = null)
    {
        if (technologyLevel < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(technologyLevel),
                technologyLevel,
                "Technology level cannot be negative.");
        }

        if (maximumRangeHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumRangeHexes),
                maximumRangeHexes,
                "Maximum range cannot be negative.");
        }

        int resolvedStandardRange = standardRangeHexes ?? maximumRangeHexes;
        if (resolvedStandardRange < 0 || resolvedStandardRange > maximumRangeHexes)
        {
            throw new ArgumentOutOfRangeException(
                nameof(standardRangeHexes),
                standardRangeHexes,
                "Standard range must be between zero and Maximum Range.");
        }

        TechnologyLevel = technologyLevel;
        StandardRangeHexes = resolvedStandardRange;
        MaximumRangeHexes = maximumRangeHexes;
        CanInterceptMissiles = canInterceptMissiles;
        LegacyAllowsApproximateTrackFire = allowsApproximateTrackFire;
    }

    public int TechnologyLevel { get; }

    public int StandardRangeHexes { get; }

    public int MaximumRangeHexes { get; }

    public bool CanInterceptMissiles { get; }

    /// <summary>
    /// Historical compatibility value retained so frozen callers/data can still
    /// round-trip. Current ship-target direct fire does not consult this value:
    /// all direct-fire weapons may attack an Approximate track at the universal
    /// combat penalty.
    /// </summary>
    public bool LegacyAllowsApproximateTrackFire { get; }

    /// <summary>
    /// Compatibility alias for older callers. It records the legacy input only
    /// and does not control current Approximate-track eligibility.
    /// </summary>
    public bool AllowsApproximateTrackFire => LegacyAllowsApproximateTrackFire;

    internal MissileDefenseProfile ToInterceptionProfile() => new(
        TechnologyLevel,
        MaximumRangeHexes,
        maximumAttemptsPerPhase: 1);
}
