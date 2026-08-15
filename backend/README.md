# NABOM Engine Backend

사주·주역 엔진을 독립 서비스로 분리한 백엔드 스캐폴드 v1.

## 구조

```text
backend/
├── contracts/            # JSON Schema 계약 (chart/reading/error)
├── saju-engine/          # 사주 엔진 private API (:8001)
│   ├── engine/           # manse/compatibility/element_analysis + 지식 CSV (스냅샷)
│   ├── data/             # NAOJ 정밀 절기 provider (번들)
│   └── app/main.py       # FastAPI 서비스
├── iching-engine/        # 주역 엔진 private API (:8002)
│   ├── engine/           # iching/advice/reflection_resolver + dataset
│   └── app/main.py       # FastAPI 서비스
├── nabom-api/            # 외부 유일 진입점 (Facade)
│   └── app/main.py       # 인증/동의/매핑 + engine client
└── tests/test_engine_apis.py  # 오프라인 ASGI 통합 테스트
```

## 엔드포인트

### Private engine (외부 노출 금지)

```text
POST /internal/v1/charts         # 사주 차트 + 오행·강약·용신
POST /internal/v1/compatibility  # 궁합 근거
POST /internal/v1/readings/cast  # 주역 cast
POST /internal/v1/reflections    # 결정적 record_reflection
GET  /healthz  /readyz
```

공통 헤더: `X-Request-Id`, `X-Contract-Version: 1.0`, 선택 `Authorization: Bearer <SAJU_SERVICE_TOKEN>`.

### NABOM Facade (외부 유일 진입점)

```text
POST /api/v1/living/profiles/initial
GET  /api/v1/living/profiles/{id}
POST /api/v1/living/profiles/{id}/feedback   # rejected → 활성 Trait에서 제외
POST /api/v1/living/reflections
POST /api/v1/living/luck?year=2026&month=5   # 세운/월운/대운
POST /api/v1/relationships/{id}/mirror
```

## 입력 검증 (fail-fast)

사주 엔진은 엔진 호출 전에 다음을 422 `INVALID_INPUT`으로 거부한다.

- 지원 연도 범위 외 (1900~2100)
- 미래 날짜
- 잘못된 날짜(예: 2026-02-30)/시간 형식
- 잘못된 timezone (500 크래시 방지)
- 잘못된 calendar/time_precision

## Idempotency

엔진 API는 `Idempotency-Key` 헤더를 지원한다. 같은 키 + 같은 body 재전송은 저장된 응답을 반환하고, 같은 키 + 다른 body는 409 `IDEMPOTENCY_CONFLICT`.

## 계약 강제

엔진 응답은 `contracts/chart.schema.json`, `contracts/reading.schema.json`으로 검증된다. 위반 시 500 `CONTRACT_VIOLATION`으로 fail-closed.

## 릴리스 락 (배포 하드닝)

엔진 소스·지식 CSV를 SHA-256으로 고정한다.

```bash
# 갱신 (엔진 변경 시)
python release/verify_engine_lock.py --update --root saju-engine --manifest release/engine-lock.json
python release/verify_engine_lock.py --update --root iching-engine --manifest release/iching-lock.json

# 검증 (배포 게이트) — mismatch/누락/미등록 파일 시 exit 1
python release/verify_engine_lock.py --verify --root saju-engine --manifest release/engine-lock.json
```

## 서비스 토큰 로테이션

`SAJU_SERVICE_TOKENS`(쉼표 구분)로 회전 overlap을 지원한다. 구·신 토큰이 동시에 유효하다.

```bash
SAJU_SERVICE_TOKENS="tok_old,tok_new" uvicorn app.main:app --port 8001 --app-dir saju-engine
```

## 검증 계약

- CanonicalReflection 응답은 `contracts/reflection.schema.json`으로 검증된다.
- 음력 변환은 lunar-python 설치 시 검증 trace와 함께 변환, 윤달 미지정 시 fail-closed한다.
- 거절된 Trait 가설은 활성 프로필에서 제외되지만 이력은 보존된다.

## 실행

```bash
# 사주 엔진
SAJU_SERVICE_TOKEN=... uvicorn app.main:app --port 8001 --app-dir saju-engine

# 주역 엔진
SAJU_SERVICE_TOKEN=... uvicorn app.main:app --port 8002 --app-dir iching-engine

# NABOM Facade
SAJU_ENGINE_URL=http://localhost:8001 ICHING_ENGINE_URL=http://localhost:8002 \
  NABOM_GOOGLE_CLIENT_ID=... NABOM_GOOGLE_CLIENT_SECRET=... \
  NABOM_PUBLIC_APP_URL=http://localhost:3000 \
  NABOM_GOOGLE_REDIRECT_URI=http://localhost:8080/api/v1/auth/google/callback \
  uvicorn app.main:app --port 8080 --app-dir nabom-api
```

Google 로그인은 `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`도 읽는다. 콜백 URL은 Google Cloud 콘솔 Authorized redirect URIs에 등록해야 한다. 시크릿은 저장소에 넣지 않는다.

`SAJU_SERVICE_TOKEN` 미설정 시 개발 모드(인증 없음)로 동작한다.

## 테스트

```bash
python tests/test_engine_apis.py
```

오프라인 ASGI 통합 테스트가 사주/주역/Facade 전체 계약을 검증한다.

## 정책 요약

- 사주 엔진은 기본으로 번들 NAOJ provider를 로드한다.
- `quality_mode: strict`는 근사 절기가 감지되면 `APPROXIMATE_SOLAR_TERMS_BLOCKED`(422)로 fail-closed한다.
- 주역 회고는 정렬된 Evidence ID + 기간 + resolver version의 결정적 해시로 생성된다.
- Facade는 raw chart/괘/고전 문장을 외부 응답에 노출하지 않는다.
- 관계 Mirror는 `X-Consent: granted`가 없으면 403이다.

## 배포 주의

- `saju-engine/engine`과 `iching-engine/engine`은 상위 저장소에서 복사한 스냅샷이다.
  배포 시 엔진 소스와 지식 CSV의 버전을 고정(pin)하고 릴리스 게이트에서 해시를 검증해야 한다.
- 엔진 서비스는 public ingress를 만들지 않는다. service token 또는 mTLS로 보호한다.
