# NTP 서버 구축 (Chrony)

## 개요

본 문서는 레거시 온프레미스 환경의 NTP(Network Time Protocol) 서버 구축 절차를 정의한다.

NTP는 서버 간 시간을 동기화하기 위한 프로토콜로, 로그 분석, 서비스 운영, 백업 작업, 장애 분석 시 동일한 기준 시간을 제공한다.

본 환경에서는 운영 서버(`legacy-ops-01`)에 Chrony를 설치하여 내부 NTP 서버를 구축한다.

운영 서버는 외부 시간 서버와 동기화하며, 웹 서버, 애플리케이션 서버, 데이터베이스 서버는 운영 서버를 기준으로 시간을 동기화한다.

---

# 서버 정보

| 항목    | 설정값        |
| ------- | ------------- |
| 서버명  | legacy-ops-01 |
| 역할    | NTP Server    |
| 서비스  | Chrony        |
| IP 주소 | 192.168.100.5 |

---

# 관리자 계정

| 항목     | 값        |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# 운영 구조

```text
Google Public NTP
(time.google.com)
        │
        ▼
legacy-ops-01
192.168.100.5
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
web     app     db
```

운영 서버는 외부 NTP 서버와 시간을 동기화한다.

웹 서버, 애플리케이션 서버, 데이터베이스 서버는 운영 서버를 기준으로 시간을 동기화한다.

---

# 사전 조건

```text
03 OPS Server Build
04 Web Server Build
05 WAS Server Build
06 DB Server Build
```

완료 상태여야 한다.

---

# 서버 상태 확인

운영 서버에 로그인한다.

```bash
ssh admin@192.168.100.5
```

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

---

# 패키지 업데이트

```bash
sudo apt update
```

```bash
sudo apt upgrade -y
```

---

# Chrony 설치

```bash
sudo apt install chrony -y
```

설치 여부를 확인한다.

```bash
chronyc -v
```

---

# Chrony 서비스 확인

서비스 상태를 확인한다.

```bash
sudo systemctl status chrony
```

예상 결과

```text
active (running)
```

자동 시작 여부를 확인한다.

```bash
sudo systemctl is-enabled chrony
```

예상 결과

```text
enabled
```

---

# NTP 포트 허용

현재 상태를 확인한다.

```bash
sudo ufw status
```

UDP 123 포트를 허용한다.

```bash
sudo ufw allow 123/udp
```

상태를 확인한다.

```bash
sudo ufw status
```

예상 결과

```text
123/udp ALLOW Anywhere
```

---

# Chrony 설정 파일 백업

설정 파일을 백업한다.

```bash
sudo cp \
/etc/chrony/chrony.conf \
/etc/chrony/chrony.conf.bak
```

확인한다.

```bash
ls -al /etc/chrony/chrony.conf*
```

---

# Chrony 서버 설정

설정 파일을 수정한다.

```bash
sudo vi /etc/chrony/chrony.conf
```

아래 내용을 확인하거나 추가한다.

```conf
server time.google.com iburst

allow 192.168.100.0/24

driftfile /var/lib/chrony/chrony.drift

makestep 1.0 3

rtcsync
```

---

# Chrony 서비스 재시작

설정을 적용한다.

```bash
sudo systemctl restart chrony
```

상태를 확인한다.

```bash
sudo systemctl status chrony
```

---

# 운영 서버 동기화 확인

외부 NTP 서버와 동기화 상태를 확인한다.

```bash
chronyc tracking
```

예상 결과

```text
Leap status     : Normal
```

시간 소스를 확인한다.

```bash
chronyc sources
```

예상 결과

```text
^* time.google.com
```

---

# UDP 123 포트 확인

```bash
sudo ss -ulpn | grep ':123'
```

예상 결과

```text
udp UNCONN 0 0 0.0.0.0:123
```

---

# Web 서버 Chrony 설치

Web 서버에 접속한다.

```bash
ssh admin@192.168.100.10
```

패키지를 갱신한다.

```bash
sudo apt update
```

Chrony를 설치한다.

```bash
sudo apt install chrony -y
```

설정 파일을 백업한다.

```bash
sudo cp \
/etc/chrony/chrony.conf \
/etc/chrony/chrony.conf.bak
```

설정 파일을 수정한다.

```bash
sudo vi /etc/chrony/chrony.conf
```

기존 pool 또는 server 항목을 주석 처리한다.

예시

```conf
# pool ntp.ubuntu.com iburst
```

운영 서버를 추가한다.

```conf
server 192.168.100.5 iburst
```

서비스를 재시작한다.

```bash
sudo systemctl restart chrony
```

---

# WAS 서버 Chrony 설치

WAS 서버에 접속한다.

```bash
ssh admin@192.168.100.20
```

패키지를 갱신한다.

```bash
sudo apt update
```

Chrony를 설치한다.

```bash
sudo apt install chrony -y
```

설정 파일을 백업한다.

```bash
sudo cp \
/etc/chrony/chrony.conf \
/etc/chrony/chrony.conf.bak
```

설정 파일을 수정한다.

```bash
sudo vi /etc/chrony/chrony.conf
```

운영 서버를 추가한다.

```conf
server 192.168.100.5 iburst
```

서비스를 재시작한다.

```bash
sudo systemctl restart chrony
```

---

# DB 서버 Chrony 설치

DB 서버에 접속한다.

```bash
ssh admin@192.168.100.30
```

패키지를 갱신한다.

```bash
sudo apt update
```

Chrony를 설치한다.

```bash
sudo apt install chrony -y
```

설정 파일을 백업한다.

```bash
sudo cp \
/etc/chrony/chrony.conf \
/etc/chrony/chrony.conf.bak
```

설정 파일을 수정한다.

```bash
sudo vi /etc/chrony/chrony.conf
```

운영 서버를 추가한다.

```conf
server 192.168.100.5 iburst
```

서비스를 재시작한다.

```bash
sudo systemctl restart chrony
```

---

# 클라이언트 동기화 확인

각 서버에서 아래 명령어를 실행한다.

```bash
chronyc sources
```

예상 결과

```text
^* 192.168.100.5
```

상세 상태를 확인한다.

```bash
chronyc tracking
```

예상 결과

```text
Leap status     : Normal
```

시간 동기화 상태를 확인한다.

```bash
timedatectl
```

예상 결과

```text
System clock synchronized: yes
NTP service: active
```

---

# 운영 서버 접근 확인

각 서버에서 운영 서버 NTP 상태를 확인한다.

```bash
chronyc -h 192.168.100.5 tracking
```

정상적으로 결과가 출력되어야 한다.

---

# 시간 확인

각 서버에서 현재 시간을 확인한다.

```bash
date
```

Web 서버

```bash
ssh admin@192.168.100.10
date
```

WAS 서버

```bash
ssh admin@192.168.100.20
date
```

DB 서버

```bash
ssh admin@192.168.100.30
date
```

시간이 거의 동일해야 한다.

---

# 서비스 구조 검증

```text
time.google.com
        │
        ▼
legacy-ops-01
192.168.100.5
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
web     app     db
```

정상 동작 확인

---

# 재부팅 검증

운영 서버 재부팅

```bash
sudo reboot
```

재접속 후 확인

```bash
sudo systemctl status chrony
```

```bash
chronyc tracking
```

클라이언트 서버도 각각 재부팅 후 확인한다.

```bash
sudo reboot
```

재접속 후

```bash
sudo systemctl status chrony
```

```bash
chronyc sources
```

```bash
timedatectl
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
08-NTP-Complete
```

---

# 구축 완료 기준

- admin 계정 로그인 가능
- Chrony 설치 완료
- Chrony 서비스 정상 동작
- 자동 시작 설정 완료
- UDP 123 포트 허용 완료
- 운영 서버 외부 NTP 동기화 확인
- Web 서버 동기화 확인
- WAS 서버 동기화 확인
- DB 서버 동기화 확인
- timedatectl 정상 확인
- 재부팅 후 정상 동작
- Snapshot 생성 완료

---

# 다음 단계

```text
09 Database Backup
```
