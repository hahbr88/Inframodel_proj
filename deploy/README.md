# VM별 Docker Compose 배포

상세 구축 절차와 검증 결과:

- [Docker Compose 3-Tier 구축 가이드](../docs/docker-compose-3tier/01-deployment-guide.md)
- [Docker Compose 3-Tier 검증 결과](../docs/docker-compose-3tier/02-validation-result.md)

Ubuntu 24.04 VM 세 대를 다음 두 단계로 구성합니다.

1. `init-vm.sh`: OS, 네트워크, Docker, UFW 구성
2. 역할별 `deploy.sh`: 이미지 빌드 또는 pull 후 컨테이너 실행

Mac의 VMware Fusion과 Windows의 VMware Workstation 모두 VM 내부가
Ubuntu 24.04라면 같은 Bash 스크립트를 사용합니다. 호스트별 NAT 대역 차이는
환경변수로 전달합니다.

## 1단계: VM 초기화

`init-vm.sh` 파일만 USB, VMware 공유 폴더 또는 `scp`로 각 VM에 전달한 뒤
VMware 콘솔에서 실행합니다. Git checkout으로 받은 파일은 `.gitattributes`에
의해 LF 줄바꿈이 유지됩니다. 별도로 전달한 Windows 파일이라면 먼저 실행합니다.

```bash
sed -i 's/\r$//' init-vm.sh
chmod +x init-vm.sh
```

```bash
# db-vm
sudo ROLE=db APPLY_STATIC_IP=yes ./init-vm.sh

# was-vm
sudo ROLE=was APPLY_STATIC_IP=yes ./init-vm.sh

# web-vm
sudo ROLE=web APPLY_STATIC_IP=yes ./init-vm.sh
```

기본 네트워크:

- web-vm: `192.168.100.10`
- was-vm: `192.168.100.20`
- db-vm: `192.168.100.30`
- gateway: `192.168.100.2`

Windows 호스트의 VMware NAT 대역이 `192.168.200.0/24`라면 다음처럼
모든 VM에 동일한 네트워크 값을 전달합니다.

```bash
sudo ROLE=web \
  WEB_IP=192.168.200.10 \
  WAS_IP=192.168.200.20 \
  DB_IP=192.168.200.30 \
  GATEWAY=192.168.200.2 \
  APPLY_STATIC_IP=yes \
  ./init-vm.sh
```

초기화 후 로그아웃하고 다시 로그인해 Docker 그룹 권한을 적용합니다.

## 2단계: 저장소 준비

각 VM에서 저장소를 clone합니다.

```bash
git clone https://github.com/hahbr88/Inframodel_proj.git
cd Inframodel_proj
```

Git에는 `node_modules`, `.venv`, 빌드 결과물이 포함되지 않으므로 로컬 작업
디렉터리 전체 크기가 그대로 clone되는 것은 아닙니다. 운영 배포 전용 서버에서
Git 이력이 필요 없을 때만 선택적으로 `--depth 1`을 사용합니다.

## 3단계: 역할별 배포

`db -> was -> web` 순서로 실행합니다. DB와 WAS에 전달하는
`DB_PASSWORD`는 반드시 같아야 합니다.

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
KMA_SERVICE_KEY='<공공데이터포털 Decoding 인증키>' \
./deploy/was/deploy.sh
```

```bash
# web-vm
./deploy/web/deploy.sh
```

NAT 대역을 변경했다면 배포 시에도 같은 주소를 전달합니다.

```bash
WEB_IP=192.168.200.10 \
WAS_IP=192.168.200.20 \
DB_IP=192.168.200.30 \
DB_PASSWORD='app-pass-1234' \
JWT_SECRET='replace-with-random-secret-32-chars' \
ADMIN_PASSWORD='admin-pass-1234' \
./deploy/was/deploy.sh
```

예시 비밀번호와 JWT는 실제 배포 전에 변경합니다. 허용 문자는 영문, 숫자,
`.`, `_`, `~`, `-`이며 JWT는 32자 이상이어야 합니다. 역할별 `deploy.sh`는
실행할 때마다 같은 디렉터리의 `.env`를 전달값으로 다시 생성합니다.

MariaDB 비밀번호 환경변수는 데이터 볼륨을 처음 생성할 때만 DB 사용자 생성에
사용됩니다. 기존 `mariadb-data` 볼륨에서 비밀번호를 바꾸려면 MariaDB 계정의
비밀번호도 별도로 변경해야 합니다.

접속 경로:

- 사용자 웹: `http://WEB_VM_IP/`
- 관리자 웹: `http://WEB_VM_IP/admin/`
- API 프록시: `http://WEB_VM_IP/api/`

## 날씨 수집

WAS 배포 시 공공데이터포털에서 발급받은 Decoding 인증키를
`KMA_SERVICE_KEY`로 전달합니다. 최초에는 전체 코스 대신 일부만 수집해
연결과 인증키를 확인할 수 있습니다.

```bash
KMA_COURSE_LIMIT=3 \
./deploy/was/collect-weather.sh
```

정상 확인 후 전체 코스를 한 번 수집합니다.

```bash
./deploy/was/collect-weather.sh
```

수집 결과는 DB의 `weather_snapshots`, `weather_forecasts`,
`climate_indices` 테이블에 저장됩니다.

기상청 발표 시각 10분 후에 자동 수집하도록 cron을 등록합니다.

```bash
sudo apt-get install -y cron
sudo systemctl enable --now cron
./deploy/was/install-weather-cron.sh
```

등록 확인과 로그 확인:

```bash
crontab -l
tail -f deploy/was/kma-collector.log
```

Docker의 published port는 일부 환경에서 UFW 규칙보다 먼저 처리될 수 있습니다.
VMware NAT와 호스트 방화벽에서도 외부 접근을 제한해야 합니다.
