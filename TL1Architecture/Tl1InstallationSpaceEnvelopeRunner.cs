using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.ScenarioRunner.TL1;

namespace StarCluster.ScenarioRunner.TL1Architecture;

public static class Tl1InstallationSpaceEnvelopeRunner
{
    private const string ExpectedSchemaVersion =
        "star-cluster-tl1-installation-space-envelope-v1";
    private const string ExpectedStudyId =
        "tl1-space01-35-space-construction-envelope";

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        bool preflightOnly)
    {
        Tl1InstallationSpaceEnvelopeStudy study = JsonSerializer.Deserialize<
            Tl1InstallationSpaceEnvelopeStudy>(
                File.ReadAllText(studyPath),
                JsonOptions()) ?? throw new InvalidOperationException(
                "TL1 Installation Space study could not be read.");
        Tl1BaselineCatalog baseline = Tl1BaselineCatalog.Load(baselinePath);

        ValidateStudy(study, baseline);
        IReadOnlyList<Tl1MacroLoadout> macroLoadouts = EnumerateMacroLoadouts(study);
        IReadOnlyList<Tl1PowerVariant> powerVariants = ExpandPowerVariants(
            study,
            baseline,
            macroLoadouts);
        IReadOnlyList<Tl1ReferenceBuildEvidence> referenceEvidence =
            BuildReferenceEvidence(study, macroLoadouts);
        IReadOnlyList<Tl1ArchitectureGate> gates = BuildGates(
            study,
            baseline,
            macroLoadouts,
            powerVariants,
            referenceEvidence);
        int failed = gates.Count(gate => !gate.Passed);

        int exactFill = macroLoadouts.Count(row => row.FreeSupportSpace == 0);
        int nominalOvercommit = powerVariants.Count(row => row.PowerMargin < 0);
        Console.WriteLine(
            "TL1 35-Space architecture preflight: " +
            $"{macroLoadouts.Count} macro loadouts, " +
            $"{powerVariants.Count} weapon/power variants, " +
            $"{exactFill} exact-fill macro loadouts, " +
            $"{nominalOvercommit} nominal power-overcommit variants, " +
            $"{failed} failed gates.");

        if (preflightOnly)
        {
            return failed == 0 ? 0 : 1;
        }

        Directory.CreateDirectory(outputDirectory);
        WriteMacroLoadouts(macroLoadouts, outputDirectory);
        WritePowerVariants(powerVariants, outputDirectory);
        WriteReferenceEvidence(referenceEvidence, outputDirectory);
        WriteGates(gates, outputDirectory);
        WriteSummary(
            study,
            baseline,
            macroLoadouts,
            powerVariants,
            referenceEvidence,
            gates,
            outputDirectory);
        WriteResultHash(outputDirectory);

        Console.WriteLine(
            $"TL1 Installation Space Envelope: {failed} failed gates. " +
            $"Output: {Path.GetFullPath(outputDirectory)}");
        return failed == 0 ? 0 : 1;
    }

    private static void ValidateStudy(
        Tl1InstallationSpaceEnvelopeStudy study,
        Tl1BaselineCatalog baseline)
    {
        if (!string.Equals(
                study.SchemaVersion,
                ExpectedSchemaVersion,
                StringComparison.Ordinal) ||
            !string.Equals(study.Id, ExpectedStudyId, StringComparison.Ordinal) ||
            study.Checkpoint != 60 ||
            string.IsNullOrWhiteSpace(study.Status) ||
            string.IsNullOrWhiteSpace(study.Policy))
        {
            throw new InvalidOperationException(
                "Unexpected TL1 Installation Space study identity.");
        }
        if (study.TotalSpace <= 0 || study.FixedPrimarySystems.Count != 3)
        {
            throw new InvalidOperationException(
                "TL1 Installation Space fixed architecture is invalid.");
        }
        string[] expectedFixed = { "stl_drive", "ftl_drive", "tactical_computer" };
        foreach (string id in expectedFixed)
        {
            if (!study.FixedPrimarySystems.Any(item =>
                    string.Equals(item.Id, id, StringComparison.Ordinal) &&
                    item.Space > 0))
            {
                throw new InvalidOperationException(
                    $"TL1 Installation Space study is missing fixed primary system '{id}'.");
            }
        }
        if (study.MainWeapon.Space <= 0 || study.MainWeapon.MinimumCount != 1 ||
            study.MainReactor.Space <= 0 || study.MainReactor.MinimumCount != 1 ||
            study.ActiveSensor.Space <= 0 || study.ActiveSensor.MaximumCount != 1 ||
            study.ShieldGenerator.Space <= 0 || study.ShieldGenerator.MaximumCount != 1 ||
            study.KineticPds.Space <= 0 || study.KineticPds.MinimumCount != 0)
        {
            throw new InvalidOperationException(
                "TL1 Installation Space variable-system inputs are invalid.");
        }
        if (study.PowerDiagnostic.WeaponFamilies.Count != 3 ||
            study.PowerDiagnostic.ActiveSensorSettingOnePower < 0 ||
            string.IsNullOrWhiteSpace(study.PowerDiagnostic.ReactorOutputParameterId) ||
            string.IsNullOrWhiteSpace(study.PowerDiagnostic.PdsPowerParameterId))
        {
            throw new InvalidOperationException(
                "TL1 Installation Space power-diagnostic inputs are invalid.");
        }
        string[] expectedFamilies = { "kinetic", "energy", "missile" };
        foreach (string family in expectedFamilies)
        {
            Tl1WeaponFamilyPowerInput? item = study.PowerDiagnostic.WeaponFamilies
                .SingleOrDefault(value => string.Equals(
                    value.Id,
                    family,
                    StringComparison.Ordinal));
            if (item is null || string.IsNullOrWhiteSpace(item.PowerParameterId))
            {
                throw new InvalidOperationException(
                    $"TL1 Installation Space study is missing weapon family '{family}'.");
            }
            _ = baseline.GetInt(item.PowerParameterId);
        }
        _ = baseline.GetInt(study.PowerDiagnostic.ReactorOutputParameterId);
        _ = baseline.GetInt(study.PowerDiagnostic.PdsPowerParameterId);
        if (study.ReferenceBuilds.Count == 0)
        {
            throw new InvalidOperationException(
                "TL1 Installation Space study requires reference builds.");
        }
    }

    private static IReadOnlyList<Tl1MacroLoadout> EnumerateMacroLoadouts(
        Tl1InstallationSpaceEnvelopeStudy study)
    {
        int fixedSpace = study.FixedPrimarySystems.Sum(item => item.Space);
        int weaponMax = study.TotalSpace / study.MainWeapon.Space;
        int reactorMax = study.TotalSpace / study.MainReactor.Space;
        int pdsMax = study.TotalSpace / study.KineticPds.Space;
        var rows = new List<Tl1MacroLoadout>();

        for (int weapons = study.MainWeapon.MinimumCount; weapons <= weaponMax; weapons++)
        {
            for (int reactors = study.MainReactor.MinimumCount; reactors <= reactorMax; reactors++)
            {
                for (int sensor = 0; sensor <= study.ActiveSensor.MaximumCount; sensor++)
                {
                    for (int shield = 0; shield <= study.ShieldGenerator.MaximumCount; shield++)
                    {
                        for (int pds = study.KineticPds.MinimumCount; pds <= pdsMax; pds++)
                        {
                            int used = checked(
                                fixedSpace +
                                weapons * study.MainWeapon.Space +
                                reactors * study.MainReactor.Space +
                                sensor * study.ActiveSensor.Space +
                                shield * study.ShieldGenerator.Space +
                                pds * study.KineticPds.Space);
                            if (used > study.TotalSpace)
                            {
                                continue;
                            }
                            rows.Add(new Tl1MacroLoadout(
                                weapons,
                                reactors,
                                sensor == 1,
                                shield == 1,
                                pds,
                                used,
                                study.TotalSpace - used));
                        }
                    }
                }
            }
        }

        return rows
            .OrderBy(row => row.MainWeaponCount)
            .ThenBy(row => row.MainReactorCount)
            .ThenBy(row => row.ActiveSensor ? 1 : 0)
            .ThenBy(row => row.ShieldGenerator ? 1 : 0)
            .ThenBy(row => row.KineticPdsCount)
            .ToArray();
    }

    private static IReadOnlyList<Tl1PowerVariant> ExpandPowerVariants(
        Tl1InstallationSpaceEnvelopeStudy study,
        Tl1BaselineCatalog baseline,
        IReadOnlyList<Tl1MacroLoadout> macroLoadouts)
    {
        int reactorOutput = baseline.GetInt(
            study.PowerDiagnostic.ReactorOutputParameterId);
        int pdsPower = baseline.GetInt(
            study.PowerDiagnostic.PdsPowerParameterId);
        var familyPowers = study.PowerDiagnostic.WeaponFamilies
            .ToDictionary(
                item => item.Id,
                item => baseline.GetInt(item.PowerParameterId),
                StringComparer.Ordinal);
        string[] orderedFamilies = study.PowerDiagnostic.WeaponFamilies
            .Select(item => item.Id)
            .ToArray();
        var rows = new List<Tl1PowerVariant>();

        foreach (Tl1MacroLoadout macro in macroLoadouts)
        {
            IReadOnlyList<IReadOnlyList<string>> patterns = BuildWeaponPatterns(
                orderedFamilies,
                macro.MainWeaponCount);
            foreach (IReadOnlyList<string> pattern in patterns)
            {
                int weaponPower = pattern.Sum(family => familyPowers[family]);
                int sensorPower = macro.ActiveSensor
                    ? study.PowerDiagnostic.ActiveSensorSettingOnePower
                    : 0;
                int readiedPdsPower = checked(macro.KineticPdsCount * pdsPower);
                int demand = checked(weaponPower + sensorPower + readiedPdsPower);
                int output = checked(macro.MainReactorCount * reactorOutput);
                rows.Add(new Tl1PowerVariant(
                    macro.MainWeaponCount,
                    macro.MainReactorCount,
                    macro.ActiveSensor,
                    macro.ShieldGenerator,
                    macro.KineticPdsCount,
                    macro.UsedSpace,
                    macro.FreeSupportSpace,
                    string.Join("+", pattern),
                    weaponPower,
                    sensorPower,
                    readiedPdsPower,
                    demand,
                    output,
                    output - demand));
            }
        }

        return rows.ToArray();
    }

    private static IReadOnlyList<IReadOnlyList<string>> BuildWeaponPatterns(
        IReadOnlyList<string> families,
        int count)
    {
        var result = new List<IReadOnlyList<string>>();
        var current = new List<string>();

        void Add(int startIndex)
        {
            if (current.Count == count)
            {
                result.Add(current.ToArray());
                return;
            }
            for (int index = startIndex; index < families.Count; index++)
            {
                current.Add(families[index]);
                Add(index);
                current.RemoveAt(current.Count - 1);
            }
        }

        Add(0);
        return result;
    }

    private static IReadOnlyList<Tl1ReferenceBuildEvidence> BuildReferenceEvidence(
        Tl1InstallationSpaceEnvelopeStudy study,
        IReadOnlyList<Tl1MacroLoadout> macroLoadouts)
    {
        var rows = new List<Tl1ReferenceBuildEvidence>();
        int fixedSpace = study.FixedPrimarySystems.Sum(item => item.Space);
        foreach (Tl1ReferenceBuildInput input in study.ReferenceBuilds)
        {
            int used = checked(
                fixedSpace +
                input.MainWeaponCount * study.MainWeapon.Space +
                input.MainReactorCount * study.MainReactor.Space +
                (input.ActiveSensor ? study.ActiveSensor.Space : 0) +
                (input.ShieldGenerator ? study.ShieldGenerator.Space : 0) +
                input.KineticPdsCount * study.KineticPds.Space);
            bool legal = used <= study.TotalSpace && macroLoadouts.Any(row =>
                row.MainWeaponCount == input.MainWeaponCount &&
                row.MainReactorCount == input.MainReactorCount &&
                row.ActiveSensor == input.ActiveSensor &&
                row.ShieldGenerator == input.ShieldGenerator &&
                row.KineticPdsCount == input.KineticPdsCount);
            rows.Add(new Tl1ReferenceBuildEvidence(
                input.Id,
                input.Description,
                input.MainWeaponCount,
                input.MainReactorCount,
                input.ActiveSensor,
                input.ShieldGenerator,
                input.KineticPdsCount,
                used,
                study.TotalSpace - used,
                legal,
                input.ExpectedUsedSpace,
                input.ExpectedFreeSupportSpace,
                input.ExpectedLegal));
        }
        return rows;
    }

    private static IReadOnlyList<Tl1ArchitectureGate> BuildGates(
        Tl1InstallationSpaceEnvelopeStudy study,
        Tl1BaselineCatalog baseline,
        IReadOnlyList<Tl1MacroLoadout> macroLoadouts,
        IReadOnlyList<Tl1PowerVariant> powerVariants,
        IReadOnlyList<Tl1ReferenceBuildEvidence> referenceEvidence)
    {
        var gates = new List<Tl1ArchitectureGate>();
        void Gate(string id, bool passed, string detail) =>
            gates.Add(new Tl1ArchitectureGate(id, passed, detail));

        int fixedSpace = study.FixedPrimarySystems.Sum(item => item.Space);
        int mandatoryCoreSpace = fixedSpace +
            study.MainWeapon.MinimumCount * study.MainWeapon.Space +
            study.MainReactor.MinimumCount * study.MainReactor.Space;
        Gate(
            "total-space",
            study.TotalSpace == study.Expected.TotalSpace,
            $"Expected {study.Expected.TotalSpace}; observed {study.TotalSpace}.");
        Gate(
            "fixed-primary-space",
            fixedSpace == study.Expected.FixedPrimarySpace,
            $"Expected {study.Expected.FixedPrimarySpace}; observed {fixedSpace}.");
        Gate(
            "mandatory-core-space",
            mandatoryCoreSpace == study.Expected.MandatoryCoreSpace,
            $"Expected {study.Expected.MandatoryCoreSpace}; observed {mandatoryCoreSpace}.");
        Gate(
            "macro-loadout-count",
            macroLoadouts.Count == study.Expected.MacroLoadoutCount,
            $"Expected {study.Expected.MacroLoadoutCount}; observed {macroLoadouts.Count}.");
        Gate(
            "weapon-power-variant-count",
            powerVariants.Count == study.Expected.WeaponPowerVariantCount,
            $"Expected {study.Expected.WeaponPowerVariantCount}; observed {powerVariants.Count}.");
        Gate(
            "exact-fill-macro-count",
            macroLoadouts.Count(row => row.FreeSupportSpace == 0) ==
                study.Expected.ExactFillMacroCount,
            $"Expected {study.Expected.ExactFillMacroCount}; observed " +
            $"{macroLoadouts.Count(row => row.FreeSupportSpace == 0)}.");
        Gate(
            "maximum-main-weapons",
            macroLoadouts.Max(row => row.MainWeaponCount) ==
                study.Expected.MaximumMainWeapons,
            $"Expected {study.Expected.MaximumMainWeapons}; observed " +
            $"{macroLoadouts.Max(row => row.MainWeaponCount)}.");
        Gate(
            "maximum-main-reactors",
            macroLoadouts.Max(row => row.MainReactorCount) ==
                study.Expected.MaximumMainReactors,
            $"Expected {study.Expected.MaximumMainReactors}; observed " +
            $"{macroLoadouts.Max(row => row.MainReactorCount)}.");
        Gate(
            "maximum-kinetic-pds",
            macroLoadouts.Max(row => row.KineticPdsCount) ==
                study.Expected.MaximumKineticPds,
            $"Expected {study.Expected.MaximumKineticPds}; observed " +
            $"{macroLoadouts.Max(row => row.KineticPdsCount)}.");
        bool dualDualLegal = macroLoadouts.Any(row =>
            row.MainWeaponCount >= 2 && row.MainReactorCount >= 2);
        Gate(
            "dual-main-dual-reactor-does-not-fit",
            dualDualLegal == study.Expected.DualMainDualReactorLegal,
            $"Expected legal={study.Expected.DualMainDualReactorLegal}; observed legal={dualDualLegal}.");
        int dualDualSpace = checked(
            fixedSpace +
            2 * study.MainWeapon.Space +
            2 * study.MainReactor.Space);
        Gate(
            "dual-main-dual-reactor-space",
            dualDualSpace == study.Expected.DualMainDualReactorSpace,
            $"Expected {study.Expected.DualMainDualReactorSpace}; observed {dualDualSpace}.");
        Gate(
            "free-support-space-range",
            macroLoadouts.Min(row => row.FreeSupportSpace) == 0 &&
            macroLoadouts.Max(row => row.FreeSupportSpace) ==
                study.Expected.MaximumFreeSupportSpace,
            $"Observed free support range " +
            $"{macroLoadouts.Min(row => row.FreeSupportSpace)}.." +
            $"{macroLoadouts.Max(row => row.FreeSupportSpace)}.");

        int overcommit = powerVariants.Count(row => row.PowerMargin < 0);
        int exactPower = powerVariants.Count(row => row.PowerMargin == 0);
        Gate(
            "nominal-power-overcommit-count",
            overcommit == study.Expected.NominalPowerOvercommitVariantCount,
            $"Expected {study.Expected.NominalPowerOvercommitVariantCount}; observed {overcommit}.");
        Gate(
            "nominal-power-exact-count",
            exactPower == study.Expected.NominalPowerExactVariantCount,
            $"Expected {study.Expected.NominalPowerExactVariantCount}; observed {exactPower}.");
        Gate(
            "power-margin-range",
            powerVariants.Min(row => row.PowerMargin) == study.Expected.MinimumPowerMargin &&
            powerVariants.Max(row => row.PowerMargin) == study.Expected.MaximumPowerMargin,
            $"Expected {study.Expected.MinimumPowerMargin}..{study.Expected.MaximumPowerMargin}; observed " +
            $"{powerVariants.Min(row => row.PowerMargin)}..{powerVariants.Max(row => row.PowerMargin)}.");
        Gate(
            "retained-reactor-output",
            baseline.GetInt(study.PowerDiagnostic.ReactorOutputParameterId) == 5,
            $"Observed {baseline.GetInt(study.PowerDiagnostic.ReactorOutputParameterId)} TP per Operational TL1 reactor.");
        Gate(
            "retained-main-weapon-power",
            GetFamilyPower(study, baseline, "kinetic") == 1 &&
            GetFamilyPower(study, baseline, "energy") == 2 &&
            GetFamilyPower(study, baseline, "missile") == 0,
            "Expected retained TL1 standard main-weapon costs K/E/M = 1/2/0 TP.");
        Gate(
            "retained-pds-readiness-power",
            baseline.GetInt(study.PowerDiagnostic.PdsPowerParameterId) == 1,
            $"Observed {baseline.GetInt(study.PowerDiagnostic.PdsPowerParameterId)} TP per readied kinetic PDS.");
        Gate(
            "construction-legality-independent-of-nominal-power",
            overcommit > 0 && powerVariants.Where(row => row.PowerMargin < 0).All(row =>
                macroLoadouts.Any(macro =>
                    macro.MainWeaponCount == row.MainWeaponCount &&
                    macro.MainReactorCount == row.MainReactorCount &&
                    macro.ActiveSensor == row.ActiveSensor &&
                    macro.ShieldGenerator == row.ShieldGenerator &&
                    macro.KineticPdsCount == row.KineticPdsCount)),
            "Nominal power overcommit is a tactical operating constraint, not an Installation Space legality rule.");

        foreach (Tl1ReferenceBuildEvidence row in referenceEvidence)
        {
            bool passed = row.UsedSpace == row.ExpectedUsedSpace &&
                row.FreeSupportSpace == row.ExpectedFreeSupportSpace &&
                row.Legal == row.ExpectedLegal;
            Gate(
                $"reference-{row.Id}",
                passed,
                $"Used/free/legal observed {row.UsedSpace}/{row.FreeSupportSpace}/{row.Legal}; " +
                $"expected {row.ExpectedUsedSpace}/{row.ExpectedFreeSupportSpace}/{row.ExpectedLegal}.");
        }

        return gates;
    }

    private static int GetFamilyPower(
        Tl1InstallationSpaceEnvelopeStudy study,
        Tl1BaselineCatalog baseline,
        string familyId)
    {
        Tl1WeaponFamilyPowerInput family = study.PowerDiagnostic.WeaponFamilies
            .Single(item => string.Equals(item.Id, familyId, StringComparison.Ordinal));
        return baseline.GetInt(family.PowerParameterId);
    }

    private static void WriteMacroLoadouts(
        IReadOnlyList<Tl1MacroLoadout> rows,
        string outputDirectory)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "main_weapons,main_reactors,active_sensor,shield_generator,kinetic_pds,used_space,free_support_space");
        foreach (Tl1MacroLoadout row in rows)
        {
            builder.AppendLine(string.Join(",", new[]
            {
                row.MainWeaponCount.ToString(CultureInfo.InvariantCulture),
                row.MainReactorCount.ToString(CultureInfo.InvariantCulture),
                Bool(row.ActiveSensor),
                Bool(row.ShieldGenerator),
                row.KineticPdsCount.ToString(CultureInfo.InvariantCulture),
                row.UsedSpace.ToString(CultureInfo.InvariantCulture),
                row.FreeSupportSpace.ToString(CultureInfo.InvariantCulture),
            }));
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "macro-loadouts.csv"),
            builder.ToString(),
            Encoding.UTF8);
    }

    private static void WritePowerVariants(
        IReadOnlyList<Tl1PowerVariant> rows,
        string outputDirectory)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "main_weapons,main_reactors,active_sensor,shield_generator,kinetic_pds,used_space,free_support_space,weapon_pattern,weapon_power,sensor_power,pds_power,nominal_demand,reactor_output,power_margin,nominal_all_systems_feasible");
        foreach (Tl1PowerVariant row in rows)
        {
            builder.AppendLine(string.Join(",", new[]
            {
                row.MainWeaponCount.ToString(CultureInfo.InvariantCulture),
                row.MainReactorCount.ToString(CultureInfo.InvariantCulture),
                Bool(row.ActiveSensor),
                Bool(row.ShieldGenerator),
                row.KineticPdsCount.ToString(CultureInfo.InvariantCulture),
                row.UsedSpace.ToString(CultureInfo.InvariantCulture),
                row.FreeSupportSpace.ToString(CultureInfo.InvariantCulture),
                Csv(row.WeaponPattern),
                row.WeaponPower.ToString(CultureInfo.InvariantCulture),
                row.SensorPower.ToString(CultureInfo.InvariantCulture),
                row.PdsPower.ToString(CultureInfo.InvariantCulture),
                row.NominalDemand.ToString(CultureInfo.InvariantCulture),
                row.ReactorOutput.ToString(CultureInfo.InvariantCulture),
                row.PowerMargin.ToString(CultureInfo.InvariantCulture),
                Bool(row.PowerMargin >= 0),
            }));
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "power-variants.csv"),
            builder.ToString(),
            Encoding.UTF8);
    }

    private static void WriteReferenceEvidence(
        IReadOnlyList<Tl1ReferenceBuildEvidence> rows,
        string outputDirectory)
    {
        var builder = new StringBuilder();
        builder.AppendLine(
            "id,description,main_weapons,main_reactors,active_sensor,shield_generator,kinetic_pds,used_space,free_support_space,legal,expected_used_space,expected_free_support_space,expected_legal");
        foreach (Tl1ReferenceBuildEvidence row in rows)
        {
            builder.AppendLine(string.Join(",", new[]
            {
                Csv(row.Id),
                Csv(row.Description),
                row.MainWeaponCount.ToString(CultureInfo.InvariantCulture),
                row.MainReactorCount.ToString(CultureInfo.InvariantCulture),
                Bool(row.ActiveSensor),
                Bool(row.ShieldGenerator),
                row.KineticPdsCount.ToString(CultureInfo.InvariantCulture),
                row.UsedSpace.ToString(CultureInfo.InvariantCulture),
                row.FreeSupportSpace.ToString(CultureInfo.InvariantCulture),
                Bool(row.Legal),
                row.ExpectedUsedSpace.ToString(CultureInfo.InvariantCulture),
                row.ExpectedFreeSupportSpace.ToString(CultureInfo.InvariantCulture),
                Bool(row.ExpectedLegal),
            }));
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "reference-builds.csv"),
            builder.ToString(),
            Encoding.UTF8);
    }

    private static void WriteGates(
        IReadOnlyList<Tl1ArchitectureGate> gates,
        string outputDirectory)
    {
        var builder = new StringBuilder();
        builder.AppendLine("gate_id,passed,detail");
        foreach (Tl1ArchitectureGate gate in gates)
        {
            builder.AppendLine(string.Join(",", new[]
            {
                Csv(gate.Id),
                Bool(gate.Passed),
                Csv(gate.Detail),
            }));
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "gates.csv"),
            builder.ToString(),
            Encoding.UTF8);
    }

    private static void WriteSummary(
        Tl1InstallationSpaceEnvelopeStudy study,
        Tl1BaselineCatalog baseline,
        IReadOnlyList<Tl1MacroLoadout> macroLoadouts,
        IReadOnlyList<Tl1PowerVariant> powerVariants,
        IReadOnlyList<Tl1ReferenceBuildEvidence> referenceEvidence,
        IReadOnlyList<Tl1ArchitectureGate> gates,
        string outputDirectory)
    {
        int failed = gates.Count(gate => !gate.Passed);
        var summary = new
        {
            study.SchemaVersion,
            study.Id,
            study.Checkpoint,
            study.Status,
            study.Policy,
            study.TotalSpace,
            baseline = new
            {
                path = baseline.SourcePath,
                sha256 = baseline.Sha256,
                valueCount = baseline.Count,
            },
            counts = new
            {
                macroLoadouts = macroLoadouts.Count,
                weaponPowerVariants = powerVariants.Count,
                exactFillMacroLoadouts = macroLoadouts.Count(row => row.FreeSupportSpace == 0),
                nominalPowerOvercommitVariants = powerVariants.Count(row => row.PowerMargin < 0),
                nominalPowerExactVariants = powerVariants.Count(row => row.PowerMargin == 0),
                referenceBuilds = referenceEvidence.Count,
                gates = gates.Count,
                failedGates = failed,
            },
            envelope = new
            {
                maximumMainWeapons = macroLoadouts.Max(row => row.MainWeaponCount),
                maximumMainReactors = macroLoadouts.Max(row => row.MainReactorCount),
                maximumKineticPds = macroLoadouts.Max(row => row.KineticPdsCount),
                minimumFreeSupportSpace = macroLoadouts.Min(row => row.FreeSupportSpace),
                maximumFreeSupportSpace = macroLoadouts.Max(row => row.FreeSupportSpace),
                minimumNominalPowerMargin = powerVariants.Min(row => row.PowerMargin),
                maximumNominalPowerMargin = powerVariants.Max(row => row.PowerMargin),
            },
            diagnosticPowerPolicy = study.PowerDiagnostic.Policy,
            supportSpacePolicy = study.SupportSpacePolicy,
            referenceBuilds = referenceEvidence,
            gates,
        };
        File.WriteAllText(
            Path.Combine(outputDirectory, "summary.json"),
            JsonSerializer.Serialize(summary, JsonOptions(writeIndented: true)) + "\n",
            Encoding.UTF8);
    }

    private static void WriteResultHash(string outputDirectory)
    {
        string[] names = Directory.GetFiles(outputDirectory)
            .Where(path => !string.Equals(
                Path.GetFileName(path),
                "result-sha256.txt",
                StringComparison.OrdinalIgnoreCase))
            .OrderBy(path => Path.GetFileName(path), StringComparer.Ordinal)
            .ToArray();
        using IncrementalHash hasher = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (string path in names)
        {
            byte[] name = Encoding.UTF8.GetBytes(Path.GetFileName(path) + "\n");
            hasher.AppendData(name);
            hasher.AppendData(File.ReadAllBytes(path));
        }
        string hash = Convert.ToHexString(hasher.GetHashAndReset()).ToLowerInvariant();
        File.WriteAllText(
            Path.Combine(outputDirectory, "result-sha256.txt"),
            hash + "\n",
            Encoding.UTF8);
    }

    private static string Bool(bool value) => value ? "true" : "false";

    private static string Csv(string value)
    {
        if (!value.Contains(',') &&
            !value.Contains('"') &&
            !value.Contains('\n') &&
            !value.Contains('\r'))
        {
            return value;
        }
        return "\"" + value.Replace("\"", "\"\"", StringComparison.Ordinal) + "\"";
    }

    private static JsonSerializerOptions JsonOptions(bool writeIndented = false) =>
        new()
        {
            PropertyNameCaseInsensitive = true,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = writeIndented,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        };
}

public sealed class Tl1InstallationSpaceEnvelopeStudy
{
    public string SchemaVersion { get; set; } = string.Empty;
    public string Id { get; set; } = string.Empty;
    public int Checkpoint { get; set; }
    public string Status { get; set; } = string.Empty;
    public string Policy { get; set; } = string.Empty;
    public int TotalSpace { get; set; }
    public List<Tl1FixedPrimarySystemInput> FixedPrimarySystems { get; set; } = new();
    public Tl1CountedSpaceInput MainWeapon { get; set; } = new();
    public Tl1CountedSpaceInput MainReactor { get; set; } = new();
    public Tl1OptionalSpaceInput ActiveSensor { get; set; } = new();
    public Tl1OptionalSpaceInput ShieldGenerator { get; set; } = new();
    public Tl1CountedSpaceInput KineticPds { get; set; } = new();
    public Tl1PowerDiagnosticInput PowerDiagnostic { get; set; } = new();
    public string SupportSpacePolicy { get; set; } = string.Empty;
    public List<Tl1ReferenceBuildInput> ReferenceBuilds { get; set; } = new();
    public Tl1ArchitectureExpectedInput Expected { get; set; } = new();
}

public sealed class Tl1FixedPrimarySystemInput
{
    public string Id { get; set; } = string.Empty;
    public int Space { get; set; }
}

public sealed class Tl1CountedSpaceInput
{
    public string Id { get; set; } = string.Empty;
    public int Space { get; set; }
    public int MinimumCount { get; set; }
}

public sealed class Tl1OptionalSpaceInput
{
    public string Id { get; set; } = string.Empty;
    public int Space { get; set; }
    public int MaximumCount { get; set; }
}

public sealed class Tl1PowerDiagnosticInput
{
    public string Policy { get; set; } = string.Empty;
    public string ReactorOutputParameterId { get; set; } = string.Empty;
    public string PdsPowerParameterId { get; set; } = string.Empty;
    public int ActiveSensorSettingOnePower { get; set; }
    public List<Tl1WeaponFamilyPowerInput> WeaponFamilies { get; set; } = new();
}

public sealed class Tl1WeaponFamilyPowerInput
{
    public string Id { get; set; } = string.Empty;
    public string PowerParameterId { get; set; } = string.Empty;
}

public sealed class Tl1ReferenceBuildInput
{
    public string Id { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int MainWeaponCount { get; set; }
    public int MainReactorCount { get; set; }
    public bool ActiveSensor { get; set; }
    public bool ShieldGenerator { get; set; }
    public int KineticPdsCount { get; set; }
    public int ExpectedUsedSpace { get; set; }
    public int ExpectedFreeSupportSpace { get; set; }
    public bool ExpectedLegal { get; set; }
}

public sealed class Tl1ArchitectureExpectedInput
{
    public int TotalSpace { get; set; }
    public int FixedPrimarySpace { get; set; }
    public int MandatoryCoreSpace { get; set; }
    public int MacroLoadoutCount { get; set; }
    public int WeaponPowerVariantCount { get; set; }
    public int ExactFillMacroCount { get; set; }
    public int MaximumMainWeapons { get; set; }
    public int MaximumMainReactors { get; set; }
    public int MaximumKineticPds { get; set; }
    public int MaximumFreeSupportSpace { get; set; }
    public bool DualMainDualReactorLegal { get; set; }
    public int DualMainDualReactorSpace { get; set; }
    public int NominalPowerOvercommitVariantCount { get; set; }
    public int NominalPowerExactVariantCount { get; set; }
    public int MinimumPowerMargin { get; set; }
    public int MaximumPowerMargin { get; set; }
}

public sealed record Tl1MacroLoadout(
    int MainWeaponCount,
    int MainReactorCount,
    bool ActiveSensor,
    bool ShieldGenerator,
    int KineticPdsCount,
    int UsedSpace,
    int FreeSupportSpace);

public sealed record Tl1PowerVariant(
    int MainWeaponCount,
    int MainReactorCount,
    bool ActiveSensor,
    bool ShieldGenerator,
    int KineticPdsCount,
    int UsedSpace,
    int FreeSupportSpace,
    string WeaponPattern,
    int WeaponPower,
    int SensorPower,
    int PdsPower,
    int NominalDemand,
    int ReactorOutput,
    int PowerMargin);

public sealed record Tl1ReferenceBuildEvidence(
    string Id,
    string Description,
    int MainWeaponCount,
    int MainReactorCount,
    bool ActiveSensor,
    bool ShieldGenerator,
    int KineticPdsCount,
    int UsedSpace,
    int FreeSupportSpace,
    bool Legal,
    int ExpectedUsedSpace,
    int ExpectedFreeSupportSpace,
    bool ExpectedLegal);

public sealed record Tl1ArchitectureGate(
    string Id,
    bool Passed,
    string Detail);
