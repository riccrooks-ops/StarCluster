from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from starcluster_research.ecology import CandidateMatrix

REPO = Path(__file__).resolve().parents[3]
CANONICAL_MATRIX = "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_2.json"


class CanonicalDamageScaleTests(unittest.TestCase):
    def test_candidate_matrix_default_remains_historical_for_old_studies(self):
        matrix = CandidateMatrix(REPO)
        self.assertTrue(str(matrix.path).endswith("technology_numerical_matrix_v0_1.json"))
        self.assertEqual(12, matrix.p("hull", 1)["hullPoints"])
        self.assertEqual(5, matrix.p("missile_delivery", 1)["warheadDamage"])

    def test_candidate_matrix_can_bind_canonical_x2_successor(self):
        matrix = CandidateMatrix(REPO, CANONICAL_MATRIX)
        self.assertEqual(2, matrix.doc["damagePointScale"]["canonicalScale"])
        self.assertEqual(24, matrix.p("hull", 1)["hullPoints"])
        self.assertEqual(10, matrix.p("missile_delivery", 1)["warheadDamage"])
        self.assertEqual(8, matrix.p("kinetic_main", 1)["damage"])

    def test_tl1_repair_kit_yield_remains_one_canonical_hull(self):
        path = REPO / "docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_4.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = {r["parameter_id"]: r for r in csv.DictReader(stream)}
        self.assertEqual("Repair 1 Hull", rows["repair_hull_chance"]["display_name"])
        self.assertEqual("40", rows["repair_hull_chance"]["value"])
        self.assertIn("1 canonical Hull point", rows["repair_hull_chance"]["rationale"])

    def test_canonical_authority_declares_repair_and_critical_exceptions(self):
        path = REPO / "docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_1.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(2, doc["damagePointScale"])
        self.assertEqual(1, doc["productionDamageControlHullPerRepairKit"])
        self.assertEqual(2, doc["parityOnlyHullPerRepairKit"])
        self.assertTrue(doc["criticalCadenceMigrationDeferred"])
        self.assertFalse(doc["oddHalfStepValuesPromoted"])


if __name__ == "__main__":
    unittest.main()
