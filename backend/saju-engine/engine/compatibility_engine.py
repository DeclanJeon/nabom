#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

from manse_engine import calculate_chart, load_tables as load_manse_tables

ROOT = Path(__file__).resolve().parent

GENERATION = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
CONTROL = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}
TEN_GOD_COMFORT = {
    "resource": 4,
    "output": 4,
    "wealth": 3,
    "peer": 2,
    "authority": -2,
}
SUPPORTIVE_SHINSAL = {"nyeonsal", "mangsin", "jangseong", "banan", "yeokma", "hwagae"}
CAUTION_SHINSAL = {"geopsal", "jaesal", "yukhae"}


def read_csv(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clamp(value, low, high):
    return max(low, min(high, value))


def load_tables():
    stems = {row["stem_code"]: row for row in read_csv("heavenly-stems.csv")}
    branches = {row["branch_code"]: row for row in read_csv("earthly-branches.csv")}
    elements = {row["element_code"]: row for row in read_csv("elements.csv")}
    scoring_rules = {row["rule_code"]: row for row in read_csv("compatibility-scoring-rules.csv")}
    weights = {row["feature_code"]: row for row in read_csv("compatibility-feature-weights.csv")}
    ten_god_map = {
        (row["day_stem_code"], row["target_stem_code"]): row
        for row in read_csv("ten-god-stem-map.csv")
    }
    use_god = {
        (row["day_stem_code"], row["month_branch_code"]): row
        for row in read_csv("classical-seasonal-use-god-rules.csv")
    }
    branch_relationships = read_csv("earthly-branch-relationships.csv")
    stem_relationships = read_csv("heavenly-stem-relationships.csv")
    shinsal_rules = read_csv("twelve-shinsal-rules.csv")
    shinsal_names = {row["shinsal_code"]: row["ko_name"] for row in read_csv("twelve-shinsal.csv")}
    templates = sorted(read_csv("compatibility-output-templates.csv"), key=lambda row: int(row["score_min"]))
    return {
        "stems": stems,
        "branches": branches,
        "elements": elements,
        "scoring_rules": scoring_rules,
        "weights": weights,
        "ten_god_map": ten_god_map,
        "use_god": use_god,
        "branch_relationships": branch_relationships,
        "stem_relationships": stem_relationships,
        "shinsal_rules": shinsal_rules,
        "shinsal_names": shinsal_names,
        "templates": templates,
    }


def day_pillar(chart):
    return chart["four_pillars"]["day"]


def month_pillar(chart):
    return chart["four_pillars"]["month"]


def chart_element_counts(chart, tables):
    counts = {element: 0 for element in GENERATION}
    for pillar in chart["four_pillars"].values():
        if not pillar:
            continue
        counts[tables["stems"][pillar["stem_code"]]["element_code"]] += 1
        counts[tables["branches"][pillar["branch_code"]]["element_code"]] += 1
    return counts


def element_names(elements, tables):
    return ",".join(tables["elements"][element]["ko_name"] for element in elements)


def object_particle(value):
    last = value[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3 and (code - 0xAC00) % 28:
        return "을"
    return "를"


def element_object_phrase(elements, tables):
    names = element_names(elements, tables)
    return f"{names}{object_particle(names)}"


def rule_note(tables, code, point):
    rule = tables["scoring_rules"][code]
    return {
        "rule_code": code,
        "points": point,
        "good": rule["good_copy"],
        "caution": rule["caution_copy"],
        "bucket": rule["output_bucket"],
    }


def relationship_lookup(rows, left_key, right_key, type_name=None):
    matched = []
    pair = {left_key, right_key}
    for row in rows:
        if type_name and row["relationship_type"] != type_name:
            continue
        if "left_stem" in row:
            if {row["left_stem"], row["right_stem"]} == pair:
                matched.append(row)
        else:
            branches = set(row["branches"].split(";"))
            if row["relationship_type"] in {"six_harmony", "clash"} and branches == pair:
                matched.append(row)
            elif row["relationship_type"] in {"triad", "seasonal", "punishment"} and pair.issubset(branches):
                matched.append(row)
    return matched


def score_day_stem(user_chart, partner_chart, tables):
    user = day_pillar(user_chart)
    partner = day_pillar(partner_chart)
    user_element = tables["stems"][user["stem_code"]]["element_code"]
    partner_element = tables["stems"][partner["stem_code"]]["element_code"]
    score = 10
    notes = []

    if user_element == partner_element:
        score += 4
        notes.append(rule_note(tables, "stem_same_element", 4))
    if GENERATION[user_element] == partner_element:
        score += 8
        notes.append(rule_note(tables, "stem_generates_partner", 8))
    if GENERATION[partner_element] == user_element:
        score += 8
        notes.append(rule_note(tables, "stem_supported_by_partner", 8))
    if CONTROL[user_element] == partner_element:
        score -= 5
        notes.append(rule_note(tables, "stem_controls_partner", -5))
    if CONTROL[partner_element] == user_element:
        score -= 5
        notes.append(rule_note(tables, "stem_controlled_by_partner", -5))

    for relation in relationship_lookup(tables["stem_relationships"], user["stem_code"], partner["stem_code"]):
        if relation["relationship_type"] == "combine":
            score += 7
            note = rule_note(tables, "stem_combine", 7)
            note["relationship_name"] = relation["ko_name"]
            notes.append(note)
        if relation["relationship_type"] == "clash":
            score -= 7
            note = rule_note(tables, "stem_clash", -7)
            note["relationship_name"] = relation["ko_name"]
            notes.append(note)

    return clamp(score, 0, 20), notes


def score_day_branch(user_chart, partner_chart, tables):
    user = day_pillar(user_chart)
    partner = day_pillar(partner_chart)
    score = 9
    notes = []
    rule_map = {
        "six_harmony": ("branch_six_harmony", 8),
        "triad": ("branch_triad", 7),
        "seasonal": ("branch_seasonal", 5),
        "clash": ("branch_clash", -8),
        "punishment": ("branch_punishment", -6),
    }
    for relation in relationship_lookup(tables["branch_relationships"], user["branch_code"], partner["branch_code"]):
        rule_code, delta = rule_map[relation["relationship_type"]]
        score += delta
        note = rule_note(tables, rule_code, delta)
        note["relationship_name"] = relation["ko_name"]
        note["interpretation"] = relation["interpretation"]
        notes.append(note)
    return clamp(score, 0, 18), notes


def score_element_complement(user_chart, partner_chart, tables):
    user_counts = chart_element_counts(user_chart, tables)
    partner_counts = chart_element_counts(partner_chart, tables)
    partner_needs = [element for element, count in partner_counts.items() if count == min(partner_counts.values())]
    user_needs = [element for element, count in user_counts.items() if count == min(user_counts.values())]
    score = 8
    notes = []
    supported = [element for element in user_needs if partner_counts[element] > 0]
    reciprocal = [element for element in partner_needs if user_counts[element] > 0]
    if supported:
        score += 6
        notes.append({"rule_code": "element_balance_complement", "points": 6, "good": f"상대 명식이 내 부족 오행 {element_object_phrase(supported, tables)} 보완한다", "caution": "보완을 의존으로 굳히지 않기", "bucket": "support"})
    if reciprocal:
        score += 2
        notes.append({"rule_code": "element_balance_reciprocal", "points": 2, "good": f"나도 상대 부족 오행 {element_object_phrase(reciprocal, tables)} 보완한다", "caution": "서로의 생활 루틴을 존중하기", "bucket": "support"})
    return clamp(score, 0, 16), notes


def score_ten_god(user_chart, partner_chart, tables):
    user = day_pillar(user_chart)
    partner = day_pillar(partner_chart)
    user_view = tables["ten_god_map"][(user["stem_code"], partner["stem_code"])]
    partner_view = tables["ten_god_map"][(partner["stem_code"], user["stem_code"])]
    score = 7 + TEN_GOD_COMFORT[user_view["category"]] + TEN_GOD_COMFORT[partner_view["category"]]
    notes = [
        {
            "rule_code": "ten_god_role_fit",
            "points": score - 7,
            "good": f"내 기준 상대는 {user_view['ten_god_ko']} 역할, 상대 기준 나는 {partner_view['ten_god_ko']} 역할로 읽힌다",
            "caution": "십신 역할은 실제 관계 대화와 함께 확인해야 한다",
            "bucket": "support" if score >= 8 else "caution",
        }
    ]
    return clamp(score, 0, 14), notes


def score_useful_element(user_chart, partner_chart, tables):
    user_day = day_pillar(user_chart)
    user_month = month_pillar(user_chart)
    partner_counts = chart_element_counts(partner_chart, tables)
    rule = tables["use_god"].get((user_day["stem_code"], user_month["branch_code"]))
    if not rule:
        return 6, []
    score = 4
    notes = []
    if partner_counts[rule["primary_use_element"]] > 0:
        score += 6
        notes.append(rule_note(tables, "useful_element_complement", 6))
    if partner_counts[rule["secondary_use_element"]] > 0:
        score += 2
        notes.append({"rule_code": "secondary_use_element_complement", "points": 2, "good": "상대가 보조 균형 오행도 일부 제공한다", "caution": "오행 보완은 계절과 전체 구조 안에서 확인한다", "bucket": "support"})
    return clamp(score, 0, 12), notes


def score_trigger_risk(branch_notes, stem_notes):
    score = 6
    notes = []
    for note in branch_notes + stem_notes:
        if note["bucket"] in {"good", "support"}:
            score += 1
        if note["bucket"] in {"tension", "caution"}:
            score -= 2
            notes.append({"rule_code": f"{note['rule_code']}_trigger", "points": -2, "good": note["good"], "caution": note["caution"], "bucket": note["bucket"]})
    return clamp(score, 0, 10), notes


def shinsal_for_partner_branch(user_branch_code, partner_branch_code, tables):
    for row in tables["shinsal_rules"]:
        if user_branch_code in row["base_branches"].split(";"):
            for code in ["geopsal", "jaesal", "cheonsal", "jisal", "nyeonsal", "wolsal", "mangsin", "jangseong", "banan", "yeokma", "yukhae", "hwagae"]:
                if row[code] == partner_branch_code:
                    return code
    return ""


def score_shinsal(user_chart, partner_chart, tables):
    code = shinsal_for_partner_branch(day_pillar(user_chart)["branch_code"], day_pillar(partner_chart)["branch_code"], tables)
    name = tables["shinsal_names"].get(code, "")
    if code in SUPPORTIVE_SHINSAL:
        score = 5
        bucket = "support"
        good = f"12신살 보조지표로 {name} 흐름이 관계 분위기를 살린다"
        caution = "12신살은 단독 결론이 아니라 보조 힌트로만 쓴다"
    elif code in CAUTION_SHINSAL:
        score = 2
        bucket = "caution"
        good = f"{name} 흐름은 관계에서 배울 지점을 보여준다"
        caution = "반복 갈등이나 불안 신호는 실제 대화로 확인한다"
    else:
        score = 3
        bucket = "support"
        good = f"12신살 보조지표는 {name or '중립'} 흐름으로 읽는다"
        caution = "세부 신살보다 일간 일지 오행 관계를 우선한다"
    return score, [{"rule_code": "twelve_shinsal_resonance", "points": score, "good": good, "caution": caution, "bucket": bucket, "shinsal_code": code, "shinsal_ko": name}]


def chart_quality_summary(role, chart):
    flags = sorted(set(chart.get("quality_flags", [])))
    solar_term_quality = chart.get("solar_term_quality", {})
    timezone_quality = chart.get("timezone_quality", {})
    return {
        "role": role,
        "source_quality": solar_term_quality.get("source_quality", "unknown"),
        "boundary_risk_level": solar_term_quality.get("boundary_risk_level", "unknown"),
        "confidence_score": solar_term_quality.get("confidence_score"),
        "confidence_band": solar_term_quality.get("confidence_band", "unknown"),
        "nearest_term_ko": solar_term_quality.get("nearest_term_ko", ""),
        "nearest_boundary_delta_hours": solar_term_quality.get("nearest_boundary_delta_hours"),
        "timezone_quality": timezone_quality,
        "quality_flags": flags,
    }


def score_quality(user_chart, partner_chart):
    flags = sorted(set(user_chart["quality_flags"] + partner_chart["quality_flags"]))
    score = 4
    notes = []

    def cap_score(cap, rule_code, caution):
        nonlocal score
        if score > cap:
            score = cap
        notes.append(
            {
                "rule_code": rule_code,
                "points": cap - 4,
                "good": "검증된 항목 위주로 궁합을 설명한다",
                "caution": caution,
                "bucket": "quality",
            }
        )

    if "noon_placeholder_for_missing_time" in flags or "birth_time_missing" in flags:
        cap_score(0, "data_quality_missing_birth_time", "출생시간 미상 때문에 시간주와 세부 점수 확신도를 낮춘다")
    if "birth_time_range_crosses_hour_branch" in flags:
        cap_score(1, "data_quality_time_range_crosses_hour_branch", "출생시간 범위가 시주 경계를 지나 세부 궁합 점수는 후보로 본다")
    if "ja_hour_candidate_only" in flags or "late_ja_hour_alternate_day_candidate" in flags:
        cap_score(1, "data_quality_ja_hour_candidate_only", "자시 경계 후보가 있어 일주/시주 기반 관계 해석을 후보로 본다")
    if "approximate_solar_terms" in flags:
        cap_score(2, "data_quality_approximate_solar_terms", "검증 절기 시각이 없는 연도라 월주·대운 기반 궁합 확신도를 낮춘다")
    if "approximate_solar_term_boundary_risk" in flags:
        cap_score(1, "data_quality_approximate_boundary_risk", "근사 절기 경계 근처 입력이라 월주 경계가 달라질 수 있다")
    if "birth_place_missing" in flags:
        cap_score(2, "data_quality_birth_place_missing", "출생지가 비어 있어 시간대 입력은 사용하지만 지역 맥락을 보수적으로 본다")
    if "timezone_fixed_offset_used" in flags:
        score = min(score, 3)
        notes.append(
            {
                "rule_code": "data_quality_fixed_timezone_offset",
                "points": -1,
                "good": "입력한 UTC offset을 그대로 사용해 계산한다",
                "caution": "IANA 시간대가 아니므로 DST나 역사적 offset 검증은 제한된다",
                "bucket": "quality",
            }
        )
    if "timezone_historical_offset_used" in flags or "timezone_dst_offset_used" in flags:
        notes.append(
            {
                "rule_code": "data_quality_timezone_offset_trace",
                "points": 0,
                "good": "시간대 DB의 실제 offset trace를 보존해 계산 근거를 확인할 수 있다",
                "caution": "지역·시대 시간대가 해석에 영향을 줄 수 있어 품질 안내와 함께 본다",
                "bucket": "quality",
            }
        )
    if "birth_time_range_touches_hour_boundary" in flags:
        score = min(score, 3)
        notes.append(
            {
                "rule_code": "data_quality_time_range_touches_hour_boundary",
                "points": -1,
                "good": "검증된 항목 위주로 궁합을 설명한다",
                "caution": "출생시간 범위가 시주 경계에 닿아 세부 시간 해석은 보수적으로 본다",
                "bucket": "quality",
            }
        )
    summary = {
        "score": score,
        "max_points": 4,
        "user": chart_quality_summary("user", user_chart),
        "partner": chart_quality_summary("partner", partner_chart),
        "evidence_refs": ["compatibility-scoring-model.md", "compatibility-feature-weights.csv"],
    }
    return score, notes, flags, summary


def choose_template(score, quality_flags, tables):
    if "noon_placeholder_for_missing_time" in quality_flags or "birth_time_missing" in quality_flags:
        return next(row for row in tables["templates"] if row["template_code"] == "quality_overlay")
    for row in tables["templates"]:
        if row["template_code"] == "quality_overlay":
            continue
        if int(row["score_min"]) <= score <= int(row["score_max"]):
            return row
    return tables["templates"][-2]


def score_band(score):
    if score >= 85:
        return "very_high", "매우 높음"
    if score >= 70:
        return "high", "높음"
    if score >= 55:
        return "medium", "보통"
    if score >= 40:
        return "low", "낮음"
    return "very_low", "매우 낮음"


def score_display_policy(score, quality_score, quality_flags):
    band, band_label = score_band(score)
    exact_score_allowed = quality_score >= 3
    display_flags = list(quality_flags)
    if not exact_score_allowed and "compatibility_exact_score_suppressed" not in display_flags:
        display_flags.append("compatibility_exact_score_suppressed")
    return {
        "score_band": band,
        "score_band_label_ko": band_label,
        "score_display_policy": "exact_score_allowed" if exact_score_allowed else "score_band_only_low_confidence",
        "exact_score_allowed": exact_score_allowed,
        "quality_flags": sorted(set(display_flags)),
    }


def explain_points(feature_results):
    good_points = []
    caution_points = []
    evidence = []
    for feature in feature_results:
        for note in feature["notes"]:
            if note["bucket"] in {"good", "support"}:
                good_points.append(note["good"])
            if note["bucket"] in {"caution", "tension", "quality"} or note.get("caution"):
                caution_points.append(note["caution"])
            evidence.append(note)
    return good_points[:6], caution_points[:6], evidence


def calculate_compatibility_from_charts(user_chart, partner_chart, tables=None):
    tables = tables or load_tables()
    stem_score, stem_notes = score_day_stem(user_chart, partner_chart, tables)
    branch_score, branch_notes = score_day_branch(user_chart, partner_chart, tables)
    element_score, element_notes = score_element_complement(user_chart, partner_chart, tables)
    ten_god_score, ten_god_notes = score_ten_god(user_chart, partner_chart, tables)
    useful_score, useful_notes = score_useful_element(user_chart, partner_chart, tables)
    trigger_score, trigger_notes = score_trigger_risk(branch_notes, stem_notes)
    shinsal_score, shinsal_notes = score_shinsal(user_chart, partner_chart, tables)
    quality_score, quality_notes, quality_flags, quality_summary = score_quality(user_chart, partner_chart)

    feature_results = [
        {"feature_code": "day_stem_relation", "ko_name": tables["weights"]["day_stem_relation"]["ko_name"], "score": stem_score, "max_points": 20, "notes": stem_notes},
        {"feature_code": "day_branch_relation", "ko_name": tables["weights"]["day_branch_relation"]["ko_name"], "score": branch_score, "max_points": 18, "notes": branch_notes},
        {"feature_code": "element_balance_complement", "ko_name": tables["weights"]["element_balance_complement"]["ko_name"], "score": element_score, "max_points": 16, "notes": element_notes},
        {"feature_code": "ten_god_role_fit", "ko_name": tables["weights"]["ten_god_role_fit"]["ko_name"], "score": ten_god_score, "max_points": 14, "notes": ten_god_notes},
        {"feature_code": "useful_element_support", "ko_name": tables["weights"]["useful_element_support"]["ko_name"], "score": useful_score, "max_points": 12, "notes": useful_notes},
        {"feature_code": "relationship_trigger_risk", "ko_name": tables["weights"]["relationship_trigger_risk"]["ko_name"], "score": trigger_score, "max_points": 10, "notes": trigger_notes},
        {"feature_code": "twelve_shinsal_resonance", "ko_name": tables["weights"]["twelve_shinsal_resonance"]["ko_name"], "score": shinsal_score, "max_points": 6, "notes": shinsal_notes},
        {"feature_code": "data_quality_confidence", "ko_name": tables["weights"]["data_quality_confidence"]["ko_name"], "score": quality_score, "max_points": 4, "notes": quality_notes},
    ]
    score = sum(feature["score"] for feature in feature_results)
    template = choose_template(score, quality_flags, tables)
    display_policy = score_display_policy(score, quality_score, quality_flags)
    good_points, caution_points, evidence = explain_points(feature_results)
    return {
        "engine_metadata": {
            "engine": "compatibility-korean-v1",
            "manse_engine_versions": sorted(
                {
                    chart.get("engine_metadata", {}).get("engine_version", "unknown")
                    for chart in (user_chart, partner_chart)
                }
            ),
            "scoring_rule_source": "compatibility-scoring-rules.csv",
            "feature_weight_source": "compatibility-feature-weights.csv",
        },
        "score": score,
        "score_max": 100,
        "score_band": display_policy["score_band"],
        "score_band_label_ko": display_policy["score_band_label_ko"],
        "score_display_policy": display_policy["score_display_policy"],
        "exact_score_allowed": display_policy["exact_score_allowed"],
        "label": template["ko_label"],
        "relationship_feel": template["relationship_feel"],
        "good_points": good_points or [template["good_prompt"]],
        "caution_points": caution_points or [template["caution_prompt"]],
        "guardrail": template["guardrail"],
        "feature_scores": feature_results,
        "evidence": evidence,
        "quality_flags": display_policy["quality_flags"],
        "quality_summary": quality_summary,
        "user_chart": user_chart,
        "partner_chart": partner_chart,
    }


def calculate_compatibility(user_input, partner_input, tables=None, manse_tables=None):
    tables = tables or load_tables()
    manse_tables = manse_tables or load_manse_tables()
    user_chart = calculate_chart(**user_input, tables=manse_tables)
    partner_chart = calculate_chart(**partner_input, tables=manse_tables)
    return calculate_compatibility_from_charts(user_chart, partner_chart, tables=tables)


def main():
    parser = argparse.ArgumentParser(description="Calculate saju compatibility from two birth inputs.")
    parser.add_argument("--user-birth-date", required=True)
    parser.add_argument("--user-birth-time", default="")
    parser.add_argument("--user-gender", default="unknown")
    parser.add_argument("--user-birth-place", default="")
    parser.add_argument("--partner-birth-date", required=True)
    parser.add_argument("--partner-birth-time", default="")
    parser.add_argument("--partner-gender", default="unknown")
    parser.add_argument("--partner-birth-place", default="")
    args = parser.parse_args()
    result = calculate_compatibility(
        {
            "birth_date": args.user_birth_date,
            "birth_time": args.user_birth_time,
            "gender": args.user_gender,
            "birth_place": args.user_birth_place,
        },
        {
            "birth_date": args.partner_birth_date,
            "birth_time": args.partner_birth_time,
            "gender": args.partner_gender,
            "birth_place": args.partner_birth_place,
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
