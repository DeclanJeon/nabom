#!/usr/bin/env python3
"""12운성 외부 대조: 위키피디아(ko) 기준 vs 엔진 twelve-life-stage-map/stages.

외부 기준 (https://ko.wikipedia.org/wiki/십이운성, 2026-08-12):
1. 12운성 명칭: 장생·목욕·관대·건록·제왕·쇠·병·사·묘·절·태·양
2. 화토동법: 병화와 무토, 정화와 기토의 십이운성 일치
3. 양간은 순행, 음간은 역행
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "docs" / "saju-life-guide" / "saju-document"
sys.path.insert(0, str(ROOT))

from manse_engine import calculate_chart, load_tables  # noqa: E402

WIKI_STAGES = {"장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"}
YANG_STEMS = {"gap", "byeong", "mu", "gyeong", "im"}


def require(cond, msg):
    if not cond:
        raise SystemExit(msg)


def main():
    map_rows = list(csv.DictReader(open(ROOT / "twelve-life-stage-map.csv", encoding="utf-8")))
    stage_rows = list(csv.DictReader(open(ROOT / "twelve-life-stages.csv", encoding="utf-8")))

    # 1) 명칭
    names = {r["ko_name"] for r in stage_rows}
    require(names == WIKI_STAGES, f"12운성 명칭 불일치: {names ^ WIKI_STAGES}")

    # 2) 화토동법
    by_stem = {}
    for r in map_rows:
        by_stem.setdefault(r["day_stem_code"], {})[r["branch_code"]] = r["stage_code"]

    def same(a, b):
        return all(by_stem[a][br] == by_stem[b][br] for br in by_stem[a])

    require(same("byeong", "mu"), "화토동법(병=무) 불일치")
    require(same("jeong", "gi"), "화토동법(정=기) 불일치")

    # 3) 양순음역
    require(all(r["direction"] == "forward" for r in map_rows if r["day_stem_code"] in YANG_STEMS), "양간 순행 불일치")
    require(all(r["direction"] == "reverse" for r in map_rows if r["day_stem_code"] not in YANG_STEMS), "음간 역행 불일치")

    # 4) 사용자 차트 일지 12운성 (丙/子 → 태)
    chart = calculate_chart(birth_date="1992-03-01", birth_time="07:20", gender="남성", tables=load_tables())
    day_stage = next(s for s in chart["auxiliary_signals"]["twelve_life_stages"] if s["position"] == "day")
    require(day_stage["stage_ko"] == "태", f"丙/子 12운성: {day_stage['stage_ko']}")

    print("12운성 외부 대조: 명칭·화토동법·양순음역·차트 적용 4/4 일치 ✓")


if __name__ == "__main__":
    main()
