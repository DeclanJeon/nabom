#!/usr/bin/env bash
# 완성된 stage PNG를 GIF로 파생한다. PNG 생성과 독립적으로 중단/재개 가능.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
PUB="$ROOT/frontend/public/characters/stage"
PYTHON="${NABOM_PYTHON:-$ROOT/backend/.venv/bin/python}"
export PYTHONPATH="$ROOT/backend/nabom-api/app"

for png in "$PUB"/*/*.png; do
  [ -s "$png" ] || continue
  gif="${png%.png}.gif"
  [ -s "$gif" ] && continue
  "$PYTHON" - "$png" "$gif" <<'PY'
from pathlib import Path
import sys
import character_visual

png = Path(sys.argv[1])
gif = Path(sys.argv[2])
if character_visual.build_character_gif(png, gif):
    print("GIF", gif.name)
else:
    raise SystemExit(f"GIF failed: {png}")
PY
done
printf 'GIF catalog complete: %s files\n' "$(find "$PUB" -mindepth 1 -name '*.gif' | wc -l)"
