#!/usr/bin/env python3
"""Element balance, day-master strength, and useful-god candidate analysis.

Additive module on top of manse_engine. All outputs are candidates/hypotheses,
never deterministic verdicts. Evidence refs point to the knowledge CSVs.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from manse_engine import load_tables as load_manse_tables
from classical_analysis import analyze_classical  # noqa: E402

ROOT = Path(__file__).resolve().parent

ELEMENTS = ("wood", "fire", "earth", "metal", "water")
ELEMENT_KO = {"wood": "목", "fire": "화", "earth": "토", "metal": "금", "water": "수"}

# 상생: key가 value를 생한다. 목생화, 화생토, 토생금, 금생수, 수생목
GENERATES = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
# 상극: key가 value를 극한다. 목극토, 토극수, 수극화, 화극금, 금극목
CONTROLS = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}

# 월지 계절 오행 (인묘진=목, 사오미=화, 신유술=금, 해자축=수, 진술축미=토)
MONTH_BRANCH_ELEMENT = {
    "in": "wood", "myo": "wood", "jin": "earth",
    "sa": "fire", "o": "fire", "mi": "earth",
    "sin": "metal", "yu": "metal", "sul": "earth",
    "hae": "water", "ja": "water", "chuk": "earth",
}

# 12운성 강약 가중치: 장생~제왕(1~5) = 뿌리 강, 쇠/병/사(6~8) = 약간 약, 묘/절/태/양(9~12) = 약
LIFE_STAGE_WEIGHT = {
    "jangsaeng": 1.0, "mogyok": 0.9, "gwandae": 1.0, "geonrok": 1.0, "jewang": 1.0,
    "soe": 0.55, "byeong": 0.5, "sa": 0.45,
    "myo": 0.35, "jeol": 0.3, "tae": 0.3, "yang": 0.25,
}

# 지장간 일수(연해자평/위키 30일): 생지 16·7·7, 왕지 본기 중심, 고지 18·9·3.
# 역할 키는 hidden-stems.csv (본기/중기/여기). 세미콜론 순서로 zip하지 않는다.
SAENGJI_BRANCHES = {"in", "sa", "sin", "hae"}
WANGJI_BRANCHES = {"ja", "myo", "o", "yu"}
GOJI_BRANCHES = {"jin", "sul", "chuk", "mi"}
HIDDEN_ROLE_DAYS = {
    "saengji": {"main": 16, "middle": 7, "residual": 7},
    "wangji": {"main": 21, "middle": 9, "residual": 0},
    "goji": {"main": 18, "middle": 9, "residual": 3},
}
TRIAD_BONUS = {2: 0.5, 3: 0.8}
SEASONAL_BONUS = {2: 0.35, 3: 0.6}
STRONG_LIFE_STAGES = {"jangsaeng", "gwandae", "geonrok", "jewang"}


def read_csv(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class ElementTables:
    def __init__(self):
        self.stems = {r["stem_code"]: r for r in read_csv("heavenly-stems.csv")}
        self.stem_by_hanja = {r["hanja_name"]: r["stem_code"] for r in self.stems.values()}
        self.branches = {r["branch_code"]: r for r in read_csv("earthly-branches.csv")}
        self.elements = {r["element_code"]: r for r in read_csv("elements.csv")}
        self.use_god = {
            (r["day_stem_code"], r["month_branch_code"]): r
            for r in read_csv("classical-seasonal-use-god-rules.csv")
        }
        self.life_stages = {
            (r["day_stem_code"], r["branch_code"]): r
            for r in read_csv("twelve-life-stage-map.csv")
        }
        self.growth_quests = {r["element_code"]: r for r in read_csv("character-growth-quests.csv")}
        self.ten_god_map = {
            (r["day_stem_code"], r["target_stem_code"]): r
            for r in read_csv("ten-god-stem-map.csv")
        }
        self.ten_god_meta = {r["ten_god_code"]: r for r in read_csv("ten-god-rules.csv")}
        self.special_stars = {r["special_star_code"]: r for r in read_csv("special-stars.csv")}
        self.hidden_stems = {}
        for row in read_csv("hidden-stems.csv"):
            self.hidden_stems.setdefault(row["branch_code"], []).append(row)
        self.branch_relations = [
            r for r in read_csv("earthly-branch-relationships.csv")
            if r["relationship_type"] in {"triad", "seasonal"}
        ]


def _pillars(chart):
    return [p for p in chart["four_pillars"].values() if p]


def _branch_kind(branch_code):
    if branch_code in SAENGJI_BRANCHES:
        return "saengji"
    if branch_code in WANGJI_BRANCHES:
        return "wangji"
    return "goji"


def hidden_stem_weights(branch_code, tables: ElementTables):
    """역할 키 기준 30일 비중. 세미콜론 순서 zip을 쓰지 않는다."""
    rows = list(tables.hidden_stems.get(branch_code, []))
    kind = _branch_kind(branch_code)
    role_days = HIDDEN_ROLE_DAYS[kind]
    weighted = []
    for row in rows:
        days = role_days.get(row["hidden_role"], 0)
        if days <= 0:
            continue
        weighted.append((row, days))
    total_days = sum(days for _, days in weighted) or 1
    return [(row, days / total_days) for row, days in weighted]


def _source_of(mapping, target):
    return next(src for src, dst in mapping.items() if dst == target)


def _combination_boosts(chart, tables: ElementTables):
    present = {p["branch_code"] for p in _pillars(chart)}
    boosts = Counter()
    notes = []
    for row in tables.branch_relations:
        members = [b.strip() for b in row["branches"].split(";") if b.strip()]
        hit = len(present.intersection(members))
        table = TRIAD_BONUS if row["relationship_type"] == "triad" else SEASONAL_BONUS
        bonus = table.get(hit)
        result = row.get("result_element")
        if not bonus or not result:
            continue
        boosts[result] += bonus
        notes.append(
            {
                "type": row["relationship_type"],
                "group": row["group_key"],
                "hit": hit,
                "needed": len(members),
                "result_element": result,
                "bonus": bonus,
            }
        )
    return boosts, notes


def element_balance(chart, tables: ElementTables, convention="hidden"):
    """오행 분포. convention: '8_char' | 'hidden'"""
    counts = Counter()
    notes = []
    combination_notes = []
    for pillar in _pillars(chart):
        stem_el = tables.stems[pillar["stem_code"]]["element_code"]
        branch = tables.branches[pillar["branch_code"]]
        branch_el = branch["element_code"]
        if convention == "8_char":
            counts[stem_el] += 1
            counts[branch_el] += 1
        else:
            counts[stem_el] += 1.0
            weighted = hidden_stem_weights(pillar["branch_code"], tables)
            for row, weight in weighted:
                counts[tables.stems[row["stem_code"]]["element_code"]] += weight
            notes.append(
                {
                    "branch_code": pillar["branch_code"],
                    "branch_hanja": branch["ko_name"],
                    "branch_kind": _branch_kind(pillar["branch_code"]),
                    "hidden_stems": [row["stem_hanja"] for row, _ in weighted],
                    "hidden_roles": [row["hidden_role"] for row, _ in weighted],
                    "weights": [round(weight, 4) for _, weight in weighted],
                    "weight_basis": "yeonhae_ziping_30day",
                }
            )
    if convention == "hidden":
        boosts, combination_notes = _combination_boosts(chart, tables)
        for el, bonus in boosts.items():
            counts[el] += bonus
    total = sum(counts.values()) or 1
    normalized = {el: round(counts[el] / total, 4) for el in ELEMENTS}
    return {
        "convention": convention,
        "counts": {el: round(counts[el], 2) for el in ELEMENTS},
        "ratio": normalized,
        "dominant": max(ELEMENTS, key=lambda el: normalized[el]),
        "deficient": min(ELEMENTS, key=lambda el: normalized[el]),
        "notes": notes,
        "combination_notes": combination_notes,
        "evidence_refs": ["heavenly-stems.csv", "earthly-branches.csv", "hidden-stems.csv", "earthly-branch-relationships.csv", "elements.csv"],
    }


def _season_support(day_stem_element, month_branch_code, tables: ElementTables):
    month_el = MONTH_BRANCH_ELEMENT[month_branch_code]
    if month_el == day_stem_element:
        return "strong", "월지가 일간과 같은 오행이라 득령한다", True
    if GENERATES[month_el] == day_stem_element:
        return "strong", f"월지({ELEMENT_KO[month_el]})가 일간({ELEMENT_KO[day_stem_element]})을 생한다", True
    if CONTROLS[month_el] == day_stem_element:
        return "weak", f"월지({ELEMENT_KO[month_el]})가 일간을 극한다", False
    if CONTROLS[day_stem_element] == month_el:
        return "moderate", f"일간이 월지({ELEMENT_KO[month_el]})를 극해 힘을 쓴다", False
    return "moderate", "월지와 일간이 상생·상극의 직접 관계가 아니다", False


def _root_support(day_stem_code, day_branch_code, tables: ElementTables):
    stage = tables.life_stages.get((day_stem_code, day_branch_code))
    if not stage:
        return 0.5, None
    weight = LIFE_STAGE_WEIGHT.get(stage["stage_code"], 0.5)
    return weight, stage


def _day_branch_hides_day_stem(day_stem_code, day_branch_code, tables: ElementTables):
    return any(row["stem_code"] == day_stem_code for row in tables.hidden_stems.get(day_branch_code, []))


def day_master_strength(chart, tables: ElementTables):
    day = chart["four_pillars"]["day"]
    month = chart["four_pillars"]["month"]
    day_stem_code = day["stem_code"]
    day_el = tables.stems[day_stem_code]["element_code"]
    month_branch_code = month["branch_code"]

    season_level, season_reason, deungnyeong = _season_support(day_el, month_branch_code, tables)
    root_weight, root_stage = _root_support(day_stem_code, day["branch_code"], tables)
    hidden_root = _day_branch_hides_day_stem(day_stem_code, day["branch_code"], tables)
    stage_code = root_stage["stage_code"] if root_stage else None
    deungji = hidden_root or stage_code in STRONG_LIFE_STAGES

    # 생부/극설: 십성 오행은 표준 순환이다.
    #  - 비겁: 같은 오행
    #  - 인성: 일간을 생하는 오행
    #  - 식상: 일간이 생하는 오행
    #  - 재성: 일간이 극하는 오행
    #  - 관살: 일간을 극하는 오행
    balance = element_balance(chart, tables, convention="hidden")
    ratio = balance["ratio"]
    peer = ratio[day_el]
    resource = ratio[_source_of(GENERATES, day_el)]
    drain = ratio[GENERATES[day_el]]
    wealth = ratio[CONTROLS[day_el]]
    officer = ratio[_source_of(CONTROLS, day_el)]
    support = peer + resource
    pressure = drain + wealth + officer
    raw_ratio = support / max(pressure, 1e-6)
    deungse = support > pressure

    season_mult = {"strong": 1.3, "moderate": 1.0, "weak": 0.85}[season_level]
    root_mult = 0.85 + 0.25 * root_weight
    adjusted = raw_ratio * season_mult * root_mult

    if adjusted >= 1.15:
        verdict, verdict_ko = "shingang", "신강 후보"
    elif adjusted >= 0.9:
        verdict, verdict_ko = "neutral", "중화 후보"
    else:
        verdict, verdict_ko = "shinyak", "신약 후보"

    flags = list(chart.get("quality_flags", []))
    confidence = 0.72 if "approximate_solar_terms" not in flags else 0.6

    return {
        "day_master": {"code": day_stem_code, "hanja": day["hanja"][0], "element": day_el, "element_ko": ELEMENT_KO[day_el]},
        "season_support": {
            "level": season_level,
            "reason": season_reason,
            "month_branch": month["hanja"][1],
            "deungnyeong": deungnyeong,
        },
        "root_support": {
            "weight": root_weight,
            "stage": root_stage["stage_ko"] if root_stage else None,
            "day_branch": day["hanja"][1],
            "hidden_root": hidden_root,
            "deungji": deungji,
        },
        "peer_support": {"same_element_ratio": round(peer, 4), "resource_ratio": round(resource, 4)},
        "pressure_breakdown": {
            "drain": round(drain, 4),
            "wealth": round(wealth, 4),
            "officer": round(officer, 4),
        },
        "strength_flags": {
            "deungnyeong": deungnyeong,
            "deungji": deungji,
            "deungse": deungse,
        },
        "raw_ratio": round(raw_ratio, 4),
        "adjusted_ratio": round(adjusted, 4),
        "score": round(adjusted / (adjusted + 1), 3),
        "verdict": verdict,
        "verdict_ko": verdict_ko,
        "confidence": confidence,
        "status": "candidate",
        "evidence_refs": ["twelve-life-stage-map.csv", "heavenly-stems.csv", "hidden-stems.csv", "elements.csv", "classical-analysis-modules.csv"],
    }


def use_god_candidates(chart, tables: ElementTables):
    day = chart["four_pillars"]["day"]
    month = chart["four_pillars"]["month"]
    rule = tables.use_god.get((day["stem_code"], month["branch_code"]))
    if not rule:
        return {"status": "not_available", "candidates": []}

    balance = element_balance(chart, tables, convention="hidden")
    ratio = balance["ratio"]
    candidates = []
    for key, label in (("primary_use_element", "용신 후보"), ("secondary_use_element", "보조 용신 후보")):
        el = rule[key]
        if not el:
            continue
        present = ratio[el]
        note = "후보 오행이 차트에 충분하다" if present >= 0.2 else "후보 오행이 차트에 부족해 보강이 필요하다"
        candidates.append(
            {
                "element": el,
                "element_ko": ELEMENT_KO[el],
                "role": label,
                "chart_ratio": present,
                "balance_note": note,
            }
        )
    avoid = rule.get("avoid_element")
    if avoid:
        candidates.append({"element": avoid, "element_ko": ELEMENT_KO[avoid], "role": "경계 오행", "chart_ratio": ratio.get(avoid, 0), "balance_note": "과다 시 조절이 필요하다"})

    return {
        "status": "candidate",
        "day_stem": day["hanja"][0],
        "month_branch": month["hanja"][1],
        "modern_rule": rule["modern_rule"],
        "source_codes": rule["source_codes"].split(";"),
        "rule_confidence": rule["confidence"],
        "candidates": candidates,
        "evidence_refs": ["classical-seasonal-use-god-rules.csv", "classical-analysis-modules.csv"],
    }


def growth_direction(chart, tables: ElementTables):
    balance = element_balance(chart, tables, convention="hidden")
    deficient = balance["deficient"]
    dominant = balance["dominant"]
    quest = tables.growth_quests.get(deficient, {})
    dominant_quest = tables.growth_quests.get(dominant, {})
    return {
        "deficient_element": deficient,
        "deficient_quest": {
            "code": quest.get("quest_code"),
            "element_ko": ELEMENT_KO[deficient],
            "beast": quest.get("guardian_beast"),
            "routine_title": quest.get("quest_name"),
            "routine": quest.get("recommended_action"),
            "caution": quest.get("caution"),
        },
        "dominant_element": dominant,
        "dominant_caution": {
            "beast": dominant_quest.get("guardian_beast"),
            "caution": dominant_quest.get("caution"),
        },
        "status": "candidate",
        "evidence_refs": ["character-growth-quests.csv", "elements.csv", "modern-principles.csv"],
    }


# star_family → 길흉 방향성 (후보 레벨). 명시적 확정 판정이 아니다.
STAR_FAMILY_DIRECTION = {
    "noble": "positive",      # 천을귀인 계열 등 인덕·조력
    "charm": "neutral",       # 도화 계열 — 상황 의존
    "power": "negative",      # 양인·괴강 — 강한 긴장 에너지
    "blade": "negative",      # 백호대살 등 위기 결단
    "sensitive": "negative",  # 귀문관 — 통찰이자 불안 신호
    "skill": "neutral",       # 현침 — 재능과 깊이
}


def ten_gods(chart, tables: ElementTables):
    """십신 산출: 일간 기준 각 천간(연월일시)의 십신 + 범주 비중."""
    day = chart["four_pillars"]["day"]
    day_stem = day["stem_code"]
    rows = []
    category_counts = {}
    for name, pillar in chart["four_pillars"].items():
        if not pillar:
            continue
        relation = tables.ten_god_map.get((day_stem, pillar["stem_code"]))
        if not relation:
            continue
        category_counts[relation["category"]] = category_counts.get(relation["category"], 0) + 1
        rows.append(
            {
                "position": name,
                "stem": pillar["stem_code"],
                "ten_god": relation["ten_god_code"],
                "ten_god_ko": relation["ten_god_ko"],
                "category": relation["category"],
                "yinyang_relation": relation["yinyang_relation"],
            }
        )
    return {
        "day_stem": day_stem,
        "rows": rows,
        "category_counts": category_counts,
        "status": "candidate",
        "evidence_refs": ["ten-god-stem-map.csv", "ten-god-rules.csv"],
    }


def special_star_classification(chart, tables: ElementTables):
    """특수신살 길흉 분류 (후보 레벨, star_family 기반)."""
    stars = chart.get("auxiliary_signals", {}).get("special_stars", [])
    classified = []
    for star in stars:
        code = star.get("special_star_code") or star.get("code")
        meta = tables.special_stars.get(code, {})
        family = meta.get("star_family", "neutral")
        direction = STAR_FAMILY_DIRECTION.get(family, "neutral")
        classified.append(
            {
                "special_star_code": code,
                "ko_name": meta.get("ko_name", code),
                "star_family": family,
                "direction": direction,
                "positions": star.get("positions", []),
                "modern_domain": meta.get("modern_domain", ""),
            }
        )
    return {
        "stars": classified,
        "policy": "candidate_reference_not_deterministic_judgment",
        "status": "candidate",
        "evidence_refs": ["special-stars.csv", "special-star-rules.csv"],
    }


def analyze_chart(chart, tables: ElementTables | None = None):
    tables = tables or ElementTables()
    seasonal = use_god_candidates(chart, tables)
    classical = analyze_classical(chart)
    by_school = classical.get("useful_god_by_school") or {}
    seasonal_payload = dict(seasonal)
    seasonal_payload["schools"] = by_school.get("schools", {})
    seasonal_payload["agreement"] = by_school.get("agreement", False)
    seasonal_payload["agreement_element"] = by_school.get("agreement_element")
    seasonal_payload["merge_policy"] = "schools_stay_separate"
    return {
        "element_balance": element_balance(chart, tables),
        "day_master_strength": day_master_strength(chart, tables),
        "use_god_candidates": seasonal_payload,
        "use_god_schools": by_school,
        "growth_direction": growth_direction(chart, tables),
        "ten_gods": ten_gods(chart, tables),
        "special_star_classification": special_star_classification(chart, tables),
        "classical_analysis": classical,
        "chart_quality_flags": chart.get("quality_flags", []),
        "precision_policy": chart.get("precision_policy"),
    }


def main():
    import argparse
    import json
    from manse_engine import calculate_chart

    parser = argparse.ArgumentParser(description="NABOM element/strength/use-god analysis")
    parser.add_argument("--birth-date", required=True)
    parser.add_argument("--birth-time", default="")
    parser.add_argument("--gender", default="unknown")
    parser.add_argument("--birth-place", default="")
    parser.add_argument("--timezone", default="Asia/Seoul")
    args = parser.parse_args()

    chart = calculate_chart(
        birth_date=args.birth_date,
        birth_time=args.birth_time,
        gender=args.gender,
        birth_place=args.birth_place,
        timezone=args.timezone,
        tables=load_manse_tables(),
    )
    print(json.dumps(analyze_chart(chart), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
