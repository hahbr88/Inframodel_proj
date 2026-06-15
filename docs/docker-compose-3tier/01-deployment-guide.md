# Docker Compose 3-Tier 구축 가이드

## 1. 목적

Ubuntu 호스트에 Nginx, FastAPI, MariaDB를 직접 설치하지 않고 Docker
Engine과 Docker Compose Plugin만 설치한 뒤 모든 서비스를 컨테이너로
실행한다.

```text
Browser
  |
  v
web-vm (192.168.100.10)
  |- gateway Nginx
  |- service-web
  `- admin-web
       |
       v
was-vm (192.168.100.20)
  |- FastAPI
  `- KMA collector
       |
       v
db-vm (192.168.100.30)
  `- MariaDB
```

## 2. 서버 구성

| VM | 컨테이너 | 호스트 공개 포트 | 접근 범위 |
|---|---|---:|---|
| web-vm | gateway, service-web, admin-web | 80 | 클라이언트 |
| was-vm | was | 8000 | web-vm |
| was-vm | kma-collector | 없음 | 일회성 수집 작업 |
| db-vm | mariadb | 3306 | was-vm |

`kma-collector`는 상시 실행 서비스가 아니다. 수동 실행 또는 cron 호출 시
일회성 컨테이너로 실행되고 완료 후 제거된다.

## 3. 저장소 구조

```text
apps/
|- service-web/
|  |- Dockerfile
|  `- nginx/default.conf
|- admin-web/
|  |- Dockerfile
|  `- nginx/default.conf
`- integrated-was/
   `- Dockerfile

deploy/
|- common/init-vm.sh
|- web/
|  |- compose.yaml
|  |- deploy.sh
|  `- gateway/default.conf.template
|- was/
|  |- compose.yaml
|  |- deploy.sh
|  |- collect-weather.sh
|  `- install-weather-cron.sh
`- db/
   |- compose.yaml
   `- deploy.sh
```

Dockerfile은 애플리케이션 빌드 방법을 관리하고, Compose 파일은 VM별
컨테이너 실행 구성을 관리한다.

## 4. VM 초기화

`init-vm.sh`는 Ubuntu 24.04 VM 내부에서 실행한다. macOS의 VMware Fusion과
Windows의 VMware Workstation 모두 같은 스크립트를 사용할 수 있다.

스크립트 전달 예:

```bash
scp deploy/common/init-vm.sh <사용자>@<현재-VM-IP>:~/
```

VM에서 실행 권한을 설정한다.

```bash
sed -i 's/\r$//' ~/init-vm.sh
chmod +x ~/init-vm.sh
```

VMware 콘솔에서 역할별로 실행한다.

```bash
sudo ROLE=db APPLY_STATIC_IP=yes ~/init-vm.sh
sudo ROLE=was APPLY_STATIC_IP=yes ~/init-vm.sh
sudo ROLE=web APPLY_STATIC_IP=yes ~/init-vm.sh
```

고정 IP가 이미 설정되어 있다면 `APPLY_STATIC_IP=yes`를 제외한다. 고정 IP
변경 시 SSH 연결이 끊길 수 있으므로 VMware 콘솔에서 실행하는 편이 안전하다.

초기화 스크립트가 수행하는 작업:

- 호스트명과 `/etc/hosts` 설정
- 선택적 Netplan 고정 IP 설정
- Git, SSH, cron, UFW 설치
- Docker Engine과 Compose Plugin 설치
- 역할별 UFW 규칙 등록

기본 UFW 규칙:

| VM | 허용 규칙 |
|---|---|
| 공통 | `22/tcp` |
| web-vm | `80/tcp` |
| was-vm | web-vm에서 오는 `8000/tcp` |
| db-vm | was-vm에서 오는 `3306/tcp` |

## 5. 저장소 준비

초기화 후 다시 로그인하고 각 VM에서 저장소를 clone한다.

```bash
git clone https://github.com/hahbr88/Inframodel_proj.git
cd Inframodel_proj
```

검증 및 디버깅용 VM에서는 일반 clone을 사용한다. 배포만 수행하는 서버에서는
필요에 따라 `--depth 1`을 사용할 수 있다.

## 6. 환경변수 구분

역할별 `.env`는 서로 다른 컨테이너가 읽는다.

### db-vm

`deploy/db/.env`

```dotenv
DB_BIND_IP=192.168.100.30
MARIADB_DATABASE=integrated
MARIADB_USER=app
MARIADB_PASSWORD=<DB 비밀번호>
MARIADB_ROOT_PASSWORD=<root 비밀번호>
```

MariaDB가 DB와 사용자를 생성할 때 사용한다.

이 값들은 MariaDB 데이터 볼륨을 처음 초기화할 때 적용된다. 기존
`mariadb-data` 볼륨이 있는 상태에서 `.env`만 변경해도 기존 DB 사용자의
비밀번호는 자동으로 바뀌지 않는다. 비밀번호 변경은 MariaDB에서 별도로
수행하고 was-vm의 DB URL도 같은 값으로 맞춘다.

### was-vm

`deploy/was/.env`

```dotenv
WAS_BIND_IP=192.168.100.20
ENVIRONMENT=production
DATA_MODE=database
WEATHER_MODE=database
WEATHER_STORAGE=database

WRITE_DATABASE_URL=mysql+asyncmy://app:<DB 비밀번호>@192.168.100.30:3306/integrated
READ_DATABASE_URL=mysql+asyncmy://app:<DB 비밀번호>@192.168.100.30:3306/integrated

JWT_SECRET=<32자 이상 임의 문자열>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<관리자 비밀번호>
KMA_SERVICE_KEY=<공공데이터포털 Decoding 인증키>

CORS_ORIGINS=http://192.168.100.10
COOKIE_SECURE=false
```

DB 비밀번호는 db-vm의 `MARIADB_PASSWORD`와 같아야 한다. DB가 한 대이므로
현재 읽기와 쓰기 URL은 같으며, 향후 복제 구성이 생기면 분리할 수 있다.

### web-vm

`deploy/web/.env`

```dotenv
WAS_HOST=192.168.100.20
WAS_PORT=8000
```

실제 비밀번호와 인증키가 들어 있는 `.env` 파일은 Git에 커밋하지 않는다.

현재 Compose에는 Redis 컨테이너가 없다. `REDIS_URL` 접속에 실패하면
애플리케이션의 KMA 클라이언트 캐시는 프로세스 메모리로 대체된다. 날씨 원본과
수집 스냅샷의 영구 저장소는 Redis가 아니라 MariaDB다.

## 7. 역할별 배포

반드시 `db -> was -> web` 순서로 배포한다.

```bash
# db-vm
DB_PASSWORD='app-pass-1234' \
DB_ROOT_PASSWORD='root-pass-1234' \
./deploy/db/deploy.sh
```

```bash
# was-vm
DB_PASSWORD='app-pass-1234' \
JWT_SECRET='replace-with-random-secret-32-chars' \
ADMIN_PASSWORD='admin-pass-1234' \
KMA_SERVICE_KEY='<Decoding 인증키>' \
./deploy/was/deploy.sh
```

```bash
# web-vm
./deploy/web/deploy.sh
```

DB 및 WAS 배포 스크립트의 비밀번호와 JWT 값에는 영문, 숫자, `.`, `_`, `~`,
`-`만 사용할 수 있다. `JWT_SECRET`은 32자 이상이어야 한다.

각 역할의 `deploy.sh`는 전달받은 값으로 해당 디렉터리의 `.env`를 매번 다시
생성한다. `.env`를 직접 수정한 뒤 설정을 유지하려면 `deploy.sh`를 다시
실행하지 말고 해당 역할 디렉터리에서 Compose 명령을 사용한다.

```bash
cd deploy/was
docker compose up -d --build
```

DB 데이터를 삭제할 수 있으므로 다음 명령은 특별한 초기화 목적이 아니면
실행하지 않는다.

```bash
docker compose down -v
```

## 8. Gateway 라우팅

`deploy/web/gateway/default.conf.template`는 gateway 컨테이너가 실제로
사용하는 Nginx 템플릿이다.

```text
/         -> service-web
/admin/   -> admin-web
/api/     -> was-vm:8000
/health   -> gateway health check
```

공식 Nginx 이미지가 컨테이너 시작 시 `${WAS_HOST}`와 `${WAS_PORT}`를 치환해
최종 설정을 생성한다.

## 9. 날씨 수집

최초에는 코스 3개만 수집해 인증키, 외부 API, MariaDB 저장을 확인한다.

```bash
KMA_COURSE_LIMIT=3 ./deploy/was/collect-weather.sh
```

정상 확인 후 전체 코스를 수집한다.

```bash
./deploy/was/collect-weather.sh
```

수집 데이터는 JSON 파일이 아니라 MariaDB의 다음 테이블에 저장된다.

```text
weather_snapshots
weather_forecasts
climate_indices
```

정기 수집 등록:

```bash
./deploy/was/install-weather-cron.sh
crontab -l
```

실행 시각은 KST 기준 매일 `02:10, 05:10, 08:10, 11:10, 14:10, 17:10,
20:10, 23:10`이다. `init-vm.sh`가 VM 시스템 시간대를 `Asia/Seoul`로
설정하며, cron 항목에도 `CRON_TZ=Asia/Seoul`을 기록한다.

```bash
tail -f deploy/was/kma-collector.log
```

## 10. 운영 확인

```bash
docker compose ps
docker compose logs --tail=100
```

접속 주소:

```text
사용자 웹: http://192.168.100.10/
관리자 웹: http://192.168.100.10/admin/
WAS API:   http://192.168.100.20:8000/
API 문서:  http://192.168.100.20:8000/docs
```

관리자 로그인은 `deploy/was/.env`의 `ADMIN_USERNAME`,
`ADMIN_PASSWORD`를 사용한다.

## 11. DBeaver 연결

의도한 UFW 정책은 DB 포트를 was-vm에서만 접근하도록 제한한다. 관리 도구에서는
DB 포트를 추가 공개하지 않고 SSH 터널을 사용하는 방식을 권장한다.

SSH 터널을 사용할 때 MariaDB 연결:

```text
Host:     localhost
Port:     3306
Database: integrated
Username: app
Password: MARIADB_PASSWORD 값
```

SSH 터널:

```text
Host:     192.168.100.30
Port:     22
Username: Ubuntu VM 사용자
Password: VM 로그인 비밀번호
```

DBeaver가 MariaDB JDBC 드라이버 다운로드를 요청하면 최초 한 번
`Download`를 실행한다.

Docker published port는 환경에 따라 UFW보다 먼저 처리될 수 있다. UFW 규칙만
신뢰하지 말고 VMware NAT와 호스트 방화벽에서도 WAS와 DB 포트의 외부 접근을
제한해야 한다.
