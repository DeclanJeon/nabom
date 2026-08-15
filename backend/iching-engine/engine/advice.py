"""DeepSeek-backed Korean/English advice generation for an I Ching reading."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"

SYSTEM_PROMPT = """You are an I Ching reflection assistant.
Use only the supplied reading evidence. Do not claim certainty, prophecy, fate,
or guaranteed outcomes. Do not replace medical, legal, financial, or safety
professionals. Give practical, reversible next steps and mention uncertainty.
Separate classical evidence from modern application. Never invent a quotation.
"""


def build_messages(reading: dict, question: str, language: str = "ko") -> list[dict[str, str]]:
    if language not in {"ko", "en"}:
        raise ValueError("language must be 'ko' or 'en'.")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string.")
    language_name = "Korean" if language == "ko" else "English"
    evidence = {
        "question": question.strip(),
        "primary_hexagram": reading["primary_hexagram"],
        "changing_lines": reading["changing_lines"],
        "special_line": reading.get("special_line"),
        "resulting_hexagram": reading["resulting_hexagram"],
        "relationships": reading["relationships"],
        "interpretation_policy": reading["interpretation"],
        "theme_links": reading.get("theme_links", []),
        "translation": reading.get("translations", {}).get("legge"),
    }
    user_prompt = f"""Answer in {language_name}.
Return these sections:
1. Reading summary
2. Classical evidence (quote only from supplied evidence)
3. Practical interpretation for the question
4. One immediate action
5. One risk or counter-signal
6. Confidence and limitations

Reading evidence JSON:
{json.dumps(evidence, ensure_ascii=False, indent=2)}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def generate_advice(
    reading: dict,
    question: str,
    language: str = "ko",
    *,
    api_key: str | None = None,
    model: str | None = None,
    timeout: int = 60,
) -> dict:
    """Generate advice through DeepSeek's OpenAI-compatible chat endpoint."""
    key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not configured. Set it in the environment; never commit it."
        )
    selected_model = model or os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)
    payload = {
        "model": selected_model,
        "messages": build_messages(reading, question, language),
        "temperature": 0.3,
        "stream": False,
    }
    request = Request(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"DeepSeek connection failed: {error.reason}") from error
    except TimeoutError as error:
        raise RuntimeError("DeepSeek connection timed out.") from error
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("DeepSeek returned an unexpected response shape.") from error
    return {
        "provider": "deepseek",
        "model": selected_model,
        "language": language,
        "question": question.strip(),
        "advice": content,
        "usage": result.get("usage"),
    }


def render_reading(reading: dict, advice: dict | None = None) -> str:
    """Render a reading for a person, rather than exposing the raw JSON shape."""
    english = advice is not None and advice.get("language") == "en"
    primary = reading["primary_hexagram"]
    resulting = reading["resulting_hexagram"]
    changing = reading["changing_lines"]
    lines = [
        (
            f"Primary hexagram: {primary['hexagram_id']} {primary['name_zh']} ({primary['name_ko']})"
            if english
            else f"본괘: {primary['hexagram_id']} {primary['name_zh']} ({primary['name_ko']})"
        ),
        (
            f"Resulting hexagram: {resulting['hexagram_id']} {resulting['name_zh']} ({resulting['name_ko']})"
            if english
            else f"지괘: {resulting['hexagram_id']} {resulting['name_zh']} ({resulting['name_ko']})"
        ),
    ]
    if changing:
        labels = ", ".join(line["line_label"] for line in changing)
        lines.append(f"Changing lines: {labels}" if english else f"동효: {labels}")
    else:
        lines.append("Changing lines: none" if english else "동효: 없음")
    lines.append("")
    lines.append("Classical evidence" if english else "주역의 근거")
    lines.append(f"- Judgment: {primary['judgment_text']}" if english else f"- 괘사: {primary['judgment_text']}")
    korean_judgment = reading.get("korean_judgment_ko")
    if korean_judgment and not english:
        lines.append(f"  해석: {korean_judgment}")
    themes = reading.get("themes") or []
    if themes:
        lines.append("")
        lines.append("Themes" if english else "주제별 해석")
        for theme in themes:
            topic = theme.get("topic", "")
            lens = theme.get("lens", "")[:120]
            lines.append(f"- [{topic}] {lens}")
    if changing:
        for line in changing:
            lines.append(f"- {line['line_label']}: {line['classical_text']}")
            if line.get("korean_text"):
                if english:
                    lines.append("  English translation is available in the JSON result.")
                else:
                    lines.append(f"  해석: {line['korean_text']}")
    lines.append("")
    if advice:
        lines.append("현실 조언" if advice["language"] == "ko" else "Practical advice")
        lines.append(advice["advice"].strip())
    else:
        lines.append(
            "This is the structured reading. Use --advice for an explanation."
            if english
            else "이 결과는 점괘와 원문 근거입니다. --advice를 사용하면 DeepSeek가 이해하기 쉬운 조언으로 정리합니다."
        )
    return "\n".join(lines)
