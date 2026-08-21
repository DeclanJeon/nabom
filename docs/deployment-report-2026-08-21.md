# 나봄 배포 보고서

- 일자: 2026-08-21
- 대상: `https://nabom.ponslink.com`
- 배포 서버: `ponslink:~/nabom-deploy`

## 작업 내용

1. 오늘·프로필·회고·여정·설정 탭 이동을 Next 라우트 재탐색이 아닌 History API 기반 SPA 전환으로 변경했습니다.
2. 브라우저 뒤로가기·앞으로가기와 URL 동기화를 유지했습니다.
3. 배포 과정에서 확인된 백엔드 컨테이너 시작 오류를 수정했습니다.
   - 서비스별 Python 패키지 초기화 파일 추가
   - uvicorn `--app-dir` 경로 수정
   - Docker 컨테이너 시작 명령 수정

## 검증 결과

- 프론트엔드 lint 통과
- 프론트엔드 production build 통과
- 백엔드 `/healthz` 응답 정상
- PostgreSQL store 연결 정상
- 프로필 5건, 회고 3건 조회 확인
- 내부 웹 주소 `/today`: HTTP 200
- 공개 주소 `/today`: HTTP 200
- PostgreSQL, Redis, backend, web 컨테이너 정상 실행

## 배포 커밋

- `45c3984` — SPA 탭 내비게이션
- `1b79dca` — 백엔드 앱 패키지 초기화
- `85a7c8c` — uvicorn 앱 경로 수정
- `ab6f5d6` — 백엔드 컨테이너 시작 명령 수정

## 결론

배포 완료 상태이며, 공개 서비스의 주요 화면과 백엔드 상태 확인을 마쳤습니다.
