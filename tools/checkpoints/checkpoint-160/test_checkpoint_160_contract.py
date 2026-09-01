#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

MAN = 'docs/validation/evidence/checkpoint-160/CP160_REPOSITORY_SHA256SUMS.txt'


def req(value, message):
    if not value:
        raise AssertionError(message)


def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def js(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def manifest(path: Path):
    out = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():
            h, rel = line.split('  ', 1); out[rel] = h
    return out


def owned(repo: Path):
    out = set()
    for path in repo.rglob('*'):
        if not path.is_file(): continue
        rel = path.relative_to(repo).as_posix(); wrapped = '/' + rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in wrapped or rel.endswith('.pyc') or '/bin/' in wrapped or '/obj/' in wrapped or '/TestResults/' in wrapped or rel == MAN:
            continue
        if rel.startswith('StarCluster_CP160_native_results_') and rel.endswith('.zip'):
            continue
        out.add(rel)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo', required=True); ap.add_argument('--native-results', required=True); args = ap.parse_args()
    repo = Path(args.repo).resolve(); nr = Path(args.native_results).resolve()
    try:
        man = manifest(repo/MAN); cur = owned(repo)
        req(set(man) == cur, f'manifest path drift added={sorted(cur-set(man))[:10]} missing={sorted(set(man)-cur)[:10]}')
        req(all(sha(repo/rel) == expected for rel, expected in man.items()), 'manifest hash mismatch')
        req(len(man) > 3310, 'owned count did not advance')
        final_path = nr/'CP160_NATIVE_ACCEPTANCE_SUMMARY.json'; repo_only = nr/'CP160_REPOSITORY_ONLY_ACCEPTANCE.json'
        summary = js(final_path if final_path.exists() else repo_only)
        req(summary['checkpoint'] == 160 and summary['pythonTestsPassed'] == 628 and summary['xunitPassed'] == 934 and summary['researchParityPassed'] == 25 and summary['cp160FocusedTestsPassed'] == 24, 'regression acceptance')
        req(summary['pendingFinalizationBaselineId'] == 'CP160-PF4' and not summary['productionAuthorityChanged'], 'authority boundary')
        req(summary['substantiveCombatTrials'] == 0 and summary['repairDroneMicroTrials'] == 0 and not summary['tuningAllowed'], 'zero-combat boundary')
        req(summary['isolatedAuxMagnitudeArchitectureClosed'] and summary['poweredAuxTpCostsRemainProvisional'], 'AUX closure boundary')
        req(summary['fieldStabilizerTrajectory'] == '16/18/20@1TP' and summary['crystallineTrajectory'] == 'CRY_RISE_A' and summary['repairDroneKitRule'] == '+100% default prepared kit reserve', 'selected AUX closure')
        req(summary['nextPass'] == 'Reactor/TP Scarcity and Whole-Ship Equilibrium', 'next pass')
        if final_path.exists():
            req(summary['repositoryOnlyAccepted'] and summary['baselinePromotionCompleted'], 'final acceptance state')
        print(f'CP160 contract PASS: {len(man)} repository-owned files; CP160-PF4 AUX closure authority preserved; zero substantive combats; production authority unchanged; Reactor/TP is the sole remaining major balance dependency.')
        return 0
    except Exception as exc:
        print(f'CP160 contract failure: {exc}', file=__import__('sys').stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
