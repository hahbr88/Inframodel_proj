# 운영 서버 구축

## 개요

본 문서는 레거시 온프레미스 환경의 운영 서버(`legacy-ops-01`) 구축 절차를 정의한다.

운영 서버는 DNS, NTP, Backup, VPN 등 공통 운영 서비스를 제공하는 관리 서버로 사용한다.

본 문서에서는 운영 서버의 기본 운영 환경을 구성한다.

```text
1. 서버 상태 확인
2. 패키지 업데이트
3. 운영 도구 설치
4. SSH 서비스 확인
5. 방화벽 구성
6. 운영 디렉터리 구성
7. 로그 확인
8. 시스템 자원 확인
9. SSH 접속 검증
10. 재부팅 검증
11. Snapshot 생성
```

---

# 서버 정보

| 항목     | 설정값                    |
| -------- | ------------------------- |
| 서버명   | legacy-ops-01             |
| 역할     | Operations Server         |
| 운영체제 | Ubuntu Server 24.04.4 LTS |
| CPU      | 1 Core                    |
| Memory   | 2 GB                      |
| Storage  | 10 GB                     |
| IP 주소  | 192.168.100.5/24          |

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
```

완료 상태여야 한다.

---

# 서버 상태 확인

현재 로그인 계정을 확인한다.

```bash
whoami
```

예상 결과

```text
admin
```

서버명을 확인한다.

```bash
hostnamectl
```

예상 결과

```text
Static hostname: legacy-ops-01
```

IP 주소를 확인한다.

```bash
ip addr
```

예상 결과

```text
192.168.100.5/24
```

운영체제 버전을 확인한다.

```bash
lsb_release -a
```

예상 결과

```text
Ubuntu 24.04.4 LTS
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

설치 확인

```bash
vim --version
curl --version
wget --version
htop --version
```

---

# SSH 서비스 확인

```bash
sudo systemctl status ssh
```

예상 결과

```text
active (running)
```

자동 시작 확인

```bash
sudo systemctl is-enabled ssh
```

예상 결과

```text
enabled
```

SSH 포트 확인

```bash
sudo ss -tulnp | grep ssh
```

예상 결과

```text
0.0.0.0:22
```

---

# 방화벽 구성

현재 상태 확인

```bash
sudo ufw status
```

예상 결과

```text
Status: inactive
```

SSH 허용

```bash
sudo ufw allow 22/tcp
```

방화벽 활성화

```bash
sudo ufw enable
```

상태 확인

```bash
sudo ufw status
```

예상 결과

```text
22/tcp ALLOW Anywhere
```

---

# 운영 디렉터리 구성

```bash
sudo mkdir -p /infra
sudo mkdir -p /infra/scripts
sudo mkdir -p /infra/logs
sudo mkdir -p /infra/backup
```

구조 확인

```bash
tree /infra
```

예상 결과

```text
/infra
├── backup
├── logs
└── scripts
```

권한 확인

```bash
ls -al /infra
```

---

# 로그 확인

최근 시스템 로그

```bash
sudo journalctl -xe
```

최근 부팅 로그

```bash
sudo journalctl -b
```

SSH 인증 로그

```bash
sudo tail -f /var/log/auth.log
```

종료

```text
Ctrl + C
```

시스템 로그

```bash
sudo tail -f /var/log/syslog
```

종료

```text
Ctrl + C
```

---

# 시스템 자원 확인

```bash
lscpu
```

```bash
free -h
```

```bash
df -h
```

---

# SSH 접속 검증

관리 PC 또는 다른 서버에서 접속한다.

```bash
ssh admin@192.168.100.5
```

정상적으로 로그인되어야 한다.

---

# 재부팅 검증

```bash
sudo reboot
```

재접속 후 확인

```bash
hostnamectl
ip addr
sudo systemctl status ssh
sudo ufw status
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
03-Ops-Complete
```

---

# 구축 완료 기준

- admin 계정 로그인 가능
- hostname 정상 설정
- 고정 IP 유지
- 패키지 최신 상태
- 운영 도구 설치 완료
- SSH 서비스 정상 동작
- UFW 정상 동작
- 운영 디렉터리 생성 완료
- 로그 확인 가능
- SSH 접속 검증 완료
- 재부팅 후 정상 동작
- Snapshot 생성 완료

---

# 다음 단계

```text
04 Web Server Build
```
