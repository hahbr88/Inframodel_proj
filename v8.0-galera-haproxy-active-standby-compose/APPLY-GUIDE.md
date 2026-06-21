# VM 적용 가이드

## 1. VM 준비

Ubuntu 24.04 LTS VM 5대를 준비한다.

| VM | IP |
|---|---:|
| haproxy1 | `192.168.100.11` |
| haproxy2 | `192.168.100.12` |
| db1 | `192.168.100.30` |
| db2 | `192.168.100.40` |
| db3 | `192.168.100.50` |

WAS 또는 테스트 클라이언트는 `haproxy1`을 1순위, `haproxy2`를 2순위 접속 대상으로 사용한다.

```bash
ping -c 3 192.168.100.11
ping -c 3 192.168.100.12
ping -c 3 192.168.100.30
ping -c 3 192.168.100.40
ping -c 3 192.168.100.50
```

## 2. Docker 설치

모든 VM에서 실행한다.

```bash
sudo apt update
sudo apt install -y ca-certificates curl mariadb-client
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker
```

DB VM에 호스트 MariaDB 서버가 있으면 중지한다.

```bash
sudo systemctl disable --now mariadb || true
sudo ss -lntup | grep ':3306' || true
```

## 3. 프로젝트 배치

모든 VM에 이 폴더를 같은 경로로 배치한다.

```bash
cd ~/v8.0-galera-haproxy-active-standby-compose
```

## 4. Secret 생성

db1에서만 생성한다.

```bash
mkdir -p secrets
openssl rand -hex 24 | tr -d '\n' > secrets/root_password.txt
openssl rand -hex 24 | tr -d '\n' > secrets/app_password.txt
openssl rand -hex 24 | tr -d '\n' > secrets/sst_password.txt
chmod 644 secrets/*.txt
sha256sum secrets/*.txt
```

db2, db3에 복사한다.

```bash
scp secrets/*.txt guru@192.168.100.40:/home/guru/v8.0-galera-haproxy-active-standby-compose/secrets/
scp secrets/*.txt guru@192.168.100.50:/home/guru/v8.0-galera-haproxy-active-standby-compose/secrets/
```

## 5. DB VM `.env` 생성

```bash
# db1
cp .env.vm-db1.example .env

# db2
cp .env.vm-db2.example .env

# db3
cp .env.vm-db3.example .env
```

정상 기준:

| VM | `GALERA_READ_ONLY` |
|---|---|
| db1 | `OFF` |
| db2 | `OFF` |
| db3 | `OFF` |

## 6. DB 이미지 빌드

db1, db2, db3에서 실행한다.

```bash
docker compose --env-file .env -f compose.vm-db.yaml config >/dev/null
docker compose --env-file .env -f compose.vm-db.yaml build --no-cache
```

## 7. Galera 기동

db1 bootstrap:

```bash
sed -i 's/^GALERA_BOOTSTRAP=.*/GALERA_BOOTSTRAP=1/' .env
docker compose --env-file .env -f compose.vm-db.yaml up -d
docker compose --env-file .env -f compose.vm-db.yaml ps
```

db2, db3 합류:

```bash
docker compose --env-file .env -f compose.vm-db.yaml up -d
docker compose --env-file .env -f compose.vm-db.yaml ps
```

db1 bootstrap 해제:

```bash
sed -i 's/^GALERA_BOOTSTRAP=.*/GALERA_BOOTSTRAP=0/' .env
docker compose --env-file .env -f compose.vm-db.yaml up -d --force-recreate
```

각 DB VM에서 상태 확인:

```bash
bash scripts/status-db.sh
```

## 8. HAProxy 구성

haproxy1:

```bash
cp .env.vm-haproxy1.example .env
docker compose --env-file .env -f compose.vm-haproxy.yaml up -d
docker compose --env-file .env -f compose.vm-haproxy.yaml ps
```

이미 HAProxy 컨테이너가 떠 있었다면 설정 변경 반영을 위해 재생성한다.

```bash
docker compose --env-file .env -f compose.vm-haproxy.yaml up -d --force-recreate
```

haproxy2:

```bash
cp .env.vm-haproxy2.example .env
docker compose --env-file .env -f compose.vm-haproxy.yaml up -d
docker compose --env-file .env -f compose.vm-haproxy.yaml ps
```

이미 HAProxy 컨테이너가 떠 있었다면 설정 변경 반영을 위해 재생성한다.

```bash
docker compose --env-file .env -f compose.vm-haproxy.yaml up -d --force-recreate
```

HAProxy stats 확인:

```bash
curl -s http://192.168.100.11:8404/ | head || true
curl -s http://192.168.100.12:8404/ | head || true
```

HAProxy VM에서 포트 리슨 상태를 확인한다.

```bash
sudo ss -lntp | grep -E ':3306|:3307|:8404'
docker logs --tail 100 haproxy-galera
```

클라이언트 VM에서 접근성을 확인한다.

```bash
sudo apt install -y netcat-openbsd
nc -vz -w 3 192.168.100.11 3306
nc -vz -w 3 192.168.100.11 3307
nc -vz -w 3 192.168.100.12 3306
nc -vz -w 3 192.168.100.12 3307
```

## 9. 접속 정보

| 용도 | 1순위 주소 | 2순위 주소 | 포트 | 평상시 DB 대상 | DB 장애 시 대상 |
|---|---|---|---:|---|---|
| write | `192.168.100.11` | `192.168.100.12` | `3306` | db1 | db2, 이후 db3 |
| read | `192.168.100.11` | `192.168.100.12` | `3307` | db2 | db3, 이후 db1 |

DB 3대는 모두 `read_only=OFF`다. 평상시 쓰기 우선순위는 HAProxy가 통제하므로, WAS가 DB VM의 3306에 직접 접속하지 못하게 방화벽이나 보안 그룹으로 막는다.

AWS에서 검증할 때 HAProxy 앞에 NLB를 둔다면 NLB target을 `haproxy1`, `haproxy2`로 등록하면 된다. 그 경우에도 이 폴더 안에서는 VIP를 쓰지 않는다.

## 10. 방화벽

DB VM:

```bash
sudo ufw allow from 192.168.100.11 to any port 3306 proto tcp
sudo ufw allow from 192.168.100.12 to any port 3306 proto tcp
sudo ufw allow from 192.168.100.0/24 to any port 4444 proto tcp
sudo ufw allow from 192.168.100.0/24 to any port 4567 proto tcp
sudo ufw allow from 192.168.100.0/24 to any port 4567 proto udp
sudo ufw allow from 192.168.100.0/24 to any port 4568 proto tcp
```

HAProxy VM:

```bash
sudo ufw allow from 192.168.100.0/24 to any port 3306 proto tcp
sudo ufw allow from 192.168.100.0/24 to any port 3307 proto tcp
sudo ufw allow from 192.168.100.0/24 to any port 8404 proto tcp
```
