"""Focused tests for NFC token lifecycle, deletion, and 21-day entitlement."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-nfc-", suffix=".sqlite")[1]
os.environ["NABOM_GENERATE_CHARACTERS"] = "0"
os.environ["NABOM_CHARACTER_DIR"] = tempfile.mkdtemp(prefix="nabom-char-")


import httpx  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


nabom_main = _load_module("nabom_nfc_app_main", BACKEND / "nabom-api" / "app" / "main.py")
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        issued = await client.post("/api/v1/nfc/tokens", headers={"X-User-Id": "usr_a"})
        require(issued.status_code == 200, issued.text)
        token = issued.json()["token"]
        require("usr_" not in token, token)

        anonymous = await client.get(f"/api/v1/nfc/resolve/{token}")
        require(anonymous.status_code == 200, anonymous.text)
        require(anonymous.json()["status"] == "unlinked", anonymous.json())
        require(anonymous.json()["analysis_result_included"] is False, anonymous.json())

        claimed = await client.post(f"/api/v1/nfc/tokens/{token}/claim", headers={"X-User-Id": "usr_a"})
        require(claimed.status_code == 200, claimed.text)
        require(claimed.json()["owned_by_requester"] is True, claimed.json())

        owner = await client.get(f"/api/v1/nfc/resolve/{token}", headers={"X-User-Id": "usr_a"})
        require(owner.json()["status"] == "owner", owner.json())
        other = await client.get(f"/api/v1/nfc/resolve/{token}", headers={"X-User-Id": "usr_b"})
        require(other.json()["status"] == "other_account", other.json())
        require("owner_user_id" not in other.json(), other.json())
        login = await client.get(f"/api/v1/nfc/resolve/{token}")
        require(login.json()["status"] == "login_required", login.json())

        stolen = await client.post(f"/api/v1/nfc/tokens/{token}/revoke", headers={"X-User-Id": "usr_b"})
        require(stolen.status_code == 403, stolen.text)

        replaced = await client.post(f"/api/v1/nfc/tokens/{token}/replace", headers={"X-User-Id": "usr_a"})
        require(replaced.status_code == 200, replaced.text)
        require(replaced.json()["revoked"]["status"] == "revoked", replaced.json())
        new_token = replaced.json()["replacement"]["token"]
        require(new_token != token, replaced.json())
        old = await client.get(f"/api/v1/nfc/resolve/{token}", headers={"X-User-Id": "usr_a"})
        require(old.json()["status"] == "revoked", old.json())
        stolen_after = await client.post(f"/api/v1/nfc/tokens/{token}/replace", headers={"X-User-Id": "usr_b"})
        require(stolen_after.status_code == 403, stolen_after.text)

        created = await client.post(
            "/api/v1/living/entries",
            json={"date": "2026-08-01", "mood": 3, "energy": 3, "satisfaction": 3, "text": "비밀 일기"},
            headers={"X-User-Id": "usr_a"},
        )
        entry_id = created.json()["entry_id"]
        evidence = await client.post(
            "/api/v1/living/evidence",
            json={"source_type": "daily", "source_record_id": entry_id},
            headers={"X-User-Id": "usr_a"},
        )
        require(evidence.status_code == 200, evidence.text)
        deleted = await client.delete(f"/api/v1/living/entries/{entry_id}", headers={"X-User-Id": "usr_a"})
        require(deleted.status_code == 200, deleted.text)
        require(deleted.json()["invalidated_evidence"] == 1, deleted.json())
        gone = await client.get(f"/api/v1/living/entries/{entry_id}", headers={"X-User-Id": "usr_a"})
        require(gone.status_code == 404, gone.text)

        for index in range(21):
            day = f"2026-07-{(index + 1):02d}"
            await client.post(
                "/api/v1/living/entries",
                json={"date": day, "mood": 3, "energy": 3, "satisfaction": 3},
                headers={"X-User-Id": "usr_a"},
            )
        report = await client.get("/api/v1/living/reports/21-day", headers={"X-User-Id": "usr_a"})
        require(report.status_code == 200, report.text)
        require(report.json()["eligible"] is True, report.json())
        require(report.json()["distinct_recorded_days"] >= 21, report.json())

        rel = await client.post("/api/v1/relationships", json={"participant_user_id": "usr_b"}, headers={"X-User-Id": "usr_a"})
        rel_id = rel.json()["relationship_id"]
        grant = await client.post(
            f"/api/v1/relationships/{rel_id}/consent",
            json={"scopes": ["relationship_mirror"]},
            headers={"X-User-Id": "usr_a"},
        )
        require(grant.status_code == 200, grant.text)
        audits = [item for item in nabom_main.store.list("consent_audits") if item.get("subject_id") == rel_id]
        require(len(audits) == 1, audits)
        require(set(audits[0]) >= {"actor", "scopes", "policy_version", "reason", "timestamp"}, audits[0])

        wipe = await client.post("/api/v1/privacy/delete-account", headers={"X-User-Id": "usr_a"})
        require(wipe.status_code == 200, wipe.text)
        stored = nabom_main.store.get("relationships", rel_id)
        require(stored["state"] == "revoked", stored)
        require(not stored.get("birth_inputs"), stored)
        emptied = await client.get("/api/v1/living/entries", headers={"X-User-Id": "usr_a"})
        require(emptied.json()["entries"] == [], emptied.json())


if __name__ == "__main__":
    asyncio.run(run())
    print("nfc-privacy-contract: PASS")
