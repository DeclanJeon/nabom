"""SMTP mailer. Reads SMTP_* from the process env or an env file.

The env file path is NABOM_SMTP_ENV_FILE. Only SMTP_* and NABOM_PUBLIC_APP_URL
are imported. Other secrets in that file are ignored.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

# Google 전용 로그인에서는 이메일 발송이 필요 없다. NABOM_MAIL_ENABLED=1을
# 명시적으로 켜지 않는 한 어떤 메일도 발송하지 않는다.
DEFAULT_MAIL_ENABLED = False
DEFAULT_SMTP_ENV_FILE = "/home/declan/Documents/Develop/Project/pons_p2p/ponslink-api-infra/.env"
SMTP_KEYS = (
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASS",
    "SMTP_FROM",
    "SMTP_SECURE",
    "NABOM_PUBLIC_APP_URL",
)


class MailError(RuntimeError):
    """SMTP delivery failure."""


def mail_enabled() -> bool:
    """Opt-in gate. Default OFF: NABOM never sends email unless explicitly enabled."""
    value = os.environ.get("NABOM_MAIL_ENABLED", "")
    if value.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return DEFAULT_MAIL_ENABLED


def _parse_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key not in SMTP_KEYS:
            continue
        values[key] = value.strip().strip("'").strip('"')
    return values


def smtp_settings() -> dict[str, str]:
    settings = {key: os.environ.get(key, "") for key in SMTP_KEYS}
    env_file = os.environ.get("NABOM_SMTP_ENV_FILE", DEFAULT_SMTP_ENV_FILE)
    if env_file and Path(env_file).is_file():
        loaded = _parse_env_file(env_file)
        for key, value in loaded.items():
            if not settings.get(key):
                settings[key] = value
    return settings


def smtp_configured(settings: dict[str, str] | None = None) -> bool:
    current = settings or smtp_settings()
    return bool(current.get("SMTP_HOST") and current.get("SMTP_USER") and current.get("SMTP_PASS"))


def send_mail(*, to_address: str, subject: str, text_body: str) -> None:
    if not mail_enabled():
        raise MailError("mail_disabled")
    settings = smtp_settings()
    if not smtp_configured(settings):
        raise MailError("smtp_not_configured")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.get("SMTP_FROM") or settings["SMTP_USER"]
    message["To"] = to_address
    message.set_content(text_body)
    host = settings["SMTP_HOST"]
    port = int(settings.get("SMTP_PORT") or "587")
    user = settings["SMTP_USER"]
    password = settings["SMTP_PASS"]
    secure = settings.get("SMTP_SECURE", "false").strip().lower() in {"1", "true", "yes"}
    try:
        if secure or port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20) as client:
                client.login(user, password)
                client.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as client:
                client.ehlo()
                client.starttls()
                client.login(user, password)
                client.send_message(message)
    except Exception as exc:  # noqa: BLE001
        raise MailError("smtp_send_failed") from exc


def verify_smtp() -> dict[str, str]:
    if not mail_enabled():
        raise MailError("mail_disabled")
    settings = smtp_settings()
    if not smtp_configured(settings):
        raise MailError("smtp_not_configured")
    host = settings["SMTP_HOST"]
    port = int(settings.get("SMTP_PORT") or "587")
    user = settings["SMTP_USER"]
    password = settings["SMTP_PASS"]
    secure = settings.get("SMTP_SECURE", "false").strip().lower() in {"1", "true", "yes"}
    try:
        if secure or port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20) as client:
                client.login(user, password)
        else:
            with smtplib.SMTP(host, port, timeout=20) as client:
                client.ehlo()
                client.starttls()
                client.login(user, password)
    except Exception as exc:  # noqa: BLE001
        raise MailError("smtp_login_failed") from exc
    return {"host": host, "port": str(port), "user": user, "from": settings.get("SMTP_FROM") or user}

def send_recovery_mail(to_address: str, token: str) -> None:
    base = smtp_settings().get("NABOM_PUBLIC_APP_URL") or "http://127.0.0.1:4174"
    body = (
        "나봄 계정 비밀번호 재설정 요청을 받았습니다.\n\n"
        f"복구 토큰: {token}\n"
        f"재설정 화면: {base}/index.html#/recovery\n\n"
        "요청하지 않았다면 이 메일을 무시하세요.\n"
    )
    send_mail(to_address=to_address, subject="[나봄] 비밀번호 재설정", text_body=body)


def send_verify_email_mail(to_address: str, token: str) -> None:
    """계정 가입 시 이메일 주소 확인 링크를 발송한다."""
    base = smtp_settings().get("NABOM_PUBLIC_APP_URL") or "http://127.0.0.1:4174"
    body = (
        "나봄에 오신 것을 환영합니다.\n\n"
        "이메일 주소를 확인하려면 아래 주소를 열어주세요.\n"
        f"{base}/verify-email?token={token}\n\n"
        "요청하지 않았다면 이 메일을 무시하세요.\n"
    )
    send_mail(to_address=to_address, subject="[나봄] 이메일 확인", text_body=body)


def send_weekly_mirror_ready_mail(to_address: str, nickname: str = "") -> None:
    """주간 회고가 준비됐음을 알린다."""
    base = smtp_settings().get("NABOM_PUBLIC_APP_URL") or "http://127.0.0.1:4174"
    greeting = f"{nickname}님, " if nickname else ""
    body = (
        f"{greeting}이번 주 기록을 바탕으로 회고가 준비됐어요.\n\n"
        f"지금 확인하기: {base}/mirror\n\n"
        "오늘의 나는, 어제의 나와 조금 다르니까.\n"
    )
    send_mail(to_address=to_address, subject="[나봄] 이번 주의 회고가 준비됐어요", text_body=body)
