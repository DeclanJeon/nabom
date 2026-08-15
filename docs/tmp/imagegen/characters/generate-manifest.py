from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ASSET_DIR = ROOT / "frontend" / "public" / "characters" / "stage"
OUT = ASSET_DIR / "manifest.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key_for(path: Path) -> tuple[str, str]:
    parts = path.stem.split("_")[:4]
    if len(parts) == 3:
        return path.stem, "base"
    if len(parts) == 4:
        return path.stem, parts[-1]
    return path.stem, "unknown"


def rel(path: Path) -> str:
    return str(path.relative_to(ASSET_DIR)).replace(os.sep, "/")


import os  # noqa: E402

assets = []
for png in sorted(ASSET_DIR.rglob("*.png")):
    if png.name == "manifest.json":
        continue
    key, state = key_for(png)
    gif = png.with_suffix(".gif")
    assets.append(
        {
            "key": key,
            "state": state,
            "png": rel(png),
            "gif": rel(gif) if gif.exists() else None,
            "sha256_png": digest(png),
            "sha256_gif": digest(gif) if gif.exists() else None,
            "qa_status": "generated",
        }
    )

manifest = {
    "manifest_version": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    "asset_count": len(assets),
    "assets": assets,
}
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(OUT, len(assets))
