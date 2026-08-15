#!/usr/bin/env python3
"""Integrate parsed 주역전의 into korean_translations.json.

Strategy (G002):
- Keep the existing ko.wikisource machine translation as the user-facing
  `judgment_ko` / `lines_ko` baseline.
- Add the Vault 주역전의 structured parse as a parallel reference layer:
  `juyeok_jeonui` per hexagram with {judgment_hanmun, judgment_to,
  great_image_hanmun, great_image_to, line_texts, commentary}.
- Promote source_hierarchy: Vault 주역전의 status reference_only → integrated_reference.
- Every user-facing field stays hangul-only; hanmun is confined to the
  reference layer and never emitted to user-facing responses.
"""

from __future__ import annotations

import json
from pathlib import Path

ENGINE_DATA = Path(__file__).resolve().parent / "data"
KOREAN_PATH = ENGINE_DATA / "korean_translations.json"
PARSED_PATH = ENGINE_DATA / "juyeok_jeonui_parsed.json"


def main() -> int:
    korean = json.loads(KOREAN_PATH.read_text(encoding="utf-8"))
    parsed = json.loads(PARSED_PATH.read_text(encoding="utf-8"))

    hexagrams = korean.get("hexagrams", {})
    jeonui = parsed.get("hexagrams", {})
    merged = 0
    for hid, g in jeonui.items():
        target = hexagrams.get(hid)
        if target is None:
            continue
        target["juyeok_jeonui"] = {
            "source": "주역/03_한국어_역주 (주역전의 상·하)",
            "quality": "structured_parse_reference",
            "judgment_hanmun": g.get("judgment_hanmun", ""),
            "judgment_to": g.get("judgment_to", ""),
            "great_image_hanmun": g.get("great_image_hanmun", ""),
            "great_image_to": g.get("great_image_to", ""),
            "line_texts": g.get("line_texts", {}),
            "commentary_count": len(g.get("commentary", [])),
        }
        merged += 1

    # source_hierarchy 승격: reference_only → integrated_reference
    hierarchy = korean.get("source_hierarchy", [])
    for entry in hierarchy:
        if "주역전의" in str(entry.get("source", "")):
            entry["status"] = "integrated_reference"
            entry["note"] = "구조화 파싱 완료 — hanmun/to 분리, 사용자 노출은 한글만"
    korean["source_hierarchy"] = hierarchy
    korean["source"] = "주역/03_한국어_역주 + ko.wikisource"
    korean["quality_policy"] = "reference_integrated_hangul_only"
    korean["schema_version"] = 2

    KOREAN_PATH.write_text(json.dumps(korean, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"통합 괘: {merged}/64")
    print(f"korean_translations.json 업데이트: schema v{korean['schema_version']}, quality_policy={korean['quality_policy']}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
