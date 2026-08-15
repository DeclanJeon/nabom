#!/usr/bin/env python3
"""12신살 외부 대조: 위키피디아(ko) 신살 문서 기준 vs 엔진 CSV + 사용자 차트.

외부 기준 출처:
- https://ko.wikipedia.org/wiki/신살 (역마/도화/화개 삼합 매핑, 12신살 구성)
- https://ko.wikipedia.org/wiki/사주팔자 (십이신살 구성, 지장간, 십이운성)
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "saju-engine" / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from manse_engine import calculate_chart, load_tables  # noqa: E402

BRANCH_KO = {"hae": "해", "ja": "자", "chuk": "축", "in": "인", "myo": "묘", "jin": "진",
             "sa": "사", "o": "오", "mi": "미", "sin": "신", "yu": "유", "sul": "술"}

# 외부 기준(위키피디아)에서 도출한 삼합 → 신살 매핑 (코드 기준)
# 겁,재,천,지,년,월,망,장,반,역,육,화 순서
WIKI_12SHINSAL = {
    "fire":  {"geopsal": "hae", "jaesal": "ja", "cheonsal": "chuk", "jisal": "in", "nyeonsal": "myo", "wolsal": "jin", "mangsin": "sa", "jangseong": "o", "banan": "mi", "yeokma": "sin", "yukhae": "yu", "hwagae": "sul"},  # 寅午戌
    "metal": {"geopsal": "in", "jaesal": "myo", "cheonsal": "jin", "jisal": "sa", "nyeonsal": "o", "wolsal": "mi", "mangsin": "sin", "jangseong": "yu", "banan": "sul", "yeokma": "hae", "yukhae": "ja", "hwagae": "chuk"},  # 巳酉丑
    "water": {"geopsal": "sa", "jaesal": "o", "cheonsal": "mi", "jisal": "sin", "nyeonsal": "yu", "wolsal": "sul", "mangsin": "hae", "jangseong": "ja", "banan": "chuk", "yeokma": "in", "yukhae": "myo", "hwagae": "jin"},  # 申子辰
    "wood":  {"geopsal": "sin", "jaesal": "yu", "cheonsal": "sul", "jisal": "hae", "nyeonsal": "ja", "wolsal": "chuk", "mangsin": "in", "jangseong": "myo", "banan": "jin", "yeokma": "sa", "yukhae": "o", "hwagae": "mi"},  # 亥卯未
}

# 위키피디아가 명시적으로 정의한 항목 (역마/도화/화개)
WIKI_EXPLICIT = {
    "yeokma": {"wood": "sa", "fire": "sin", "metal": "hae", "water": "in"},
    "hwagae": {"wood": "mi", "fire": "sul", "metal": "chuk", "water": "jin"},
    "nyeonsal": {"wood": "ja", "fire": "myo", "metal": "o", "water": "yu"},  # 도화살 위치와 일치
}

SHINSAL_COLS = ["geopsal", "jaesal", "cheonsal", "jisal", "nyeonsal", "wolsal", "mangsin", "jangseong", "banan", "yeokma", "yukhae", "hwagae"]


def load_engine_table():
    rows = list(csv.DictReader(open(ENGINE_DIR / "twelve-shinsal-rules.csv", encoding="utf-8")))
    return {row["triad_group"]: {code: row[code] for code in SHINSAL_COLS} for row in rows}


def main():
    engine = load_engine_table()
    failures = []
    checked = 0

    # 1) 전체 12신살 표 대조
    for group, wiki_row in WIKI_12SHINSAL.items():
        for code in SHINSAL_COLS:
            checked += 1
            if engine[group][code] != wiki_row[code]:
                failures.append(f"{group}/{code}: engine={engine[group][code]} wiki={wiki_row[code]}")

    # 2) 위키피디아 명시 항목(역마/화개/년살=도화) 교차 확인
    for code, mapping in WIKI_EXPLICIT.items():
        for group, branch in mapping.items():
            checked += 1
            if engine[group][code] != branch:
                failures.append(f"explicit {code}/{group}: engine={engine[group][code]} wiki={branch}")

    # 3) 사용자 차트(1992-03-01 07:20) 일지 기준 삼합 적용 검증
    chart = calculate_chart(birth_date="1992-03-01", birth_time="07:20", gender="남성",
                            birth_place="대한민국 부산광역시", timezone="Asia/Seoul", tables=load_tables())
    day_branch = chart["four_pillars"]["day"]["branch_code"]  # ja
    group = "water"  # 자 → 신자진 수국
    positions = {"year": chart["four_pillars"]["year"]["branch_code"],
                 "month": chart["four_pillars"]["month"]["branch_code"],
                 "day": chart["four_pillars"]["day"]["branch_code"],
                 "hour": chart["four_pillars"]["hour"]["branch_code"]}
    expected = {}
    for pos, branch in positions.items():
        for code, mapped in WIKI_12SHINSAL[group].items():
            if mapped == branch:
                expected[pos] = code
    engine_signals = chart["auxiliary_signals"]["twelve_shinsal"]["day_base"]
    engine_map = {s["target_position"]: s["shinsal_code"] for s in engine_signals}
    for pos in ("year", "month", "day", "hour"):
        checked += 1
        if engine_map.get(pos) != expected.get(pos):
            failures.append(f"chart {pos}: engine={engine_map.get(pos)} wiki-expected={expected.get(pos)}")

    print("=== 12신살 외부 대조 결과 ===")
    print(f"검증 항목: {checked}건, 불일치: {len(failures)}건")
    for f in failures:
        print("  ✗", f)
    if not failures:
        print("결론: 엔진 CSV 및 사용자 차트 신살 배정이 외부 기준(위키피디아)과 완전 일치")
    else:
        print("결론: 불일치 존재")
        sys.exit(1)


if __name__ == "__main__":
    main()
