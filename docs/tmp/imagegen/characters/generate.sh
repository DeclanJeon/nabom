#!/usr/bin/env bash
# Generate NABOM profile chibis via Codex OAuth imagen.
# Skip a code if its raw PNG already exists.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
IMAGEN="${CODEX_IMAGEN:-$HOME/.hermes/skills/codex-imagen/scripts/codex-imagen.mjs}"
KEY="${CHROMA_KEY:-$HOME/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py}"
RAW="$HERE/raw"
CUT="$HERE/cutout"
PROMPT="$HERE/prompts"
PUB="$ROOT/frontend/public/characters"
CODES=(pathfinder brightener steadier decider observer)

mkdir -p "$RAW" "$CUT" "$PUB"

gen_one() {
  local code="$1"
  local dest="$RAW/${code}.png"
  if [ -s "$dest" ]; then
    echo "SKIP $code (raw exists)"
    return 0
  fi
  echo "GEN $code"
  node "$IMAGEN" \
    --timeout 600 \
    --retries 2 \
    --quiet \
    --output "$dest" \
    --prompt-file "$PROMPT/${code}.txt"
}

cut_one() {
  local code="$1"
  python3 "$KEY" \
    --input "$RAW/${code}.png" \
    --out "$CUT/${code}.png" \
    --key-color "#00ff00" \
    --auto-key corners \
    --soft-matte \
    --despill \
    --force
}

for code in "${CODES[@]}"; do
  gen_one "$code"
  cut_one "$code"
done

python3 - "$CUT" "$PUB" <<'PY'
from pathlib import Path
import sys
from PIL import Image

cut = Path(sys.argv[1])
pub = Path(sys.argv[2])
pub.mkdir(parents=True, exist_ok=True)
for src in sorted(cut.glob("*.png")):
    im = Image.open(src)
    im.thumbnail((768, 768), Image.Resampling.LANCZOS)
    dest = pub / src.name
    im.save(dest, format="PNG", optimize=True)
    print(f"INSTALL {dest.name} {dest.stat().st_size}")
PY
