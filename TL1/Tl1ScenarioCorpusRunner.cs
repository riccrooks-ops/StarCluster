namespace StarCluster.ScenarioRunner.TL1;

public static class Tl1ScenarioCorpusRunner
{
    public static int Run(
        IReadOnlyList<string> scenarioFiles,
        string baselinePath,
        string outputDirectory,
        bool preflightOnly)
    {
        if (scenarioFiles.Count == 0)
        {
            throw new InvalidOperationException(
                "No TL1 Phase A scenario JSON files were found.");
        }

        Tl1BaselineCatalog baseline = Tl1BaselineCatalog.Load(baselinePath);
        var documents = new List<Tl1MechanicsScenarioDocument>();
        var preflightFailures = new List<(string Id, string Path, string Failure)>();
        foreach (string path in scenarioFiles)
        {
            string fallbackId = Path.GetFileNameWithoutExtension(path);
            try
            {
                Tl1MechanicsScenarioDocument document =
                    Tl1ScenarioSerialization.Read(path);
                string id = string.IsNullOrWhiteSpace(document.Id)
                    ? fallbackId
                    : document.Id;
                foreach (string failure in
                    Tl1ScenarioPreflightValidator.Validate(document))
                {
                    preflightFailures.Add((id, path, failure));
                }
                for (int caseIndex = 0; caseIndex < document.Cases.Count; caseIndex++)
                {
                    Tl1MechanicsCaseDocument testCase = document.Cases[caseIndex];
                    foreach (string failure in
                        Tl1ScenarioValueResolver.ValidateTemplate(
                            testCase.Input,
                            baseline,
                            allowInputReferences: false,
                            allowActualReferences: false))
                    {
                        preflightFailures.Add((
                            id,
                            path,
                            $"cases[{caseIndex}].input {failure}"));
                    }
                    foreach (string failure in
                        Tl1ScenarioValueResolver.ValidateTemplate(
                            testCase.Expected,
                            baseline,
                            allowInputReferences: true,
                            allowActualReferences: true))
                    {
                        preflightFailures.Add((
                            id,
                            path,
                            $"cases[{caseIndex}].expected {failure}"));
                    }
                    foreach (string failure in
                        Tl1ScenarioBaselineBindingValidator.Validate(testCase))
                    {
                        preflightFailures.Add((
                            id,
                            path,
                            $"cases[{caseIndex}] {failure}"));
                    }
                }
                if (!string.Equals(
                        document.BaselineSha256,
                        baseline.Sha256,
                        StringComparison.OrdinalIgnoreCase))
                {
                    preflightFailures.Add((
                        id,
                        path,
                        $"baselineSha256 '{document.BaselineSha256}' does not match loaded baseline '{baseline.Sha256}'."));
                }
                documents.Add(document);
            }
            catch (Exception exception)
            {
                preflightFailures.Add((fallbackId, path, exception.Message));
            }
        }

        int duplicateDocumentIds = documents.Count - documents
            .Select(item => item.Id)
            .Distinct(StringComparer.Ordinal)
            .Count();
        if (duplicateDocumentIds > 0)
        {
            preflightFailures.Add((
                "corpus",
                string.Join(", ", scenarioFiles),
                $"Corpus contains {duplicateDocumentIds} duplicate scenario ID(s)."));
        }

        int duplicateMatrixIds = documents.Count - documents
            .Select(item => item.MatrixScenarioId)
            .Distinct(StringComparer.Ordinal)
            .Count();
        if (duplicateMatrixIds > 0)
        {
            preflightFailures.Add((
                "corpus",
                string.Join(", ", scenarioFiles),
                $"Corpus contains {duplicateMatrixIds} duplicate matrix scenario ID(s)."));
        }

        string[] allCaseIds = documents
            .SelectMany(item => item.Cases)
            .Select(item => item.Id)
            .ToArray();
        int duplicateCaseIds = allCaseIds.Length - allCaseIds
            .Distinct(StringComparer.Ordinal)
            .Count();
        if (duplicateCaseIds > 0)
        {
            preflightFailures.Add((
                "corpus",
                string.Join(", ", scenarioFiles),
                $"Corpus contains {duplicateCaseIds} duplicate mechanics case ID(s)."));
        }

        if (preflightFailures.Count > 0)
        {
            Console.WriteLine(
                $"TL1 Phase A preflight failed: {preflightFailures.Count} issue(s). " +
                "No mechanics cases were executed.");
            foreach (var group in preflightFailures.GroupBy(
                item => item.Id,
                StringComparer.Ordinal))
            {
                Console.WriteLine($"FAIL {group.Key} (preflight)");
                foreach (var failure in group)
                {
                    Console.WriteLine($"     {failure.Failure}");
                }
                Tl1ScenarioOutputWriter.WriteRunnerError(
                    outputDirectory,
                    group.Key,
                    string.Join(
                        Environment.NewLine,
                        group.Select(item =>
                            $"Scenario file: {Path.GetFullPath(item.Path)}" +
                            Environment.NewLine +
                            $"Preflight failure: {item.Failure}")));
            }
            return 1;
        }

        int caseCount = documents.Sum(item => item.Cases.Count);
        Console.WriteLine(
            $"TL1 Phase A preflight: {documents.Count} scenario documents, " +
            $"{caseCount} mechanics cases, baseline {baseline.Count} values; passed.");
        if (preflightOnly)
        {
            return 0;
        }

        var executor = new Tl1ScenarioExecutor(baseline);
        int failedScenarios = 0;
        int failedCases = 0;
        foreach (Tl1MechanicsScenarioDocument document in documents)
        {
            Tl1ScenarioRunResult result = executor.Execute(document);
            Tl1ScenarioOutputWriter.Write(result, baseline, outputDirectory);
            int documentFailedCases = result.Cases.Count(item => !item.Passed);
            failedCases += documentFailedCases;
            if (!result.Passed)
            {
                failedScenarios++;
            }
            Console.WriteLine(
                $"{(result.Passed ? "PASS" : "FAIL")} {document.Id} " +
                $"({result.Cases.Count - documentFailedCases}/" +
                $"{result.Cases.Count} cases)");
            foreach (string failure in result.Failures)
            {
                Console.WriteLine($"     {failure}");
            }
        }

        Console.WriteLine(
            $"TL1 Phase A: {documents.Count - failedScenarios} passed, " +
            $"{failedScenarios} failed, {documents.Count} scenarios; " +
            $"{caseCount - failedCases} passed, {failedCases} failed, " +
            $"{caseCount} cases. Output: {Path.GetFullPath(outputDirectory)}");
        return failedScenarios == 0 ? 0 : 1;
    }
}
