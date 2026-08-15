"""Profile character visual: everyday-language spec + per-result image key.

The saju engine output differs per birth. User-facing copy stays everyday
language. Images are keyed by that public visual spec, not by raw myeongni.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
from pathlib import Path

from character_state import condition_prompt

# 오행 레벨 성향 (레거시/폴백용)
CHARACTER_VOICE = {
    "wood": {"code": "pathfinder", "label_ko": "길을 여는 사람", "tone": "호기심 많고 시작하는"},
    "fire": {"code": "brightener", "label_ko": "분위기를 밝히는 사람", "tone": "명랑하고 드러내는"},
    "earth": {"code": "steadier", "label_ko": "자리를 지키는 사람", "tone": "차분하고 돌보는"},
    "metal": {"code": "decider", "label_ko": "기준을 세우는 사람", "tone": "또렷하고 정리하는"},
    "water": {"code": "observer", "label_ko": "흐름을 읽는 사람", "tone": "차분하고 깊이 보는"},
}

# 천간 10개 → 아키타입 (일간 = 나 자신이므로 천간이 정확한 기준)
# 양(陽) 5개는 CHARACTER_VOICE와 호환, 음(陰) 5개가 추가됐다.
STEM_VOICE = {
    "gap": {"code": "pathfinder", "label_ko": "길을 여는 사람", "tone": "호기심 많고 시작하는"},
    "eul": {"code": "weaver", "label_ko": "이어주는 사람", "tone": "유연하게 조율하는"},
    "byeong": {"code": "brightener", "label_ko": "분위기를 밝히는 사람", "tone": "명랑하고 드러내는"},
    "jeong": {"code": "lighter", "label_ko": "온기를 나누는 사람", "tone": "섬세하게 비추는"},
    "mu": {"code": "steadier", "label_ko": "자리를 지키는 사람", "tone": "차분하고 돌보는"},
    "gi": {"code": "gardener", "label_ko": "가꾸는 사람", "tone": "꼼꼼하게 가꾸는"},
    "gyeong": {"code": "decider", "label_ko": "기준을 세우는 사람", "tone": "또렷하고 정리하는"},
    "sin": {"code": "polisher", "label_ko": "다듬는 사람", "tone": "섬세하게 다듬는"},
    "im": {"code": "observer", "label_ko": "흐름을 읽는 사람", "tone": "차분하고 깊이 보는"},
    "gye": {"code": "seer", "label_ko": "깊이 비추는 사람", "tone": "조용히 스며드는"},
}

PALETTE = {
    "wood": "sage green, leaf-tea, warm ivory",
    "fire": "terracotta, apricot, warm cream",
    "earth": "warm clay, oatmeal, soft brown",
    "metal": "muted gold, stone gray, warm white",
    "water": "mist sage, slate blue, paper ivory",
}

MOTIF = {
    "wood": "a tiny paper compass",
    "fire": "a small paper lantern",
    "earth": "a ceramic mug",
    "metal": "a slim closed notebook",
    "water": "a folded paper boat",
}

ENERGY = {
    "shingang": "open chest, brighter posture, slightly larger presence",
    "shinyak": "softer posture, quieter face, slightly smaller presence",
    "neutral": "balanced stance, calm even presence",
}

ACCENT = {
    "wood": "a faint leaf-tea scarf",
    "fire": "a warm apricot scarf",
    "earth": "an oatmeal knit cuff",
    "metal": "a muted-gold pin on the cardigan",
    "water": "a mist-sage collar",
}
PRESENTATION = {
    "male": "a Korean chibi man",
    "female": "a Korean chibi woman",
    "unknown": "a Korean chibi person with a soft unisex look",
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
    "hexagram",
    "dragon",
    "phoenix",
    "tiger",
    "turtle",
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PUBLIC_DIR = REPO_ROOT / "frontend" / "public" / "characters"
DEFAULT_IMAGEN = Path.home() / ".hermes" / "skills" / "codex-imagen" / "scripts" / "codex-imagen.mjs"
DEFAULT_CHROMA = Path.home() / ".codex" / "skills" / ".system" / "imagegen" / "scripts" / "remove_chroma_key.py"
_GENERATE_LOCK = threading.Lock()


def character_voice(element: str) -> dict:
    return CHARACTER_VOICE.get(element, CHARACTER_VOICE["earth"])


def _clamp_ratio(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.2
    return round(max(0.05, min(0.95, number)), 3)


def _bucket(value: float) -> str:
    if value >= 0.55:
        return "high"
    if value >= 0.25:
        return "mid"
    return "low"


def normalize_presentation(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in {"male", "man", "m", "남", "남성"}:
        return "male"
    if value in {"female", "woman", "f", "여", "여성"}:
        return "female"
    return "unknown"


# ── 성장 단계 (다크세이버식 10단계, 단 일상어) ──────────────────────────
# 기록일수 → 단계. 1단계가 첫 프로필, 10단계가 가장 성숙한 모습.
# 기록일수로만 결정되므로 생성 호출 없이 캐릭터가 '자란다'.
STAGE_DAYS = [0, 7, 14, 21, 28, 35, 42, 49, 56, 63]  # 1~10단계 임계값

# 아키타입별 단계 명칭 (일상어 — 게임 용어 아님)
STAGE_NAMES = {
    "pathfinder": ["새싹", "오솔길", "갈림길", "숲길", "첫 정상", "새 지도", "개척자", "등산로", "대륙의 길", "지평선 너머"],
    "weaver": ["실타래", "매듭", "다리", "그물", "오케스트라", "직물", "수놓은 천", "정원의 울타리", "연결의 중심", "하나로 이어진 길"],
    "brightener": ["불씨", "모닥불", "등불", "횃불", "벽난로", "아궁이", "화로", "등대", "태양 정원", "무대 위 빛"],
    "lighter": ["촛불", "별빛", "등잔", "가로등", "창가의 빛", "손전등", "달빛", "노을", "온기의 집", "작은 별의 하늘"],
    "steadier": ["씨앗", "화분", "정원", "텃밭", "농장", "단단한 벽", "성채", "고요한 호수", "오래된 참나무", "대지의 중심"],
    "gardener": ["흙 한 줌", "새싹 키우기", "화단", "이끼 낀 돌", "분재", "온실", "허브 정원", "숲의 관리인", "수백 년 정원", "지구의 정원사"],
    "decider": ["연필", "자", "가위", "도면", "설계도", "기준선", "청사진", "나침반", "정밀 시계", "방향타"],
    "polisher": ["숫돌", "사포", "광택제", "조각칼", "보석 다듬기", "유리 면", "거울 연마", "정밀 조정", "완성된 악기", "빛나는 보석"],
    "observer": ["물방울", "시냇물", "강물", "호수", "깊은 바다", "수면 아래", "달빛", "별빛", "은하수", "밤하늘 전체"],
    "seer": ["고요한 연못", "안개", "이슬", "새벽의 강", "깊은 샘", "잠든 호수", "달의 뒷면", "별들의 지도", "빛 없는 밤", "눈빛만으로 비추는 등"],
}

STAGE_MOTIF = {
    "pathfinder": "a growing trail marker",
    "weaver": "threads weaving together into a larger pattern",
    "brightener": "a small flame that grows brighter",
    "lighter": "a small candle glow that becomes a warm room",
    "steadier": "a growing tree with deeper roots",
    "gardener": "a seedling that becomes a tended garden",
    "decider": "a compass that becomes more precise",
    "polisher": "a rough stone that becomes a polished gem",
    "observer": "a drop of water that becomes a deep sea",
    "seer": "a still pond that reflects the whole sky",
}


def stage_for(recorded_days: int) -> int:
    """기록일수 → 1~10 단계 (결정적, 생성 없음)."""
    for stage, threshold in enumerate(STAGE_DAYS, start=1):
        if recorded_days < threshold:
            return max(1, stage - 1)
    return len(STAGE_DAYS)


def stage_name(code: str, stage: int) -> str:
    names = STAGE_NAMES.get(code, STAGE_NAMES["steadier"])
    return names[max(0, min(len(names) - 1, stage - 1))]


def catalog_key(code: str, presentation: str, stage: int) -> str:
    """프리렌더 카탈로그 키: {code}_{gender}_{stage} → 정적 파일."""
    return f"{code}_{presentation}_{stage:02d}"


def state_catalog_key(code: str, presentation: str, stage: int, condition_state: str) -> str:
    return f"{catalog_key(code, presentation, stage)}_{condition_state}"


def build_character_visual(
    analysis: dict,
    gender: str | None = None,
    recorded_days: int = 0,
    condition_state: str = "steady",
) -> dict:
    """Everyday-language visual spec derived from engine analysis.

    Internal keys stay English. Public prompt/label never include myeongni terms.
    성장 단계(stage)는 기록일수에서 결정적으로 나온다.
    """
    day = (analysis.get("day_master_strength") or {}).get("day_master") or {}
    strength = analysis.get("day_master_strength") or {}
    balance = analysis.get("element_balance") or {}
    growth = analysis.get("growth_direction") or {}
    element = day.get("element") or "earth"
    # 일간 천간 코드(갑/을/병/…)가 있으면 10천간 아키타입, 없으면 오행 폴백
    stem_code = day.get("code") or ""
    voice = STEM_VOICE.get(stem_code) or character_voice(element)
    dominant = balance.get("dominant") or element
    deficient = growth.get("deficient_element") or balance.get("deficient") or "earth"
    verdict = strength.get("verdict") or "neutral"
    if verdict not in ENERGY:
        verdict = "neutral"
    ratio = balance.get("ratio") or {}
    dominant_level = _bucket(_clamp_ratio(ratio.get(dominant, 0.4)))
    presentation = normalize_presentation(gender)
    visual_key = "_".join((voice["code"], verdict, dominant, deficient, dominant_level, presentation))
    stage = stage_for(recorded_days)
    spec = {
        "visual_key": visual_key,
        "catalog_key": catalog_key(voice["code"], presentation, stage),
        "state_catalog_key": state_catalog_key(
            voice["code"], presentation, stage, condition_state
        ),
        "stage": stage,
        "stage_name": stage_name(voice["code"], stage),
        "condition_state": condition_state if condition_state in {"rising", "steady", "strained", "recovering"} else "steady",
        "condition_prompt": condition_prompt(condition_state),
        "code": voice["code"],
        "label_ko": voice["label_ko"],
        "tone": voice["tone"],
        "element": element,
        "energy": verdict,
        "dominant": dominant,
        "deficient": deficient,
        "dominant_level": dominant_level,
        "presentation": presentation,
        "palette": PALETTE[element],
        "motif": MOTIF[element],
        "accent": ACCENT.get(deficient, ACCENT["earth"]),
        "posture": ENERGY[verdict],
    }
    leaked = [term for term in FORBIDDEN if term in json.dumps(spec, ensure_ascii=False)]
    if leaked:
        raise ValueError(f"character visual leaked forbidden terms: {leaked}")
    return spec


def character_image_url(visual_key: str) -> str:
    return f"/characters/{visual_key}.png"


def character_gif_url(visual_key: str) -> str:
    return f"/characters/{visual_key}.gif"


def _catalog_key_segments(catalog_key: str) -> tuple[str, str]:
    """catalog_key({code}_{gender}_{stage}[_{state}]) → (code, gender)."""
    parts = catalog_key.split("_")
    code = parts[0] if parts else "steadier"
    gender = parts[1] if len(parts) > 1 else "unknown"
    return code, gender


def catalog_image_path(catalog_key: str, public_dir: Path | None = None) -> Path:
    """프리렌더 카탈로그 이미지 경로 (부하 0 정적 서빙).

    stage/{code}/{gender}/{catalog_key}.png
    """
    root = public_dir or Path(os.environ.get("NABOM_CHARACTER_DIR", DEFAULT_PUBLIC_DIR))
    code, gender = _catalog_key_segments(catalog_key)
    return root / "stage" / code / gender / f"{catalog_key}.png"


def catalog_gif_path(catalog_key: str, public_dir: Path | None = None) -> Path:
    root = public_dir or Path(os.environ.get("NABOM_CHARACTER_DIR", DEFAULT_PUBLIC_DIR))
    code, gender = _catalog_key_segments(catalog_key)
    return root / "stage" / code / gender / f"{catalog_key}.gif"


def catalog_image_url(catalog_key: str) -> str:
    code, gender = _catalog_key_segments(catalog_key)
    return f"/characters/stage/{code}/{gender}/{catalog_key}.png"


def catalog_gif_url(catalog_key: str) -> str:
    code, gender = _catalog_key_segments(catalog_key)
    return f"/characters/stage/{code}/{gender}/{catalog_key}.gif"


def character_image_path(visual_key: str, public_dir: Path | None = None) -> Path:
    root = public_dir or Path(os.environ.get("NABOM_CHARACTER_DIR", DEFAULT_PUBLIC_DIR))
    return root / f"{visual_key}.png"


def character_gif_path(visual_key: str, public_dir: Path | None = None) -> Path:
    root = public_dir or Path(os.environ.get("NABOM_CHARACTER_DIR", DEFAULT_PUBLIC_DIR))
    return root / f"{visual_key}.gif"


def build_character_gif(png_path: Path, gif_path: Path) -> bool:
    """단일 PNG에서 스프라이트 프레임을 파생해 루프 GIF를 합성한다.

    캐릭터 bbox를 크롭한 뒤, 프레임마다 bob(위아래)·호흡(스케일)·미세 기울임을
    입힌다. 투명 배경은 유지된다. 생성 실패 시 False (PNG만 사용).
    """
    try:
        from PIL import Image
    except ImportError:
        return False
    try:
        src = Image.open(png_path)
        src.load()
    except (OSError, ValueError):
        return False
    if src.mode != "RGBA":
        src = src.convert("RGBA")

    # 투명 픽셀 제외 bbox → 캐릭터만 크롭
    bbox = src.getbbox()
    if not bbox:
        return False
    cropped = src.crop(bbox)
    w, h = cropped.size
    # 프레임 크기: bob + 회전 여유 추가 (가로 세로 12% 여백)
    pad_x = int(w * 0.12)
    pad_y = int(h * 0.16)
    frame_w = w + pad_x * 2
    frame_h = h + pad_y * 2

    frames: list[Image.Image] = []
    durations: list[int] = []
    steps = 8
    for i in range(steps):
        phase = i / steps
        # bob: sin 곡선으로 ±5px
        bob = int(round(5 * __import__("math").sin(phase * 2 * __import__("math").pi)))
        # 호흡 스케일 0.98 ~ 1.02
        scale = 1.0 + 0.02 * __import__("math").sin(phase * 2 * __import__("math").pi)
        # 미세 기울임 ±1.5도
        tilt = 1.5 * __import__("math").sin((phase + 0.25) * 2 * __import__("math").pi)

        scaled_w = max(1, int(w * scale))
        scaled_h = max(1, int(h * scale))
        resized = cropped.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

        frame = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        rot = resized.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=False)
        # 중앙 정렬 + bob
        x = (frame_w - scaled_w) // 2
        y = (frame_h - scaled_h) // 2 + pad_y // 2 + bob
        frame.paste(rot, (x, y), rot)
        frames.append(frame)
        durations.append(70)  # 8프레임 x 70ms ≈ 0.56s 루프

    # GIF로 저장 (P-mode + 투명 유지)
    try:
        palette_frame = frames[0].convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        gif_path.parent.mkdir(parents=True, exist_ok=True)
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            disposal=2,
            transparency=0,
            optimize=True,
        )
    except (OSError, ValueError):
        try:
            gif_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    return gif_path.exists() and gif_path.stat().st_size > 0


# 아키타입×단계 심볼 (개별 생성 폴백 경로용 — 프리렌더 TSV와 동일)
STAGE_SYMBOLS_EN: dict[tuple[str, int], str] = {
    ("pathfinder", 1): "holding a tiny potted sprout",
    ("pathfinder", 2): "a small stone at the entrance of a path",
    ("pathfinder", 3): "a small branch chosen at a fork in the road",
    ("pathfinder", 4): "a small lantern lighting the forest trail",
    ("pathfinder", 5): "a tiny flag planted at the first summit",
    ("pathfinder", 6): "a bag with a new map",
    ("pathfinder", 7): "a compass and a worn backpack",
    ("pathfinder", 8): "a trail signpost",
    ("pathfinder", 9): "a large rolled map of the land",
    ("pathfinder", 10): "a flag pointing to the horizon plus a compass",
    ("weaver", 1): "holding a single ball of thread",
    ("weaver", 2): "a knot joining two colors of thread",
    ("weaver", 3): "a small bridge model",
    ("weaver", 4): "a knitted handkerchief",
    ("weaver", 5): "a small net connecting people",
    ("weaver", 6): "an orchestra baton",
    ("weaver", 7): "a piece of embroidered cloth",
    ("weaver", 8): "a painting of a bridge connecting the whole town",
    ("weaver", 9): "a large woven fabric of many colors",
    ("weaver", 10): "a finished tapestry joining everyone together",
    ("brightener", 1): "holding a small lamp with a tiny flame",
    ("brightener", 2): "warming hands by a campfire",
    ("brightener", 3): "holding a lantern",
    ("brightener", 4): "raising a torch high",
    ("brightener", 5): "smiling in front of a fireplace",
    ("brightener", 6): "lighting a stove fire",
    ("brightener", 7): "holding a brazier",
    ("brightener", 8): "glowing from the top of a lighthouse",
    ("brightener", 9): "in the middle of a sun garden",
    ("brightener", 10): "under bright stage lights",
    ("lighter", 1): "holding a single candle",
    ("lighter", 2): "by a window lit with starlight",
    ("lighter", 3): "pouring oil into a lamp",
    ("lighter", 4): "smiling under a street lamp",
    ("lighter", 5): "sharing the light from the window with someone",
    ("lighter", 6): "lending a flashlight",
    ("lighter", 7): "offering a teacup in moonlight",
    ("lighter", 8): "turning on a lamp in a room at sunset",
    ("lighter", 9): "in front of a warm house door",
    ("lighter", 10): "lighting many lamps like small stars",
    ("steadier", 1): "holding a single seed",
    ("steadier", 2): "watering a potted plant",
    ("steadier", 3): "tending a small garden",
    ("steadier", 4): "working a vegetable patch",
    ("steadier", 5): "opening the gate of a farm",
    ("steadier", 6): "laying solid bricks",
    ("steadier", 7): "guarding the gate of a fortress",
    ("steadier", 8): "sitting by a still lake",
    ("steadier", 9): "resting under an old oak tree",
    ("steadier", 10): "embracing the center of the earth",
    ("gardener", 1): "holding a handful of soil",
    ("gardener", 2): "watering a sprout",
    ("gardener", 3): "arranging flower beds",
    ("gardener", 4): "caressing a mossy stone",
    ("gardener", 5): "pruning a bonsai",
    ("gardener", 6): "looking into a greenhouse",
    ("gardener", 7): "harvesting herbs",
    ("gardener", 8): "as the keeper of a forest",
    ("gardener", 9): "walking through a centuries-old garden",
    ("gardener", 10): "tending the earth like a garden",
    ("decider", 1): "holding a single pencil",
    ("decider", 2): "drawing a straight line with a ruler",
    ("decider", 3): "cutting with scissors",
    ("decider", 4): "drawing a blueprint",
    ("decider", 5): "unfolding a design plan",
    ("decider", 6): "setting a baseline",
    ("decider", 7): "completing a master plan",
    ("decider", 8): "holding a compass",
    ("decider", 9): "adjusting a precision clock",
    ("decider", 10): "gripping a steering helm",
    ("polisher", 1): "holding a whetstone",
    ("polisher", 2): "rubbing with sandpaper",
    ("polisher", 3): "applying polish",
    ("polisher", 4): "carving with a chisel",
    ("polisher", 5): "refining a gem",
    ("polisher", 6): "polishing a glass surface",
    ("polisher", 7): "cleaning a mirror",
    ("polisher", 8): "adjusting a precision instrument",
    ("polisher", 9): "tuning the strings of a finished instrument",
    ("polisher", 10): "offering a shining gem",
    ("observer", 1): "holding a single water drop",
    ("observer", 2): "dipping a hand into a stream",
    ("observer", 3): "watching the river",
    ("observer", 4): "skipping a stone on a lake",
    ("observer", 5): "swimming in the deep sea",
    ("observer", 6): "gazing below the surface",
    ("observer", 7): "sitting in moonlight",
    ("observer", 8): "counting stars",
    ("observer", 9): "gazing at the milky way",
    ("observer", 10): "embracing the whole night sky",
    ("seer", 1): "beside a still pond",
    ("seer", 2): "in a misty morning",
    ("seer", 3): "holding a dewdrop",
    ("seer", 4): "at a riverbank at dawn",
    ("seer", 5): "looking into a deep spring",
    ("seer", 6): "by a sleeping lakeshore",
    ("seer", 7): "drawing the far side of the moon",
    ("seer", 8): "unfolding a star chart",
    ("seer", 9): "reading a night without light",
    ("seer", 10): "holding a lamp lit only by a glance",
}


def stage_symbol(code: str, stage: int) -> str:
    return STAGE_SYMBOLS_EN.get((code, stage), "a small everyday item that reflects this stage")


def build_character_prompt(spec: dict) -> str:
    stage = int(spec.get("stage") or 1)
    code = spec.get("code") or "steadier"
    symbol = stage_symbol(code, stage)
    condition = spec.get("condition_prompt") or condition_prompt(spec.get("condition_state", "steady"))
    return (
        "Use case: stylized-concept\n"
        "Asset type: NABOM profile character sprite\n"
        f"Primary request: A single cute two-head-tall {PRESENTATION[spec.get('presentation', 'unknown')]}, tiny body, oversized round head. "
        f"Everyday human who feels {spec['tone']}. At this growth stage (stage {stage} of 10) the character is {symbol}. "
        f"Current condition visual direction: {condition}. {spec['accent']}.\n"
        "Scene/backdrop: Perfectly flat solid #00ff00 chroma-key background. No floor, shadow, gradient, reflection, texture, or scenery.\n"
        f"Subject: One person only. {spec['posture']}. No extra characters.\n"
        "Style/medium: Cute Korean illustration, paper-cut warmth, clean edges, 2-head-tall chibi.\n"
        "Composition/framing: Centered full-body, generous padding, square 1:1, subject fully separated from the background.\n"
        "Lighting/mood: Soft studio light, no cast shadow.\n"
        f"Color palette: {spec['palette']}. Do not use #00ff00 anywhere on the subject.\n"
        "Constraints: no text, no watermark, no animals, no mythical beasts, no armor, no weapons.\n"
        "Avoid: photorealism, 3D render look, busy background, Chinese characters, fortune-telling symbols.\n"
    )


def _archetype_source(spec: dict) -> Path:
    return DEFAULT_PUBLIC_DIR / f"{spec['code']}.png"


def _copy_archetype_fallback(spec: dict, dest: Path) -> bool:
    """Seed the keyed file from the real archetype asset.

    The archetype always lives in DEFAULT_PUBLIC_DIR even when NABOM_CHARACTER_DIR
    redirects writes (tests), so tests never pollute the shipped assets.
    """
    source = _archetype_source(spec)
    if not source.exists() or source == dest:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return True


def _is_fallback_copy(spec: dict, dest: Path) -> bool:
    """True when the keyed file is still a byte-identical archetype copy."""
    source = _archetype_source(spec)
    if not source.exists() or source == dest:
        return False
    try:
        same_size = dest.stat().st_size == source.stat().st_size
        return same_size and dest.read_bytes() == source.read_bytes()
    except OSError:
        return False


def _render_character_image(spec: dict, dest: Path) -> str:
    imagen = Path(os.environ.get("NABOM_IMAGEN", DEFAULT_IMAGEN))
    chroma = Path(os.environ.get("NABOM_CHROMA_KEY", DEFAULT_CHROMA))
    if not imagen.exists():
        return "missing"
    raw = dest.with_suffix(".raw.png")
    prompt_path = dest.with_suffix(".prompt.txt")
    prompt_path.write_text(build_character_prompt(spec), encoding="utf-8")
    subprocess.run(
        [
            "node",
            str(imagen),
            "--timeout",
            "600",
            "--retries",
            "1",
            "--quiet",
            "--output",
            str(raw),
            "--prompt-file",
            str(prompt_path),
        ],
        check=True,
        timeout=700,
    )
    if chroma.exists() and raw.exists():
        subprocess.run(
            [
                "python3",
                str(chroma),
                "--input",
                str(raw),
                "--out",
                str(dest),
                "--key-color",
                "#00ff00",
                "--auto-key",
                "corners",
                "--soft-matte",
                "--despill",
                "--force",
            ],
            check=True,
            timeout=60,
        )
        raw.unlink(missing_ok=True)
    elif raw.exists():
        raw.replace(dest)
    if dest.exists() and dest.stat().st_size > 0:
        return "generated"
    return "missing"


def _schedule_background_render(spec: dict, dest: Path) -> None:
    marker = dest.with_suffix(".pending")
    if marker.exists():
        return
    marker.write_text("pending\n", encoding="utf-8")

    def _run() -> None:
        try:
            _render_character_image(spec, dest)
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            marker.unlink(missing_ok=True)

    threading.Thread(target=_run, name=f"nabom-character-{spec['visual_key']}", daemon=True).start()


def _ensure_gif(spec: dict, png_path: Path) -> str:
    """PNG가 확정되면 GIF를 생성한다. 이미 있으면 스킵."""
    gif = character_gif_path(spec["visual_key"], png_path.parent)
    if gif.exists() and gif.stat().st_size > 0:
        return character_gif_url(spec["visual_key"])
    if build_character_gif(png_path, gif):
        return character_gif_url(spec["visual_key"])
    return character_image_url(spec["visual_key"])


def _catalog_result(spec: dict, public_dir: Path | None = None) -> dict | None:
    """카탈로그 PNG가 있으면 정적 URL을 반환한다 (부하 0). 없으면 None."""
    state_key = spec.get("state_catalog_key")
    state_png = catalog_image_path(state_key, public_dir) if state_key else None
    use_state = bool(state_png and state_png.exists() and state_png.stat().st_size > 0)
    selected_key = state_key if use_state else spec["catalog_key"]
    png = state_png if use_state else catalog_image_path(spec["catalog_key"], public_dir)
    if not png.exists() or png.stat().st_size == 0:
        return None
    gif = catalog_gif_path(selected_key, public_dir)
    if not gif.exists() or gif.stat().st_size == 0:
        build_character_gif(png, gif)
    return {
        "status": "catalog",
        "path": str(png),
        "image_url": catalog_image_url(selected_key),
        "image_gif_url": catalog_gif_url(selected_key),
        "catalog_key": selected_key,
        "base_catalog_key": spec["catalog_key"],
        "condition_state": spec.get("condition_state", "steady"),
        "stage": spec["stage"],
        "stage_name": spec["stage_name"],
    }


def generate_character_image(spec: dict, public_dir: Path | None = None) -> dict:
    """캐릭터 자산 해석: 카탈로그 우선, 없으면 개별 생성 폴백.

    - 카탈로그(프리렌더 stage/{code}_{gender}_{stage}) PNG가 있으면 정적 URL만
      반환 — 유저가 늘어도 생성 호출이 없다.
    - 없으면 기존 visual_key 개별 생성 경로로 폴백 (레거시/아직 프리렌더 전).
    """
    catalog = _catalog_result(spec, public_dir)
    if catalog is not None:
        return catalog

    dest = character_image_path(spec["visual_key"], public_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image_url = character_image_url(spec["visual_key"])

    def _with_gif(result: dict) -> dict:
        gif_url = _ensure_gif(spec, dest)
        result["image_gif_url"] = gif_url
        result["stage"] = spec["stage"]
        result["stage_name"] = spec["stage_name"]
        result["catalog_key"] = spec["catalog_key"]
        result["state_catalog_key"] = spec.get("state_catalog_key")
        result["condition_state"] = spec.get("condition_state", "steady")
        return result

    with _GENERATE_LOCK:
        if dest.exists() and dest.stat().st_size > 0:
            if not _is_fallback_copy(spec, dest):
                return _with_gif({"status": "exists", "path": str(dest), "image_url": image_url})
            # Still a fallback copy: a previous background render never landed.
            # Schedule again so a fresh image eventually replaces it.
            enabled = os.environ.get("NABOM_GENERATE_CHARACTERS", "1") != "0"
            if enabled:
                _schedule_background_render(spec, dest)
            return _with_gif({"status": "queued", "path": str(dest), "image_url": image_url})

        enabled = os.environ.get("NABOM_GENERATE_CHARACTERS", "1") != "0"
        fallback = _copy_archetype_fallback(spec, dest)
        if enabled:
            _schedule_background_render(spec, dest)
        if fallback:
            return _with_gif({"status": "queued" if enabled else "fallback", "path": str(dest), "image_url": image_url})
        return {
            "status": "queued" if enabled else "missing",
            "path": str(dest),
            "image_url": image_url if dest.exists() else character_image_url(spec["code"]),
        }


def visual_fingerprint(spec: dict) -> str:
    payload = json.dumps(spec, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
