#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, math, re, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP132_RESULTS_SHA='5b454578e4e24836a9defeabc6309719ab8d9844b679de9c2a94040d21f1a564'
OLD_MANIFEST='docs/validation/evidence/checkpoint-132/CP132_REPOSITORY_SHA256SUMS.txt'

def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'missing {p}'); return p.read_text(encoding='utf-8-sig')
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

def read_xlsx_numerical(path:Path):
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','p':'http://schemas.openxmlformats.org/package/2006/relationships'}
    with zipfile.ZipFile(path) as z:
        wb=ET.fromstring(z.read('xl/workbook.xml')); rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relmap={e.attrib['Id']:e.attrib['Target'].lstrip('/') for e in rels}
        sheets=[]
        for sh in wb.find('x:sheets',ns):
            rid=sh.attrib['{'+ns['r']+'}id']; sheets.append((sh.attrib['name'],relmap[rid]))
        names=[n for n,_ in sheets]
        req(names==['Overview','Lineage Map','Numerical Baseline','Optional Components','CP128 Baseline','CP133 Baseline'],f'workbook sheets {names}')
        root=ET.fromstring(z.read(dict(sheets)['Numerical Baseline']))
        rows=[]
        for row in root.findall('x:sheetData/x:row',ns):
            vals=[None]*5
            for cell in row.findall('x:c',ns):
                ref=cell.attrib.get('r',''); m=re.match(r'([A-E])([0-9]+)$',ref)
                if not m: continue
                idx=ord(m.group(1))-65; typ=cell.attrib.get('t')
                if typ=='inlineStr': vals[idx]=''.join((n.text or '') for n in cell.findall('.//x:t',ns))
                else:
                    v=cell.find('x:v',ns); raw='' if v is None or v.text is None else v.text
                    if typ=='n' and raw:
                        num=float(raw); vals[idx]=int(num) if num.is_integer() else num
                    else: vals[idx]=raw
            rows.append(vals)
    req(len(rows)==181 and rows[0]==['Profile','TL','Technology','Characteristics','Notes'],'workbook numerical shape')
    return rows

def validate_cp132(repo:Path):
    base=repo/'docs/validation/evidence/checkpoint-133/accepted-cp132'
    z=base/'CP132_NATIVE_RESULTS_ORIGINAL.zip'; req(sha(z)==CP132_RESULTS_SHA,'CP132 native result hash')
    s=js(base/'CP132_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==132 and s['failedGates']==[] and s['buildPassed'] is True,'CP132 accepted identity')
    req(s['pythonTestsPassed']==196 and s['xunitPassed']==910 and s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'CP132 accepted gates')
    req(s['canonicalKernelVersion']=='0.1' and s['canonicalDamageModel']=='penetration-hardening-v1','CP132 canonical identity')

def validate_frozen_implementation(repo:Path):
    old=manifest(repo/OLD_MANIFEST)
    for prefix in ('src/','tests/','tools/simulation/'):
        cur=sorted(p.relative_to(repo).as_posix() for p in (repo/prefix.rstrip('/')).rglob('*') if p.is_file() and '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix() and '/__pycache__/' not in '/'+p.relative_to(repo).as_posix())
        exp=sorted(r for r in old if r.startswith(prefix))
        req(cur==exp,f'implementation path drift under {prefix}')
        for rel in exp: req(sha(repo/rel)==old[rel],f'implementation hash drift {rel}')
    for rel in ('docs/Star_Cluster_Game_Concept_v0.7t.docx','docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json'):
        req(sha(repo/rel)==old[rel],f'frozen authority drift {rel}')

def validate_matrix(repo:Path):
    d=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_6.json')
    req(d['checkpoint']==133 and d['schemaVersion'].endswith('v0.6'),'matrix identity')
    req(d['combatModifiers']['directFireApproximateTrackPenaltyPp']==-25 and d['combatModifiers']['directFireExtendedRangePenaltyPp']==-10 and d['combatModifiers']['modifiersStack'] is True,'direct-fire modifiers')
    H=[(35,24),(35,25),(36,26),(36,27),(37,28),(37,29),(38,30),(38,31),(39,32)]
    A=[(0,6,0),(0,8,0),(1,9,0),(1,10,0),(2,10,0),(1,10,1),(1,12,2),(2,12,2),(3,14,3)]
    Sh=[(4,2,1,2,0),(5,2,1,3,0),(6,2,2,2,0),(7,3,2,2,0),(8,2,2,3,0),(8,4,2,2,0),(9,3,2,3,0),(10,4,3,2,1),(12,6,3,2,1)]
    K=[(20,6,0,0,2,3,1),(20,7,0,1,2,3,1),(20,7,0,1,2,4,1),(25,7,0,2,2,4,1),(25,8,0,2,3,5,1),(30,8,0,2,3,6,1),(30,9,0,2,3,6,1),(30,10,0,3,4,7,2),(35,11,0,3,4,8,2)]
    E=[(4,25,2,5,0,0,2),(4,30,2,5,0,0,3),(5,30,2,5,0,0,4),(6,30,2,6,0,0,4),(6,30,2,6,1,0,4),(7,35,2,6,1,0,5),(7,35,2,7,1,0,5),(8,35,4,8,2,0,5),(9,40,4,9,2,0,5)]
    M=[(6,2,8,0,0),(7,3,8,0,0),(7,4,8,0,0),(8,5,9,0,0),(9,6,10,0,0),(10,7,10,0,0),(10,8,11,0,0),(11,9,12,1,0),(12,10,14,1,0)]
    S={2:(7,3,3,0,0,10,10),3:(7,4,3,0,0,10,10),4:(8,5,4,0,0,10,10),5:(9,6,4,0,0,10,10),6:(10,7,4,0,0,10,10),7:(10,8,5,0,0,15,15),8:(11,9,5,1,0,15,15),9:(12,10,6,1,0,15,15)}
    p=d['profiles']
    for i,tl in enumerate(range(1,10)):
        h=p['hull'][str(tl)]; req((h['capacity'],h['hullPoints'])==H[i],f'hull TL{tl}')
        a=p['armor'][str(tl)]; req((a['ap'],a['ai'],a['tacticalRegenerationCapTp'])==A[i],f'armor TL{tl}')
        sh=p['shield'][str(tl)]; tup=(sh['capacity'],sh['baseRecharge'],sh['tacticalRechargePerTp'],sh['tacticalRechargeCapTp'],sh['shieldArmor']); req(tup==Sh[i],f'shield TL{tl}'); req(sh['baseRecharge']+sh['tacticalRechargePerTp']*sh['tacticalRechargeCapTp']>=sh['capacity'],f'shield refill TL{tl}')
        k=p['kinetic_main'][str(tl)]; req((k['accuracyPp'],k['damage'],k['spen'],k['apen'],k['standardRange'],k['maxRange'],k['firingTp'])==K[i] and k['ammo']==100,f'kinetic TL{tl}')
        e=p['energy_main'][str(tl)]; req((e['maxRange'],e['accuracyPp'],e['standardTp'],e['standardDamage'],e['spen'],e['apen'],e['standardRange'])==E[i],f'energy TL{tl}'); req(e['lowTp']==math.ceil(e['standardTp']/2) and e['lowDamage']==math.ceil(e['standardDamage']/2) and e['overloadTp']==math.ceil(e['standardTp']*1.5) and e['overloadDamage']==math.ceil(e['standardDamage']*1.5) and e['overloadAddsStrain'] is True,f'energy modes TL{tl}')
        md=p['missile_delivery'][str(tl)]; mw=p['missile_gp_warhead'][str(tl)]; req((md['range'],md['missileMove'],mw['damage'],mw['spen'],mw['apen'])==M[i] and md['launchTp']==0 and md['flights']==25,f'missile TL{tl}')
        sw=p['missile_swarmer'][str(tl)]
        if tl==1: req(sw['available'] is False,'Swarmer TL1 unavailable')
        else: req((md['range'],md['missileMove'],sw['packetDamage'],sw['spen'],sw['apen'],sw['terminalGuidanceBonusPp'],sw['pdsInterceptPenaltyPp'])==S[tl] and sw['packetCount']==2,f'Swarmer TL{tl}')
    seeds={x['id']:x for x in d['candidateBranchSeeds']}; req(seeds['A_b1']['tl6']['ap']==2 and seeds['A_b1']['tl6']['ai']==12,'A_b1 seed'); req(seeds['E_b1']['numeric']=='TBD' and 'CREW' in seeds['M_b2']['numeric'],'branch seeds')
    req(d['sameTlCalibrationContract']['mandatoryDefenses']==['shield','armor'] and d['sameTlCalibrationContract']['branchProfilesExcludedInitially'] is True,'same-TL contract')
    return d

def validate_table_and_workbook(repo:Path,matrix):
    t=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_8.json'); req(t['checkpoint']==133 and t['schemaVersion'].endswith('v0.8'),'table identity'); req(t['cp133RevisedBaselineSummary']['primaryMatrix']=='technology_numerical_matrix_v0_6.json','table matrix pointer')
    a=js(repo/'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_5.json'); req(a['checkpoint']==133 and a['primaryReferenceMatrix']=='technology_numerical_matrix_v0_6.json' and a['primaryTechnologyTable']=='technology_component_table_v0_8.json','authority pointer'); req(a['storyboardReconciled'] is False and a['balanceCalibrationRun'] is False,'authority boundary')
    rows=read_xlsx_numerical(repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8.xlsx')
    m={(str(r[0]),int(r[1])):(r[2],json.loads(r[3]),r[4]) for r in rows[1:]}
    req(len(m)==180,'workbook numerical rows')
    for fam,tiers in matrix['profiles'].items():
        for tl,row in tiers.items():
            tech,stats,notes=m[(fam,int(tl))]; expected={k:v for k,v in row.items() if k not in {'tl','technology','notes'}}
            req(tech==row.get('technology','') and stats==expected and (notes or '')==row.get('notes',''),f'workbook mismatch {fam} TL{tl}')

def validate_python_surface(repo:Path):
    files=list((repo/'tools/checkpoints/checkpoint-133').glob('*.py'))+[repo/'tools/checkpoints/prepackage_repository_hygiene.py']
    std=set(sys.stdlib_module_names)|{'__future__'}; bad=[]
    for p in files:
        tree=ast.parse(text(p),filename=str(p))
        for n in ast.walk(tree):
            names=[]
            if isinstance(n,ast.Import): names=[a.name.split('.',1)[0] for a in n.names]
            elif isinstance(n,ast.ImportFrom) and n.level==0 and n.module: names=[n.module.split('.',1)[0]]
            for name in names:
                if name not in std: bad.append(f'{p.name}:{getattr(n,"lineno","?")}:{name}')
    req(not bad,'non-stdlib CP133 dependency: '+','.join(bad))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);args=ap.parse_args();repo=Path(args.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-133/checkpoint_133_definition.json'); req(d['checkpoint']==133 and d['declaredSubstantiveTrials']==0 and d['balanceCalibrationRun'] is False,'definition')
        print('       Validating accepted CP132 native provenance...');validate_cp132(repo)
        print('       Verifying production C#/tests/canonical Python kernel, Concept, and Storyboard remain byte-frozen from CP132...');validate_frozen_implementation(repo)
        print('       Validating revised candidate matrix, family invariants, Energy modes, and planned same-TL boundary...');matrix=validate_matrix(repo)
        print('       Validating Technology Table v0.8, canonical candidate authority, and stdlib OOXML workbook synchronization...');validate_table_and_workbook(repo,matrix)
        print('       Validating CP133 checkpoint Python surface remains stdlib-only...');validate_python_surface(repo)
        print('       CP133 preflight passed: CP132 accepted mechanics preserved; 8 selected profiles revised; Storyboard/production/simulation frozen; -25 Approx / -10 extended-range candidate modifiers recorded; Shield+Armor mandatory for planned same-TL calibration; zero Monte Carlo trials.')
        return 0
    except Exception as e:
        print(f'CP133 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
