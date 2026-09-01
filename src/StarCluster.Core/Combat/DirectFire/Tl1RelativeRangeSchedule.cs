namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// One scripted change to the shared relative separation used by compact TL1
/// calibration. The change is applied at the start of the named turn.
/// </summary>
public sealed record Tl1RelativeRangeChange(int Turn, int RangeHexes);

/// <summary>
/// Validates and applies a constrained relative-range schedule without adding
/// absolute board coordinates, headings, or free-form movement AI.
/// </summary>
public sealed class Tl1RelativeRangeSchedule
{
    public const int MaximumBoardSeparationHexes = 10;

    private readonly IReadOnlyDictionary<int, int> _rangeByTurn;

    public Tl1RelativeRangeSchedule(
        int initialRangeHexes,
        int turnCap,
        IReadOnlyList<Tl1RelativeRangeChange>? changes)
    {
        if (initialRangeHexes is < 0 or > MaximumBoardSeparationHexes)
        {
            throw new ArgumentOutOfRangeException(
                nameof(initialRangeHexes),
                $"Relative range must be between 0 and {MaximumBoardSeparationHexes} hexes.");
        }
        if (turnCap <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(turnCap));
        }

        InitialRangeHexes = initialRangeHexes;
        var ordered = (changes ?? Array.Empty<Tl1RelativeRangeChange>()).ToArray();
        var ranges = new Dictionary<int, int>();
        int previousTurn = 1;
        int previousRange = initialRangeHexes;
        foreach (Tl1RelativeRangeChange change in ordered)
        {
            if (change.Turn < 2 || change.Turn > turnCap)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(changes),
                    $"Range-change turn {change.Turn} must be between 2 and {turnCap}.");
            }
            if (change.Turn <= previousTurn || ranges.ContainsKey(change.Turn))
            {
                throw new ArgumentException(
                    "Relative-range changes must be unique and strictly ordered by turn.",
                    nameof(changes));
            }
            if (change.RangeHexes is < 0 or > MaximumBoardSeparationHexes)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(changes),
                    $"Relative range must be between 0 and {MaximumBoardSeparationHexes} hexes.");
            }
            if (change.RangeHexes == previousRange)
            {
                throw new ArgumentException(
                    $"Range change on turn {change.Turn} is a no-op.",
                    nameof(changes));
            }

            ranges.Add(change.Turn, change.RangeHexes);
            previousTurn = change.Turn;
            previousRange = change.RangeHexes;
        }

        Changes = ordered;
        _rangeByTurn = ranges;
    }

    public int InitialRangeHexes { get; }

    public IReadOnlyList<Tl1RelativeRangeChange> Changes { get; }

    public bool TryApplyTurn(
        int turn,
        ref int currentRangeHexes,
        out int deltaHexes)
    {
        if (!_rangeByTurn.TryGetValue(turn, out int nextRange))
        {
            deltaHexes = 0;
            return false;
        }

        deltaHexes = nextRange - currentRangeHexes;
        currentRangeHexes = nextRange;
        return true;
    }
}
