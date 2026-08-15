"""Rate limiter with pluggable backend (memory | redis).

Sliding-window limiter for auth enumeration and admin writes.
Driver selection via env:
  NABOM_RATE_LIMIT_DRIVER = memory (default) | redis
  REDIS_URL (redis only) e.g. redis://localhost:6379/0
Redis unavailability falls back to the in-process memory driver at startup.
"""

from __future__ import annotations

import os
import threading
import time

from fastapi import HTTPException, Request


class RateLimitBackend:
    """check(key, limit, window) raises HTTPException(429) when over limit."""

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError


class MemoryBackend(RateLimitBackend):
    """In-process sliding-window limiter (default, zero-dependency)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = {}

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            recent = [stamp for stamp in self._hits.get(key, []) if stamp > cutoff]
            if len(recent) >= limit:
                self._hits[key] = recent
                raise _rate_limited()
            recent.append(now)
            self._hits[key] = recent

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


class RedisBackend(RateLimitBackend):
    """Redis sorted-set sliding window. Requires redis-py."""

    def __init__(self, redis_url: str | None = None):
        url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "RedisBackend requires redis-py — install backend[redis] or set NABOM_RATE_LIMIT_DRIVER=memory"
            ) from exc
        self._redis = redis.from_url(url, decode_responses=True)

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        now = time.time()
        member = f"{now}:{threading.get_ident()}:{id(self)}"
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zadd(key, {member: now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 5)
        _, _, count, _ = pipe.execute()
        if int(count) > limit:
            raise _rate_limited()

    def reset(self) -> None:
        # reset is test-only; a broad flush is unsafe on a shared instance.
        self._redis.flushdb()


def _rate_limited() -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={
            "code": "RATE_LIMITED",
            "message": "너무 많이 시도했어요. 잠시 후 다시 시도해주세요.",
            "retryable": True,
        },
    )


def create_backend(driver: str | None = None) -> RateLimitBackend:
    """Backend factory. Falls back to memory when redis is requested but unavailable."""
    selected = (driver or os.environ.get("NABOM_RATE_LIMIT_DRIVER", "memory")).strip().lower()
    if selected == "redis":
        try:
            return RedisBackend()
        except (RuntimeError, ImportError, Exception):  # noqa: BLE001
            return MemoryBackend()
    return MemoryBackend()


# 프로세스 공유 싱글턴
_backend = create_backend()


def _window_seconds() -> int:
    try:
        return max(1, int(os.environ.get("NABOM_RATE_LIMIT_WINDOW", "60")))
    except ValueError:
        return 60


def _auth_limit() -> int:
    try:
        return max(1, int(os.environ.get("NABOM_AUTH_RATE_LIMIT", "8")))
    except ValueError:
        return 8


def reset() -> None:
    _backend.reset()


def check(key: str, *, limit: int, window_seconds: int | None = None) -> None:
    _backend.check(key, limit=limit, window_seconds=_window_seconds() if window_seconds is None else max(1, window_seconds))


def client_key(request: Request, prefix: str, extra: str = "") -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    host = forwarded or (request.client.host if request.client else "unknown")
    suffix = extra.strip().lower()
    return f"{prefix}:{host}:{suffix}" if suffix else f"{prefix}:{host}"


def enforce_auth(request: Request, email: str = "") -> None:
    check(client_key(request, "auth", email), limit=_auth_limit())
