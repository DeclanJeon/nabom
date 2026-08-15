"""Tests for the release lock gate (engine source/data pinning)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "release"))

from verify_engine_lock import collect_hashes, update_manifest, verify_manifest  # noqa: E402


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def _seed(root: Path):
    (root / "engine").mkdir(parents=True)
    (root / "engine" / "a.py").write_text("VERSION=1\n", encoding="utf-8")
    (root / "engine" / "b.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    (root / "engine" / "__pycache__").mkdir()
    (root / "engine" / "__pycache__" / "junk.pyc").write_bytes(b"junk")


def test_lock_update_and_verify():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = root / "release" / "engine-lock.json"
        _seed(root / "saju")
        payload = update_manifest(root / "saju", manifest)
        require(payload["entry_count"] == 2, f"should lock 2 files, got {payload['entry_count']}")
        result = verify_manifest(root / "saju", manifest)
        require(result["ok"], f"verify should pass: {result['errors']}")


def test_lock_detects_mismatch_and_extra():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = root / "release" / "engine-lock.json"
        engine = root / "saju"
        _seed(engine)
        update_manifest(engine, manifest)

        # 1) 내용 변경
        (engine / "engine" / "a.py").write_text("VERSION=2\n", encoding="utf-8")
        result = verify_manifest(engine, manifest)
        require(not result["ok"], "hash mismatch should fail")
        require(any("a.py" in e for e in result["errors"]), f"mismatch should name file: {result['errors']}")

        # 원복 후
        (engine / "engine" / "a.py").write_text("VERSION=1\n", encoding="utf-8")

        # 2) 미등록 추가 파일
        (engine / "engine" / "c.json").write_text("{}", encoding="utf-8")
        result = verify_manifest(engine, manifest)
        require(not result["ok"], "extra file should fail")
        require(any("c.json" in e for e in result["errors"]), f"extra should name file: {result['errors']}")

        # 3) 누락 파일
        (engine / "engine" / "c.json").unlink()
        (engine / "engine" / "b.csv").unlink()
        result = verify_manifest(engine, manifest)
        require(not result["ok"], "missing file should fail")
        require(any("b.csv" in e for e in result["errors"]), f"missing should name file: {result['errors']}")


def test_lock_ignores_pycache_and_venv():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed(root / "saju")
        hashes = collect_hashes(root / "saju")
        require("engine/__pycache__/junk.pyc" not in hashes, "pycache must be ignored")


def main():
    test_lock_update_and_verify()
    test_lock_detects_mismatch_and_extra()
    test_lock_ignores_pycache_and_venv()
    print("release lock tests passed")


if __name__ == "__main__":
    main()
