"""Character visuals are keyed by everyday analysis, generated once per key."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_GENERATE_CHARACTERS"] = "0"
os.environ["NABOM_CHARACTER_DIR"] = tempfile.mkdtemp(prefix="nabom-char-")

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "nabom-api" / "app"))

import character_visual  # noqa: E402


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def sample(verdict="shinyak", dominant="water", deficient="fire", water=0.42, fire=0.18, wood=0.12, earth=0.16, metal=0.12):
    return {
        "day_master_strength": {
            "verdict": verdict,
            "day_master": {"element": "fire"},
        },
        "element_balance": {
            "dominant": dominant,
            "deficient": deficient,
            "ratio": {"wood": wood, "fire": fire, "earth": earth, "metal": metal, "water": water},
        },
        "growth_direction": {"deficient_element": deficient, "dominant_element": dominant},
    }


def run():
    first = character_visual.build_character_visual(sample())
    require(first["code"] == "brightener", first)
    require(first["label_ko"] == "분위기를 밝히는 사람", first)
    require(first["visual_key"] == "brightener_shinyak_water_fire_mid_unknown", first)
    male = character_visual.build_character_visual(sample(), "male")
    female = character_visual.build_character_visual(sample(), "female")
    require(male["visual_key"] == "brightener_shinyak_water_fire_mid_male", male)
    require(female["visual_key"] == "brightener_shinyak_water_fire_mid_female", female)
    require(male["visual_key"] != female["visual_key"], "gender splits visual key")
    require("chibi man" in character_visual.build_character_prompt(male), "male prompt")
    require("chibi woman" in character_visual.build_character_prompt(female), "female prompt")

    # 단계 심볼: 아키타입×단계별 고유 아이템이 프롬프트에 명시된다
    grown = character_visual.build_character_visual(sample(), "male", recorded_days=63)  # stage 10
    grown_prompt = character_visual.build_character_prompt(grown)
    require("stage 10 of 10" in grown_prompt, grown_prompt)
    require("under bright stage lights" in grown_prompt, grown_prompt)
    seer_spec = dict(grown)
    seer_spec["code"] = "seer"
    seer_spec["stage"] = 10
    seer_prompt = character_visual.build_character_prompt(seer_spec)
    require("holding a lamp lit only by a glance" in seer_prompt, seer_prompt)
    require("주작" not in character_visual.build_character_prompt(first), "prompt leak")
    require("일간" not in first["visual_key"], first)

    other = character_visual.build_character_visual(sample(verdict="shingang", dominant="fire", water=0.1, fire=0.6))
    require(other["visual_key"] != first["visual_key"], (first["visual_key"], other["visual_key"]))
    require(other["visual_key"].startswith("brightener_"), other)

    # 10천간: day_master.code가 있으면 음양 구분 아키타입 (갑→pathfinder, 을→weaver)
    stem_sample = dict(sample())
    stem_sample["day_master_strength"] = {
        "verdict": "shinyak",
        "day_master": {"code": "gap", "hanja": "甲", "element": "wood"},
    }
    gap = character_visual.build_character_visual(stem_sample, "male")
    require(gap["code"] == "pathfinder", gap)
    require(gap["label_ko"] == "길을 여는 사람", gap)
    stem_sample["day_master_strength"] = {
        "verdict": "shinyak",
        "day_master": {"code": "eul", "hanja": "乙", "element": "wood"},
    }
    eul = character_visual.build_character_visual(stem_sample, "male")
    require(eul["code"] == "weaver", eul)
    require(eul["label_ko"] == "이어주는 사람", eul)
    require(eul["catalog_key"] == "weaver_male_01", eul["catalog_key"])
    require("실타래" in character_visual.STAGE_NAMES["weaver"][0], character_visual.STAGE_NAMES["weaver"])

    same = character_visual.build_character_visual(sample())
    require(same["visual_key"] == first["visual_key"], "same analysis must reuse key")

    # 성장 단계: 기록일수에 따라 1~10단계 (결정적, 생성 없음)
    require(character_visual.stage_for(0) == 1, character_visual.stage_for(0))
    require(character_visual.stage_for(7) == 2, character_visual.stage_for(7))
    require(character_visual.stage_for(27) == 4, character_visual.stage_for(27))
    require(character_visual.stage_for(28) == 5, character_visual.stage_for(28))
    require(character_visual.stage_for(63) == 10, character_visual.stage_for(63))
    require(character_visual.stage_for(999) == 10, character_visual.stage_for(999))
    grown = character_visual.build_character_visual(sample(), "male", recorded_days=63)
    require(grown["stage"] == 10, grown)
    require(grown["stage_name"] == "무대 위 빛", grown["stage_name"])
    require(grown["catalog_key"] == "brightener_male_10", grown["catalog_key"])
    require(first["catalog_key"] == "brightener_unknown_01", first["catalog_key"])

    # 카탈로그 우선: stage/{code}/{gender}/PNG가 있으면 정적 URL (생성 호출 없음)
    with tempfile.TemporaryDirectory() as tmp:
        cat_dir = Path(tmp) / "stage" / "brightener" / "male"
        cat_dir.mkdir(parents=True)
        import shutil

        shutil.copy2(character_visual._archetype_source(grown), cat_dir / "brightener_male_10.png")
        result = character_visual.generate_character_image(grown, public_dir=Path(tmp))
        require(result["status"] == "catalog", result)
        require(result["image_url"] == "/characters/stage/brightener/male/brightener_male_10.png", result["image_url"])
        require(result["stage_name"] == "무대 위 빛", result)

        strained = dict(grown)
        strained["condition_state"] = "strained"
        strained["state_catalog_key"] = "brightener_male_10_strained"
        shutil.copy2(character_visual._archetype_source(grown), cat_dir / "brightener_male_10_strained.png")
        state_result = character_visual.generate_character_image(strained, public_dir=Path(tmp))
        require(state_result["image_url"].endswith("brightener_male_10_strained.png"), state_result)

    with tempfile.TemporaryDirectory() as tmp:
        public = Path(tmp)
        generated = character_visual.generate_character_image(first, public_dir=public)
        require(generated["status"] == "fallback", generated)
        dest = public / f"{first['visual_key']}.png"
        require(dest.exists(), dest)
        # A fallback copy must not count as a real render: it re-queues a fresh
        # generation instead of silently becoming "exists" forever.
        again = character_visual.generate_character_image(first, public_dir=public)
        require(again["status"] == "queued", again)
        # GIF is synthesized from the fallback PNG (tests: public_dir temp)
        gif_path = public / f"{first['visual_key']}.gif"
        require(gif_path.exists() and gif_path.stat().st_size > 0, "gif synthesized")
        gif_url = again.get("image_gif_url") or generated.get("image_gif_url")
        require(gif_url and gif_url.endswith(".gif"), gif_url)

    # GIF: real archetype PNG → 8-frame looped GIF, transparency preserved
    import shutil

    from PIL import Image  # noqa: E402

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        png = out / "brightener.png"
        shutil.copy2(character_visual._archetype_source(first), png)
        gif = out / "brightener.gif"
        require(character_visual.build_character_gif(png, gif), "build gif")
        im = Image.open(gif)
        require(im.n_frames == 8, im.n_frames)
        require(im.info.get("loop") == 0, im.info.get("loop"))

    print("character-visual: PASS")


if __name__ == "__main__":
    run()
