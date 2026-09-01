#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, re, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP126_SHA='a82e8e1f98f9af5589666d091f4773cd3f98b881c82c108a7da7ab2d1c74edb0'
EXPECTED_DIFFS={
 ('stl','5','move'):(6,5),('stl','8','move'):(9,8),('stl','9','move'):(10,9),
 ('missile_delivery','5','missileMove'):(5,6),('missile_delivery','8','missileMove'):(8,9),('missile_delivery','9','missileMove'):(9,10),
 ('energy_main','8','lowDamage'):(8,7),('energy_main','8','standardDamage'):(11,10),('energy_main','8','highDamage'):(13,12),
}

def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def manifest(p):
    out={}
    for line in text(p).splitlines():
        if line.strip(): h,r=line.split('  ',1);out[r]=h
    return out

def validate_stdlib_only_python_surface(repo:Path):
    """Reject undeclared third-party imports before any checkpoint work depends on them."""
    roots=[repo/'tools/simulation', repo/'tools/checkpoints/checkpoint-127']
    files=[]
    for root in roots:
        files.extend(sorted(root.rglob('*.py')))
    files.append(repo/'tools/checkpoints/prepackage_repository_hygiene.py')
    stdlib=set(sys.stdlib_module_names)|{'__future__'}
    local_roots={'starcluster_research'}
    violations=[]
    for path in files:
        source=text(path)
        tree=ast.parse(source,filename=str(path))
        for node in ast.walk(tree):
            names=[]
            if isinstance(node,ast.Import):
                names=[a.name.split('.',1)[0] for a in node.names]
            elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
                names=[node.module.split('.',1)[0]]
            for name in names:
                if name not in stdlib and name not in local_roots:
                    violations.append(f"{path.relative_to(repo).as_posix()}:{getattr(node,'lineno','?')}:{name}")
    req(not violations,'non-stdlib Python dependency on CP127 acceptance surface: '+', '.join(violations[:8]))
    return len(files)

def read_xlsx_table(path:Path):
    """Read the CP127 workbook with stdlib OOXML only; no third-party Excel package is required."""
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'p':'http://schemas.openxmlformats.org/package/2006/relationships'}
    with zipfile.ZipFile(path) as z:
        workbook=ET.fromstring(z.read('xl/workbook.xml'))
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relmap={e.attrib['Id']:e.attrib['Target'].lstrip('/') for e in rels}
        sheets=[]
        for sh in workbook.find('x:sheets',ns):
            rid=sh.attrib['{'+ns['r']+'}id']
            sheets.append((sh.attrib['name'],relmap[rid]))
        req([n for n,_ in sheets]==['Overview','Lineage Map','Numerical Baseline','Optional Components','CP127 Decisions'],'workbook sheets')
        target=dict(sheets)['Numerical Baseline']
        root=ET.fromstring(z.read(target))
        dim=root.find('x:dimension',ns)
        req(dim is not None and dim.attrib.get('ref')=='A1:E181','workbook numerical shape')
        rows=[]
        for row in root.findall('x:sheetData/x:row',ns):
            vals=[None]*5
            for cell in row.findall('x:c',ns):
                ref=cell.attrib.get('r','')
                m=re.match(r'([A-E])([0-9]+)$',ref)
                if not m: continue
                idx=ord(m.group(1))-ord('A')
                ctype=cell.attrib.get('t')
                if ctype=='inlineStr':
                    vals[idx]=''.join((node.text or '') for node in cell.findall('.//x:t',ns))
                else:
                    v=cell.find('x:v',ns)
                    raw='' if v is None or v.text is None else v.text
                    if ctype=='n' and raw!='':
                        num=float(raw)
                        vals[idx]=int(num) if num.is_integer() else num
                    else:
                        vals[idx]=raw
            rows.append(vals)
    req(len(rows)==181 and rows[0]==['Profile','TL','Technology','Characteristics','Notes'],'workbook numerical rows/header')
    return rows

def validate_cp126(repo:Path):
    z=repo/'docs/validation/evidence/checkpoint-127/CP126_NATIVE_RESULTS_ORIGINAL.zip'
    req(z.is_file() and sha(z)==CP126_SHA,'accepted CP126 archive hash')
    s=js(repo/'docs/validation/evidence/checkpoint-127/CP126_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==126 and s['failedGates']==[],'CP126 accepted identity')
    req(s['dotnetSdk']=='8.0.423' and s['buildPassed'] and s['pythonTestsPassed']==160 and s['xunitPassed']==907,'CP126 build/test provenance')
    req(s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'CP126 self-test/parity provenance')
    req(s['symmetryComparisons']==2250 and s['symmetryMismatches']==0,'CP126 symmetry provenance')
    req(s['generatedVariants']==139000 and s['substantiveTrials']==34750000 and s['mixedTlShipsExecuted'] is False,'CP126 substantive provenance')

def validate_production_frozen(repo:Path):
    old=manifest(repo/'docs/validation/evidence/checkpoint-126/CP126_REPOSITORY_SHA256SUMS.txt')
    for prefix in ('src/','tests/StarCluster.Tests/'):
        current=sorted(p.relative_to(repo).as_posix() for p in (repo/prefix.rstrip('/')).rglob('*') if p.is_file() and '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix())
        expected=sorted(r for r in old if r.startswith(prefix))
        req(current==expected,f'production path drift under {prefix}')
        for rel in expected: req(sha(repo/rel)==old[rel],f'production hash drift {rel}')

def numeric_leaves(d):
    out={}
    for fam,tiers in d['profiles'].items():
        for tl,row in tiers.items():
            for k,v in row.items():
                if isinstance(v,(int,float)) and not isinstance(v,bool) and k!='tl': out[(fam,tl,k)]=v
    return out

def validate_matrix(repo:Path):
    old=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json')
    new=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_4.json')
    req(new['schemaVersion'].endswith('v0.4') and new['authorityBoundary']['referenceCheckpoint']==127,'matrix identity')
    a,b=numeric_leaves(old),numeric_leaves(new)
    diffs={k:(a.get(k),b.get(k)) for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)}
    req(diffs==EXPECTED_DIFFS,f'unexpected numerical delta: {diffs}')
    p=new['profiles']
    req([p['stl'][str(t)]['move'] for t in range(1,10)]==list(range(1,10)),'STL invariant')
    req([p['missile_delivery'][str(t)]['missileMove'] for t in range(1,10)]==list(range(2,11)),'Missile Move invariant')
    req([p['ftl'][str(t)]['strategicMove'] for t in range(1,10)]==[1,2,3,4,4,6,7,9,12],'FTL strategic exception')
    e=p['energy_main']['8'];req((e['lowDamage'],e['standardDamage'],e['highDamage'],e['accuracyPp'],e['apen'],e['spen'],e['range'])==(7,10,12,35,3,5,9),'TL8 Energy candidate')

def storykeys(s): return [(d['disciplineId'],l['id'],int(b['tl']),b['title']) for d in s['disciplines'] for l in d['lineages'] for b in l['beats']]
def tablekeys(t): return [(e['disciplineId'],e['lineageId'],int(e['tl']),e['technology']) for e in t['lineageEntries']]
def validate_table(repo:Path):
    s=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json')
    t=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_6.json')
    req(t['checkpoint']==127 and t['cp127StabilizationSummary']['numericLeafChangesFromV0_3']==9,'Tech Table identity')
    sk,tk=storykeys(s),tablekeys(t); req(len(sk)==218 and len(tk)==218 and len(set(tk))==218 and set(sk)==set(tk),'Storyboard/Tech Table reconciliation')
    c=js(repo/'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_3.json')
    req(c['checkpoint']==127 and c['primaryReferenceMatrix']=='technology_numerical_matrix_v0_4.json' and c['primaryTechnologyTable']=='technology_component_table_v0_6.json','canonical authority')

def validate_docs(repo:Path):
    active=list((repo/'docs').glob('Star_Cluster_Game_Concept_v0.7*.docx'))
    req([p.name for p in active]==['Star_Cluster_Game_Concept_v0.7r.docx'],f'active Concept: {active}')
    with zipfile.ZipFile(active[0]) as z:
        doc=''.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
        header=''.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/header') and n.endswith('.xml'))
        core=z.read('docProps/core.xml').decode('utf-8','ignore')
    for phrase in ('8.13 Main-subsystem technology stabilization','standard Move equals its installed Drive TL','Operational Missile Move equals the installed Missile Drive TL plus 1','1, 2, 3, 4, 4, 6, 7, 9, and 12','7/10/12'):
        req(phrase in doc,f'Concept missing {phrase}')
    req('v0.7r' in header and 'Star Cluster Game Concept v0.7r' in core and '<cp:version>0.7r</cp:version>' in core,'Concept version metadata')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/README.md','docs/design/testing/README.md','docs/design/player_technology/README.md','docs/validation/README.md','docs/Prototype_TODO.md','docs/development/Simulation_Development_Guidelines.md'):
        req('127' in text(repo/rel) or 'cp127' in text(repo/rel).lower(),f'{rel} not CP127-aware')
    sheet_rows=read_xlsx_table(repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Stabilized_TL1_TL9_Technology_Component_Table_v0_6.xlsx')
    matrix=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_4.json')
    rows={(str(r[0]),int(r[1])):(r[2],json.loads(r[3]),r[4]) for r in sheet_rows[1:]}
    req(len(rows)==180,'workbook numerical rows')
    for fam,tiers in matrix['profiles'].items():
        for tl,row in tiers.items():
            tech,stats,notes=rows[(fam,int(tl))]
            expected={k:v for k,v in row.items() if k not in {'tl','technology','notes'}}
            req(tech==row.get('technology','') and stats==expected and (notes or '')==row.get('notes',''),'workbook matrix mismatch '+fam+' TL'+tl)

def validate_plan(repo:Path):
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.main_subsystem_stabilization_analysis import build_plan,validate_study
    study=repo/'docs/archive/testing/pre-cp165-active/cp127_main_subsystem_tl_stabilization_study_v0_1.json'
    req(validate_study(js(study))==[],'CP127 study schema')
    s=build_plan(repo,study,None)['summary']
    req(s['failedGates']==[] and s['legalBuilds']==9427 and s['generatedVariants']==86584 and s['plannedSubstantiveTrials']==8658400,'CP127 plan')
    req(s['finalBaselineVariants']==74584 and s['tl5Tl6AblationVariants']==4320 and s['tl8EnergyVariants']==7680,'CP127 lane counts')


def validate_checkpoint_surface(repo:Path):
    wrapper=text(repo/'tools/checkpoints/checkpoint-127/apply_checkpoint_127.ps1')
    contract=text(repo/'tools/checkpoints/checkpoint-127/test_checkpoint_127_contract.py')
    for token in (
        'Python self-tests: 170/170 passed.',
        '86,584 variants x 100 trials = 8,658,400 engagements',
        "'--mode','smoke'",
        "'--mode','run'",
        'symmetryComparisons=2250',
        'numericLeafChanges=9',
        'mixedTlShipsExecuted=$false',
        'auxiliaryNumericalStabilizationDeferred=$true',
    ):
        req(token in wrapper,f'wrapper contract missing {token}')
    for token in ('pythonTestsPassed\"] == 170','expectedVariants\"] == 86584','expectedSubstantiveTrials\"] == 8658400','pipeline-smoke/analysis.json','main-subsystem-stabilization-study/analysis.json'):
        req(token in contract,f'repository/evidence contract missing {token}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-127/checkpoint_127_definition.json');req(d['checkpoint']==127 and d['expectedPythonTests']==170 and d['expectedVariants']==86584,'definition')
        req(d.get('pythonDependencyPolicy')=='stdlib-only' and d.get('thirdPartyPythonPackagesAllowed')==[],'CP127 Python dependency policy')
        count=validate_stdlib_only_python_surface(repo)
        print(f'       Validating stdlib-only CP127 Python acceptance surface ({count} files; no third-party packages)...')
        print('       Validating accepted CP126 native evidence and frozen production C#/xUnit surface...');validate_cp126(repo);validate_production_frozen(repo)
        print('       Validating exact nine-leaf main-subsystem numerical change set and movement invariants...');validate_matrix(repo)
        print('       Validating Storyboard/Tech Table/canonical authority and synchronized Concept/workbook/docs...');validate_table(repo);validate_docs(repo)
        print('       Validating CP127 native wrapper and evidence-contract interfaces...');validate_checkpoint_surface(repo)
        print('       Reconstructing CP127 full-map stabilization plan...');validate_plan(repo)
        print('       CP127 preflight: CP126 native evidence preserved; production C#/xUnit surface frozen; exactly 9 numerical leaves changed; STL=TL; Missile Move=TL+1; FTL strategic exception retained; 9,427 legal builds; 86,584 variants; 8,658,400 planned substantive engagements; mixed-TL ships excluded; most AUX tuning deferred.')
        return 0
    except Exception as e:
        print(f'CP127 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
