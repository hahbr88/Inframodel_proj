# Docker Compose 배포 검증 결과

## 1. 검증 개요

| 항목 | 내용 |
|---|---|
| 검증일 | 2026-06-16 |
| 호스트 | macOS, VMware |
| 게스트 | Ubuntu 24.04 |
| 컨테이너 런타임 | Docker Engine, Docker Compose Plugin |
| 네트워크 | VMware NAT `192.168.100.0/24` |
| app-vm | `192.168.100.10` |
| db-vm | `192.168.100.30` |

검증 목적은 기존 web-vm과 was-vm 분리 구성을 하나의 app-vm 안에서 각각의
컨테이너로 실행하고, app-vm에서 db-vm의 MariaDB까지 연결되는지 확인하는
것이다.

## 2. 검증 대상 구조

```text
Browser
  -> app-vm:80
     -> gateway
        /        -> service-web
        /admin/  -> admin-web
        /api/    -> was:8000
                    -> db-vm:3306
```

컨테이너 배치:

| VM | 컨테이너 | 역할 |
|---|---|---|
| app-vm | gateway | 외부 HTTP 진입점 및 reverse proxy |
| app-vm | service-web | 사용자 웹 정적 파일 |
| app-vm | admin-web | 관리자 웹 정적 파일 |
| app-vm | was | FastAPI 애플리케이션 |
| db-vm | mariadb | 서비스 DB |

## 3. 검증 결과

| 검증 항목 | 결과 | 확인 내용 |
|---|---|---|
| db-vm MariaDB 배포 | 성공 | `db-mariadb-1` healthy |
| app-vm 통합 Compose 배포 | 성공 | gateway, service-web, admin-web, was healthy |
| gateway health check | 성공 | `GET /health` -> `200 OK` |
| 사용자 웹 라우팅 | 성공 | `GET /` -> `200 OK` |
| 관리자 웹 라우팅 | 성공 | `GET /admin/` -> `200 OK` |
| gateway -> was 내부 통신 | 성공 | `http://was:8000/` healthy 응답 |
| gateway -> service-web 내부 통신 | 성공 | HTML 응답 확인 |
| gateway -> admin-web 내부 통신 | 성공 | `/admin/` HTML 응답 확인 |
| gateway -> was -> db 통신 | 성공 | `/api/course-catalog` JSON 응답 |
| DB 데이터 조회 | 성공 | `total_count=434`, 첫 페이지 `count=20` |
| KMA 소량 수집 | 성공 | `KMA_COURSE_LIMIT=3`, 코스 1~3 `weather_available=true` |
| KMA 전체 수집 | 성공 | 434개 중 432개 성공, 예보 44,416건, 관광기후지수 147건 |
| cron 등록 | 성공 | `install-weather-cron.sh`로 KST 8회 실행 등록 |
| cron 자동 실행 | 미검증 | 다음 예정 시각의 실행 로그 확인 필요 |
| VM 재부팅 복구 | 미검증 | 컨테이너 자동 기동과 데이터 유지 확인 필요 |

`/api/` 단독 요청은 `404 Not Found`가 정상일 수 있다. FastAPI에 `/api/` 루트
엔드포인트가 없기 때문이다. 실제 API인 `/api/course-catalog`는 정상 응답했다.

## 4. 확인 명령과 결과

app-vm 컨테이너 상태:

```text
app-admin-web-1     Up (healthy)
app-gateway-1       Up (healthy)   0.0.0.0:80->80/tcp
app-service-web-1   Up (healthy)
app-was-1           Up (healthy)
```

gateway health check:

```bash
curl -i http://127.0.0.1/health
```

```text
HTTP/1.1 200 OK
healthy
```

웹 라우팅:

```bash
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/admin/
```

두 요청 모두 `200 OK`를 반환했다.

gateway 컨테이너에서 내부 서비스명으로 접근:

```bash
docker compose exec gateway wget -qO- http://was:8000/
docker compose exec gateway wget -qO- http://service-web/ | head
docker compose exec gateway wget -qO- http://admin-web/admin/ | head
```

WAS는 다음 형태의 healthy 응답을 반환했다.

```json
{
  "status": "healthy",
  "service": "Integrated Weather & Course WAS",
  "environment": "production",
  "data_mode": "database",
  "weather_mode": "database",
  "weather_storage": "database",
  "timezone": "Asia/Seoul"
}
```

DB 기반 API 조회:

```bash
curl -s http://127.0.0.1/api/course-catalog | head
```

확인 값:

```text
status=success
forecast_time=2026061611
count=20
total_count=434
has_next=true
```

날씨 수집 후 `weather_available=true`, `weather`, `forecasts`,
`tourist_index` 값이 응답에 포함되는 것을 확인했다.

KMA 전체 수집 결과:

```text
기준시각: 2026061611
전체 코스: 434개
동네예보 성공: 432개
데이터 없음: 2개
통신실패: 0개
동네예보 저장: 44,416건
관광기후지수 지역: 147개
MariaDB 관광기후지수 저장: 147건
snapshot_id: 2
총 소요: 190.9초
```

중간에 KMA API `HTTP 504` timeout이 있었지만 collector 재시도로 회복했고,
최종 통신 실패는 0건이었다. `데이터 없음` 2건은 KMA 응답에 해당 코스 데이터가
없어 기존 데이터를 유지한 케이스다.

cron 등록 결과:

```text
# inframodel-kma-collector
CRON_TZ=Asia/Seoul
10 2,5,8,11,14,17,20,23 * * * /home/guru/Inframodel_proj/deploy/app/collect-weather.sh >> /home/guru/Inframodel_proj/deploy/app/kma-collector.log 2>&1
```

`install-weather-cron.sh`는 등록 후 현재 crontab을 한 번 출력한다. 바로 이어서
`crontab -l`을 실행하면 같은 항목이 두 번 보일 수 있지만, 실제 등록이 중복된
것은 아니다.

## 5. DB 검증 결과

db-vm에서 MariaDB 컨테이너 상태:

```text
db-mariadb-1   mariadb:11.4   Up (healthy)   192.168.100.30:3306->3306/tcp
```

`deploy/db/deploy.sh` 실행 시 다음 리소스가 생성됐다.

```text
Network db_default
Volume db_mariadb-data
Container db-mariadb-1
```

MariaDB 데이터는 Docker named volume `db_mariadb-data`에 저장된다. 기존
볼륨이 있는 상태에서 `MARIADB_PASSWORD`만 변경해도 DB 사용자 비밀번호는
자동으로 바뀌지 않는다.

## 6. 보안 구성

- 외부 사용자는 app-vm의 80 포트로 접근한다.
- WAS 8000 포트는 app-vm 호스트에 publish하지 않는다.
- gateway는 Docker 내부 네트워크에서 `was:8000`으로 접근한다.
- DB 3306 포트는 app-vm에서만 접근하도록 UFW/AWS Security Group에서 제한한다.
- 검증 환경은 HTTP이므로 `COOKIE_SECURE=false`를 사용한다.
- HTTPS 적용 시 `PUBLIC_ORIGIN=https://...`, `COOKIE_SECURE=true`로 변경한다.

Docker published port는 환경에 따라 UFW 규칙보다 먼저 처리될 수 있다. VMware
NAT, AWS Security Group, 호스트 방화벽에서도 DB 포트의 외부 접근을 제한해야
한다.

## 7. 잔여 검증

다음 항목을 완료하면 app-vm + db-vm 1차 검증을 종료할 수 있다.

1. Mac 브라우저에서 `http://192.168.100.10/`, `/admin/`, `/api/course-catalog` 접속 확인
2. 관리자 로그인 확인
3. 예약 생성, 조회, 수정, 취소 확인
4. cron 다음 예정 시각 실행 로그 확인
5. VM 두 대 재부팅 후 컨테이너 자동 시작 확인
6. 재부팅 후 MariaDB 데이터와 날씨 스냅샷 유지 확인
7. app-vm 외 호스트에서 DB 포트 접근 차단 확인

## 8. 향후 AWS 전환 시 변경점

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
- HTTP -> HTTPS 및 인증서 적용
- 단일 MariaDB -> 3-node MariaDB Galera Cluster

Galera 전환 시 app은 DB 노드 개별 IP가 아니라 HAProxy, MaxScale, 내부 DNS 같은
클러스터 endpoint를 `DB_HOST`로 사용한다.

## 9. 이전 3대 VM 검증에서 확인한 이슈

web-vm, was-vm, db-vm을 분리했던 이전 검증에서 다음 이슈를 확인하고 조치했다.

| 이슈 | 조치 |
|---|---|
| ARM64에서 `asyncmy` 빌드 실패 | WAS Dockerfile을 멀티스테이지 빌드로 변경 |
| 공유 `AsyncSession` 동시 쿼리 오류 | 공유 세션 쿼리를 순차 실행으로 변경 |
| 관리자 로그인 실패 | `ADMIN_PASSWORD` 기준으로 관리자 해시 갱신 |
| 관리자 페이지 흰 화면 | admin Vite base와 Router basename을 `/admin`으로 정리 |

현재 통합 app-vm 검증은 위 조치가 반영된 상태에서 수행했다.
