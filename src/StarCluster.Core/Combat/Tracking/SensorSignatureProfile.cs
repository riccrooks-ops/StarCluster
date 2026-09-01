using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Data-driven contribution made by a target's observable signature. Positive
/// values make the target detectable farther away; negative values represent a
/// quieter or harder-to-detect target. Active emissions are added only while
/// that target is operating active sensors.
/// </summary>
public sealed class SensorSignatureProfile
{
    public SensorSignatureProfile(
        string id,
        int baselineRangeModifierHexes = 0,
        int activeEmissionRangeModifierHexes = 0)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("A signature profile ID is required.", nameof(id));
        }

        if (activeEmissionRangeModifierHexes < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(activeEmissionRangeModifierHexes));
        }

        Id = id;
        BaselineRangeModifierHexes = baselineRangeModifierHexes;
        ActiveEmissionRangeModifierHexes = activeEmissionRangeModifierHexes;
    }

    public static SensorSignatureProfile Neutral { get; } =
        new("neutral-signature");

    public string Id { get; }

    public int BaselineRangeModifierHexes { get; }

    public int ActiveEmissionRangeModifierHexes { get; }

    public int GetRangeModifier(SensorMode targetSensorMode) =>
        targetSensorMode == SensorMode.Active
            ? checked(
                BaselineRangeModifierHexes +
                ActiveEmissionRangeModifierHexes)
            : BaselineRangeModifierHexes;
}
