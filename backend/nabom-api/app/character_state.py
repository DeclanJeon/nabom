"""Current character condition derived from recent living records.

The journey stage is cumulative. This module deliberately models a separate,
reversible current state so a character can look tired, stable, growing, or
recovering without erasing the user's accumulated journey.
"""

from __future__ import annotations

import hashlib
from statistics import mean

STATES = {"rising", "steady", "strained", "recovering"}
STATE_LABELS = {
    "rising": "조금씩 힘이 붙는 중",
    "steady": "지금의 리듬을 지키는 중",
    "strained": "잠시 힘을 덜어내는 중",
    "recovering": "다시 힘을 고르는 중",
}


def _score(entry: dict) -> float:
    values = [entry.get(key) for key in ("mood", "energy", "satisfaction")]
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    return mean(numeric) if numeric else 3.0


def _recent_entries(entries: list[dict], window: int = 14) -> list[dict]:
    active = [item for item in entries if item.get("status") in {None, "active"}]
    return sorted(active, key=lambda item: item.get("date", ""))[-window:]


def derive_condition_state(
    entries: list[dict],
    journals: list[dict] | None = None,
    evidence: list[dict] | None = None,
    previous_state: str | None = None,
) -> dict:
    """Return a stable, reversible state from a recent observation window.

    Fewer than three daily observations remain steady: sparse data must not
    make a character look worse or better. The decision uses the recent seven
    records versus the preceding seven records and has intentionally broad
    thresholds to avoid visual flicker.
    """
    recent = _recent_entries(entries)
    if len(recent) < 3:
        state = previous_state if previous_state in STATES else "steady"
        return {"state": state, "label": STATE_LABELS[state], "confidence": 0.1, "observations": len(recent)}

    scores = [_score(item) for item in recent]
    current = mean(scores[-7:])
    previous_scores = scores[:-7]
    previous = mean(previous_scores) if previous_scores else current
    delta = current - previous

    # Evidence is already normalized by living.build_evidence. Use it only as
    # a bounded supplement so raw journal text never enters this calculator.
    normalized = [
        signal
        for item in (evidence or [])
        for signal in item.get("signals") or []
        if signal.get("direction") in {"positive", "negative"}
    ]
    if normalized:
        evidence_bias = mean(
            1.0 if signal["direction"] == "positive" else -1.0
            for signal in normalized
        )
        current += max(-0.5, min(0.5, evidence_bias * 0.5))

    if current <= 2.5:
        state = "strained"
    elif previous <= 2.8 and current >= 3.4 and delta >= 0.35:
        state = "recovering"
    elif current >= 3.8 and delta >= 0.3:
        state = "rising"
    else:
        state = "steady"

    # Hysteresis: sparse windows do not flip an established visual state.
    if previous_state in STATES and len(recent) < 7:
        state = previous_state
    elif previous_state == "strained" and state == "rising":
        state = "recovering"

    confidence = min(0.9, round(0.25 + len(recent) * 0.04, 2))
    return {
        "state": state,
        "label": STATE_LABELS[state],
        "confidence": confidence,
        "observations": len(recent),
    }


def condition_prompt(state: str) -> str:
    """Everyday visual direction for the image prompt."""
    return {
        "rising": "open posture, clear eyes, a slightly forward gesture, neatly added personal detail",
        "steady": "relaxed centered posture, calm eyes, familiar clothing and a comfortable gesture",
        "strained": "smaller posture, lowered shoulders, thoughtful tired eyes, simpler slightly rumpled clothing, keep the character gentle rather than defeated",
        "recovering": "careful upright posture, soft warm eyes, one small restored detail in the clothing, a nearby comforting light or rest object",
    }.get(state, "relaxed centered posture, calm eyes, familiar clothing")


def appearance_seed(profile_id: str, profile_version: str, stage: int, state: str) -> str:
    """Stable internal seed for reproducible pose/style variation."""
    raw = f"{profile_id}:{profile_version}:{stage}:{state}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]
