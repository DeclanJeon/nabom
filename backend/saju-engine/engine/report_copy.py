#!/usr/bin/env python3
"""Report copy assembly: engine outputs → user-facing Korean sentences.

원칙 (NABOM 문장 정책):
- 확정/운명/필연 표현 금지 (guardrail로 강제)
- 모든 문장은 후보·가설·관찰 레벨
- 추천은 실행 가능하고 가역적인 단일 행동
"""

from __future__ import annotations

FORBIDDEN = ["운명", "반드시", "확실", "무조건", "절대", "타고난 정해진", "당신은 원래", "예언", "필연"]


def _guard(segments: list[str]) -> list[str]:
    clean = []
    for s in segments:
        s = s.strip()
        if not s:
            continue
        lowered = s
        if any(w in lowered for w in FORBIDDEN):
            continue
        clean.append(s)
    return clean


def strength_copy(strength: dict) -> str:
    ko = strength["verdict_ko"]
    reason = strength["season_support"]["reason"]
    root = strength["root_support"]["stage"]
    return f"일간은 {ko}로 보이며, {reason}하지만 일지 뿌리는 {root} 상태입니다. 이는 후보 판단입니다."


def element_copy(balance: dict) -> str:
    dom = balance["dominant"]
    deff = balance["deficient"]
    return (
        f"오행 분포를 보면 {dom}이(가) 가장 많고 {deff}이(가) 가장 적은 흐름이 보입니다. "
        f"절대 수치가 아니라 분포 경향으로만 참고하세요."
    )


def use_god_copy(use_god: dict) -> str:
    rules = []
    for c in use_god.get("candidates", []):
        note = "차트에 부족해 보강이 필요해 보입니다" if c.get("chart_ratio", 1) < 0.15 else "이미 어느 정도 갖춰져 있습니다"
        rules.append(f"{c['role']}인 {c['element_ko']}을(를) 살피며, {note}")
    return "용신 후보: " + " / ".join(rules) + " (고전 규칙 기반 후보입니다)."


def pattern_copy(classical: dict) -> str:
    p = classical["pattern_assessment"]
    c = classical["climate_adjustment"]
    return (
        f"월지 본기로 보는 격국 후보는 {p['pattern_name']}이며, {p['reason']} 상태입니다. "
        f"계절 조후는 {c['temperature_bias']}·{c['moisture_bias']} 편향으로, {c['climate_use_god_ko']}의 보완을 살펴볼 수 있습니다."
    )


def growth_copy(growth: dict) -> str:
    q = growth["deficient_quest"]
    return (
        f"지금은 {q['beast']}의 성장 루틴, «{q['routine_title']}»을 시도해 볼 수 있습니다: "
        f"{q['routine']}. 주의점은 {q['caution']}입니다."
    )


def luck_copy(luck: dict) -> str:
    annual = luck.get("annual", {})
    monthly = luck.get("monthly")
    parts = [f"{annual.get('year')}년 세운은 {annual.get('pillar', {}).get('ko', '')}으로 읽힙니다"]
    if monthly:
        m = monthly
        parts.append(f"{m.get('month')}월 월운은 {m.get('pillar', {}).get('ko', '')} ({m.get('solar_term', '')} 기준)")
    parts.append("운세는 예측이 아니라 흐름 참고용입니다")
    return ". ".join(parts) + "."


def action_copy(analysis: dict) -> str:
    """실행 가능한 단일 행동 제안 (가역적)."""
    s = analysis["day_master_strength"]
    if s["verdict"] == "shinyak":
        return "이번 주에는 하루 한 가지 일에만 집중하고 나머지는 기록만 남겨보세요."
    if s["verdict"] == "shingang":
        return "에너지가 실린 주이니, 한 가지 과제를 끝까지 마무리하는 데 시간을 써보세요."
    return "이번 주에는 기분과 에너지 변화를 짧게 기록해 흐름을 살펴보세요."


def build_narrative(analysis: dict, classical: dict | None = None, luck: dict | None = None) -> dict:
    """엔진 산출물 → 사용자-facing 문장 조립 (guardrail 적용)."""
    segments = [
        strength_copy(analysis["day_master_strength"]),
        element_copy(analysis["element_balance"]),
        use_god_copy(analysis["use_god_candidates"]),
    ]
    if classical:
        segments.append(pattern_copy(classical))
    segments.append(growth_copy(analysis["growth_direction"]))
    if luck:
        segments.append(luck_copy(luck))
    segments.append(action_copy(analysis))
    clean = _guard(segments)
    return {
        "narrative": clean,
        "action": action_copy(analysis),
        "guardrail": {"forbidden_terms": FORBIDDEN, "removed": len(segments) - len(clean)},
        "status": "candidate",
    }


def main():
    import argparse
    import json
    from manse_engine import calculate_chart, load_tables
    from element_analysis import analyze_chart
    from classical_analysis import analyze_classical
    from luck_analysis import luck_outlook
    from zoneinfo import ZoneInfo

    parser = argparse.ArgumentParser()
    parser.add_argument("--birth-date", required=True)
    parser.add_argument("--birth-time", default="")
    parser.add_argument("--gender", default="unknown")
    parser.add_argument("--birth-place", default="")
    parser.add_argument("--year", type=int, default=2026)
    args = parser.parse_args()

    chart = calculate_chart(birth_date=args.birth_date, birth_time=args.birth_time, gender=args.gender,
                            birth_place=args.birth_place, timezone="Asia/Seoul", tables=load_tables())
    chart["_tzinfo"] = ZoneInfo("Asia/Seoul")
    analysis = analyze_chart(chart)
    classical = analyze_classical(chart)
    luck = luck_outlook(chart, load_tables(), reference_year=args.year)
    print(json.dumps(build_narrative(analysis, classical, luck), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
