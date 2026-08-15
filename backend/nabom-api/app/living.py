"""Owned living-record domain: DailyEntry, journal, and Evidence.

Canonical shapes follow 06_Core_JSON_Schemas.md. Records are user-owned.
Relationship/group responses must never receive raw journal or birth text
from these collections.
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from domain import new_id

DAILY_TEXT_LIMIT = 8000
JOURNAL_TEXT_LIMIT = 20000
SUMMARY_LIMIT = 120
MAX_TAGS = 12
TAG_LENGTH_LIMIT = 32
SCALE_RANGE = range(1, 6)
EVIDENCE_SOURCE_TYPES = {"daily", "journal"}

# 사용자-facing 라벨 (회고 내러티브 조립용)
MOOD_LABELS = {1: "매우 나쁨", 2: "나쁨", 3: "보통", 4: "좋음", 5: "매우 좋음"}
TRAIT_KO = {
    "exploration": "호기심",
    "execution": "추진력",
    "persistence": "꾸준함",
    "connection": "친밀함",
    "recovery": "회복력",
    "structure": "안정감",
    "expression": "명랑함",
}


PUBLIC_PROFILE_KEYS = {
    "profile_version_id",
    "number",
    "created_at",
    "identity_sentence",
    "traits",
    "strengths",
    "watch_patterns",
    "growth_theme",
    "lenses",
    "evidence_cutoff",
    "character_profile",
    "trait_candidates",
}


def public_profile(profile: dict) -> dict:
    """사용자-facing 프로필. 명리 원문·용신·서사는 밖으로 나가지 않는다."""
    result = {key: profile[key] for key in PUBLIC_PROFILE_KEYS if key in profile}
    character = result.get("character_profile")
    if isinstance(character, dict):
        # visual_key는 내부 조합에 raw 분석 용어가 포함될 수 있으므로 public에서 제거한다.
        # guardian_beast.code는 레거시 PNG 폴백 경로에 필요한 안정적인 아키타입 코드다.
        character = dict(character)
        character.pop("visual_key", None)
        character.pop("representative_element", None)
        character.pop("appearance_seed", None)
        result["character_profile"] = character
    return result


class LivingRecordError(ValueError):
    """Typed validation failure for living-record writes."""


def _now(timezone: str) -> datetime:
    return datetime.now(tz=_timezone(timezone))


def _timezone(name: str) -> ZoneInfo:
    if not isinstance(name, str) or not name.strip():
        raise LivingRecordError("timezone is required")
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, KeyError) as exc:
        raise LivingRecordError("invalid timezone") from exc


def local_today(timezone: str, now: datetime | None = None) -> date:
    current = now or _now(timezone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=_timezone(timezone))
    else:
        current = current.astimezone(_timezone(timezone))
    return current.date()


def parse_record_date(value: str, timezone: str, now: datetime | None = None) -> date:
    if not isinstance(value, str):
        raise LivingRecordError("date must be YYYY-MM-DD")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise LivingRecordError("date must be YYYY-MM-DD") from exc
    if parsed > local_today(timezone, now):
        raise LivingRecordError("date cannot be in the future")
    return parsed


def validate_scale(name: str, value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value not in SCALE_RANGE:
        raise LivingRecordError(f"{name} must be an integer from 1 to 5")
    return value


def normalize_tags(tags) -> list[str]:
    if tags is None:
        return []
    if not isinstance(tags, list) or len(tags) > MAX_TAGS:
        raise LivingRecordError("tags must be a list of at most 12 strings")
    normalized: list[str] = []
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip() or len(tag.strip()) > TAG_LENGTH_LIMIT:
            raise LivingRecordError("each tag must be a non-empty string of at most 32 characters")
        cleaned = tag.strip()
        if cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def normalize_text(value, *, required: bool, limit: int) -> str:
    if value is None:
        text = ""
    elif not isinstance(value, str):
        raise LivingRecordError("text must be a string")
    else:
        text = value
    if len(text) > limit:
        raise LivingRecordError(f"text exceeds {limit} characters")
    if required and not text.strip():
        raise LivingRecordError("text is required")
    return text


def summarize(text: str) -> str:
    compact = " ".join((text or "").split())
    if not compact:
        return "기록이 남겨졌습니다."
    if len(compact) <= SUMMARY_LIMIT:
        return compact
    return compact[: SUMMARY_LIMIT - 1].rstrip() + "…"


def daily_signals(mood: int, energy: int, satisfaction: int) -> list[dict]:
    signals = []
    if mood >= 4:
        signals.append({"trait": "recovery", "direction": "positive", "strength": 0.25})
    elif mood <= 2:
        signals.append({"trait": "recovery", "direction": "negative", "strength": 0.25})
    if energy >= 4:
        signals.append({"trait": "execution", "direction": "positive", "strength": 0.25})
    elif energy <= 2:
        signals.append({"trait": "execution", "direction": "negative", "strength": 0.25})
    if satisfaction >= 4:
        signals.append({"trait": "persistence", "direction": "positive", "strength": 0.25})
    elif satisfaction <= 2:
        signals.append({"trait": "persistence", "direction": "negative", "strength": 0.25})
    return signals


def journal_signals(text: str) -> list[dict]:
    if len(text.strip()) >= 40:
        return [{"trait": "expression", "direction": "positive", "strength": 0.2}]
    return [{"trait": "expression", "direction": "neutral", "strength": 0.1}]


def build_daily_entry(
    user_id: str,
    *,
    record_date: str,
    timezone: str,
    mood: int,
    energy: int,
    satisfaction: int,
    text: str | None,
    tags: list[str] | None,
    existing: dict | None = None,
) -> dict:
    parsed_date = parse_record_date(record_date, timezone)
    payload = {
        "entry_id": existing["entry_id"] if existing else new_id("entry"),
        "user_id": user_id,
        "date": parsed_date.isoformat(),
        "timezone": timezone,
        "mood": validate_scale("mood", mood),
        "energy": validate_scale("energy", energy),
        "satisfaction": validate_scale("satisfaction", satisfaction),
        "text": normalize_text(text, required=False, limit=DAILY_TEXT_LIMIT),
        "tags": normalize_tags(tags),
        "created_at": existing["created_at"] if existing else _now(timezone).isoformat(),
        "updated_at": _now(timezone).isoformat(),
        "status": "active",
    }
    return payload


def public_daily_entry(entry: dict) -> dict:
    return {
        "entry_id": entry["entry_id"],
        "date": entry["date"],
        "timezone": entry.get("timezone", "Asia/Seoul"),
        "mood": entry["mood"],
        "energy": entry["energy"],
        "satisfaction": entry["satisfaction"],
        "text": entry.get("text", ""),
        "tags": list(entry.get("tags") or []),
        "created_at": entry["created_at"],
        "updated_at": entry.get("updated_at", entry["created_at"]),
        "status": entry.get("status", "active"),
    }


def build_journal(
    user_id: str,
    *,
    record_date: str,
    timezone: str,
    text: str,
    tags: list[str] | None,
    existing: dict | None = None,
) -> dict:
    parsed_date = parse_record_date(record_date, timezone)
    return {
        "journal_id": existing["journal_id"] if existing else new_id("journal"),
        "user_id": user_id,
        "date": parsed_date.isoformat(),
        "timezone": timezone,
        "text": normalize_text(text, required=True, limit=JOURNAL_TEXT_LIMIT),
        "tags": normalize_tags(tags),
        "created_at": existing["created_at"] if existing else _now(timezone).isoformat(),
        "updated_at": _now(timezone).isoformat(),
        "status": "active",
    }


def public_journal(journal: dict) -> dict:
    return {
        "journal_id": journal["journal_id"],
        "date": journal["date"],
        "timezone": journal.get("timezone", "Asia/Seoul"),
        "text": journal["text"],
        "tags": list(journal.get("tags") or []),
        "created_at": journal["created_at"],
        "updated_at": journal.get("updated_at", journal["created_at"]),
        "status": journal.get("status", "active"),
    }


def build_evidence(
    user_id: str,
    *,
    source_type: str,
    source: dict,
    timezone: str,
    existing: dict | None = None,
) -> dict:
    if source_type not in EVIDENCE_SOURCE_TYPES:
        raise LivingRecordError("source_type must be daily or journal")
    if source.get("user_id") != user_id:
        raise LivingRecordError("source_record_not_owned")
    if source.get("status") not in {None, "active"}:
        raise LivingRecordError("source_record_not_active")
    occurred = source.get("updated_at") or source.get("created_at") or _now(timezone).isoformat()
    if source_type == "daily":
        source_record_id = source["entry_id"]
        signals = daily_signals(source["mood"], source["energy"], source["satisfaction"])
        summary = summarize(source.get("text") or f"기분 {source['mood']}, 에너지 {source['energy']}")
    else:
        source_record_id = source["journal_id"]
        signals = journal_signals(source["text"])
        summary = summarize(source["text"])
    return {
        "evidence_id": existing["evidence_id"] if existing else new_id("ev"),
        "user_id": user_id,
        "type": source_type,
        "occurred_at": occurred,
        "source_record_id": source_record_id,
        "signals": signals,
        "summary": summary,
        "status": "active",
        "created_at": existing["created_at"] if existing else _now(timezone).isoformat(),
        "updated_at": _now(timezone).isoformat(),
    }


def public_evidence(evidence: dict) -> dict:
    return {
        "evidence_id": evidence["evidence_id"],
        "type": evidence["type"],
        "occurred_at": evidence["occurred_at"],
        "source_record_id": evidence["source_record_id"],
        "signals": list(evidence.get("signals") or []),
        "summary": evidence["summary"],
        "status": evidence.get("status", "active"),
    }


def local_calendar_date(timezone: str, instant: datetime | None = None) -> str:
    current = instant.astimezone(_timezone(timezone)) if instant else _now(timezone)
    return datetime.combine(current.date(), time.min, tzinfo=_timezone(timezone)).date().isoformat()


def stored_reflection_context(
    *,
    period_from: str,
    period_to: str,
    timezone: str,
    entries: list[dict],
    journals: list[dict],
    evidence: list[dict],
) -> dict:
    start = parse_record_date(period_from, timezone)
    end = parse_record_date(period_to, timezone)
    if start > end:
        raise LivingRecordError("period_from must be on or before period_to")
    in_period_entries = [item for item in entries if start.isoformat() <= item.get("date", "") <= end.isoformat() and item.get("status") in {None, "active"}]
    in_period_journals = [item for item in journals if start.isoformat() <= item.get("date", "") <= end.isoformat() and item.get("status") in {None, "active"}]
    recorded_days = {item["date"] for item in in_period_entries}
    recorded_days.update(item["date"] for item in in_period_journals)
    if not recorded_days:
        raise LivingRecordError("weekly mirror requires at least one recorded day")
    source_ids = {item.get("entry_id") for item in in_period_entries} | {item.get("journal_id") for item in in_period_journals}
    refs = [
        item["evidence_id"]
        for item in evidence
        if item.get("status") in {None, "active"} and item.get("source_record_id") in source_ids
    ]
    moods = [item["mood"] for item in in_period_entries]
    energies = [item["energy"] for item in in_period_entries]
    return {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "days_recorded": len(recorded_days),
        "mood": {"average": _mean(moods)} if moods else None,
        "energy": {"average": _mean(energies)} if energies else None,
        "tag_counts": {},
        "goal_actions": {},
        "evidence_refs": refs,
    }


def coverage_mode(days_recorded: int) -> str:
    if days_recorded <= 0:
        return "none"
    if days_recorded <= 2:
        return "light"
    if days_recorded <= 4:
        return "partial"
    return "full"


def _mean(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _signal_key(signal: dict) -> tuple[str, str]:
    return (str(signal.get("trait") or ""), str(signal.get("direction") or ""))


def _has_batchim(word: str) -> bool:
    if not word:
        return False
    code = ord(word[-1])
    return 0xAC00 <= code <= 0xD7A3 and (code - 0xAC00) % 28 != 0


def _wa_gwa(word: str) -> str:
    return f"{word}과" if _has_batchim(word) else f"{word}와"


def _pattern_title(trait: str, direction: str) -> str:
    trait_ko = TRAIT_KO.get(trait, trait)
    subject = _wa_gwa(trait_ko)
    if direction == "positive":
        return f"{subject} 관련된 긍정 신호가 반복됐어요"
    if direction == "negative":
        return f"{subject} 관련해 에너지가 빠지는 흐름이 보였어요"
    return f"{subject} 관련된 기록이 있었어요"


def _pattern_confidence(count: int, source_type_count: int) -> float:
    """결정적 confidence 추정: 횟수와 소스 다양성이 많을수록 높지만 상한을 둔다."""
    return round(min(0.85, 0.3 + 0.1 * count + (0.15 if source_type_count >= 2 else 0)), 2)


def _changes_from_previous(metrics: dict, previous: dict | None, days_recorded: int) -> list[str]:
    if not previous:
        return []
    prev_metrics = previous.get("metrics") or {}
    changes = []
    for key, label in (("average_mood", "기분"), ("average_energy", "에너지"), ("average_satisfaction", "만족도")):
        current = metrics.get(key)
        before = prev_metrics.get(key)
        if current is None or before is None:
            continue
        diff = current - before
        if diff >= 0.3:
            changes.append(f"{label} 평균이 지난주보다 높아졌어요 ({before} → {current})")
        elif diff <= -0.3:
            changes.append(f"{label} 평균이 지난주보다 낮아졌어요 ({before} → {current})")
    if not changes and days_recorded >= 3:
        changes.append("지난주와 비슷한 흐름이 이어지고 있어요")
    return changes[:3]


def build_weekly_mirror(
    user_id: str,
    *,
    period_from: str,
    period_to: str,
    timezone: str,
    entries: list[dict],
    journals: list[dict],
    evidence: list[dict],
    previous: dict | None = None,
) -> dict:
    start = parse_record_date(period_from, timezone)
    end = parse_record_date(period_to, timezone)
    if start > end:
        raise LivingRecordError("period_from must be on or before period_to")
    in_period_entries = [item for item in entries if start.isoformat() <= item.get("date", "") <= end.isoformat() and item.get("status") != "deleted"]
    in_period_journals = [item for item in journals if start.isoformat() <= item.get("date", "") <= end.isoformat() and item.get("status") != "deleted"]
    recorded_days = {item["date"] for item in in_period_entries}
    recorded_days.update(item["date"] for item in in_period_journals)
    days_recorded = len(recorded_days)
    mode = coverage_mode(days_recorded)
    if mode == "none":
        raise LivingRecordError("weekly mirror requires at least one recorded day")
    moods = [item["mood"] for item in in_period_entries]
    energies = [item["energy"] for item in in_period_entries]
    satisfactions = [item["satisfaction"] for item in in_period_entries]
    metrics = {
        "average_mood": _mean(moods),
        "average_energy": _mean(energies),
        "average_satisfaction": _mean(satisfactions),
    }
    emotion_flow = [
        {"date": item["date"], "mood": item["mood"], "label": MOOD_LABELS.get(item["mood"], str(item["mood"]))}
        for item in sorted(in_period_entries, key=lambda item: item["date"])
    ]

    def _day_summary(item: dict) -> str:
        text = (item.get("text") or "").strip()
        compact = " ".join(text.split())
        if len(compact) > 24:
            compact = compact[:23].rstrip() + "…"
        return compact or "특별한 기록 없이 지나간 하루"

    gainer_days = [item for item in in_period_entries if item["energy"] >= 4]
    drainer_days = [item for item in in_period_entries if item["energy"] <= 2]
    energy_gainers = [f"{item['date']} — {_day_summary(item)}" for item in gainer_days]
    energy_drainers = [f"{item['date']} — {_day_summary(item)}" for item in drainer_days]
    notable = sorted(
        in_period_entries,
        key=lambda item: (item["mood"] + item["satisfaction"]) * 10 + item["energy"],
        reverse=True,
    )
    notable_moments = []
    for item in notable[:3]:
        notable_moments.append(f"{item['date']} — {_day_summary(item)}")
    low_days = [item for item in in_period_entries if item["mood"] <= 2]
    for item in low_days:
        label = f"{item['date']} — 힘들었던 하루: {_day_summary(item)}"
        if label not in notable_moments:
            notable_moments.append(label)
    notable_moments = notable_moments[:4]

    source_ids = {item["entry_id"] for item in in_period_entries} | {item["journal_id"] for item in in_period_journals}
    period_evidence = [
        item
        for item in evidence
        if item.get("status") != "deleted" and item.get("source_record_id") in source_ids
    ]
    counts: dict[tuple[str, str], dict] = {}
    for item in period_evidence:
        for signal in item.get("signals") or []:
            key = _signal_key(signal)
            bucket = counts.setdefault(key, {"count": 0, "types": set()})
            bucket["count"] += 1
            bucket["types"].add(item.get("type"))
    patterns = []
    hypotheses = []
    for (trait, direction), bucket in sorted(counts.items()):
        if not trait or not direction:
            continue
        count = bucket["count"]
        source_type_count = len(bucket["types"])
        confidence = _pattern_confidence(count, source_type_count)
        confirmed = count >= 3 or source_type_count >= 2
        if confirmed and mode in {"partial", "full"}:
            patterns.append(
                {
                    "trait": trait,
                    "direction": direction,
                    "title": _pattern_title(trait, direction),
                    "description": f"이번 주 기록 {count}건에서 같은 방향의 신호가 반복적으로 보였어요.",
                    "evidence_count": count,
                    "confidence": confidence,
                    "status": "pattern",
                }
            )
        else:
            hypotheses.append(
                {
                    "trait": trait,
                    "direction": direction,
                    "title": f"{TRAIT_KO.get(trait, trait)} 관련 흐름이 조금씩 보여요",
                    "description": f"이번 주 기록 {count}건에서 이 방향의 신호가 나타났어요. 아직 확인이 필요해요.",
                    "confidence": round(min(0.5, 0.25 + 0.05 * count), 2),
                }
            )
    if mode == "light":
        summary = "이번 주 전체를 말하기에는 기록이 아직 적어요. 대신 남겨준 장면에서 이런 감정이 눈에 띄었습니다."
        patterns = []
    elif mode == "partial":
        summary = "충분한 항목만 조심스럽게 살펴본 부분 거울입니다. 아직 확인이 필요한 흐름은 가능성으로 남겨 둡니다."
    else:
        summary = "이번 주 기록에서 에너지와 감정의 흐름을 비교할 수 있을 만큼 쌓였습니다."
    experiment = None
    if mode == "full":
        experiment = {
            "experiment_id": new_id("exp"),
            "title": "하루 10분, 혼자만의 시간에 적어보기",
            "instruction": "잠들기 전 10분, 오늘 느낀 감정을 아무 필터 없이 적어보세요. 평가하지 않고 그저 적기만 합니다.",
            "success_condition": "이번 주에 최소 4일, 10분 이상 감정을 적었는지",
            "reversible": True,
        }
    return {
        "mirror_id": new_id("wm"),
        "user_id": user_id,
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "coverage": {"days_recorded": days_recorded, "mode": mode},
        "summary": summary,
        "metrics": metrics,
        "notable_moments": notable_moments,
        "emotion_flow": emotion_flow,
        "energy_gainers": energy_gainers,
        "energy_drainers": energy_drainers,
        "patterns": patterns,
        "changes": _changes_from_previous(metrics, previous, days_recorded),
        "hypotheses": hypotheses,
        "growth_experiment": experiment,
        "growth_experiment_id": experiment["experiment_id"] if experiment else None,
        "evidence_refs": [item["evidence_id"] for item in period_evidence],
        "generated_at": _now(timezone).isoformat(),
        "prompt_version": "weekly-v1",
        "status": "active",
    }


def public_weekly_mirror(mirror: dict) -> dict:
    return {
        "mirror_id": mirror["mirror_id"],
        "period": dict(mirror["period"]),
        "coverage": dict(mirror["coverage"]),
        "summary": mirror["summary"],
        "metrics": dict(mirror.get("metrics") or {}),
        "notable_moments": list(mirror.get("notable_moments") or []),
        "emotion_flow": list(mirror.get("emotion_flow") or []),
        "energy_gainers": list(mirror.get("energy_gainers") or []),
        "energy_drainers": list(mirror.get("energy_drainers") or []),
        "patterns": list(mirror.get("patterns") or []),
        "changes": list(mirror.get("changes") or []),
        "hypotheses": list(mirror.get("hypotheses") or []),
        "growth_experiment": mirror.get("growth_experiment"),
        "growth_experiment_id": mirror.get("growth_experiment_id"),
        "evidence_refs": list(mirror.get("evidence_refs") or []),
        "generated_at": mirror["generated_at"],
        "prompt_version": mirror.get("prompt_version", "weekly-v1"),
        "status": mirror.get("status", "active"),
    }
