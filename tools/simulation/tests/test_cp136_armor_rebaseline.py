from __future__ import annotations
import json, re, sys, unittest, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
REPO=Path(__file__).resolve().parents[3]
SIM=REPO/'tools/simulation'
if str(SIM) not in sys.path: sys.path.insert(0,str(SIM))
from starcluster_research.ecology import CandidateMatrix, EcologyBuild, _armor_profile
from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION
from starcluster_research.same_tl_candidate_baseline_analysis import validate_study, build_plan

MATRIX='docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_8.json'
STUDY=REPO/'docs/archive/testing/pre-cp165-active/cp136_armor_rebaseline_study_v0_1.json'

def build(tl:int, armor='mainline')->EcologyBuild:
    m=CandidateMatrix(REPO,MATRIX); cap=m.capacity(tl)
    return EcologyBuild(f'tl{tl}-{armor}',tl,'probe','Kinetic',1,1,True,False,False,None,False,cap,0,cap,armor_profile=armor)

def xlsx_rows(path:Path,sheet_name:str):
    NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    RNS='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    PKG='{http://schemas.openxmlformats.org/package/2006/relationships}'
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall(NS+'si'): shared.append(''.join(t.text or '' for t in si.iter(NS+'t')))
        wb=ET.fromstring(z.read('xl/workbook.xml')); rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relmap={x.attrib['Id']:x.attrib['Target'] for x in rels.findall(PKG+'Relationship')}; target=None
        for s in wb.find(NS+'sheets'):
            if s.attrib['name']==sheet_name: target=relmap[s.attrib[RNS+'id']]; break
        if not target: raise AssertionError(f'missing sheet {sheet_name}')
        target=('xl/'+target.lstrip('/')) if not target.startswith('/') else target.lstrip('/')
        root=ET.fromstring(z.read(target)); rows=[]
        for row in root.iter(NS+'row'):
            vals={}
            for c in row.findall(NS+'c'):
                ref=c.attrib['r']; col=re.match(r'[A-Z]+',ref).group(0); typ=c.attrib.get('t'); v=c.find(NS+'v'); isel=c.find(NS+'is'); raw=''
                if typ=='s' and v is not None: raw=shared[int(v.text)]
                elif typ=='inlineStr' and isel is not None: raw=''.join(t.text or '' for t in isel.iter(NS+'t'))
                elif v is not None: raw=v.text or ''
                vals[col]=raw
            rows.append(vals)
        return rows

class Cp136ArmorRebaselineTests(unittest.TestCase):
    def test_kernel_version_unchanged(self): self.assertEqual('0.7',CANONICAL_COMBAT_KERNEL_VERSION)
    def test_study_shape(self):
        doc=json.loads(STUDY.read_text()); self.assertEqual([],validate_study(doc)); p=build_plan(REPO,STUDY,None)['summary']; self.assertEqual(196,p['logicalContexts']); self.assertEqual(392,p['generatedVariants']); self.assertEqual(136,p['tl6Variants'])
    def test_mainline_armor_progression(self):
        m=CandidateMatrix(REPO,MATRIX)
        expected={1:(0,6,0,0),2:(0,8,0,0),3:(1,9,0,0),4:(1,10,0,0),5:(2,10,0,0),6:(1,9,1,1),7:(1,10,1,1),8:(2,11,1,1),9:(3,12,1,2)}
        for tl,want in expected.items():
            p=m.p('armor',tl); got=(int(p['ap']),int(p['ai']),int(p['tacticalRegenerationPerTp']),int(p['tacticalRegenerationCapTp'])); self.assertEqual(want,got,tl)
    def test_regeneration_cap_is_steady(self):
        m=CandidateMatrix(REPO,MATRIX); self.assertEqual([1,1,1,2],[int(m.p('armor',tl)['tacticalRegenerationCapTp']) for tl in (6,7,8,9)])
        self.assertEqual([1,1,1,1],[int(m.p('armor',tl)['tacticalRegenerationPerTp']) for tl in (6,7,8,9)])
    def test_crystalline_tl6_seed(self):
        m=CandidateMatrix(REPO,MATRIX); p=_armor_profile(m,build(6,'A_b1')); self.assertEqual((2,11,0,0),(int(p['ap']),int(p['ai']),int(p['tacticalRegenerationPerTp']),int(p['tacticalRegenerationCapTp'])))
    def test_crystalline_remains_tl6_only(self):
        m=CandidateMatrix(REPO,MATRIX)
        with self.assertRaises(ValueError): _armor_profile(m,build(7,'A_b1'))
    def test_workbook_has_unique_branch_key_and_current_values(self):
        rows=xlsx_rows(REPO/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8c.xlsx','Numerical Baseline')
        found=[]
        for r in rows:
            if r.get('A') in ('armor','armor_A_b1') and r.get('B'):
                found.append((r['A'],int(float(r['B'])),r.get('C',''),json.loads(r['D'])))
        self.assertEqual(10,len(found)); self.assertEqual(10,len({(x[0],x[1]) for x in found}))
        branch=[x for x in found if x[0]=='armor_A_b1'][0]; self.assertEqual((2,11,0),(branch[3]['ap'],branch[3]['ai'],branch[3]['tacticalRegenerationCapTp']))

if __name__=='__main__': unittest.main()
