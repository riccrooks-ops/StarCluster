using System.Text.Json;

namespace StarCluster.ScenarioRunner.TL1;

/// <summary>
/// Guards the deterministic corpus against copying mutable TL1 baseline
/// numbers into scenario expectations. Explicit low-level mechanics fixtures
/// remain legal; baseline-owned profile operations must use resolver
/// directives instead of numeric literals.
/// </summary>
public static class Tl1ScenarioBaselineBindingValidator
{
    private static readonly IReadOnlyDictionary<string, string[]> BaselineBoundExpectedPaths =
        new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase)
        {
            ["weaponFire"] = new[]
            {
                "$.fire.tacticalPowerSpent",
                "$.fire.power.envelope",
                "$.fire.power.available",
                "$.fire.power.spent",
                "$.fire.damageResolution.incomingDamage",
                "$.fire.damageResolution.shieldBypass",
                "$.fire.damageResolution.shieldAbsorption",
                "$.defense.currentShieldCapacity",
            },
            ["turnStartRecharge"] = new[]
            {
                "$.baseRestored",
                "$.tacticalPowerSpent",
                "$.tacticalRestored",
                "$.power.envelope",
                "$.power.available",
                "$.power.spent",
            },
            ["reactorEnvelope"] = new[]
            {
                "$.beforeDamage.envelope",
                "$.afterDamage.envelope",
                "$.nextTurn.envelope",
                "$.nextTurn.available",
            },
            ["reactorOverload"] = new[]
            {
                "$.attempts[0].result.powerGained",
                "$.attempts[0].power.envelope",
            },
        };

    public static IReadOnlyList<string> Validate(Tl1MechanicsCaseDocument testCase)
    {
        ArgumentNullException.ThrowIfNull(testCase);
        var failures = new List<string>();

        if (string.Equals(testCase.Operation, "weaponFire", StringComparison.OrdinalIgnoreCase) &&
            TrySelect(testCase.Input, "$.envelope", out JsonElement envelope) &&
            envelope.ValueKind == JsonValueKind.Number)
        {
            failures.Add(
                "weaponFire input envelope is baseline-owned; omit it or use a $baseline directive.");
        }

        if (!BaselineBoundExpectedPaths.TryGetValue(
                testCase.Operation,
                out string[]? paths))
        {
            return failures.AsReadOnly();
        }

        foreach (string path in paths)
        {
            if (!TrySelect(testCase.Expected, path, out JsonElement value))
            {
                continue;
            }
            if (value.ValueKind == JsonValueKind.Number &&
                (!value.TryGetDecimal(out decimal number) || number != 0))
            {
                failures.Add(
                    $"expected path '{path}' is baseline-owned and must use a scenario-value directive rather than numeric literal {value.GetRawText()}.");
            }
        }
        return failures.AsReadOnly();
    }

    private static bool TrySelect(
        JsonElement root,
        string path,
        out JsonElement value)
    {
        value = root;
        if (!path.StartsWith("$.", StringComparison.Ordinal))
        {
            return false;
        }
        int index = 2;
        while (index < path.Length)
        {
            int start = index;
            while (index < path.Length && path[index] != '.' && path[index] != '[')
            {
                index++;
            }
            string property = path[start..index];
            if (property.Length > 0)
            {
                if (value.ValueKind != JsonValueKind.Object ||
                    !value.TryGetProperty(property, out JsonElement next))
                {
                    return false;
                }
                value = next;
            }
            while (index < path.Length && path[index] == '[')
            {
                int close = path.IndexOf(']', index + 1);
                if (close < 0 ||
                    !int.TryParse(path[(index + 1)..close], out int arrayIndex) ||
                    value.ValueKind != JsonValueKind.Array)
                {
                    return false;
                }
                JsonElement[] items = value.EnumerateArray().ToArray();
                if (arrayIndex < 0 || arrayIndex >= items.Length)
                {
                    return false;
                }
                value = items[arrayIndex];
                index = close + 1;
            }
            if (index < path.Length)
            {
                index++;
            }
        }
        return true;
    }
}
