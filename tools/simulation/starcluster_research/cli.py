from __future__ import annotations
import argparse,json,sys,unittest
from pathlib import Path
from .runner import run_study,analyze,analyze_cp104,environment_report
from .study import load_json,validate_study,build_study
from .parity import run_parity, PARITY_CASE_COUNT
from .power_calibration import run_power_calibration, validate_study as validate_power_study
from .ecology import run_ecology, validate_study as validate_ecology_study
from .neighbor_analysis import run_neighbor_analysis, validate_study as validate_neighbor_study
from .payload_analysis import run_payload_analysis, validate_study as validate_payload_study
from .weapon_family_analysis import run_weapon_family_analysis, validate_study as validate_weapon_family_study
from .role_generation_analysis import run_role_generation_analysis, validate_study as validate_role_generation_study
from .simplified_progression_analysis import run_simplified_progression_analysis, validate_study as validate_simplified_progression_study
from .weapon_integration_analysis import run_weapon_integration_analysis, validate_study as validate_weapon_integration_study
from .weapon_sensitivity_analysis import run_weapon_sensitivity_analysis, validate_study as validate_weapon_sensitivity_study
from .damage_resolution_analysis import run_damage_resolution_analysis, validate_study as validate_damage_resolution_study
from .baseline_foundation import run_baseline_foundation, validate_study as validate_baseline_foundation_study
from .whole_ladder_analysis import run_whole_ladder_analysis, validate_study as validate_whole_ladder_study
from .fidelity_attribution_analysis import run_fidelity_attribution, validate_study as validate_fidelity_attribution_study
from .main_subsystem_stabilization_analysis import run_main_subsystem_stabilization, validate_study as validate_main_subsystem_stabilization_study
from .whole_ladder_sensitivity_analysis import run_whole_ladder_sensitivity, validate_study as validate_whole_ladder_sensitivity_study
from .missile_progression_analysis import run_missile_progression, validate_study as validate_missile_progression_study
from .missile_late_maturation_analysis import run_late_missile_maturation, validate_study as validate_late_missile_maturation_study
from .same_tl_candidate_baseline_analysis import run_same_tl_candidate_baseline, validate_study as validate_same_tl_candidate_baseline_study
from .auxiliary_integration_analysis import run_auxiliary_integration, validate_study as validate_auxiliary_integration_study
from .def_res_reconciliation_analysis import run_analysis as run_def_res_reconciliation, validate_study as validate_def_res_reconciliation_study
from .stage_a_integration_analysis import run_integration as run_stage_a_integration, merge_integration_batches as merge_stage_a_integration_batches, validate_study as validate_stage_a_integration_study
from .combat_duration_stalemate_analysis import run_batch as run_combat_duration_stalemate_batch, merge_batches as merge_combat_duration_stalemate_batches, validate_study as validate_combat_duration_stalemate_study
from .missile_mirror_pacing_attribution import run_batch as run_missile_mirror_pacing_batch, merge_batches as merge_missile_mirror_pacing_batches, validate_study as validate_missile_mirror_pacing_study
from .combat_surface_reconciliation_analysis import run_batch as run_combat_surface_reconciliation_batch, merge_batches as merge_combat_surface_reconciliation_batches, validate_study as validate_combat_surface_reconciliation_study, write_reconciliation_evidence
from .whole_combat_stage_a_response_surface import (run_smoke_batch as run_cp144_smoke_batch, merge_smoke_batches as merge_cp144_smoke_batches, run_substantive_batch as run_cp144_substantive_batch, merge_substantive_batches as merge_cp144_substantive_batches, validate_study as validate_cp144_stage_a_study, validate_population as validate_cp144_stage_a_population)
from .stage_a_diagnostic_attribution import run_analysis as run_cp145_stage_a_diagnostic, validate_study as validate_cp145_stage_a_diagnostic_study, validate_population as validate_cp145_stage_a_diagnostic_population
from .combat_resource_doctrine_validation import run_analysis as run_cp146_combat_resource_doctrine, validate_study as validate_cp146_combat_resource_doctrine_study, validate_population as validate_cp146_combat_resource_doctrine_population
from .tactical_package_utility_validation import run_analysis as run_cp147_tactical_package_utility, validate_study as validate_cp147_tactical_package_utility_study, validate_population as validate_cp147_tactical_package_utility_population
from .kinetic_full_characteristic_sweep import run_plan as run_cp149_kinetic_plan, run_batch as run_cp149_kinetic_batch, merge_batches as merge_cp149_kinetic_batches, validate_study as validate_cp149_kinetic_study, validate_population as validate_cp149_kinetic_population
from .kinetic_viable_region_refinement import run_plan as run_cp150_kinetic_plan, run_batch as run_cp150_kinetic_batch, merge_batches as merge_cp150_kinetic_batches, validate_study as validate_cp150_kinetic_study, validate_population as validate_cp150_kinetic_population
from .point_scale_multivariate_response import run_plan as run_cp151_point_scale_plan, run_batch as run_cp151_point_scale_batch, run_equivalence as run_cp151_point_scale_equivalence, merge_batches as merge_cp151_point_scale_batches, validate_study as validate_cp151_point_scale_study, validate_population as validate_cp151_point_scale_population
from .direct_fire_joint_refinement import run_plan as run_cp152_direct_fire_plan, run_lane_batch as run_cp152_direct_fire_lane_batch, merge_lane as merge_cp152_direct_fire_lane, select_joint_shortlist as select_cp152_direct_fire_joint, run_joint_batch as run_cp152_direct_fire_joint_batch, merge_joint as merge_cp152_direct_fire_joint, validate_study as validate_cp152_direct_fire_study, validate_population as validate_cp152_direct_fire_population
from .four_main_ladder_synthesis import run_plan as run_cp153_plan, run_energy_batch as run_cp153_energy_batch, merge_energy as merge_cp153_energy, synthesize_ladders as synthesize_cp153_ladders, run_package_batch as run_cp153_package_batch, merge_packages as merge_cp153_packages, select_deep as select_cp153_deep, validate_study as validate_cp153_study, validate_population as validate_cp153_population
from .pds_lifecycle_closure import run_plan as run_cp154_pds_plan, run_candidate_batch as run_cp154_pds_candidate_batch, merge_candidate_batches as merge_cp154_pds_candidates, synthesize_ladders as synthesize_cp154_pds_ladders, run_deep_batch as run_cp154_pds_deep_batch, merge_deep as merge_cp154_pds_deep, validate_study as validate_cp154_pds_study, validate_population as validate_cp154_pds_population
from .pds_architecture_resynthesis import run_plan as run_cp155_pds_plan, run_baseline as run_cp155_pds_baseline, run_candidate_batch as run_cp155_pds_candidate_batch, merge_candidate_batches as merge_cp155_pds_candidates, synthesize_ladders as synthesize_cp155_pds_ladders, run_deep_batch as run_cp155_pds_deep_batch, merge_deep as merge_cp155_pds_deep, validate_study as validate_cp155_pds_study, validate_population as validate_cp155_pds_population


def _write_summary(outdir: Path|None, payload: dict):
    if outdir is None:
        return
    outdir.mkdir(parents=True,exist_ok=True)
    normalized=dict(payload)
    if 'gates' not in normalized:
        passed=bool(normalized.get('passed',True))
        normalized['gates']={'failed':([] if passed else ['command-failed']),'passed':passed}
    normalized['failedGates']=len(normalized.get('gates',{}).get('failed',[]))
    (outdir/'summary.json').write_text(json.dumps(normalized,indent=2)+'\n',encoding='utf-8')


def main(argv=None):
    p=argparse.ArgumentParser(prog='starcluster-research')
    p.add_argument('--repo',default='.')
    sub=p.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('environment'); e.add_argument('--output-dir')
    v=sub.add_parser('validate'); v.add_argument('study'); v.add_argument('--output-dir')
    q=sub.add_parser('parity'); q.add_argument('--output-dir')
    t=sub.add_parser('self-test'); t.add_argument('--output-dir')
    r=sub.add_parser('run'); r.add_argument('study'); r.add_argument('--out','--output-dir',dest='out',required=True); r.add_argument('--trials',type=int); r.add_argument('--jobs',type=int,default=1); r.add_argument('--plan-only',action='store_true')
    a=sub.add_parser('analyze'); a.add_argument('--primary',required=True); a.add_argument('--overlay'); a.add_argument('--output-dir',required=True)
    a104=sub.add_parser('analyze-cp104'); a104.add_argument('--diagnostic',required=True); a104.add_argument('--cp103-primary',required=True); a104.add_argument('--output-dir',required=True)
    pc=sub.add_parser('power-calibrate'); pc.add_argument('study'); pc.add_argument('--output-dir',required=True)
    ec=sub.add_parser('ecology'); ec.add_argument('study'); ec.add_argument('--output-dir',required=True); ec.add_argument('--trials',type=int); ec.add_argument('--jobs',type=int,default=1)
    nb=sub.add_parser('neighbor-study'); nb.add_argument('study'); nb.add_argument('--output-dir',required=True); nb.add_argument('--trials',type=int); nb.add_argument('--jobs',type=int,default=1)
    pl=sub.add_parser('payload-study'); pl.add_argument('study'); pl.add_argument('--output-dir',required=True); pl.add_argument('--trials',type=int); pl.add_argument('--jobs',type=int,default=1)
    wf=sub.add_parser('weapon-family-study'); wf.add_argument('study'); wf.add_argument('--output-dir',required=True); wf.add_argument('--trials',type=int); wf.add_argument('--jobs',type=int,default=1)
    rg=sub.add_parser('warhead-generation-study'); rg.add_argument('study'); rg.add_argument('--output-dir',required=True); rg.add_argument('--trials',type=int); rg.add_argument('--jobs',type=int,default=1)
    sp=sub.add_parser('simplified-weapon-study'); sp.add_argument('study'); sp.add_argument('--output-dir',required=True); sp.add_argument('--trials',type=int); sp.add_argument('--jobs',type=int,default=1)
    wi=sub.add_parser('weapon-integration-study'); wi.add_argument('study'); wi.add_argument('--output-dir',required=True); wi.add_argument('--trials',type=int); wi.add_argument('--jobs',type=int,default=1)
    ws=sub.add_parser('weapon-sensitivity-study'); ws.add_argument('study'); ws.add_argument('--output-dir',required=True); ws.add_argument('--trials',type=int); ws.add_argument('--jobs',type=int,default=1)
    dr=sub.add_parser('damage-resolution-study'); dr.add_argument('study'); dr.add_argument('--output-dir',required=True); dr.add_argument('--trials',type=int); dr.add_argument('--equivalence-trials',type=int); dr.add_argument('--jobs',type=int,default=1)
    bf=sub.add_parser('baseline-foundation'); bf.add_argument('study'); bf.add_argument('--output-dir',required=True)
    wl=sub.add_parser('whole-ladder-study'); wl.add_argument('study'); wl.add_argument('--output-dir',required=True); wl.add_argument('--mode',choices=('plan','smoke','run'),required=True); wl.add_argument('--trials',type=int); wl.add_argument('--jobs',type=int,default=24)
    fa=sub.add_parser('fidelity-attribution-study'); fa.add_argument('study'); fa.add_argument('--output-dir',required=True); fa.add_argument('--mode',choices=('plan','symmetry','smoke','run'),required=True); fa.add_argument('--trials',type=int); fa.add_argument('--jobs',type=int,default=24)
    ms=sub.add_parser('main-subsystem-stabilization-study'); ms.add_argument('study'); ms.add_argument('--output-dir',required=True); ms.add_argument('--mode',choices=('plan','symmetry','smoke','run'),required=True); ms.add_argument('--trials',type=int); ms.add_argument('--jobs',type=int,default=24)
    ps=sub.add_parser('whole-ladder-sensitivity-study'); ps.add_argument('study'); ps.add_argument('--output-dir',required=True); ps.add_argument('--mode',choices=('plan','symmetry','smoke','run'),required=True); ps.add_argument('--jobs',type=int,default=24)
    mp=sub.add_parser('missile-progression-study'); mp.add_argument('study'); mp.add_argument('--output-dir',required=True); mp.add_argument('--mode',choices=('plan','smoke','run'),required=True); mp.add_argument('--jobs',type=int,default=24)
    lm=sub.add_parser('late-missile-maturation-study'); lm.add_argument('study'); lm.add_argument('--output-dir',required=True); lm.add_argument('--mode',choices=('plan','smoke','run'),required=True); lm.add_argument('--jobs',type=int,default=24)
    st=sub.add_parser('same-tl-candidate-baseline-study'); st.add_argument('study'); st.add_argument('--output-dir',required=True); st.add_argument('--mode',choices=('plan','symmetry','smoke','run'),required=True); st.add_argument('--trials',type=int); st.add_argument('--jobs',type=int,default=24)
    ax=sub.add_parser('auxiliary-integration-study'); ax.add_argument('study'); ax.add_argument('--output-dir',required=True); ax.add_argument('--mode',choices=('plan','symmetry','smoke','run'),required=True); ax.add_argument('--trials',type=int); ax.add_argument('--jobs',type=int,default=24)
    cr=sub.add_parser('combat-model-reconciliation-study'); cr.add_argument('study'); cr.add_argument('--output-dir',required=True)
    si=sub.add_parser('stage-a-integration-study'); si.add_argument('study'); si.add_argument('--output-dir',required=True); si.add_argument('--mode',choices=('plan','smoke'),required=True); si.add_argument('--jobs',type=int,default=24); si.add_argument('--batch-start',type=int,default=0); si.add_argument('--batch-end',type=int)
    sm=sub.add_parser('stage-a-integration-merge'); sm.add_argument('study'); sm.add_argument('--batch-root',required=True); sm.add_argument('--output-dir',required=True)
    cd=sub.add_parser('combat-duration-stalemate-study'); cd.add_argument('study'); cd.add_argument('--output-dir',required=True); cd.add_argument('--jobs',type=int,default=24); cd.add_argument('--batch-start',type=int,default=0); cd.add_argument('--batch-end',type=int)
    cm=sub.add_parser('combat-duration-stalemate-merge'); cm.add_argument('study'); cm.add_argument('--batch-root',required=True); cm.add_argument('--output-dir',required=True)
    cs=sub.add_parser('combat-surface-reconciliation-study'); cs.add_argument('study'); cs.add_argument('--output-dir',required=True); cs.add_argument('--jobs',type=int,default=24); cs.add_argument('--batch-start',type=int,default=0); cs.add_argument('--batch-end',type=int)
    csm=sub.add_parser('combat-surface-reconciliation-merge'); csm.add_argument('study'); csm.add_argument('--batch-root',required=True); csm.add_argument('--output-dir',required=True)
    csa=sub.add_parser('combat-surface-reconciliation-audit'); csa.add_argument('study'); csa.add_argument('--output-dir',required=True)
    mp=sub.add_parser('missile-mirror-pacing-attribution-study'); mp.add_argument('study'); mp.add_argument('--output-dir',required=True); mp.add_argument('--jobs',type=int,default=24); mp.add_argument('--batch-start',type=int,default=0); mp.add_argument('--batch-end',type=int)
    mpm=sub.add_parser('missile-mirror-pacing-attribution-merge'); mpm.add_argument('study'); mpm.add_argument('--batch-root',required=True); mpm.add_argument('--output-dir',required=True)
    wcs=sub.add_parser('whole-combat-stage-a-smoke'); wcs.add_argument('study'); wcs.add_argument('--output-dir',required=True); wcs.add_argument('--jobs',type=int,default=24); wcs.add_argument('--batch-start',type=int,default=0); wcs.add_argument('--batch-end',type=int)
    wcsm=sub.add_parser('whole-combat-stage-a-smoke-merge'); wcsm.add_argument('study'); wcsm.add_argument('--batch-root',required=True); wcsm.add_argument('--output-dir',required=True)
    wcr=sub.add_parser('whole-combat-stage-a-substantive'); wcr.add_argument('study'); wcr.add_argument('--output-dir',required=True); wcr.add_argument('--jobs',type=int,default=24); wcr.add_argument('--batch-start',type=int,default=0); wcr.add_argument('--batch-end',type=int); wcr.add_argument('--trials-per-scenario',type=int)
    wcrm=sub.add_parser('whole-combat-stage-a-substantive-merge'); wcrm.add_argument('study'); wcrm.add_argument('--batch-root',required=True); wcrm.add_argument('--output-dir',required=True); wcrm.add_argument('--trials-per-scenario',type=int)
    cpd=sub.add_parser('stage-a-diagnostic-attribution'); cpd.add_argument('study'); cpd.add_argument('--output-dir',required=True); cpd.add_argument('--jobs',type=int,default=24)
    crd=sub.add_parser('combat-resource-doctrine-validation'); crd.add_argument('study'); crd.add_argument('--output-dir',required=True); crd.add_argument('--jobs',type=int,default=24)
    tpu=sub.add_parser('tactical-package-utility-validation'); tpu.add_argument('study'); tpu.add_argument('--output-dir',required=True); tpu.add_argument('--jobs',type=int,default=24)
    ksp=sub.add_parser('kinetic-full-characteristic-plan'); ksp.add_argument('study'); ksp.add_argument('--output-dir',required=True)
    ksb=sub.add_parser('kinetic-full-characteristic-sweep'); ksb.add_argument('study'); ksb.add_argument('--output-dir',required=True); ksb.add_argument('--jobs',type=int,default=24); ksb.add_argument('--tl',type=int,required=True); ksb.add_argument('--candidate-start',type=int,default=0); ksb.add_argument('--candidate-end',type=int); ksb.add_argument('--trials',type=int); ksb.add_argument('--smoke-panel',action='store_true')
    ksm=sub.add_parser('kinetic-full-characteristic-merge'); ksm.add_argument('study'); ksm.add_argument('--batch-root',required=True); ksm.add_argument('--output-dir',required=True); ksm.add_argument('--trials',type=int)
    krp=sub.add_parser('kinetic-viable-region-plan'); krp.add_argument('study'); krp.add_argument('--output-dir',required=True)
    krb=sub.add_parser('kinetic-viable-region-sweep'); krb.add_argument('study'); krb.add_argument('--output-dir',required=True); krb.add_argument('--jobs',type=int,default=24); krb.add_argument('--tl',type=int,required=True); krb.add_argument('--candidate-start',type=int,default=0); krb.add_argument('--candidate-end',type=int); krb.add_argument('--trials',type=int); krb.add_argument('--smoke-panel',action='store_true')
    krm=sub.add_parser('kinetic-viable-region-merge'); krm.add_argument('study'); krm.add_argument('--batch-root',required=True); krm.add_argument('--output-dir',required=True); krm.add_argument('--trials',type=int)
    psp=sub.add_parser('point-scale-plan'); psp.add_argument('study'); psp.add_argument('--output-dir',required=True)
    pse=sub.add_parser('point-scale-equivalence'); pse.add_argument('study'); pse.add_argument('--output-dir',required=True); pse.add_argument('--jobs',type=int,default=24)
    psb=sub.add_parser('point-scale-sweep'); psb.add_argument('study'); psb.add_argument('--output-dir',required=True); psb.add_argument('--jobs',type=int,default=24); psb.add_argument('--tl',type=int,required=True); psb.add_argument('--candidate-start',type=int,default=0); psb.add_argument('--candidate-end',type=int); psb.add_argument('--trials',type=int); psb.add_argument('--smoke-panel',action='store_true')
    psm=sub.add_parser('point-scale-merge'); psm.add_argument('study'); psm.add_argument('--batch-root',required=True); psm.add_argument('--output-dir',required=True); psm.add_argument('--trials',type=int)
    dfp=sub.add_parser('direct-fire-refinement-plan'); dfp.add_argument('study'); dfp.add_argument('--output-dir',required=True)
    dfb=sub.add_parser('direct-fire-refinement-sweep'); dfb.add_argument('study'); dfb.add_argument('--lane',choices=('K','E'),required=True); dfb.add_argument('--output-dir',required=True); dfb.add_argument('--jobs',type=int,default=24); dfb.add_argument('--tl',type=int,required=True); dfb.add_argument('--candidate-start',type=int,default=0); dfb.add_argument('--candidate-end',type=int); dfb.add_argument('--trials',type=int); dfb.add_argument('--smoke-panel',action='store_true')
    dfm=sub.add_parser('direct-fire-refinement-merge'); dfm.add_argument('study'); dfm.add_argument('--lane',choices=('K','E'),required=True); dfm.add_argument('--batch-root',required=True); dfm.add_argument('--output-dir',required=True)
    dfs=sub.add_parser('direct-fire-joint-select'); dfs.add_argument('study'); dfs.add_argument('--k-merged',required=True); dfs.add_argument('--e-merged',required=True); dfs.add_argument('--output-dir',required=True)
    dfj=sub.add_parser('direct-fire-joint-sweep'); dfj.add_argument('study'); dfj.add_argument('--joint-ledger',required=True); dfj.add_argument('--output-dir',required=True); dfj.add_argument('--jobs',type=int,default=24); dfj.add_argument('--tl',type=int,required=True); dfj.add_argument('--candidate-start',type=int,default=0); dfj.add_argument('--candidate-end',type=int); dfj.add_argument('--trials',type=int)
    dfjm=sub.add_parser('direct-fire-joint-merge'); dfjm.add_argument('study'); dfjm.add_argument('--joint-ledger',required=True); dfjm.add_argument('--batch-root',required=True); dfjm.add_argument('--output-dir',required=True)
    fmp=sub.add_parser('four-main-ladder-plan'); fmp.add_argument('study'); fmp.add_argument('--output-dir',required=True)
    fme=sub.add_parser('four-main-energy-closure'); fme.add_argument('study'); fme.add_argument('--output-dir',required=True); fme.add_argument('--jobs',type=int,default=24); fme.add_argument('--tl',type=int,required=True); fme.add_argument('--candidate-start',type=int,default=0); fme.add_argument('--candidate-end',type=int); fme.add_argument('--trials',type=int); fme.add_argument('--smoke-panel',action='store_true')
    fmem=sub.add_parser('four-main-energy-merge'); fmem.add_argument('study'); fmem.add_argument('--batch-root',required=True); fmem.add_argument('--output-dir',required=True)
    fms=sub.add_parser('four-main-ladder-synthesize'); fms.add_argument('study'); fms.add_argument('--energy-merged',required=True); fms.add_argument('--output-dir',required=True)
    fmb=sub.add_parser('four-main-package-sweep'); fmb.add_argument('study'); fmb.add_argument('--package-ledger',required=True); fmb.add_argument('--mode',choices=('screen','deep'),required=True); fmb.add_argument('--output-dir',required=True); fmb.add_argument('--jobs',type=int,default=24); fmb.add_argument('--package-start',type=int,default=0); fmb.add_argument('--package-end',type=int); fmb.add_argument('--trials',type=int)
    fmm=sub.add_parser('four-main-package-merge'); fmm.add_argument('study'); fmm.add_argument('--package-ledger',required=True); fmm.add_argument('--mode',choices=('screen','deep'),required=True); fmm.add_argument('--batch-root',required=True); fmm.add_argument('--output-dir',required=True)
    fmd=sub.add_parser('four-main-deep-select'); fmd.add_argument('study'); fmd.add_argument('--package-ledger',required=True); fmd.add_argument('--screen-merged',required=True); fmd.add_argument('--output-dir',required=True)
    pplan=sub.add_parser('pds-closure-plan'); pplan.add_argument('study'); pplan.add_argument('--output-dir',required=True)
    pcs=sub.add_parser('pds-closure-candidate-sweep'); pcs.add_argument('study'); pcs.add_argument('--output-dir',required=True); pcs.add_argument('--family',choices=('Kinetic','Energy','AMM'),required=True); pcs.add_argument('--tl',type=int,required=True); pcs.add_argument('--candidate-start',type=int,default=0); pcs.add_argument('--candidate-end',type=int); pcs.add_argument('--jobs',type=int,default=24); pcs.add_argument('--trials',type=int); pcs.add_argument('--smoke',action='store_true')
    pcm=sub.add_parser('pds-closure-candidate-merge'); pcm.add_argument('study'); pcm.add_argument('--batch-root',required=True); pcm.add_argument('--output-dir',required=True)
    pls=sub.add_parser('pds-closure-ladder-synthesize'); pls.add_argument('study'); pls.add_argument('--candidate-merged',required=True); pls.add_argument('--output-dir',required=True)
    pdsd=sub.add_parser('pds-closure-deep-sweep'); pdsd.add_argument('study'); pdsd.add_argument('--ladder-ledger',required=True); pdsd.add_argument('--output-dir',required=True); pdsd.add_argument('--ladder-start',type=int,default=0); pdsd.add_argument('--ladder-end',type=int); pdsd.add_argument('--jobs',type=int,default=24); pdsd.add_argument('--trials',type=int)
    pdm=sub.add_parser('pds-closure-deep-merge'); pdm.add_argument('study'); pdm.add_argument('--ladder-ledger',required=True); pdm.add_argument('--batch-root',required=True); pdm.add_argument('--output-dir',required=True)
    p155p=sub.add_parser('pds-resynthesis-plan'); p155p.add_argument('study'); p155p.add_argument('--output-dir',required=True)
    p155b=sub.add_parser('pds-resynthesis-baseline'); p155b.add_argument('study'); p155b.add_argument('--output-dir',required=True); p155b.add_argument('--jobs',type=int,default=24); p155b.add_argument('--trials',type=int)
    p155c=sub.add_parser('pds-resynthesis-candidate-sweep'); p155c.add_argument('study'); p155c.add_argument('--output-dir',required=True); p155c.add_argument('--family',choices=('Kinetic','Energy','AMM'),required=True); p155c.add_argument('--tl',type=int,required=True); p155c.add_argument('--candidate-start',type=int,default=0); p155c.add_argument('--candidate-end',type=int); p155c.add_argument('--jobs',type=int,default=24); p155c.add_argument('--trials',type=int); p155c.add_argument('--smoke',action='store_true')
    p155m=sub.add_parser('pds-resynthesis-candidate-merge'); p155m.add_argument('study'); p155m.add_argument('--baseline-dir',required=True); p155m.add_argument('--batch-root',required=True); p155m.add_argument('--output-dir',required=True)
    p155s=sub.add_parser('pds-resynthesis-ladder-synthesize'); p155s.add_argument('study'); p155s.add_argument('--candidate-merged',required=True); p155s.add_argument('--output-dir',required=True)
    p155d=sub.add_parser('pds-resynthesis-deep-sweep'); p155d.add_argument('study'); p155d.add_argument('--ladder-ledger',required=True); p155d.add_argument('--output-dir',required=True); p155d.add_argument('--ladder-start',type=int,default=0); p155d.add_argument('--ladder-end',type=int); p155d.add_argument('--jobs',type=int,default=24); p155d.add_argument('--trials',type=int)
    p155dm=sub.add_parser('pds-resynthesis-deep-merge'); p155dm.add_argument('study'); p155dm.add_argument('--baseline-dir',required=True); p155dm.add_argument('--ladder-ledger',required=True); p155dm.add_argument('--batch-root',required=True); p155dm.add_argument('--output-dir',required=True)
    args=p.parse_args(argv); repo=Path(args.repo).resolve()
    try:
        if args.cmd=='environment':
            payload={'passed':True,'environment':environment_report(),'gates':{'failed':[],'passed':True}}
            _write_summary(Path(args.output_dir) if args.output_dir else None,payload); print(json.dumps(payload,indent=2)); return 0
        if args.cmd=='validate':
            doc=load_json(repo/args.study); errs=validate_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['schema-validation'],'passed':False}}
                _write_summary(Path(args.output_dir) if args.output_dir else None,payload); print(json.dumps(payload,indent=2)); return 2
            built=build_study(doc)
            payload={'passed':True,'raw':built['raw'],'legal_builds':len(built['builds']),'logical_pairings':len(built['pairs']),'variants':len(built['variants']),'sample_attempts':built['sample_attempts'],'diversity_attempts':built['diversity_attempts'],'space_counts':built['space_counts'],'gates':{'failed':[],'passed':True}}
            _write_summary(Path(args.output_dir) if args.output_dir else None,payload); print(json.dumps(payload,indent=2)); return 0
        if args.cmd=='parity':
            errs=run_parity(repo); payload={'passed':not errs,'cases':PARITY_CASE_COUNT,'errors':errs,'gates':{'failed':(['parity'] if errs else []),'passed':not errs}}
            _write_summary(Path(args.output_dir) if args.output_dir else None,payload); print(json.dumps(payload,indent=2)); return 0 if not errs else 3
        if args.cmd=='self-test':
            tests_dir=repo/'tools/simulation/tests'
            suite=unittest.defaultTestLoader.discover(str(tests_dir),pattern='test_*.py')
            result=unittest.TextTestRunner(verbosity=2).run(suite)
            payload={'passed':result.wasSuccessful(),'tests':{'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},'gates':{'failed':([] if result.wasSuccessful() else ['python-unit-tests']),'passed':result.wasSuccessful()}}
            _write_summary(Path(args.output_dir) if args.output_dir else None,payload); print(json.dumps(payload,indent=2)); return 0 if result.wasSuccessful() else 5
        if args.cmd=='run':
            s=run_study(repo,repo/args.study,repo/args.out,args.trials,args.jobs,'plan' if args.plan_only else 'run'); print(json.dumps(s,indent=2)); return 0 if not s.get('gate_failures') and not s.get('gates',{}).get('failed') else 4
        if args.cmd=='analyze':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            res=analyze(repo/args.primary,repo/args.overlay if args.overlay else None,outdir/'analysis.json')
            failed=list(res.get('failed_gates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 6
        if args.cmd=='analyze-cp104':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            res=analyze_cp104(repo/args.diagnostic,repo/args.cp103_primary,outdir/'analysis.json')
            failed=list(res.get('failed_gates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 7
        if args.cmd=='power-calibrate':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_power_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['power-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 8
            res=run_power_calibration(repo,study_path,outdir)
            failed=list(res.get('failedGates',[])); passed=not failed and int(res.get('trialErrors',0))==0
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 9
        if args.cmd=='ecology':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_ecology_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['ecology-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 10
            res=run_ecology(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 11
        if args.cmd=='neighbor-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_neighbor_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['neighbor-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 12
            res=run_neighbor_analysis(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 13
        if args.cmd=='payload-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_payload_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['payload-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 14
            res=run_payload_analysis(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 15
        if args.cmd=='weapon-family-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_weapon_family_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['weapon-family-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 16
            res=run_weapon_family_analysis(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 17
        if args.cmd=='warhead-generation-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_role_generation_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['warhead-generation-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 18
            res=run_role_generation_analysis(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 19
        if args.cmd=='simplified-weapon-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_simplified_progression_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['simplified-weapon-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 20
            res=run_simplified_progression_analysis(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 21
        if args.cmd=='weapon-integration-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_weapon_integration_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['weapon-integration-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 22
            res=run_weapon_integration_analysis(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 23
        if args.cmd=='weapon-sensitivity-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_weapon_sensitivity_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['weapon-sensitivity-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 24
            res=run_weapon_sensitivity_analysis(repo,study_path,outdir,args.trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 25
        if args.cmd=='damage-resolution-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_damage_resolution_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['damage-resolution-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 26
            res=run_damage_resolution_analysis(repo,study_path,outdir,args.trials,args.equivalence_trials,args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 27
        if args.cmd=='baseline-foundation':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_baseline_foundation_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['baseline-foundation-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 28
            res=run_baseline_foundation(repo,study_path,outdir)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 29
        if args.cmd=='fidelity-attribution-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_fidelity_attribution_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['fidelity-attribution-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 32
            res=run_fidelity_attribution(repo,study_path,outdir,mode=args.mode,trials=args.trials,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 33
        if args.cmd=='main-subsystem-stabilization-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_main_subsystem_stabilization_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['main-subsystem-stabilization-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 34
            res=run_main_subsystem_stabilization(repo,study_path,outdir,mode=args.mode,trials=args.trials,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 35
        if args.cmd=='whole-ladder-sensitivity-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_whole_ladder_sensitivity_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['whole-ladder-sensitivity-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 36
            res=run_whole_ladder_sensitivity(repo,study_path,outdir,mode=args.mode,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 37
        if args.cmd=='missile-progression-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_missile_progression_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['missile-progression-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 38
            res=run_missile_progression(repo,study_path,outdir,mode=args.mode,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 39
        if args.cmd=='late-missile-maturation-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_late_missile_maturation_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['late-missile-maturation-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 40
            res=run_late_missile_maturation(repo,study_path,outdir,mode=args.mode,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 41
        if args.cmd=='same-tl-candidate-baseline-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_same_tl_candidate_baseline_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['same-tl-candidate-baseline-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 42
            res=run_same_tl_candidate_baseline(repo,study_path,outdir,mode=args.mode,trials=args.trials,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 43
        if args.cmd=='auxiliary-integration-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_auxiliary_integration_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['auxiliary-integration-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 44
            res=run_auxiliary_integration(repo,study_path,outdir,mode=args.mode,trials=args.trials,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 45
        if args.cmd=='combat-model-reconciliation-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_def_res_reconciliation_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['combat-model-reconciliation-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 46
            res=run_def_res_reconciliation(repo,study_path,outdir)
            failed=list(res.get('failedGates',[])); passed=bool(res.get('passed')) and not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 47
        if args.cmd=='stage-a-integration-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_stage_a_integration_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['stage-a-integration-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 48
            res=run_stage_a_integration(repo,study_path,outdir,mode=args.mode,jobs=args.jobs,batch_start=args.batch_start,batch_end=args.batch_end)
            failed=list(res.get('failedGates',[])); passed=bool(res.get('passed')) and not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 49
        if args.cmd=='stage-a-integration-merge':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_stage_a_integration_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['stage-a-integration-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 50
            batch_root=Path(args.batch_root)
            if not batch_root.is_absolute(): batch_root=repo/batch_root
            res=merge_stage_a_integration_batches(repo,study_path,batch_root,outdir)
            failed=list(res.get('failedGates',[])); passed=bool(res.get('passed')) and not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 51
        if args.cmd=='combat-surface-reconciliation-audit':
            outdir=repo/args.output_dir; study_path=repo/args.study; doc=load_json(study_path); errs=validate_combat_surface_reconciliation_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['combat-surface-reconciliation-audit-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 44
            res=write_reconciliation_evidence(repo,doc['matrix'],outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 45
        if args.cmd=='combat-surface-reconciliation-study':
            outdir=repo/args.output_dir; study_path=repo/args.study; doc=load_json(study_path); errs=validate_combat_surface_reconciliation_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['combat-surface-reconciliation-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 46
            res=run_combat_surface_reconciliation_batch(repo,study_path,outdir,jobs=args.jobs,batch_start=args.batch_start,batch_end=args.batch_end)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 47
        if args.cmd=='combat-surface-reconciliation-merge':
            outdir=repo/args.output_dir; study_path=repo/args.study; doc=load_json(study_path); errs=validate_combat_surface_reconciliation_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['combat-surface-reconciliation-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 48
            res=merge_combat_surface_reconciliation_batches(repo,study_path,repo/args.batch_root,outdir)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 49
        if args.cmd=='missile-mirror-pacing-attribution-study':
            study_path=Path(args.study); outdir=Path(args.output_dir)
            doc=load_json(study_path); errs=validate_missile_mirror_pacing_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['missile-mirror-pacing-attribution-validation'],'passed':False}}
                print(json.dumps(payload,indent=2)); return 1
            res=run_missile_mirror_pacing_batch(repo,study_path,outdir,jobs=args.jobs,batch_start=args.batch_start,batch_end=args.batch_end)
            print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 1
        if args.cmd=='missile-mirror-pacing-attribution-merge':
            study_path=Path(args.study); batch_root=Path(args.batch_root); outdir=Path(args.output_dir)
            doc=load_json(study_path); errs=validate_missile_mirror_pacing_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['missile-mirror-pacing-attribution-merge-validation'],'passed':False}}
                print(json.dumps(payload,indent=2)); return 1
            res=merge_missile_mirror_pacing_batches(repo,study_path,batch_root,outdir)
            print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 1
        if args.cmd=='whole-combat-stage-a-smoke':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp144_stage_a_study(doc)+validate_cp144_stage_a_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['whole-combat-stage-a-smoke-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 56
            res=run_cp144_smoke_batch(repo,study_path,outdir,jobs=args.jobs,batch_start=args.batch_start,batch_end=args.batch_end)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 57
        if args.cmd=='whole-combat-stage-a-smoke-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True); batch_root=Path(args.batch_root)
            if not batch_root.is_absolute(): batch_root=repo/batch_root
            doc=load_json(study_path); errs=validate_cp144_stage_a_study(doc)+validate_cp144_stage_a_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['whole-combat-stage-a-smoke-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 58
            res=merge_cp144_smoke_batches(repo,study_path,batch_root,outdir)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 59
        if args.cmd=='whole-combat-stage-a-substantive':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp144_stage_a_study(doc)+validate_cp144_stage_a_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['whole-combat-stage-a-substantive-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 60
            res=run_cp144_substantive_batch(repo,study_path,outdir,jobs=args.jobs,batch_start=args.batch_start,batch_end=args.batch_end,trials_per_scenario=args.trials_per_scenario)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 61
        if args.cmd=='whole-combat-stage-a-substantive-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True); batch_root=Path(args.batch_root)
            if not batch_root.is_absolute(): batch_root=repo/batch_root
            doc=load_json(study_path); errs=validate_cp144_stage_a_study(doc)+validate_cp144_stage_a_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['whole-combat-stage-a-substantive-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 62
            res=merge_cp144_substantive_batches(repo,study_path,batch_root,outdir,expected_trials_per_scenario=args.trials_per_scenario)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 63
        if args.cmd=='stage-a-diagnostic-attribution':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp145_stage_a_diagnostic_study(doc)+validate_cp145_stage_a_diagnostic_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['stage-a-diagnostic-attribution-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 64
            res=run_cp145_stage_a_diagnostic(repo,study_path,outdir,jobs=args.jobs)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 65
        if args.cmd=='combat-resource-doctrine-validation':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp146_combat_resource_doctrine_study(doc)+validate_cp146_combat_resource_doctrine_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['combat-resource-doctrine-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 66
            res=run_cp146_combat_resource_doctrine(repo,study_path,outdir,jobs=args.jobs)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 67
        if args.cmd=='tactical-package-utility-validation':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp147_tactical_package_utility_study(doc)+validate_cp147_tactical_package_utility_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['tactical-package-utility-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 68
            res=run_cp147_tactical_package_utility(repo,study_path,outdir,jobs=args.jobs)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 69
        if args.cmd=='kinetic-full-characteristic-plan':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp149_kinetic_study(doc)+validate_cp149_kinetic_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['kinetic-full-characteristic-plan-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 70
            res=run_cp149_kinetic_plan(repo,study_path,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 71
        if args.cmd=='kinetic-full-characteristic-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp149_kinetic_study(doc)+validate_cp149_kinetic_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['kinetic-full-characteristic-sweep-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 72
            res=run_cp149_kinetic_batch(repo,study_path,outdir,jobs=args.jobs,tl=args.tl,candidate_start=args.candidate_start,candidate_end=args.candidate_end,trials=args.trials,smoke_panel=args.smoke_panel)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 73
        if args.cmd=='kinetic-full-characteristic-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp149_kinetic_study(doc)+validate_cp149_kinetic_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['kinetic-full-characteristic-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 74
            br=Path(args.batch_root); br=br if br.is_absolute() else repo/br
            res=merge_cp149_kinetic_batches(repo,study_path,br,outdir,expected_trials=args.trials); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 75
        if args.cmd=='kinetic-viable-region-plan':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp150_kinetic_study(doc)+validate_cp150_kinetic_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['kinetic-viable-region-plan-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 76
            res=run_cp150_kinetic_plan(repo,study_path,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 77
        if args.cmd=='kinetic-viable-region-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp150_kinetic_study(doc)+validate_cp150_kinetic_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['kinetic-viable-region-sweep-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 78
            res=run_cp150_kinetic_batch(repo,study_path,outdir,jobs=args.jobs,tl=args.tl,candidate_start=args.candidate_start,candidate_end=args.candidate_end,trials=args.trials,smoke_panel=args.smoke_panel)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 79
        if args.cmd=='kinetic-viable-region-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp150_kinetic_study(doc)+validate_cp150_kinetic_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['kinetic-viable-region-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 80
            br=Path(args.batch_root); br=br if br.is_absolute() else repo/br
            res=merge_cp150_kinetic_batches(repo,study_path,br,outdir,expected_trials=args.trials); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 81
        if args.cmd=='point-scale-plan':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp151_point_scale_study(doc)+validate_cp151_point_scale_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['point-scale-plan-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 82
            res=run_cp151_point_scale_plan(repo,study_path,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 83
        if args.cmd=='point-scale-equivalence':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp151_point_scale_study(doc)+validate_cp151_point_scale_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['point-scale-equivalence-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 84
            res=run_cp151_point_scale_equivalence(repo,study_path,outdir,jobs=args.jobs); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 85
        if args.cmd=='point-scale-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp151_point_scale_study(doc)+validate_cp151_point_scale_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['point-scale-sweep-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 86
            res=run_cp151_point_scale_batch(repo,study_path,outdir,jobs=args.jobs,tl=args.tl,candidate_start=args.candidate_start,candidate_end=args.candidate_end,trials=args.trials,smoke_panel=args.smoke_panel)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 87
        if args.cmd=='point-scale-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp151_point_scale_study(doc)+validate_cp151_point_scale_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['point-scale-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 88
            br=Path(args.batch_root); br=br if br.is_absolute() else repo/br
            res=merge_cp151_point_scale_batches(repo,study_path,br,outdir,expected_trials=args.trials); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 89
        if args.cmd=='direct-fire-refinement-plan':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp152_direct_fire_study(doc)+validate_cp152_direct_fire_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['direct-fire-refinement-plan-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 90
            res=run_cp152_direct_fire_plan(repo,study_path,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 91
        if args.cmd=='direct-fire-refinement-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            doc=load_json(study_path); errs=validate_cp152_direct_fire_study(doc)+validate_cp152_direct_fire_population(repo,doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['direct-fire-refinement-sweep-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 92
            res=run_cp152_direct_fire_lane_batch(repo,study_path,outdir,lane=args.lane,jobs=args.jobs,tl=args.tl,candidate_start=args.candidate_start,candidate_end=args.candidate_end,trials=args.trials,smoke_panel=args.smoke_panel)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 93
        if args.cmd=='direct-fire-refinement-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            br=Path(args.batch_root); br=br if br.is_absolute() else repo/br
            res=merge_cp152_direct_fire_lane(repo,study_path,args.lane,br,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 94
        if args.cmd=='direct-fire-joint-select':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            km=Path(args.k_merged); km=km if km.is_absolute() else repo/km; em=Path(args.e_merged); em=em if em.is_absolute() else repo/em
            res=select_cp152_direct_fire_joint(repo,study_path,km,em,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 95
        if args.cmd=='direct-fire-joint-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True); jl=Path(args.joint_ledger); jl=jl if jl.is_absolute() else repo/jl
            res=run_cp152_direct_fire_joint_batch(repo,study_path,jl,outdir,jobs=args.jobs,tl=args.tl,candidate_start=args.candidate_start,candidate_end=args.candidate_end,trials=args.trials)
            _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 96
        if args.cmd=='direct-fire-joint-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True); jl=Path(args.joint_ledger); jl=jl if jl.is_absolute() else repo/jl; br=Path(args.batch_root); br=br if br.is_absolute() else repo/br
            res=merge_cp152_direct_fire_joint(repo,study_path,jl,br,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 97
        if args.cmd=='four-main-ladder-plan':
            study_path=repo/args.study; outdir=repo/args.output_dir; res=run_cp153_plan(repo,study_path,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 98
        if args.cmd=='four-main-energy-closure':
            study_path=repo/args.study; outdir=repo/args.output_dir; res=run_cp153_energy_batch(repo,study_path,outdir,jobs=args.jobs,tl=args.tl,candidate_start=args.candidate_start,candidate_end=args.candidate_end,trials=args.trials,smoke_panel=args.smoke_panel); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 99
        if args.cmd=='four-main-energy-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; br=Path(args.batch_root); br=br if br.is_absolute() else repo/br; res=merge_cp153_energy(repo,study_path,br,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 100
        if args.cmd=='four-main-ladder-synthesize':
            study_path=repo/args.study; outdir=repo/args.output_dir; em=Path(args.energy_merged); em=em if em.is_absolute() else repo/em; res=synthesize_cp153_ladders(repo,study_path,em,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 101
        if args.cmd=='four-main-package-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; pl=Path(args.package_ledger); pl=pl if pl.is_absolute() else repo/pl; res=run_cp153_package_batch(repo,study_path,pl,outdir,args.mode,jobs=args.jobs,package_start=args.package_start,package_end=args.package_end,trials=args.trials); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 102
        if args.cmd=='four-main-package-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; pl=Path(args.package_ledger); pl=pl if pl.is_absolute() else repo/pl; br=Path(args.batch_root); br=br if br.is_absolute() else repo/br; res=merge_cp153_packages(repo,study_path,pl,br,outdir,args.mode); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 103
        if args.cmd=='four-main-deep-select':
            study_path=repo/args.study; outdir=repo/args.output_dir; pl=Path(args.package_ledger); pl=pl if pl.is_absolute() else repo/pl; sm=Path(args.screen_merged); sm=sm if sm.is_absolute() else repo/sm; res=select_cp153_deep(repo,study_path,pl,sm,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 104
        if args.cmd=='pds-closure-plan':
            study_path=repo/args.study; outdir=repo/args.output_dir; res=run_cp154_pds_plan(repo,study_path,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 105
        if args.cmd=='pds-closure-candidate-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; res=run_cp154_pds_candidate_batch(repo,study_path,outdir,args.family,args.tl,args.candidate_start,args.candidate_end,args.jobs,args.trials,args.smoke); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 106
        if args.cmd=='pds-closure-candidate-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; br=Path(args.batch_root); br=br if br.is_absolute() else repo/br; res=merge_cp154_pds_candidates(repo,study_path,br,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 107
        if args.cmd=='pds-closure-ladder-synthesize':
            study_path=repo/args.study; outdir=repo/args.output_dir; cm=Path(args.candidate_merged); cm=cm if cm.is_absolute() else repo/cm; res=synthesize_cp154_pds_ladders(repo,study_path,cm,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 108
        if args.cmd=='pds-closure-deep-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; ll=Path(args.ladder_ledger); ll=ll if ll.is_absolute() else repo/ll; res=run_cp154_pds_deep_batch(repo,study_path,ll,outdir,args.ladder_start,args.ladder_end,args.jobs,args.trials); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 109
        if args.cmd=='pds-closure-deep-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; ll=Path(args.ladder_ledger); ll=ll if ll.is_absolute() else repo/ll; br=Path(args.batch_root); br=br if br.is_absolute() else repo/br; res=merge_cp154_pds_deep(repo,study_path,ll,br,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 110
        if args.cmd=='pds-resynthesis-plan':
            study_path=repo/args.study; outdir=repo/args.output_dir; res=run_cp155_pds_plan(repo,study_path,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 111
        if args.cmd=='pds-resynthesis-baseline':
            study_path=repo/args.study; outdir=repo/args.output_dir; res=run_cp155_pds_baseline(repo,study_path,outdir,args.jobs,args.trials); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 112
        if args.cmd=='pds-resynthesis-candidate-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; res=run_cp155_pds_candidate_batch(repo,study_path,outdir,args.family,args.tl,args.candidate_start,args.candidate_end,args.jobs,args.trials,args.smoke); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 113
        if args.cmd=='pds-resynthesis-candidate-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; bd=Path(args.baseline_dir); bd=bd if bd.is_absolute() else repo/bd; br=Path(args.batch_root); br=br if br.is_absolute() else repo/br; res=merge_cp155_pds_candidates(repo,study_path,bd,br,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 114
        if args.cmd=='pds-resynthesis-ladder-synthesize':
            study_path=repo/args.study; outdir=repo/args.output_dir; cm=Path(args.candidate_merged); cm=cm if cm.is_absolute() else repo/cm; res=synthesize_cp155_pds_ladders(repo,study_path,cm,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 115
        if args.cmd=='pds-resynthesis-deep-sweep':
            study_path=repo/args.study; outdir=repo/args.output_dir; ll=Path(args.ladder_ledger); ll=ll if ll.is_absolute() else repo/ll; res=run_cp155_pds_deep_batch(repo,study_path,ll,outdir,args.ladder_start,args.ladder_end,args.jobs,args.trials); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 116
        if args.cmd=='pds-resynthesis-deep-merge':
            study_path=repo/args.study; outdir=repo/args.output_dir; bd=Path(args.baseline_dir); bd=bd if bd.is_absolute() else repo/bd; ll=Path(args.ladder_ledger); ll=ll if ll.is_absolute() else repo/ll; br=Path(args.batch_root); br=br if br.is_absolute() else repo/br; res=merge_cp155_pds_deep(repo,study_path,bd,ll,br,outdir); _write_summary(outdir,res); print(json.dumps(res,indent=2)); return 0 if res.get('passed') else 117
        if args.cmd=='combat-duration-stalemate-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_combat_duration_stalemate_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['combat-duration-stalemate-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 52
            res=run_combat_duration_stalemate_batch(repo,study_path,outdir,jobs=args.jobs,batch_start=args.batch_start,batch_end=args.batch_end)
            failed=list(res.get('failedGates',[])); passed=bool(res.get('passed')) and not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 53
        if args.cmd=='combat-duration-stalemate-merge':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_combat_duration_stalemate_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['combat-duration-stalemate-merge-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 54
            batch_root=Path(args.batch_root)
            if not batch_root.is_absolute(): batch_root=repo/batch_root
            res=merge_combat_duration_stalemate_batches(repo,study_path,batch_root,outdir)
            failed=list(res.get('failedGates',[])); passed=bool(res.get('passed')) and not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 55
        if args.cmd=='whole-ladder-study':
            outdir=repo/args.output_dir; outdir.mkdir(parents=True,exist_ok=True)
            study_path=repo/args.study
            doc=load_json(study_path); errs=validate_whole_ladder_study(doc)
            if errs:
                payload={'passed':False,'errors':errs,'gates':{'failed':['whole-ladder-study-validation'],'passed':False}}
                _write_summary(outdir,payload); print(json.dumps(payload,indent=2)); return 30
            res=run_whole_ladder_analysis(repo,study_path,outdir,mode=args.mode,trials=args.trials,jobs=args.jobs)
            failed=list(res.get('failedGates',[])); passed=not failed
            payload={'passed':passed,'analysis':res,'gates':{'failed':failed,'passed':passed},'failedGates':len(failed)}
            (outdir/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); print(json.dumps(res,indent=2)); return 0 if passed else 31
    except Exception as exc:
        payload={'passed':False,'error':f'{type(exc).__name__}: {exc}','gates':{'failed':['exception'],'passed':False}}
        outdir=None
        if getattr(args,'output_dir',None): outdir=Path(args.output_dir)
        elif getattr(args,'out',None): outdir=Path(args.out)
        _write_summary(outdir,payload); print(json.dumps(payload,indent=2),file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
