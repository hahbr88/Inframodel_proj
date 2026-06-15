# Docker Compose 3-Tier 검증 결과

## 1. 검증 개요

| 항목 | 내용 |
|---|---|
| 검증일 | 2026-06-15 |
| 호스트 | macOS, VMware Fusion |
| 게스트 | Ubuntu 24.04.4 LTS ARM64 |
| 컨테이너 런타임 | Docker Engine, Docker Compose Plugin |
| 네트워크 | VMware NAT `192.168.100.0/24` |

검증 목적은 호스트에 서비스를 직접 설치하던 구성을 Docker Compose 기반
컨테이너 구조로 전환하고, 실제 3-tier 통신과 외부 날씨 수집을 확인하는
것이다.

## 2. 검증 결과

| 검증 항목 | 결과 | 확인 내용 |
|---|---|---|
| VM 역할별 고정 IP | 성공 | web `.10`, was `.20`, db `.30` |
| Docker 및 Compose 설치 | 성공 | Ubuntu ARM64에서 실행 |
| MariaDB 컨테이너 | 성공 | named volume과 health check 확인 |
| FastAPI 이미지 빌드 | 성공 | ARM64에서 `asyncmy` 컴파일 |
| service-web 빌드 | 성공 | Nginx 정적 이미지 |
| admin-web 빌드 | 성공 | `/admin/` base path 적용 |
| WEB -> WAS 통신 | 성공 | gateway `/api/` 프록시 |
| WAS -> DB 통신 | 성공 | 코스 434개 및 예약 데이터 조회 |
| KMA API 인증 | 성공 | Decoding 인증키 사용 |
| 소량 날씨 수집 | 성공 | 코스 3개, 예보 176건 |
| 관광기후지수 수집 | 성공 | 지역 3개 |
| MariaDB 날씨 적재 | 성공 | `snapshot_id=1` 생성 |
| API 날씨 응답 | 성공 | `weather_available=true` |
| cron 등록 스크립트 | 구현 완료 | 실제 자동 실행 시각은 추가 확인 필요 |
| 관리자 로그인 | 수정 완료 | 환경변수 계정 동기화 후 재검증 필요 |
| VM 재부팅 복구 | 미검증 | 컨테이너 자동 기동과 데이터 유지 확인 필요 |

## 3. 확인된 요청 흐름

```text
Browser
  -> web-vm gateway
  -> was-vm FastAPI
  -> db-vm MariaDB
```

날씨 데이터:

```text
KMA API
  -> kma-collector
  -> MariaDB weather tables
  -> FastAPI
  -> service-web
```

소량 수집 결과:

```text
코스: 3개
동네예보: 176건
관광기후지수: 3건
저장소: MariaDB
스냅샷: snapshot_id=1
```

API 응답에서 다음 항목을 확인했다.

```text
status=success
total_count=434
weather_available=true
weather=<요약 데이터>
tourist_index=<점수 및 등급>
```

## 4. 발생 문제와 해결

### 4.1 ARM64에서 WAS 이미지 빌드 실패

증상:

```text
error: command 'gcc' failed: No such file or directory
```

원인:

`asyncmy==0.2.10`의 ARM64용 wheel이 없어 소스 컴파일이 필요했지만
`python:3.12-slim`에 컴파일러가 없었다.

해결:

- WAS Dockerfile을 멀티스테이지 빌드로 변경
- builder 단계에만 `build-essential` 설치
- `/opt/venv`를 최종 slim 이미지로 복사

최종 이미지에는 gcc와 빌드 패키지가 포함되지 않는다.

### 4.2 공유 AsyncSession 동시 쿼리 오류

증상:

```text
sqlalchemy.exc.InvalidRequestError:
concurrent operations are not permitted
```

원인:

하나의 SQLAlchemy `AsyncSession`을 공유하는 두 DB 쿼리를
`asyncio.gather()`로 동시에 실행했다.

해결:

공유 세션을 사용하는 코스 및 예약 조회를 순차 실행으로 변경했다. 독립적인
외부 날씨 API 호출의 병렬 처리는 유지했다.

### 4.3 관리자 로그인 실패

증상:

```text
Invalid administrator credentials
```

원인:

최초 DB 초기화 당시 저장된 관리자 비밀번호 해시와 이후
`ADMIN_PASSWORD` 환경변수 값이 달랐다. 기존 코드는 사용자 테이블에 한 행이라도
있으면 관리자 정보를 갱신하지 않았다.

해결:

- 시작 시 `ADMIN_USERNAME`으로 관리자 계정 조회
- 계정이 없으면 생성
- 비밀번호가 다르면 `ADMIN_PASSWORD` 값으로 해시 갱신
- 프론트의 고정 `password123` 안내와 자동 입력 제거

### 4.4 관리자 페이지 흰 화면

증상:

`/admin/` HTML은 응답했지만 사용자 웹의 JS/CSS 자산이 요청됐다.

확인 내용:

브라우저에서 관리자 번들이 아닌 사용자 웹의 JS/CSS 파일을 요청하는 상태를
확인했다. 소스의 관리자 빌드는 `/admin/assets/` 경로를 정상 생성했으므로,
web-vm의 이전 이미지 또는 gateway 컨테이너 상태와 브라우저 캐시를 우선
원인으로 판단했다.

해결:

- admin-web의 Vite base를 `/admin/`으로 설정
- BrowserRouter basename을 `/admin`으로 설정
- web 배포 시 `--force-recreate` 적용
- 브라우저 캐시를 강력 새로고침

## 5. 보안 구성

- `.env` 파일은 Git에서 제외
- UFW에 DB 포트를 was-vm에서만 허용하는 규칙 등록
- UFW에 WAS 포트를 web-vm에서만 허용하는 규칙 등록
- 외부 사용자는 web-vm의 80 포트로 접근
- DBeaver는 DB 포트를 추가 공개하지 않고 SSH 터널 사용
- 검증 환경은 HTTP이므로 `COOKIE_SECURE=false`

AWS 배포 시에는 HTTPS를 적용하고 `COOKIE_SECURE=true`로 변경해야 한다.
UFW와 별도로 Security Group에서도 동일한 접근 제어가 필요하다.

단, Docker published port는 환경에 따라 UFW 규칙을 우회할 수 있다. VMware
NAT와 호스트 방화벽을 포함한 실제 포트 차단 여부는 잔여 검증에 포함한다.

## 6. 잔여 검증

다음 항목을 완료하면 1차 VMware 검증을 종료할 수 있다.

1. 관리자 환경변수 동기화 후 사용자/관리자 로그인 재확인
2. 예약 생성, 조회, 수정, 취소 확인
3. 전체 434개 코스 날씨 수집 확인
4. cron 실제 등록 및 다음 실행 로그 확인
5. VM 3대 재부팅 후 컨테이너 자동 시작 확인
6. 재부팅 후 MariaDB 데이터와 날씨 스냅샷 유지 확인
7. web-vm 외 호스트에서 WAS/DB 포트 접근 차단 확인

## 7. AWS 전환 시 변경점

VMware 검증에서는 각 VM이 소스를 clone하고 이미지를 직접 빌드한다. AWS
단계에서는 다음 구조로 전환한다.

```text
GitHub push
  -> CI 이미지 빌드
  -> Amazon ECR push
  -> EC2/ECS 이미지 pull
```

추가 전환 대상:

- UFW 중심 접근 제어 -> Security Group
- 호스트 cron -> EventBridge 또는 ECS Scheduled Task
- 로컬 `.env` 비밀값 -> Secrets Manager 또는 Parameter Store
- 자체 JWT 발급 -> Cognito User Pool 검토
- HTTP -> HTTPS 및 인증서 적용
