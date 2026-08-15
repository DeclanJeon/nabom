#!/usr/bin/env bash
# NABOM 데이터 백업 — SQLite/PostgreSQL 공용.
# 사용법:
#   ./backup.sh                      # 백업 실행 (기본)
#   ./backup.sh --dry-run            # 실제 복사 없이 대상 경로만 출력
#   ./backup.sh --driver sqlite      # 강제 sqlite (기본)
#   ./backup.sh --driver postgres    # pg_dump 사용 (DATABASE_URL 필요)
#   BACKUP_DIR=/path ./backup.sh     # 출력 디렉터리 지정
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DRIVER="${NABOM_STORE_DRIVER:-sqlite}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
STAMP="$(date +%Y%m%dT%H%M%SZ)"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --driver) DRIVER="$2"; shift 2 ;;
    *) echo "알 수 없는 인자: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$BACKUP_DIR"
echo "NABOM backup start — driver=$DRIVER"

if [ "$DRIVER" = "postgres" ]; then
  DB_URL="${DATABASE_URL:?DATABASE_URL required for postgres backup}"
  DEST="$BACKUP_DIR/nabom-$STAMP.sql"
  if [ "$DRY_RUN" = "1" ]; then
    echo "  [dry-run] pg_dump '$DB_URL' → $DEST"
  else
    pg_dump "$DB_URL" -f "$DEST"
    echo "  -> $DEST ($(wc -c < "$DEST") bytes)"
  fi
else
  # SQLite: NABOM_STORE_PATH 지정 시 해당 파일, 기본은 e2e/로컬 경로 후보 탐색
  SRC="${NABOM_STORE_PATH:-}"
  if [ -z "$SRC" ] || [ ! -f "$SRC" ]; then
    for candidate in "$ROOT/backend/data/nabom.db" "$ROOT/data/nabom.db" /tmp/nabom-e2e/nabom.db; do
      if [ -f "$candidate" ]; then SRC="$candidate"; break; fi
    done
  fi
  if [ -z "$SRC" ] || [ ! -f "$SRC" ]; then
    echo "SQLite 파일을 찾을 수 없습니다 (NABOM_STORE_PATH 또는 후보 경로 확인)" >&2
    exit 1
  fi
  DEST="$BACKUP_DIR/nabom-$(basename "$SRC" .db)-$STAMP.db"
  if [ "$DRY_RUN" = "1" ]; then
    echo "  [dry-run] cp '$SRC' → $DEST"
  else
    # WAL 모드 대비: 파일 + -wal/-shm 함께 복사하면 일관성이 유지된다.
    cp "$SRC" "$DEST"
    [ -f "$SRC-wal" ] && cp "$SRC-wal" "$DEST-wal"
    [ -f "$SRC-shm" ] && cp "$SRC-shm" "$DEST-shm"
    echo "  -> $DEST ($(wc -c < "$DEST") bytes)"
  fi
fi

echo "NABOM backup done — $BACKUP_DIR"
