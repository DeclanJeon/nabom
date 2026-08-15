#!/usr/bin/env python3
"""NABOM engine release lock: pin engine source+data hashes for deployments.

Usage:
  python verify_engine_lock.py --update --root backend/saju-engine --manifest backend/release/engine-lock.json
  python verify_engine_lock.py --verify --root backend/saju-engine --manifest backend/release/engine-lock.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

IGNORED_DIRS = {"__pycache__", ".venv", ".git", "node_modules"}
HASHED_SUFFIXES = {".py", ".csv", ".json", ".md"}


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_hashes(root: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in HASHED_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        entries[rel] = _hash_file(path)
    return entries


def update_manifest(root: Path, manifest: Path) -> dict:
    entries = collect_hashes(root)
    payload = {
        "lock_version": 1,
        "root": root.resolve().as_posix(),
        "entry_count": len(entries),
        "entries": entries,
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def verify_manifest(root: Path, manifest: Path) -> dict:
    if not manifest.exists():
        return {"ok": False, "errors": ["manifest missing: run --update first"]}
    locked = json.loads(manifest.read_text(encoding="utf-8"))
    current = collect_hashes(root)
    errors: list[str] = []
    for rel, locked_hash in locked["entries"].items():
        if rel not in current:
            errors.append(f"missing: {rel}")
            continue
        if current[rel] != locked_hash:
            errors.append(f"hash mismatch: {rel}")
    for rel in current:
        if rel not in locked["entries"]:
            errors.append(f"unlocked extra file: {rel}")
    return {"ok": not errors, "errors": errors, "locked_count": len(locked["entries"]), "current_count": len(current)}


def main():
    parser = argparse.ArgumentParser(description="NABOM engine release lock")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--update", action="store_true", help="write the lock manifest")
    group.add_argument("--verify", action="store_true", help="verify against the lock manifest")
    args = parser.parse_args()

    if args.update:
        payload = update_manifest(args.root, args.manifest)
        print(json.dumps({"ok": True, "action": "update", "entry_count": payload["entry_count"]}, ensure_ascii=False))
        return
    result = verify_manifest(args.root, args.manifest)
    print(json.dumps(result, ensure_ascii=False))
    if not result["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
