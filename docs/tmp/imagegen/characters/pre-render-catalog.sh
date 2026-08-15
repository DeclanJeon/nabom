#!/usr/bin/env bash
# 프리렌더 카탈로그: 5 아키타입 × 2 성별 × 10 단계 = 100개 캐릭터.
# 같은 파일이 있으면 스킵 → 중단/재개 안전. 1회 생성 후 모든 유저가 정적 서빙.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
IMAGEN="${CODEX_IMAGEN:-$HOME/.hermes/skills/codex-imagen/scripts/codex-imagen.mjs}"
KEY="${CHROMA_KEY:-$HOME/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py}"
RAW="$ROOT/docs/tmp/imagegen/characters/catalog-raw"
CUT="$ROOT/docs/tmp/imagegen/characters/catalog-cut"
PUB="$ROOT/frontend/public/characters/stage"
mkdir -p "$RAW" "$CUT" "$PUB"

# 아키타입별 단계 모티프/스타일 변화 (일상어 — 게임 용어 아님)
# 10천간: 양 5 (기존) + 음 5 (weaver/lighter/gardener/polisher/seer)
declare -A MOTIF=(
  [pathfinder]="a growing trail marker"
  [weaver]="threads weaving together into a larger pattern"
  [brightener]="a small flame that grows brighter"
  [lighter]="a small candle glow that becomes a warm room"
  [steadier]="a growing tree with deeper roots"
  [gardener]="a seedling that becomes a tended garden"
  [decider]="a compass that becomes more precise"
  [polisher]="a rough stone that becomes a polished gem"
  [observer]="a drop of water that becomes a deep sea"
  [seer]="a still pond that reflects the whole sky"
)
declare -A TONE=(
  [pathfinder]="curious and beginning"
  [weaver]="flexible and harmonizing"
  [brightener]="bright and expressive"
  [lighter]="delicate and warm"
  [steadier]="calm and caring"
  [gardener]="meticulous and nurturing"
  [decider]="clear and decisive"
  [polisher]="refined and precise"
  [observer]="deep and observant"
  [seer]="quiet and penetrating"
)
declare -A PALETTE=(
  [pathfinder]="sage green, leaf-tea, warm ivory"
  [weaver]="forest green, soft beige, warm cream"
  [brightener]="terracotta, apricot, warm cream"
  [lighter]="candle gold, blush, cream"
  [steadier]="warm clay, oatmeal, soft brown"
  [gardener]="earth green, moss, warm tan"
  [decider]="muted gold, stone gray, warm white"
  [polisher]="silver, pearl, cool white"
  [observer]="mist sage, slate blue, paper ivory"
  [seer]="deep navy, silver, night mist"
)

# 기록일수 → 단계 임계값 (character_visual.STAGE_DAYS와 동일)
STAGE_DAYS=(0 7 14 21 28 35 42 49 56 63)

# 아키타입×단계 심볼 테이블 (stage-symbols.tsv): {code}\t{stage}\t{symbol_en}
SYMBOLS_TSV="$(cd "$(dirname "$0")" && pwd)/stage-symbols.tsv"

symbol_for() {
  local code="$1" stage="$2"
  awk -F'\t' -v c="$code" -v s="$stage" '$1==c && $2==s {print $3}' "$SYMBOLS_TSV" | head -1
}

prompt_for() {
  local code="$1" gender="$2" stage="$3" days="$4"
  local motif="${MOTIF[$code]}"
  local tone="${TONE[$code]}"
  local palette="${PALETTE[$code]}"
  local symbol
  symbol="$(symbol_for "$code" "$stage")"
  [ -z "$symbol" ] && symbol="a small everyday item that reflects this stage"
  local who="a Korean chibi person with a soft unisex look"
  [ "$gender" = "male" ] && who="a Korean chibi man"
  [ "$gender" = "female" ] && who="a Korean chibi woman"
  # 단계가 높을수록 '성숙/완성' 표현 강화
  local maturity="fresh and new"
  if [ "$stage" -ge 8 ]; then maturity="seasoned and complete"
  elif [ "$stage" -ge 5 ]; then maturity="settled and confident"
  elif [ "$stage" -ge 3 ]; then maturity="growing steadily"; fi
  cat <<EOF
Use case: stylized-concept
Asset type: NABOM profile character sprite (stage $stage of 10, ${days}+ days of records)
Primary request: A single cute two-head-tall $who, tiny body, oversized round head. Everyday human who feels $tone and $maturity. The motif is $motif, and at this growth stage the character is ${symbol}. The held item or scene symbol clearly shows this stage, still the same friendly person.
Scene/backdrop: Perfectly flat solid #00ff00 chroma-key background. No floor, shadow, gradient, reflection, texture, or scenery.
Subject: One person only. No extra characters.
Style/medium: Cute Korean illustration, paper-cut warmth, clean edges, 2-head-tall chibi.
Composition/framing: Centered full-body, generous padding, square 1:1, subject fully separated from the background.
Lighting/mood: Soft studio light, no cast shadow.
Color palette: $palette. Do not use #00ff00 anywhere on the subject.
Constraints: no text, no watermark, no animals, no mythical beasts, no armor, no weapons.
Avoid: photorealism, 3D render look, busy background, Chinese characters, fortune-telling symbols.
EOF
}

gen_one() {
  local code="$1" gender="$2" stage="$3"
  local key="${code}_${gender}_$(printf '%02d' "$stage")"
  mkdir -p "$PUB/$code/$gender"; local dest="$PUB/$code/$gender/${key}.png"
  if [ -s "$dest" ]; then
    echo "SKIP $key (exists)"
    return 0
  fi
  local days="${STAGE_DAYS[$((stage - 1))]}"
  local raw="$RAW/${key}.png" cut="$CUT/${key}.png" prompt="$RAW/${key}.txt"
  echo "GEN  $key (stage $stage, ${days}일 기준)"
  prompt_for "$code" "$gender" "$stage" "$days" > "$prompt"
  node "$IMAGEN" --timeout 600 --retries 2 --quiet --output "$raw" --prompt-file "$prompt"
  python3 "$KEY" --input "$raw" --out "$cut" --key-color "#00ff00" --auto-key corners --soft-matte --despill --force
  python3 - "$cut" "$dest" <<'PY'
from pathlib import Path
import sys
from PIL import Image
src = Path(sys.argv[1]); dest = Path(sys.argv[2])
im = Image.open(src)
im.thumbnail((512, 512), Image.Resampling.LANCZOS)
im.save(dest, format='PNG', optimize=True)
print('  ->', dest.name, dest.stat().st_size)
PY
}

echo "프리렌더 카탈로그 생성 시작 (10천간 × 2 × 10 = 200 PNG, 중단/재개 가능)"
for code in pathfinder weaver brightener lighter steadier gardener decider polisher observer seer; do
  for gender in male female; do
    for stage in $(seq 1 10); do
      gen_one "$code" "$gender" "$stage"
    done
  done
done
echo "카탈로그 완료: $(ls "$PUB"/*.png 2>/dev/null | wc -l) PNG"
