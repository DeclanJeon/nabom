"""Profile refresh: evidence-based trait blend + new ProfileVersion proposal.

Design §3.3 / §8: Daily(Evidence) → Weekly(Pattern) → Monthly/충분한 Evidence
→ Profile Update Proposal → user confirm → new ProfileVersion (002, 003, ...).

The initial profile is a birth-hypothesis baseline. As journal evidence
accumulates, trait values move toward what the person actually records.
Character visuals follow: when the blended dominant trait changes the visual
key, a fresh character image is generated (same key = reuse).
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from living import daily_signals, journal_signals  # noqa: E402

# 새 버전 제안 조건: 기록일 수 (4주)
MIN_RECORDED_DAYS = 28
MIN_RECORD_COUNT = 14

# evidence 신호의 trait별 방향 (trait → 얼마나 "높음"에 기여하는지)
POSITIVE_TRAITS = {"recovery", "execution", "persistence", "expression"}
NEGATIVE_TRAITS = {"recovery", "execution", "persistence"}  # 낮은 지표가 낮추는 방향


def signals_from_records(entries: list[dict], journals: list[dict]) -> tuple[list[dict], int]:
    """daily_entries/journals에서 직접 신호를 뽑는다 (evidence 미생성 대비).

    returns (signals, 신호가 있는 기록 수)
    """
    signals: list[dict] = []
    count = 0
    for entry in entries:
        signals.extend(
            {"trait": s["trait"], "direction": s["direction"], "strength": s["strength"]}
            for s in daily_signals(entry.get("mood", 3), entry.get("energy", 3), entry.get("satisfaction", 3))
        )
        count += 1
    for journal in journals:
        signals.extend(
            {"trait": s["trait"], "direction": s["direction"], "strength": s["strength"]}
            for s in journal_signals(journal.get("text", ""))
        )
        count += 1
    return signals, count


def aggregate_signals(signals: list[dict]) -> dict[str, float]:
    """trait → 누적 신호 (positive는 +, negative는 -)."""
    totals: dict[str, float] = {}
    for signal in signals:
        trait = signal.get("trait")
        direction = signal.get("direction")
        strength = float(signal.get("strength") or 0.0)
        if not trait:
            continue
        if direction == "positive":
            totals[trait] = totals.get(trait, 0.0) + strength
        elif direction == "negative":
            totals[trait] = totals.get(trait, 0.0) - strength
        else:
            totals[trait] = totals.get(trait, 0.0) + 0.0
    return totals


def blend_trait_value(birth_value: float, evidence_total: float, evidence_count: int) -> float:
    """birth 후보와 기록 신호를 blend한다.

    evidence가 적으면 birth에 가깝고, 쌓일수록 기록 쪽으로 움직인다.
    """
    if evidence_count <= 0:
        return birth_value
    # evidence 1건당 0.04씩 기록 비중 증가, 최대 0.55 (기록이 과반을 넘지 않게)
    record_weight = min(0.55, evidence_count * 0.04)
    # 신호 합을 0..1 로 압축 (sigmoid 대신 clamp된 단순 비율)
    signal_ratio = max(0.0, min(1.0, 0.5 + evidence_total / max(evidence_count, 1)))
    blended = birth_value * (1 - record_weight) + signal_ratio * record_weight
    return round(max(0.05, min(0.95, blended)), 3)


def refresh_candidates(
    analysis: dict,
    trait_candidates: list[dict],
    entries: list[dict],
    journals: list[dict],
) -> list[dict]:
    """기존 trait 후보에 기록 신호를 blend한 갱신 후보를 만든다.

    반환은 status="refresh_proposal"인 새 후보 목록. 기록 신호가 없으면
    birth 후보를 그대로 둔다.
    """
    signals, _count = signals_from_records(entries, journals)
    if not signals:
        return trait_candidates
    totals = aggregate_signals(signals)
    trait_counts: dict[str, int] = {}
    for signal in signals:
        trait = signal.get("trait")
        if trait:
            trait_counts[trait] = trait_counts.get(trait, 0) + 1
    refreshed: list[dict] = []
    for candidate in trait_candidates:
        trait = candidate["trait"]
        evidence_total = totals.get(trait, 0.0)
        count = trait_counts.get(trait, 0)
        blended = blend_trait_value(candidate["strength"], evidence_total, count)
        # 기록 신호가 그 trait에 전혀 없으면 기존 값 유지
        if count == 0:
            refreshed.append(dict(candidate))
            continue
        updated = dict(candidate)
        updated["strength"] = blended
        updated["source"] = "evidence_blend"
        updated["status"] = "refresh_proposal"
        updated["reason_refs"] = [*candidate.get("reason_refs", []), "evidence_blend"]
        # 신뢰도: 기록이 쌓일수록 조금씩 올라가지만 candidate 유지
        updated["confidence"] = round(
            max(0.05, min(0.55, candidate.get("confidence", 0.2) + count * 0.01)), 3
        )
        refreshed.append(updated)
    return refreshed


def should_propose_refresh(recorded_days: int, record_count: int) -> bool:
    return recorded_days >= MIN_RECORDED_DAYS and record_count >= MIN_RECORD_COUNT


def new_profile_version_id() -> str:
    return f"pv_{uuid.uuid4().hex[:8]}"


def utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
