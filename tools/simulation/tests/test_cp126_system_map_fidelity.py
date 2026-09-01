import json
import unittest
from pathlib import Path

from starcluster_research.baseline_foundation import BaselineCatalog, _build_to_ecology, enumerate_legal_builds
from starcluster_research.ecology import EcologyVariant
from starcluster_research.canonical_combat import mirror_equivalent, run_trial_full_map
from starcluster_research.tactical_geometry import (
    HexCoord, HexMap, RangeOrder, TacticalOrderPlan,
    advance_missile_finite_map, resolve_finite_movement, resolve_search_toward_center,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "docs/archive/testing/pre-cp165-active/system_map_research_parity_fixtures_v0_1.json"


def coord(v):
    return HexCoord(int(v[0]), int(v[1]))


class Cp126SystemMapFidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.map = HexMap.create_hexagon(int(cls.doc["mapRadius"]))

    def test_shared_geometry_fixture(self):
        self.assertEqual(self.doc["expectedCellCount"], len(self.map.cells))
        for row in self.doc["searchCases"]:
            got = resolve_search_toward_center(self.map, coord(row["origin"]), int(row["available"]))
            self.assertEqual(coord(row["destination"]), got.destination, row["id"])
            self.assertEqual(int(row["movement"]), got.movement_hexes, row["id"])
        for row in self.doc["movementCases"]:
            got = resolve_finite_movement(
                self.map, coord(row["origin"]), coord(row["target"]), int(row["available"]),
                TacticalOrderPlan(RangeOrder(row["order"]), int(row["desired"])),
            )
            self.assertEqual(coord(row["destination"]), got.destination, row["id"])
            self.assertEqual(tuple(coord(v) for v in row["path"]), got.path, row["id"])
            self.assertEqual(int(row["finalRange"]), got.final_range, row["id"])
            self.assertEqual(int(row["closest"]), got.closest_approach, row["id"])
            self.assertEqual(int(row["farthest"]), got.farthest_separation, row["id"])
            self.assertEqual(int(row["movement"]), got.movement_hexes, row["id"])
            self.assertEqual(bool(row["boundary"]), got.ended_on_boundary, row["id"])
        for row in self.doc["missileCases"]:
            got = advance_missile_finite_map(
                self.map, coord(row["origin"]), coord(row["target"]), int(row["speed"]),
                int(row["maximumTravel"]), int(row["alreadyTraveled"]),
            )
            self.assertEqual(coord(row["destination"]), got.destination, row["id"])
            self.assertEqual(int(row["movement"]), got.distance_traveled_this_phase, row["id"])
            self.assertEqual(int(row["totalTraveled"]), got.total_distance_traveled, row["id"])
            self.assertEqual(bool(row["terminal"]), got.terminal, row["id"])
            self.assertEqual(bool(row["rangeExhausted"]), got.range_exhausted, row["id"])

    def test_physical_side_swap_symmetry(self):
        catalog = BaselineCatalog(ROOT)
        _, builds = enumerate_legal_builds(catalog)
        representatives = []
        for tl in (1, 2, 3, 5, 7, 9):
            group = [b for b in builds if b.tl == tl]
            representatives.append((tl, group[len(group)//3], group[(2*len(group))//3]))
        for tl, left, right in representatives:
            a = _build_to_ecology(left, "cp126-symmetry")
            b = _build_to_ecology(right, "cp126-symmetry")
            for first in ("SideAFirst", "SideBFirst"):
                mirrored = "SideBFirst" if first == "SideAFirst" else "SideAFirst"
                for trial in range(20):
                    v1 = EcologyVariant(
                        f"sym-{tl}-one", tl, a, b, first,
                        geometry="radius5_full_hex_adaptive", population="cp126_symmetry", scenario_group=f"cp126_symmetry_tl{tl}",
                        physical_id_a=f"tl{tl}-ship1", physical_id_b=f"tl{tl}-ship2",
                    )
                    v2 = EcologyVariant(
                        f"sym-{tl}-two", tl, b, a, mirrored,
                        geometry="radius5_full_hex_adaptive", population="cp126_symmetry", scenario_group=f"cp126_symmetry_tl{tl}",
                        physical_id_a=f"tl{tl}-ship2", physical_id_b=f"tl{tl}-ship1",
                    )
                    r1 = run_trial_full_map(catalog.matrix, v1, 12620260816, trial)
                    r2 = run_trial_full_map(catalog.matrix, v2, 12620260816, trial)
                    self.assertTrue(mirror_equivalent(r1, r2), f"TL{tl} {first} trial {trial}")

    def test_adaptive_standoff_memory_is_exercised(self):
        catalog = BaselineCatalog(ROOT)
        _, builds = enumerate_legal_builds(catalog)
        # TL8 provides a clean demonstrated-standoff lane: Missile guidance can
        # obtain Firm track at a range beyond the Kinetic physical envelope.
        m = next(b for b in builds if b.tl == 8 and b.weapon_family == "Missile" and b.missile_payload == "GP" and b.main_count == 1 and b.reactor_count == 1 and not b.shield and b.ecm_count == 0 and b.eccm_count == 0 and b.pds_family == "")
        k = next(b for b in builds if b.tl == 8 and b.weapon_family == "Kinetic" and b.main_count == 1 and b.reactor_count == 1 and not b.shield and b.ecm_count == 0 and b.eccm_count == 0 and b.pds_family == "")
        v = EcologyVariant(
            "cp126-standoff-probe", 8, _build_to_ecology(m,"probe"), _build_to_ecology(k,"probe"), "SideAFirst",
            geometry="radius5_full_hex_adaptive", population="cp126_probe", scenario_group="cp126_probe",
        )
        seen = 0
        for trial in range(10):
            r = run_trial_full_map(catalog.matrix, v, 12620260816, trial)
            seen += r.full_a.adaptive_standoff_orders + r.full_b.adaptive_standoff_orders
        self.assertGreater(seen, 0)


if __name__ == "__main__":
    unittest.main()
