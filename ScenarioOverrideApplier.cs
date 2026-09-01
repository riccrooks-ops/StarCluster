using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace StarCluster.ScenarioRunner;

public static partial class ScenarioOverrideApplier
{
    public static ScenarioDocument Apply(
        ScenarioDocument baseDocument,
        IEnumerable<ScenarioOverrideDocument> overrides)
    {
        ArgumentNullException.ThrowIfNull(baseDocument);
        ArgumentNullException.ThrowIfNull(overrides);

        JsonNode root = JsonNode.Parse(
            ScenarioDocumentSerialization.SerializeCanonical(baseDocument)) ??
            throw new InvalidOperationException("Could not clone the base scenario.");

        foreach (ScenarioOverrideDocument item in overrides)
        {
            ApplyOne(root, item);
        }

        return root.Deserialize<ScenarioDocument>(
                ScenarioDocumentSerialization.ReadOptions) ??
            throw new InvalidOperationException(
                "The overridden scenario could not be deserialized.");
    }

    private static void ApplyOne(JsonNode root, ScenarioOverrideDocument item)
    {
        if (string.IsNullOrWhiteSpace(item.Path))
        {
            throw new InvalidOperationException("A scenario override path is required.");
        }

        MatchCollection matches = PathTokenRegex().Matches(item.Path);
        int consumed = 0;
        foreach (Match match in matches)
        {
            if (match.Index != consumed)
            {
                throw new InvalidOperationException(
                    $"Invalid scenario override path '{item.Path}'.");
            }
            consumed += match.Length;
        }
        if (matches.Count == 0 || consumed != item.Path.Length)
        {
            throw new InvalidOperationException(
                $"Invalid scenario override path '{item.Path}'.");
        }

        JsonNode current = root;
        for (int index = 0; index < matches.Count - 1; index++)
        {
            current = Descend(current, matches[index], item.Path);
        }

        Match final = matches[matches.Count - 1];
        JsonNode? replacement = JsonNode.Parse(item.Value.GetRawText());
        if (final.Groups["property"].Success)
        {
            if (current is not JsonObject objectNode)
            {
                throw new InvalidOperationException(
                    $"Override path '{item.Path}' expected an object at its final parent.");
            }

            objectNode[final.Groups["property"].Value] = replacement;
            return;
        }

        if (current is not JsonArray arrayNode)
        {
            throw new InvalidOperationException(
                $"Override path '{item.Path}' expected an array at its final parent.");
        }

        int arrayIndex = int.Parse(
            final.Groups["index"].Value,
            System.Globalization.CultureInfo.InvariantCulture);
        if (arrayIndex < 0 || arrayIndex >= arrayNode.Count)
        {
            throw new InvalidOperationException(
                $"Override path '{item.Path}' selected array index {arrayIndex} " +
                $"outside 0..{arrayNode.Count - 1}.");
        }
        arrayNode[arrayIndex] = replacement;
    }

    private static JsonNode Descend(JsonNode current, Match token, string path)
    {
        if (token.Groups["property"].Success)
        {
            if (current is not JsonObject objectNode ||
                objectNode[token.Groups["property"].Value] is not JsonNode next)
            {
                throw new InvalidOperationException(
                    $"Override path '{path}' could not find property " +
                    $"'{token.Groups["property"].Value}'.");
            }
            return next;
        }

        if (current is not JsonArray arrayNode)
        {
            throw new InvalidOperationException(
                $"Override path '{path}' expected an array.");
        }
        int arrayIndex = int.Parse(
            token.Groups["index"].Value,
            System.Globalization.CultureInfo.InvariantCulture);
        if (arrayIndex < 0 || arrayIndex >= arrayNode.Count ||
            arrayNode[arrayIndex] is not JsonNode selected)
        {
            throw new InvalidOperationException(
                $"Override path '{path}' selected invalid array index {arrayIndex}.");
        }
        return selected;
    }

    [GeneratedRegex(@"(?:^|\.)(?<property>[A-Za-z_][A-Za-z0-9_]*)|\[(?<index>\d+)\]", RegexOptions.CultureInvariant)]
    private static partial Regex PathTokenRegex();
}
