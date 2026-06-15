# 시스템 통합 검증

## 개요

본 문서는 레거시 온프레미스 환경 구축 완료 후 수행하는 최종 검증 절차를 정의한다.

모든 서버 및 서비스가 정상적으로 동작하는지 확인하며, 운영 환경으로 전환 가능한 상태인지 검증한다.

검증 대상은 다음과 같다.

- 서버 상태
- 네트워크 통신
- DNS 서비스
- NTP 서비스
- Web 서비스
- Application 서비스
- Database 서비스
- Backup 서비스
- VPN 서비스

---

# 검증 대상 서버

| 서버명        | 역할              | IP 주소        |
| ------------- | ----------------- | -------------- |
| legacy-ops-01 | 운영 서버         | 192.168.100.5  |
| legacy-web-01 | 웹 서버           | 192.168.100.10 |
| legacy-app-01 | 애플리케이션 서버 | 192.168.100.20 |
| legacy-db-01  | 데이터베이스 서버 | 192.168.100.30 |

---

# 서버 상태 확인

각 서버에 접속하여 상태를 확인한다.

```bash
hostnamectl
```

```bash
uptime
```

확인 항목

- 서버 정상 부팅
- 서버명 정상 적용
- SSH 접속 가능

---

# 네트워크 통신 확인

운영 서버에서 각 서버로 Ping 테스트를 수행한다.

```bash
ping -c 4 192.168.100.10
```

```bash
ping -c 4 192.168.100.20
```

```bash
ping -c 4 192.168.100.30
```

모든 서버가 정상 응답해야 한다.

---

# DNS 서비스 검증

DNS 서버 상태를 확인한다.

```bash
sudo systemctl status bind9
```

DNS 조회를 수행한다.

```bash
dig web.<DOMAIN>
```

또는

```bash
nslookup web.<DOMAIN>
```

DNS 이름 기반 통신을 확인한다.

```bash
ping web.<DOMAIN>
```

```bash
ping app.<DOMAIN>
```

```bash
ping db.<DOMAIN>
```

확인 항목

- DNS 조회 성공
- 등록된 IP 반환
- DNS 이름 해석 성공
- DNS 이름 기반 통신 성공
- bind9 서비스 정상 동작

---

# NTP 서비스 검증

Chrony 서비스 상태를 확인한다.

```bash
sudo systemctl status chrony
```

동기화 상태를 확인한다.

```bash
chronyc tracking
```

확인 항목

- chrony 서비스 정상 실행
- 시간 동기화 정상

---

# Web 서비스 검증

웹 서버 상태를 확인한다.

```bash
sudo systemctl status nginx
```

웹 페이지 접속을 확인한다.

```text
http://192.168.100.10
```

확인 항목

- nginx 정상 실행
- 웹 페이지 정상 출력

---

# WAS 서비스 검증

애플리케이션 서버 상태를 확인한다.

```bash
ss -tulpen | grep ':3000'
```

확인 항목

- 서비스 프로세스 실행
- 3000 포트 LISTEN 확인

---

# Database 서비스 검증

MariaDB 상태를 확인한다.

```bash
sudo systemctl status mariadb
```

포트를 확인한다.

```bash
ss -tulpen | grep ':3306'
```

MariaDB 접속을 확인한다.

```bash
sudo mysql
```

확인 항목

- mariadb 정상 실행
- 3306 포트 LISTEN 확인
- DB 접속 성공

---

# Web → WAS 연동 검증

웹 서비스를 통해 애플리케이션 서버가 정상 동작하는지 확인한다.

확인 항목

- Web 접속 성공
- WAS 요청 처리 성공

---

# WAS → DB 연동 검증

애플리케이션 기능을 통해 데이터 조회 및 저장을 수행한다.

확인 항목

- DB 연결 성공
- 데이터 조회 성공
- 데이터 저장 성공

---

# 백업 검증

백업 파일 생성 여부를 확인한다.

```bash
ls -lh /backup/mariadb
```

Cron 등록 상태를 확인한다.

```bash
sudo crontab -l
```

확인 항목

- 백업 파일 생성 확인
- Cron 등록 확인
- 7일 보관 정책 적용 확인

---

# VPN 검증

WireGuard 상태를 확인한다.

```bash
sudo wg
```

포트를 확인한다.

```bash
ss -ulpn | grep 51820
```

VPN 접속 후 내부 서버 접근을 확인한다.

```bash
ping 192.168.100.10
```

```bash
ping 192.168.100.20
```

```bash
ping 192.168.100.30
```

확인 항목

- VPN 연결 성공
- 내부 서버 접근 성공

---

# 최종 서비스 흐름 검증

서비스 흐름을 확인한다.

```text
Internet
    │
    ▼
legacy-web-01
    │
    ▼
legacy-app-01
    │
    ▼
legacy-db-01
```

확인 항목

- 사용자 접속 가능
- 웹 서비스 동작
- 애플리케이션 동작
- 데이터 저장 및 조회 가능

---

# 최종 검증 체크리스트

| 검증 항목           | 결과 |
| ------------------- | ---- |
| 서버 생성 완료      | □    |
| 네트워크 통신 성공  | □    |
| DNS 동작 확인       | □    |
| NTP 동기화 확인     | □    |
| Web 서비스 확인     | □    |
| WAS 서비스 확인     | □    |
| DB 서비스 확인      | □    |
| Web → WAS 연동 확인 | □    |
| WAS → DB 연동 확인  | □    |
| Backup 확인         | □    |
| VPN 접속 확인       | □    |

---

# 검증 완료 기준

다음 항목을 모두 만족하면 레거시 온프레미스 환경 구축이 완료된 것으로 판단한다.

- 서버 4대 정상 운영
- DNS 정상 동작
- NTP 정상 동기화
- Web 서비스 정상 제공
- WAS 서비스 정상 동작
- Database 정상 동작
- Backup 정상 수행
- VPN 정상 접속
- 전체 서비스 연동 성공
