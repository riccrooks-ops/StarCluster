using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Weapons;
using StarCluster.ScenarioRunner.TL1;

namespace StarCluster.ScenarioRunner.TL2Scaling;

public static class CombatScalingStudyRunner
{
    private const string SchemaVersion = "star-cluster-combat-scaling-v2";
    private static readonly WeaponFamily[] Families =
    {
        WeaponFamily.Kinetic,
        WeaponFamily.Energy,
        WeaponFamily.Missile,
    };

    public static int Run(
        string studyPath,
        string baselinePath,
        string outputDirectory,
        bool preflightOnly)
    {
        CombatScalingStudyDocument study = JsonSerializer.Deserialize<CombatScalingStudyDocument>(
            File.ReadAllText(studyPath),
            JsonOptions()) ?? throw new InvalidOperationException(
                "Combat-scaling study could not be read.");
        Tl1BaselineCatalog baseline = Tl1BaselineCatalog.Load(baselinePath);
        Validate(study, baseline);
        TechnologyCombatProfile tl1 = BuildTl1Profile(baseline);
        IReadOnlyList<MirrorEvidence> mirrorEvidence = ReadMirrorEvidence(
            ResolveStudyRelativePath(studyPath, study.MirrorCalibrationEvidence),
            baseline.Sha256);
        IReadOnlyList<CrossFamilyEvidence> crossFamilyEvidence = ReadCrossFamilyEvidence(
            ResolveStudyRelativePath(studyPath, study.CrossFamilyCalibrationEvidence),
            baseline.Sha256);
        IReadOnlyDictionary<WeaponFamily, double> calibration =
            BuildFamilyCalibration(tl1, study.Ranges, mirrorEvidence);
        IReadOnlyDictionary<FamilyRangeKey, double> crossFamilyCalibration =
            BuildCrossFamilyCalibration(
                tl1,
                study.Ranges,
                calibration,
                crossFamilyEvidence);

        Console.WriteLine(
            $"Combat-scaling preflight: {study.Candidates.Count} TL2 candidates; " +
            $"Ranges {string.Join(", ", study.Ranges)}; {mirrorEvidence.Count} accepted " +
            $"TL1 mirror rows and {crossFamilyEvidence.Count} ordered-pair rows; " +
            "packet, protection, power, identity, and calibrated odds vectors; passed.");
        if (preflightOnly)
        {
            return 0;
        }

        var packetRows = new List<PacketTraceRow>();
        var breakpointRows = new List<ProtectionBreakpointRow>();
        var sameTlRows = new List<RangeComparisonRow>();
        var crossTlRows = new List<RangeComparisonRow>();
        var reviewRows = new List<CandidateReviewRow>();
        var profileRows = new List<ProfileRow> { ProfileRow.From(tl1) };
        var profiles = new List<TechnologyCombatProfile> { tl1 };

        foreach (Tl2CandidateDocument candidate in study.Candidates)
        {
            TechnologyCombatProfile profile = BuildCandidateProfile(candidate);
            profiles.Add(profile);
            profileRows.Add(ProfileRow.From(profile));
            packetRows.AddRange(BuildPacketTraces(profile));
            breakpointRows.AddRange(BuildBreakpoints(profile));
            sameTlRows.AddRange(BuildSameTlGrid(
                profile, study.Ranges, calibration, crossFamilyCalibration));
            IReadOnlyList<RangeComparisonRow> candidateCrossTl =
                BuildCrossTlGrid(
                    profile,
                    tl1,
                    study.Ranges,
                    calibration,
                    crossFamilyCalibration);
            crossTlRows.AddRange(candidateCrossTl);
            reviewRows.Add(BuildReview(
                candidate,
                profile,
                candidateCrossTl,
                study,
                calibration,
                crossFamilyCalibration));
        }
        packetRows.InsertRange(0, BuildPacketTraces(tl1));
        breakpointRows.InsertRange(0, BuildBreakpoints(tl1));

        IReadOnlyList<CalibrationRow> calibrationRows = BuildCalibrationRows(
            tl1,
            study.Ranges,
            mirrorEvidence,
            calibration);
        IReadOnlyList<CrossFamilyCalibrationRow> crossFamilyCalibrationRows =
            BuildCrossFamilyCalibrationRows(
                tl1,
                study.Ranges,
                calibration,
                crossFamilyEvidence,
                crossFamilyCalibration);
        IReadOnlyList<ScalingGate> gates = BuildGates(
            study,
            baseline,
            mirrorEvidence,
            crossFamilyEvidence,
            calibrationRows,
            crossFamilyCalibrationRows,
            reviewRows,
            profiles);
        WriteOutputs(
            study,
            baseline,
            calibration,
            crossFamilyCalibration,
            profileRows,
            calibrationRows,
            crossFamilyCalibrationRows,
            packetRows,
            breakpointRows,
            sameTlRows,
            crossTlRows,
            reviewRows,
            gates,
            outputDirectory);

        int failed = gates.Count(gate => !gate.Passed);
        foreach (CandidateReviewRow review in reviewRows)
        {
            Console.WriteLine(
                $"{(review.WithinTargetBand ? "PASS" : "REVIEW")} {review.CandidateId}: " +
                $"mean TL2-over-TL1 odds {review.MeanHigherTlWinPercent:F2}%, " +
                $"power margin {review.PowerMargin}, strongest same-TL edge " +
                $"{review.StrongestSameTlEdgePercent:F2}%, identity " +
                $"{(review.IdentityPassed ? "PASS" : "REVIEW")}.");
        }
        Console.WriteLine(
            $"Combat Scaling and TL2 Candidate Derivation: {study.Candidates.Count} " +
            $"candidates, {failed} failed gates. Output: " +
            Path.GetFullPath(outputDirectory));
        return failed == 0 ? 0 : 1;
    }

    private static void Validate(
        CombatScalingStudyDocument study,
        Tl1BaselineCatalog baseline)
    {
        if (!string.Equals(study.SchemaVersion, SchemaVersion, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Unexpected combat-scaling schema version.");
        }
        if (string.IsNullOrWhiteSpace(study.Id))
        {
            throw new InvalidOperationException("Combat-scaling study ID is required.");
        }
        if (!string.Equals(
                study.BaselineSha256,
                baseline.Sha256,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "Combat-scaling study baseline hash does not match the authoritative TL1 baseline.");
        }
        if (study.Ranges.Count != 4 ||
            !study.Ranges.SequenceEqual(new[] { 2, 3, 4, 5 }))
        {
            throw new InvalidOperationException(
                "Combat-scaling ranges must be exactly 2, 3, 4, and 5.");
        }
        if (study.Candidates.Count != 3)
        {
            throw new InvalidOperationException(
                "Combat-scaling study must contain exactly three TL2 candidates.");
        }
        if (study.Candidates.Select(item => item.Id)
            .Distinct(StringComparer.Ordinal).Count() != study.Candidates.Count)
        {
            throw new InvalidOperationException("TL2 candidate IDs must be unique.");
        }
        if (study.TargetHigherTlWinPercent <= 50.0 ||
            study.TargetHigherTlWinPercent >= 100.0 ||
            study.ReviewBandMinimumPercent <= 50.0 ||
            study.ReviewBandMaximumPercent >= 100.0 ||
            study.ReviewBandMinimumPercent >= study.ReviewBandMaximumPercent)
        {
            throw new InvalidOperationException("Invalid TL2 odds target or review band.");
        }
        if (string.IsNullOrWhiteSpace(study.MirrorCalibrationEvidence) ||
            string.IsNullOrWhiteSpace(study.CrossFamilyCalibrationEvidence) ||
            study.AggressiveControlThresholdPercent <= study.ReviewBandMaximumPercent ||
            study.IdentityGuardrails.MinimumMeaningfulDifferencesPerPair < 1 ||
            study.IdentityGuardrails.MaximumSharedCoreAttributesPerPair < 0 ||
            study.TierModel.WithinBandNominalHigherTlWinPercent <= 50.0 ||
            study.TierModel.BandBreakNominalHigherTlWinPercent <=
                study.TierModel.WithinBandNominalHigherTlWinPercent ||
            study.TierModel.BandBreakStressHigherTlWinPercent <
                study.TierModel.BandBreakNominalHigherTlWinPercent)
        {
            throw new InvalidOperationException(
                "Invalid evidence, identity guardrail, or tier-transition target.");
        }

        foreach (Tl2CandidateDocument candidate in study.Candidates)
        {
            ValidateCandidate(candidate);
        }
    }

    private static void ValidateCandidate(Tl2CandidateDocument candidate)
    {
        if (string.IsNullOrWhiteSpace(candidate.Id) ||
            string.IsNullOrWhiteSpace(candidate.Label) ||
            string.IsNullOrWhiteSpace(candidate.DesignThesis))
        {
            throw new InvalidOperationException(
                "Each TL2 candidate requires an ID, label, and design thesis.");
        }
        if (candidate.Defense.Hull <= 0 ||
            candidate.Defense.ArmorIntegrity < 0 ||
            candidate.Defense.ArmorProtection < 0 ||
            candidate.Defense.ShieldCapacity < 0 ||
            candidate.Defense.ShieldBaseRecharge < 0 ||
            candidate.Defense.ShieldArmor < 0)
        {
            throw new InvalidOperationException(
                $"Candidate '{candidate.Id}' contains invalid defensive values.");
        }
        if (candidate.PowerAndControl.ReactorOutput <= 0 ||
            candidate.PowerAndControl.TargetingBonus < 0 ||
            candidate.PowerAndControl.EffectivePdsChance < 0 ||
            candidate.PowerAndControl.EffectivePdsChance > 95 ||
            candidate.PowerAndControl.PdsPower < 0 ||
            candidate.PowerAndControl.StandardCombatPowerCommitment < 0)
        {
            throw new InvalidOperationException(
                $"Candidate '{candidate.Id}' contains invalid power/control values.");
        }
        if (candidate.Movement.ShipMove != 2 || candidate.Movement.MissileMove != 3)
        {
            throw new InvalidOperationException(
                $"Candidate '{candidate.Id}' must use TL2 ship Move 2 and missile Move 3.");
        }
        ValidateWeapon(candidate.Id, WeaponFamily.Kinetic, candidate.Weapons.Kinetic);
        ValidateWeapon(candidate.Id, WeaponFamily.Energy, candidate.Weapons.Energy);
        ValidateWeapon(candidate.Id, WeaponFamily.Missile, candidate.Weapons.Missile);

        string[] names =
        {
            candidate.ComponentNames.Hull,
            candidate.ComponentNames.Armor,
            candidate.ComponentNames.Shield,
            candidate.ComponentNames.Reactor,
            candidate.ComponentNames.Stl,
            candidate.ComponentNames.Sensors,
            candidate.ComponentNames.Computer,
            candidate.ComponentNames.Kinetic,
            candidate.ComponentNames.Energy,
            candidate.ComponentNames.Missile,
        };
        if (names.Any(string.IsNullOrWhiteSpace))
        {
            throw new InvalidOperationException(
                $"Candidate '{candidate.Id}' contains an empty component name.");
        }
    }

    private static void ValidateWeapon(
        string candidateId,
        WeaponFamily family,
        ScalingWeaponDocument weapon)
    {
        if (weapon.Damage <= 0 ||
            weapon.ShieldPenetration < 0 ||
            weapon.ArmorPenetration < 0 ||
            weapon.MaximumRange <= 0 ||
            weapon.PowerCost < 0 ||
            weapon.AccuracyBonus < 0 ||
            weapon.GuidanceChance < 0 ||
            weapon.GuidanceChance > 95 ||
            weapon.AmmunitionValue is < 0)
        {
            throw new InvalidOperationException(
                $"Candidate '{candidateId}' contains invalid {family} weapon values.");
        }
        if (family == WeaponFamily.Missile && weapon.GuidanceChance <= 0)
        {
            throw new InvalidOperationException(
                $"Candidate '{candidateId}' missile guidance chance must be positive.");
        }
    }

    private static TechnologyCombatProfile BuildTl1Profile(
        Tl1BaselineCatalog baseline) =>
        TechnologyCombatProfileCatalog.BuildTl1(baseline);

    private static TechnologyCombatProfile BuildCandidateProfile(
        Tl2CandidateDocument candidate) =>
        TechnologyCombatProfileCatalog.BuildCandidate(candidate);

    private static IReadOnlyList<MirrorEvidence> ReadMirrorEvidence(
        string path,
        string baselineSha256)
    {
        IReadOnlyList<IReadOnlyList<string>> rows = Tl1Csv.Read(path);
        if (rows.Count < 2)
        {
            throw new InvalidOperationException("TL1 calibration evidence contains no data.");
        }
        IReadOnlyList<string> header = rows[0];
        int hashIndex = Column(header, "baseline_sha256");
        int idIndex = Column(header, "source_variant_id");
        int familyIndex = Column(header, "family");
        int rangeIndex = Column(header, "range_hexes");
        int turnsIndex = Column(header, "mean_turns");
        int unresolvedIndex = Column(header, "unresolved_percent");
        var evidence = new List<MirrorEvidence>();
        foreach (IReadOnlyList<string> row in rows.Skip(1))
        {
            if (!string.Equals(row[hashIndex], baselineSha256, StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException(
                    $"Calibration evidence '{row[idIndex]}' uses a different TL1 baseline hash.");
            }
            evidence.Add(new MirrorEvidence(
                row[idIndex],
                ParseFamily(row[familyIndex]),
                ParseInt(row[rangeIndex], "range_hexes"),
                ParseDouble(row[turnsIndex], "mean_turns"),
                ParseDouble(row[unresolvedIndex], "unresolved_percent")));
        }
        return evidence.AsReadOnly();
    }

    private static IReadOnlyList<CrossFamilyEvidence> ReadCrossFamilyEvidence(
        string path,
        string baselineSha256)
    {
        IReadOnlyList<IReadOnlyList<string>> rows = Tl1Csv.Read(path);
        if (rows.Count < 2)
        {
            throw new InvalidOperationException(
                "TL1 cross-family calibration evidence contains no data.");
        }
        IReadOnlyList<string> header = rows[0];
        int hashIndex = Column(header, "baseline_sha256");
        int idIndex = Column(header, "source_variant_id");
        int sideAIndex = Column(header, "side_a_family");
        int sideBIndex = Column(header, "side_b_family");
        int rangeIndex = Column(header, "range_hexes");
        int sideAWinIndex = Column(header, "side_a_conditional_win_percent");
        int mutualIndex = Column(header, "mutual_percent");
        int unresolvedIndex = Column(header, "unresolved_percent");
        var evidence = new List<CrossFamilyEvidence>();
        foreach (IReadOnlyList<string> row in rows.Skip(1))
        {
            if (!string.Equals(
                    row[hashIndex],
                    baselineSha256,
                    StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException(
                    $"Cross-family evidence '{row[idIndex]}' uses a different " +
                    "TL1 baseline hash.");
            }
            evidence.Add(new CrossFamilyEvidence(
                row[idIndex],
                ParseFamily(row[sideAIndex]),
                ParseFamily(row[sideBIndex]),
                ParseInt(row[rangeIndex], "range_hexes"),
                ParseDouble(row[sideAWinIndex], "side_a_conditional_win_percent"),
                ParseDouble(row[mutualIndex], "mutual_percent"),
                ParseDouble(row[unresolvedIndex], "unresolved_percent")));
        }
        return evidence.AsReadOnly();
    }

    private static IReadOnlyDictionary<FamilyRangeKey, double>
        BuildCrossFamilyCalibration(
            TechnologyCombatProfile tl1,
            IReadOnlyList<int> ranges,
            IReadOnlyDictionary<WeaponFamily, double> familyCalibration,
            IReadOnlyList<CrossFamilyEvidence> evidence)
    {
        var result = new Dictionary<FamilyRangeKey, double>();
        foreach (CrossFamilyEvidence item in evidence.Where(item =>
            ranges.Contains(item.RangeHexes)))
        {
            var key = new FamilyRangeKey(
                item.SideAFamily, item.SideBFamily, item.RangeHexes);
            if (item.SideAFamily == item.SideBFamily)
            {
                result[key] = 1.0;
                continue;
            }
            double aKill = ExpectedKillTurns(
                tl1, tl1, item.SideAFamily, item.RangeHexes,
                familyCalibration[item.SideAFamily]);
            double bKill = ExpectedKillTurns(
                tl1, tl1, item.SideBFamily, item.RangeHexes,
                familyCalibration[item.SideBFamily]);
            double rawWin = RangeComparisonRow.WinPercent(aKill, bKill, 1.0);
            if (rawWin <= 0.0 || rawWin >= 100.0 ||
                item.SideAConditionalWinPercent <= 0.0 ||
                item.SideAConditionalWinPercent >= 100.0)
            {
                result[key] = 1.0;
                continue;
            }
            double rawOdds = rawWin / (100.0 - rawWin);
            double observedOdds = item.SideAConditionalWinPercent /
                (100.0 - item.SideAConditionalWinPercent);
            result[key] = observedOdds / rawOdds;
        }
        return result;
    }

    private static IReadOnlyList<CrossFamilyCalibrationRow>
        BuildCrossFamilyCalibrationRows(
            TechnologyCombatProfile tl1,
            IReadOnlyList<int> ranges,
            IReadOnlyDictionary<WeaponFamily, double> familyCalibration,
            IReadOnlyList<CrossFamilyEvidence> evidence,
            IReadOnlyDictionary<FamilyRangeKey, double> crossFamilyCalibration)
    {
        var rows = new List<CrossFamilyCalibrationRow>();
        foreach (CrossFamilyEvidence item in evidence.Where(item =>
            ranges.Contains(item.RangeHexes)))
        {
            double aKill = ExpectedKillTurns(
                tl1, tl1, item.SideAFamily, item.RangeHexes,
                familyCalibration[item.SideAFamily]);
            double bKill = ExpectedKillTurns(
                tl1, tl1, item.SideBFamily, item.RangeHexes,
                familyCalibration[item.SideBFamily]);
            var key = new FamilyRangeKey(
                item.SideAFamily, item.SideBFamily, item.RangeHexes);
            double multiplier = crossFamilyCalibration.TryGetValue(
                key, out double found) ? found : 1.0;
            double raw = RangeComparisonRow.WinPercent(aKill, bKill, 1.0);
            double calibrated = RangeComparisonRow.WinPercent(
                aKill, bKill, multiplier);
            rows.Add(new CrossFamilyCalibrationRow(
                item.SourceVariantId,
                item.SideAFamily,
                item.SideBFamily,
                item.RangeHexes,
                item.SideAConditionalWinPercent,
                raw,
                multiplier,
                calibrated,
                Math.Abs(calibrated - item.SideAConditionalWinPercent),
                item.MutualPercent,
                item.UnresolvedPercent));
        }
        return rows.AsReadOnly();
    }

    private static IReadOnlyDictionary<WeaponFamily, double> BuildFamilyCalibration(
        TechnologyCombatProfile tl1,
        IReadOnlyList<int> ranges,
        IReadOnlyList<MirrorEvidence> evidence)
    {
        var calibration = new Dictionary<WeaponFamily, double>();
        foreach (WeaponFamily family in Families)
        {
            var ratios = new List<double>();
            foreach (MirrorEvidence item in evidence.Where(item =>
                item.Family == family && item.UnresolvedPercent < 99.0 &&
                ranges.Contains(item.RangeHexes)))
            {
                double analytical = ExpectedKillTurns(
                    tl1,
                    tl1,
                    family,
                    item.RangeHexes,
                    calibrationFactor: 1.0);
                if (double.IsFinite(analytical) && analytical > 0.0)
                {
                    ratios.Add(item.MeanTurns / analytical);
                }
            }
            if (ratios.Count == 0)
            {
                throw new InvalidOperationException(
                    $"No usable TL1 calibration evidence exists for {family}.");
            }
            calibration.Add(family, ratios.Average());
        }
        return calibration;
    }

    private static IReadOnlyList<CalibrationRow> BuildCalibrationRows(
        TechnologyCombatProfile tl1,
        IReadOnlyList<int> ranges,
        IReadOnlyList<MirrorEvidence> evidence,
        IReadOnlyDictionary<WeaponFamily, double> calibration)
    {
        var rows = new List<CalibrationRow>();
        foreach (MirrorEvidence item in evidence.Where(item => ranges.Contains(item.RangeHexes)))
        {
            double raw = ExpectedKillTurns(
                tl1,
                tl1,
                item.Family,
                item.RangeHexes,
                calibrationFactor: 1.0);
            double calibrated = double.IsFinite(raw)
                ? raw * calibration[item.Family]
                : double.PositiveInfinity;
            double error = double.IsFinite(calibrated) && item.MeanTurns > 0.0
                ? Math.Abs(calibrated - item.MeanTurns) / item.MeanTurns * 100.0
                : item.UnresolvedPercent >= 99.0 && !double.IsFinite(calibrated)
                    ? 0.0
                    : 100.0;
            rows.Add(new CalibrationRow(
                item.SourceVariantId,
                item.Family,
                item.RangeHexes,
                item.MeanTurns,
                raw,
                calibration[item.Family],
                calibrated,
                error,
                item.UnresolvedPercent));
        }
        return rows.AsReadOnly();
    }

    private static IReadOnlyList<PacketTraceRow> BuildPacketTraces(
        TechnologyCombatProfile profile)
    {
        var rows = new List<PacketTraceRow>();
        foreach (WeaponFamily family in Families)
        {
            ScalingWeaponProfile weapon = profile.Weapon(family);
            DefenseState state = profile.PristineDefense;
            for (int packetNumber = 1; packetNumber <= 64 && state.Hull > 0; packetNumber++)
            {
                DefenseState recharged = state with
                {
                    Shield = Math.Min(
                        profile.ShieldCapacity,
                        state.Shield + profile.ShieldBaseRecharge),
                };
                DamageStep step = ResolveDamage(profile, recharged, weapon);
                rows.Add(new PacketTraceRow(
                    profile.Id,
                    family,
                    packetNumber,
                    recharged.Shield,
                    recharged.ArmorIntegrity,
                    recharged.ArmorProtection,
                    recharged.Hull,
                    step.Resolution.ShieldBypass,
                    step.Resolution.ShieldAbsorption,
                    step.Resolution.ShieldArmorPrevented,
                    step.Resolution.ArmorLayers.Sum(item => item.DamagePrevented),
                    step.Resolution.ArmorLayers.Sum(item => item.IntegrityDamage),
                    step.Resolution.ArmorLayers.Sum(item => item.ProtectionDamage),
                    step.Resolution.HullDamage,
                    step.State.Shield,
                    step.State.ArmorIntegrity,
                    step.State.ArmorProtection,
                    step.State.Hull));
                if (step.State.Equals(recharged))
                {
                    break;
                }
                state = step.State;
            }
        }
        return rows.AsReadOnly();
    }

    private static IReadOnlyList<ProtectionBreakpointRow> BuildBreakpoints(
        TechnologyCombatProfile profile)
    {
        var rows = new List<ProtectionBreakpointRow>();
        foreach (WeaponFamily family in Families)
        {
            ScalingWeaponProfile weapon = profile.Weapon(family);
            for (int protection = 0; protection <= weapon.Damage + 1; protection++)
            {
                rows.Add(new ProtectionBreakpointRow(
                    profile.Id,
                    family,
                    "armor",
                    protection,
                    weapon.ArmorPenetration,
                    Math.Max(0, protection - weapon.ArmorPenetration),
                    Math.Max(0, weapon.Damage - Math.Max(
                        0,
                        protection - weapon.ArmorPenetration))));
                rows.Add(new ProtectionBreakpointRow(
                    profile.Id,
                    family,
                    "shield",
                    protection,
                    weapon.ShieldPenetration,
                    protection,
                    Math.Max(
                        0,
                        weapon.Damage - weapon.ShieldPenetration - protection) +
                    Math.Min(weapon.Damage, weapon.ShieldPenetration)));
            }
        }
        return rows.AsReadOnly();
    }

    private static IReadOnlyList<RangeComparisonRow> BuildSameTlGrid(
        TechnologyCombatProfile profile,
        IReadOnlyList<int> ranges,
        IReadOnlyDictionary<WeaponFamily, double> calibration,
        IReadOnlyDictionary<FamilyRangeKey, double> crossFamilyCalibration)
    {
        var rows = new List<RangeComparisonRow>();
        foreach (int range in ranges)
        {
            foreach (WeaponFamily sideA in Families)
            {
                foreach (WeaponFamily sideB in Families)
                {
                    double aKill = ExpectedKillTurns(
                        profile,
                        profile,
                        sideA,
                        range,
                        calibration[sideA]);
                    double bKill = ExpectedKillTurns(
                        profile,
                        profile,
                        sideB,
                        range,
                        calibration[sideB]);
                    rows.Add(RangeComparisonRow.Create(
                        "same-tl",
                        profile.Id,
                        profile.Id,
                        sideA,
                        sideB,
                        range,
                        aKill,
                        bKill,
                        crossFamilyCalibration.TryGetValue(
                            new FamilyRangeKey(sideA, sideB, range),
                            out double multiplier) ? multiplier : 1.0));
                }
            }
        }
        return rows.AsReadOnly();
    }

    private static IReadOnlyList<RangeComparisonRow> BuildCrossTlGrid(
        TechnologyCombatProfile higher,
        TechnologyCombatProfile lower,
        IReadOnlyList<int> ranges,
        IReadOnlyDictionary<WeaponFamily, double> calibration,
        IReadOnlyDictionary<FamilyRangeKey, double> crossFamilyCalibration)
    {
        var rows = new List<RangeComparisonRow>();
        foreach (int range in ranges)
        {
            foreach (WeaponFamily higherFamily in Families)
            {
                foreach (WeaponFamily lowerFamily in Families)
                {
                    double higherKill = ExpectedKillTurns(
                        higher,
                        lower,
                        higherFamily,
                        range,
                        calibration[higherFamily]);
                    double lowerKill = ExpectedKillTurns(
                        lower,
                        higher,
                        lowerFamily,
                        range,
                        calibration[lowerFamily]);
                    double multiplier = crossFamilyCalibration.TryGetValue(
                        new FamilyRangeKey(higherFamily, lowerFamily, range),
                        out double found) ? found : 1.0;
                    rows.Add(RangeComparisonRow.Create(
                        "cross-tl-ordered-family",
                        higher.Id,
                        lower.Id,
                        higherFamily,
                        lowerFamily,
                        range,
                        higherKill,
                        lowerKill,
                        multiplier));
                }
            }
        }
        return rows.AsReadOnly();
    }

    private static CandidateReviewRow BuildReview(
        Tl2CandidateDocument candidate,
        TechnologyCombatProfile profile,
        IReadOnlyList<RangeComparisonRow> crossTlRows,
        CombatScalingStudyDocument study,
        IReadOnlyDictionary<WeaponFamily, double> calibration,
        IReadOnlyDictionary<FamilyRangeKey, double> crossFamilyCalibration)
    {
        double[] validShares = crossTlRows
            .Where(row => row.BothSidesCanAttack)
            .Select(row => row.SideAWinPercent)
            .ToArray();
        double meanShare = validShares.Length == 0 ? 0.0 : validShares.Average();
        IReadOnlyList<RangeComparisonRow> sameTl = BuildSameTlGrid(
            profile,
            study.Ranges,
            calibration,
            crossFamilyCalibration);
        double strongestEdge = sameTl
            .Where(row => row.SideAFamily != row.SideBFamily && row.BothSidesCanAttack)
            .Select(row => Math.Max(row.SideAWinPercent, row.SideBWinPercent))
            .DefaultIfEmpty(50.0)
            .Max();
        int powerMargin = profile.ReactorOutput - profile.StandardCombatPowerCommitment;
        CandidateIdentityReview identity = BuildIdentityReview(
            candidate, profile, study.IdentityGuardrails);
        return new CandidateReviewRow(
            candidate.Id,
            candidate.Label,
            candidate.Status,
            meanShare,
            meanShare - study.TargetHigherTlWinPercent,
            meanShare >= study.ReviewBandMinimumPercent &&
                meanShare <= study.ReviewBandMaximumPercent,
            candidate.Status.Contains(
                "aggressive", StringComparison.OrdinalIgnoreCase) ||
                meanShare >= study.AggressiveControlThresholdPercent,
            strongestEdge,
            powerMargin,
            identity.Passed,
            identity.MinimumMeaningfulDifferences,
            identity.MaximumSharedCoreAttributes,
            string.Join("; ", identity.Warnings),
            candidate.DesignThesis,
            string.Join("; ", candidate.NamingReview));
    }

    private static CandidateIdentityReview BuildIdentityReview(
        Tl2CandidateDocument candidate,
        TechnologyCombatProfile profile,
        IdentityGuardrailsDocument guardrails)
    {
        var warnings = new List<string>();
        int minimumDifferences = int.MaxValue;
        int maximumSharedCore = 0;
        foreach ((WeaponFamily left, WeaponFamily right) in new[]
        {
            (WeaponFamily.Kinetic, WeaponFamily.Energy),
            (WeaponFamily.Kinetic, WeaponFamily.Missile),
            (WeaponFamily.Energy, WeaponFamily.Missile),
        })
        {
            ScalingWeaponProfile a = profile.Weapon(left);
            ScalingWeaponProfile b = profile.Weapon(right);
            int sharedCore = 0;
            if (a.Damage == b.Damage) sharedCore++;
            int aControl = left == WeaponFamily.Missile ? a.GuidanceChance : a.AccuracyBonus;
            int bControl = right == WeaponFamily.Missile ? b.GuidanceChance : b.AccuracyBonus;
            if (aControl == bControl) sharedCore++;
            if (a.MaximumRange == b.MaximumRange) sharedCore++;
            int differences = 0;
            if (a.Damage != b.Damage) differences++;
            if (aControl != bControl) differences++;
            if (a.MaximumRange != b.MaximumRange) differences++;
            if (a.ShieldPenetration != b.ShieldPenetration) differences++;
            if (a.ArmorPenetration != b.ArmorPenetration) differences++;
            if (a.PowerCost != b.PowerCost) differences++;
            if (a.Ammunition.HasValue != b.Ammunition.HasValue) differences++;
            minimumDifferences = Math.Min(minimumDifferences, differences);
            maximumSharedCore = Math.Max(maximumSharedCore, sharedCore);
            if (differences < guardrails.MinimumMeaningfulDifferencesPerPair)
            {
                warnings.Add(
                    $"{left}/{right} has only {differences} meaningful vector differences.");
            }
            if (sharedCore > guardrails.MaximumSharedCoreAttributesPerPair)
            {
                warnings.Add(
                    $"{left}/{right} shares {sharedCore} core combat attributes.");
            }
        }
        if (profile.Kinetic.Damage <= profile.Energy.Damage &&
            profile.Kinetic.PowerCost >= profile.Energy.PowerCost)
        {
            warnings.Add(
                "Kinetic lacks both a raw-packet and power-cost advantage over energy.");
        }
        if (profile.Energy.AccuracyBonus <= profile.Kinetic.AccuracyBonus &&
            profile.Energy.MaximumRange <= profile.Kinetic.MaximumRange)
        {
            warnings.Add(
                "Energy lacks both an accuracy and range advantage over kinetic.");
        }
        if (profile.Missile.Damage <= Math.Max(
                profile.Kinetic.Damage, profile.Energy.Damage))
        {
            warnings.Add(
                "Missile terminal damage is not greater than both direct-fire packets.");
        }
        if (minimumDifferences == int.MaxValue) minimumDifferences = 0;
        return new CandidateIdentityReview(
            warnings.Count == 0,
            minimumDifferences,
            maximumSharedCore,
            warnings.AsReadOnly());
    }

    private static double ExpectedKillTurns(
        TechnologyCombatProfile attacker,
        TechnologyCombatProfile defender,
        WeaponFamily family,
        int range,
        double calibrationFactor)
    {
        ScalingWeaponProfile weapon = attacker.Weapon(family);
        if (range > weapon.MaximumRange)
        {
            return double.PositiveInfinity;
        }
        double hitProbability;
        int flightDelay = 0;
        if (family == WeaponFamily.Missile)
        {
            hitProbability = weapon.GuidanceChance / 100.0 *
                (1.0 - defender.EffectivePdsChance / 100.0);
            flightDelay = Math.Max(
                0,
                (int)Math.Ceiling(range / (double)attacker.MissileMove) - 1);
        }
        else
        {
            int chance = Math.Clamp(
                50 + weapon.AccuracyBonus + attacker.TargetingBonus - 5 * range,
                5,
                95);
            hitProbability = chance / 100.0;
        }
        if (hitProbability <= 0.0)
        {
            return double.PositiveInfinity;
        }
        double stateTurns = SolveExpectedAbsorptionTurns(
            defender,
            weapon,
            hitProbability);
        return double.IsFinite(stateTurns)
            ? (stateTurns + flightDelay) * calibrationFactor
            : double.PositiveInfinity;
    }

    private static double SolveExpectedAbsorptionTurns(
        TechnologyCombatProfile defender,
        ScalingWeaponProfile weapon,
        double hitProbability)
    {
        DefenseState initial = defender.PristineDefense;
        var states = new List<DefenseState>();
        var indices = new Dictionary<DefenseState, int>();
        var queue = new Queue<DefenseState>();
        void Add(DefenseState state)
        {
            if (state.Hull == 0 || indices.ContainsKey(state))
            {
                return;
            }
            indices.Add(state, states.Count);
            states.Add(state);
            queue.Enqueue(state);
        }
        Add(initial);
        while (queue.Count > 0)
        {
            DefenseState state = queue.Dequeue();
            DefenseState recharged = state with
            {
                Shield = Math.Min(
                    defender.ShieldCapacity,
                    state.Shield + defender.ShieldBaseRecharge),
            };
            DefenseState hit = ResolveDamage(defender, recharged, weapon).State;
            if (hit.Equals(recharged))
            {
                return double.PositiveInfinity;
            }
            Add(recharged);
            Add(hit);
        }

        int count = states.Count;
        var matrix = new double[count, count + 1];
        for (int row = 0; row < count; row++)
        {
            DefenseState state = states[row];
            DefenseState recharged = state with
            {
                Shield = Math.Min(
                    defender.ShieldCapacity,
                    state.Shield + defender.ShieldBaseRecharge),
            };
            DefenseState hit = ResolveDamage(defender, recharged, weapon).State;
            matrix[row, row] = 1.0;
            if (recharged.Hull > 0)
            {
                matrix[row, indices[recharged]] -= 1.0 - hitProbability;
            }
            if (hit.Hull > 0)
            {
                matrix[row, indices[hit]] -= hitProbability;
            }
            matrix[row, count] = 1.0;
        }
        double[] solution = SolveLinearSystem(matrix);
        return solution[indices[initial]];
    }

    private static double[] SolveLinearSystem(double[,] augmented)
    {
        int count = augmented.GetLength(0);
        for (int column = 0; column < count; column++)
        {
            int pivot = column;
            double pivotMagnitude = Math.Abs(augmented[pivot, column]);
            for (int row = column + 1; row < count; row++)
            {
                double magnitude = Math.Abs(augmented[row, column]);
                if (magnitude > pivotMagnitude)
                {
                    pivot = row;
                    pivotMagnitude = magnitude;
                }
            }
            if (pivotMagnitude < 1e-12)
            {
                return Enumerable.Repeat(double.PositiveInfinity, count).ToArray();
            }
            if (pivot != column)
            {
                for (int index = column; index <= count; index++)
                {
                    double temporary = augmented[column, index];
                    augmented[column, index] = augmented[pivot, index];
                    augmented[pivot, index] = temporary;
                }
            }
            double divisor = augmented[column, column];
            for (int index = column; index <= count; index++)
            {
                augmented[column, index] /= divisor;
            }
            for (int row = 0; row < count; row++)
            {
                if (row == column)
                {
                    continue;
                }
                double factor = augmented[row, column];
                if (Math.Abs(factor) < 1e-15)
                {
                    continue;
                }
                for (int index = column; index <= count; index++)
                {
                    augmented[row, index] -= factor * augmented[column, index];
                }
            }
        }
        var result = new double[count];
        for (int row = 0; row < count; row++)
        {
            result[row] = augmented[row, count];
        }
        return result;
    }

    private static DamageStep ResolveDamage(
        TechnologyCombatProfile defender,
        DefenseState state,
        ScalingWeaponProfile weapon)
    {
        var defense = new LayeredDefenseState(
            defender.ShieldCapacity,
            state.Shield,
            defender.ShieldArmor,
            new[]
            {
                new ArmorLayerState(
                    "primary",
                    defender.ArmorProtection,
                    state.ArmorProtection,
                    defender.ArmorIntegrity,
                    state.ArmorIntegrity),
            },
            defender.Hull,
            state.Hull);
        LayeredDamageResolution resolution = LayeredDamageResolver.Resolve(
            defense,
            new AttackPacket(
                weapon.Damage,
                weapon.ShieldPenetration,
                weapon.ArmorPenetration));
        ArmorLayerState armor = defense.ArmorLayers[0];
        return new DamageStep(
            new DefenseState(
                defense.CurrentShieldCapacity,
                armor.CurrentIntegrity,
                armor.CurrentProtection,
                defense.CurrentHull),
            resolution);
    }

    private static IReadOnlyList<ScalingGate> BuildGates(
        CombatScalingStudyDocument study,
        Tl1BaselineCatalog baseline,
        IReadOnlyList<MirrorEvidence> mirrorEvidence,
        IReadOnlyList<CrossFamilyEvidence> crossFamilyEvidence,
        IReadOnlyList<CalibrationRow> calibration,
        IReadOnlyList<CrossFamilyCalibrationRow> crossFamilyCalibration,
        IReadOnlyList<CandidateReviewRow> reviews,
        IReadOnlyList<TechnologyCombatProfile> profiles)
    {
        CandidateReviewRow recommended = reviews.Single(row =>
            row.CandidateId == "tl2-identity-preserving-refinement");
        return new[]
        {
            Gate("baseline-hash", string.Equals(study.BaselineSha256, baseline.Sha256, StringComparison.OrdinalIgnoreCase), baseline.Sha256),
            Gate("tl1-mirror-evidence-coverage", mirrorEvidence.Count == 12, $"{mirrorEvidence.Count} mirror rows"),
            Gate("tl1-cross-family-evidence-coverage", crossFamilyEvidence.Count == 36, $"{crossFamilyEvidence.Count} ordered-pair rows"),
            Gate("tl1-calibration-error", calibration.Where(row => row.UnresolvedPercent < 99.0).All(row => row.AbsoluteErrorPercent <= 12.0), $"max {calibration.Where(row => row.UnresolvedPercent < 99.0).Max(row => row.AbsoluteErrorPercent):F2}%"),
            Gate("three-candidate-screen", study.Candidates.Count == 3, $"{study.Candidates.Count} candidates"),
            Gate("cross-family-calibration-finite", crossFamilyCalibration.All(row => double.IsFinite(row.OddsMultiplier) && row.OddsMultiplier > 0.0), $"{crossFamilyCalibration.Count} rows"),
            Gate("range-grid", study.Ranges.SequenceEqual(new[] { 2, 3, 4, 5 }), string.Join(",", study.Ranges)),
            Gate("low-tech-tier", study.TierModel.LowTech.SequenceEqual(new[] { 1, 2, 3 }), string.Join(",", study.TierModel.LowTech)),
            Gate("tl2-movement-law", profiles.Where(item => item.TechnologyLevel == 2).All(item => item.ShipMove == 2 && item.MissileMove == 3), "ship 2 / missile 3"),
            Gate("tl2-armor-ap0", profiles.Where(item => item.TechnologyLevel == 2).All(item => item.ArmorProtection == 0), "all candidate AP 0"),
            Gate("candidate-power-margin", reviews.All(item => item.PowerMargin >= 1), $"minimum {reviews.Min(item => item.PowerMargin)}"),
            Gate("recommended-odds-band", recommended.WithinTargetBand, $"{recommended.MeanHigherTlWinPercent:F2}% in {study.ReviewBandMinimumPercent:F1}-{study.ReviewBandMaximumPercent:F1}%"),
            Gate("recommended-target-distance", Math.Abs(recommended.TargetDeltaPercentagePoints) <= 2.0, $"delta {recommended.TargetDeltaPercentagePoints:F2} points"),
            Gate("recommended-identity", !study.IdentityGuardrails.RecommendedCandidateMustPass || recommended.IdentityPassed, recommended.IdentityWarnings),
            Gate("aggressive-control-retained", reviews.Any(row => row.IsAggressiveControl), $"threshold {study.AggressiveControlThresholdPercent:F1}%"),
            Gate("naming-review-preserved", study.Candidates.Any(item => item.NamingReview.Count > 0), "provisional naming concerns recorded"),
        };
    }

    private static ScalingGate Gate(string id, bool passed, string details) =>
        new(id, passed, details);

    private static void WriteOutputs(
        CombatScalingStudyDocument study,
        Tl1BaselineCatalog baseline,
        IReadOnlyDictionary<WeaponFamily, double> calibration,
        IReadOnlyDictionary<FamilyRangeKey, double> crossFamilyCalibration,
        IReadOnlyList<ProfileRow> profiles,
        IReadOnlyList<CalibrationRow> calibrationRows,
        IReadOnlyList<CrossFamilyCalibrationRow> crossFamilyCalibrationRows,
        IReadOnlyList<PacketTraceRow> packetRows,
        IReadOnlyList<ProtectionBreakpointRow> breakpointRows,
        IReadOnlyList<RangeComparisonRow> sameTlRows,
        IReadOnlyList<RangeComparisonRow> crossTlRows,
        IReadOnlyList<CandidateReviewRow> reviewRows,
        IReadOnlyList<ScalingGate> gates,
        string outputDirectory)
    {
        Directory.CreateDirectory(outputDirectory);
        var summary = new
        {
            schemaVersion = SchemaVersion,
            studyId = study.Id,
            baselineSha256 = baseline.Sha256,
            baselineParameterCount = baseline.Count,
            targetHigherTlWinPercent = study.TargetHigherTlWinPercent,
            reviewBandMinimumPercent = study.ReviewBandMinimumPercent,
            reviewBandMaximumPercent = study.ReviewBandMaximumPercent,
            aggressiveControlThresholdPercent = study.AggressiveControlThresholdPercent,
            tierTransitionTargets = new
            {
                withinBand = study.TierModel.WithinBandNominalHigherTlWinPercent,
                bandBreak = study.TierModel.BandBreakNominalHigherTlWinPercent,
                bandBreakStress = study.TierModel.BandBreakStressHigherTlWinPercent,
            },
            identityGuardrails = study.IdentityGuardrails,
            familyCalibration = calibration.ToDictionary(
                item => item.Key.ToString(),
                item => item.Value),
            crossFamilyOddsCalibration = crossFamilyCalibration.ToDictionary(
                item => item.Key.ToString(),
                item => item.Value),
            candidates = reviewRows,
            gates,
            passed = gates.All(gate => gate.Passed),
        };
        WriteJson(Path.Combine(outputDirectory, "summary.json"), summary);
        WriteCsv(Path.Combine(outputDirectory, "profiles.csv"), ProfileRow.Header, profiles.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "tl1-calibration.csv"), CalibrationRow.Header, calibrationRows.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "tl1-cross-family-calibration.csv"), CrossFamilyCalibrationRow.Header, crossFamilyCalibrationRows.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "packet-traces.csv"), PacketTraceRow.Header, packetRows.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "protection-breakpoints.csv"), ProtectionBreakpointRow.Header, breakpointRows.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "same-tl-range-grid.csv"), RangeComparisonRow.Header, sameTlRows.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "cross-tl-range-grid.csv"), RangeComparisonRow.Header, crossTlRows.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "candidate-review.csv"), CandidateReviewRow.Header, reviewRows.Select(item => item.Cells));
        WriteCsv(Path.Combine(outputDirectory, "gates.csv"), ScalingGate.Header, gates.Select(item => item.Cells));

        string[] resultFiles = Directory.GetFiles(outputDirectory)
            .Where(path => !path.EndsWith("result.sha256.txt", StringComparison.OrdinalIgnoreCase))
            .OrderBy(path => path, StringComparer.Ordinal)
            .ToArray();
        using var incremental = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (string path in resultFiles)
        {
            byte[] name = Encoding.UTF8.GetBytes(Path.GetFileName(path) + "\n");
            incremental.AppendData(name);
            incremental.AppendData(File.ReadAllBytes(path));
        }
        File.WriteAllText(
            Path.Combine(outputDirectory, "result.sha256.txt"),
            Convert.ToHexString(incremental.GetHashAndReset()).ToLowerInvariant() +
            Environment.NewLine);
    }

    private static void WriteJson(string path, object value) =>
        File.WriteAllText(
            path,
            JsonSerializer.Serialize(value, new JsonSerializerOptions
            {
                WriteIndented = true,
                Converters = { new JsonStringEnumConverter() },
            }) + Environment.NewLine);

    private static void WriteCsv(
        string path,
        IReadOnlyList<string> header,
        IEnumerable<IReadOnlyList<string>> rows)
    {
        var builder = new StringBuilder();
        builder.AppendLine(string.Join(",", header.Select(EscapeCsv)));
        foreach (IReadOnlyList<string> row in rows)
        {
            builder.AppendLine(string.Join(",", row.Select(EscapeCsv)));
        }
        File.WriteAllText(path, builder.ToString(), Encoding.UTF8);
    }

    private static string EscapeCsv(string value)
    {
        if (!value.Contains(',') && !value.Contains('"') &&
            !value.Contains('\r') && !value.Contains('\n'))
        {
            return value;
        }
        return '"' + value.Replace("\"", "\"\"") + '"';
    }

    private static JsonSerializerOptions JsonOptions() => new()
    {
        PropertyNameCaseInsensitive = false,
        Converters = { new JsonStringEnumConverter() },
    };

    private static string ResolveStudyRelativePath(string studyPath, string value)
    {
        if (Path.IsPathRooted(value))
        {
            return value;
        }
        string repositoryRoot = FindRepositoryRoot(Path.GetFullPath(studyPath));
        return Path.GetFullPath(Path.Combine(repositoryRoot, value));
    }

    private static string FindRepositoryRoot(string startPath)
    {
        DirectoryInfo? directory = new FileInfo(startPath).Directory;
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "StarCluster.Calibration.sln")))
            {
                return directory.FullName;
            }
            directory = directory.Parent;
        }
        throw new InvalidOperationException("Repository root could not be located.");
    }

    private static int Column(IReadOnlyList<string> header, string name)
    {
        for (int index = 0; index < header.Count; index++)
        {
            if (string.Equals(header[index], name, StringComparison.Ordinal))
            {
                return index;
            }
        }
        throw new InvalidOperationException($"CSV column '{name}' was not found.");
    }

    private static int ParseInt(string value, string label) =>
        int.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out int parsed)
            ? parsed
            : throw new InvalidOperationException($"{label} is not an integer: '{value}'.");

    private static double ParseDouble(string value, string label) =>
        double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out double parsed)
            ? parsed
            : throw new InvalidOperationException($"{label} is not numeric: '{value}'.");

    private static WeaponFamily ParseFamily(string value) => value switch
    {
        "Kinetic" => WeaponFamily.Kinetic,
        "Energy" => WeaponFamily.Energy,
        "Missile" => WeaponFamily.Missile,
        _ => throw new InvalidOperationException($"Unknown weapon family '{value}'."),
    };
}

public sealed class CombatScalingStudyDocument
{
    [JsonPropertyName("schemaVersion")]
    public string SchemaVersion { get; set; } = string.Empty;

    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("baselineSha256")]
    public string BaselineSha256 { get; set; } = string.Empty;

    [JsonPropertyName("mirrorCalibrationEvidence")]
    public string MirrorCalibrationEvidence { get; set; } = string.Empty;

    [JsonPropertyName("crossFamilyCalibrationEvidence")]
    public string CrossFamilyCalibrationEvidence { get; set; } = string.Empty;

    [JsonPropertyName("targetHigherTlWinPercent")]
    public double TargetHigherTlWinPercent { get; set; }

    [JsonPropertyName("reviewBandMinimumPercent")]
    public double ReviewBandMinimumPercent { get; set; }

    [JsonPropertyName("reviewBandMaximumPercent")]
    public double ReviewBandMaximumPercent { get; set; }

    [JsonPropertyName("aggressiveControlThresholdPercent")]
    public double AggressiveControlThresholdPercent { get; set; }

    [JsonPropertyName("ranges")]
    public List<int> Ranges { get; set; } = new();

    [JsonPropertyName("tierModel")]
    public TechnologyTierModelDocument TierModel { get; set; } = new();

    [JsonPropertyName("identityGuardrails")]
    public IdentityGuardrailsDocument IdentityGuardrails { get; set; } = new();

    [JsonPropertyName("tl1AnalyticalAssumptions")]
    public Tl1AnalyticalAssumptionsDocument Tl1AnalyticalAssumptions { get; set; } = new();

    [JsonPropertyName("candidates")]
    public List<Tl2CandidateDocument> Candidates { get; set; } = new();
}

public sealed class TechnologyTierModelDocument
{
    [JsonPropertyName("lowTech")]
    public List<int> LowTech { get; set; } = new();

    [JsonPropertyName("mediumTech")]
    public List<int> MediumTech { get; set; } = new();

    [JsonPropertyName("highTech")]
    public List<int> HighTech { get; set; } = new();

    [JsonPropertyName("progressionRhythm")]
    public string ProgressionRhythm { get; set; } = string.Empty;

    [JsonPropertyName("withinBandNominalHigherTlWinPercent")]
    public double WithinBandNominalHigherTlWinPercent { get; set; }

    [JsonPropertyName("bandBreakNominalHigherTlWinPercent")]
    public double BandBreakNominalHigherTlWinPercent { get; set; }

    [JsonPropertyName("bandBreakStressHigherTlWinPercent")]
    public double BandBreakStressHigherTlWinPercent { get; set; }
}

public sealed class IdentityGuardrailsDocument
{
    [JsonPropertyName("minimumMeaningfulDifferencesPerPair")]
    public int MinimumMeaningfulDifferencesPerPair { get; set; }

    [JsonPropertyName("maximumSharedCoreAttributesPerPair")]
    public int MaximumSharedCoreAttributesPerPair { get; set; }

    [JsonPropertyName("coreAttributes")]
    public List<string> CoreAttributes { get; set; } = new();

    [JsonPropertyName("supportAttributes")]
    public List<string> SupportAttributes { get; set; } = new();

    [JsonPropertyName("recommendedCandidateMustPass")]
    public bool RecommendedCandidateMustPass { get; set; }

    [JsonPropertyName("reviewOnlyForControls")]
    public bool ReviewOnlyForControls { get; set; }
}

public sealed class Tl1AnalyticalAssumptionsDocument
{
    [JsonPropertyName("effectivePdsChanceFormula")]
    public string EffectivePdsChanceFormula { get; set; } = string.Empty;

    [JsonPropertyName("missileLaunchCadenceTurns")]
    public int MissileLaunchCadenceTurns { get; set; }

    [JsonPropertyName("directFireCadenceTurns")]
    public int DirectFireCadenceTurns { get; set; }

    [JsonPropertyName("shieldRechargeTiming")]
    public string ShieldRechargeTiming { get; set; } = string.Empty;

    [JsonPropertyName("simultaneousRaceModel")]
    public string SimultaneousRaceModel { get; set; } = string.Empty;
}

public sealed class Tl2CandidateDocument
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("label")]
    public string Label { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("designThesis")]
    public string DesignThesis { get; set; } = string.Empty;

    [JsonPropertyName("componentNames")]
    public CandidateComponentNamesDocument ComponentNames { get; set; } = new();

    [JsonPropertyName("defense")]
    public CandidateDefenseDocument Defense { get; set; } = new();

    [JsonPropertyName("powerAndControl")]
    public CandidatePowerAndControlDocument PowerAndControl { get; set; } = new();

    [JsonPropertyName("movement")]
    public CandidateMovementDocument Movement { get; set; } = new();

    [JsonPropertyName("weapons")]
    public CandidateWeaponsDocument Weapons { get; set; } = new();

    [JsonPropertyName("referenceInfluences")]
    public List<string> ReferenceInfluences { get; set; } = new();

    [JsonPropertyName("namingReview")]
    public List<string> NamingReview { get; set; } = new();
}

public sealed class CandidateComponentNamesDocument
{
    [JsonPropertyName("hull")] public string Hull { get; set; } = string.Empty;
    [JsonPropertyName("armor")] public string Armor { get; set; } = string.Empty;
    [JsonPropertyName("shield")] public string Shield { get; set; } = string.Empty;
    [JsonPropertyName("reactor")] public string Reactor { get; set; } = string.Empty;
    [JsonPropertyName("stl")] public string Stl { get; set; } = string.Empty;
    [JsonPropertyName("sensors")] public string Sensors { get; set; } = string.Empty;
    [JsonPropertyName("computer")] public string Computer { get; set; } = string.Empty;
    [JsonPropertyName("kinetic")] public string Kinetic { get; set; } = string.Empty;
    [JsonPropertyName("energy")] public string Energy { get; set; } = string.Empty;
    [JsonPropertyName("missile")] public string Missile { get; set; } = string.Empty;
}

public sealed class CandidateDefenseDocument
{
    [JsonPropertyName("hull")] public int Hull { get; set; }
    [JsonPropertyName("armorIntegrity")] public int ArmorIntegrity { get; set; }
    [JsonPropertyName("armorProtection")] public int ArmorProtection { get; set; }
    [JsonPropertyName("shieldCapacity")] public int ShieldCapacity { get; set; }
    [JsonPropertyName("shieldBaseRecharge")] public int ShieldBaseRecharge { get; set; }
    [JsonPropertyName("shieldArmor")] public int ShieldArmor { get; set; }
}

public sealed class CandidatePowerAndControlDocument
{
    [JsonPropertyName("reactorOutput")] public int ReactorOutput { get; set; }
    [JsonPropertyName("targetingBonus")] public int TargetingBonus { get; set; }
    [JsonPropertyName("effectivePdsChance")] public int EffectivePdsChance { get; set; }
    [JsonPropertyName("pdsPower")] public int PdsPower { get; set; }
    [JsonPropertyName("standardCombatPowerCommitment")] public int StandardCombatPowerCommitment { get; set; }
}

public sealed class CandidateMovementDocument
{
    [JsonPropertyName("shipMove")] public int ShipMove { get; set; }
    [JsonPropertyName("missileMove")] public int MissileMove { get; set; }
}

public sealed class CandidateWeaponsDocument
{
    [JsonPropertyName("kinetic")] public ScalingWeaponDocument Kinetic { get; set; } = new();
    [JsonPropertyName("energy")] public ScalingWeaponDocument Energy { get; set; } = new();
    [JsonPropertyName("missile")] public ScalingWeaponDocument Missile { get; set; } = new();
}

public sealed class ScalingWeaponDocument
{
    [JsonPropertyName("damage")] public int Damage { get; set; }
    [JsonPropertyName("shieldPenetration")] public int ShieldPenetration { get; set; }
    [JsonPropertyName("armorPenetration")] public int ArmorPenetration { get; set; }
    [JsonPropertyName("accuracyBonus")] public int AccuracyBonus { get; set; }
    [JsonPropertyName("guidanceChance")] public int GuidanceChance { get; set; }
    [JsonPropertyName("maximumRange")] public int MaximumRange { get; set; }
    [JsonPropertyName("powerCost")] public int PowerCost { get; set; }
    [JsonPropertyName("ammunition")] public int? AmmunitionValue { get; set; }
    [JsonIgnore] public int Ammunition => AmmunitionValue ?? -1;
}

internal sealed record TechnologyCombatProfile(
    string Id,
    string Label,
    int TechnologyLevel,
    int Hull,
    int ArmorIntegrity,
    int ArmorProtection,
    int ShieldCapacity,
    int ShieldBaseRecharge,
    int ShieldArmor,
    int ReactorOutput,
    int TargetingBonus,
    int EffectivePdsChance,
    int PdsPower,
    int StandardCombatPowerCommitment,
    int ShipMove,
    int MissileMove,
    ScalingWeaponProfile Kinetic,
    ScalingWeaponProfile Energy,
    ScalingWeaponProfile Missile)
{
    public DefenseState PristineDefense => new(
        ShieldCapacity,
        ArmorIntegrity,
        ArmorProtection,
        Hull);

    public ScalingWeaponProfile Weapon(WeaponFamily family) => family switch
    {
        WeaponFamily.Kinetic => Kinetic,
        WeaponFamily.Energy => Energy,
        WeaponFamily.Missile => Missile,
        _ => throw new InvalidOperationException($"Unsupported scaling family {family}."),
    };
}

internal sealed record ScalingWeaponProfile(
    WeaponFamily Family,
    int Damage,
    int ShieldPenetration,
    int ArmorPenetration,
    int AccuracyBonus,
    int GuidanceChance,
    int MaximumRange,
    int PowerCost,
    int? Ammunition)
{
    public static ScalingWeaponProfile From(
        WeaponFamily family,
        ScalingWeaponDocument document) => new(
        family,
        document.Damage,
        document.ShieldPenetration,
        document.ArmorPenetration,
        document.AccuracyBonus,
        document.GuidanceChance,
        document.MaximumRange,
        document.PowerCost,
        document.AmmunitionValue);
}

internal readonly record struct DefenseState(
    int Shield,
    int ArmorIntegrity,
    int ArmorProtection,
    int Hull);

internal sealed record DamageStep(
    DefenseState State,
    LayeredDamageResolution Resolution);

internal sealed record MirrorEvidence(
    string SourceVariantId,
    WeaponFamily Family,
    int RangeHexes,
    double MeanTurns,
    double UnresolvedPercent);

internal sealed record ScalingGate(string Id, bool Passed, string Details)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "gate_id", "passed", "details",
    };
    public IReadOnlyList<string> Cells => new[]
    {
        Id,
        Passed.ToString(),
        Details,
    };
}

internal sealed record ProfileRow(
    string Id,
    string Label,
    int Tl,
    int Hull,
    int Ai,
    int Ap,
    int Shield,
    int Recharge,
    int ShieldArmor,
    int Reactor,
    int Targeting,
    int PdsChance,
    int PowerCommitment,
    int PowerMargin,
    int ShipMove,
    int MissileMove,
    int KineticDamage,
    int KineticApen,
    int KineticAccuracy,
    int KineticRange,
    int EnergyDamage,
    int EnergyApen,
    int EnergyAccuracy,
    int EnergyRange,
    int MissileDamage,
    int MissileApen,
    int MissileGuidance,
    int MissileRange)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "profile_id", "label", "tl", "hull", "armor_integrity", "armor_protection",
        "shield_capacity", "shield_recharge", "shield_armor", "reactor_output",
        "targeting_bonus", "effective_pds_chance", "standard_power_commitment",
        "power_margin", "ship_move", "missile_move", "kinetic_damage", "kinetic_apen",
        "kinetic_accuracy", "kinetic_range", "energy_damage", "energy_apen",
        "energy_accuracy", "energy_range", "missile_damage", "missile_apen",
        "missile_guidance", "missile_range",
    };

    public static ProfileRow From(TechnologyCombatProfile profile) => new(
        profile.Id,
        profile.Label,
        profile.TechnologyLevel,
        profile.Hull,
        profile.ArmorIntegrity,
        profile.ArmorProtection,
        profile.ShieldCapacity,
        profile.ShieldBaseRecharge,
        profile.ShieldArmor,
        profile.ReactorOutput,
        profile.TargetingBonus,
        profile.EffectivePdsChance,
        profile.StandardCombatPowerCommitment,
        profile.ReactorOutput - profile.StandardCombatPowerCommitment,
        profile.ShipMove,
        profile.MissileMove,
        profile.Kinetic.Damage,
        profile.Kinetic.ArmorPenetration,
        profile.Kinetic.AccuracyBonus,
        profile.Kinetic.MaximumRange,
        profile.Energy.Damage,
        profile.Energy.ArmorPenetration,
        profile.Energy.AccuracyBonus,
        profile.Energy.MaximumRange,
        profile.Missile.Damage,
        profile.Missile.ArmorPenetration,
        profile.Missile.GuidanceChance,
        profile.Missile.MaximumRange);

    public IReadOnlyList<string> Cells => new[]
    {
        Id, Label, F(Tl), F(Hull), F(Ai), F(Ap), F(Shield), F(Recharge),
        F(ShieldArmor), F(Reactor), F(Targeting), F(PdsChance),
        F(PowerCommitment), F(PowerMargin), F(ShipMove), F(MissileMove),
        F(KineticDamage), F(KineticApen), F(KineticAccuracy), F(KineticRange),
        F(EnergyDamage), F(EnergyApen), F(EnergyAccuracy), F(EnergyRange),
        F(MissileDamage), F(MissileApen), F(MissileGuidance), F(MissileRange),
    };

    private static string F(int value) => value.ToString(CultureInfo.InvariantCulture);
}

internal sealed record CalibrationRow(
    string SourceVariantId,
    WeaponFamily Family,
    int Range,
    double ObservedMeanTurns,
    double RawAnalyticalTurns,
    double CalibrationFactor,
    double CalibratedTurns,
    double AbsoluteErrorPercent,
    double UnresolvedPercent)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "source_variant_id", "family", "range", "observed_mean_turns",
        "raw_analytical_turns", "calibration_factor", "calibrated_turns",
        "absolute_error_percent", "unresolved_percent",
    };
    public IReadOnlyList<string> Cells => new[]
    {
        SourceVariantId, Family.ToString(), F(Range), D(ObservedMeanTurns),
        D(RawAnalyticalTurns), D(CalibrationFactor), D(CalibratedTurns),
        D(AbsoluteErrorPercent), D(UnresolvedPercent),
    };
    private static string F(int value) => value.ToString(CultureInfo.InvariantCulture);
    private static string D(double value) => double.IsFinite(value)
        ? value.ToString("F6", CultureInfo.InvariantCulture)
        : "INF";
}

internal sealed record PacketTraceRow(
    string ProfileId,
    WeaponFamily Family,
    int Packet,
    int StartShield,
    int StartAi,
    int StartAp,
    int StartHull,
    int ShieldBypass,
    int ShieldAbsorption,
    int ShieldArmorPrevented,
    int ArmorPrevented,
    int ArmorIntegrityDamage,
    int ArmorProtectionDamage,
    int HullDamage,
    int EndShield,
    int EndAi,
    int EndAp,
    int EndHull)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "profile_id", "family", "packet", "start_shield", "start_ai", "start_ap",
        "start_hull", "shield_bypass", "shield_absorption", "shield_armor_prevented",
        "armor_prevented", "armor_integrity_damage", "armor_protection_damage",
        "hull_damage", "end_shield", "end_ai", "end_ap", "end_hull",
    };
    public IReadOnlyList<string> Cells => new[]
    {
        ProfileId, Family.ToString(), F(Packet), F(StartShield), F(StartAi), F(StartAp),
        F(StartHull), F(ShieldBypass), F(ShieldAbsorption), F(ShieldArmorPrevented),
        F(ArmorPrevented), F(ArmorIntegrityDamage), F(ArmorProtectionDamage), F(HullDamage),
        F(EndShield), F(EndAi), F(EndAp), F(EndHull),
    };
    private static string F(int value) => value.ToString(CultureInfo.InvariantCulture);
}

internal sealed record ProtectionBreakpointRow(
    string ProfileId,
    WeaponFamily Family,
    string Layer,
    int Protection,
    int Penetration,
    int EffectiveProtection,
    int NetDamage)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "profile_id", "family", "layer", "protection", "penetration",
        "effective_protection", "net_damage",
    };
    public IReadOnlyList<string> Cells => new[]
    {
        ProfileId, Family.ToString(), Layer, F(Protection), F(Penetration),
        F(EffectiveProtection), F(NetDamage),
    };
    private static string F(int value) => value.ToString(CultureInfo.InvariantCulture);
}

internal sealed record RangeComparisonRow(
    string ComparisonType,
    string SideAProfile,
    string SideBProfile,
    WeaponFamily SideAFamily,
    WeaponFamily SideBFamily,
    int Range,
    double SideAExpectedKillTurns,
    double SideBExpectedKillTurns,
    double SideAWinPercent,
    double SideBWinPercent,
    double OddsCalibrationMultiplier,
    bool BothSidesCanAttack)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "comparison_type", "side_a_profile", "side_b_profile", "side_a_family",
        "side_b_family", "range", "side_a_expected_kill_turns",
        "side_b_expected_kill_turns", "side_a_win_percent", "side_b_win_percent",
        "odds_calibration_multiplier", "both_sides_can_attack",
    };

    public static RangeComparisonRow Create(
        string comparisonType,
        string sideAProfile,
        string sideBProfile,
        WeaponFamily sideAFamily,
        WeaponFamily sideBFamily,
        int range,
        double sideAKill,
        double sideBKill,
        double oddsCalibrationMultiplier = 1.0)
    {
        bool aFinite = double.IsFinite(sideAKill);
        bool bFinite = double.IsFinite(sideBKill);
        double aWin = WinPercent(
            sideAKill, sideBKill, oddsCalibrationMultiplier);
        return new RangeComparisonRow(
            comparisonType,
            sideAProfile,
            sideBProfile,
            sideAFamily,
            sideBFamily,
            range,
            sideAKill,
            sideBKill,
            aWin,
            100.0 - aWin,
            oddsCalibrationMultiplier,
            aFinite && bFinite);
    }

    public static double WinPercent(
        double sideAKill,
        double sideBKill,
        double oddsCalibrationMultiplier)
    {
        bool aFinite = double.IsFinite(sideAKill);
        bool bFinite = double.IsFinite(sideBKill);
        if (aFinite && bFinite)
        {
            double rawOdds = sideBKill / sideAKill;
            double adjustedOdds = rawOdds * Math.Max(
                0.000001, oddsCalibrationMultiplier);
            return adjustedOdds / (1.0 + adjustedOdds) * 100.0;
        }
        if (aFinite) return 100.0;
        if (bFinite) return 0.0;
        return 50.0;
    }

    public IReadOnlyList<string> Cells => new[]
    {
        ComparisonType, SideAProfile, SideBProfile, SideAFamily.ToString(),
        SideBFamily.ToString(), F(Range), D(SideAExpectedKillTurns),
        D(SideBExpectedKillTurns), D(SideAWinPercent), D(SideBWinPercent),
        D(OddsCalibrationMultiplier), BothSidesCanAttack.ToString(),
    };
    private static string F(int value) => value.ToString(CultureInfo.InvariantCulture);
    private static string D(double value) => double.IsFinite(value)
        ? value.ToString("F6", CultureInfo.InvariantCulture)
        : "INF";
}

internal sealed record CandidateReviewRow(
    string CandidateId,
    string Label,
    string Status,
    double MeanHigherTlWinPercent,
    double TargetDeltaPercentagePoints,
    bool WithinTargetBand,
    bool IsAggressiveControl,
    double StrongestSameTlEdgePercent,
    int PowerMargin,
    bool IdentityPassed,
    int MinimumMeaningfulDifferences,
    int MaximumSharedCoreAttributes,
    string IdentityWarnings,
    string DesignThesis,
    string NamingReview)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "candidate_id", "label", "status", "mean_higher_tl_win_percent",
        "target_delta_percentage_points", "within_target_band",
        "is_aggressive_control", "strongest_same_tl_edge_percent",
        "power_margin", "identity_passed",
        "minimum_meaningful_differences", "maximum_shared_core_attributes",
        "identity_warnings", "design_thesis", "naming_review",
    };
    public IReadOnlyList<string> Cells => new[]
    {
        CandidateId, Label, Status, D(MeanHigherTlWinPercent),
        D(TargetDeltaPercentagePoints), WithinTargetBand.ToString(),
        IsAggressiveControl.ToString(), D(StrongestSameTlEdgePercent),
        PowerMargin.ToString(CultureInfo.InvariantCulture),
        IdentityPassed.ToString(),
        MinimumMeaningfulDifferences.ToString(CultureInfo.InvariantCulture),
        MaximumSharedCoreAttributes.ToString(CultureInfo.InvariantCulture),
        IdentityWarnings, DesignThesis, NamingReview,
    };
    private static string D(double value) =>
        value.ToString("F6", CultureInfo.InvariantCulture);
}

internal readonly record struct FamilyRangeKey(
    WeaponFamily SideAFamily,
    WeaponFamily SideBFamily,
    int Range)
{
    public override string ToString() =>
        $"{SideAFamily}-{SideBFamily}-R{Range}";
}

internal sealed record CrossFamilyEvidence(
    string SourceVariantId,
    WeaponFamily SideAFamily,
    WeaponFamily SideBFamily,
    int RangeHexes,
    double SideAConditionalWinPercent,
    double MutualPercent,
    double UnresolvedPercent);

internal sealed record CrossFamilyCalibrationRow(
    string SourceVariantId,
    WeaponFamily SideAFamily,
    WeaponFamily SideBFamily,
    int Range,
    double ObservedSideAConditionalWinPercent,
    double RawSideAWinPercent,
    double OddsMultiplier,
    double CalibratedSideAWinPercent,
    double AbsoluteErrorPercentagePoints,
    double MutualPercent,
    double UnresolvedPercent)
{
    public static readonly IReadOnlyList<string> Header = new[]
    {
        "source_variant_id", "side_a_family", "side_b_family", "range",
        "observed_side_a_conditional_win_percent", "raw_side_a_win_percent",
        "odds_multiplier", "calibrated_side_a_win_percent",
        "absolute_error_percentage_points", "mutual_percent",
        "unresolved_percent",
    };
    public IReadOnlyList<string> Cells => new[]
    {
        SourceVariantId, SideAFamily.ToString(), SideBFamily.ToString(), F(Range),
        D(ObservedSideAConditionalWinPercent), D(RawSideAWinPercent),
        D(OddsMultiplier), D(CalibratedSideAWinPercent),
        D(AbsoluteErrorPercentagePoints), D(MutualPercent), D(UnresolvedPercent),
    };
    private static string F(int value) =>
        value.ToString(CultureInfo.InvariantCulture);
    private static string D(double value) => double.IsFinite(value)
        ? value.ToString("F6", CultureInfo.InvariantCulture)
        : "INF";
}

internal sealed record CandidateIdentityReview(
    bool Passed,
    int MinimumMeaningfulDifferences,
    int MaximumSharedCoreAttributes,
    IReadOnlyList<string> Warnings);
