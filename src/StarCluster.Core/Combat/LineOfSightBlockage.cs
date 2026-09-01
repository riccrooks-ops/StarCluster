using System;
using System.Collections.Generic;

namespace StarCluster.Core.Combat;

/// <summary>
/// Describes the first range step that fully blocks direct fire.
/// </summary>
public sealed class LineOfSightBlockage
{
    internal LineOfSightBlockage(
        int rangeStep,
        IReadOnlyList<LineOfSightBlocker> blockers)
    {
        if (rangeStep <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(rangeStep),
                rangeStep,
                "A blockage must occur after the origin cell.");
        }

        Blockers = blockers ?? throw new ArgumentNullException(nameof(blockers));

        if (blockers.Count == 0)
        {
            throw new ArgumentException(
                "A blockage must identify at least one blocking object.",
                nameof(blockers));
        }

        RangeStep = rangeStep;
    }

    /// <summary>
    /// Gets the range step at which direct fire first becomes impossible.
    /// </summary>
    public int RangeStep { get; }

    /// <summary>
    /// Gets the blocking objects at that range step.
    /// </summary>
    /// <remarks>
    /// An ordinary interior crossing normally contains one blocker. An exact
    /// boundary pinched by bodies on both sides can contain two blockers.
    /// </remarks>
    public IReadOnlyList<LineOfSightBlocker> Blockers { get; }

    /// <summary>
    /// Gets whether blockers occupy both sides of an exact boundary.
    /// </summary>
    public bool IsBoundaryPinch => Blockers.Count > 1;
}
