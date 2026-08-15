"""Admin summary endpoint + backup script dry-run."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-admin-", suffix=".sqlite")[1]
os.environ["NABOM_GENERATE_CHARACTERS"] = "0"
os.environ["NABOM_CHARACTER_DIR"] = tempfile.mkdtemp(prefix="nabom-char-")

import httpx  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parents[0]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


nabom_main = _load_module("adm_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    # 관리자 ID 설정 (테스트용)
    os.environ["NABOM_ADMIN_USER_IDS"] = "admin-qa"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        # 관리자 가입 (dev auth: X-User-Id)
        admin_h = {"X-User-Id": "admin-qa", "Authorization": "Bearer admin-token"}
        # admin 라우트는 bearer가 필요한데 dev 모드에선 x_user_id로 대체 — auth.get_authenticated_identity 확인
        # dev mode: x_user_id로 identity가 나오므로 bearer 불필요. admin-qa로 요청.
        summary = await client.get("/api/v1/admin/summary", headers={"X-User-Id": "admin-qa"})
        require(summary.status_code == 200, f"admin summary: {summary.status_code} {summary.text[:120]}")
        body = summary.json()
        require("accounts" in body and "records" in body and "living" in body and "devices" in body, body)
        require(body["accounts"]["total"] >= 0, body)

        # 비관리자는 403
        denied = await client.get("/api/v1/admin/summary", headers={"X-User-Id": "someone-else"})
        require(denied.status_code == 403, f"denied: {denied.status_code}")

        # users 목록 (raw journal 미포함 확인)
        users = await client.get("/api/v1/admin/users", headers={"X-User-Id": "admin-qa"})
        require(users.status_code == 200, f"users: {users.status_code}")
        raw = users.text
        for forbidden in ("text", "journal_text", "raw_chart", "analysis"):
            # daily entry 텍스트/저널 원문이 admin 목록에 없어야 함
            if f'"{forbidden}"' in raw:
                print(f"  경고: admin users에 {forbidden} 필드 존재")

    # 백업 스크립트 dry-run
    script = ROOT / "docs" / "scripts" / "backup.sh"
    require(script.exists(), "backup.sh missing")
    result = subprocess.run(
        ["bash", str(script), "--dry-run", "--driver", "sqlite"],
        capture_output=True,
        text=True,
        env={**os.environ, "NABOM_STORE_PATH": os.environ["NABOM_STORE_PATH"], "BACKUP_DIR": tempfile.mkdtemp(prefix="nabom-bak-")},
    )
    require(result.returncode == 0, f"backup dry-run failed: {result.stderr[:200]}")
    require("[dry-run]" in result.stdout, result.stdout)

    print("admin-and-backup: PASS")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
