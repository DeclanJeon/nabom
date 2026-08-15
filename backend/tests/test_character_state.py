"""Current visual condition can rise, strain, recover, or remain steady."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nabom-api" / "app"))

import character_state  # noqa: E402


def entry(day: str, value: int) -> dict:
    return {"date": day, "mood": value, "energy": value, "satisfaction": value, "status": "active"}


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def run():
    require(character_state.derive_condition_state([])["state"] == "steady", "sparse data must be steady")
    strained = character_state.derive_condition_state([entry(f"2026-08-{i:02d}", 2) for i in range(1, 8)])
    require(strained["state"] == "strained", strained)
    rising = character_state.derive_condition_state(
        [entry(f"2026-08-{i:02d}", 2) for i in range(1, 8)]
        + [entry(f"2026-08-{i:02d}", 5) for i in range(8, 15)]
    )
    require(rising["state"] == "recovering", rising)
    improving = character_state.derive_condition_state(
        [entry(f"2026-08-{i:02d}", 3) for i in range(1, 8)]
        + [entry(f"2026-08-{i:02d}", 5) for i in range(8, 15)]
    )
    require(improving["state"] == "rising", improving)
    require(character_state.condition_prompt("strained").startswith("smaller posture"), "strained prompt")
    require(character_state.condition_prompt("recovering").startswith("careful upright"), "recovery prompt")
    seed_a = character_state.appearance_seed("profile-a", "version-1", 5, "steady")
    seed_b = character_state.appearance_seed("profile-a", "version-1", 5, "steady")
    require(seed_a == seed_b and len(seed_a) == 16, "appearance seed must be stable")
    held = character_state.derive_condition_state(
        [entry("2026-08-01", 2), entry("2026-08-02", 2), entry("2026-08-03", 2)],
        previous_state="recovering",
    )
    require(held["state"] == "recovering", held)
    evidence_adjusted = character_state.derive_condition_state(
        [entry(f"2026-08-{i:02d}", 3) for i in range(1, 8)],
        evidence=[{"signals": [{"direction": "negative", "strength": 0.25}]}] * 4,
    )
    require(evidence_adjusted["state"] == "strained", evidence_adjusted)
    print("character-state: PASS")


if __name__ == "__main__":
    run()
