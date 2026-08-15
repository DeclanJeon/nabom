#!/usr/bin/env bash
# 상태 변형 카탈로그: 10 성장 방식 × 2 성별 × 10 단계 × 4 상태 = 800 PNG.
# STATE_FILTER=rising|steady|strained|recovering 로 일부 상태만 재개할 수 있다.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
IMAGEN="${CODEX_IMAGEN:-$HOME/.hermes/skills/codex-imagen/scripts/codex-imagen.mjs}"
KEY="${CHROMA_KEY:-$HOME/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py}"
RAW="$ROOT/docs/tmp/imagegen/characters/state-raw"
CUT="$ROOT/docs/tmp/imagegen/characters/state-cut"
PUB="$ROOT/frontend/public/characters/stage"
SYMBOLS="$ROOT/docs/tmp/imagegen/characters/stage-symbols.tsv"
mkdir -p "$RAW" "$CUT" "$PUB"

STAGE_DAYS=(0 7 14 21 28 35 42 49 56 63)
STATES=(rising steady strained recovering)
FILTER="${STATE_FILTER:-all}"

# 상태별 포즈·표정·패션 방향. 실패나 벌처럼 보이지 않게 한다.
declare -A STATE_PROMPT=(
  [rising]="open posture, clear eyes, a slightly forward gesture, neatly added personal detail"
  [steady]="relaxed centered posture, calm eyes, familiar clothing and a comfortable gesture"
  [strained]="smaller posture, lowered shoulders, thoughtful tired eyes, simpler slightly rumpled clothing, gentle not defeated"
  [recovering]="careful upright posture, soft warm eyes, one small restored clothing detail, a nearby comforting light or rest object"
)
declare -A STYLE=(
  [pathfinder]="curious path opener, sage green, trail marker"
  [weaver]="flexible connector, forest green and lavender, thread and bridge"
  [brightener]="warm atmosphere brightener, terracotta and apricot, gentle flame"
  [lighter]="quiet warmth sharer, candle gold and cream, small lamps"
  [steadier]="calm place keeper, clay and oatmeal, seed and old tree"
  [gardener]="careful tender gardener, moss and earth green, growing plants"
  [decider]="clear standard setter, muted gold and stone gray, compass and plan"
  [polisher]="precise refiner, silver and pearl, mirror and gem"
  [observer]="deep flow reader, mist and slate blue, water and night sky"
  [seer]="quiet deep illuminator, navy and silver, pond and star chart"
)

symbol_for() { awk -F'\t' -v c="$1" -v s="$2" '$1==c && $2==s {print $3}' "$SYMBOLS" | head -1; }

render_one() {
  local code="$1" gender="$2" stage="$3" state="$4"
  local key="${code}_${gender}_$(printf '%02d' "$stage")_${state}"
  mkdir -p "$PUB/$code/$gender"; local dest="$PUB/$code/$gender/${key}.png"
  [ -s "$dest" ] && { echo "SKIP $key"; return; }
  local days="${STAGE_DAYS[$((stage-1))]}" symbol="$(symbol_for "$code" "$stage")"
  local who="a Korean chibi person with a soft unisex look"
  [ "$gender" = male ] && who="a Korean chibi man"
  [ "$gender" = female ] && who="a Korean chibi woman"
  local prompt="$RAW/${key}.txt" raw="$RAW/${key}.png" cut="$CUT/${key}.png"
  cat > "$prompt" <<EOF
Use case: NABOM personal growth character sprite
Asset: stage $stage of 10, condition $state, ${days}+ recorded days
Create one cute two-head-tall $who. This is the same identity family as the other stages. Style identity: ${STYLE[$code]}. Stage symbol: $symbol. Current visual direction: ${STATE_PROMPT[$state]}.
The character must show the condition through pose, expression, hairstyle detail, clothing detail, and light while remaining kind and everyday. No game level, no combat, no judgment.
Background: flat #00ff00 chroma key, no floor, shadow, scenery, gradient, reflection, or text.
Composition: centered full-body, square 1:1, generous padding, clean separated silhouette.
Style: premium Korean paper-cut chibi illustration, coherent character design, warm editorial art.
Constraints: one person only, no text, no watermark, no animals, no mythical beings, no weapons, no fortune-telling imagery, no Chinese characters.
EOF
  echo "GEN $key"
  node "$IMAGEN" --timeout 600 --retries 2 --quiet --output "$raw" --prompt-file "$prompt"
  python3 "$KEY" --input "$raw" --out "$cut" --key-color '#00ff00' --auto-key corners --soft-matte --despill --force
  python3 - "$cut" "$dest" <<'PY'
from pathlib import Path
import sys
from PIL import Image
src, dest = Path(sys.argv[1]), Path(sys.argv[2])
im = Image.open(src); im.thumbnail((512,512), Image.Resampling.LANCZOS)
im.save(dest, format='PNG', optimize=True)
PY
}

for code in pathfinder weaver brightener lighter steadier gardener decider polisher observer seer; do
  for gender in male female; do
    for stage in $(seq 1 10); do
      for state in "${STATES[@]}"; do
        [ "$FILTER" = all ] || [ "$FILTER" = "$state" ] || continue
        render_one "$code" "$gender" "$stage" "$state"
      done
    done
  done
done
printf 'state PNG complete: %s files\n' "$(find "$PUB" -maxdepth 1 -name '*_rising.png' -o -name '*_steady.png' -o -name '*_strained.png' -o -name '*_recovering.png' | wc -l)"
