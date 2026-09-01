from __future__ import annotations
import itertools, json, math
from collections import defaultdict
from pathlib import Path
from typing import Any
from .model import Build, PopulationCell, Pairing, Variant
from .rng import XorShift64

REQUIRED_AXES = ['hull','weapon','reactor','computer','sensor','shield','shieldHardener','armor','ecm','eccm','stl','ftl','pds']
SPACE_ORDER = {'exact_fill':0,'near_fill':1,'underfilled':2}

class StudyError(ValueError):
    pass


_CP165_EXACT_RELOCATIONS = {
    'docs/Star_Cluster_Game_Concept_v0.7x.docx': 'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx',
}
_CP165_RETAINED_ACTIVE_REFERENCES = {
    'docs/design/player_technology/technology_numerical_matrix_v0_9.json',
    'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json',
}
_CP165_RELOCATION_PREFIXES = (
    ('docs/design/player_technology/', 'docs/archive/player_technology/pre-cp165-active/'),
    ('docs/design/testing/', 'docs/archive/testing/pre-cp165-active/'),
    ('docs/design/ai/', 'docs/archive/ai/pre-cp165-active/'),
)

def canonical_relocated_reference(value: str) -> str:
    """Resolve a pre-CP165 logical document reference without rewriting frozen evidence."""
    normalized=value.replace('\\','/')
    if normalized in _CP165_EXACT_RELOCATIONS:return _CP165_EXACT_RELOCATIONS[normalized]
    if normalized in _CP165_RETAINED_ACTIVE_REFERENCES:return value
    for old_prefix,archive_prefix in _CP165_RELOCATION_PREFIXES:
        if normalized.startswith(old_prefix):return archive_prefix+normalized[len(old_prefix):]
    return value

def canonicalize_relocated_references(value: Any) -> Any:
    if isinstance(value,str):return canonical_relocated_reference(value)
    if isinstance(value,list):return [canonicalize_relocated_references(v) for v in value]
    if isinstance(value,dict):return {k:canonicalize_relocated_references(v) for k,v in value.items()}
    return value

def resolve_relocated_path(path: Path) -> Path:
    normalized=path.as_posix()
    for old_ref,archive_ref in _CP165_EXACT_RELOCATIONS.items():
        marker='/'+old_ref
        if normalized.endswith(marker):
            candidate=Path(normalized[:-len(marker)]+'/'+archive_ref)
            if candidate.exists():return candidate
    if path.exists():return path
    for old_prefix,archive_prefix in _CP165_RELOCATION_PREFIXES:
        marker='/'+old_prefix
        if marker in normalized:
            candidate=Path(normalized.replace(marker,'/'+archive_prefix,1))
            if candidate.exists():return candidate
    return path

def load_json(path: Path) -> dict[str, Any]:
    resolved=resolve_relocated_path(path)
    try:
        return canonicalize_relocated_references(json.loads(resolved.read_text(encoding='utf-8-sig')))
    except Exception as exc:
        raise StudyError(f'cannot read JSON {path}: {exc}') from exc


def require_type(obj: dict[str, Any], key: str, typ, *, allow_none=False):
    if key not in obj:
        raise StudyError(f'missing required field {key}')
    value=obj[key]
    if allow_none and value is None:
        return value
    if typ is int and isinstance(value, bool):
        raise StudyError(f'{key} must be int, not bool')
    if not isinstance(value, typ):
        raise StudyError(f'{key} must be {getattr(typ,"__name__",typ)}, got {type(value).__name__}')
    return value


def validate_study(doc: dict[str, Any], *, expected_id: str|None=None) -> list[str]:
    errors=[]
    def check(fn):
        try: fn()
        except StudyError as e: errors.append(str(e))
    check(lambda: require_type(doc,'schemaVersion',str))
    check(lambda: require_type(doc,'checkpoint',str))
    check(lambda: require_type(doc,'id',str))
    check(lambda: require_type(doc,'coverageMode',str))
    check(lambda: require_type(doc,'masterSeed',int))
    check(lambda: require_type(doc,'trialsPerVariant',int))
    check(lambda: require_type(doc,'expectedRawCombinationCount',int))
    check(lambda: require_type(doc,'expectedLegalBuildCount',int))
    if expected_id and doc.get('id') != expected_id:
        errors.append(f'id mismatch: expected {expected_id}, got {doc.get("id")}')
    if doc.get('schemaVersion') != 'star-cluster-cross-tl-build-permutation-v8':
        errors.append('Python research runner requires schemaVersion star-cluster-cross-tl-build-permutation-v8')
    if doc.get('checkpoint') not in ('103','104'):
        errors.append('v8 checkpoint must be the string "103" or "104"')
    if doc.get('researchSimulationEngine') != 'starcluster-python-research-v1':
        errors.append('CP103 v8 researchSimulationEngine must be starcluster-python-research-v1')
    if doc.get('researchSimulationAuthority') != 'screening_not_gameplay_authority':
        errors.append('CP103 v8 researchSimulationAuthority must be screening_not_gameplay_authority')
    if doc.get('pythonRuntimeMajorMinor') != '3.13':
        errors.append('CP103 v8 pythonRuntimeMajorMinor must be 3.13')
    if doc.get('coverageMode') not in ('integration_screening','diagnostic_overlay'):
        errors.append('coverageMode must be integration_screening or diagnostic_overlay')
    axes=doc.get('axes')
    if not isinstance(axes,list):
        errors.append('axes must be an array')
    else:
        ids=[a.get('id') for a in axes if isinstance(a,dict)]
        if ids != REQUIRED_AXES:
            errors.append(f'axes must appear in canonical order {REQUIRED_AXES}; got {ids}')
        for axis in axes:
            if not isinstance(axis,dict): errors.append('axis entry must be object'); continue
            if not isinstance(axis.get('id'),str) or not isinstance(axis.get('code'),str):
                errors.append('axis id/code must be strings')
            opts=axis.get('options')
            if not isinstance(opts,list) or not opts:
                errors.append(f'axis {axis.get("id")} must contain options'); continue
            oids=[]
            for o in opts:
                if not isinstance(o,dict): errors.append(f'axis {axis.get("id")} option must be object'); continue
                for k,t in [('id',str),('technologyLevel',int),('space',int)]:
                    if k not in o or not isinstance(o[k],t) or (t is int and isinstance(o[k],bool)):
                        errors.append(f'axis {axis.get("id")} option {o.get("id")} field {k} has wrong type')
                oids.append(o.get('id'))
            if len(oids)!=len(set(oids)): errors.append(f'axis {axis.get("id")} has duplicate option ids')
    if doc.get('coverageMode')=='integration_screening':
        s=doc.get('stratifiedPairingSelection')
        if not isinstance(s,dict) or s.get('enabled') is not True:
            errors.append('integration_screening requires enabled stratifiedPairingSelection')
        else:
            for k in ['seed','expectedBasePairCount','expectedSampleCount','maxAttempts','nearDistanceMaximum','equalLowAdvancedMaximum','targetBasePairBudget','minimumPerPopulationCell','maximumPerPopulationCell','expectedDiversityBasePairCount','expectedDiversitySampleCount']:
                if not isinstance(s.get(k),int) or isinstance(s.get(k),bool): errors.append(f'stratifiedPairingSelection.{k} must be int')
            if not isinstance(s.get('allocationExponent'),(int,float)) or isinstance(s.get('allocationExponent'),bool):
                errors.append('stratifiedPairingSelection.allocationExponent must be numeric')
    if doc.get('coverageMode')=='diagnostic_overlay':
        if doc.get('stratifiedPairingSelection',{}).get('enabled') not in (False,None):
            errors.append('diagnostic_overlay must not enable stratifiedPairingSelection')
    return errors


def axes_map(doc):
    return {a['id']:{o['id']:o for o in a['options']} for a in doc['axes']}


def _ew_ratings(opt):
    if isinstance(opt.get('ewRatings'),list): return [int(x) for x in opt['ewRatings']]
    if isinstance(opt.get('ewRating'),int): return [opt['ewRating']]
    return []


def _advanced_count(sel: dict[str,dict[str,Any]]) -> int:
    count=0
    for aid,count_field in [('weapon','mainWeaponCount'),('reactor','reactorCount')]:
        o=sel[aid]
        if o['technologyLevel']>=3: count += int(o.get(count_field,1) or 1)
    for aid in ['computer','sensor','shield','armor','hull','shieldHardener','stl','pds']:
        o=sel[aid]
        if o.get('installed',True) is not False and o['technologyLevel']>=3: count += 1
    for aid in ['ecm','eccm']:
        o=sel[aid]
        if o.get('installed',True) is not False and o['technologyLevel']>=3:
            count += len(_ew_ratings(o))
    return count


def _info_count(sel):
    count=0
    for aid in ['computer','sensor']:
        o=sel[aid]
        if o.get('installed',True) is not False and o['technologyLevel']>=3: count += 1
    for aid in ['ecm','eccm']:
        o=sel[aid]
        if o.get('installed',True) is not False and o['technologyLevel']>=3: count += len(_ew_ratings(o))
    return count


def _space_class(used,cap,selection):
    headroom=selection.get('nearFillHeadroomMaximum') if isinstance(selection,dict) else None
    if isinstance(headroom,int) and headroom>=0: near_min=max(0,cap-headroom)
    else: near_min=(selection or {}).get('nearFillMinimumUsedSpace',max(0,cap-3))
    if used==cap: return 'exact_fill'
    if near_min <= used < cap: return 'near_fill'
    return 'underfilled'


def resolve_build(doc, selection: dict[str,str], amap=None) -> Build:
    amap=amap or axes_map(doc)
    sel={aid:amap[aid][oid] for aid,oid in selection.items()}
    used=sum(int(o.get('space',0)) for o in sel.values()) + int(doc.get('fixedShellSpace',0))
    cap=int(sel['hull'].get('installationSpaceCapacity',doc.get('totalInstallationSpace',0)))
    main=sum(int(o.get('mainWeaponCount',0) or 0) for o in sel.values())
    reactors=sum(int(o.get('reactorCount',0) or 0) for o in sel.values())
    sensor_installed=sel['sensor'].get('installed',True) is not False
    shield_installed=sel['shield'].get('installed',True) is not False
    hard=sel['shieldHardener'].get('installed',False) is True
    if used>cap or main<1 or reactors<1 or not sensor_installed or (hard and not shield_installed):
        raise StudyError('named recipe is not a legal combat build')
    installed=[o for o in sel.values() if o.get('installed',True) is not False]
    max_tl=max(o['technologyLevel'] for o in installed)
    ewr=len(_ew_ratings(sel['ecm']))>1 or len(_ew_ratings(sel['eccm']))>1
    dup=main>1 or reactors>1
    comp='combined-duplication' if ewr and dup else 'weapon-reactor-duplication' if dup else 'ew-redundancy' if ewr else 'single-no-ew-redundancy'
    sc=_space_class(used,cap,doc.get('stratifiedPairingSelection') or {})
    bid='b-'+'_'.join(a['code']+'-'+selection[a['id']] for a in doc['axes'])
    return Build(bid,dict(selection),used,cap,max_tl,_advanced_count(sel),_info_count(sel),main,reactors,sel['weapon']['family'],comp,sc,sel)


def enumerate_builds(doc: dict[str,Any]) -> tuple[int,list[Build],dict[str,Build]]:
    amap=axes_map(doc)
    raw=math.prod(len(a['options']) for a in doc['axes'])
    named={}
    if doc.get('coverageMode')=='diagnostic_overlay':
        for r in doc.get('namedRecipes',[]):
            b=resolve_build(doc,r['selections'],amap)
            named[r['id']]=b
        unique={b.id:b for b in named.values()}
        return raw,sorted(unique.values(),key=lambda b:b.id),named
    axes=doc['axes']; option_lists=[a['options'] for a in axes]
    legal=[]
    for combo in itertools.product(*option_lists):
        sel={a['id']:o for a,o in zip(axes,combo)}
        used=sum(int(o.get('space',0)) for o in combo)+int(doc.get('fixedShellSpace',0))
        cap=int(sel['hull'].get('installationSpaceCapacity',doc.get('totalInstallationSpace',0)))
        if used>cap: continue
        main=sum(int(o.get('mainWeaponCount',0) or 0) for o in combo)
        reactors=sum(int(o.get('reactorCount',0) or 0) for o in combo)
        if main<1 or reactors<1 or sel['sensor'].get('installed',True) is False: continue
        if sel['shieldHardener'].get('installed',False) is True and sel['shield'].get('installed',True) is False: continue
        selection={a['id']:o['id'] for a,o in zip(axes,combo)}
        legal.append(resolve_build(doc,selection,amap))
    for r in doc.get('namedRecipes',[]):
        named[r['id']]=resolve_build(doc,r['selections'],amap)
    legal.sort(key=lambda b:b.id)
    return raw,legal,named


def progression_magnitude(a:Build,b:Build,sel):
    d=abs(a.advanced_count-b.advanced_count)
    if d==0: return 'equal_low' if a.advanced_count<=int(sel.get('equalLowAdvancedMaximum',3)) else 'equal_high'
    return 'near' if d<=int(sel.get('nearDistanceMaximum',2)) else 'far'


def composition_pair(a:Build,b:Build):
    ew=a.composition in ('ew-redundancy','combined-duplication') or b.composition in ('ew-redundancy','combined-duplication')
    dup=a.composition in ('weapon-reactor-duplication','combined-duplication') or b.composition in ('weapon-reactor-duplication','combined-duplication')
    return 'combined-duplication' if ew and dup else 'weapon-reactor-duplication' if dup else 'ew-redundancy' if ew else 'single-no-ew-redundancy'


def space_pair(a:Build,b:Build):
    x,y=a.space_class,b.space_class
    if SPACE_ORDER[x]>SPACE_ORDER[y]: x,y=y,x
    return x+'-'+y


def cell_key(a:Build,b:Build,sel):
    return '~'.join((composition_pair(a,b),progression_magnitude(a,b,sel),space_pair(a,b)))


def population_cells(doc,builds):
    sel=doc['stratifiedPairingSelection']
    buckets=defaultdict(int)
    for b in builds:
        ewr=b.composition in ('ew-redundancy','combined-duplication')
        dup=b.composition in ('weapon-reactor-duplication','combined-duplication')
        buckets[(ewr,dup,b.advanced_count,b.space_class)] += 1
    items=sorted(buckets.items(),key=lambda kv:(kv[0][0],kv[0][1],kv[0][2],kv[0][3]))
    counts=defaultdict(int)
    for i,(ka,ca) in enumerate(items):
        for j in range(i,len(items)):
            kb,cb=items[j]
            n=ca*(ca-1)//2 if i==j else ca*cb
            if not n: continue
            ewa,dupa,aa,sa=ka; ewb,dupb,ab,sb=kb
            ew=ewa or ewb; dup=dupa or dupb
            comp='combined-duplication' if ew and dup else 'weapon-reactor-duplication' if dup else 'ew-redundancy' if ew else 'single-no-ew-redundancy'
            d=abs(aa-ab)
            prog=('equal_low' if aa<=sel['equalLowAdvancedMaximum'] else 'equal_high') if d==0 else ('near' if d<=sel['nearDistanceMaximum'] else 'far')
            x,y=sa,sb
            if SPACE_ORDER[x]>SPACE_ORDER[y]: x,y=y,x
            counts[f'{comp}~{prog}~{x}-{y}'] += n
    total=len(builds)*(len(builds)-1)//2
    configured=[]
    for comp in sel['compositionClasses']:
      for prog in sel['progressionMagnitudeStrata']:
       for sp in sel['spacePairStrata']:
        k=f'{comp}~{prog}~{sp}'; n=counts.get(k,0)
        configured.append(PopulationCell(k,comp,prog,sp,n,n/total if total else 0.0))
    if sum(c.population for c in configured)!=total: raise StudyError('population-cell total mismatch')
    if any(c.population<=0 for c in configured): raise StudyError('configured CP103 population cell is empty')
    return {c.key:c for c in configured}


def allocate_quotas(cells:dict[str,PopulationCell],sel):
    ordered=sorted(cells.values(),key=lambda c:c.key)
    minimum=int(sel['minimumPerPopulationCell']); maximum=int(sel['maximumPerPopulationCell']); budget=int(sel['targetBasePairBudget'])
    quotas={c.key:minimum for c in ordered}; remaining=budget-minimum*len(ordered)
    weights=[c.population**float(sel['allocationExponent']) for c in ordered]; total=sum(weights)
    frac=[]; allocated=0
    for c,w in zip(ordered,weights):
        exact=remaining*w/total
        floor=min(maximum-minimum,math.floor(exact)); quotas[c.key]+=floor; allocated+=floor
        frac.append((c.key,exact-math.floor(exact),c.population))
    residual=remaining-allocated
    frac.sort(key=lambda x:(-x[1],-x[2],x[0]))
    while residual:
        progressed=False
        for key,_,_ in frac:
            if quotas[key]>=maximum: continue
            quotas[key]+=1; residual-=1; progressed=True
            if not residual: break
        if not progressed: raise StudyError('adaptive quota allocation could not satisfy budget')
    return quotas


def secondary_key(a:Build,b:Build,sel):
    fam='-'.join(sorted((a.family,b.family)))
    d=abs(a.info_advanced_count-b.info_advanced_count)
    band='equal' if d==0 else 'near' if d<=int(sel.get('informationControlNearDistanceMaximum',2)) else 'far'
    return fam+'~'+band


def sample_primary(doc,builds,cells):
    sel=doc['stratifiedPairingSelection']; quotas=allocate_quotas(cells,sel)
    rng=XorShift64(int(sel['seed'])); counts={k:0 for k in cells}; selected=set(); pairs=[]; attempts=0
    target=int(sel['expectedBasePairCount'])
    while len(pairs)//2 < target and attempts<int(sel['maxAttempts']):
        attempts+=1
        ai=rng.next_u64()%len(builds); bi=rng.next_u64()%len(builds)
        if ai==bi: continue
        a,b=builds[ai],builds[bi]
        if a.id>b.id: a,b=b,a
        k=cell_key(a,b,sel)
        if counts[k]>=quotas[k]: continue
        uk=a.id+'|'+b.id
        if uk in selected: continue
        selected.add(uk); counts[k]+=1; ordinal=counts[k]
        bundle=f'adaptive-{composition_pair(a,b)}-{progression_magnitude(a,b,sel)}-{space_pair(a,b)}-{ordinal:02d}'
        cell=cells[k]; weight=cell.population/quotas[k]
        pairs.append(Pairing(bundle+'-forward',bundle,'forward','statistical',a,b,k,cell.population,weight))
        pairs.append(Pairing(bundle+'-reverse',bundle,'reverse','statistical',b,a,k,cell.population,weight))
    if len(pairs)//2 != target: raise StudyError(f'adaptive sampler stopped at {len(pairs)//2}/{target} after {attempts} attempts')
    # diversity overlay
    top=sorted(cells.values(),key=lambda c:(-c.population,c.key))[:int(sel['diversityOverlayTopCellCount'])]
    topkeys={c.key for c in top}; oc={k:0 for k in topkeys}
    secondary={k:{secondary_key(p.side_a,p.side_b,sel) for p in pairs if p.source=='statistical' and p.orientation=='forward' and p.population_cell==k} for k in topkeys}
    overlay_rng=XorShift64(int(sel['seed']) ^ 0xD1B54A32D192ED03); overlay_target=int(sel['expectedDiversityBasePairCount']); overlay_count=0; overlay_attempts=0
    def add_overlay(a,b,k):
        nonlocal overlay_count
        oc[k]+=1; overlay_count+=1; ordinal=oc[k]
        bundle=f'diversity-{composition_pair(a,b)}-{progression_magnitude(a,b,sel)}-{space_pair(a,b)}-{ordinal:02d}'
        cell=cells[k]
        pairs.append(Pairing(bundle+'-forward',bundle,'forward','diversity',a,b,k,cell.population,0.0))
        pairs.append(Pairing(bundle+'-reverse',bundle,'reverse','diversity',b,a,k,cell.population,0.0))
    while overlay_count<overlay_target and overlay_attempts<int(sel['maxAttempts']):
        overlay_attempts+=1; ai=overlay_rng.next_u64()%len(builds); bi=overlay_rng.next_u64()%len(builds)
        if ai==bi: continue
        a,b=builds[ai],builds[bi]
        if a.id>b.id: a,b=b,a
        k=cell_key(a,b,sel)
        if k not in topkeys or oc[k]>=int(sel['diversityOverlayPairsPerCell']): continue
        uk=a.id+'|'+b.id
        if uk in selected: continue
        sk=secondary_key(a,b,sel)
        if sk in secondary[k]: continue
        selected.add(uk); secondary[k].add(sk); add_overlay(a,b,k)
    fallback=0
    while overlay_count<overlay_target and fallback<int(sel['maxAttempts']):
        fallback+=1; ai=overlay_rng.next_u64()%len(builds); bi=overlay_rng.next_u64()%len(builds)
        if ai==bi: continue
        a,b=builds[ai],builds[bi]
        if a.id>b.id: a,b=b,a
        k=cell_key(a,b,sel)
        if k not in topkeys or oc[k]>=int(sel['diversityOverlayPairsPerCell']): continue
        uk=a.id+'|'+b.id
        if uk in selected: continue
        selected.add(uk); secondary[k].add(secondary_key(a,b,sel)); add_overlay(a,b,k)
    if overlay_count!=overlay_target: raise StudyError('diversity overlay did not fill')
    return pairs,quotas,attempts,overlay_attempts+fallback


def named_pairings(doc,named):
    pairs=[]
    for group in doc.get('pairingGroups',[]):
        for a_id in group.get('sideARecipes',[]):
            for b_id in group.get('sideBRecipes',[]):
                a=named[a_id]; b=named[b_id]
                bundle='named-'+group['id']
                pairs.append(Pairing(bundle,bundle,'declared','named',a,b,'',0,0.0))
    return pairs


def variants_from_pairs(doc,pairs):
    out=[]; n=1
    for p in pairs:
        for g in doc['geometries']:
            out.append(Variant(f'{doc["variantIdPrefix"]}-{n:04d}-{g["id"]}',p.id,p.bundle_id,p.orientation,p.source,g['movementOrder'],int(g['initialRangeHexes']),p.side_a,p.side_b,p.population_cell,p.population_count,p.representative_weight))
            n+=1
    return out


def build_study(doc):
    raw,builds,named=enumerate_builds(doc)
    if raw!=doc['expectedRawCombinationCount']: raise StudyError(f'raw count {raw} != expected {doc["expectedRawCombinationCount"]}')
    if len(builds)!=doc['expectedLegalBuildCount']: raise StudyError(f'legal build count {len(builds)} != expected {doc["expectedLegalBuildCount"]}')
    counts={k:sum(b.space_class==k for b in builds) for k in ('exact_fill','near_fill','underfilled')}
    for k,field in [('exact_fill','expectedExactFillBuildCount'),('near_fill','expectedNearFillBuildCount'),('underfilled','expectedUnderfilledBuildCount')]:
        if counts[k]!=doc[field]: raise StudyError(f'{k} {counts[k]} != expected {doc[field]}')
    if doc['coverageMode']=='integration_screening':
        cells=population_cells(doc,builds); statistical,quotas,attempts,overlay_attempts=sample_primary(doc,builds,cells); named_pairs=named_pairings(doc,named); pairs=statistical+named_pairs
        variants=variants_from_pairs(doc,pairs)
        if len(statistical)!=doc['expectedStratifiedLogicalPairingCount']: raise StudyError('stratified logical pairing count mismatch')
        if len(named_pairs)!=doc['expectedNamedLogicalPairingCount']: raise StudyError('named logical pairing count mismatch')
        if len(pairs)!=doc['expectedLogicalPairingCount'] or len(variants)!=doc['expectedGeneratedVariantCount']: raise StudyError('generated pairing/variant count mismatch')
        return {'raw':raw,'builds':builds,'named':named,'cells':cells,'quotas':quotas,'pairs':pairs,'variants':variants,'sample_attempts':attempts,'diversity_attempts':overlay_attempts,'space_counts':counts}
    pairs=named_pairings(doc,named); variants=variants_from_pairs(doc,pairs)
    if len(named)!=doc['expectedNamedRecipeCount']: raise StudyError('named recipe count mismatch')
    if len(pairs)!=doc['expectedLogicalPairingCount'] or len(variants)!=doc['expectedGeneratedVariantCount']: raise StudyError('overlay pairing/variant count mismatch')
    return {'raw':raw,'builds':builds,'named':named,'cells':{},'quotas':{},'pairs':pairs,'variants':variants,'sample_attempts':0,'diversity_attempts':0,'space_counts':counts}
