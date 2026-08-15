"""Deterministic record-reflection resolver for NABOM.

Canonical rule (from NABOM Self Loop contract):
- canonical hash input = sorted Evidence IDs + period + resolver_version only
- user ID, current time, external randomness are excluded
- hash maps deterministically to six cast values (6, 7, 8, 9), bottom-to-top
- same snapshot replay must return the same hexagram set
"""

from __future__ import annotations

import hashlib

CAST_VALUES = (6, 7, 8, 9)
RESOLVER_VERSION = "iching-reflection-v1"


def canonical_seed(evidence_ids, period, resolver_version=RESOLVER_VERSION):
    """Build the canonical seed string. Evidence IDs are sorted; period is stable."""
    sorted_ids = sorted(evidence_ids)
    return "|".join([*sorted_ids, period, resolver_version])


def seed_hash(evidence_ids, period, resolver_version=RESOLVER_VERSION):
    return hashlib.sha256(canonical_seed(evidence_ids, period, resolver_version).encode()).hexdigest()


def resolve_casts(evidence_ids, period, resolver_version=RESOLVER_VERSION):
    """Deterministic six cast values (6,7,8,9) from the canonical seed."""
    digest = hashlib.sha256(canonical_seed(evidence_ids, period, resolver_version).encode()).digest()
    return [CAST_VALUES[byte % 4] for byte in digest[:6]]


def build_reflection_request(evidence_ids, period, resolver_version=RESOLVER_VERSION):
    casts = resolve_casts(evidence_ids, period, resolver_version)
    return {
        "mode": "record_reflection",
        "casts": casts,
        "resolver": {
            "version": resolver_version,
            "input_hash": f"sha256:{seed_hash(evidence_ids, period, resolver_version)}",
        },
    }


def reflection_replay_safe(evidence_ids, period, resolver_version=RESOLVER_VERSION):
    """Return (first_request, second_request, identical_bool)."""
    first = build_reflection_request(evidence_ids, period, resolver_version)
    second = build_reflection_request(list(reversed(evidence_ids)), period, resolver_version)
    return first, second, first == second
