namespace StarCluster.ScenarioRunner.TL1;

public static class Tl1ScenarioPreflightValidator
{
    private static readonly HashSet<string> SupportedOperations = new(
        new[]
        {
            "resolveDamage",
            "turnStartRecharge",
            "powerScript",
            "heldInterception",
            "reactorEnvelope",
            "reactorOverload",
            "resetState",
            "weaponFire",
            "chargedWeaponScript",
        },
        StringComparer.OrdinalIgnoreCase);

    public static IReadOnlyList<string> Validate(
        Tl1MechanicsScenarioDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);
        var failures = new List<string>();
        if (!string.Equals(
                document.SchemaVersion,
                "star-cluster-tl1-phase-a-v1",
                StringComparison.Ordinal))
        {
            failures.Add(
                "schemaVersion must be 'star-cluster-tl1-phase-a-v1'.");
        }
        if (string.IsNullOrWhiteSpace(document.Id))
        {
            failures.Add("id is required.");
        }
        if (string.IsNullOrWhiteSpace(document.MatrixScenarioId))
        {
            failures.Add("matrixScenarioId is required.");
        }
        if (string.IsNullOrWhiteSpace(document.Name))
        {
            failures.Add("name is required.");
        }
        if (!string.Equals(
                document.BaselineVersion,
                "tl1-core-combat-v0.1",
                StringComparison.Ordinal))
        {
            failures.Add(
                "baselineVersion must be 'tl1-core-combat-v0.1'.");
        }
        string baselineHash = document.BaselineSha256 ?? string.Empty;
        if (baselineHash.Length != 64 ||
            baselineHash.Any(character =>
                !Uri.IsHexDigit(character)))
        {
            failures.Add("baselineSha256 must be a 64-character hexadecimal SHA-256 value.");
        }
        if (document.Cases.Count == 0)
        {
            failures.Add("at least one case is required.");
        }

        var caseIds = new HashSet<string>(StringComparer.Ordinal);
        for (int index = 0; index < document.Cases.Count; index++)
        {
            Tl1MechanicsCaseDocument testCase = document.Cases[index];
            string prefix = $"cases[{index}]";
            if (string.IsNullOrWhiteSpace(testCase.Id))
            {
                failures.Add($"{prefix}.id is required.");
            }
            else if (!caseIds.Add(testCase.Id))
            {
                failures.Add($"{prefix}.id '{testCase.Id}' is duplicated.");
            }
            if (string.IsNullOrWhiteSpace(testCase.Name))
            {
                failures.Add($"{prefix}.name is required.");
            }
            if (!SupportedOperations.Contains(testCase.Operation))
            {
                failures.Add(
                    $"{prefix}.operation '{testCase.Operation}' is unsupported.");
            }
            if (testCase.Input.ValueKind is
                System.Text.Json.JsonValueKind.Undefined or
                System.Text.Json.JsonValueKind.Null)
            {
                failures.Add($"{prefix}.input is required.");
            }
            if (testCase.Expected.ValueKind is
                System.Text.Json.JsonValueKind.Undefined or
                System.Text.Json.JsonValueKind.Null)
            {
                failures.Add($"{prefix}.expected is required.");
            }
        }
        return failures.AsReadOnly();
    }
}
