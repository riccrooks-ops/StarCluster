using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Movement;

/// <summary>
/// Immutable authoritative state for one ship's tactical Movement phase.
/// The executed path records every entered hex so a distant destination can
/// still resolve as individual movement steps.
/// </summary>
public sealed class ShipMovementTurnState
{
    private readonly IReadOnlyList<HexCoord> _executedPath;

    internal ShipMovementTurnState(
        int maximumDistance,
        IEnumerable<HexCoord> executedPath,
        bool isComplete)
    {
        if (maximumDistance < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maximumDistance),
                maximumDistance,
                "Maximum movement distance cannot be negative.");
        }

        ArgumentNullException.ThrowIfNull(executedPath);
        HexCoord[] materialized = executedPath.ToArray();
        if (materialized.Length == 0)
        {
            throw new ArgumentException(
                "A movement turn must contain its starting coordinate.",
                nameof(executedPath));
        }

        for (int index = 1; index < materialized.Length; index++)
        {
            if (materialized[index - 1].DistanceTo(materialized[index]) != 1)
            {
                throw new ArgumentException(
                    "Every committed movement step must enter an adjacent hex.",
                    nameof(executedPath));
            }
        }

        if (materialized.Length - 1 > maximumDistance)
        {
            throw new ArgumentException(
                "The executed path cannot exceed the movement allowance.",
                nameof(executedPath));
        }

        MaximumDistance = maximumDistance;
        _executedPath = Array.AsReadOnly(materialized);
        IsComplete = isComplete || RemainingDistance == 0;
    }

    public int MaximumDistance { get; }

    public IReadOnlyList<HexCoord> ExecutedPath => _executedPath;

    public HexCoord StartingCoordinate => _executedPath[0];

    public HexCoord CurrentCoordinate => _executedPath[^1];

    public int DistanceSpent => _executedPath.Count - 1;

    public int RemainingDistance => MaximumDistance - DistanceSpent;

    public bool IsComplete { get; }

    internal ShipMovementTurnState CommitStep(HexCoord coordinate) =>
        new(
            MaximumDistance,
            _executedPath.Concat(new[] { coordinate }),
            isComplete: false);

    internal ShipMovementTurnState Complete() =>
        IsComplete
            ? this
            : new ShipMovementTurnState(
                MaximumDistance,
                _executedPath,
                isComplete: true);
}
