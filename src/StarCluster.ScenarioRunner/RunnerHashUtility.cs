using System.Security.Cryptography;
using System.Text;
using StarCluster.Core.Simulation;

namespace StarCluster.ScenarioRunner;

public static class RunnerHashUtility
{
    private static readonly Lazy<string> RunnerAssemblyHash = new(
        () => ComputeFileSha256(typeof(Program).Assembly.Location),
        LazyThreadSafetyMode.ExecutionAndPublication);

    private static readonly Lazy<string> CoreAssemblyHash = new(
        () => ComputeFileSha256(typeof(ScenarioInitializationService).Assembly.Location),
        LazyThreadSafetyMode.ExecutionAndPublication);

    public static string RunnerAssemblySha256 => RunnerAssemblyHash.Value;

    public static string CoreAssemblySha256 => CoreAssemblyHash.Value;

    public static string ComputeFileSha256(string path)
    {
        if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
        {
            throw new InvalidOperationException(
                $"Cannot hash missing assembly or file '{path}'.");
        }

        using FileStream stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }

    public static string ComputeRunKey(
        string scenarioSha256,
        string variantId,
        string randomSeedNamespace,
        ulong masterSeed,
        string runnerAssemblySha256,
        string coreAssemblySha256)
    {
        string identity = string.Join(
            "\n",
            scenarioSha256,
            variantId,
            randomSeedNamespace,
            masterSeed.ToString(System.Globalization.CultureInfo.InvariantCulture),
            runnerAssemblySha256,
            coreAssemblySha256);
        return Convert.ToHexString(
            SHA256.HashData(Encoding.UTF8.GetBytes(identity)))
            .ToLowerInvariant();
    }
}
