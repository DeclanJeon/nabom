"""Profile lenses: everyday-language, no myeongni leak, candidate-only."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["NABOM_GENERATE_CHARACTERS"] = "0"

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "nabom-api" / "app"))

import profile_lenses  # noqa: E402


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def sample(verdict="shinyak", element="fire", month_branch="寅", category="authority", deficient="metal"):
    return {
        "day_master_strength": {
            "verdict": verdict,
            "day_master": {"element": element},
            "season_support": {"month_branch": month_branch, "deungnyeong": True},
            "strength_flags": {"deungnyeong": True, "deungji": False, "deungse": False},
        },
        "element_balance": {"dominant": "water", "deficient": "metal", "ratio": {"water": 0.56}},
        "growth_direction": {
            "deficient_element": deficient,
            "dominant_element": "water",
            "deficient_quest": {"routine": "선택 기준을 정하고 불필요한 일을 줄이기"},
        },
        "ten_gods": {"category_counts": {category: 3, "peer": 1}},
        "classical_analysis": {
            "pattern_success_failure": {
                "helper_element": "wood",
                "controller_element": "water",
                "verdict_ko": "성립 유리 후보",
            }
        },
        "special_star_classification": {
            "stars": [
                {"star_family": "noble", "direction": "positive"},
                {"star_family": "blade", "direction": "negative"},
            ]
        },
    }


def run():
    lenses = profile_lenses.build_lenses(sample())
    require(isinstance(lenses["headline"], list) and 1 <= len(lenses["headline"]) <= 3, lenses["headline"])
    require("표현력" in lenses["headline"], lenses["headline"])
    require("책임감" in lenses["headline"], lenses["headline"])
    for key in ("energy_style", "element_style", "season_rhythm", "relation_style", "root_support", "attention_points", "summary", "pattern_balance", "stability"):
        require(key in lenses, f"missing lens {key}")
    require(lenses["season_rhythm"]["title"] == "초봄의 기운", lenses["season_rhythm"])
    require(lenses["relation_style"]["title"] == "책임감", lenses["relation_style"])
    require(len(lenses["attention_points"]) >= 1, lenses["attention_points"])
    require(lenses["summary"]["moving_force"]["title"] == "나를 움직이는 힘", lenses["summary"])
    require(lenses["summary"]["adjust_point"]["title"] == "조율 포인트", lenses["summary"])
    require(lenses["summary"]["today_action"]["title"] == "오늘의 실천", lenses["summary"])
    require(lenses["pattern_balance"]["good"]["title"] == "잘 쓰이면", lenses["pattern_balance"])
    require(lenses["pattern_balance"]["over"]["title"] == "과하면", lenses["pattern_balance"])
    require("안정적" in lenses["stability"]["body"], lenses["stability"])

    raw = str(lenses)
    for leaked in ("주작", "백호", "청룡", "현무", "황룡", "일간", "병화", "오행", "용신", "신강", "신약", "십신", "편관", "비견", "천간", "지지", "대운", "세운", "운세", "사주", "궁합"):
        require(leaked not in raw, f"myeongni term leaked: {leaked}")

    male = profile_lenses.build_lenses(sample(verdict="shingang", month_branch="午", category="expression"))
    require(male["energy_style"]["title"] == "에너지가 바깥으로 퍼지는 편", male["energy_style"])
    require(male["season_rhythm"]["title"] == "한여름의 기운", male["season_rhythm"])
    require(male["relation_style"]["title"] == "표현력", male["relation_style"])

    no_stars = profile_lenses.build_lenses(sample(month_branch="子"))
    require(no_stars["season_rhythm"]["title"] == "한겨울의 기운", no_stars["season_rhythm"])

    print("profile-lenses: PASS")


if __name__ == "__main__":
    run()
