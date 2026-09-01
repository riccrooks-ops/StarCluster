using System.Globalization;
using System.Text.Json;

namespace StarCluster.ScenarioRunner.TL1;

public static class Tl1ExpectedSubsetComparer
{
    public static IReadOnlyList<string> Compare(
        JsonElement expected,
        JsonElement actual)
    {
        var failures = new List<string>();
        CompareCore(expected, actual, "$", failures);
        return failures.AsReadOnly();
    }

    private static void CompareCore(
        JsonElement expected,
        JsonElement actual,
        string path,
        ICollection<string> failures)
    {
        if (expected.ValueKind != actual.ValueKind)
        {
            if (IsNumber(expected) && IsNumber(actual))
            {
                CompareNumbers(expected, actual, path, failures);
                return;
            }
            failures.Add(
                $"{path}: expected {expected.ValueKind}, actual {actual.ValueKind}.");
            return;
        }

        switch (expected.ValueKind)
        {
            case JsonValueKind.Object:
                foreach (JsonProperty property in expected.EnumerateObject())
                {
                    if (!actual.TryGetProperty(property.Name, out JsonElement actualValue))
                    {
                        failures.Add($"{path}.{property.Name}: property is missing.");
                        continue;
                    }
                    CompareCore(
                        property.Value,
                        actualValue,
                        $"{path}.{property.Name}",
                        failures);
                }
                break;
            case JsonValueKind.Array:
                JsonElement[] expectedItems = expected.EnumerateArray().ToArray();
                JsonElement[] actualItems = actual.EnumerateArray().ToArray();
                if (expectedItems.Length != actualItems.Length)
                {
                    failures.Add(
                        $"{path}: expected {expectedItems.Length} item(s), " +
                        $"actual {actualItems.Length}.");
                    return;
                }
                for (int index = 0; index < expectedItems.Length; index++)
                {
                    CompareCore(
                        expectedItems[index],
                        actualItems[index],
                        $"{path}[{index}]",
                        failures);
                }
                break;
            case JsonValueKind.Number:
                CompareNumbers(expected, actual, path, failures);
                break;
            case JsonValueKind.String:
                if (!string.Equals(
                        expected.GetString(),
                        actual.GetString(),
                        StringComparison.Ordinal))
                {
                    failures.Add(
                        $"{path}: expected '{expected.GetString()}', " +
                        $"actual '{actual.GetString()}'.");
                }
                break;
            case JsonValueKind.True:
            case JsonValueKind.False:
                if (expected.GetBoolean() != actual.GetBoolean())
                {
                    failures.Add(
                        $"{path}: expected {expected.GetBoolean()}, " +
                        $"actual {actual.GetBoolean()}.");
                }
                break;
            case JsonValueKind.Null:
            case JsonValueKind.Undefined:
                break;
            default:
                failures.Add($"{path}: unsupported JSON kind {expected.ValueKind}.");
                break;
        }
    }

    private static void CompareNumbers(
        JsonElement expected,
        JsonElement actual,
        string path,
        ICollection<string> failures)
    {
        if (!expected.TryGetDecimal(out decimal expectedNumber) ||
            !actual.TryGetDecimal(out decimal actualNumber))
        {
            string expectedText = expected.GetRawText();
            string actualText = actual.GetRawText();
            if (!string.Equals(expectedText, actualText, StringComparison.Ordinal))
            {
                failures.Add(
                    $"{path}: expected {expectedText}, actual {actualText}.");
            }
            return;
        }
        if (expectedNumber != actualNumber)
        {
            failures.Add(
                $"{path}: expected " +
                expectedNumber.ToString(CultureInfo.InvariantCulture) +
                ", actual " +
                actualNumber.ToString(CultureInfo.InvariantCulture) + ".");
        }
    }

    private static bool IsNumber(JsonElement value) =>
        value.ValueKind == JsonValueKind.Number;
}
