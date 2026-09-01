from __future__ import annotations
import copy, sys, unittest
from collections import Counter
from pathlib import Path

SIM_ROOT = Path(__file__).resolve().parents[1]
REPO = SIM_ROOT.parents[1]
if str(SIM_ROOT) not in sys.path:
    sys.path.insert(0, str(SIM_ROOT))

from starcluster_research.study import load_json, validate_study, build_study

STUDY = REPO / 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v1_3.json'

class Cp104ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json(STUDY)
        cls.built = build_study(cls.doc)

    def test_cp104_exact_diagnostic_contract(self):
        b=self.built
        self.assertEqual(124002900,b['raw'])
        self.assertEqual(52,len(b['builds']))
        self.assertEqual({'exact_fill':12,'near_fill':14,'underfilled':26},b['space_counts'])
        self.assertEqual(128,len(b['pairs']))
        self.assertEqual(256,len(b['variants']))
        self.assertTrue(all(p.representative_weight==0.0 for p in b['pairs']))

    def test_cp104_category_and_higher_tl_gate(self):
        counts=Counter(g['id'].split('__',1)[0] for g in self.doc['pairingGroups'])
        self.assertEqual({'legacy-response':32,'movement':20,'energy-synergy':44,'power-hotspot':28,'control':4},dict(counts))
        gate=self.doc['higherTlExpansionGate']
        self.assertTrue(gate['afterCheckpoint104'])
        self.assertTrue(gate['additionalTl3CalibrationOnlyForArchitecturalDefect'])

    def test_cp104_checkpoint_string_and_numeric_rejection(self):
        self.assertEqual([],validate_study(self.doc))
        bad=copy.deepcopy(self.doc); bad['checkpoint']=104
        errs=validate_study(bad)
        self.assertTrue(any('checkpoint must be str' in e or 'checkpoint must be the string' in e for e in errs),errs)

    def test_cp103_studies_remain_valid_after_schema_generalization(self):
        for name in ('cross-tl-build-permutation-foundation-v1_1.json','cross-tl-build-permutation-foundation-v1_2.json'):
            doc=load_json(REPO/'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology'/name)
            self.assertEqual([],validate_study(doc),name)

if __name__=='__main__': unittest.main()
