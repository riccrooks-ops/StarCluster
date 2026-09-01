using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace StarCluster.ScenarioRunner.TL1;

/// <summary>
/// Resolves explicit scenario-value directives against the authoritative TL1
/// numerical baseline and, for expectations, the resolved input and actual
/// operation result. This keeps baseline-owned values out of scenario JSON.
/// </summary>
public static class Tl1ScenarioValueResolver
{
    private static readonly HashSet<string> DirectiveNames = new(
        new[]
        {
            "$baseline",
            "$input",
            "$actual",
            "$add",
            "$subtract",
            "$multiply",
            "$min",
            "$max",
        },
        StringComparer.Ordinal);

    public static JsonElement ResolveInput(
        JsonElement template,
        Tl1BaselineCatalog baseline) =>
        Resolve(template, baseline, input: null, actual: null);

    public static JsonElement ResolveExpected(
        JsonElement template,
        Tl1BaselineCatalog baseline,
        JsonElement resolvedInput,
        JsonElement actual) =>
        Resolve(template, baseline, resolvedInput, actual);

    public static IReadOnlyList<string> ValidateTemplate(
        JsonElement template,
        Tl1BaselineCatalog baseline,
        bool allowInputReferences,
        bool allowActualReferences)
    {
        ArgumentNullException.ThrowIfNull(baseline);
        var failures = new List<string>();
        ValidateNode(
            template,
            baseline,
            "$",
            allowInputReferences,
            allowActualReferences,
            failures);
        return failures.AsReadOnly();
    }

    public static bool IsDirective(JsonElement value)
    {
        if (value.ValueKind != JsonValueKind.Object)
        {
            return false;
        }
        JsonProperty[] properties = value.EnumerateObject().ToArray();
        return properties.Length == 1 && DirectiveNames.Contains(properties[0].Name);
    }

    private static JsonElement Resolve(
        JsonElement template,
        Tl1BaselineCatalog baseline,
        JsonElement? input,
        JsonElement? actual)
    {
        ArgumentNullException.ThrowIfNull(baseline);
        JsonNode? resolved = ResolveNode(template, baseline, input, actual, "$input");
        using JsonDocument document = JsonDocument.Parse(
            resolved?.ToJsonString() ?? "null");
        return document.RootElement.Clone();
    }

    private static JsonNode? ResolveNode(
        JsonElement value,
        Tl1BaselineCatalog baseline,
        JsonElement? input,
        JsonElement? actual,
        string path)
    {
        if (value.ValueKind == JsonValueKind.Object)
        {
            JsonProperty[] properties = value.EnumerateObject().ToArray();
            if (properties.Length == 1 && DirectiveNames.Contains(properties[0].Name))
            {
                return ResolveDirective(
                    properties[0],
                    baseline,
                    input,
                    actual,
                    path);
            }

            var result = new JsonObject();
            foreach (JsonProperty property in properties)
            {
                result[property.Name] = ResolveNode(
                    property.Value,
                    baseline,
                    input,
                    actual,
                    $"{path}.{property.Name}");
            }
            return result;
        }

        if (value.ValueKind == JsonValueKind.Array)
        {
            var result = new JsonArray();
            int index = 0;
            foreach (JsonElement item in value.EnumerateArray())
            {
                result.Add(ResolveNode(
                    item,
                    baseline,
                    input,
                    actual,
                    $"{path}[{index}]") );
                index++;
            }
            return result;
        }

        return JsonNode.Parse(value.GetRawText());
    }

    private static JsonNode? ResolveDirective(
        JsonProperty directive,
        Tl1BaselineCatalog baseline,
        JsonElement? input,
        JsonElement? actual,
        string path)
    {
        switch (directive.Name)
        {
            case "$baseline":
                string parameterId = RequireString(directive.Value, path, "$baseline");
                return BaselineNode(baseline, parameterId);
            case "$input":
                if (input is null)
                {
                    throw new InvalidOperationException(
                        $"{path}: $input is not available while resolving scenario input.");
                }
                return JsonNode.Parse(
                    SelectPath(input.Value, RequireString(directive.Value, path, "$input"))
                        .GetRawText());
            case "$actual":
                if (actual is null)
                {
                    throw new InvalidOperationException(
                        $"{path}: $actual is not available before operation execution.");
                }
                return JsonNode.Parse(
                    SelectPath(actual.Value, RequireString(directive.Value, path, "$actual"))
                        .GetRawText());
            case "$add":
                return NumberNode(ResolveNumbers(
                    directive.Value, baseline, input, actual, path).Sum());
            case "$subtract":
            {
                decimal[] values = ResolveNumbers(
                    directive.Value, baseline, input, actual, path);
                if (values.Length != 2)
                {
                    throw new InvalidOperationException(
                        $"{path}: $subtract requires exactly two operands.");
                }
                return NumberNode(values[0] - values[1]);
            }
            case "$multiply":
            {
                decimal product = 1;
                foreach (decimal operand in ResolveNumbers(
                    directive.Value, baseline, input, actual, path))
                {
                    product *= operand;
                }
                return NumberNode(product);
            }
            case "$min":
            {
                decimal[] values = ResolveNumbers(
                    directive.Value, baseline, input, actual, path);
                if (values.Length == 0)
                {
                    throw new InvalidOperationException(
                        $"{path}: $min requires at least one operand.");
                }
                return NumberNode(values.Min());
            }
            case "$max":
            {
                decimal[] values = ResolveNumbers(
                    directive.Value, baseline, input, actual, path);
                if (values.Length == 0)
                {
                    throw new InvalidOperationException(
                        $"{path}: $max requires at least one operand.");
                }
                return NumberNode(values.Max());
            }
            default:
                throw new InvalidOperationException(
                    $"{path}: unsupported scenario value directive '{directive.Name}'.");
        }
    }

    private static decimal[] ResolveNumbers(
        JsonElement operands,
        Tl1BaselineCatalog baseline,
        JsonElement? input,
        JsonElement? actual,
        string path)
    {
        if (operands.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidOperationException(
                $"{path}: arithmetic directive operands must be an array.");
        }
        var result = new List<decimal>();
        int index = 0;
        foreach (JsonElement operand in operands.EnumerateArray())
        {
            JsonNode? node = ResolveNode(
                operand,
                baseline,
                input,
                actual,
                $"{path}[{index}]");
            if (node is null ||
                !decimal.TryParse(
                    node.ToJsonString(),
                    NumberStyles.Number,
                    CultureInfo.InvariantCulture,
                    out decimal number))
            {
                throw new InvalidOperationException(
                    $"{path}[{index}]: arithmetic operand is not numeric.");
            }
            result.Add(number);
            index++;
        }
        return result.ToArray();
    }

    private static JsonNode BaselineNode(
        Tl1BaselineCatalog baseline,
        string parameterId)
    {
        string raw = baseline.Get(parameterId);
        if (int.TryParse(
                raw,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out int integer))
        {
            return JsonValue.Create(integer)!;
        }
        if (decimal.TryParse(
                raw,
                NumberStyles.Number,
                CultureInfo.InvariantCulture,
                out decimal number))
        {
            return JsonValue.Create(number)!;
        }
        if (bool.TryParse(raw, out bool boolean))
        {
            return JsonValue.Create(boolean)!;
        }
        return JsonValue.Create(raw)!;
    }

    private static JsonNode NumberNode(decimal value)
    {
        if (decimal.Truncate(value) == value &&
            value >= int.MinValue &&
            value <= int.MaxValue)
        {
            return JsonValue.Create((int)value)!;
        }
        return JsonValue.Create(value)!;
    }

    private static string RequireString(
        JsonElement value,
        string path,
        string directive)
    {
        if (value.ValueKind != JsonValueKind.String ||
            string.IsNullOrWhiteSpace(value.GetString()))
        {
            throw new InvalidOperationException(
                $"{path}: {directive} requires a non-empty string argument.");
        }
        return value.GetString()!;
    }

    private static JsonElement SelectPath(JsonElement root, string path)
    {
        if (path == "$")
        {
            return root;
        }
        if (!path.StartsWith("$.", StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"JSON path '{path}' must begin with '$.'.");
        }

        JsonElement current = root;
        int index = 2;
        while (index < path.Length)
        {
            int segmentStart = index;
            while (index < path.Length && path[index] != '.' && path[index] != '[')
            {
                index++;
            }
            if (index > segmentStart)
            {
                string propertyName = path[segmentStart..index];
                if (current.ValueKind != JsonValueKind.Object ||
                    !current.TryGetProperty(propertyName, out JsonElement next))
                {
                    throw new InvalidOperationException(
                        $"JSON path '{path}' could not resolve property '{propertyName}'.");
                }
                current = next;
            }

            while (index < path.Length && path[index] == '[')
            {
                int close = path.IndexOf(']', index + 1);
                if (close < 0 ||
                    !int.TryParse(
                        path[(index + 1)..close],
                        NumberStyles.None,
                        CultureInfo.InvariantCulture,
                        out int arrayIndex))
                {
                    throw new InvalidOperationException(
                        $"JSON path '{path}' contains an invalid array index.");
                }
                if (current.ValueKind != JsonValueKind.Array)
                {
                    throw new InvalidOperationException(
                        $"JSON path '{path}' expected an array before index {arrayIndex}.");
                }
                JsonElement[] items = current.EnumerateArray().ToArray();
                if (arrayIndex < 0 || arrayIndex >= items.Length)
                {
                    throw new InvalidOperationException(
                        $"JSON path '{path}' array index {arrayIndex} is out of range.");
                }
                current = items[arrayIndex];
                index = close + 1;
            }

            if (index < path.Length)
            {
                if (path[index] != '.')
                {
                    throw new InvalidOperationException(
                        $"JSON path '{path}' contains an unexpected character at index {index}.");
                }
                index++;
            }
        }
        return current;
    }

    private static void ValidateNode(
        JsonElement value,
        Tl1BaselineCatalog baseline,
        string path,
        bool allowInputReferences,
        bool allowActualReferences,
        ICollection<string> failures)
    {
        if (value.ValueKind == JsonValueKind.Object)
        {
            JsonProperty[] properties = value.EnumerateObject().ToArray();
            if (properties.Length == 1 && DirectiveNames.Contains(properties[0].Name))
            {
                ValidateDirective(
                    properties[0],
                    baseline,
                    path,
                    allowInputReferences,
                    allowActualReferences,
                    failures);
                return;
            }
            foreach (JsonProperty property in properties)
            {
                ValidateNode(
                    property.Value,
                    baseline,
                    $"{path}.{property.Name}",
                    allowInputReferences,
                    allowActualReferences,
                    failures);
            }
            return;
        }

        if (value.ValueKind == JsonValueKind.Array)
        {
            int index = 0;
            foreach (JsonElement item in value.EnumerateArray())
            {
                ValidateNode(
                    item,
                    baseline,
                    $"{path}[{index}]",
                    allowInputReferences,
                    allowActualReferences,
                    failures);
                index++;
            }
        }
    }

    private static void ValidateDirective(
        JsonProperty directive,
        Tl1BaselineCatalog baseline,
        string path,
        bool allowInputReferences,
        bool allowActualReferences,
        ICollection<string> failures)
    {
        try
        {
            switch (directive.Name)
            {
                case "$baseline":
                    _ = baseline.Get(RequireString(
                        directive.Value, path, directive.Name));
                    break;
                case "$input":
                    if (!allowInputReferences)
                    {
                        failures.Add($"{path}: $input is not allowed in this template.");
                    }
                    _ = RequireString(directive.Value, path, directive.Name);
                    break;
                case "$actual":
                    if (!allowActualReferences)
                    {
                        failures.Add($"{path}: $actual is not allowed in this template.");
                    }
                    _ = RequireString(directive.Value, path, directive.Name);
                    break;
                case "$add":
                case "$multiply":
                case "$min":
                case "$max":
                    if (directive.Value.ValueKind != JsonValueKind.Array ||
                        directive.Value.GetArrayLength() == 0)
                    {
                        failures.Add(
                            $"{path}: {directive.Name} requires a non-empty operand array.");
                    }
                    else
                    {
                        ValidateNode(
                            directive.Value,
                            baseline,
                            path,
                            allowInputReferences,
                            allowActualReferences,
                            failures);
                    }
                    break;
                case "$subtract":
                    if (directive.Value.ValueKind != JsonValueKind.Array ||
                        directive.Value.GetArrayLength() != 2)
                    {
                        failures.Add(
                            $"{path}: $subtract requires exactly two operands.");
                    }
                    else
                    {
                        ValidateNode(
                            directive.Value,
                            baseline,
                            path,
                            allowInputReferences,
                            allowActualReferences,
                            failures);
                    }
                    break;
            }
        }
        catch (Exception exception)
        {
            failures.Add($"{path}: {exception.Message}");
        }
    }
}
