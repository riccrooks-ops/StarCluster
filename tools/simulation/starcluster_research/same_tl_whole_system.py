from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import statistics
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, fields, replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable

from .canonical_combat import FULL_MAP_GEOMETRY, aggregate_full_map_variant, mirror_equivalent, run_trial_full_map
from .current_working_combat import (
    apu_profile,
    authority_identity,
    aux_id,
    execution_coverage,
    load_current_working_matrix,
)
from .ecology import EcologyBuild, EcologyVariant, SideTelemetry, UTILITY_COMBAT_DOCTRINE
from .rng import derive_seed
from .study import load_json

SCHEMA = "star-cluster-cp166-same-tl-whole-system-diagnostic-v0.1"
WEAPON_CODES = ("K", "E", "GP", "SW")
PDS_CODES = ("NONE", "K", "E", "AMM")
BINARY_AUX = (
    "shield_battery",
    "shield_booster",
    "shield_hardener",
    "ablative_armor",
    "energized_armor",
    "crystalline_armor",
    "field_stabilizer",
    "repair_drone_bay",
)
SHIELD_AUX = {"shield_battery", "shield_booster", "shield_hardener", "field_stabilizer"}
MAG_BY_WEAPON = {"K": "kinetic_magazine", "GP": "missile_magazine", "SW": "missile_magazine"}
EXPECTED_SKELETONS_BY_TL = {1:267,2:788,3:1616,4:1616,5:3816,6:9728,7:25712,8:25712,9:31952}


@dataclass(frozen=True, slots=True)
class ArchitectureSkeleton:
    id: str
    tl: int
    weapon: str
    main_count: int
    reactor_count: int
    shield: bool
    ecm: bool
    eccm: bool
    pds: str
    aux_flags: tuple[str, ...]
    capacity: int
    used_without_stacks: int
    free_for_stacks: int


@dataclass(frozen=True, slots=True)
class ExecutableArchitecture:
    id: str
    skeleton_id: str
    tl: int
    weapon: str
    main_count: int
    reactor_count: int
    shield: bool
    ecm: bool
    eccm: bool
    pds: str
    aux_flags: tuple[str, ...]
    apu_count: int
    magazine_count: int
    capacity: int
    used_space: int
    free_space: int

    @property
    def ew_state(self) -> str:
        return "BOTH" if self.ecm and self.eccm else "ECM" if self.ecm else "ECCM" if self.eccm else "NONE"

    @property
    def armor_branch(self) -> str:
        return "CRYSTALLINE" if "crystalline_armor" in self.aux_flags else "MAINLINE"


@dataclass(frozen=True, slots=True)
class VariantMeta:
    pair_id: str
    build1_id: str
    build2_id: str
    build1_weapon: str
    build2_weapon: str
    side_a_physical: str
    side_b_physical: str
    side_a_build_id: str
    side_b_build_id: str
    orientation: str


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA: errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 166 or int(doc.get("baseCheckpoint", 0)) != 165: errors.append("checkpoint")
    if doc.get("population") != "pure_same_tl_current_working_effect_distinct": errors.append("population")
    if doc.get("combatDoctrine") != UTILITY_COMBAT_DOCTRINE: errors.append("combatDoctrine")
    if int(doc.get("representativesPerTl", 0)) != 28: errors.append("representativesPerTl")
    if int(doc.get("trialsPerVariant", 0)) != 200: errors.append("trialsPerVariant")
    if int(doc.get("monotonicityTrialsPerVariant", 0)) != 250: errors.append("monotonicityTrialsPerVariant")
    if doc.get("tlRange") != list(range(1,10)): errors.append("tlRange")
    if doc.get("mixedTlShipsExecuted") is not False: errors.append("mixedTlShipsExecuted")
    if doc.get("differentTlCombatsExecuted") is not False: errors.append("differentTlCombatsExecuted")
    if doc.get("tuningAllowed") is not False or doc.get("automaticPromotion") is not False: errors.append("promotionBoundary")
    expected = doc.get("expected", {})
    checks = {
        "skeletons": sum(EXPECTED_SKELETONS_BY_TL.values()),
        "representatives": 28 * 9,
        "pairGroups": (28 * 29 // 2) * 9,
        "combatVariants": (28 * 29 // 2) * 4 * 9,
        "substantiveCombatTrials": (28 * 29 // 2) * 4 * 9 * 200,
        "monotonicityVariants": 4 * 2 * 4 * 9,
        "monotonicityCombatTrials": 4 * 2 * 4 * 9 * 250,
        "totalDiagnosticCombatTrials": (28 * 29 // 2) * 4 * 9 * 200 + 4 * 2 * 4 * 9 * 250,
        "effectDistinctStackCombinations": 635428,
    }
    for key, value in checks.items():
        if int(expected.get(key, -1)) != value: errors.append("expected." + key)
    return errors


def _weapon_family(code: str) -> str:
    return "Kinetic" if code == "K" else "Energy" if code == "E" else "Missile"


def _weapon_profile_key(code: str) -> str:
    return "kinetic_main" if code == "K" else "energy_main" if code == "E" else "missile_delivery"


def _pds_profile_key(code: str) -> str | None:
    return None if code == "NONE" else {"K":"kinetic_pds","E":"energy_pds","AMM":"amm_pds"}[code]


def _available_weapons(matrix, tl: int) -> tuple[str, ...]:
    return ("K","E","GP","SW") if bool(matrix.p("missile_swarmer", tl).get("available", False)) else ("K","E","GP")


def _available_aux(matrix, tl: int, shield: bool) -> tuple[str, ...]:
    out=[]
    for cid in BINARY_AUX:
        if aux_id(matrix, cid, tl) is None: continue
        if cid in SHIELD_AUX and not shield: continue
        out.append(cid)
    return tuple(out)


def _fixed_core_space(matrix, tl: int) -> int:
    return sum(int(matrix.p(k, tl).get("space", 0)) for k in ("stl","ftl","computer","sensor"))


def _base_space(matrix, tl: int, weapon: str, main_count: int, reactor_count: int,
                shield: bool, ecm: bool, eccm: bool, pds: str) -> int:
    total = _fixed_core_space(matrix, tl)
    total += main_count * int(matrix.p(_weapon_profile_key(weapon), tl)["space"])
    total += reactor_count * int(matrix.p("reactor", tl)["space"])
    if shield: total += int(matrix.p("shield", tl)["space"])
    if ecm: total += int(matrix.p("ecm", tl)["space"])
    if eccm: total += int(matrix.p("eccm", tl)["space"])
    pk = _pds_profile_key(pds)
    if pk: total += int(matrix.p(pk, tl)["space"])
    return total


def enumerate_skeletons(matrix, tl: int) -> list[ArchitectureSkeleton]:
    capacity = int(matrix.capacity(tl))
    rows: list[ArchitectureSkeleton] = []
    for weapon in _available_weapons(matrix, tl):
        for main_count in range(1, 4):
            for reactor_count in range(1, 4):
                for shield, ecm, eccm, pds in itertools.product((False, True), (False, True), (False, True), PDS_CODES):
                    used = _base_space(matrix, tl, weapon, main_count, reactor_count, shield, ecm, eccm, pds)
                    if used > capacity: continue
                    available = _available_aux(matrix, tl, shield)
                    for bits in itertools.product((False, True), repeat=len(available)):
                        flags = tuple(cid for cid, enabled in zip(available, bits) if enabled)
                        aux_space = sum(int(matrix.cp158_aux_profiles[aux_id(matrix, cid, tl)]["space"]) for cid in flags)
                        total = used + aux_space
                        if total > capacity: continue
                        mask = ".".join(x.replace("_", "-") for x in flags) if flags else "none"
                        sid = f"S{tl}-{weapon}-M{main_count}R{reactor_count}-S{int(shield)}-EW{int(ecm)}{int(eccm)}-P{pds}-AUX[{mask}]"
                        rows.append(ArchitectureSkeleton(sid,tl,weapon,main_count,reactor_count,shield,ecm,eccm,pds,flags,capacity,total,capacity-total))
    rows.sort(key=lambda x:x.id)
    return rows


def _stack_solution_count(s: ArchitectureSkeleton) -> int:
    """Exact APU/magazine integer combinations represented by one skeleton."""
    free=s.free_for_stacks
    if s.weapon not in MAG_BY_WEAPON:
        return free//2 + 1
    return sum((free - 2*a) + 1 for a in range(free//2 + 1))


def _candidate_stack_pairs(s: ArchitectureSkeleton) -> tuple[tuple[int,int], ...]:
    free=s.free_for_stacks; pairs={(0,0)}
    max_apu=free//2
    for n in (1,2,3,max_apu):
        if n>=0 and 2*n<=free: pairs.add((n,0))
    if s.weapon in MAG_BY_WEAPON:
        max_mag=free
        if max_mag>=1:pairs.add((0,1));pairs.add((0,max_mag))
        if free>=3:pairs.add((1,1))
        # Preserve a mixed endurance/power extreme without exploding the census.
        if max_apu>=1:
            rem=free-2*max_apu
            if rem>0:pairs.add((max_apu,rem))
    return tuple(sorted(pairs))


def _arch_from(s: ArchitectureSkeleton, apu_count: int, magazine_count: int) -> ExecutableArchitecture:
    used=s.used_without_stacks + apu_count*2 + magazine_count
    if used>s.capacity: raise ValueError("illegal stack materialization")
    digest=hashlib.sha1(s.id.encode()).hexdigest()[:8]
    aid=f"WS166-TL{s.tl}-{s.weapon}-M{s.main_count}R{s.reactor_count}-S{int(s.shield)}-EW{int(s.ecm)}{int(s.eccm)}-P{s.pds}-U{apu_count}-G{magazine_count}-{digest}"
    return ExecutableArchitecture(aid,s.id,s.tl,s.weapon,s.main_count,s.reactor_count,s.shield,s.ecm,s.eccm,s.pds,s.aux_flags,apu_count,magazine_count,s.capacity,used,s.capacity-used)


def candidate_reservoir(skeletons: list[ArchitectureSkeleton], limit: int = 5000) -> list[ExecutableArchitecture]:
    # Always include every low-complexity skeleton base plus deterministic stack
    # extremes sampled by stable hash. This is a selection reservoir only; the
    # census itself remains exhaustive at skeleton/stack-combination level.
    all_candidates: list[ExecutableArchitecture] = []
    for s in skeletons:
        for apu,mag in _candidate_stack_pairs(s):
            all_candidates.append(_arch_from(s,apu,mag))
    if len(all_candidates)<=limit:return all_candidates
    ranked=sorted(all_candidates,key=lambda a:hashlib.sha256(a.id.encode()).hexdigest())
    # Keep exact simple/base anchors from every major core signature in addition
    # to the hash reservoir.
    simple=[a for a in all_candidates if a.apu_count==0 and a.magazine_count==0 and not a.aux_flags and a.main_count==1 and a.reactor_count==1]
    chosen={a.id:a for a in simple}
    for a in ranked:
        if len(chosen)>=limit:break
        chosen.setdefault(a.id,a)
    return sorted(chosen.values(),key=lambda a:a.id)


def _complexity(a: ExecutableArchitecture) -> tuple[Any,...]:
    return (len(a.aux_flags)+a.apu_count+a.magazine_count, abs(a.main_count-1)+abs(a.reactor_count-1), -a.free_space, a.id)


def _feature_vector(a: ExecutableArchitecture) -> tuple[float,...]:
    w=[1.0 if a.weapon==x else 0.0 for x in WEAPON_CODES]
    p=[1.0 if a.pds==x else 0.0 for x in PDS_CODES]
    aux=[1.0 if x in a.aux_flags else 0.0 for x in BINARY_AUX]
    return tuple(w+[a.main_count/3,a.reactor_count/3,float(a.shield),float(a.ecm),float(a.eccm)]+p+aux+[min(a.apu_count,4)/4,min(a.magazine_count,4)/4,a.used_space/a.capacity])


def _distance(a: ExecutableArchitecture,b: ExecutableArchitecture)->float:
    va=_feature_vector(a);vb=_feature_vector(b)
    return sum((x-y)*(x-y) for x,y in zip(va,vb))


def _best(cands: list[ExecutableArchitecture], predicate, selected: set[str], key=None) -> ExecutableArchitecture|None:
    pool=[a for a in cands if a.id not in selected and predicate(a)]
    if not pool:return None
    return min(pool,key=key or _complexity)


def select_representatives(matrix, tl: int, count: int = 28, *, skeletons: list[ArchitectureSkeleton] | None = None) -> list[ExecutableArchitecture]:
    skeletons = skeletons if skeletons is not None else enumerate_skeletons(matrix,tl)
    reservoir=candidate_reservoir(skeletons,5000)
    # Anchor search must see stack extremes that may have fallen outside the hash reservoir.
    stack_extremes=[]
    for sk in skeletons:
        pairs=_candidate_stack_pairs(sk)
        for apu,mag in pairs:
            if apu==sk.free_for_stacks//2 or (sk.weapon in MAG_BY_WEAPON and mag==sk.free_for_stacks):
                stack_extremes.append(_arch_from(sk,apu,mag))
    all_for_anchors={a.id:a for a in reservoir}
    for a in stack_extremes:all_for_anchors.setdefault(a.id,a)
    anchors=list(all_for_anchors.values()); selected: list[ExecutableArchitecture]=[]; seen:set[str]=set()

    weapons=_available_weapons(matrix,tl)
    base=count//len(weapons); rem=count%len(weapons)
    quota={w:base+(1 if i<rem else 0) for i,w in enumerate(weapons)}
    weapon_count={w:0 for w in weapons}

    def add(a):
        if a is not None and a.id not in seen:
            selected.append(a);seen.add(a.id);weapon_count[a.weapon]+=1

    def balanced_best(predicate, key=None):
        pool=[a for a in anchors if a.id not in seen and predicate(a)]
        if not pool:return None
        under=[a for a in pool if weapon_count[a.weapon] < quota[a.weapon]]
        if under:pool=under
        base_key=key or _complexity
        return min(pool,key=lambda a:(weapon_count[a.weapon]/max(1,quota[a.weapon]),base_key(a)))

    # One normal single-main/single-reactor Shielded anchor for every family.
    for w in weapons:
        add(_best(anchors,lambda a,w=w:a.weapon==w and a.main_count==1 and a.reactor_count==1 and a.shield and a.pds=="NONE" and a.apu_count==0 and a.magazine_count==0 and not a.aux_flags,seen))
    # PDS, EW, legal extremes, power/endurance, and every available AUX identity.
    for pds in ("K","E","AMM"):
        add(balanced_best(lambda a,pds=pds:a.pds==pds and a.main_count==1 and a.reactor_count==1 and a.shield))
    add(balanced_best(lambda a:a.ecm and a.eccm and a.main_count==1 and a.reactor_count==1))
    add(balanced_best(lambda a:a.main_count>=2,key=lambda a:(-a.main_count,)+_complexity(a)))
    add(balanced_best(lambda a:a.reactor_count>=2,key=lambda a:(-a.reactor_count,)+_complexity(a)))
    add(balanced_best(lambda a:a.main_count>=3,key=_complexity))
    add(balanced_best(lambda a:a.reactor_count>=3,key=_complexity))
    add(balanced_best(lambda a:a.apu_count>0,key=lambda a:(-a.apu_count,)+_complexity(a)))
    add(balanced_best(lambda a:a.magazine_count>0,key=lambda a:(-a.magazine_count,)+_complexity(a)))
    add(balanced_best(lambda a:not a.shield,key=_complexity))
    for cid in BINARY_AUX:
        if aux_id(matrix,cid,tl) is not None:
            add(balanced_best(lambda a,cid=cid:cid in a.aux_flags,key=_complexity))

    # Maximin diversity fill from the deterministic 5k reservoir, while honoring
    # the family quotas. Cache vectors/min-distance for TL8/TL9 performance.
    vectors={a.id:_feature_vector(a) for a in reservoir}
    selected_vectors=[_feature_vector(a) for a in selected]
    def dvec(va, vb):
        return sum((x-y)*(x-y) for x,y in zip(va,vb))
    min_distance={};vector_sum={}
    for a in reservoir:
        if a.id in seen:continue
        va=vectors[a.id];vector_sum[a.id]=sum(va)
        min_distance[a.id]=min((dvec(va,vb) for vb in selected_vectors),default=float("inf"))
    while len(selected)<count:
        pool=[a for a in reservoir if a.id not in seen and weapon_count[a.weapon] < quota[a.weapon]]
        if not pool:
            pool=[a for a in reservoir if a.id not in seen]
        if not pool:break
        if not selected:nxt=min(pool,key=lambda a:a.id)
        else:nxt=max(pool,key=lambda a:(min_distance[a.id],-vector_sum[a.id],a.id))
        add(nxt);vn=vectors[nxt.id]
        for a in reservoir:
            if a.id in seen:continue
            da=dvec(vectors[a.id],vn)
            if da<min_distance[a.id]:min_distance[a.id]=da
    if len(selected)!=count:
        raise ValueError(f"TL{tl}: expected {count} representatives, found {len(selected)}")
    if {w:sum(a.weapon==w for a in selected) for w in weapons} != quota:
        raise ValueError(f"TL{tl}: representative weapon quota mismatch")
    return selected


def to_ecology_build(matrix, a: ExecutableArchitecture) -> EcologyBuild:
    aux_profiles=[]
    for cid in a.aux_flags:
        aid=aux_id(matrix,cid,a.tl)
        if aid:aux_profiles.append(aid)
    mag_cid=MAG_BY_WEAPON.get(a.weapon)
    if mag_cid and a.magazine_count:
        mid=aux_id(matrix,mag_cid,a.tl)
        if mid:aux_profiles.extend([mid]*a.magazine_count)
    apu=apu_profile(matrix,a.tl)
    return EcologyBuild(
        id=a.id,tl=a.tl,archetype="cp166-whole-system",weapon_family=_weapon_family(a.weapon),main_count=a.main_count,
        reactor_count=a.reactor_count,shield=a.shield,ecm=a.ecm,eccm=a.eccm,
        pds_family=None if a.pds=="NONE" else {"K":"Kinetic","E":"Energy","AMM":"AMM"}[a.pds],
        shield_hardener="shield_hardener" in a.aux_flags,capacity=a.capacity,combat_space=a.used_space,mission_aux_space=a.free_space,
        missile_payload="Swarmer" if a.weapon=="SW" else "GP",armor_profile="mainline",auxiliary_profiles=tuple(aux_profiles),
        auxiliary_power_tp=a.apu_count*int(apu["operationalTp"]),auxiliary_reactor_count=a.apu_count,
    )


def representative_rows(matrix, reps: list[ExecutableArchitecture]) -> list[dict[str,Any]]:
    out=[]
    for idx,a in enumerate(reps,1):
        out.append({
            "representative_index":idx,"build_id":a.id,"skeleton_id":a.skeleton_id,"tl":a.tl,"weapon":a.weapon,"main_count":a.main_count,
            "reactor_count":a.reactor_count,"shield":int(a.shield),"ecm":int(a.ecm),"eccm":int(a.eccm),"ew_state":a.ew_state,"pds":a.pds,
            "armor_branch":a.armor_branch,"apu_count":a.apu_count,"apu_tp_each":apu_profile(matrix,a.tl)["operationalTp"],"total_apu_tp":a.apu_count*apu_profile(matrix,a.tl)["operationalTp"],
            "magazine_count":a.magazine_count,"aux_flags":";".join(a.aux_flags),"capacity":a.capacity,"used_space":a.used_space,"free_space":a.free_space,
            "player_base_envelope":int(a.main_count==1 and a.reactor_count==1 and a.shield),
        })
    return out


def build_match_variants(matrix, reps: list[ExecutableArchitecture]) -> list[tuple[EcologyVariant,VariantMeta]]:
    builds={a.id:to_ecology_build(matrix,a) for a in reps}; out=[]
    for i,a1 in enumerate(reps):
        for j in range(i,len(reps)):
            a2=reps[j]; pair=f"TL{a1.tl}-PAIR-{i+1:02d}-{j+1:02d}"
            p1=pair+":physical-1";p2=pair+":physical-2"
            layouts=(
                ("12-AFIRST",a1,a2,"SideAFirst",p1,p2),
                ("12-BFIRST",a1,a2,"SideBFirst",p1,p2),
                ("21-AFIRST",a2,a1,"SideAFirst",p2,p1),
                ("21-BFIRST",a2,a1,"SideBFirst",p2,p1),
            )
            for orient,sa,sb,order,pa,pb in layouts:
                vid=f"{pair}-{orient}"
                v=EcologyVariant(vid,a1.tl,builds[sa.id],builds[sb.id],order,geometry=FULL_MAP_GEOMETRY,population="cp166-same-tl-whole-system",max_turns=90,scenario_group=pair,physical_id_a=pa,physical_id_b=pb)
                out.append((v,VariantMeta(pair,a1.id,a2.id,a1.weapon,a2.weapon,pa,pb,sa.id,sb.id,orient)))
    return out


def _sentinel_reps(reps:list[ExecutableArchitecture])->list[ExecutableArchitecture]:
    roles=[];seen=set()
    def pick(pred):
        pool=[a for a in reps if a.id not in seen and pred(a)]
        if not pool:pool=[a for a in reps if a.id not in seen]
        if not pool:return
        a=min(pool,key=_complexity);roles.append(a);seen.add(a.id)
    pick(lambda a:a.weapon=="E" and a.ecm and a.eccm)
    pick(lambda a:a.weapon=="K" and a.shield)
    pick(lambda a:a.weapon=="GP" and a.pds!="NONE")
    pick(lambda a:a.weapon=="SW" and a.pds!="NONE")
    while len(roles)<4:pick(lambda a:True)
    return roles[:4]


def build_monotonicity_variants(matrix,reps:list[ExecutableArchitecture])->list[tuple[EcologyVariant,dict[str,Any]]]:
    out=[]
    for role_index,a in enumerate(_sentinel_reps(reps),1):
        base=to_ecology_build(matrix,a)
        for delta in (1,2):
            boosted=replace(base,id=base.id+f"+P{delta}",auxiliary_power_tp=base.auxiliary_power_tp+delta)
            group=f"TL{a.tl}-MONO-R{role_index}-D{delta}"
            pboost=group+":boosted";pbase=group+":base"
            layouts=(
                ("BOOST-A-AFIRST",boosted,base,"SideAFirst",pboost,pbase,"A"),
                ("BOOST-A-BFIRST",boosted,base,"SideBFirst",pboost,pbase,"A"),
                ("BOOST-B-AFIRST",base,boosted,"SideAFirst",pbase,pboost,"B"),
                ("BOOST-B-BFIRST",base,boosted,"SideBFirst",pbase,pboost,"B"),
            )
            for orient,sa,sb,order,pa,pb,boost_side in layouts:
                v=EcologyVariant(group+"-"+orient,a.tl,sa,sb,order,geometry=FULL_MAP_GEOMETRY,population="cp166-power-monotonicity-diagnostic",max_turns=90,scenario_group=group,perturbation=f"free-diagnostic-power-plus-{delta}",physical_id_a=pa,physical_id_b=pb)
                out.append((v,{"probe_group":group,"role_index":role_index,"base_build_id":a.id,"weapon":a.weapon,"delta_tp":delta,"boost_side":boost_side,"orientation":orient}))
    return out


def _census(repo:Path,out:Path,representatives_per_tl:int)->dict[str,Any]:
    m=load_current_working_matrix(repo); out.mkdir(parents=True,exist_ok=True)
    coverage=execution_coverage();_write_csv(out/"execution_coverage.csv",coverage)
    all_skeleton_rows=[];summary=[];rep_rows=[]
    for tl in range(1,10):
        sk=enumerate_skeletons(m,tl); reps=select_representatives(m,tl,representatives_per_tl,skeletons=sk)
        effect_count=sum(_stack_solution_count(x) for x in sk)
        player=[x for x in sk if x.main_count==1 and x.reactor_count==1 and x.shield]
        summary.append({"tl":tl,"capacity":m.capacity(tl),"skeletons":len(sk),"effect_distinct_stack_combinations":effect_count,"player_base_skeletons":len(player),"representatives":len(reps),"weapons":";".join(_available_weapons(m,tl))})
        for s in sk:
            all_skeleton_rows.append({"skeleton_id":s.id,"tl":s.tl,"weapon":s.weapon,"main_count":s.main_count,"reactor_count":s.reactor_count,"shield":int(s.shield),"ecm":int(s.ecm),"eccm":int(s.eccm),"pds":s.pds,"aux_flags":";".join(s.aux_flags),"capacity":s.capacity,"used_without_stacks":s.used_without_stacks,"free_for_stacks":s.free_for_stacks,"apu_mag_stack_combinations":_stack_solution_count(s),"max_apu_count":s.free_for_stacks//2,"max_magazine_count":s.free_for_stacks if s.weapon in MAG_BY_WEAPON else 0,"player_base_envelope":int(s.main_count==1 and s.reactor_count==1 and s.shield)})
        rep_rows.extend(representative_rows(m,reps))
    _write_csv(out/"architecture_skeletons.csv",all_skeleton_rows);_write_csv(out/"architecture_census_summary.csv",summary);_write_csv(out/"representatives.csv",rep_rows)
    payload={"mode":"static","passed":all(x["skeletons"]==EXPECTED_SKELETONS_BY_TL[x["tl"]] for x in summary),"authority":authority_identity(repo),"skeletons":len(all_skeleton_rows),"effectDistinctStackCombinations":sum(int(x["effect_distinct_stack_combinations"]) for x in summary),"representatives":len(rep_rows),"coverageRows":len(coverage),"sameTlOnly":True,"tuningAllowed":False}
    _write_json(out/"summary.json",payload);return payload


_W_REPO:Path|None=None;_W_MATRIX=None;_W_SEED=0;_W_TRIALS=0

def _worker_init(repo:str,seed:int,trials:int):
    global _W_REPO,_W_MATRIX,_W_SEED,_W_TRIALS
    _W_REPO=Path(repo);_W_MATRIX=load_current_working_matrix(_W_REPO);_W_SEED=int(seed);_W_TRIALS=int(trials)


def _trial_task(args):
    idx,v,meta=args
    results=[run_trial_full_map(_W_MATRIX,v,_W_SEED,i,combat_doctrine=UTILITY_COMBAT_DOCTRINE) for i in range(_W_TRIALS)]
    row=aggregate_full_map_variant(v,results)
    row.update(meta if isinstance(meta,dict) else {f.name:getattr(meta,f.name) for f in fields(VariantMeta)})
    row["turn_cap_sentinels"]=sum(r.termination_cause=="TURN_CAP_SENTINEL" for r in results)
    row["offensive_exhaustions"]=sum(r.termination_cause=="MUTUAL_OFFENSIVE_EXHAUSTION" for r in results)
    row["error_trials"]=sum(bool(r.error) for r in results)
    return idx,row


def _execute(repo:Path,tasks:list[tuple[Any,Any]],seed:int,trials:int,jobs:int)->list[dict[str,Any]]:
    indexed=[(i,v,m) for i,(v,m) in enumerate(tasks)]
    if jobs<=1:
        _worker_init(str(repo),seed,trials);rows=[_trial_task(x) for x in indexed]
    else:
        ctx=get_context("spawn" if os.name=="nt" else "fork")
        with ProcessPoolExecutor(max_workers=min(jobs,len(indexed)),mp_context=ctx,initializer=_worker_init,initargs=(str(repo),seed,trials)) as ex:
            rows=list(ex.map(_trial_task,indexed,chunksize=1))
    rows.sort(key=lambda x:x[0]);return [r for _,r in rows]


def _symmetry_audit(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    by=defaultdict(dict)
    for r in rows:by[r["pair_id"]][r["orientation"]]=r
    out=[]
    for pair,g in sorted(by.items()):
        pairs=(("12-AFIRST","21-BFIRST"),("12-BFIRST","21-AFIRST"))
        for left,right in pairs:
            a,b=g[left],g[right]
            exact=(int(a["wins_a"])==int(b["wins_b"]) and int(a["wins_b"])==int(b["wins_a"]) and int(a["draws"])==int(b["draws"]) and int(a["unresolved"])==int(b["unresolved"]) and abs(float(a["mean_turns"])-float(b["mean_turns"]))<1e-12)
            out.append({"pair_id":pair,"left":left,"right":right,"passed":int(exact),"left_wins_a":a["wins_a"],"right_wins_b":b["wins_b"],"left_mean_turns":a["mean_turns"],"right_mean_turns":b["mean_turns"]})
    return out


def run_batch(repo:Path,study_path:Path,out:Path,tl:int,trials:int|None=None,jobs:int=24)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs:raise ValueError("CP166 study invalid: "+", ".join(errs))
    m=load_current_working_matrix(repo);reps=select_representatives(m,tl,int(doc["representativesPerTl"]));variants=build_match_variants(m,reps)
    mono=build_monotonicity_variants(m,reps);trials=int(trials or doc["trialsPerVariant"]);mono_trials=int(doc["monotonicityTrialsPerVariant"])
    started=time.perf_counter();rows=_execute(repo,variants,derive_seed(int(doc["masterSeed"]),"same-tl",tl),trials,jobs)
    mono_rows=_execute(repo,mono,derive_seed(int(doc["masterSeed"]),"monotonicity",tl),mono_trials,jobs)
    out.mkdir(parents=True,exist_ok=True);_write_csv(out/"representatives.csv",representative_rows(m,reps));_write_csv(out/"variant_results.csv",rows);_write_csv(out/"monotonicity_results.csv",mono_rows)
    sym=_symmetry_audit(rows);_write_csv(out/"symmetry_audit.csv",sym)
    summary={"mode":"batch","tl":tl,"passed":not any(int(r["error_trials"]) for r in rows+mono_rows) and all(int(r["passed"]) for r in sym),"representatives":len(reps),"pairGroups":len(reps)*(len(reps)+1)//2,"combatVariants":len(rows),"trialsPerVariant":trials,"combatTrials":len(rows)*trials,"monotonicityVariants":len(mono_rows),"monotonicityTrialsPerVariant":mono_trials,"monotonicityCombatTrials":len(mono_rows)*mono_trials,"errors":sum(int(r["error_trials"]) for r in rows+mono_rows),"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows+mono_rows),"symmetryRows":len(sym),"symmetryFailures":sum(not int(r["passed"]) for r in sym),"elapsedSeconds":time.perf_counter()-started,"tuningAllowed":False}
    _write_json(out/"summary.json",summary);return summary


def _pair_aggregate(rows:list[dict[str,str]])->list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:groups[(int(r["tl"]),r["pair_id"],r["build1_id"],r["build2_id"],r["build1_weapon"],r["build2_weapon"])].append(r)
    out=[]
    for key,g in sorted(groups.items()):
        b1,b2=key[2],key[3];w1=w2=draw=unr=err=trials=0
        turns=[]
        for r in g:
            n=int(r["trials"]);trials+=n;draw+=int(r["draws"]);unr+=int(r["unresolved"]);err+=int(r["errors"]);turns.append(float(r["mean_turns"]))
            if r["side_a_build_id"]==b1:w1+=int(r["wins_a"]);w2+=int(r["wins_b"])
            else:w1+=int(r["wins_b"]);w2+=int(r["wins_a"])
        out.append({"tl":key[0],"pair_id":key[1],"build1_id":b1,"build2_id":b2,"build1_weapon":key[4],"build2_weapon":key[5],"variants":len(g),"trials":trials,"build1_wins":w1,"build2_wins":w2,"draws":draw,"unresolved":unr,"errors":err,"build1_decisive_share":w1/max(1,w1+w2),"mean_turns":statistics.fmean(turns)})
    return out


def _build_performance(pair_rows:list[dict[str,Any]],rep_rows:list[dict[str,str]])->list[dict[str,Any]]:
    meta={r["build_id"]:r for r in rep_rows};shares=defaultdict(list);wins=defaultdict(int);losses=defaultdict(int);draws=defaultdict(int)
    for p in pair_rows:
        b1,b2=p["build1_id"],p["build2_id"];s=float(p["build1_decisive_share"])
        shares[b1].append(s);shares[b2].append(1-s if b2!=b1 else s);wins[b1]+=int(p["build1_wins"]);losses[b1]+=int(p["build2_wins"]);draws[b1]+=int(p["draws"])
        if b2!=b1:wins[b2]+=int(p["build2_wins"]);losses[b2]+=int(p["build1_wins"]);draws[b2]+=int(p["draws"])
    out=[]
    for bid,r in sorted(meta.items()):
        avg=statistics.fmean(shares.get(bid,[.5]));out.append({**r,"mean_pair_decisive_share":avg,"pair_opponents":len(shares.get(bid,[])),"total_wins":wins[bid],"total_losses":losses[bid],"total_draws":draws[bid],"dominance_watch":int(avg>.70),"weak_watch":int(avg<.30)})
    return out


def _family_matchups(pair_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    g=defaultdict(list)
    for p in pair_rows:
        g[(p["tl"],p["build1_weapon"],p["build2_weapon"])].append(float(p["build1_decisive_share"]))
        if p["build1_weapon"]!=p["build2_weapon"]:g[(p["tl"],p["build2_weapon"],p["build1_weapon"])].append(1-float(p["build1_decisive_share"]))
    return [{"tl":k[0],"weapon":k[1],"opponent_weapon":k[2],"pair_groups":len(v),"mean_decisive_share":statistics.fmean(v)} for k,v in sorted(g.items())]


def _feature_performance(build_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    features=("weapon","main_count","reactor_count","shield","ew_state","pds","armor_branch","apu_count","magazine_count")
    for feat in features:
        groups=defaultdict(list)
        for r in build_rows:groups[(int(r["tl"]),str(r[feat]))].append(float(r["mean_pair_decisive_share"]))
        for (tl,val),xs in sorted(groups.items()):out.append({"tl":tl,"feature":feat,"value":val,"representatives":len(xs),"mean_build_decisive_share":statistics.fmean(xs)})
    for cid in BINARY_AUX:
        groups=defaultdict(list)
        for r in build_rows:
            present=cid in str(r.get("aux_flags","")).split(";")
            groups[(int(r["tl"]),"present" if present else "absent")].append(float(r["mean_pair_decisive_share"]))
        for (tl,val),xs in sorted(groups.items()):out.append({"tl":tl,"feature":"aux:"+cid,"value":val,"representatives":len(xs),"mean_build_decisive_share":statistics.fmean(xs)})
    return out


def _monotonicity_summary(rows:list[dict[str,str]])->list[dict[str,Any]]:
    g=defaultdict(list)
    for r in rows:g[(int(r["tl"]),r["probe_group"],int(r["role_index"]),r["base_build_id"],r["weapon"],int(r["delta_tp"]))].append(r)
    out=[]
    for key,rr in sorted(g.items()):
        boost=base=draw=unr=0
        for r in rr:
            if r["boost_side"]=="A":boost+=int(r["wins_a"]);base+=int(r["wins_b"])
            else:boost+=int(r["wins_b"]);base+=int(r["wins_a"])
            draw+=int(r["draws"]);unr+=int(r["unresolved"])
        share=boost/max(1,boost+base)
        out.append({"tl":key[0],"probe_group":key[1],"role_index":key[2],"base_build_id":key[3],"weapon":key[4],"delta_tp":key[5],"variants":len(rr),"boosted_wins":boost,"base_wins":base,"draws":draw,"unresolved":unr,"boosted_decisive_share":share,"allocator_regression_watch":int(share<.45),"strong_positive_threshold":int(share>.60)})
    return out


def _tactics_watch(variant_rows:list[dict[str,str]],mono_summary:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for r in variant_rows:
        for side,opp in (("a","b"),("b","a")):
            opp_family=r[f"side_{opp}_family"]
            pds=float(r.get(f"mean_{side}_power_pds",0) or 0)
            if opp_family!="Missile" and pds>.05:
                out.append({"tl":r["tl"],"watch":"PDS_POWER_WITHOUT_MISSILE_THREAT","variant_id":r["variant_id"],"side":side.upper(),"value":pds})
            div=float(r.get(f"mean_{side}_cp147_sole_main_diversions_without_hull_risk",0) or 0)
            if div>.10:out.append({"tl":r["tl"],"watch":"SOLE_MAIN_DEFENSIVE_DIVERSION_WITHOUT_HULL_RISK","variant_id":r["variant_id"],"side":side.upper(),"value":div})
            starve=float(r.get(f"mean_{side}_weapon_power_shortfalls",0) or 0)
            if starve>2.0:out.append({"tl":r["tl"],"watch":"REPEATED_WEAPON_POWER_SHORTFALL","variant_id":r["variant_id"],"side":side.upper(),"value":starve})
        if float(r.get("unresolved_rate",0) or 0)>.05:out.append({"tl":r["tl"],"watch":"UNRESOLVED_RATE_GT_5PCT","variant_id":r["variant_id"],"side":"BOTH","value":r["unresolved_rate"]})
    for r in mono_summary:
        if r["allocator_regression_watch"]:out.append({"tl":r["tl"],"watch":"EXTRA_POWER_OUTCOME_REGRESSION","variant_id":r["probe_group"],"side":"BOOSTED","value":r["boosted_decisive_share"]})
    return out


def merge_batches(repo:Path,study_path:Path,batch_root:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs:raise ValueError("CP166 study invalid: "+", ".join(errs))
    variant_rows=[];mono_rows=[];rep_rows=[];batch_summary=[];sym_rows=[]
    for tl in range(1,10):
        d=batch_root/f"tl{tl}";sm=json.loads((d/"summary.json").read_text());batch_summary.append(sm)
        if not sm.get("passed"):raise ValueError(f"TL{tl} batch failed")
        variant_rows+=_read_csv(d/"variant_results.csv");mono_rows+=_read_csv(d/"monotonicity_results.csv");rep_rows+=_read_csv(d/"representatives.csv");sym_rows+=_read_csv(d/"symmetry_audit.csv")
    pairs=_pair_aggregate(variant_rows);builds=_build_performance(pairs,rep_rows);families=_family_matchups(pairs);features=_feature_performance(builds);mono=_monotonicity_summary(mono_rows);watches=_tactics_watch(variant_rows,mono)
    out.mkdir(parents=True,exist_ok=True);_write_csv(out/"variant_results.csv",variant_rows);_write_csv(out/"pair_results.csv",pairs);_write_csv(out/"build_performance.csv",builds);_write_csv(out/"family_matchups.csv",families);_write_csv(out/"feature_performance.csv",features);_write_csv(out/"monotonicity_results.csv",mono_rows);_write_csv(out/"monotonicity_summary.csv",mono);_write_csv(out/"tactics_watch.csv",watches);_write_csv(out/"symmetry_audit.csv",sym_rows);_write_csv(out/"execution_coverage.csv",execution_coverage())
    dom=sum(int(r["dominance_watch"]) for r in builds);weak=sum(int(r["weak_watch"]) for r in builds);reg=sum(int(r["allocator_regression_watch"]) for r in mono)
    summary={"mode":"merge","passed":len(variant_rows)==int(doc["expected"]["combatVariants"]) and len(mono_rows)==int(doc["expected"]["monotonicityVariants"]) and not any(int(r.get("errors",0)) for r in variant_rows+mono_rows) and all(int(r["passed"]) for r in sym_rows),"sameTlOnly":True,"representatives":len(builds),"pairGroups":len(pairs),"combatVariants":len(variant_rows),"substantiveCombatTrials":sum(int(r["trials"]) for r in variant_rows),"monotonicityVariants":len(mono_rows),"monotonicityCombatTrials":sum(int(r["trials"]) for r in mono_rows),"totalDiagnosticCombatTrials":sum(int(r["trials"]) for r in variant_rows+mono_rows),"errors":sum(int(r.get("errors",0)) for r in variant_rows+mono_rows),"turnCapSentinels":sum(int(r.get("turn_cap_sentinels",0)) for r in variant_rows+mono_rows),"symmetryFailures":sum(not int(r["passed"]) for r in sym_rows),"dominanceWatchBuilds":dom,"weakWatchBuilds":weak,"allocatorRegressionWatches":reg,"tacticsWatchRows":len(watches),"automaticPromotion":False,"tuningAllowed":False,"nextStage":"same-TL component-state/multi-package integration after diagnostic assessment"}
    _write_json(out/"summary.json",summary);return summary


def plan(repo:Path,study_path:Path,out:Path|None=None)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs:raise ValueError("CP166 study invalid: "+", ".join(errs))
    m=load_current_working_matrix(repo);per=[]
    for tl in range(1,10):
        sk=enumerate_skeletons(m,tl);reps=select_representatives(m,tl,int(doc["representativesPerTl"]),skeletons=sk);vars_=build_match_variants(m,reps);mono=build_monotonicity_variants(m,reps)
        counts={w:sum(a.weapon==w for a in reps) for w in _available_weapons(m,tl)}
        per.append({"tl":tl,"skeletons":len(sk),"representatives":len(reps),"weaponRepresentativeCounts":counts,"pairGroups":len(reps)*(len(reps)+1)//2,"combatVariants":len(vars_),"monotonicityVariants":len(mono)})
    s={"mode":"plan","passed":all(x["skeletons"]==EXPECTED_SKELETONS_BY_TL[x["tl"]] and x["representatives"]==28 and x["combatVariants"]==1624 and x["monotonicityVariants"]==32 for x in per),"authority":authority_identity(repo),"perTl":per,**doc["expected"],"automaticPromotion":False,"tuningAllowed":False}
    if out:out.mkdir(parents=True,exist_ok=True);_write_csv(out/"plan_by_tl.csv",per);_write_json(out/"summary.json",s)
    return s


def smoke(repo:Path,study_path:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);m=load_current_working_matrix(repo);checks=[]
    for tl in (1,5,9):
        reps=select_representatives(m,tl,28);vmeta=build_match_variants(m,reps)
        # Exercise an early self mirror and a high-diversity pair with one trial.
        for v,meta in (vmeta[0],vmeta[-1]):
            r=run_trial_full_map(m,v,derive_seed(int(doc["masterSeed"]),"smoke",tl),0,combat_doctrine=UTILITY_COMBAT_DOCTRINE)
            checks.append({"probe":v.id,"tl":tl,"passed":int(not r.error),"winner":r.winner,"turns":r.turns,"termination":r.termination_cause})
    # Exact mirror-equivalence probe with current authorities.
    reps=select_representatives(m,9,28);qs=build_match_variants(m,reps);a=qs[4][0];b=qs[7][0]
    ra=run_trial_full_map(m,a,derive_seed(int(doc["masterSeed"]),"mirror"),0,combat_doctrine=UTILITY_COMBAT_DOCTRINE);rb=run_trial_full_map(m,b,derive_seed(int(doc["masterSeed"]),"mirror"),0,combat_doctrine=UTILITY_COMBAT_DOCTRINE)
    checks.append({"probe":"current-working-mirror-equivalence","tl":9,"passed":int(mirror_equivalent(ra,rb)),"winner":ra.winner,"turns":ra.turns,"termination":ra.termination_cause})
    out.mkdir(parents=True,exist_ok=True);_write_csv(out/"cp166_smoke.csv",checks);s={"mode":"smoke","passed":all(int(x["passed"]) for x in checks),"probes":len(checks),"liveCombatTrials":len(checks)+1,"errors":sum(not int(x["passed"]) for x in checks)};_write_json(out/"summary.json",s);return s


def main(argv=None)->int:
    p=argparse.ArgumentParser(prog="cp166-same-tl-whole-system")
    p.add_argument("--repo",required=True);p.add_argument("--study",required=True)
    sub=p.add_subparsers(dest="mode",required=True)
    for name in ("plan","static","smoke","merge"):
        q=sub.add_parser(name);q.add_argument("--out",required=True)
        if name=="merge":q.add_argument("--batch-root",required=True)
    b=sub.add_parser("batch");b.add_argument("--tl",type=int,required=True,choices=range(1,10));b.add_argument("--out",required=True);b.add_argument("--jobs",type=int,default=24);b.add_argument("--trials",type=int)
    a=p.parse_args(argv);repo=Path(a.repo).resolve();study=Path(a.study);study=study if study.is_absolute() else repo/study;out=Path(a.out);out=out if out.is_absolute() else repo/out
    if a.mode=="plan":res=plan(repo,study,out)
    elif a.mode=="static":res=_census(repo,out,int(load_json(study)["representativesPerTl"]))
    elif a.mode=="smoke":res=smoke(repo,study,out)
    elif a.mode=="batch":res=run_batch(repo,study,out,a.tl,a.trials,a.jobs)
    else:
        br=Path(a.batch_root);br=br if br.is_absolute() else repo/br;res=merge_batches(repo,study,br,out)
    print(json.dumps(res,indent=2));return 0 if res.get("passed") else 2


if __name__=="__main__":raise SystemExit(main())
