# VM별 Docker Compose 배포

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

각 VM에서 저장소를 얕게 clone합니다.

```bash
git clone --depth 1 https://github.com/hahbr88/Inframodel_proj.git
cd Inframodel_proj
```

Git에는 `node_modules`, `.venv`, 빌드 결과물이 포함되지 않으므로 로컬 작업
디렉터리 전체 크기가 그대로 clone되는 것은 아닙니다.

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
JWT_SECRET='local-jwt-secret-1234567890abcdef' \
ADMIN_PASSWORD='admin-pass-1234' \
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
JWT_SECRET='local-jwt-secret-1234567890abcdef' \
ADMIN_PASSWORD='admin-pass-1234' \
./deploy/was/deploy.sh
```

접속 경로:

- 사용자 웹: `http://WEB_VM_IP/`
- 관리자 웹: `http://WEB_VM_IP/admin/`
- API 프록시: `http://WEB_VM_IP/api/`

Docker의 published port는 일부 환경에서 UFW 규칙보다 먼저 처리될 수 있습니다.
VMware NAT와 호스트 방화벽에서도 외부 접근을 제한해야 합니다.
