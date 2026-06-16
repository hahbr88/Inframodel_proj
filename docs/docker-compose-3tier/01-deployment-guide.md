# Docker Compose 배포 가이드

## 1. 목적

Ubuntu 호스트에 Nginx, FastAPI, MariaDB를 직접 설치하지 않고 Docker
Engine과 Docker Compose Plugin만 설치한 뒤 서비스를 컨테이너로 실행한다.

현재 실제 서비스 배포 기본 구조는 `app-vm + db-vm` 두 대다. `app-vm` 안에서
웹과 WAS가 각각 컨테이너로 실행되고, DB는 초기에는 단일 MariaDB VM을 사용한다.

```text
Browser
  |
  v
app-vm (192.168.100.10)
  |- gateway Nginx
  |- service-web
  |- admin-web
  |- was
  `- kma-collector
       |
       v
db-vm (192.168.100.30)
  `- MariaDB
```

기존 `deploy/web`, `deploy/was`는 web-vm과 was-vm을 분리한 3대 VM 검증용으로
남긴다. 신규 배포 기본 경로는 `deploy/app`이다.

## 2. 서버 구성

| VM | 컨테이너 | 호스트 공개 포트 | 접근 범위 |
|---|---|---:|---|
| app-vm | gateway | 80 | 클라이언트 |
| app-vm | service-web, admin-web | 없음 | gateway 내부 프록시 |
| app-vm | was | 없음 | gateway 내부 프록시 |
| app-vm | kma-collector | 없음 | 일회성 수집 작업 |
| db-vm | mariadb | 3306 | app-vm |

`was`의 8000 포트는 호스트에 publish하지 않는다. gateway 컨테이너가 같은
Compose 네트워크 안에서 `was:8000`으로 접근한다.

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
|- app/
|  |- compose.yaml
|  |- deploy.sh
|  |- collect-weather.sh
|  |- install-weather-cron.sh
|  `- gateway/default.conf.template
|- db/
|  |- compose.yaml
|  `- deploy.sh
|- web/
`- was/
```

Dockerfile은 애플리케이션 빌드 방법을 관리하고, Compose 파일은 배포 단위별
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
sudo ROLE=app APPLY_STATIC_IP=yes ~/init-vm.sh
```

고정 IP가 이미 설정되어 있다면 `APPLY_STATIC_IP=yes`를 제외한다. 고정 IP
변경 시 SSH 연결이 끊길 수 있으므로 VMware 콘솔에서 실행하는 편이 안전하다.

### Windows / VMware Workstation 주의사항

스크립트는 Windows PowerShell에서 실행하는 것이 아니라 Ubuntu VM 안에서
실행한다. Windows에서는 `ssh`, `scp`, VMware 콘솔을 통해 VM에 접속하고,
실제 명령은 Ubuntu 터미널에서 수행한다.

Windows에서 파일을 전달할 때는 PowerShell의 OpenSSH 또는 Git Bash를 사용할 수
있다.

```powershell
scp .\deploy\common\init-vm.sh <사용자>@<현재-VM-IP>:~/
```

Windows에서 편집하거나 복사한 스크립트는 CRLF 줄바꿈이 섞일 수 있다. 실행 전
VM 안에서 다음 명령을 항상 한 번 실행한다.

```bash
sed -i 's/\r$//' ~/init-vm.sh
chmod +x ~/init-vm.sh
```

VMware Workstation의 NAT 대역은 macOS 검증 환경과 다를 수 있다. Windows에서
`192.168.100.0/24`를 그대로 쓰기 전에 `Virtual Network Editor`에서 VMnet8 NAT
대역과 gateway 주소를 확인한다. 예를 들어 NAT 대역이 `192.168.200.0/24`라면
두 VM 모두 같은 값으로 실행한다.

```bash
sudo ROLE=app \
  APP_IP=192.168.200.10 \
  DB_IP=192.168.200.30 \
  GATEWAY=192.168.200.2 \
  APPLY_STATIC_IP=yes \
  ~/init-vm.sh

sudo ROLE=db \
  APP_IP=192.168.200.10 \
  DB_IP=192.168.200.30 \
  GATEWAY=192.168.200.2 \
  APPLY_STATIC_IP=yes \
  ~/init-vm.sh
```

두 VM은 같은 NAT 네트워크에 있어야 하고, 각 고정 IP는 DHCP 할당 범위와 겹치지
않아야 한다. 고정 IP 적용 후 접속이 끊기면 VMware 콘솔에서 `ip addr`,
`ip route`, `ping 8.8.8.8`로 네트워크를 확인한다.

Windows Defender 방화벽이나 보안 프로그램이 호스트에서 VM으로 가는 연결을 막을
수 있다. 브라우저에서 `http://APP_VM_IP/`가 열리지 않으면 VM 내부 컨테이너
상태뿐 아니라 Windows의 VMnet8 네트워크가 사설 네트워크로 허용되어 있는지도
확인한다.

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
| app-vm | `80/tcp` |
| db-vm | app-vm에서 오는 `3306/tcp` |

## 5. 저장소 준비

초기화 후 다시 로그인하고 각 VM에서 저장소를 clone한다.

```bash
git clone https://github.com/hahbr88/Inframodel_proj.git
cd Inframodel_proj
```

검증 및 디버깅용 VM에서는 일반 clone을 사용한다. 배포만 수행하는 서버에서는
필요에 따라 `--depth 1`을 사용할 수 있다.

## 6. 환경변수 구분

역할별 `.env`는 서로 다른 컨테이너가 읽는다. 실제 비밀번호와 인증키가 들어
있는 `.env` 파일은 Git에 커밋하지 않는다.

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
수행하고 app-vm의 DB URL도 같은 값으로 맞춘다.

### app-vm

`deploy/app/.env`

```dotenv
HTTP_BIND_IP=0.0.0.0
HTTP_PORT=80
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

`deploy/app/deploy.sh`에는 `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD`를 전달한다. 스크립트가 이 값으로 `WRITE_DATABASE_URL`과
`READ_DATABASE_URL`을 생성한다.

DB 비밀번호는 db-vm의 `MARIADB_PASSWORD`와 같아야 한다. 초기에는 읽기와 쓰기
URL이 같은 단일 MariaDB를 가리킨다. 향후 Galera 앞단에 HAProxy, MaxScale,
내부 DNS를 둘 경우 `DB_HOST`만 해당 endpoint로 변경한다.

현재 Compose에는 Redis 컨테이너가 없다. `REDIS_URL` 접속에 실패하면
애플리케이션의 KMA 클라이언트 캐시는 프로세스 메모리로 대체된다. 날씨 원본과
수집 스냅샷의 영구 저장소는 Redis가 아니라 MariaDB다.

## 7. 배포

반드시 `db -> app` 순서로 배포한다.

```bash
# db-vm
DB_PASSWORD='app-pass-1234' \
DB_ROOT_PASSWORD='root-pass-1234' \
./deploy/db/deploy.sh
```

```bash
# app-vm
DB_HOST='192.168.100.30' \
DB_PASSWORD='app-pass-1234' \
JWT_SECRET='replace-with-random-secret-32-chars' \
ADMIN_PASSWORD='admin-pass-1234' \
KMA_SERVICE_KEY='<Decoding 인증키>' \
PUBLIC_ORIGIN='http://192.168.100.10' \
./deploy/app/deploy.sh
```

DB 및 app 배포 스크립트의 비밀번호와 JWT 값에는 영문, 숫자, `.`, `_`, `~`,
`-`만 사용할 수 있다. `JWT_SECRET`은 32자 이상이어야 한다.

각 역할의 `deploy.sh`는 전달받은 값으로 해당 디렉터리의 `.env`를 매번 다시
생성한다. `.env`를 직접 수정한 뒤 설정을 유지하려면 `deploy.sh`를 다시
실행하지 말고 해당 역할 디렉터리에서 Compose 명령을 사용한다.

```bash
cd deploy/app
docker compose up -d --build
```

DB 데이터를 삭제할 수 있으므로 다음 명령은 특별한 초기화 목적이 아니면
실행하지 않는다.

```bash
docker compose down -v
```

## 8. Gateway 라우팅

`deploy/app/gateway/default.conf.template`는 gateway 컨테이너가 실제로
사용하는 Nginx 템플릿이다.

```text
/         -> service-web
/admin/   -> admin-web
/api/     -> was:8000
/health   -> gateway health check
```

web과 WAS가 같은 Compose 프로젝트 안에 있으므로 gateway는 호스트 IP가 아니라
Docker 서비스명 `was`로 API 서버를 찾는다.

## 9. 날씨 수집

최초에는 코스 3개만 수집해 인증키, 외부 API, MariaDB 저장을 확인한다.

```bash
KMA_COURSE_LIMIT=3 ./deploy/app/collect-weather.sh
```

정상 확인 후 전체 코스를 수집한다.

```bash
./deploy/app/collect-weather.sh
```

수집 데이터는 JSON 파일이 아니라 MariaDB의 다음 테이블에 저장된다.

```text
weather_snapshots
weather_forecasts
climate_indices
```

정기 수집 등록:

```bash
./deploy/app/install-weather-cron.sh
crontab -l
```

실행 시각은 KST 기준 매일 `02:10, 05:10, 08:10, 11:10, 14:10, 17:10,
20:10, 23:10`이다. `init-vm.sh`가 VM 시스템 시간대를 `Asia/Seoul`로
설정하며, cron 항목에도 `CRON_TZ=Asia/Seoul`을 기록한다.

```bash
tail -f deploy/app/kma-collector.log
```

## 10. 운영 확인

```bash
cd deploy/app
docker compose ps
docker compose logs --tail=100
```

접속 주소:

```text
사용자 웹: http://192.168.100.10/
관리자 웹: http://192.168.100.10/admin/
API 프록시: http://192.168.100.10/api/
```

관리자 로그인은 `deploy/app/.env`의 `ADMIN_USERNAME`, `ADMIN_PASSWORD`를
사용한다.

## 11. DBeaver 연결

의도한 UFW 정책은 DB 포트를 app-vm에서만 접근하도록 제한한다. 관리 도구에서는
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

DBeaver가 MariaDB JDBC 드라이버 다운로드를 요청하면 최초 한 번 `Download`를
실행한다.

## 12. 향후 AWS Galera 전환

초기 레거시 단계에서는 `deploy/db`의 단일 MariaDB를 사용한다. AWS 전환
단계에서는 DB EC2 세 대에 MariaDB Galera Cluster를 구성하고, app은 DB 노드
개별 IP가 아니라 Galera 앞단 endpoint를 바라보게 한다.

권장 흐름:

```text
app-ec2
  -> db-proxy.internal 또는 db-cluster.internal
     -> db-ec2-1 / Galera node1
     -> db-ec2-2 / Galera node2
     -> db-ec2-3 / Galera node3
```

app 배포 값은 다음처럼 바뀐다.

```bash
DB_HOST='db-proxy.internal' \
DB_PASSWORD='app-pass-1234' \
JWT_SECRET='replace-with-random-secret-32-chars' \
ADMIN_PASSWORD='admin-pass-1234' \
PUBLIC_ORIGIN='https://example.com' \
COOKIE_SECURE=true \
./deploy/app/deploy.sh
```

Galera 노드 사이에는 다음 포트가 필요하다.

| 용도 | 포트 |
|---|---:|
| MariaDB client | `3306/tcp` |
| Galera replication | `4567/tcp`, `4567/udp` |
| IST | `4568/tcp` |
| SST | `4444/tcp` |

AWS Security Group 기준:

| Security Group | Inbound |
|---|---|
| app-sg | `80/443` from client 또는 ALB |
| db-sg | `3306/tcp` from app-sg |
| db-sg | `4567/tcp`, `4567/udp`, `4568/tcp`, `4444/tcp` from db-sg |

Galera는 3개처럼 홀수 노드로 구성하고, 전체 클러스터 재기동 시 bootstrap
대상 노드를 신중히 선택해야 한다. 애플리케이션은 처음에는 단일 write endpoint를
사용하는 방식으로 운용하는 것이 단순하다.

Docker published port는 환경에 따라 UFW보다 먼저 처리될 수 있다. UFW 규칙만
신뢰하지 말고 VMware NAT, AWS Security Group, 호스트 방화벽에서도 WAS와 DB
포트의 외부 접근을 제한해야 한다.
