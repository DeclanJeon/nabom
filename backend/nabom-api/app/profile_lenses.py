"""Profile lenses: everyday-language readings of the engine analysis.

The saju engine produces structured signals (ten gods, season support, element
balance, strength flags, special stars). All of it is classical vocabulary that
must not reach the user. This module translates those signals into everyday
language lenses so a profile feels multi-dimensional without ever saying
오행/일간/십신/신살/용신.

Every lens is a candidate hypothesis, never a verdict.
"""

from __future__ import annotations

# ── Everyday voice tables (internal only) ──────────────────────────────────

ELEMENT_HEADLINE = {
    "wood": "도전",
    "fire": "표현력",
    "earth": "안정감",
    "metal": "판단력",
    "water": "직관력",
}

ELEMENT_STYLE = {
    "wood": ("움직이고 시작하는 힘이 먼저 보여요", "새로운 길을 열고 성장시키는 쪽으로 에너지가 흘러요"),
    "fire": ("밝게 드러내고 표현하는 힘이 먼저 보여요", "생각과 감정을 밖으로 꺼내면 힘이 살아나요"),
    "earth": ("차분히 지키고 돌보는 힘이 먼저 보여요", "자리와 관계를 안정시키는 쪽으로 에너지가 흘러요"),
    "metal": ("또렷하게 가르고 정리하는 힘이 먼저 보여요", "기준을 세우고 불필요한 것을 줄이는 쪽이 자연스러워요"),
    "water": ("깊이 보고 흐름을 읽는 힘이 먼저 보여요", "생각을 모아 숨 고르는 쪽으로 에너지가 흘러요"),
}

ENERGY_STYLE = {
    "shingang": {
        "title": "에너지가 바깥으로 퍼지는 편",
        "body": "새로운 일을 시작하고 주변을 움직이는 힘이 먼저 보여요. 지칠 때는 잠시 멈추고 모으는 연습이 도움이 돼요.",
    },
    "shinyak": {
        "title": "에너지를 아껴 안쪽으로 모으는 편",
        "body": "깊이 듣고 차분히 정리하는 힘이 먼저 보여요. 바깥으로 내보내는 연습을 조금씩 하면 힘이 살아나요.",
    },
    "neutral": {
        "title": "바깥과 안쪽이 비슷하게 흐르는 편",
        "body": "쓰는 힘과 모으는 힘이 균형을 이루고 있어요. 상황에 따라 유연하게 움직일 수 있는 편이에요.",
    },
}

SEASON_RHYTHM = {
    "寅": ("초봄의 기운", "겨울잠에서 깨어나 새싹이 움트는 시기예요. 시작과 도전이 자연스러운 리듬이에요."),
    "卯": ("한창 봄의 기운", "꽃이 피고 퍼져나가는 시기예요. 관계와 표현이 활발해지는 리듬이에요."),
    "辰": ("늦봄의 기운", "봄이 무르익어 정리로 넘어가는 시기예요. 쌓은 것을 다듬는 리듬이에요."),
    "巳": ("초여름의 기운", "온도가 올라가고 활동이 커지는 시기예요. 추진력이 살아나는 리듬이에요."),
    "午": ("한여름의 기운", "빛과 열이 가장 강한 시기예요. 드러내고 주도하는 리듬이 자연스러워요."),
    "未": ("늦여름의 기운", "열기가 무르익어 결실을 준비하는 시기예요. 돌보고 가꾸는 리듬이에요."),
    "申": ("초가을의 기운", "더위가 꺾이고 정리가 시작되는 시기예요. 거두고 가르는 리듬이에요."),
    "酉": ("가을 한창의 기운", "결실을 거두고 기준을 세우는 시기예요. 판단과 정돈이 살아나는 리듬이에요."),
    "戌": ("늦가을의 기운", "수확을 마무리하고 보관을 준비하는 시기예요. 지킴과 저장의 리듬이에요."),
    "亥": ("초겨울의 기운", "활동이 가라앉고 내면으로 향하는 시기예요. 쉼과 성찰의 리듬이에요."),
    "子": ("한겨울의 기운", "깊이 잠기고 재충전하는 시기예요. 내면을 듣고 비축하는 리듬이에요."),
    "丑": ("늦겨울의 기운", "겨울이 끝나가며 새싹을 준비하는 시기예요. 견디며 비축하는 리듬이에요."),
}

RELATION_STYLE = {
    "authority": {
        "keyword": "책임감",
        "body": "책임을 지고 기준을 세우는 역할을 자주 맡는 편이에요. 혼자 다 짊어지려다 무거워질 수 있어요.",
    },
    "peer": {
        "keyword": "주체성",
        "body": "동등한 관계에서 힘을 얻는 편이에요. 함께 세우는 쪽이 더 오래 가요.",
    },
    "expression": {
        "keyword": "표현력",
        "body": "생각과 감정을 밖으로 꺼내는 힘이 있는 편이에요. 나눌수록 더 선명해져요.",
    },
    "resource": {
        "keyword": "직관력",
        "body": "배우고 깊이 보는 힘이 있는 편이에요. 정보를 모으고 되새기는 쪽이 자연스러워요.",
    },
    "wealth": {
        "keyword": "현실감",
        "body": "현실적인 성과를 만드는 힘에 관심이 가는 편이에요. 결실을 보는 데서 힘을 얻어요.",
    },
}

ROOT_SUPPORT = {
    "season": "태어난 계절의 기운이 나를 버텨주는 편",
    "place": "자리에서 뿌리를 얻는 편",
    "peers": "주변의 힘을 얻는 편",
    "none": "혼자 버티기보다 곁의 힘을 함께 쓰는 쪽이 자연스러운 편",
}

ATTENTION_NOBLE = "곁에 도움을 주는 사람이 생기는 흐름이 있는 편"
ATTENTION_BLADE = "위기에 강하게 반응하는 편이라, 예민할 때는 숨 고르기가 도움이 돼요"
ATTENTION_TRAP = "매력과 걱정이 함께 오는 흐름이 있는 편이라, 선택을 천천히 해보는 게 좋아요"

# fatemirror '잘 쓰이면 / 과하면' 이진 구조 → 일상어
HELPER_VOICE = {
    "wood": "앞으로 나아가는 힘을 잘 살리면 계획이 실행으로 이어져요",
    "fire": "드러내고 표현하는 힘을 잘 살리면 사람과 일에 활기가 퍼져요",
    "earth": "차분히 챙기는 힘을 잘 살리면 관계와 자리가 안정돼요",
    "metal": "기준을 세우는 힘을 잘 살리면 정리와 결단이 빨라져요",
    "water": "깊이 보는 힘을 잘 살리면 흐름을 읽고 미리 준비할 수 있어요",
}

CONTROLLER_VOICE = {
    "wood": "지나치면 밀어붙이는 쪽으로 치우치니, 잠시 멈추고 살펴보는 시간이 필요해요",
    "fire": "지나치면 감정이 앞서니, 말하기 전에 숨을 한 번 고르면 좋아요",
    "earth": "지나치면 고집과 안주로 이어지니, 작은 변화를 열어두면 좋아요",
    "metal": "지나치면 날카로워지니, 표현을 한 톤 부드럽게 다듬으면 좋아요",
    "water": "지나치면 생각에 빠지니, 몸을 움직여 순환시키면 좋아요",
}

# fatemirror '3분 요약' 3카드 → 일상어
MOVING_FORCE = {
    "wood": "새로운 길을 열고 성장시키는 힘이 먼저 움직여요",
    "fire": "생각과 감정을 밖으로 꺼내는 힘이 먼저 움직여요",
    "earth": "자리와 관계를 안정시키는 힘이 먼저 움직여요",
    "metal": "기준을 세우고 정리하는 힘이 먼저 움직여요",
    "water": "깊이 보고 흐름을 읽는 힘이 먼저 움직여요",
}

ADJUST_POINT = {
    "wood": "계획만 쌓이지 않게 작은 실행까지 연결하기",
    "fire": "마음이 달아오르면 잠시 쉬고 수면을 먼저 챙기기",
    "earth": "완벽보다 매일 반복할 수 있는 작은 기준 두기",
    "metal": "판단이 날카로워질 때 표현을 부드럽게 바꾸기",
    "water": "생각이 깊어질수록 몸을 움직여 순환시키기",
}

FORBIDDEN = (
    "주작",
    "백호",
    "청룡",
    "현무",
    "황룡",
    "일간",
    "병화",
    "오행",
    "용신",
    "신강",
    "신약",
    "십신",
    "편관",
    "비견",
    "천간",
    "지지",
    "대운",
    "세운",
    "운세",
    "궁합",
    "사주",
)


def _pick_category(analysis: dict) -> tuple[str, int]:
    counts = (analysis.get("ten_gods") or {}).get("category_counts") or {}
    if not counts:
        return "peer", 0
    return max(counts.items(), key=lambda item: item[1])


def _season_key(analysis: dict) -> str:
    month_branch = (
        (analysis.get("day_master_strength") or {}).get("season_support") or {}
    ).get("month_branch") or "寅"
    return month_branch if month_branch in SEASON_RHYTHM else "寅"


def build_headline(analysis: dict) -> list[str]:
    """2–3 everyday keywords, like 병자 리포트의 '표현력 · 직관 · 책임감'."""
    day = (analysis.get("day_master_strength") or {}).get("day_master") or {}
    element = day.get("element") or "earth"
    keywords = [ELEMENT_HEADLINE.get(element, "균형")]
    category, count = _pick_category(analysis)
    style = RELATION_STYLE.get(category)
    if style and count >= 1:
        keywords.append(style["keyword"])
    deficient = (analysis.get("growth_direction") or {}).get("deficient_element") or ""
    if deficient and deficient != element and len(keywords) < 3:
        keywords.append(ELEMENT_HEADLINE.get(deficient, "회복력"))
    return keywords[:3]


def build_lenses(analysis: dict) -> dict:
    """All everyday language. Each lens is a candidate hypothesis."""
    day = (analysis.get("day_master_strength") or {}).get("day_master") or {}
    strength = analysis.get("day_master_strength") or {}
    element = day.get("element") or "earth"
    verdict = strength.get("verdict") or "neutral"
    if verdict not in ENERGY_STYLE:
        verdict = "neutral"

    style_title, style_body = ELEMENT_STYLE.get(element, ELEMENT_STYLE["earth"])

    category, _count = _pick_category(analysis)
    relation = RELATION_STYLE.get(category, RELATION_STYLE["peer"])

    season_key = _season_key(analysis)
    season_title, season_body = SEASON_RHYTHM[season_key]

    flags = (strength.get("strength_flags") or {})
    deungnyeong = flags.get("deungnyeong")
    deungji = flags.get("deungji")
    deungse = flags.get("deungse")
    if deungnyeong:
        root = ROOT_SUPPORT["season"]
    elif deungji:
        root = ROOT_SUPPORT["place"]
    elif deungse:
        root = ROOT_SUPPORT["peers"]
    else:
        root = ROOT_SUPPORT["none"]

    attention = []
    stars = (analysis.get("special_star_classification") or {}).get("stars") or []
    for star in stars:
        family = star.get("star_family") or "neutral"
        direction = star.get("direction") or "neutral"
        text = None
        if family == "noble":
            text = ATTENTION_NOBLE
        elif direction == "negative" and family in {"blade", "harm", "trap", "star"}:
            text = ATTENTION_BLADE
        elif direction == "negative":
            text = ATTENTION_TRAP
        if text and text not in attention:
            attention.append(text)
        if len(attention) >= 2:
            break

    # ── fatemirror 3분 요약: 나를 움직이는 힘 / 조율 포인트 / 오늘의 실천 ──
    dominant = (analysis.get("element_balance") or {}).get("dominant") or element
    deficient = (analysis.get("growth_direction") or {}).get("deficient_element") or (
        (analysis.get("element_balance") or {}).get("deficient") or "earth"
    )
    quest = ((analysis.get("growth_direction") or {}).get("deficient_quest") or {}).get("routine")
    summary = {
        "moving_force": {"title": "나를 움직이는 힘", "body": MOVING_FORCE.get(dominant, MOVING_FORCE["earth"])},
        "adjust_point": {"title": "조율 포인트", "body": ADJUST_POINT.get(deficient, ADJUST_POINT["earth"])},
        "today_action": {
            "title": "오늘의 실천",
            "body": quest or ADJUST_POINT.get(deficient, ADJUST_POINT["earth"]),
        },
    }

    # ── fatemirror 잘 쓰이면 / 과하면: 격국 보호·조절 힘 → 일상어 ──
    pattern = ((analysis.get("classical_analysis") or {}).get("pattern_success_failure") or {})
    helper = pattern.get("helper_element") or ""
    controller = pattern.get("controller_element") or ""
    pattern_balance = {
        "verdict": pattern.get("verdict_ko") or "후보",
        "good": {"title": "잘 쓰이면", "body": HELPER_VOICE.get(helper, HELPER_VOICE["earth"])},
        "over": {"title": "과하면", "body": CONTROLLER_VOICE.get(controller, CONTROLLER_VOICE["earth"])},
    }

    # ── fatemirror 계산 안정도: 품질 플래그 → 일상어 신뢰 ──
    flags = analysis.get("chart_quality_flags") or []
    stability_points = []
    if not any("birth_time" in f or "time" in f for f in flags):
        pass  # 시간이 정확하면 별도 신뢰 문구 없음
    for flag in flags:
        if "time" in flag and "birth_time_missing" in flag:
            stability_points.append("태어난 시간이 불명확해서, 시간에 민감한 해석은 아주 느슨한 가설이에요")
        elif "approximate" in flag:
            stability_points.append("입력 정보가 근사치라서, 세부 해석은 넓은 범위로 봐주세요")
    if not stability_points and "precision" in (analysis.get("precision_policy") or {}):
        pass
    stability = {
        "title": "계산 안정도",
        "body": " ".join(stability_points) if stability_points else "입력 정보가 정확해서 해석의 기반이 안정적이에요",
        "points": stability_points,
    }

    lenses = {
        "headline": build_headline(analysis),
        "summary": summary,
        "energy_style": {"title": ENERGY_STYLE[verdict]["title"], "body": ENERGY_STYLE[verdict]["body"]},
        "element_style": {"title": style_title, "body": style_body},
        "season_rhythm": {"title": season_title, "body": season_body},
        "relation_style": {"title": relation["keyword"], "body": relation["body"]},
        "root_support": {"title": "버팀의 흐름", "body": root},
        "pattern_balance": pattern_balance,
        "stability": stability,
        "attention_points": attention,
    }

    raw = json_dumps(lenses)
    leaked = [term for term in FORBIDDEN if term in raw]
    if leaked:
        raise ValueError(f"profile lenses leaked forbidden terms: {leaked}")
    return lenses


def json_dumps(value: dict) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)
