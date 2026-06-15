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

# NTP 서비스 목적

서버 간 시간이 일치하지 않을 경우 다음과 같은 문제가 발생할 수 있다.

- 로그 분석 시간 불일치
- 장애 원인 분석 어려움
- 백업 작업 시간 불일치
- 인증 관련 오류 발생 가능
- 서버 간 이벤트 추적 어려움

따라서 본 환경에서는 운영 서버를 기준 시간 서버(NTP Server)로 사용한다.

---

# 운영 구조

```text
Google Public NTP
(time.google.com)
        │
        ▼
legacy-ops-01
(192.168.100.5)
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
web    app     db
```

운영 서버는 Google Public NTP와 시간을 동기화한다.

웹 서버, 애플리케이션 서버, 데이터베이스 서버는 운영 서버를 기준으로 시간을 동기화한다.

---

# 패키지 업데이트

패키지 정보를 최신 상태로 갱신한다.

```bash
sudo apt update
```

---

# Chrony 설치

Chrony 패키지를 설치한다.

```bash
sudo apt install chrony -y
```

설치 상태를 확인한다.

```bash
sudo systemctl status chrony
```

정상 상태 예시

```text
Active: active (running)
```

---

# 자동 시작 확인

시스템 부팅 시 자동 실행 여부를 확인한다.

```bash
sudo systemctl is-enabled chrony
```

정상 결과

```text
enabled
```

---

# Chrony 서버 설정

설정 파일을 수정한다.

```bash
sudo vi /etc/chrony/chrony.conf
```

다음 항목을 확인 또는 추가한다.

```conf
# External NTP Server
server time.google.com iburst

allow 192.168.100.0/24

driftfile /var/lib/chrony/chrony.drift

makestep 1.0 3

rtcsync
```

---

# 설정 항목 설명

| 항목                          | 설명                       |
| ----------------------------- | -------------------------- |
| server time.google.com iburst | Google Public NTP 서버     |
| allow 192.168.100.0/24        | 내부 서버 시간 동기화 허용 |
| driftfile                     | 시간 오차 기록             |
| makestep                      | 초기 시간 오차 자동 보정   |
| rtcsync                       | 시스템 시간 동기화         |

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

# 운영 서버 동기화 상태 확인

운영 서버가 외부 NTP 서버와 정상 동기화되는지 확인한다.

```bash
chronyc tracking
```

정상 결과 예시

```text
Reference ID : XXXX
Leap status  : Normal
```

---

# 운영 서버 시간 소스 확인

운영 서버가 어떤 시간 서버를 사용하는지 확인한다.

```bash
chronyc sources
```

정상 결과 예시

```text
MS Name/IP address
===============================================================================
^* time.google.com
```

---

# NTP 서비스 포트 확인

UDP 123 포트를 확인한다.

```bash
ss -ulpn | grep ':123'
```

정상 결과 예시

```text
udp UNCONN 0 0 0.0.0.0:123
```

---

# 클라이언트 서버 설정

다음 서버는 운영 서버를 기준으로 시간 동기화를 수행한다.

| 서버명        |
| ------------- |
| legacy-web-01 |
| legacy-app-01 |
| legacy-db-01  |

설정 파일을 수정한다.

```bash
sudo vi /etc/chrony/chrony.conf
```

기존 외부 NTP 설정을 비활성화하고 운영 서버를 지정한다.

```conf
# 기존 외부 NTP 설정 비활성화

server 192.168.100.5 iburst
```

---

# 클라이언트 서비스 재시작

설정을 적용한다.

```bash
sudo systemctl restart chrony
```

상태를 확인한다.

```bash
sudo systemctl status chrony
```

---

# 클라이언트 동기화 확인

클라이언트 서버가 운영 서버와 정상 동기화되는지 확인한다.

```bash
chronyc sources
```

정상 결과 예시

```text
MS Name/IP address
===============================================================================
^* 192.168.100.5
```

---

# 클라이언트 시간 확인

현재 시간 동기화 상태를 확인한다.

```bash
timedatectl
```

정상 결과 예시

```text
System clock synchronized: yes
NTP service: active
```

---

# 운영 관점 설명

레거시 환경에서는 여러 서버가 동시에 운영되므로 모든 서버가 동일한 시간을 사용하는 것이 중요하다.

서버 간 시간이 다를 경우 로그 분석, 장애 추적, 백업 작업, 사용자 인증 과정에서 문제가 발생할 수 있다.

본 환경에서는 운영 서버를 기준 시간 서버로 사용하여 시간 관리 기준을 일원화한다.

운영 서버는 Google Public NTP와 시간을 동기화하며, 내부 서버는 운영 서버만 참조하도록 구성한다.

예시

```text
10:00:00 Web Server 로그

10:00:01 Application Server 로그

10:00:02 Database Server 로그
```

모든 서버가 동일한 기준 시간을 사용해야 장애 발생 시 정확한 원인 분석이 가능하다.

---

# 점검 항목

| 점검 항목                      | 확인 |
| ------------------------------ | ---- |
| Chrony 설치 완료               | □    |
| chrony 서비스 실행 확인        | □    |
| 자동 시작 설정 확인            | □    |
| Chrony 서버 설정 완료          | □    |
| allow 설정 완료                | □    |
| UDP 123 포트 확인              | □    |
| tracking 정상 확인             | □    |
| 운영 서버 외부 NTP 동기화 확인 | □    |
| 클라이언트 설정 완료           | □    |
| 클라이언트 동기화 확인         | □    |
| timedatectl 확인 완료          | □    |

---

# 구축 완료 기준

다음 항목을 모두 만족하면 NTP 서버 구축이 완료된 것으로 판단한다.

- Chrony 설치 완료
- chrony 서비스 정상 실행
- UDP 123 포트 정상 확인
- 운영 서버 외부 NTP 동기화 성공
- 클라이언트 서버 설정 완료
- 클라이언트 서버 동기화 성공
- timedatectl 동기화 상태 확인 완료

---

# 다음 단계

NTP 서버 구축이 완료되면 다음 문서를 진행한다.

- 09-db-backup.md
