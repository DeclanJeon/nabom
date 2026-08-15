"""Rate limit backend abstraction: memory default, redis contract, fallback."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-rl-", suffix=".sqlite")[1]

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "nabom-api" / "app"))

import rate_limit  # noqa: E402


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def run():
    # 1) default backend = memory
    require(isinstance(rate_limit.create_backend(), rate_limit.MemoryBackend), "default backend")

    # 2) memory window behavior
    b = rate_limit.MemoryBackend()
    for i in range(3):
        b.check("k", limit=3, window_seconds=60)
    try:
        b.check("k", limit=3, window_seconds=60)
        require(False, "4th hit should be limited")
    except Exception as exc:  # noqa: BLE001
        require(getattr(exc, "status_code", None) == 429, "expected 429")

    # 3) window expiry
    b2 = rate_limit.MemoryBackend()
    b2.check("k2", limit=1, window_seconds=0)  # zero window → immediate expiry
    b2.check("k2", limit=1, window_seconds=0)

    # 4) redis driver contract + fallback
    try:
        rl = rate_limit.create_backend("redis")
        if isinstance(rl, rate_limit.RedisBackend):
            rl.check("probe", limit=10, window_seconds=60)
            rl.reset()
            require(True, "redis live")
        else:
            require(isinstance(rl, rate_limit.MemoryBackend), "redis fallback to memory")
    except Exception as exc:  # noqa: BLE001
        require(False, f"redis path crashed: {exc}")

    # 5) module-level check still enforces 429
    rate_limit.reset()
    for i in range(2):
        rate_limit.check("mod", limit=2, window_seconds=60)
    try:
        rate_limit.check("mod", limit=2, window_seconds=60)
        require(False, "module check should 429")
    except Exception as exc:  # noqa: BLE001
        require(getattr(exc, "status_code", None) == 429, "module 429")

    print("rate-limit-driver: PASS")


if __name__ == "__main__":
    run()
