using System.Text.Json;
using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1;

public static class Tl1ScenarioSerialization
{
    public static readonly JsonSerializerOptions ReadOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
        Converters = { new JsonStringEnumConverter() },
    };

    public static readonly JsonSerializerOptions WriteOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true,
        Converters = { new JsonStringEnumConverter() },
    };

    public static Tl1MechanicsScenarioDocument Read(string path)
    {
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<Tl1MechanicsScenarioDocument>(
                json,
                ReadOptions) ??
            throw new InvalidOperationException(
                $"TL1 scenario '{path}' could not be deserialized.");
    }

    public static T ReadInput<T>(JsonElement input) where T : class =>
        input.Deserialize<T>(ReadOptions) ??
        throw new InvalidOperationException(
            $"TL1 scenario input could not be deserialized as {typeof(T).Name}.");

    public static JsonElement ToElement(object value) =>
        JsonSerializer.SerializeToElement(value, WriteOptions);
}
