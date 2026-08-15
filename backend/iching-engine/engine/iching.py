"""Deterministic hexagram calculations using the canonical dataset."""

from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).with_name("data") / "dataset.json"
KOREAN_DATA_PATH = Path(__file__).with_name("data") / "korean_translations.json"
THEME_DATA_PATH = Path(__file__).with_name("data") / "theme_interpretations.json"
CAST_VALUES = (6, 7, 8, 9)
SOURCE_URLS = {
    "classical_text": "https://zh.wikisource.org/wiki/周易",
    "korean_translation": "https://ko.wikisource.org/wiki/역경",
}


def load_dataset(path: Path = DATA_PATH) -> dict:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    _merge_korean(dataset)
    return dataset


def _merge_korean(dataset: dict, path: Path = KOREAN_DATA_PATH) -> None:
    """ko.wikisource 한국어 번역을 추가(결손 시 조용히 스킵 — 핵심 데이터는 원문)."""
    if not path.exists():
        return
    korean = json.loads(path.read_text(encoding="utf-8"))
    dataset["korean"] = {
        "schema_version": korean.get("schema_version", 1),
        "quality_policy": korean.get("quality_policy", "machine_rough_medium_original_required"),
        "hexagrams": korean.get("hexagrams", {}),
    }
    _merge_themes(dataset)


def _merge_themes(dataset: dict, path: Path = THEME_DATA_PATH) -> None:
    """주제별 해석(참조 레이어) 추가. 결손 시 스킵."""
    if not path.exists():
        return
    themes = json.loads(path.read_text(encoding="utf-8"))
    dataset["themes"] = {
        "schema_version": themes.get("schema_version", 1),
        "quality_policy": themes.get("quality_policy", "reference_interpretation_layer"),
        "topics": themes.get("topics", {}),
        "hexagram_topics": themes.get("hexagram_topics", {}),
    }


def get_themes(hexagram_id: int, dataset: dict | None = None) -> list[dict]:
    dataset = load_dataset() if dataset is None else dataset
    return dataset.get("themes", {}).get("hexagram_topics", {}).get(str(hexagram_id), [])


def get_korean(hexagram_id: int, line_label: str | None = None, dataset: dict | None = None) -> dict | str | None:
    """한국어 번역 조회. line_label 없으면 괘사 번역 반환, 있으면 해당 효사 번역."""
    dataset = load_dataset() if dataset is None else dataset
    entry = dataset.get("korean", {}).get("hexagrams", {}).get(str(hexagram_id))
    if not entry:
        return None
    if line_label is None:
        return {"hexagram_id": hexagram_id, "judgment_ko": entry.get("judgment_ko", ""), "quality": entry.get("quality")}
    return entry.get("lines_ko", {}).get(line_label)


def get_wing(wing_id: str, chapter_id: str | None = None, dataset: dict | None = None) -> list[dict]:
    """Return local Ten Wings records, optionally narrowed to one chapter."""
    dataset = load_dataset() if dataset is None else dataset
    validate_dataset(dataset)
    if wing_id in {
        "tuan", "tuan_upper", "tuan_lower",
        "xiang", "xiang_upper", "xiang_lower", "xiang_great", "xiang_small",
    }:
        if wing_id == "xiang_small":
            return [
                {
                    "wing_id": "xiang_small",
                    "wing_name": "小象",
                    "chapter_id": f"{row['hexagram_id']}:{row['line_position']}",
                    "chapter_title": row["line_label"],
                    "text": row["small_image_text"],
                    "translation": row["small_image_translation"],
                    "source_note": next(
                        hexagram["source_note"]
                        for hexagram in dataset["hexagrams"]
                        if hexagram["hexagram_id"] == row["hexagram_id"]
                    ),
                }
                for row in dataset["lines"]
                if chapter_id is None
                or f"{row['hexagram_id']}:{row['line_position']}" == chapter_id
            ]
        rows = []
        for hexagram in dataset["hexagrams"]:
            if wing_id.startswith("tuan"):
                rows.append({
                    "wing_id": wing_id,
                    "wing_name": "彖傳",
                    "chapter_id": str(hexagram["hexagram_id"]),
                    "chapter_title": hexagram["name_zh"],
                    "text": hexagram["tuan_text"],
                    "translation": hexagram["tuan_translation"],
                    "source_note": hexagram["source_note"],
                })
            else:
                rows.append({
                    "wing_id": wing_id,
                    "wing_name": "大象",
                    "chapter_id": str(hexagram["hexagram_id"]),
                    "chapter_title": hexagram["name_zh"],
                    "text": hexagram["great_image_text"],
                    "translation": hexagram["great_image_translation"],
                    "source_note": hexagram["source_note"],
                })
        return [row for row in rows if chapter_id is None or row["chapter_id"] == chapter_id]
    rows = [row for row in dataset["wings"] if row["wing_id"] == wing_id]
    if chapter_id is not None:
        rows = [row for row in rows if row["chapter_id"] == chapter_id]
    return rows


def get_translation(
    hexagram_id: int, translation_id: str = "legge", dataset: dict | None = None
) -> dict:
    """Return a translation record without mixing it with classical text."""
    dataset = load_dataset() if dataset is None else dataset
    validate_dataset(dataset)
    rows = dataset["translations"].get(translation_id, [])
    for row in rows:
        if row["hexagram_id"] == hexagram_id:
            return row
    raise KeyError(f"Unknown translation or hexagram: {translation_id}/{hexagram_id}")


def validate_dataset(dataset: dict) -> None:
    """Reject malformed canonical data before it reaches calculation code."""
    required = {
        "trigrams",
        "hexagrams",
        "lines",
        "special_lines",
        "relationships",
        "theme_links",
        "wings",
        "sources",
        "translations",
        "wing_catalog",
    }
    missing = required - dataset.keys()
    if missing:
        raise ValueError(f"Dataset is missing sections: {sorted(missing)}")
    hexagrams = dataset["hexagrams"]
    if len(hexagrams) != 64 or {row["hexagram_id"] for row in hexagrams} != set(range(1, 65)):
        raise ValueError("Dataset must contain hexagrams 1 through 64 exactly once.")
    if len({row["binary_bottom_to_top"] for row in hexagrams}) != 64:
        raise ValueError("Hexagram binary representations must be unique.")
    keys = {(row["hexagram_id"], row["line_position"]) for row in dataset["lines"]}
    expected = {(hexagram_id, position) for hexagram_id in range(1, 65) for position in range(1, 7)}
    if keys != expected or len(dataset["lines"]) != 384:
        raise ValueError("Dataset must contain six regular lines for every hexagram.")
    if {row["line_label"] for row in dataset["special_lines"]} != {"用九", "用六"}:
        raise ValueError("Dataset must contain 用九 and 用六 special lines.")
    if len(dataset["trigrams"]) != 8 or len(dataset["relationships"]) != 64:
        raise ValueError("Dataset must contain eight trigrams and 64 relationships.")
    if len(dataset["wings"]) < 30 or len(dataset["sources"]) < 4:
        raise ValueError("Dataset must contain the local Ten Wings corpus and source registry.")
    if {row["wing_id"] for row in dataset["wings"]} != {
        "01", "02", "03", "04", "05", "06", "07"
    }:
        raise ValueError("Dataset must contain all seven local Ten Wings source files.")
    if len(dataset["wing_catalog"]) != 10:
        raise ValueError("Dataset must contain the canonical ten-component Wing catalog.")
    legge = dataset["translations"].get("legge", [])
    if len(legge) != 64 or {row["hexagram_id"] for row in legge} != set(range(1, 65)):
        raise ValueError("Dataset must contain all 64 Legge English translations.")
    if any(
        not row.get("judgment_text", "").strip()
        or len(row.get("line_texts", {})) != 6
        or any(not value.strip() for value in row["line_texts"].values())
        for row in legge
    ):
        raise ValueError("Every Legge translation must contain one judgment and six line texts.")
    if any(
        not row.get("judgment_text")
        or not row.get("tuan_text")
        or not row.get("great_image_text")
        or not row.get("external_legge_url")
        for row in hexagrams
    ):
        raise ValueError("Every hexagram must have core text and a cross-reference URL.")
    trigram_bits = {
        row["trigram_id"]: row["binary_bottom_to_top"] for row in dataset["trigrams"]
    }
    for row in hexagrams:
        expected_bits = (
            trigram_bits[row["lower_trigram_id"]]
            + trigram_bits[row["upper_trigram_id"]]
        )
        if row["binary_bottom_to_top"] != expected_bits:
            raise ValueError(
                f"Hexagram {row['hexagram_id']} does not match its trigram composition."
            )
    hexagram_by_id = {row["hexagram_id"]: row for row in hexagrams}
    for row in dataset["lines"]:
        expected_yin_yang = (
            "yang"
            if hexagram_by_id[row["hexagram_id"]]["binary_bottom_to_top"][
                row["line_position"] - 1
            ]
            == "1"
            else "yin"
        )
        if row["yin_yang"] != expected_yin_yang:
            raise ValueError(
                f"Line polarity mismatch: {row['hexagram_id']}/{row['line_position']}"
            )


def _validate_bits(bits: list[int]) -> None:
    if len(bits) != 6 or any(bit not in (0, 1) for bit in bits):
        raise ValueError("A hexagram needs six binary lines, bottom to top.")


def resolve_casts(casts: list[int], dataset: dict | None = None) -> dict:
    """Resolve six coin/yarrow values: 6, 7, 8, or 9, bottom to top."""
    if (
        len(casts) != 6
        or any(type(cast) is not int or cast not in CAST_VALUES for cast in casts)
    ):
        raise ValueError("casts must contain six values, each one of 6, 7, 8, or 9.")
    dataset = load_dataset() if dataset is None else dataset
    validate_dataset(dataset)
    primary_bits = [1 if cast in (7, 9) else 0 for cast in casts]
    changing_lines = [position for position, cast in enumerate(casts, start=1) if cast in (6, 9)]
    resulting_bits = [
        1 - bit if cast in (6, 9) else bit
        for bit, cast in zip(primary_bits, casts)
    ]
    hexagrams = {row["hexagram_id"]: row for row in dataset["hexagrams"]}
    by_bits = {row["binary_bottom_to_top"]: row for row in dataset["hexagrams"]}
    line_index = {
        (row["hexagram_id"], row["line_position"]): row for row in dataset["lines"]
    }
    translation_index = {
        row["hexagram_id"]: row for row in dataset["translations"]["legge"]
    }
    relationship_index = {
        row["hexagram_id"]: row for row in dataset["relationships"]
    }
    theme_index: dict[int, list[dict]] = {}
    for row in dataset.get("theme_links", []):
        theme_index.setdefault(row["hexagram_id"], []).append(row)
    _validate_bits(primary_bits)
    _validate_bits(resulting_bits)
    primary_id = by_bits["".join(map(str, primary_bits))]["hexagram_id"]
    resulting_id = by_bits["".join(map(str, resulting_bits))]["hexagram_id"]
    special_line = None
    if len(changing_lines) == 6 and primary_id in (1, 2):
        special_label = "用九" if primary_id == 1 else "用六"
        special_line = next(
            row for row in dataset["special_lines"] if row["line_label"] == special_label
        )
    korean_map = dataset.get("korean", {}).get("hexagrams", {})
    korean_primary = korean_map.get(str(primary_id), {})
    changing_lines_ko = []
    for line in [line_index[(primary_id, position)] for position in changing_lines]:
        enriched = dict(line)
        enriched["korean_text"] = korean_primary.get("lines_ko", {}).get(line["line_label"], "")
        changing_lines_ko.append(enriched)
    return {
        "casts": casts,
        "primary_hexagram": hexagrams[primary_id],
        "changing_lines": changing_lines_ko,
        "special_line": special_line,
        "resulting_hexagram": hexagrams[resulting_id],
        "korean_judgment_ko": korean_primary.get("judgment_ko", ""),
        "korean_quality": korean_primary.get("quality", ""),
        "themes": dataset.get("themes", {}).get("hexagram_topics", {}).get(str(primary_id), []),
        "relationships": relationship_index[primary_id],
        "theme_links": theme_index.get(primary_id, []),
        "translations": {
            "legge": translation_index[primary_id],
            "legge_resulting": translation_index[resulting_id],
        },
        "interpretation": interpretation_focus(
            primary_id, resulting_id, changing_lines, line_index, hexagrams
        ),
    }


def hexagram_from_bits(bits: list[int], dataset: dict | None = None) -> dict:
    dataset = load_dataset() if dataset is None else dataset
    validate_dataset(dataset)
    _validate_bits(bits)
    key = "".join(map(str, bits))
    for row in dataset["hexagrams"]:
        if row["binary_bottom_to_top"] == key:
            return row
    raise ValueError(f"No canonical hexagram matches bits: {key}")


def resolve_three_coins(
    rolls: list[list[int]], dataset: dict | None = None
) -> dict:
    """Resolve six three-coin rolls, each coin represented by 2 (tails) or 3 (heads)."""
    if len(rolls) != 6 or any(len(roll) != 3 for roll in rolls):
        raise ValueError("rolls must contain six rolls of three coin values.")
    if any(type(coin) is not int or coin not in (2, 3) for roll in rolls for coin in roll):
        raise ValueError("Each coin must be represented by 2 or 3.")
    casts = [sum(roll) for roll in rolls]
    return resolve_casts(casts, dataset)


def resolve_yarrow(sticks: list[int], dataset: dict | None = None) -> dict:
    """Resolve six yarrow results represented by the traditional values 6..9."""
    return resolve_casts(sticks, dataset)


def interpretation_focus(
    primary_id: int,
    resulting_id: int,
    changing_lines: list[int],
    line_index: dict[tuple[int, int], dict],
    hexagrams: dict[int, dict],
) -> dict:
    """Return a deterministic, explicit moving-line reading policy.

    This is a presentation policy, not a claim that every historical school
    uses one universal rule.
    """
    count = len(changing_lines)
    primary_lines = [line_index[(primary_id, position)] for position in changing_lines]
    resulting_lines = [
        line_index[(resulting_id, position)]
        for position in range(1, 7)
        if position not in changing_lines
    ]
    if count == 6 and primary_id == 1:
        rule = "six_changing_lines: read_yong_jiu_then_resulting_judgment"
        focus = [
            {"type": "special_line", "line_label": "用九", "hexagram_id": primary_id},
            {"type": "resulting_judgment", "hexagram_id": resulting_id},
        ]
    elif count == 6 and primary_id == 2:
        rule = "six_changing_lines: read_yong_liu_then_resulting_judgment"
        focus = [
            {"type": "special_line", "line_label": "用六", "hexagram_id": primary_id},
            {"type": "resulting_judgment", "hexagram_id": resulting_id},
        ]
    elif count == 0:
        rule = "no_changing_lines: read_primary_judgment"
        focus = [{"type": "primary_judgment", "hexagram_id": primary_id}]
    elif count == 1:
        rule = "one_changing_line: read_the_changing_line"
        focus = [{"type": "changing_line", **primary_lines[0]}]
    elif count == 2:
        rule = "two_changing_lines: read_both_changing_lines_lower_first"
        focus = [{"type": "changing_line", **line} for line in primary_lines]
    elif count == 3:
        rule = "three_changing_lines: primary_judgment_middle_line_resulting_judgment"
        focus = [
            {"type": "primary_judgment", "hexagram_id": primary_id},
            {"type": "changing_line", **primary_lines[1]},
            {"type": "resulting_judgment", "hexagram_id": resulting_id},
        ]
    elif count == 4:
        rule = "four_changing_lines: read_the_two_unchanged_lines"
        focus = [{"type": "unchanged_line", **line} for line in resulting_lines]
    elif count == 5:
        rule = "five_changing_lines: read_the_one_unchanged_line"
        focus = [{"type": "unchanged_line", **resulting_lines[0]}]
    else:
        rule = "six_changing_lines: read_resulting_judgment"
        focus = [{"type": "resulting_judgment", "hexagram_id": resulting_id}]
    return {
        "policy": "explicit_moving_line_policy_v1",
        "rule": rule,
        "primary_hexagram": hexagrams[primary_id],
        "resulting_hexagram": hexagrams[resulting_id],
        "focus": focus,
        "sources": SOURCE_URLS,
    }
