#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DAY_REFERENCE = date(1992, 3, 1)
DAY_REFERENCE_HANJA = "丙子"
DEFAULT_TIMEZONE = "Asia/Seoul"
ENGINE_VERSION = "manse-korean-v1"
RULE_SET_VERSION = "csv-contract-v1"
PRECISION_LEVELS = {"precision_open", "precision_limited", "precision_blocked"}
BOUNDARY_CANDIDATE_HOURS = 2.0
LUNAR_PYTHON_CLOCK = timezone(timedelta(hours=8))  # CST; never treat as Asia/Seoul

MONTH_BRANCH_ORDER = ["in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul", "hae", "ja", "chuk"]
APPROX_SOLAR_TERM_STARTS = [
    ("chuk", "소한", 1, 6),
    ("in", "입춘", 2, 4),
    ("myo", "경칩", 3, 6),
    ("jin", "청명", 4, 5),
    ("sa", "입하", 5, 6),
    ("o", "망종", 6, 6),
    ("mi", "소서", 7, 7),
    ("sin", "입추", 8, 8),
    ("yu", "백로", 9, 8),
    ("sul", "한로", 10, 8),
    ("hae", "입동", 11, 7),
    ("ja", "대설", 12, 7),
]

MONTH_START_TERM_BRANCH = {
    "소한": "chuk",
    "입춘": "in",
    "경칩": "myo",
    "청명": "jin",
    "입하": "sa",
    "망종": "o",
    "소서": "mi",
    "입추": "sin",
    "백로": "yu",
    "한로": "sul",
    "입동": "hae",
    "대설": "ja",
}
class LunarLeapMonthAmbiguous(ValueError):
    """Unspecified leap month when that lunar year has both a normal and a leap month."""

    def __init__(self, birth_date, candidates):
        self.birth_date = birth_date
        self.candidates = candidates
        super().__init__("lunar leap month is unspecified and both normal and leap months exist")



@dataclass(frozen=True)
class Pillar:
    cycle_no: int
    gapja_code: str
    ko: str
    hanja: str
    stem_code: str
    branch_code: str


def read_csv(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def precision_policy(quality_flags, solar_term_quality, calendar_type):
    flags = set(quality_flags)
    blocked_flags = {
        "lunar_input_not_converted",
        "lunar_input_not_converted",
        "birth_date_invalid",
    }
    limited_flags = {
        "birth_time_missing",
        "birth_time_range_crosses_hour_branch",
        "ja_hour_candidate_only",
        "late_ja_hour_alternate_day_candidate",
        "approximate_solar_terms",
        "approximate_solar_term_boundary_risk",
        "near_ipchun_boundary",
        "near_solar_term_boundary",
        "birth_place_missing",
        "calendar_conversion_required",
        "timezone_historical_offset_used",
        "timezone_fixed_offset_used",
        "timezone_overseas_without_birthplace",
        "solar_term_boundary_candidate_scope",
        "hour_pillar_omitted",
        "lunar_leap_month_ambiguous",
    }
    if flags & blocked_flags:
        return {
            "level": "precision_blocked",
            "exact_claims_allowed": False,
            "reason_codes": sorted(flags & blocked_flags),
        }
    if flags & limited_flags or solar_term_quality.get("source_quality") != "verified":
        return {
            "level": "precision_limited",
            "exact_claims_allowed": False,
            "reason_codes": sorted(flags & limited_flags) or ["solar_term_source_not_verified"],
        }
    return {
        "level": "precision_open",
        "exact_claims_allowed": True,
        "reason_codes": [],
    }


def lunar_python_jieqi_utc(term_hanja, year):
    """Read lunar-python JieQi as CST (UTC+8) and return an aware UTC datetime.

    The library clock is China Standard Time. Storing it as Asia/Seoul is the
    historic −60 minute gap versus NAOJ/HKO, not an astronomy error.
    """
    from lunar_python import Lunar

    table = Lunar.fromYmd(year, 1, 1).getJieQiTable()
    solar = table.get(term_hanja)
    if solar is None:
        return None
    naive = datetime.strptime(solar.toYmdHms(), "%Y-%m-%d %H:%M:%S")
    return naive.replace(tzinfo=LUNAR_PYTHON_CLOCK).astimezone(timezone.utc)


def _try_lunar_month(year, month, day, is_leap):
    from lunar_python import Lunar

    lunar_month = -month if is_leap else month
    lunar = Lunar.fromYmd(year, lunar_month, day)
    solar = lunar.getSolar()
    return {
        "input_birth_date": f"{year:04d}-{month:02d}-{day:02d}",
        "is_lunar_leap_month": bool(is_leap),
        "solar_birth_date": solar.toYmd(),
        "provider": "lunar-python",
        "provider_version": "1.4.8",
        "provider_lunar_label": lunar.toString(),
        "role": "conversion_candidate_only",
        "clock_policy": "cst_utc_plus_8_never_asia_seoul",
    }


def lunar_month_candidates(birth_date):
    try:
        from lunar_python import LunarYear
    except ImportError as error:
        raise ValueError("lunar input requires lunar-python==1.4.8") from error
    try:
        year, month, day = (int(value) for value in birth_date.split("-"))
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid lunar input: {birth_date}") from error

    leap_month = LunarYear.fromYear(year).getLeapMonth()
    candidates = []
    for is_leap in (False, True):
        if is_leap and leap_month != month:
            continue
        try:
            candidates.append(_try_lunar_month(year, month, day, is_leap))
        except Exception:  # noqa: BLE001 — library raises generic Exception for missing months
            continue
    if not candidates:
        raise ValueError(f"invalid lunar input: {birth_date}")
    return {
        "input_birth_date": birth_date,
        "leap_month_in_year": leap_month or None,
        "candidates": candidates,
        "provider": "lunar-python",
        "provider_version": "1.4.8",
        "role": "conversion_candidate_only",
    }


def convert_lunar_input(birth_date, is_lunar_leap_month):
    probe = lunar_month_candidates(birth_date)
    if is_lunar_leap_month is None:
        if len(probe["candidates"]) == 1:
            selected = dict(probe["candidates"][0])
            selected["leap_month_auto_resolved"] = True
            return selected
        raise LunarLeapMonthAmbiguous(birth_date, probe["candidates"])
    wanted = bool(is_lunar_leap_month)
    for candidate in probe["candidates"]:
        if candidate["is_lunar_leap_month"] is wanted:
            return candidate
    raise ValueError(f"invalid lunar input: {birth_date}")


def read_csv_files(pattern):
    rows = []
    for path in sorted(ROOT.glob(pattern)):
        with path.open(newline="", encoding="utf-8") as f:
            rows.extend({**row, "source_file": str(path.relative_to(ROOT))} for row in csv.DictReader(f))
    return rows


def read_optional_csv_file(path_value, source_file_label):
    if not path_value:
        return []
    path = Path(path_value)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return [{**row, "source_file": source_file_label} for row in csv.DictReader(f)]


def merge_solar_term_provider_rows(fixture_rows, provider_rows):
    provider_years = {str(row.get("year", "")).strip() for row in provider_rows if str(row.get("year", "")).strip().isdigit()}
    provider_years = {year for year in provider_years if len(year) == 4}
    if not provider_years:
        return fixture_rows + provider_rows
    return [row for row in fixture_rows if str(row.get("year", "")).strip() not in provider_years] + provider_rows


def load_tables():
    gapja_rows = sorted(read_csv("gapja-combinations.csv"), key=lambda row: int(row["cycle_no"]))
    stems = sorted(read_csv("heavenly-stems.csv"), key=lambda row: int(row["order_no"]))
    branches = sorted(read_csv("earthly-branches.csv"), key=lambda row: int(row["order_no"]))
    month_start_rows = read_csv("month-stem-start-rules.csv")
    hour_start_rows = read_csv("hour-stem-start-rules.csv")
    fixture_solar_term_rows = read_csv_files("design/solar-term-source-attachments-*.csv")
    provider_solar_term_rows = read_optional_csv_file(os.environ.get("SAJU_SOLAR_TERM_PROVIDER_CSV", ""), "SAJU_SOLAR_TERM_PROVIDER_CSV")
    verified_solar_term_rows = merge_solar_term_provider_rows(fixture_solar_term_rows, provider_solar_term_rows)
    twelve_life_stage_rows = read_csv("twelve-life-stage-map.csv")
    twelve_life_stages = {row["stage_code"]: row for row in read_csv("twelve-life-stages.csv")}
    twelve_shinsal_rules = read_csv("twelve-shinsal-rules.csv")
    twelve_shinsal = {row["shinsal_code"]: row for row in read_csv("twelve-shinsal.csv")}
    special_star_rules = read_csv("special-star-rules.csv")
    special_stars = {row["special_star_code"]: row for row in read_csv("special-stars.csv")}

    gapja = [
        Pillar(
            cycle_no=int(row["cycle_no"]),
            gapja_code=row["gapja_code"],
            ko=row["ko_name"],
            hanja=row["hanja_name"],
            stem_code=row["stem_code"],
            branch_code=row["branch_code"],
        )
        for row in gapja_rows
    ]
    stem_order = [row["stem_code"] for row in stems]
    branch_order = [row["branch_code"] for row in branches]

    month_start = {}
    for row in month_start_rows:
        for stem_code in row["year_stem_codes"].split(";"):
            month_start[stem_code] = row["start_month_stem_code"]

    hour_start = {}
    for row in hour_start_rows:
        for stem_code in row["day_stem_codes"].split(";"):
            hour_start[stem_code] = row["start_hour_stem_code"]

    return {
        "gapja": gapja,
        "stem_order": stem_order,
        "branch_order": branch_order,
        "stems": {row["stem_code"]: row for row in stems},
        "branches": {row["branch_code"]: row for row in branches},
        "month_start": month_start,
        "hour_start": hour_start,
        "verified_solar_terms": verified_solar_term_rows,
        "twelve_life_stage_map": twelve_life_stage_rows,
        "twelve_life_stages": twelve_life_stages,
        "twelve_shinsal_rules": twelve_shinsal_rules,
        "twelve_shinsal": twelve_shinsal,
        "special_star_rules": special_star_rules,
        "special_stars": special_stars,
    }


def gapja_by_index(tables, index):
    return tables["gapja"][index % 60]


def gapja_by_stem_branch(tables, stem_code, branch_code):
    for pillar in tables["gapja"]:
        if pillar.stem_code == stem_code and pillar.branch_code == branch_code:
            return pillar
    raise ValueError(f"invalid stem/branch pair: {stem_code}/{branch_code}")


def stem_index(tables, stem_code):
    return tables["stem_order"].index(stem_code)


def branch_index(tables, branch_code):
    return tables["branch_order"].index(branch_code)


def parse_birth_time(raw_value):
    if not raw_value:
        return None, None, ["birth_time_missing"]
    if "-" in raw_value:
        start_raw, end_raw = raw_value.split("-", 1)
        start = datetime.strptime(start_raw.strip(), "%H:%M").time()
        end = datetime.strptime(end_raw.strip(), "%H:%M").time()
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
        midpoint = (start_minutes + end_minutes) // 2
        midpoint %= 24 * 60
        representative = time(midpoint // 60, midpoint % 60)
        flags = ["birth_time_range_used"]
        end_for_branch = end_minutes - 1 if end_minutes > start_minutes else end_minutes
        if hour_branch_for_minutes(start_minutes % (24 * 60)) != hour_branch_for_minutes(end_for_branch % (24 * 60)):
            flags.append("birth_time_range_crosses_hour_branch")
        if any(start_minutes <= boundary <= end_minutes for boundary in hour_boundaries_between(start_minutes, end_minutes)):
            flags.append("birth_time_range_touches_hour_boundary")
        return representative, (start, end), flags
    return datetime.strptime(raw_value.strip(), "%H:%M").time(), None, []


def hour_boundaries_between(start_minutes, end_minutes):
    boundaries = []
    for day_offset in (0, 24 * 60):
        boundaries.extend([day_offset, day_offset + 60])
        boundaries.extend(day_offset + minutes for minutes in range(3 * 60, 24 * 60, 2 * 60))
    return boundaries


def hour_branch_for_minutes(minutes):
    if minutes >= 23 * 60 or minutes < 60:
        return "ja"
    return ["chuk", "in", "myo", "jin", "sa", "o", "mi", "sin", "yu", "sul", "hae"][(minutes - 60) // 120]


def minutes_for_time(value):
    return value.hour * 60 + value.minute


def time_range_minutes(time_range):
    if not time_range:
        return None
    start, end = time_range
    start_minutes = minutes_for_time(start)
    end_minutes = minutes_for_time(end)
    if end_minutes < start_minutes:
        end_minutes += 24 * 60
    return start_minutes, end_minutes


def interval_overlaps(left_start, left_end, right_start, right_end):
    return left_start < right_end and right_start < left_end


def time_range_touches_ja_hour(time_range):
    minutes = time_range_minutes(time_range)
    if not minutes:
        return False
    start_minutes, end_minutes = minutes
    ja_windows = [(0, 60), (23 * 60, 25 * 60), (24 * 60, 25 * 60)]
    return any(interval_overlaps(start_minutes, end_minutes, window_start, window_end) for window_start, window_end in ja_windows)


def is_ja_hour_time(value):
    if value is None:
        return False
    minutes = minutes_for_time(value)
    return minutes >= 23 * 60 or minutes < 60


def parse_timezone(value):
    if not value:
        return ZoneInfo(DEFAULT_TIMEZONE)
    if value.startswith(("+", "-")) and len(value) in {5, 6}:
        sign = 1 if value[0] == "+" else -1
        normalized = value.replace(":", "")
        hours = int(normalized[1:3])
        minutes = int(normalized[3:5])
        return timezone(sign * timedelta(hours=hours, minutes=minutes))
    return ZoneInfo(value)


def format_utc_offset(offset):
    if offset is None:
        return ""
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if seconds:
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{sign}{hours:02d}:{minutes:02d}"


def timezone_quality_profile(tzinfo, timezone_value, birth_place, local_dt, quality_flags):
    timezone_label = timezone_value or DEFAULT_TIMEZONE
    offset = local_dt.utcoffset()
    dst = local_dt.dst()
    is_iana_timezone = isinstance(tzinfo, ZoneInfo)
    reference_dt = datetime(2026, 1, 1, 12, 0, tzinfo=tzinfo)
    reference_offset = reference_dt.utcoffset()
    historical_offset_used = is_iana_timezone and offset != reference_offset
    dst_offset_used = bool(dst and dst.total_seconds())
    birth_place_provided = bool((birth_place or "").strip())

    quality_flags.append("timezone_verified")
    if not timezone_value:
        quality_flags.append("timezone_defaulted")
    if not is_iana_timezone:
        quality_flags.append("timezone_fixed_offset_used")
    if historical_offset_used:
        quality_flags.append("timezone_historical_offset_used")
    if dst_offset_used:
        quality_flags.append("timezone_dst_offset_used")
    if not birth_place_provided and timezone_label not in {DEFAULT_TIMEZONE, "+09:00", "+0900"}:
        quality_flags.append("birth_place_missing")

    return {
        "timezone": timezone_label,
        "timezone_type": "iana" if is_iana_timezone else "fixed_offset",
        "utc_offset": format_utc_offset(offset),
        "reference_utc_offset_2026": format_utc_offset(reference_offset),
        "dst_offset": format_utc_offset(dst),
        "historical_offset_used": historical_offset_used,
        "dst_offset_used": dst_offset_used,
        "birth_place_status": "provided" if birth_place_provided else "missing",
        "evidence_refs": [
            "design/manse-validation-fixture-spec.md",
            "design/manse-remaining-fixture-review-plan.md",
            "IANA tz database via zoneinfo" if is_iana_timezone else "explicit UTC offset input",
        ],
    }


def verified_solar_term_boundaries(tables, year, tzinfo):
    accepted_statuses = {
        ("hko_exact_attached", "matched_0m", "matched_kma_date_name"): "verified_hko_naoj_korean",
        ("naoj_long_term_exact_attached", "source_of_record", "term_name_matched"): "verified_naoj_korean",
    }
    rows = [
        row
        for row in tables.get("verified_solar_terms", [])
        if int(row["year"]) == year
        and int(row["term_order"]) % 2 == 1
        and (row["source_status"], row["naoj_crosscheck_status"], row["korean_date_sanity_status"]) in accepted_statuses
    ]
    if len(rows) != 12:
        return []
    if {row["solar_term_ko"] for row in rows} != set(MONTH_START_TERM_BRANCH.keys()):
        return []
    return sorted(
        [
            {
                "branch_code": MONTH_START_TERM_BRANCH[row["solar_term_ko"]],
                "term_ko": row["solar_term_ko"],
                "datetime": datetime.fromisoformat(row["kst_datetime"]).astimezone(tzinfo),
                "source": f"{accepted_statuses[(row['source_status'], row['naoj_crosscheck_status'], row['korean_date_sanity_status'])]}_{row['year']}",
                "source_file": row.get("source_file", ""),
                "verified_year": int(row["year"]),
            }
            for row in rows
            if row["solar_term_ko"] in MONTH_START_TERM_BRANCH
        ],
        key=lambda row: row["datetime"],
    )


def solar_term_boundaries(tables, year, tzinfo):
    verified = verified_solar_term_boundaries(tables, year, tzinfo)
    if verified:
        return verified
    return [
        {
            "branch_code": branch_code,
            "term_ko": term_ko,
            "datetime": datetime(year, month, day, tzinfo=tzinfo),
            "source": "approximate_static_boundary",
        }
        for branch_code, term_ko, month, day in APPROX_SOLAR_TERM_STARTS
    ]


def nearest_solar_terms(tables, dt):
    terms = solar_term_boundaries(tables, dt.year - 1, dt.tzinfo) + solar_term_boundaries(tables, dt.year, dt.tzinfo) + solar_term_boundaries(tables, dt.year + 1, dt.tzinfo)
    terms.sort(key=lambda row: row["datetime"])
    previous_terms = [row for row in terms if row["datetime"] <= dt]
    next_terms = [row for row in terms if row["datetime"] > dt]
    return previous_terms[-1], next_terms[0]


def solar_term_quality_profile(previous_term, next_term, dt):
    previous_delta_hours = round(abs((dt - previous_term["datetime"]).total_seconds()) / 3600, 2)
    next_delta_hours = round(abs((next_term["datetime"] - dt).total_seconds()) / 3600, 2)
    if previous_delta_hours <= next_delta_hours:
        nearest = previous_term
        nearest_direction = "previous"
        nearest_delta_hours = previous_delta_hours
    else:
        nearest = next_term
        nearest_direction = "next"
        nearest_delta_hours = next_delta_hours
    if nearest_delta_hours <= 6:
        boundary_risk_level = "critical"
    elif nearest_delta_hours <= 24:
        boundary_risk_level = "high"
    elif nearest_delta_hours <= 48:
        boundary_risk_level = "medium"
    else:
        boundary_risk_level = "low"
    source_quality = (
        "verified"
        if previous_term.get("source") != "approximate_static_boundary" and next_term.get("source") != "approximate_static_boundary"
        else "approximate"
    )
    base_confidence = 0.95 if source_quality == "verified" else 0.68
    boundary_penalty = {
        "critical": 0.18,
        "high": 0.14,
        "medium": 0.08,
        "low": 0.0,
    }[boundary_risk_level]
    confidence_score = round(max(0.0, base_confidence - boundary_penalty), 2)
    if confidence_score >= 0.85:
        confidence_band = "high"
    elif confidence_score >= 0.65:
        confidence_band = "medium"
    elif confidence_score >= 0.45:
        confidence_band = "limited"
    else:
        confidence_band = "low"
    return {
        "source_quality": source_quality,
        "boundary_risk_level": boundary_risk_level,
        "confidence_score": confidence_score,
        "confidence_band": confidence_band,
        "previous_delta_hours": previous_delta_hours,
        "next_delta_hours": next_delta_hours,
        "nearest_term_ko": nearest["term_ko"],
        "nearest_term_direction": nearest_direction,
        "nearest_boundary_delta_hours": nearest_delta_hours,
        "evidence_refs": ["solar-term-month-boundaries.csv", previous_term.get("source_file", ""), next_term.get("source_file", "")],
    }


def year_pillar(tables, dt, quality_flags):
    ipchun = next((term["datetime"] for term in solar_term_boundaries(tables, dt.year, dt.tzinfo) if term["term_ko"] == "입춘"), None)
    if ipchun is None:
        ipchun = datetime(dt.year, 2, 4, tzinfo=dt.tzinfo)
    pillar_year = dt.year if dt >= ipchun else dt.year - 1
    if abs((dt - ipchun).total_seconds()) <= 2 * 24 * 3600:
        quality_flags.append("near_ipchun_boundary")
    return gapja_by_index(tables, pillar_year - 1984)


def month_pillar(tables, dt, year_stem_code, quality_flags):
    previous_term, next_term = nearest_solar_terms(tables, dt)
    if min(abs((dt - previous_term["datetime"]).total_seconds()), abs((next_term["datetime"] - dt).total_seconds())) <= 24 * 3600:
        quality_flags.append("near_solar_term_boundary")
    if previous_term["source"] == "approximate_static_boundary" or next_term["source"] == "approximate_static_boundary":
        quality_flags.append("approximate_solar_terms")
    else:
        quality_flags.append(f"verified_solar_term_time_{previous_term['verified_year']}")
    month_branch_code = previous_term["branch_code"]
    start_stem_code = tables["month_start"][year_stem_code]
    month_offset = MONTH_BRANCH_ORDER.index(month_branch_code)
    month_stem_code = tables["stem_order"][(stem_index(tables, start_stem_code) + month_offset) % 10]
    return gapja_by_stem_branch(tables, month_stem_code, month_branch_code), previous_term, next_term


def day_pillar(tables, local_date):
    reference_index = next(i for i, pillar in enumerate(tables["gapja"]) if pillar.hanja == DAY_REFERENCE_HANJA)
    days = (local_date - DAY_REFERENCE).days
    return gapja_by_index(tables, reference_index + days)


def hour_pillar(tables, local_time, day_stem_code):
    if local_time is None:
        return None
    branch_code = hour_branch_for_minutes(local_time.hour * 60 + local_time.minute)
    start_stem_code = tables["hour_start"][day_stem_code]
    hour_stem_code = tables["stem_order"][(stem_index(tables, start_stem_code) + branch_index(tables, branch_code)) % 10]
    return gapja_by_stem_branch(tables, hour_stem_code, branch_code)


def ja_hour_policy_profile(tables, local_date, local_time, time_range, primary_day, primary_hour, birth_time_missing):
    profile = {
        "policy": "civil_day_primary_with_early_ja_candidate",
        "status": "not_applicable",
        "primary_day_rule": "civil_date",
        "candidates": [],
        "evidence_refs": [
            "design/manse-boundary-provider-policy.md",
            "hour-stem-start-rules.csv",
        ],
    }
    if birth_time_missing or local_time is None:
        return profile

    touches_ja_hour = is_ja_hour_time(local_time) or time_range_touches_ja_hour(time_range)
    if not touches_ja_hour:
        return profile

    if time_range and time_range_touches_ja_hour(time_range):
        profile["status"] = "time_range_touches_ja_hour"
        profile["candidates"].append(
            {
                "candidate": "range_requires_ja_hour_review",
                "reason": "입력한 출생 시간 범위가 자시 구간과 겹칩니다.",
                "primary_day_pillar": asdict(primary_day),
                "primary_hour_pillar": asdict(primary_hour) if primary_hour else None,
            }
        )
        return profile

    if local_time.hour == 23:
        alternate_date = local_date + timedelta(days=1)
        alternate_day = day_pillar(tables, alternate_date)
        alternate_hour = hour_pillar(tables, local_time, alternate_day.stem_code)
        profile["status"] = "late_ja_alternate_day_candidate"
        profile["candidates"].append(
            {
                "candidate": "late_ja_next_day_pillar",
                "reason": "23시대 자시는 일부 야자시 관점에서 다음 날 일주 후보를 함께 검토합니다.",
                "candidate_date": alternate_date.isoformat(),
                "day_pillar": asdict(alternate_day),
                "hour_pillar": asdict(alternate_hour) if alternate_hour else None,
            }
        )
    elif local_time.hour == 0:
        profile["status"] = "early_ja_civil_day_primary"
        profile["candidates"].append(
            {
                "candidate": "early_ja_boundary_note",
                "reason": "00시대 자시는 입력한 민간 날짜를 기본으로 유지하되 자시 경계 표시를 남깁니다.",
                "primary_day_pillar": asdict(primary_day),
                "primary_hour_pillar": asdict(primary_hour) if primary_hour else None,
            }
        )
    else:
        profile["status"] = "ja_hour_boundary"
    return profile


def normalize_gender(raw_value):
    raw_value = (raw_value or "").strip().lower()
    if raw_value in {"male", "man", "m", "남", "남성"}:
        return "male"
    if raw_value in {"female", "woman", "f", "여", "여성"}:
        return "female"
    return "unknown"


def luck_direction(tables, gender, year_stem_code):
    normalized_gender = normalize_gender(gender)
    year_yinyang = tables["stems"][year_stem_code]["yinyang"]
    if normalized_gender == "male" and year_yinyang == "yang":
        return "forward"
    if normalized_gender == "female" and year_yinyang == "yin":
        return "forward"
    if normalized_gender in {"male", "female"}:
        return "backward"
    return "unknown"


def luck_cycles(tables, dt, gender, year, month, previous_term, next_term, quality_flags):
    direction = luck_direction(tables, gender, year.stem_code)
    solar_term_source = previous_term.get("source", "unknown") if direction == "backward" else next_term.get("source", "unknown")
    if direction == "unknown":
        quality_flags.append("luck_direction_requires_gender")
        start_age_years = None
        start_age_months = None
        remainder_days = None
        cycles = []
    else:
        anchor_delta = (next_term["datetime"] - dt) if direction == "forward" else (dt - previous_term["datetime"])
        remainder_days = round(anchor_delta.total_seconds() / 86400, 4)
        start_age_years = round(anchor_delta.total_seconds() / 86400 / 3, 1)
        start_age_months = round(start_age_years * 12, 1)
        month_index = month.cycle_no - 1
        step = 1 if direction == "forward" else -1
        cycles = []
        for offset in range(1, 11):
            pillar = gapja_by_index(tables, month_index + step * offset)
            cycles.append(
                {
                    "sequence": offset,
                    "start_age_years": round(start_age_years + (offset - 1) * 10, 1),
                    "pillar": asdict(pillar),
                }
            )
    return {
        "direction": direction,
        "start_age_years": start_age_years,
        "start_age_months": start_age_months,
        "remainder_days": remainder_days,
        "calculation_basis": "exact_solar_term_delta_days_divided_by_3" if solar_term_source != "approximate_static_boundary" else "approximate_solar_term_delta_days_divided_by_3",
        "solar_term_source": solar_term_source,
        "decade_cycles": cycles,
    }


def pillar_positions(year, month, day, hour):
    return [
        ("year", year),
        ("month", month),
        ("day", day),
        ("hour", hour),
    ]


def enrich_keywords(value):
    return [item for item in (value or "").split(";") if item]


def twelve_life_stage_signals(tables, day, year, month, hour):
    rows = {
        (row["day_stem_code"], row["branch_code"]): row
        for row in tables.get("twelve_life_stage_map", [])
    }
    signals = []
    for position, pillar in pillar_positions(year, month, day, hour):
        if pillar is None:
            continue
        row = rows.get((day.stem_code, pillar.branch_code))
        if not row:
            continue
        stage = tables.get("twelve_life_stages", {}).get(row["stage_code"], {})
        signals.append(
            {
                "position": position,
                "branch_code": pillar.branch_code,
                "stage_code": row["stage_code"],
                "stage_ko": row["stage_ko"],
                "stage_order": int(row["stage_order"]),
                "direction": row["direction"],
                "energy_state": stage.get("energy_state", ""),
                "life_metaphor": stage.get("life_metaphor", ""),
                "positive_keywords": enrich_keywords(stage.get("positive_keywords", "")),
                "caution_keywords": enrich_keywords(stage.get("caution_keywords", "")),
                "evidence_refs": ["twelve-life-stage-map.csv", "twelve-life-stages.csv", row["source_ref"]],
            }
        )
    return signals


def shinsal_group_for_branch(tables, branch_code):
    for row in tables.get("twelve_shinsal_rules", []):
        if branch_code in row["base_branches"].split(";"):
            return row
    return None


def twelve_shinsal_signals(tables, base_position, base_branch_code, year, month, day, hour):
    group = shinsal_group_for_branch(tables, base_branch_code)
    if not group:
        return []
    signals = []
    for position, pillar in pillar_positions(year, month, day, hour):
        if pillar is None:
            continue
        shinsal_code = next(
            (
                code
                for code in [
                    "geopsal",
                    "jaesal",
                    "cheonsal",
                    "jisal",
                    "nyeonsal",
                    "wolsal",
                    "mangsin",
                    "jangseong",
                    "banan",
                    "yeokma",
                    "yukhae",
                    "hwagae",
                ]
                if group.get(code) == pillar.branch_code
            ),
            None,
        )
        if not shinsal_code:
            continue
        detail = tables.get("twelve_shinsal", {}).get(shinsal_code, {})
        signals.append(
            {
                "base_position": base_position,
                "base_branch_code": base_branch_code,
                "triad_group": group["triad_group"],
                "target_position": position,
                "target_branch_code": pillar.branch_code,
                "shinsal_code": shinsal_code,
                "shinsal_ko": detail.get("ko_name", shinsal_code),
                "energy_domain": detail.get("energy_domain", ""),
                "modern_read": detail.get("modern_read", ""),
                "positive_keywords": enrich_keywords(detail.get("positive_keywords", "")),
                "caution_keywords": enrich_keywords(detail.get("caution_keywords", "")),
                "evidence_refs": ["twelve-shinsal-rules.csv", "twelve-shinsal.csv", group["source_ref"]],
            }
        )
    return signals


def add_special_star(signals, tables, code, positions, rule):
    detail = tables.get("special_stars", {}).get(code, {})
    signals.append(
        {
            "special_star_code": code,
            "special_star_ko": detail.get("ko_name", code),
            "star_family": detail.get("star_family", ""),
            "positions": positions,
            "modern_domain": detail.get("modern_domain", ""),
            "positive_keywords": enrich_keywords(detail.get("positive_keywords", "")),
            "caution_keywords": enrich_keywords(detail.get("caution_keywords", "")),
            "rule_summary": rule.get("rule_summary", ""),
            "evidence_refs": ["special-star-rules.csv", "special-stars.csv", rule.get("source_ref", "")],
        }
    )


def special_star_signals(tables, year, month, day, hour):
    positions = {position: pillar for position, pillar in pillar_positions(year, month, day, hour) if pillar is not None}
    signals = []
    for rule in tables.get("special_star_rules", []):
        code = rule["special_star_code"]
        base_keys = rule["base_key"].split(";")
        targets = rule["target_values"].split(";")
        matched_positions = []

        if code in {"cheon-eul-gwiin", "hakdang-gwiin"} and day.stem_code in base_keys:
            matched_positions = [
                position
                for position, pillar in positions.items()
                if pillar.branch_code in targets
            ]
        elif code == "woldok-gwiin" and month.branch_code in base_keys:
            matched_positions = [
                position
                for position, pillar in positions.items()
                if pillar.stem_code in targets
            ]
        elif code == "baekho-daesal":
            target_branch = tables["branch_order"][(branch_index(tables, year.branch_code) + 4) % 12]
            if day.branch_code == target_branch:
                matched_positions = ["day"]
        elif code == "gwigang-sal" and f"{day.stem_code}-{day.branch_code}" in targets:
            matched_positions = ["day"]
        elif code == "hyeonchim-sal":
            glyphs = set(targets)
            day_glyphs = set(day.hanja)
            if glyphs & day_glyphs:
                matched_positions = ["day"]

        if matched_positions:
            add_special_star(signals, tables, code, matched_positions, rule)
    return signals


def auxiliary_signals(tables, year, month, day, hour):
    return {
        "policy": "candidate_reference_not_deterministic_judgment",
        "twelve_life_stages": twelve_life_stage_signals(tables, day, year, month, hour),
        "twelve_shinsal": {
            "year_base": twelve_shinsal_signals(tables, "year", year.branch_code, year, month, day, hour),
            "day_base": twelve_shinsal_signals(tables, "day", day.branch_code, year, month, day, hour),
        },
        "special_stars": special_star_signals(tables, year, month, day, hour),
        "quality_flags": ["auxiliary_stars_candidate_not_final_judgment"],
        "evidence_refs": [
            "twelve-life-stage-map.csv",
            "twelve-shinsal-rules.csv",
            "special-star-rules.csv",
        ],
    }


def _pillar_summary(pillar):
    if pillar is None:
        return None
    payload = asdict(pillar) if not isinstance(pillar, dict) else pillar
    return {"hanja": payload.get("hanja"), "ko": payload.get("ko"), "stem_code": payload.get("stem_code"), "branch_code": payload.get("branch_code")}


def _term_payload(term):
    return {
        "term_ko": term["term_ko"],
        "branch_code": term["branch_code"],
        "datetime": term["datetime"].isoformat(),
        "source": term.get("source", "unknown"),
        "source_file": term.get("source_file", ""),
    }


def solar_term_boundary_candidates(tables, dt, year, month, previous_term, next_term, quality_flags):
    nearest_delta = min(
        abs((dt - previous_term["datetime"]).total_seconds()),
        abs((next_term["datetime"] - dt).total_seconds()),
    ) / 3600
    if nearest_delta > BOUNDARY_CANDIDATE_HOURS:
        return []

    quality_flags.append("solar_term_boundary_candidate_scope")
    if abs((dt - previous_term["datetime"]).total_seconds()) <= abs((next_term["datetime"] - dt).total_seconds()):
        before_dt = previous_term["datetime"] - timedelta(minutes=1)
        after_dt = previous_term["datetime"] + timedelta(minutes=1)
        boundary = previous_term
    else:
        before_dt = next_term["datetime"] - timedelta(minutes=1)
        after_dt = next_term["datetime"] + timedelta(minutes=1)
        boundary = next_term

    candidates = []
    for role, candidate_dt in (("before", before_dt), ("after", after_dt)):
        candidate_flags = []
        candidate_year = year_pillar(tables, candidate_dt, candidate_flags)
        candidate_month, candidate_prev, candidate_next = month_pillar(tables, candidate_dt, candidate_year.stem_code, candidate_flags)
        candidates.append(
            {
                "role": role,
                "datetime": candidate_dt.isoformat(),
                "year": _pillar_summary(candidate_year),
                "month": _pillar_summary(candidate_month),
                "previous_term": _term_payload(candidate_prev),
                "next_term": _term_payload(candidate_next),
            }
        )
    primary = {"year": _pillar_summary(year), "month": _pillar_summary(month)}
    distinct = {
        (item["year"]["hanja"], item["month"]["hanja"])
        for item in candidates
        if item["year"] and item["month"]
    }
    distinct.add((primary["year"]["hanja"], primary["month"]["hanja"]))
    if len(distinct) < 2:
        quality_flags.remove("solar_term_boundary_candidate_scope")
        return []
    return {
        "status": "candidate",
        "window_hours": BOUNDARY_CANDIDATE_HOURS,
        "boundary": _term_payload(boundary),
        "primary": primary,
        "candidates": candidates,
        "evidence_refs": [
            "solar-term-month-boundaries.csv",
            "design/solar-term-verification-source-policy.md",
        ],
    }


def calculate_chart(
    birth_date,
    birth_time="",
    gender="unknown",
    birth_place="",
    timezone=DEFAULT_TIMEZONE,
    calendar_type="solar",
    tables=None,
    allow_unconverted_lunar=False,
    is_lunar_leap_month=None,
    require_verified_solar_terms=False,
):
    """require_verified_solar_terms=True → 근사 절기가 감지되면 fail-closed."""
    tables = tables or load_tables()
    quality_flags = []
    calendar_conversion = None
    if calendar_type != "solar":
        if not allow_unconverted_lunar:
            calendar_conversion = convert_lunar_input(birth_date, is_lunar_leap_month)
            birth_date = calendar_conversion["solar_birth_date"]
            quality_flags.extend(["calendar_conversion_required", "calendar_conversion_verified"])
            if calendar_conversion.get("is_lunar_leap_month"):
                quality_flags.append("lunar_leap_month_selected")
            if calendar_conversion.get("leap_month_auto_resolved"):
                quality_flags.append("lunar_leap_month_auto_resolved")
        else:
            quality_flags.append("calendar_conversion_required")
            quality_flags.append("lunar_input_not_converted")

    local_time, time_range, time_flags = parse_birth_time(birth_time)
    quality_flags.extend(time_flags)
    birth_time_missing = local_time is None
    local_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
    representative_time = local_time
    if local_time is None:
        representative_time = time(12, 0)
        quality_flags.append("noon_placeholder_for_missing_time")
        quality_flags.append("hour_pillar_omitted")
    tz = parse_timezone(timezone)
    dt = datetime.combine(local_date, representative_time, tzinfo=tz)
    timezone_quality = timezone_quality_profile(tz, timezone, birth_place, dt, quality_flags)

    year = year_pillar(tables, dt, quality_flags)
    month, previous_term, next_term = month_pillar(tables, dt, year.stem_code, quality_flags)
    solar_term_quality = solar_term_quality_profile(previous_term, next_term, dt)
    if solar_term_quality["source_quality"] == "approximate" and solar_term_quality["boundary_risk_level"] in {"critical", "high", "medium"}:
        quality_flags.append("approximate_solar_term_boundary_risk")
    if solar_term_quality["boundary_risk_level"] == "critical":
        quality_flags.append("solar_term_boundary_within_6h")
    day = day_pillar(tables, local_date)
    hour = None if birth_time_missing else hour_pillar(tables, local_time, day.stem_code)
    ja_policy = ja_hour_policy_profile(tables, local_date, local_time, time_range, day, hour, birth_time_missing)
    if ja_policy["status"] != "not_applicable":
        quality_flags.append("near_ja_hour_boundary")
    if ja_policy["status"] == "late_ja_alternate_day_candidate":
        quality_flags.append("late_ja_hour_alternate_day_candidate")
    if ja_policy["status"] == "time_range_touches_ja_hour":
        quality_flags.extend(["birth_time_range_touches_ja_hour", "ja_hour_candidate_only"])
    luck = luck_cycles(tables, dt, gender, year, month, previous_term, next_term, quality_flags)
    boundary_scope = solar_term_boundary_candidates(tables, dt, year, month, previous_term, next_term, quality_flags)

    if require_verified_solar_terms and (
        "approximate_solar_terms" in quality_flags or "approximate_solar_term_boundary_risk" in quality_flags
    ):
        raise ValueError(
            "verified solar terms required: set SAJU_SOLAR_TERM_PROVIDER_CSV to a reviewed provider (see design/solar-term-provider-naoj-1899-2101.csv)"
        )

    return {
        "engine_metadata": {
            "engine_version": ENGINE_VERSION,
            "rule_set_version": RULE_SET_VERSION,
            "day_pillar_reference": f"{DAY_REFERENCE.isoformat()}:{DAY_REFERENCE_HANJA}",
            "solar_term_sources": sorted(
                {
                    row.get("source", "unknown")
                    for row in tables["verified_solar_terms"]
                    if row.get("source")
                }
            ),
            "solar_term_authority": "naoj_hko_utc",
            "lunar_python_role": "conversion_candidate_only",
        },
        "input": {
            "birth_date": birth_date,
            "birth_time": birth_time,
            "representative_time": representative_time.strftime("%H:%M"),
            "time_range": [value.strftime("%H:%M") for value in time_range] if time_range else None,
            "calendar_type": calendar_type,
            "birth_place": birth_place,
            "timezone": timezone,
            "gender": normalize_gender(gender),
            "hour_pillar_included": not birth_time_missing,
        },
        "calendar_conversion": calendar_conversion,
        "four_pillars": {
            "year": asdict(year),
            "month": asdict(month),
            "day": asdict(day),
            "hour": asdict(hour) if hour else None,
        },
        "solar_terms": {
            "previous": _term_payload(previous_term),
            "next": _term_payload(next_term),
        },
        "solar_term_quality": solar_term_quality,
        "timezone_quality": timezone_quality,
        "ja_hour_policy": ja_policy,
        "boundary_candidates": boundary_scope or None,
        "luck_cycles": luck,
        "auxiliary_signals": auxiliary_signals(tables, year, month, day, hour),
        "quality_flags": sorted(set(quality_flags)),
        "precision_policy": precision_policy(quality_flags, solar_term_quality, calendar_type),
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate a first-pass saju manse chart.")
    parser.add_argument("--birth-date", required=True)
    parser.add_argument("--birth-time", default="")
    parser.add_argument("--gender", default="unknown")
    parser.add_argument("--birth-place", default="")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--calendar-type", default="solar")
    lunar_group = parser.add_mutually_exclusive_group()
    lunar_group.add_argument("--lunar-leap-month", action="store_true")
    lunar_group.add_argument("--lunar-normal-month", action="store_true")
    lunar_group.add_argument("--lunar-leap-month-unspecified", action="store_true")
    parser.add_argument(
        "--allow-unconverted-lunar",
        action="store_true",
        help="review-only mode: calculate with explicit lunar-not-converted quality flags instead of failing closed",
    )
    args = parser.parse_args()
    try:
        result = calculate_chart(
            birth_date=args.birth_date,
            birth_time=args.birth_time,
            gender=args.gender,
            birth_place=args.birth_place,
            timezone=args.timezone,
            calendar_type=args.calendar_type,
            allow_unconverted_lunar=args.allow_unconverted_lunar,
            is_lunar_leap_month=(
                True if args.lunar_leap_month else
                False if args.lunar_normal_month else
                None
            ),
        )
    except LunarLeapMonthAmbiguous as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": "LUNAR_LEAP_MONTH_AMBIGUOUS",
                    "message": str(error),
                    "candidates": error.candidates,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(3) from error
    except ValueError as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": "CALENDAR_CONVERSION_REQUIRED",
                    "message": str(error),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from error
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
