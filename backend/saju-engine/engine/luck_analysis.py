#!/usr/bin/env python3
"""Annual (세운) and monthly (월운) luck outlook.

Contract follows NABOM API-SPEC `luckOutlook`:
- annual: 입춘 경계 기반 세운 간지, annual_luck_uses_verified_ipchun_boundary
- monthly: 절기 window 기반 월운 간지, monthly_luck_uses_verified_solar_term_window
- decade: chart.luck_cycles 재사용 (대운)
All outputs are reference signals, not weather/fate prediction.
"""

from __future__ import annotations

import csv
from pathlib import Path

from manse_engine import (
    DEFAULT_TIMEZONE,
    MONTH_BRANCH_ORDER,
    MONTH_START_TERM_BRANCH,
    gapja_by_index,
    gapja_by_stem_branch,
    load_tables,
    solar_term_boundaries,
    stem_index,
)

ROOT = Path(__file__).resolve().parent

# 양력 월 → 월 시작 절기 (근사 매핑, 정밀 boundary는 provider에서 덮어씀)
MONTH_TERM = {
    1: "소한", 2: "입춘", 3: "경칩", 4: "청명", 5: "입하", 6: "망종",
    7: "소서", 8: "입추", 9: "백로", 10: "한로", 11: "입동", 12: "대설",
}

SEASON_NOTES = {
    "입춘": "봄의 시작, 생장 기운 상승",
    "경칩": "초봄, 만물이 깨어나는 시기",
    "청명": "봄의 중반, 맑은 기운",
    "입하": "여름의 시작, 화기 상승",
    "망종": "초여름, 활동 에너지 확장",
    "소서": "한여름, 열기와 성장",
    "입추": "가을의 시작, 수렴 기운",
    "백로": "초가을, 결실의 기운",
    "한로": "가을의 중반, 정리와 수확",
    "입동": "겨울의 시작, 저장과 내면",
    "대설": "초겨울, 깊은 안정",
    "소한": "한겨울, 회복과 준비",
}


def _boundaries(tables, year, tzinfo, quality_flags):
    terms = solar_term_boundaries(tables, year, tzinfo)
    verified = all(t["source"] != "approximate_static_boundary" for t in terms)
    if verified:
        quality_flags.append("verified_solar_term_time_{year}".format(year=year))
    return terms, verified


def annual_luck(tables, year, tzinfo, quality_flags):
    """세운: 기준 연도의 연주 (입춘 경계 기준)."""
    terms, verified = _boundaries(tables, year, tzinfo, quality_flags)
    ipchun = next((t for t in terms if t["term_ko"] == "입춘"), None)
    pillar = gapja_by_index(tables, year - 1984)
    flags = list(quality_flags) + ["luck_weather_not_prediction"]
    if ipchun is not None and verified:
        flags.append("annual_luck_uses_verified_ipchun_boundary")
    return {
        "year": year,
        "pillar": {"ko": pillar.ko, "hanja": pillar.hanja, "stem_code": pillar.stem_code, "branch_code": pillar.branch_code},
        "boundary_term": ipchun["term_ko"] if ipchun else "입춘",
        "boundary_datetime": ipchun["datetime"].isoformat() if ipchun else None,
        "boundary_source": ipchun["source"] if ipchun else "approximate_static_boundary",
        "quality_flags": sorted(set(flags)),
        "evidence_refs": ["luck-cycle-rules.csv:annual_luck_pillar", "gapja-combinations.csv", "solar-term-month-boundaries.csv"],
    }


def monthly_luck(tables, year, month, year_stem_code, tzinfo, quality_flags):
    """월운: 해당 월의 시작 절기 window 기준 월주. year_stem_code는 운세 대상 연도의 연간."""
    terms, verified = _boundaries(tables, year, tzinfo, quality_flags)
    term_name = MONTH_TERM.get(month, "입춘")
    start = next((t for t in terms if t["term_ko"] == term_name), None)
    if start is None:
        return {"month": month, "status": "unavailable", "reason": "solar_term_not_found"}
    ordered = sorted(terms, key=lambda t: t["datetime"])
    idx = ordered.index(start)
    end = ordered[idx + 1] if idx + 1 < len(ordered) else None

    month_branch_code = MONTH_START_TERM_BRANCH[term_name]
    start_stem_code = tables["month_start"][year_stem_code]
    month_offset = MONTH_BRANCH_ORDER.index(month_branch_code)
    month_stem_code = tables["stem_order"][(stem_index(tables, start_stem_code) + month_offset) % 10]
    pillar = gapja_by_stem_branch(tables, month_stem_code, month_branch_code)

    flags = list(quality_flags) + ["luck_weather_not_prediction"]
    if verified and start["source"] != "approximate_static_boundary":
        flags.append("monthly_luck_uses_verified_solar_term_window")
    return {
        "month": month,
        "pillar": {"ko": pillar.ko, "hanja": pillar.hanja, "stem_code": pillar.stem_code, "branch_code": pillar.branch_code},
        "solar_term": term_name,
        "season_note": SEASON_NOTES.get(term_name, ""),
        "period_start_datetime": start["datetime"].isoformat(),
        "period_end_datetime": end["datetime"].isoformat() if end else None,
        "boundary_source": start["source"],
        "quality_flags": sorted(set(flags)),
        "evidence_refs": ["luck-cycle-rules.csv:monthly_luck_pillar", "month-stem-start-rules.csv", "solar-term-month-boundaries.csv"],
    }


def luck_interaction(chart, tables=None, reference_year=None):
    """대운-세운 상호작용: 현재 대운과 해당 연도 세운의 천간·지지 관계 평가.

    - 천간: 오행 상생/상극/합/충
    - 지지: 육합/충/삼합/방합/형 (earthly-branch-relationships.csv)
    모든 출력은 후보이며 운세 예측이 아니다.
    """

    tables = tables or load_tables()
    year = reference_year or int(chart["input"]["birth_date"][:4])
    from zoneinfo import ZoneInfo
    tzinfo = chart.get("_tzinfo") or ZoneInfo(DEFAULT_TIMEZONE)
    annual = annual_luck(tables, year, tzinfo, list(chart.get("quality_flags", [])))
    annual_stem = annual["pillar"]["stem_code"]
    annual_branch = annual["pillar"]["branch_code"]

    # 현재 대운 탐색: 나이 = year - 출생연도
    age = year - int(chart["input"]["birth_date"][:4])
    cycles = chart.get("luck_cycles", {}).get("decade_cycles", [])
    current = None
    for i, cyc in enumerate(cycles):
        start = cyc["start_age_years"]
        end = cycles[i + 1]["start_age_years"] if i + 1 < len(cycles) else 200
        if start <= age < end:
            current = cyc
            break
    if current is None and cycles:
        current = cycles[-1]
    if current is None:
        return {"status": "not_available", "reason": "대운 없음"}

    decade_stem = current["pillar"]["stem_code"]
    decade_branch = current["pillar"]["branch_code"]

    # 천간 관계
    stem_rel = _stem_relationship(decade_stem, annual_stem)
    # 지지 관계
    branch_rel = _branch_relationship(decade_branch, annual_branch)

    signals = []
    if stem_rel:
        signals.append({"layer": "천간", "type": stem_rel["type"], "ko": stem_rel["ko_name"], "interpretation": stem_rel["interpretation"]})
    if branch_rel:
        signals.append({"layer": "지지", "type": branch_rel["type"], "ko": branch_rel["ko_name"], "interpretation": branch_rel["interpretation"]})

    # 종합 후보
    if any(s["type"] in {"combine", "six_harmony", "triad", "seasonal"} for s in signals):
        verdict, verdict_ko = "harmonious", "합화 흐름 후보"
    elif any(s["type"] in {"clash", "punishment"} for s in signals):
        verdict, verdict_ko = "tense", "긴장 흐름 후보"
    else:
        verdict, verdict_ko = "neutral", "중립 흐름 후보"

    return {
        "year": year,
        "age": age,
        "current_decade": {"start_age_years": current["start_age_years"], "pillar_ko": current["pillar"]["ko"], "pillar_hanja": current["pillar"]["hanja"]},
        "annual_pillar_ko": annual["pillar"]["ko"],
        "signals": signals,
        "verdict": verdict,
        "verdict_ko": verdict_ko,
        "note": "대운과 세운의 합충 관계를 흐름 참고용으로만 본다",
        "status": "candidate",
        "evidence_refs": ["heavenly-stem-relationships.csv", "earthly-branch-relationships.csv", "luck-cycle-rules.csv"],
    }


def _stem_relationship(a, b):
    if a == b:
        return {"type": "same", "ko_name": "동일 천간", "interpretation": "같은 천간이 반복되어 흐름이 강조된다"}
    rows = list(csv.DictReader(open(Path(__file__).resolve().parent / "heavenly-stem-relationships.csv", encoding="utf-8")))
    pair = {a, b}
    for row in rows:
        if {row["left_stem"], row["right_stem"]} == pair:
            return {"type": row["relationship_type"], "ko_name": row["ko_name"], "interpretation": row["interpretation"]}
    return None


def _branch_relationship(a, b):
    if a == b:
        return None
    rows = list(csv.DictReader(open(Path(__file__).resolve().parent / "earthly-branch-relationships.csv", encoding="utf-8")))
    pair = {a, b}
    for row in rows:
        branches = set(row["branches"].split(";"))
        if row["relationship_type"] in {"six_harmony", "clash"} and branches == pair:
            return {"type": row["relationship_type"], "ko_name": row["ko_name"], "interpretation": row["interpretation"]}
        if row["relationship_type"] in {"triad", "seasonal", "punishment"} and pair.issubset(branches):
            return {"type": row["relationship_type"], "ko_name": row["ko_name"], "interpretation": row["interpretation"]}
    return None


def luck_outlook(chart, tables, reference_year=None, month=None):
    """연운 + 월운 + 대운 종합. reference_year 기본값: 차트 출생연도."""
    from manse_engine import DEFAULT_TIMEZONE

    from zoneinfo import ZoneInfo
    tzinfo = chart.get("_tzinfo")
    if tzinfo is None:
        tzinfo = ZoneInfo(DEFAULT_TIMEZONE)
    quality_flags = list(chart.get("quality_flags", []))
    year = reference_year or chart["input"]["birth_date"][:4]

    annual = annual_luck(tables, int(year), tzinfo, quality_flags)
    monthly = None
    if month is not None:
        # 월운은 운세 대상 연도의 연간 기준 (오호둔). 세운 연주에서 도출한다.
        year_stem = annual["pillar"]["stem_code"]
        monthly = monthly_luck(tables, int(year), month, year_stem, tzinfo, quality_flags)

    return {
        "annual": annual,
        "monthly": monthly,
        "decade": chart.get("luck_cycles", {}),
        "status": "candidate",
        "policy": "luck_weather_not_prediction",
    }
