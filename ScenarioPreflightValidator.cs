using StarCluster.Core.Geometry;

namespace StarCluster.ScenarioRunner;

/// <summary>
/// Validates every scenario document before any scenario in a batch executes.
/// The preflight deliberately reuses the production document mapper so malformed
/// initialization state cannot hide behind scenario ordering.
/// </summary>
public static class ScenarioPreflightValidator
{
    public static IReadOnlyList<string> Validate(ScenarioDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);

        var failures = new List<string>();
        ValidateOperationalTurnLimit(document, failures);
        ValidateMissileTravelHistory(document, failures);

        try
        {
            _ = ScenarioDocumentMapper.ToInitializationRequest(document);
        }
        catch (Exception exception)
        {
            bool duplicateTravelHistoryFailure =
                failures.Any(item => item.Contains("enteredCoordinates", StringComparison.Ordinal)) &&
                exception.Message.Contains(
                    "pre-simulation missile travel-history coordinate must be adjacent",
                    StringComparison.Ordinal);
            if (!duplicateTravelHistoryFailure)
            {
                failures.Add(exception.Message);
            }
        }

        return failures
            .Distinct(StringComparer.Ordinal)
            .ToArray();
    }


    private static void ValidateOperationalTurnLimit(
        ScenarioDocument document,
        ICollection<string> failures)
    {
        if (document.OperationalTurnLimit is <= 0)
        {
            failures.Add("operationalTurnLimit must be positive when supplied.");
        }

        if (document.OperationalTurnLimit is int turnLimit)
        {
            int missileActions = document.Actions.Count(action =>
                string.Equals(action.Type, "advanceMissile", StringComparison.OrdinalIgnoreCase));
            if (missileActions < turnLimit)
            {
                failures.Add(
                    $"operationalTurnLimit is {turnLimit}, but only {missileActions} " +
                    "advanceMissile actions were supplied.");
            }
        }
    }

    private static void ValidateMissileTravelHistory(
        ScenarioDocument document,
        ICollection<string> failures)
    {
        foreach (MissileDocument missile in document.Missiles)
        {
            HexCoord previous = ScenarioDocumentMapper.ToCoordinate(
                missile.LaunchPosition);

            for (int index = 0; index < missile.EnteredCoordinates.Count; index++)
            {
                HexCoord current = ScenarioDocumentMapper.ToCoordinate(
                    missile.EnteredCoordinates[index]);
                int distance = previous.DistanceTo(current);
                if (distance != 1)
                {
                    failures.Add(
                        $"Missile '{missile.Id}' enteredCoordinates[{index}] " +
                        $"moves from {previous} to {current} (distance {distance}); " +
                        "every pre-simulation travel-history step must be adjacent.");
                }

                previous = current;
            }
        }
    }
}
