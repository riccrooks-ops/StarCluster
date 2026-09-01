using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace StarCluster.ScenarioRunner;

public static class ScenarioDocumentSerialization
{
    public static readonly JsonSerializerOptions ReadOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    public static readonly JsonSerializerOptions CompactWriteOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false,
    };

    public static readonly JsonSerializerOptions IndentedWriteOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true,
    };

    public static ScenarioDocument ReadScenario(string path)
    {
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<ScenarioDocument>(json, ReadOptions) ??
            throw new InvalidOperationException(
                $"Scenario '{path}' could not be deserialized.");
    }

    public static SweepDocument ReadSweep(string path)
    {
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<SweepDocument>(json, ReadOptions) ??
            throw new InvalidOperationException(
                $"Sweep '{path}' could not be deserialized.");
    }


    public static TechnologyCalibrationStudyDocument ReadCalibrationStudy(string path)
    {
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<TechnologyCalibrationStudyDocument>(json, ReadOptions) ??
            throw new InvalidOperationException(
                $"Calibration study '{path}' could not be deserialized.");
    }

    public static TechnologyProfileCatalogDocument ReadTechnologyProfileCatalog(string path)
    {
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<TechnologyProfileCatalogDocument>(json, ReadOptions) ??
            throw new InvalidOperationException(
                $"Technology profile catalog '{path}' could not be deserialized.");
    }

    public static FullFlightCalibrationStudyDocument ReadFullFlightCalibrationStudy(string path)
    {
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<FullFlightCalibrationStudyDocument>(json, ReadOptions) ??
            throw new InvalidOperationException(
                $"Full-flight calibration study '{path}' could not be deserialized.");
    }

    public static string SerializeCanonical(ScenarioDocument document) =>
        JsonSerializer.Serialize(document, CompactWriteOptions);

    public static string Sha256Hex(string text)
    {
        byte[] bytes = SHA256.HashData(Encoding.UTF8.GetBytes(text));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}
