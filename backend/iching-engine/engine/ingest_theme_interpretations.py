#!/usr/bin/env python3
"""Ingest 05_주제별_해석 topic interpretations into theme_interpretations.json.

Formats handled (2026-08-12):
- `## N. 괘명(...)` → N is hexagram id (성장/역할/출세/재물)
- `## N. 제M괘 ...` → M is hexagram id (연결)
- `## N. 괘명(XX) · ...` or `## N. 괘명(괘명, XX)` → (XX) is id (위기/성공)
- falls back to N when it is a valid hexagram id AND heading contains dataset name_ko
Quality: reference interpretation layer (not canonical classical text).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ENGINE_DATA = Path(__file__).resolve().parent / "data"

# Obsidian Vault 원본. 환경변수 NABOM_THEME_TOPIC_DIR로 재정의 가능.
_env_topic = os.environ.get("NABOM_THEME_TOPIC_DIR", "").strip()
if _env_topic and Path(_env_topic).is_dir():
    TOPIC_DIR = Path(_env_topic)
else:
    home = Path.home()
    TOPIC_DIR = (
        home
        / "Documents"
        / "Obsidian Vault"
        / "주역"
        / "05_주제별_해석"
    )


def load_names() -> dict[int, tuple[str, str]]:
    dataset = json.loads((ENGINE_DATA / "dataset.json").read_text(encoding="utf-8"))
    return {h["hexagram_id"]: (h.get("name_ko", ""), h.get("name_zh", "")) for h in dataset["hexagrams"]}


def resolve_hexagram_id(n: int, heading: str, names: dict[int, tuple[str, str]]) -> int | None:
    m = re.search(r"제(\d{1,2})괘", heading)
    if m and 1 <= int(m.group(1)) <= 64:
        return int(m.group(1))
    # 닫는괄호 직전 숫자: (10), (風山漸, 53), (火山旅) 제외
    m = re.search(r"(\d{1,2})\s*\)", heading)
    if m and 1 <= int(m.group(1)) <= 64:
        return int(m.group(1))
    if 1 <= n <= 64:
        ko, zh = names.get(n, ("", ""))
        if zh and zh in heading:
            return n
        if ko and ko in heading:
            return n
    # 괘번호가 제목에만 있는 경우: 전체 64괘 한자 대조
    # 주의: 상하괘 표기(兌下震上 등)의 삼괘 문자는 괘명과 충돌하므로 제외
    TRIGRAMS = {"乾", "坤", "震", "巽", "坎", "離", "艮", "兌"}
    candidates = [(hid, zh) for hid, (ko, zh) in names.items() if zh and zh not in TRIGRAMS]
    candidates.sort(key=lambda x: -len(x[1]))  # 긴 이름 우선
    for hid, zh in candidates:
        if zh in heading:
            return hid
    return None


def main() -> int:
    names = load_names()
    files = sorted(TOPIC_DIR.glob("0*.md"))
    topics: dict[str, dict] = {}
    by_hexagram: dict[int, list[dict]] = {}
    skipped = []
    for f in files:
        if f.name.startswith("00_"):
            continue
        topic = f.stem.split("_", 1)[1] if "_" in f.stem else f.stem
        text = f.read_text(encoding="utf-8")
        sections = list(re.finditer(r"^#{1,2}\s*(\d+)\.\s*([^\n]*)", text, re.M))
        entries = []
        for i, m in enumerate(sections):
            n = int(m.group(1))
            heading = m.group(2).strip()
            hid = resolve_hexagram_id(n, heading, names)
            if hid is None:
                skipped.append((f.name, n, heading[:30]))
                continue
            end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
            section = text[m.start():end]
            # 렌즈 텍스트 우선순위: '사용자 추가 적용' 불릿(짧은 일상어) →
            # '적용 질문/행동' 첫 줄 → '###' 블록 요약 → 헤딩 폴백
            lens = ""
            user_bullet = re.search(r"^\- \*\*사용자 추가 적용\*\*:\s*([^\n]+)", section, re.M)
            if user_bullet:
                lens = user_bullet.group(1).strip()
            if not lens:
                action_q = re.search(r"^\- \*\*적용 질문/행동\*\*:\s*\n\s*1\.\s*([^\n]+)", section, re.M)
                if action_q:
                    lens = action_q.group(1).strip()
            if not lens:
                lens_blocks = re.findall(r"^###\s*[^\n]*\n(.*?)(?=^###|\Z)", section, re.M | re.S)
                lens = " ".join(re.sub(r"\s+", " ", b).strip() for b in lens_blocks)[:400]
            if not lens:
                lens = heading
            entries.append({"hexagram_id": hid, "lens": lens})
            by_hexagram.setdefault(hid, []).append({"topic": topic, "lens": lens})
        topics[topic] = {"file": f.name, "hexagram_count": len(entries), "hexagram_ids": sorted(e["hexagram_id"] for e in entries)}
        print(f"[{topic}] {len(entries)}괘 매핑")

    out = {
        "schema_version": 1,
        "source": "주역/05_주제별_해석",
        "quality_policy": "reference_interpretation_layer",
        "topics": topics,
        "hexagram_topics": {str(k): v for k, v in sorted(by_hexagram.items())},
    }
    ENGINE_DATA.mkdir(parents=True, exist_ok=True)
    (ENGINE_DATA / "theme_interpretations.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n주제 {len(topics)}개 / 괘 매핑 {len(by_hexagram)}개 / 스킵 {len(skipped)}건")
    for s in skipped[:8]:
        print("  스킵:", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
