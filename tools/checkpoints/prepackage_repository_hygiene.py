#!/usr/bin/env python3
from __future__ import annotations
import argparse, re, shutil
from pathlib import Path

ROOT_PATTERNS = (
    re.compile(r'^CHECKPOINT_(\d+[A-Za-z]*)_SHA256SUMS\.txt$', re.I),
    re.compile(r'^SHA256SUMS(?:[-_].*)?\.txt$', re.I),
)
DISPOSABLE_ROOT_NAMES = {
    'repository_manifest.txt', 'manifest.sha256', 'sha256sums.txt',
}

# Successor repositories preserve compact acceptance/summary evidence and hashes,
# rather than recursively nesting large native-result archives. Reference-library
# archives live outside docs/validation/evidence and are intentionally unaffected.
MAX_VALIDATION_EVIDENCE_ARCHIVE_BYTES = 5 * 1024 * 1024
MAX_VALIDATION_EVIDENCE_ARCHIVES_TOTAL_BYTES = 16 * 1024 * 1024


def stale_root_artifacts(repo: Path) -> list[Path]:
    found=[]
    for p in repo.iterdir():
        if not p.is_file():
            continue
        if p.name.lower() in DISPOSABLE_ROOT_NAMES or any(rx.match(p.name) for rx in ROOT_PATTERNS):
            found.append(p)
    return sorted(found, key=lambda p:p.name.lower())


def validation_evidence_archives(repo: Path) -> list[Path]:
    root=repo/'docs'/'validation'/'evidence'
    if not root.exists():
        return []
    return sorted((p for p in root.rglob('*.zip') if p.is_file()), key=lambda p:p.as_posix().lower())


def oversized_validation_evidence_archives(repo: Path) -> list[Path]:
    return [p for p in validation_evidence_archives(repo) if p.stat().st_size > MAX_VALIDATION_EVIDENCE_ARCHIVE_BYTES]


def validation_evidence_archive_total_bytes(repo: Path) -> int:
    return sum(p.stat().st_size for p in validation_evidence_archives(repo))


def checkpoint_token(name: str) -> str | None:
    m=ROOT_PATTERNS[0].match(name)
    return m.group(1).lower() if m else None


def apply_cleanup(repo: Path) -> list[tuple[str,str]]:
    moves=[]
    for p in stale_root_artifacts(repo):
        token=checkpoint_token(p.name)
        if token:
            dest_dir=repo/'docs'/'validation'/'evidence'/f'checkpoint-{token}'
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest=dest_dir/'REPOSITORY_MANIFEST_SHA256SUMS.txt'
            if dest.exists() and dest.read_bytes()!=p.read_bytes():
                raise RuntimeError(f'archive collision with different content: {dest}')
            if not dest.exists():
                shutil.copy2(p,dest)
            moves.append((p.relative_to(repo).as_posix(),dest.relative_to(repo).as_posix()))
        else:
            moves.append((p.relative_to(repo).as_posix(),'<removed-disposable-root-artifact>'))
        p.unlink()
    return moves


def check_repository_hygiene(repo: Path) -> list[str]:
    errors=[]
    found=stale_root_artifacts(repo)
    if found:
        errors.append('stale root checksum/manifest artifacts remain: ' + ', '.join(p.name for p in found))

    archives=validation_evidence_archives(repo)
    oversized=oversized_validation_evidence_archives(repo)
    if oversized:
        errors.append(
            'validation evidence contains archive(s) larger than 5 MiB; curate accepted summaries/hashes instead of nesting raw predecessor results: '
            + ', '.join(f'{p.relative_to(repo).as_posix()} ({p.stat().st_size} bytes)' for p in oversized)
        )
    total=validation_evidence_archive_total_bytes(repo)
    if total > MAX_VALIDATION_EVIDENCE_ARCHIVES_TOTAL_BYTES:
        errors.append(
            f'validation evidence nested-archive total is {total} bytes, exceeding the 16 MiB repository packaging budget; '
            'externalize raw predecessor results and retain compact provenance.'
        )
    return errors


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply',action='store_true')
    mode.add_argument('--check',action='store_true')
    args=ap.parse_args()
    repo=Path(args.repo).resolve()
    if args.apply:
        moves=apply_cleanup(repo)
        print(f'Prepackage hygiene removed {len(moves)} stale root artifact(s).')
        for src,dst in moves:
            print(f'  {src} -> {dst}')
        return 0
    errors=check_repository_hygiene(repo)
    if errors:
        print('Prepackage hygiene failure:')
        for e in errors:
            print('  '+e)
        return 1
    archives=validation_evidence_archives(repo)
    total=validation_evidence_archive_total_bytes(repo)
    print(f'Prepackage hygiene verified: no stale root checksum/manifest artifacts; {len(archives)} validation evidence ZIP(s), {total} total bytes, all within retention limits.')
    return 0
if __name__=='__main__': raise SystemExit(main())
