#!/usr/bin/env python3
"""Parse 주역전의(周易傳義) raw text into structured hexagram translations.

Input: Obsidian Vault 03_한국어_역주/0{1,2}_주역전의_{상,하}*.md
  - `### N. 괘명 [Cxx]` headings delimit hexagram sections
  - Inline markers: 彖曰(judgment), 象曰(great image), 初九..上九/用九(lines)
  - `傳` / `[傳]` lines are commentary (程伊川/朱子), kept separately
  - Text mixes hanja original + hangul-t'o (조사/어미); the parser splits them

Output: structured JSON per hexagram:
  { hexagram_id, name_ko, judgment_hanmun, judgment_to (한글토 해석),
    great_image_hanmun, great_image_to, lines: {label: {hanmun, to, commentary}},
    commentary: [..] }
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 한글토: 현대한글 + 옛한글 자모(ㅣ니라/니/야/면/고/며/로다/리라 등)
HANGUL = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣㅔㅐㅖㅒㅘㅙㅚㅝㅞㅟㅢ]")
# 한자 U+4E00..U+9FFF
HANJA = re.compile(r"[\u4e00-\u9fff]")
# 한글토 전용 구분자 (단독 토)
TO_MARKERS = re.compile(
    r"(이니라|하니라|니라|이로다|로다|이여|이니|이요|이오|이라|ㅣ니라|ㅣ로다|ㅣ니|ㅣ요|ㅣ오|ㅣ라|ㅣ여|ㅣ고|ㅣ며|ㅣ야|ㅣ면|ㅣ|니|요|오|라|야|면|고|며|ㄴ대|ㄴ데|여)"
)

LINE_LABELS = ["初九", "九二", "九三", "九四", "九五", "上九", "用九", "初六", "六二", "六三", "六四", "六五", "上六", "用六"]


def split_hangul_to(text: str) -> tuple[str, str]:
    """Split hanja original from hangul-t'o gloss.

    Returns (hanmun, to_text). Hanmun keeps only hanja + punctuation;
    to_text keeps the hangul gloss words with their hanja anchors removed.
    """
    if not text:
        return "", ""
    hanmun = "".join(HANJA.findall(text))
    # 인라인 마커(彖曰/象曰 등)는 원문이 아니라 구조 표지 — hanmun에서 제거
    hanmun = hanmun.replace("彖曰", "").replace("象曰", "")
    # to_text: 한글 토만 추출해 공백 조인 (조사/어미 연속)
    to_tokens = []
    for seg in TO_MARKERS.findall(text):
        if seg.strip():
            to_tokens.append(seg.strip())
    return hanmun, " ".join(to_tokens)


def section_headings(text: str) -> list[tuple[int, int, str, str]]:
    """Return [(start, end, hexagram_id, heading)] for each ### heading."""
    sections = []
    for m in re.finditer(r"^###\s+(\d+)\.\s*([^\n]*)", text, re.M):
        n = int(m.group(1))
        heading = m.group(2).strip()
        sections.append((m.start(), m.end(), n, heading))
    return sections


def hexagram_id_from_heading(n: int, heading: str, names: dict) -> int | None:
    """Map section heading to canonical hexagram id (1..64)."""
    if 1 <= n <= 64:
        return n
    # heading has name_ko or name_zh
    for hid, (ko, zh) in names.items():
        if ko and ko in heading:
            return hid
        if zh and zh in heading:
            return hid
    return None


def parse_hexagram(section_text: str, names: dict, fallback_id: int) -> dict | None:
    """Parse one hexagram section into structured fields."""
    lines = section_text.splitlines()
    result = {
        "judgment_hanmun": "",
        "judgment_to": "",
        "great_image_hanmun": "",
        "great_image_to": "",
        "line_texts": {},
        "commentary": [],
    }
    current_line = None
    in_commentary = False

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("###"):
            continue
        # commentary marker
        if line == "傳" or line.startswith("[傳]"):
            in_commentary = True
            continue
        # line label start
        label_match = None
        for lbl in LINE_LABELS:
            if line.startswith(lbl):
                label_match = lbl
                break
        if line.startswith("彖曰"):
            current_line = "judgment"
            in_commentary = False
            hanmun, to_text = split_hangul_to(line)
            result["judgment_hanmun"] += hanmun
            result["judgment_to"] += " " + to_text
            continue
        if line.startswith("象曰"):
            current_line = "great_image"
            in_commentary = False
            hanmun, to_text = split_hangul_to(line)
            result["great_image_hanmun"] += hanmun
            result["great_image_to"] += " " + to_text
            continue
        if label_match:
            current_line = label_match
            in_commentary = False
            result["line_texts"].setdefault(label_match, {"hanmun": "", "to": "", "commentary": []})
            hanmun, to_text = split_hangul_to(line)
            result["line_texts"][label_match]["hanmun"] += hanmun
            result["line_texts"][label_match]["to"] += " " + to_text
            continue
        # continuation of current item
        if in_commentary:
            result["commentary"].append(line.strip())
            continue
        if current_line == "judgment":
            hanmun, to_text = split_hangul_to(line)
            result["judgment_hanmun"] += hanmun
            result["judgment_to"] += " " + to_text
        elif current_line == "great_image":
            hanmun, to_text = split_hangul_to(line)
            result["great_image_hanmun"] += hanmun
            result["great_image_to"] += " " + to_text
        elif current_line and current_line in result["line_texts"]:
            hanmun, to_text = split_hangul_to(line)
            result["line_texts"][current_line]["hanmun"] += hanmun
            result["line_texts"][current_line]["to"] += " " + to_text

    return result


def main() -> int:
    vault_dir = Path("/home/declan/Documents/Obsidian Vault/주역/03_한국어_역주")
    out_path = Path(__file__).with_name("data") / "juyeok_jeonui_parsed.json"
    # canonical names
    dataset = json.loads((Path(__file__).with_name("data") / "dataset.json").read_text(encoding="utf-8"))
    names = {h["hexagram_id"]: (h.get("name_ko", ""), h.get("name_zh", "")) for h in dataset["hexagrams"]}

    all_results: dict[str, dict] = {}
    parse_stats = {"sections": 0, "hexagrams": 0, "skipped": []}
    for f in sorted(vault_dir.glob("0*_주역전의*.md")):
        text = f.read_text(encoding="utf-8")
        sections = section_headings(text)
        parse_stats["sections"] += len(sections)
        for i, (start, end, n, heading) in enumerate(sections):
            hid = hexagram_id_from_heading(n, heading, names)
            if hid is None:
                parse_stats["skipped"].append((f.name, n, heading[:30]))
                continue
            end_pos = sections[i + 1][0] if i + 1 < len(sections) else len(text)
            parsed = parse_hexagram(text[start:end_pos], names, hid)
            if parsed is None:
                parse_stats["skipped"].append((f.name, n, "parse failed"))
                continue
            parsed["hexagram_id"] = hid
            parsed["source_file"] = f.name
            parsed["heading"] = heading
            all_results[str(hid)] = parsed
            parse_stats["hexagrams"] += 1

    out = {
        "schema_version": 1,
        "source": "주역/03_한국어_역주 (주역전의 상·하)",
        "quality_policy": "structured_parse_prototype",
        "hexagrams": all_results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"구획 {parse_stats['sections']} / 괘 매핑 {parse_stats['hexagrams']} / 스킵 {len(parse_stats['skipped'])}")
    for s in parse_stats["skipped"][:8]:
        print("  스킵:", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
