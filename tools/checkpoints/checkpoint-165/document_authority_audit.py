#!/usr/bin/env python3
import argparse,csv,hashlib,json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
PROD='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194';PF4='7fd4dfbbe375586de2605361006db84b68f89767c76ba4b76da6cf5f48253155'
PT_SET={'README.md','Current_Technology_Tree.md','StarCluster_Current_TL1_TL9_Technology_Tree.xlsx','current_working_technology_baseline.json','component_installation_space_catalog.json','auxiliary_component_catalog.json','technology_numerical_matrix_v0_9.json','technology_research_execution_baseline_pending_finalization_v0_4.json'}
TEST_SET={'README.md','Runtime_Language_And_Testing_Boundary.md','Current_Testing_Architecture.md'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def docx_text(p):
 with ZipFile(p) as z:r=ET.fromstring(z.read('word/document.xml'))
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};return '\n'.join(''.join(t.text or '' for t in x.findall('.//w:t',ns)) for x in r.findall('.//w:p',ns))
def report(repo):
 c=[]
 def ck(n,x,d=''):c.append({'name':n,'passed':bool(x),'detail':d})
 req=['docs/CURRENT_AUTHORITIES.md','docs/Star_Cluster_Game_Concept.docx','docs/design/combat/Combat_System_Reference.md','docs/design/player_technology/Current_Technology_Tree.md','docs/design/player_technology/StarCluster_Current_TL1_TL9_Technology_Tree.xlsx','docs/design/player_technology/current_working_technology_baseline.json','docs/design/player_technology/component_installation_space_catalog.json','docs/design/player_technology/auxiliary_component_catalog.json','docs/design/testing/Current_Testing_Architecture.md','docs/references/player_technology/Technology_Family_Storyboard.md','docs/references/player_technology/Technology_Idea_Register.md']
 for x in req:ck('exists:'+x,(repo/x).is_file())
 pt=repo/'docs/design/player_technology';test=repo/'docs/design/testing'
 ck('player-tech-active-set',{p.name for p in pt.iterdir() if p.is_file()}==PT_SET)
 ck('testing-active-set',{p.name for p in test.iterdir() if p.is_file()}==TEST_SET)
 ck('old-concept-not-active',not(repo/'docs/Star_Cluster_Game_Concept_v0.7x.docx').exists());ck('old-concept-archived',(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx').is_file())
 ck('prod-hash',sha(pt/'technology_numerical_matrix_v0_9.json')==PROD);ck('pf4-hash',sha(pt/'technology_research_execution_baseline_pending_finalization_v0_4.json')==PF4)
 b=json.loads((pt/'current_working_technology_baseline.json').read_text())
 ck('baseline-cp165',b.get('checkpoint')==165);ck('space-ladder',[b['globalRules']['installationSpaceByTl'][str(i)] for i in range(1,10)]==[35,35,36,36,37,37,38,38,39])
 m=b['powerClosure']['mainReactor'];a=b['powerClosure']['apu'];ck('reactor-space',all(m[str(i)]['space']==6 for i in range(1,10)));ck('reactor-tp',[m[str(i)]['operationalTp'] for i in range(1,10)]==list(range(5,14)));ck('apu-space',all(a[str(i)]['space']==2 for i in range(1,10)));ck('apu-tp',[a[str(i)]['operationalTp'] for i in range(1,10)]==[1,1,1,1,2,2,2,2,2]);ck('apu-no-cap',b['globalRules']['apuCountCap'] is None)
 d=b['damageModel'];ck('defres',d['id']=='def-res-v1');ck('def-ladder',[d['shieldDefByTlPp'][str(i)] for i in range(1,10)]==[20,22,24,26,28,30,32,34,36]);ck('res-ladder',[d['armorResByTlPp'][str(i)] for i in range(1,10)]==[20,22,24,26,28,30,32,34,36]);ck('caps',(d['shieldDefCapPp'],d['armorResCapPp'])==(45,95))
 r=b['combatRules'];ck('direct-fire',(r['firmTrackPenaltyPp'],r['directFireApproximateTrackPenaltyPp'],r['directFireExtendedRangePenaltyPp'],r['modifiersStack'])==(0,-25,-10,True))
 text=docx_text(repo/'docs/Star_Cluster_Game_Concept.docx');
 for term in ['DEF/RES v1','5/6/7/8/9/10/11/12/13 Operational TP','Auxiliary Power Unit (APU)','Repair Drone Bay','Approximate direct fire','Swarmer']:ck('concept:'+term,term in text)
 pmap=json.loads((repo/'docs/archive/player_technology/pre-cp165-active/RELOCATION_MAP.json').read_text())['moved'];tmap=json.loads((repo/'docs/archive/testing/pre-cp165-active/RELOCATION_MAP.json').read_text())['entries'];ck('player-relocation-count',len(pmap)==116,str(len(pmap)));ck('testing-relocation-count',len(tmap)==92,str(len(tmap)))
 # .NET parity tests that consume retired fixtures must resolve them from archive, not repopulate active testing discovery.
 cs='\n'.join(x.read_text(encoding='utf-8') for x in (repo/'tests/StarCluster.Tests').rglob('*.cs'));fixtures=['canonical_combat_kernel_fixtures_v0_1.json','system_map_research_parity_fixtures_v0_1.json','cp144_engage_adaptive_policy_parity_fixtures_v0_1.json','cp146_combat_resource_doctrine_parity_fixtures_v0_1.json','cp147_tactical_package_utility_parity_fixtures_v0_1.json'];ck('dotnet-parity-fixtures-archived','\"docs\", \"design\", \"testing\"' not in cs and all(f'\"docs\", \"archive\", \"testing\", \"pre-cp165-active\", \"{name}\"' in cs for name in fixtures))
 # ScenarioRunner historical defaults must use archived frozen design fixtures after CP165 cleanup.
 sr=(repo/'src/StarCluster.ScenarioRunner/Program.cs').read_text(encoding='utf-8');legacy=['tl1_core_combat_numerical_baseline_v0_1.csv','tl1_core_combat_numerical_baseline_v0_3.csv','auxiliary_component_catalog_v0_1.json','auxiliary_component_catalog_schema_v0_1.json'];archive=repo/'docs/archive/player_technology/pre-cp165-active';ck('scenario-runner-legacy-defaults-archived','\"docs\", \"design\", \"player_technology\"' not in sr and 'LegacyPlayerTechnologyFile' in sr and all((archive/name).is_file() and f'LegacyPlayerTechnologyFile(\"{name}\")' in sr for name in legacy))
 # frozen production code
 bad=[]
 with (repo/'docs/validation/evidence/checkpoint-165/CP164_FROZEN_PRODUCTION_RUNTIME_SHA256.csv').open() as f:
  for row in csv.DictReader(f):
   p=repo/row['path']
   if not p.is_file() or sha(p)!=row['sha256']:bad.append(row['path'])
 ck('production-runtime-frozen',not bad,str(bad[:10]))
 prov=json.loads((repo/'docs/validation/evidence/checkpoint-165/CP164_ACCEPTED_NATIVE_PROVENANCE.json').read_text());ck('cp164-provenance',prov['nativeAccepted'] and prov['substantiveCombatTrials']==1620000 and prov['combatErrorTrials']==0)
 # current baseline no stale compatibility keys
 blob=json.dumps(b)
 for key in ['shieldArmor','legacyApproxPenaltyPp','researchBaselineCandidate']:ck('excluded:'+key,key not in blob)
 passed=all(x['passed'] for x in c);return {'checkpoint':165,'passed':passed,'checksPassed':sum(x['passed'] for x in c),'checksTotal':len(c),'failed':[x for x in c if not x['passed']],'checks':c}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--out-dir');z=ap.parse_args();repo=Path(z.repo).resolve();r=report(repo)
 if z.out_dir:
  out=Path(z.out_dir);out.mkdir(parents=True,exist_ok=True);(out/'cp165_authority_consistency_report.json').write_text(json.dumps(r,indent=2)+'\n')
  pm=json.loads((repo/'docs/archive/player_technology/pre-cp165-active/RELOCATION_MAP.json').read_text())['moved'];tm=json.loads((repo/'docs/archive/testing/pre-cp165-active/RELOCATION_MAP.json').read_text())['entries']
  with (out/'cp165_document_relocation_summary.csv').open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['category','old_active_path','new_archive_path']);[w.writerow(['player_technology',a,b]) for a,b in sorted(pm.items())];[w.writerow(['testing',a,b]) for a,b in sorted(tm.items())]
 print(json.dumps({'passed':r['passed'],'checksPassed':r['checksPassed'],'checksTotal':r['checksTotal'],'failed':[x['name'] for x in r['failed']]},indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
