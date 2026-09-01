from __future__ import annotations
import copy, sys, unittest
from pathlib import Path

SIM_ROOT = Path(__file__).resolve().parents[1]
REPO = SIM_ROOT.parents[1]
if str(SIM_ROOT) not in sys.path:
    sys.path.insert(0, str(SIM_ROOT))

from starcluster_research.study import load_json, validate_study, build_study
from starcluster_research.parity import run_parity

PRIMARY = REPO / 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_1.json'
OVERLAY = REPO / 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_2.json'

class Cp103ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.primary_doc = load_json(PRIMARY)
        cls.overlay_doc = load_json(OVERLAY)
        cls.primary = build_study(cls.primary_doc)
        cls.overlay = build_study(cls.overlay_doc)

    def test_numeric_checkpoint_is_rejected(self):
        doc = copy.deepcopy(self.primary_doc)
        doc['checkpoint'] = 103
        errors = validate_study(doc)
        self.assertTrue(any('checkpoint must be str' in e or 'checkpoint must be the string' in e for e in errors), errors)

    def test_primary_exact_population_contract(self):
        b = self.primary
        self.assertEqual(921600, b['raw'])
        self.assertEqual(164160, len(b['builds']))
        self.assertEqual({'exact_fill':43584,'near_fill':82848,'underfilled':37728}, b['space_counts'])
        self.assertEqual(96, len(b['cells']))
        self.assertEqual(97848, b['sample_attempts'])
        self.assertEqual(576, len(b['pairs']))
        self.assertEqual(1152, len(b['variants']))
        self.assertEqual(240, sum(1 for p in b['pairs'] if p.source == 'statistical' and p.orientation == 'forward'))
        self.assertEqual(32, sum(1 for p in b['pairs'] if p.source == 'diversity' and p.orientation == 'forward'))
        self.assertEqual(32, sum(1 for p in b['pairs'] if p.source == 'named'))

    def test_overlay_exact_contract(self):
        b = self.overlay
        self.assertEqual(1417176, b['raw'])
        self.assertEqual(28, len(b['builds']))
        self.assertEqual({'exact_fill':4,'near_fill':6,'underfilled':18}, b['space_counts'])
        self.assertEqual(33, len(b['named']))
        self.assertEqual(50, len(b['pairs']))
        self.assertEqual(100, len(b['variants']))
        self.assertTrue(all(p.representative_weight == 0.0 for p in b['pairs']))

    def test_no_dual_main_dual_reactor_primary_build(self):
        self.assertFalse(any(b.main_weapons > 1 and b.reactors > 1 for b in self.primary['builds']))

    def test_all_primary_population_cells_are_nonempty(self):
        self.assertEqual(96, len(self.primary['cells']))
        self.assertTrue(all(c.population > 0 for c in self.primary['cells'].values()))

    def test_parity_corpus(self):
        self.assertEqual([], run_parity(REPO))
        wrapper = (SIM_ROOT / 'Invoke-StarClusterResearch.ps1').read_text(encoding='utf-8-sig')
        self.assertIn("$probe = @($candidate.Prefix + @('--version'))", wrapper)
        self.assertNotRegex(wrapper, r'(?m)^\s*\$probe\s*=.*-c')
        checkpoint_root = REPO / 'tools' / 'checkpoints' / 'checkpoint-103'
        for path in (checkpoint_root / 'apply_checkpoint_103.ps1', checkpoint_root / 'test_checkpoint_103_contract.ps1'):
            powershell = path.read_text(encoding='utf-8-sig')
            self.assertNotRegex(powershell, r'\.Contains\([\"\']@\(')
            self.assertIn('[regex]::IsMatch', powershell)
        self.assertIn('Windows PowerShell 5.1', wrapper)

if __name__ == '__main__':
    unittest.main()
