# 애플리케이션 서버 구축

## 개요

본 문서는 레거시 온프레미스 환경의 애플리케이션 서버(`legacy-app-01`) 구축 절차를 정의한다.

애플리케이션 서버는 웹 서버(`legacy-web-01`)로부터 전달받은 요청을 처리하는 역할을 수행한다.

본 환경에서는 Docker Compose 기반 FastAPI WAS 서비스를 운영한다.

04번 문서에서는 Nginx Reverse Proxy 설정을 완료하고, 본 문서에서는 WAS 컨테이너 실행 후 Reverse Proxy 실제 연동 검증까지 수행한다.

---

# 서버 정보

| 항목     | 설정값                    |
| -------- | ------------------------- |
| 서버명   | legacy-app-01             |
| 역할     | Application Server        |
| 운영체제 | Ubuntu Server 24.04.4 LTS |
| CPU      | 2 Core                    |
| Memory   | 4 GB                      |
| Storage  | 30 GB                     |
| IP 주소  | 192.168.100.20/24         |
| WAS Port | 8000                      |

---

# 관리자 계정

| 항목     | 값        |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# 사전 조건

```text
01 VMware Installation
02 Network Configuration
04 Web Server Build
```

완료 상태여야 한다.

---

# 서버 상태 확인

```bash
whoami
```

예상 결과

```text
admin
```

```bash
hostnamectl
```

예상 결과

```text
Static hostname: legacy-app-01
```

```bash
ip addr
```

예상 결과

```text
192.168.100.20/24
```

```bash
lsb_release -a
```

---

# 패키지 업데이트

```bash
sudo apt update
```

```bash
sudo apt upgrade -y
```

---

# 운영 도구 설치

```bash
sudo apt install -y \
vim \
curl \
wget \
net-tools \
htop \
tree \
unzip
```

---

# Docker 설치

```bash
sudo apt install -y ca-certificates curl gnupg
```

```bash
sudo install -m 0755 -d /etc/apt/keyrings
```

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

```bash
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

```bash
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

```bash
sudo apt update
```

```bash
sudo apt install -y \
docker-ce \
docker-ce-cli \
containerd.io \
docker-buildx-plugin \
docker-compose-plugin
```

---

# Docker 서비스 확인

```bash
sudo systemctl status docker
```

예상 결과

```text
active (running)
```

```bash
sudo systemctl is-enabled docker
```

예상 결과

```text
enabled
```

```bash
docker --version
```

```bash
docker compose version
```

---

# Docker 설치 검증

```bash
sudo docker run hello-world
```

예상 결과

```text
Hello from Docker!
```

---

# Docker 그룹 설정

```bash
sudo usermod -aG docker $USER
```

로그아웃한다.

```bash
exit
```

다시 접속한다.

```bash
ssh admin@192.168.100.20
```

그룹을 확인한다.

```bash
groups
```

예상 결과에 `docker`가 포함되어야 한다.

---

# 방화벽 설정

```bash
sudo ufw status
```

WAS 포트를 허용한다.

```bash
sudo ufw allow 8000/tcp
```

```bash
sudo ufw status
```

예상 결과

```text
8000/tcp ALLOW Anywhere
```

---

# WAS 배포 디렉터리 생성

```bash
sudo mkdir -p /app/was
```

```bash
sudo chown -R admin:admin /app/was
```

```bash
cd /app/was
```

```bash
pwd
```

예상 결과

```text
/app/was
```

---

# WAS 소스 배포

팀원이 제공한 WAS 프로젝트를 `/app/was` 경로에 배포한다.

배포 후 파일을 확인한다.

```bash
ls -al
```

아래 항목이 확인되어야 한다.

```text
compose.yaml
Dockerfile
app
```

프로젝트 구조를 확인한다.

```bash
tree -L 2
```

---

# Compose 파일 확인

```bash
cat compose.yaml
```

WAS 포트 설정을 확인한다.

```bash
grep "8000:8000" compose.yaml
```

예상 결과

```text
- "8000:8000"
```

의미

```text
legacy-app-01:8000
↓
was 컨테이너:8000
```

---

# WAS 컨테이너 실행

```bash
docker compose build was
```

```bash
docker compose up -d was
```

---

# 컨테이너 상태 확인

```bash
docker compose ps
```

예상 결과

```text
was   running
```

```bash
docker ps
```

---

# WAS 로그 확인

```bash
docker compose logs -f was
```

정상적으로 애플리케이션이 실행되어야 한다.

로그 확인 종료

```text
Ctrl + C
```

---

# WAS 포트 확인

```bash
sudo ss -tulnp | grep ':8000'
```

예상 결과

```text
0.0.0.0:8000
```

---

# WAS 서버 자체 HTTP 확인

```bash
curl http://localhost:8000
```

```bash
curl http://192.168.100.20:8000
```

정상 응답이 반환되어야 한다.

---

# WEB 서버에서 WAS 직접 통신 확인

WEB 서버에 접속한다.

```bash
ssh admin@192.168.100.10
```

WEB 서버에서 WAS 서버로 직접 요청한다.

```bash
curl http://192.168.100.20:8000
```

정상 응답이 반환되어야 한다.

---

# Reverse Proxy 연동 검증

04번 문서에서 설정한 Nginx Reverse Proxy를 검증한다.

WEB 서버에서 웹 서버 IP로 요청한다.

```bash
curl http://192.168.100.10
```

정상 응답이 반환되어야 한다.

관리 PC 브라우저에서도 확인한다.

```text
http://192.168.100.10
```

정상적으로 WAS 응답이 표시되어야 한다.

---

# Nginx Access Log 확인

WEB 서버에서 Nginx 접속 로그를 확인한다.

```bash
sudo tail -f /var/log/nginx/access.log
```

관리 PC 브라우저에서 접속한다.

```text
http://192.168.100.10
```

접속 로그가 기록되는지 확인한다.

로그 확인 종료

```text
Ctrl + C
```

---

# Reverse Proxy 검증 결과

아래 흐름이 정상 동작해야 한다.

```text
Client
↓
legacy-web-01
192.168.100.10:80
↓
Nginx Reverse Proxy
↓
legacy-app-01
192.168.100.20:8000
↓
WAS Container
```

---

# DB 연동 준비 확인

현재 Compose 파일에는 MariaDB 및 Redis Profile이 포함되어 있다.

현재 레거시 환경에서는 WAS 서비스만 실행한다.

```bash
docker compose up -d was
```

MariaDB와 Redis는 사용하지 않는다.

실제 데이터베이스 연동은 별도 DB 서버(`legacy-db-01`)를 사용한다.

DB 연동 검증은 다음 문서에서 진행한다.

```text
06 DB Server Build
```

---

# 컨테이너 재시작 검증

```bash
docker compose restart was
```

```bash
docker compose ps
```

```bash
curl http://localhost:8000
```

---

# 재부팅 검증

서버를 재부팅한다.

```bash
sudo reboot
```

재접속한다.

```bash
ssh admin@192.168.100.20
```

WAS 디렉터리로 이동한다.

```bash
cd /app/was
```

컨테이너 상태를 확인한다.

```bash
docker compose ps
```

중지 상태라면 다시 실행한다.

```bash
docker compose up -d was
```

포트를 확인한다.

```bash
sudo ss -tulnp | grep ':8000'
```

응답을 확인한다.

```bash
curl http://localhost:8000
```

---

# Snapshot 생성

VMware 메뉴

```text
VM
 └─ Snapshot
      └─ Take Snapshot
```

설정

```text
Name
05-WAS-Complete
```

---

# 구축 완료 기준

- admin 계정 로그인 가능
- Docker 설치 완료
- Docker Compose 사용 가능
- Docker 설치 검증 완료
- Docker 그룹 설정 완료
- 8000 포트 허용 완료
- WAS 소스 배포 완료
- Compose 포트 확인 완료
- WAS 컨테이너 정상 실행
- 8000 포트 수신 확인
- WAS 자체 HTTP 응답 확인
- WEB 서버에서 WAS 직접 통신 확인
- Reverse Proxy 응답 확인
- 브라우저 접속 검증 완료
- Nginx Access Log 기록 확인
- 재부팅 후 WAS 재실행 가능
- Snapshot 생성 완료

---

# 다음 단계

```text
06 DB Server Build
```
