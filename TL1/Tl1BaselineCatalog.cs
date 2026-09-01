using System.Globalization;
using System.Security.Cryptography;

namespace StarCluster.ScenarioRunner.TL1;

public sealed class Tl1BaselineCatalog
{
    private readonly Dictionary<string, string> _values;

    private Tl1BaselineCatalog(
        string sourcePath,
        string sha256,
        Dictionary<string, string> values)
    {
        SourcePath = sourcePath;
        Sha256 = sha256;
        _values = values;
    }

    public string SourcePath { get; }

    public string Sha256 { get; }

    public int Count => _values.Count;

    public static Tl1BaselineCatalog Load(string path)
    {
        string fullPath = Path.GetFullPath(path);
        IReadOnlyList<IReadOnlyList<string>> rows = Tl1Csv.Read(fullPath);
        if (rows.Count < 2)
        {
            throw new InvalidOperationException(
                $"TL1 baseline '{fullPath}' does not contain data rows.");
        }

        IReadOnlyList<string> header = rows[0];
        int parameterIndex = FindColumn(header, "parameter_id");
        int valueIndex = FindColumn(header, "value");
        var values = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (IReadOnlyList<string> row in rows.Skip(1))
        {
            if (row.Count != header.Count)
            {
                throw new InvalidOperationException(
                    $"TL1 baseline row has {row.Count} columns; expected {header.Count}.");
            }
            string parameterId = row[parameterIndex];
            if (string.IsNullOrWhiteSpace(parameterId))
            {
                throw new InvalidOperationException(
                    "TL1 baseline contains an empty parameter_id.");
            }
            if (!values.TryAdd(parameterId, row[valueIndex]))
            {
                throw new InvalidOperationException(
                    $"TL1 baseline contains duplicate parameter '{parameterId}'.");
            }
        }

        string hash = Convert.ToHexString(
            SHA256.HashData(File.ReadAllBytes(fullPath))).ToLowerInvariant();
        return new Tl1BaselineCatalog(fullPath, hash, values);
    }

    public int GetInt(string parameterId)
    {
        string value = Get(parameterId);
        if (!int.TryParse(
                value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out int parsed))
        {
            throw new InvalidOperationException(
                $"TL1 baseline parameter '{parameterId}' is not an integer: '{value}'.");
        }
        return parsed;
    }

    public string Get(string parameterId)
    {
        if (!_values.TryGetValue(parameterId, out string? value))
        {
            throw new KeyNotFoundException(
                $"TL1 baseline parameter '{parameterId}' was not found.");
        }
        return value;
    }

    private static int FindColumn(
        IReadOnlyList<string> header,
        string columnName)
    {
        for (int index = 0; index < header.Count; index++)
        {
            if (string.Equals(
                    header[index],
                    columnName,
                    StringComparison.Ordinal))
            {
                return index;
            }
        }
        throw new InvalidOperationException(
            $"TL1 baseline is missing required column '{columnName}'.");
    }
}
