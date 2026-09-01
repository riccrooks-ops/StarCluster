namespace StarCluster.ScenarioRunner;

public sealed class PairedBinaryDifferenceSummary
{
    public int TrialCount { get; init; }
    public int NeitherTrue { get; init; }
    public int FromOnlyTrue { get; init; }
    public int ToOnlyTrue { get; init; }
    public int BothTrue { get; init; }
    public double ObservedDelta { get; init; }
    public double Confidence95Low { get; init; }
    public double Confidence95High { get; init; }
    public double RawPValue { get; init; }
}

public static class PairedMarginalStatistics
{
    private const double Z95 = 1.959963984540054;

    public static PairedBinaryDifferenceSummary Compare(
        IReadOnlyList<bool> from,
        IReadOnlyList<bool> to,
        string expectedDirection)
    {
        ArgumentNullException.ThrowIfNull(from);
        ArgumentNullException.ThrowIfNull(to);
        if (from.Count == 0 || from.Count != to.Count)
        {
            throw new ArgumentException(
                "Paired comparisons require equal non-empty outcome vectors.");
        }
        if (expectedDirection != "nondecreasing" &&
            expectedDirection != "nonincreasing" &&
            expectedDirection != "flat" &&
            expectedDirection != "descriptive")
        {
            throw new ArgumentException(
                $"Unsupported expected direction '{expectedDirection}'.",
                nameof(expectedDirection));
        }

        int neither = 0;
        int fromOnly = 0;
        int toOnly = 0;
        int both = 0;
        for (int index = 0; index < from.Count; index++)
        {
            if (from[index])
            {
                if (to[index])
                {
                    both++;
                }
                else
                {
                    fromOnly++;
                }
            }
            else if (to[index])
            {
                toOnly++;
            }
            else
            {
                neither++;
            }
        }

        double observedDelta = (double)(toOnly - fromOnly) / from.Count;
        int discordant = fromOnly + toOnly;
        double sumSquares = discordant;
        double sampleVariance = from.Count > 1
            ? Math.Max(
                0.0,
                (sumSquares - (from.Count * observedDelta * observedDelta)) /
                (from.Count - 1))
            : 0.0;
        double standardError = Math.Sqrt(sampleVariance / from.Count);
        double confidenceLow = Math.Max(-1.0, observedDelta - (Z95 * standardError));
        double confidenceHigh = Math.Min(1.0, observedDelta + (Z95 * standardError));
        double rawPValue = CalculateMcNemarPValue(
            fromOnly,
            toOnly,
            expectedDirection);

        return new PairedBinaryDifferenceSummary
        {
            TrialCount = from.Count,
            NeitherTrue = neither,
            FromOnlyTrue = fromOnly,
            ToOnlyTrue = toOnly,
            BothTrue = both,
            ObservedDelta = observedDelta,
            Confidence95Low = confidenceLow,
            Confidence95High = confidenceHigh,
            RawPValue = rawPValue,
        };
    }

    public static double[] AdjustHolm(IReadOnlyList<double> rawPValues)
    {
        ArgumentNullException.ThrowIfNull(rawPValues);
        if (rawPValues.Any(value => double.IsNaN(value) || value < 0.0 || value > 1.0))
        {
            throw new ArgumentOutOfRangeException(
                nameof(rawPValues),
                "Raw p-values must be finite values from 0 through 1.");
        }

        var adjusted = new double[rawPValues.Count];
        double runningMaximum = 0.0;
        var ordered = rawPValues
            .Select((value, index) => (Value: value, Index: index))
            .OrderBy(item => item.Value)
            .ThenBy(item => item.Index)
            .ToArray();
        for (int rank = 0; rank < ordered.Length; rank++)
        {
            double candidate = Math.Min(
                1.0,
                ordered[rank].Value * (ordered.Length - rank));
            runningMaximum = Math.Max(runningMaximum, candidate);
            adjusted[ordered[rank].Index] = runningMaximum;
        }

        return adjusted;
    }

    public static bool IsStatisticallyContradictory(
        string expectedDirection,
        double observedDelta,
        double holmAdjustedPValue,
        double minimumPracticalDelta,
        double familywiseAlpha)
    {
        if (expectedDirection != "nondecreasing" &&
            expectedDirection != "nonincreasing" &&
            expectedDirection != "flat" &&
            expectedDirection != "descriptive")
        {
            throw new ArgumentException(
                $"Unsupported expected direction '{expectedDirection}'.",
                nameof(expectedDirection));
        }
        if (expectedDirection == "descriptive")
        {
            return false;
        }
        if (holmAdjustedPValue < 0.0 || holmAdjustedPValue > 1.0)
        {
            throw new ArgumentOutOfRangeException(nameof(holmAdjustedPValue));
        }
        if (minimumPracticalDelta < 0.0 || minimumPracticalDelta > 1.0)
        {
            throw new ArgumentOutOfRangeException(nameof(minimumPracticalDelta));
        }
        if (familywiseAlpha <= 0.0 || familywiseAlpha >= 1.0)
        {
            throw new ArgumentOutOfRangeException(nameof(familywiseAlpha));
        }

        double opposingMagnitude = expectedDirection switch
        {
            "nondecreasing" => Math.Max(0.0, -observedDelta),
            "nonincreasing" => Math.Max(0.0, observedDelta),
            _ => Math.Abs(observedDelta),
        };
        return opposingMagnitude > minimumPracticalDelta + 1e-12 &&
            holmAdjustedPValue < familywiseAlpha;
    }

    private static double CalculateMcNemarPValue(
        int fromOnly,
        int toOnly,
        string expectedDirection)
    {
        int discordant = fromOnly + toOnly;
        if (discordant == 0)
        {
            return 1.0;
        }

        int difference = toOnly - fromOnly;
        double correctedMagnitude = Math.Max(0.0, Math.Abs(difference) - 1.0);
        double z = correctedMagnitude / Math.Sqrt(discordant);
        double oneSidedTail = Math.Max(0.0, 1.0 - NormalCdf(z));
        return expectedDirection switch
        {
            "nondecreasing" when difference < 0 => oneSidedTail,
            "nonincreasing" when difference > 0 => oneSidedTail,
            "flat" => Math.Min(1.0, 2.0 * oneSidedTail),
            "descriptive" => 1.0,
            _ => 1.0,
        };
    }

    private static double NormalCdf(double value)
    {
        double absolute = Math.Abs(value);
        double t = 1.0 / (1.0 + (0.2316419 * absolute));
        double polynomial = t *
            (0.319381530 +
             (t * (-0.356563782 +
              (t * (1.781477937 +
               (t * (-1.821255978 +
                (t * 1.330274429))))))));
        double density = 0.3989422804014327 * Math.Exp(-0.5 * absolute * absolute);
        double positiveCdf = 1.0 - (density * polynomial);
        return value >= 0.0 ? positiveCdf : 1.0 - positiveCdf;
    }
}
