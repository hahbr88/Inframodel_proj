# Docker Compose 배포

상세 구축 절차와 검증 결과:

- [Docker Compose 배포 가이드](../docs/docker-compose-3tier/01-deployment-guide.md)
- [Docker Compose 배포 검증 결과](../docs/docker-compose-3tier/02-validation-result.md)

현재 기본 배포 구조는 VM/EC2 두 대입니다.

```text
app-vm
  - gateway
  - service-web
  - admin-web
  - was
  - kma-collector

db-vm
  - mariadb
```

기존 `deploy/web`, `deploy/was`는 web-vm과 was-vm을 분리해서 검증할 때
사용할 수 있도록 남겨둡니다. 실제 서비스 배포 기본 경로는 `deploy/app`입니다.

## 1단계: VM 초기화

`init-vm.sh` 파일만 USB, VMware 공유 폴더 또는 `scp`로 각 VM에 전달한 뒤
VMware 콘솔에서 실행합니다.

```bash
sed -i 's/\r$//' init-vm.sh
chmod +x init-vm.sh
```

```bash
# app-vm
sudo ROLE=app APPLY_STATIC_IP=yes ./init-vm.sh

# db-vm
sudo ROLE=db APPLY_STATIC_IP=yes ./init-vm.sh
```

기본 네트워크:

- app-vm: `192.168.100.10`
- db-vm: `192.168.100.30`
- gateway: `192.168.100.2`

Windows 호스트의 VMware NAT 대역이 `192.168.200.0/24`라면 다음처럼
두 VM에 동일한 네트워크 값을 전달합니다.

```bash
sudo ROLE=app \
  APP_IP=192.168.200.10 \
  DB_IP=192.168.200.30 \
  GATEWAY=192.168.200.2 \
  APPLY_STATIC_IP=yes \
  ./init-vm.sh

sudo ROLE=db \
  APP_IP=192.168.200.10 \
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

## 3단계: 배포

`db -> app` 순서로 실행합니다. DB와 app에 전달하는 `DB_PASSWORD`는 반드시
같아야 합니다.

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
KMA_SERVICE_KEY='<공공데이터포털 Decoding 인증키>' \
PUBLIC_ORIGIN='http://192.168.100.10' \
./deploy/app/deploy.sh
```

예시 비밀번호와 JWT는 실제 배포 전에 변경합니다. 허용 문자는 영문, 숫자,
`.`, `_`, `~`, `-`이며 JWT는 32자 이상이어야 합니다. `deploy.sh`는 실행할
때마다 같은 디렉터리의 `.env`를 전달값으로 다시 생성합니다.

접속 경로:

- 사용자 웹: `http://APP_VM_IP/`
- 관리자 웹: `http://APP_VM_IP/admin/`
- API 프록시: `http://APP_VM_IP/api/`

## 날씨 수집

app 배포 시 공공데이터포털에서 발급받은 Decoding 인증키를
`KMA_SERVICE_KEY`로 전달합니다. 최초에는 전체 코스 대신 일부만 수집해
연결과 인증키를 확인할 수 있습니다.

```bash
KMA_COURSE_LIMIT=3 \
./deploy/app/collect-weather.sh
```

정상 확인 후 전체 코스를 한 번 수집합니다.

```bash
./deploy/app/collect-weather.sh
```

기상청 발표 시각 10분 후에 자동 수집하도록 cron을 등록합니다.

```bash
sudo apt-get install -y cron
sudo systemctl enable --now cron
./deploy/app/install-weather-cron.sh
```

등록 확인과 로그 확인:

```bash
crontab -l
tail -f deploy/app/kma-collector.log
```

## 향후 Galera 전환

초기에는 `deploy/db`의 단일 MariaDB를 사용합니다. AWS에서 DB EC2 세 대를
Galera로 구성하면 app 배포 시 `DB_HOST`만 Galera 앞단의 내부 DNS, HAProxy,
MaxScale endpoint 등으로 바꿉니다.

```bash
DB_HOST='db-cluster.internal' ./deploy/app/deploy.sh
```

Docker의 published port는 일부 환경에서 UFW 규칙보다 먼저 처리될 수 있습니다.
VMware NAT, AWS Security Group, 호스트 방화벽에서도 DB 포트의 외부 접근을
제한해야 합니다.
