using System;
using System.Collections.Generic;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat;

/// <summary>
/// Describes the logical result of tracing direct fire across a system map.
/// </summary>
public sealed class DirectFireLineOfSightResult
{
    internal DirectFireLineOfSightResult(
        HexCoord origin,
        HexCoord target,
        IReadOnlyList<HexCoord> testedCells,
        IReadOnlyList<LineOfSightGrazing> grazings,
        LineOfSightBlockage? blockage)
    {
        Origin = origin;
        Target = target;
        TestedCells = testedCells ??
            throw new ArgumentNullException(nameof(testedCells));
        Grazings = grazings ??
            throw new ArgumentNullException(nameof(grazings));
        Blockage = blockage;

        Quality = blockage is not null
            ? LineOfSightQuality.Blocked
            : grazings.Count > 0
                ? LineOfSightQuality.Grazing
                : LineOfSightQuality.Clear;
    }

    /// <summary>
    /// Gets the firing coordinate.
    /// </summary>
    public HexCoord Origin { get; }

    /// <summary>
    /// Gets the intended target coordinate.
    /// </summary>
    public HexCoord Target { get; }

    /// <summary>
    /// Gets every intermediate hex touched by the geometric line.
    /// </summary>
    /// <remarks>
    /// The origin and target cells are intentionally excluded. A boundary
    /// range step may contribute two cells.
    /// </remarks>
    public IReadOnlyList<HexCoord> TestedCells { get; }

    /// <summary>
    /// Gets the overall geometric line-of-sight quality.
    /// </summary>
    public LineOfSightQuality Quality { get; }

    /// <summary>
    /// Gets every one-sided boundary grazing encountered before any complete
    /// blockage.
    /// </summary>
    /// <remarks>
    /// Multiple grazings are preserved separately so the later combat model
    /// can apply a cumulative, potentially capped penalty. No numeric penalty
    /// is assigned by the geometry layer.
    /// </remarks>
    public IReadOnlyList<LineOfSightGrazing> Grazings { get; }

    /// <summary>
    /// Gets the first complete blockage, or <see langword="null"/> when direct
    /// fire remains geometrically possible.
    /// </summary>
    public LineOfSightBlockage? Blockage { get; }

    /// <summary>
    /// Gets the blockers at the first fully blocked range step.
    /// </summary>
    /// <remarks>
    /// This compatibility property is empty for clear and grazing results.
    /// Grazing objects are available through <see cref="Grazings"/>.
    /// </remarks>
    public IReadOnlyList<LineOfSightBlocker> Blockers =>
        Blockage?.Blockers ?? Array.Empty<LineOfSightBlocker>();

    /// <summary>
    /// Gets the number of separate grazing events along the trace.
    /// </summary>
    public int GrazingCount => Grazings.Count;

    /// <summary>
    /// Gets whether the line is completely unobstructed.
    /// </summary>
    public bool IsClear => Quality == LineOfSightQuality.Clear;

    /// <summary>
    /// Gets whether direct fire is geometrically possible but grazes at least
    /// one blocking body.
    /// </summary>
    public bool IsGrazing => Quality == LineOfSightQuality.Grazing;

    /// <summary>
    /// Gets whether direct fire is fully obstructed.
    /// </summary>
    public bool IsBlocked => Quality == LineOfSightQuality.Blocked;

    /// <summary>
    /// Gets whether geometry permits a direct-fire attempt.
    /// </summary>
    /// <remarks>
    /// Range, target lock, weapon readiness, and accuracy are separate combat
    /// requirements that are not evaluated here.
    /// </remarks>
    public bool HasLineOfSight => Quality != LineOfSightQuality.Blocked;
}
