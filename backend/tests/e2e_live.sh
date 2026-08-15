#!/usr/bin/env bash
# NABOM 백엔드 라이브 E2E: 3개 서비스 부팅 → 사용자 사주 체크 → 종료
set -u
PY=/home/declan/Documents/Develop/Project/nabom/saju-life-guide/saju-document/.venv/bin/python
BACKEND=/home/declan/Documents/Develop/Project/nabom/backend
PORT_SAJU=8011
PORT_ICHING=8022
PORT_FACADE=8088
TOKEN="dev-token-123"

cleanup() {
  for p in $(pgrep -f "uvicorn app.main:app --port $PORT_SAJU" ; pgrep -f "uvicorn app.main:app --port $PORT_ICHING" ; pgrep -f "uvicorn app.main:app --port $PORT_FACADE"); do
    kill "$p" 2>/dev/null
  done
}
trap cleanup EXIT

echo "== 1) 사주 엔진 부팅 (:$PORT_SAJU) =="
(cd "$BACKEND/saju-engine" && SAJU_SERVICE_TOKEN="$TOKEN" nohup "$PY" -m uvicorn app.main:app --port "$PORT_SAJU" --app-dir . > /tmp/nabom-saju.log 2>&1 &)
echo "== 2) 주역 엔진 부팅 (:$PORT_ICHING) =="
(cd "$BACKEND/iching-engine" && SAJU_SERVICE_TOKEN="$TOKEN" nohup "$PY" -m uvicorn app.main:app --port "$PORT_ICHING" --app-dir . > /tmp/nabom-iching.log 2>&1 &)
echo "== 3) NABOM Facade 부팅 (:$PORT_FACADE) =="
(cd "$BACKEND/nabom-api" && SAJU_ENGINE_URL="http://localhost:$PORT_SAJU" ICHING_ENGINE_URL="http://localhost:$PORT_ICHING" SAJU_SERVICE_TOKEN="$TOKEN" nohup "$PY" -m uvicorn app.main:app --port "$PORT_FACADE" --app-dir . > /tmp/nabom-facade.log 2>&1 &)

echo "== readyz 대기 =="
for i in $(seq 1 30); do
  S=$(curl -s "http://localhost:$PORT_SAJU/readyz" | python3 -c "import sys,json;print(json.load(sys.stdin).get('ready'))" 2>/dev/null)
  I=$(curl -s "http://localhost:$PORT_ICHING/readyz" | python3 -c "import sys,json;print(json.load(sys.stdin).get('ready'))" 2>/dev/null)
  [ "$S" = "True" ] && [ "$I" = "True" ] && break
  sleep 1
done
echo "saju ready=$S  iching ready=$I"

echo
echo "== 4) 내 사주 체크: POST /api/v1/living/profiles/initial =="
curl -s -X POST "http://localhost:$PORT_FACADE/api/v1/living/profiles/initial" \
  -H "Content-Type: application/json" -H "X-User-Id: declan" -H "X-Request-Id: e2e-1" \
  -d '{
    "birth_input": {
      "calendar": "solar",
      "date": "1992-03-01",
      "time": "07:20",
      "time_precision": "exact",
      "location": {"label": "대한민국 부산광역시", "timezone": "Asia/Seoul", "lat": 35.1796, "lon": 129.0756},
      "gender": "남성"
    },
    "current_priorities": ["성장", "관계"],
    "change_goal": "완성도"
  }' | python3 -m json.tool

echo
echo "== 5) 주역 회고: POST /api/v1/living/reflections =="
curl -s -X POST "http://localhost:$PORT_FACADE/api/v1/living/reflections" \
  -H "Content-Type: application/json" -H "X-User-Id: declan" -H "X-Request-Id: e2e-2" \
  -d '{
    "period_from": "2026-08-10",
    "period_to": "2026-08-16",
    "days_recorded": 5,
    "mood": {"mean": 3.2, "delta": -1},
    "energy": {"mean": 2.8, "delta": 0},
    "tag_counts": {"work": 3, "relationship": 2},
    "goal_actions": {"completed": 2, "abandoned": 1},
    "evidence_refs": ["ev1", "ev2", "ev3"]
  }' | python3 -m json.tool

echo
echo "== 6) healthz 확인 =="
curl -s "http://localhost:$PORT_FACADE/healthz"
echo
