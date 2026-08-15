#!/usr/bin/env python3
"""Classical analysis candidates: 조후, 월령/격국, 순잡, 상신, 학파별 용신.

Implements the module contracts from classical-analysis-modules.csv /
modern-analysis-modules.csv as candidate-level computations:
- month_command_extract → 월지 본기 + 계절
- climate_adjustment → 조후 편향 + 조후 용신 후보
- pattern_assessment → 격국 후보 (월지 본기 + 투출)
- pure_mixed_check → 순잡 후보
- xiangshen_helper → 상신 후보 (용신을 생하는 요소)
- useful_god_by_school → 격국/조후/부억 학파별 용신 (합치지 않음)

모든 출력은 후보(candidate)이며 확정 판정이 아니다.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _read(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class ClassicalTables:
    """고전 분석 전용 테이블 (manse tables와 독립)."""

    def __init__(self):
        self.stems = {r["stem_code"]: r for r in _read("heavenly-stems.csv")}
        self.stem_by_hanja = {r["hanja_name"]: r["stem_code"] for r in self.stems.values()}
        self.branches = {r["branch_code"]: r for r in _read("earthly-branches.csv")}
        self.ten_god_map = {(r["day_stem_code"], r["target_stem_code"]): r for r in _read("ten-god-stem-map.csv")}
        self.hidden_stems = {}
        for row in _read("hidden-stems.csv"):
            self.hidden_stems.setdefault(row["branch_code"], []).append(row)
        self.use_god = {}
        for row in _read("classical-seasonal-use-god-rules.csv"):
            self.use_god[(row["day_stem_code"], row["month_branch_code"])] = row

    def __getitem__(self, key):
        return getattr(self, key)


DEFAULT_TABLES = ClassicalTables()

# 월지 → 계절 단계 (classical-seasonal-use-god-rules.csv season_phase와 정합)
SEASON_PHASE = {
    "in": "early_spring", "myo": "mid_spring", "jin": "late_spring",
    "sa": "early_summer", "o": "mid_summer", "mi": "late_summer",
    "sin": "early_autumn", "yu": "mid_autumn", "sul": "late_autumn",
    "hae": "early_winter", "ja": "mid_winter", "chuk": "late_winter",
}

# 조후 편향: 월지 계절 → (temperature, moisture, 조후 용신 후보)
CLIMATE_TABLE = {
    "in": ("cool", "moist", "fire"),    # 초봄 한기 잔존 → 화 보정
    "myo": ("cool", "moist", "fire"),
    "jin": ("mild", "moist", "neutral"),
    "sa": ("hot", "dry", "water"),      # 초여름 열기 → 수 보정
    "o": ("hot", "dry", "water"),
    "mi": ("hot", "humid", "water"),
    "sin": ("cool", "dry", "water"),    # 가을 건조 → 수 보정
    "yu": ("cool", "dry", "water"),
    "sul": ("mild", "dry", "neutral"),
    "hae": ("cold", "moist", "fire"),   # 겨울 한랭 → 화 보정
    "ja": ("cold", "moist", "fire"),
    "chuk": ("cold", "moist", "fire"),
}

ELEMENT_KO = {"wood": "목", "fire": "화", "earth": "토", "metal": "금", "water": "수"}
STEM_KO = {"gap": "갑", "eul": "을", "byeong": "병", "jeong": "정", "mu": "무",
           "gi": "기", "gyeong": "경", "sin": "신", "im": "임", "gye": "계"}
GEN = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
CTL = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}  # key가 value를 극

# 격국 이름: 십성 category + 正/偏 구분
PATTERN_NAME = {
    "jeonggwan": "정관격", "pyeongwan": "편관격", "jeongin": "정인격", "pyeonin": "편인격",
    "jeongjae": "정재격", "pyeonjae": "편재격", "siksin": "식신격", "sanggwan": "상관격",
    "bijeon": "비견격", "geopjae": "겁재격",
}


def _hidden_by_role(tables, branch_code, role):
    for row in tables.hidden_stems.get(branch_code, []):
        if row["hidden_role"] == role:
            return row
    return None


def month_command(chart, tables=None):
    """월지 본기(지장간 본기)와 그 십성 → 월령 중심 추출."""
    tables = tables or DEFAULT_TABLES
    month = chart["four_pillars"]["month"]
    main_row = _hidden_by_role(tables, month["branch_code"], "main")
    if main_row:
        main_hidden = main_row["stem_code"]
        main_hidden_hanja = main_row["stem_hanja"]
    else:
        branch = tables["branches"][month["branch_code"]]
        main_hidden_hanja = branch["hidden_stems"].split(";")[0]
        main_hidden = tables.stem_by_hanja[main_hidden_hanja]
    middle_row = _hidden_by_role(tables, month["branch_code"], "middle")
    day_stem = chart["four_pillars"]["day"]["stem_code"]
    relation = tables["ten_god_map"].get((day_stem, main_hidden))
    return {
        "month_branch": month["branch_code"],
        "month_branch_hanja": month["hanja"][1],
        "main_hidden_stem": main_hidden,
        "main_hidden_hanja": main_hidden_hanja,
        "middle_hidden_stem": middle_row["stem_code"] if middle_row else None,
        "middle_hidden_hanja": middle_row["stem_hanja"] if middle_row else None,
        "season_phase": SEASON_PHASE.get(month["branch_code"]),
        "ten_god": relation["ten_god_ko"] if relation else None,
        "ten_god_code": relation["ten_god_code"] if relation else None,
        "category": relation["category"] if relation else None,
        "status": "candidate",
        "evidence_refs": ["hidden-stems.csv", "earthly-branches.csv", "ten-god-stem-map.csv", "classical-analysis-modules.csv:month_command_extract"],
    }


def _qiaohou_gods(day_stem, month):
    """궁통보감 조후: 월 한열에 일간을 겹친다. 병정 인묘는 임수·경금."""
    temp, moisture, generic = CLIMATE_TABLE[month]
    fire_stems = {"byeong", "jeong"}
    spring = {"in", "myo"}
    summer = {"sa", "o", "mi"}
    if day_stem in fire_stems and month in spring:
        return temp, moisture, "water", "metal"
    if day_stem in fire_stems and month in summer:
        return temp, moisture, "water", "metal"
    return temp, moisture, generic, None


def climate_adjustment(chart, tables=None):
    """조후: 월지 한열습조 + 일간×월지 궁통보감 용신 후보."""
    tables = tables or DEFAULT_TABLES
    month = chart["four_pillars"]["month"]["branch_code"]
    day_stem = chart["four_pillars"]["day"]["stem_code"]
    temp, moisture, climate_god, secondary = _qiaohou_gods(day_stem, month)
    seasonal = tables.use_god.get((day_stem, month))
    return {
        "month_branch": month,
        "day_stem": day_stem,
        "temperature_bias": temp,
        "moisture_bias": moisture,
        "climate_use_god_candidate": climate_god,
        "climate_use_god_secondary": secondary,
        "climate_use_god_ko": ELEMENT_KO[climate_god] if climate_god != "neutral" else "중립",
        "seasonal_rule": seasonal["modern_rule"] if seasonal else None,
        "note": {
            "cold": "한랭한 명식은 화(조후)의 보완을 우선 살핀다",
            "hot": "열기가 강한 명식은 수(서늘)의 보완을 우선 살핀다",
            "cool": "서늘한 명식은 온난 보완을 함께 본다. 병정 인묘는 임수·경금 후보",
        }.get(temp, ""),
        "status": "candidate",
        "evidence_refs": ["classical-seasonal-use-god-rules.csv", "classical-analysis-modules.csv:climate_adjustment"],
    }


def pattern_assessment(chart, tables=None):
    """격국 후보: 월지 본기 투출이면 정격, 없으면 외격 검토. 일간은 투출에서 제외."""
    tables = tables or DEFAULT_TABLES
    mc = month_command(chart, tables)
    main_hidden = mc["main_hidden_stem"]
    middle_hidden = mc["middle_hidden_stem"]
    other_stems = [
        chart["four_pillars"][p]["stem_code"]
        for p in ("year", "month", "hour")
        if chart["four_pillars"][p]
    ]
    투출 = main_hidden in other_stems
    middle_transit = bool(middle_hidden and middle_hidden in other_stems)
    count = other_stems.count(main_hidden)
    if 투출:
        pattern_class = "regular"
        strength = "strong" if count >= 2 else "medium"
    elif middle_transit:
        pattern_class = "regular"
        strength = "weak"
    else:
        pattern_class = "external"
        strength = "weak"
    return {
        "pattern_name": PATTERN_NAME.get(mc["ten_god_code"], f"{mc['ten_god']}격 후보" if mc["ten_god"] else "격국 후보"),
        "pattern_class": pattern_class,
        "pattern_class_ko": "정격" if pattern_class == "regular" else "외격",
        "month_command": mc["main_hidden_hanja"],
        "ten_god": mc["ten_god"],
        "투출": 투출,
        "middle_transit": middle_transit,
        "transparency_count": count,
        "strength": strength,
        "reason": f"월지 본기 {mc['main_hidden_hanja']}이(가) 천간에 {'투출됨' if 투출 else '미투출'}({count}회)",
        "status": "candidate",
        "evidence_refs": ["classical-analysis-modules.csv:pattern_assessment", "classical-pattern-rules.csv", "hidden-stems.csv", "ten-god-stem-map.csv"],
    }


def pattern_success_failure(chart, tables=None):
    """격국 성패 후보: 월지 본기 요소의 생조(보호) vs 극설(손상) 균형.

    성(成): 본기를 생하는 요소가 풍부해 격국을 보호한다.
    패(敗): 본기를 극하는 요소가 강해 격국을 손상한다.
    """
    tables = tables or DEFAULT_TABLES
    mc = month_command(chart, tables)
    main_hidden = mc["main_hidden_stem"]
    el = tables["stems"][main_hidden]["element_code"]
    helper = next((e for e in GEN if GEN[e] == el), None)  # el을 생하는 요소 (생조)
    controller = next((e for e in CTL if CTL[e] == el), None)  # el을 극하는 요소 (극손상)
    ratio = chart.get("_element_ratio") or {}
    helper_r = ratio.get(helper, 0.0) if helper else 0.0
    controller_r = ratio.get(controller, 0.0) if controller else 0.0
    balance = round(helper_r - controller_r, 3)
    if balance >= 0.15:
        verdict, verdict_ko = "favorable", "성립 유리 후보"
    elif balance <= -0.1:
        verdict, verdict_ko = "unfavorable", "성립 불리 후보"
    else:
        verdict, verdict_ko = "neutral", "성립 보통 후보"
    return {
        "pattern_element": el,
        "pattern_element_ko": ELEMENT_KO[el],
        "helper_element": helper,
        "helper_ratio": helper_r,
        "controller_element": controller,
        "controller_ratio": controller_r,
        "balance": balance,
        "verdict": verdict,
        "verdict_ko": verdict_ko,
        "note": "격국 본기를 보호하는 생조와 손상하는 극의 균형을 후보로 본다",
        "status": "candidate",
        "evidence_refs": ["classical-analysis-modules.csv:pattern_assessment", "elements.csv", "heavenly-stems.csv"],
    }


def pure_mixed_check(chart, tables=None):
    """순잡 후보: 격국 관련 오행의 혼잡도."""
    tables = tables or DEFAULT_TABLES
    stems = [chart["four_pillars"][p]["stem_code"] for p in ("year", "month", "day", "hour") if chart["four_pillars"][p]]
    stem_elements = [tables["stems"][s]["element_code"] for s in stems]
    dominant = Counter(stem_elements).most_common(1)[0][0]
    verdict = "pure" if stem_elements.count(dominant) >= 3 else "mixed"
    return {
        "verdict": verdict,
        "verdict_ko": "순(純)" if verdict == "pure" else "잡(雜) 후보",
        "dominant_element": dominant,
        "dominant_element_ko": ELEMENT_KO[dominant],
        "note": "순한 격국은 일관성이, 잡은 조율이 과제",
        "status": "candidate",
        "evidence_refs": ["classical-analysis-modules.csv:pure_mixed_check", "heavenly-stems.csv"],
    }


def xiangshen_helper(chart, tables=None, useful_element=None):
    """상신 후보: 용신(후보)을 생하는 요소가 차트에 있는지."""
    tables = tables or DEFAULT_TABLES
    if not useful_element:
        return {"status": "not_available", "candidates": []}
    helper = next((e for e in GEN if GEN[e] == useful_element), None)
    ratio = chart.get("_element_ratio") or {}
    present = ratio.get(helper, 0.0) if helper else 0.0
    damage = ratio.get(next((e for e in CTL if CTL[e] == helper), None), 0.0) if helper else 0.0  # 상신을 극하는 요소
    if present >= 0.25:
        protection = "보호됨"
    elif present >= 0.15:
        protection = "보통"
    else:
        protection = "취약"
    damage_level = "높음" if damage >= 0.25 else ("보통" if damage >= 0.15 else "낮음")
    return {
        "helper_element": helper,
        "helper_element_ko": ELEMENT_KO[helper] if helper else None,
        "chart_ratio": present,
        "helper_damage_element": next((e for e in CTL if CTL[e] == helper), None),
        "helper_damage_ratio": damage,
        "protection": protection,
        "damage_level": damage_level,
        "note": "상신은 용신을 살리는 보조 요소로, 상신을 극하는 요소가 강하면 보호가 취약해진다",
        "status": "candidate",
        "evidence_refs": ["classical-analysis-modules.csv:xiangshen_helper"],
    }


def useful_god_by_school(chart, tables=None):
    """학파별 용신 후보. 한 값으로 합치지 않는다."""
    tables = tables or DEFAULT_TABLES
    season = _seasonal_use_god(chart, tables)
    climate = climate_adjustment(chart, tables)
    balance = chart.get("_element_ratio") or {}
    strength = chart.get("_day_master_strength") or {}

    ziping = []
    if season:
        primary = season["primary_use_element"]
        ziping.append({"element": primary, "role": "격국/계절", "chart_ratio": balance.get(primary, 0)})
        if season.get("secondary_use_element"):
            ziping.append({
                "element": season["secondary_use_element"],
                "role": "격국 보조",
                "chart_ratio": balance.get(season["secondary_use_element"], 0),
            })

    di_tian_sui = []
    verdict = strength.get("verdict")
    day_el = (strength.get("day_master") or {}).get("element")
    if verdict == "shinyak" and day_el:
        helper = next((src for src, dst in GEN.items() if dst == day_el), None)
        if helper:
            di_tian_sui.append({"element": helper, "role": "부억 신약 생조", "chart_ratio": balance.get(helper, 0)})
        di_tian_sui.append({"element": day_el, "role": "부억 신약 비겁", "chart_ratio": balance.get(day_el, 0)})
    elif verdict == "shingang" and day_el:
        drain = GEN.get(day_el)
        if drain:
            di_tian_sui.append({"element": drain, "role": "부억 신강 설기", "chart_ratio": balance.get(drain, 0)})
        control = CTL.get(day_el)
        if control:
            di_tian_sui.append({"element": control, "role": "부억 신강 억제", "chart_ratio": balance.get(control, 0)})

    qiaohou = []
    if climate["climate_use_god_candidate"] != "neutral":
        cg = climate["climate_use_god_candidate"]
        qiaohou.append({"element": cg, "role": "조후", "chart_ratio": balance.get(cg, 0)})
        secondary = climate.get("climate_use_god_secondary")
        if secondary:
            qiaohou.append({"element": secondary, "role": "조후 보조", "chart_ratio": balance.get(secondary, 0)})

    schools = {
        "ziping_pattern": {
            "school": "ziping_pattern",
            "school_ko": "격국",
            "source": "자평진전",
            "candidates": ziping,
            "status": "candidate",
        },
        "di_tian_sui": {
            "school": "di_tian_sui",
            "school_ko": "부억",
            "source": "적천수",
            "candidates": di_tian_sui,
            "status": "candidate",
        },
        "qiaohou": {
            "school": "qiaohou",
            "school_ko": "조후",
            "source": "궁통보감",
            "candidates": qiaohou,
            "status": "candidate",
        },
    }
    heads = []
    for school in schools.values():
        if school["candidates"]:
            heads.append(school["candidates"][0]["element"])
    agreement = len(set(heads)) == 1 and len(heads) >= 2
    return {
        "schools": schools,
        "agreement": agreement,
        "agreement_element": heads[0] if agreement else None,
        "status": "candidate",
        "evidence_refs": [
            "classical-seasonal-use-god-rules.csv",
            "classical-analysis-modules.csv:useful_god_candidates",
        ],
    }


def useful_god_combined(chart, tables=None):
    """학파 후보를 나란히 나열한다. 한 값으로 합치지 않는다."""
    tables = tables or DEFAULT_TABLES
    by_school = useful_god_by_school(chart, tables)
    candidates = []
    for school in by_school["schools"].values():
        for item in school["candidates"]:
            tagged = dict(item)
            tagged["school"] = school["school"]
            tagged["school_ko"] = school["school_ko"]
            tagged["priority"] = "high" if tagged["chart_ratio"] < 0.15 else ("medium" if tagged["chart_ratio"] < 0.25 else "low")
            candidates.append(tagged)
    return {
        "candidates": candidates,
        "schools": by_school["schools"],
        "agreement": by_school["agreement"],
        "agreement_element": by_school["agreement_element"],
        "climate": climate_adjustment(chart, tables)["climate_use_god_candidate"],
        "status": "candidate",
        "evidence_refs": by_school["evidence_refs"],
    }


def _seasonal_use_god(chart, tables):
    day = chart["four_pillars"]["day"]
    month = chart["four_pillars"]["month"]
    return tables.use_god.get((day["stem_code"], month["branch_code"]))


def analyze_classical(chart, tables=None):
    """고전 분석 종합: 조후/월령/격국/순잡/상신/학파별 용신."""
    tables = tables or DEFAULT_TABLES
    balance = _ratio(chart, tables)
    chart["_element_ratio"] = balance
    try:
        from element_analysis import day_master_strength, ElementTables
        chart["_day_master_strength"] = day_master_strength(chart, ElementTables())
    except Exception:  # noqa: BLE001
        chart["_day_master_strength"] = {}
    combined = useful_god_combined(chart, tables)
    primary = combined["candidates"][0]["element"] if combined["candidates"] else None
    return {
        "month_command": month_command(chart, tables),
        "climate_adjustment": climate_adjustment(chart, tables),
        "pattern_assessment": pattern_assessment(chart, tables),
        "pattern_success_failure": pattern_success_failure(chart, tables),
        "pure_mixed_check": pure_mixed_check(chart, tables),
        "xiangshen_helper": xiangshen_helper(chart, tables, useful_element=primary),
        "useful_god_combined": combined,
        "useful_god_by_school": useful_god_by_school(chart, tables),
        "status": "candidate",
        "evidence_refs": ["classical-analysis-modules.csv", "classical-seasonal-use-god-rules.csv"],
    }


def _ratio(chart, tables):
    from element_analysis import element_balance, ElementTables
    return element_balance(chart, ElementTables(), convention="hidden")["ratio"]


def main():
    import argparse
    import json
    from manse_engine import calculate_chart

    parser = argparse.ArgumentParser()
    parser.add_argument("--birth-date", required=True)
    parser.add_argument("--birth-time", default="")
    parser.add_argument("--gender", default="unknown")
    args = parser.parse_args()
    from manse_engine import load_tables
    chart = calculate_chart(birth_date=args.birth_date, birth_time=args.birth_time, gender=args.gender, tables=load_tables())
    print(json.dumps(analyze_classical(chart), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
