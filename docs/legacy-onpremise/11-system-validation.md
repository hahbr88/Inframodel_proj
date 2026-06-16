# 시스템 통합 검증

## 개요

본 문서는 레거시 온프레미스 환경 구축 완료 후 수행하는 최종 검증 절차를 정의한다.

01번부터 10번까지의 구축 문서가 모두 완료된 상태에서 전체 서버, 서비스, 네트워크, 연동 흐름이 정상 동작하는지 확인한다.

본 문서에서는 다음 항목을 검증한다.

```text
1. 서버 상태 검증
2. 네트워크 통신 검증
3. DNS 검증
4. NTP 검증
5. Web 서비스 검증
6. WAS 서비스 검증
7. Reverse Proxy 검증
8. DB 서비스 검증
9. WAS → DB 연동 검증
10. Backup 검증
11. VPN 검증
12. 최종 서비스 흐름 검증
```

---

# 검증 대상 서버

| 서버명        | 역할                        | IP 주소        |
| ------------- | --------------------------- | -------------- |
| legacy-ops-01 | 운영 서버 / DNS / NTP / VPN | 192.168.100.5  |
| legacy-web-01 | Web Server / Reverse Proxy  | 192.168.100.10 |
| legacy-app-01 | Application Server / WAS    | 192.168.100.20 |
| legacy-db-01  | Database Server             | 192.168.100.30 |

---

# 관리자 계정

| 항목     | 값        |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# 사전 조건

다음 문서가 모두 완료되어 있어야 한다.

```text
01 VMware Installation
02 Network Configuration
03 OPS Server Build
04 Web Server Build
05 WAS Server Build
06 DB Server Build
07 DNS Server Build
08 NTP Server Build
09 Database Backup
10 VPN Server Build
```

---

# 1. 서버 SSH 접속 검증

관리 PC에서 각 서버에 SSH 접속한다.

```bash
ssh admin@192.168.100.5
```

```bash
ssh admin@192.168.100.10
```

```bash
ssh admin@192.168.100.20
```

```bash
ssh admin@192.168.100.30
```

모든 서버에 정상 접속되어야 한다.

---

# 2. 서버 상태 검증

각 서버에서 아래 명령어를 실행한다.

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

서버별 예상 결과는 다음과 같다.

| 서버          | 예상 Hostname |
| ------------- | ------------- |
| legacy-ops-01 | legacy-ops-01 |
| legacy-web-01 | legacy-web-01 |
| legacy-app-01 | legacy-app-01 |
| legacy-db-01  | legacy-db-01  |

IP 주소를 확인한다.

```bash
ip addr
```

서버별 예상 IP는 다음과 같다.

| 서버          | 예상 IP           |
| ------------- | ----------------- |
| legacy-ops-01 | 192.168.100.5/24  |
| legacy-web-01 | 192.168.100.10/24 |
| legacy-app-01 | 192.168.100.20/24 |
| legacy-db-01  | 192.168.100.30/24 |

서버 부팅 시간을 확인한다.

```bash
uptime
```

---

# 3. 네트워크 통신 검증

운영 서버에 접속한다.

```bash
ssh admin@192.168.100.5
```

운영 서버에서 Web 서버로 통신을 확인한다.

```bash
ping -c 4 192.168.100.10
```

운영 서버에서 WAS 서버로 통신을 확인한다.

```bash
ping -c 4 192.168.100.20
```

운영 서버에서 DB 서버로 통신을 확인한다.

```bash
ping -c 4 192.168.100.30
```

Web 서버에서 WAS 서버로 통신을 확인한다.

```bash
ssh admin@192.168.100.10
```

```bash
ping -c 4 192.168.100.20
```

WAS 서버에서 DB 서버로 통신을 확인한다.

```bash
ssh admin@192.168.100.20
```

```bash
ping -c 4 192.168.100.30
```

모든 Ping 테스트가 정상 응답되어야 한다.

---

# 4. DNS 서비스 검증

운영 서버에 접속한다.

```bash
ssh admin@192.168.100.5
```

BIND9 서비스 상태를 확인한다.

```bash
sudo systemctl status bind9
```

예상 결과

```text
active (running)
```

DNS 포트를 확인한다.

```bash
sudo ss -tulnp | grep ':53'
```

DNS 조회를 수행한다.

```bash
dig @192.168.100.5 tripkey.shop
```

예상 결과

```text
192.168.100.10
```

```bash
dig @192.168.100.5 www.tripkey.shop
```

예상 결과

```text
192.168.100.10
```

클라이언트 서버에서 DNS 조회를 확인한다.

```bash
ssh admin@192.168.100.10
```

```bash
dig tripkey.shop
```

```bash
dig www.tripkey.shop
```

정상적으로 `192.168.100.10`이 반환되어야 한다.

---

# 5. NTP 서비스 검증

운영 서버에 접속한다.

```bash
ssh admin@192.168.100.5
```

Chrony 서비스 상태를 확인한다.

```bash
sudo systemctl status chrony
```

예상 결과

```text
active (running)
```

운영 서버 동기화 상태를 확인한다.

```bash
chronyc tracking
```

예상 결과

```text
Leap status     : Normal
```

클라이언트 서버에서 시간 소스를 확인한다.

Web 서버

```bash
ssh admin@192.168.100.10
chronyc sources
```

WAS 서버

```bash
ssh admin@192.168.100.20
chronyc sources
```

DB 서버

```bash
ssh admin@192.168.100.30
chronyc sources
```

예상 결과

```text
192.168.100.5
```

각 서버의 시간 동기화 상태를 확인한다.

```bash
timedatectl
```

예상 결과

```text
System clock synchronized: yes
NTP service: active
```

---

# 6. Web 서비스 검증

Web 서버에 접속한다.

```bash
ssh admin@192.168.100.10
```

Nginx 상태를 확인한다.

```bash
sudo systemctl status nginx
```

예상 결과

```text
active (running)
```

80 포트를 확인한다.

```bash
sudo ss -tulnp | grep ':80'
```

Web 서버 내부에서 접속을 확인한다.

```bash
curl http://localhost
```

관리 PC 또는 내부 서버에서 접속을 확인한다.

```bash
curl http://192.168.100.10
```

DNS 이름 기반으로 접속을 확인한다.

```bash
curl http://tripkey.shop
```

---

# 7. WAS 서비스 검증

WAS 서버에 접속한다.

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

예상 결과

```text
was   running
```

컨테이너 목록을 확인한다.

```bash
docker ps
```

8000 포트를 확인한다.

```bash
sudo ss -tulnp | grep ':8000'
```

WAS 서버 자체 응답을 확인한다.

```bash
curl http://localhost:8000
```

```bash
curl http://192.168.100.20:8000
```

정상 응답이 반환되어야 한다.

---

# 8. Reverse Proxy 검증

Web 서버에 접속한다.

```bash
ssh admin@192.168.100.10
```

Web 서버에서 WAS 서버를 직접 호출한다.

```bash
curl http://192.168.100.20:8000
```

정상 응답이 반환되어야 한다.

Nginx Reverse Proxy를 통해 호출한다.

```bash
curl http://192.168.100.10
```

정상 응답이 반환되어야 한다.

DNS 이름 기반으로 호출한다.

```bash
curl http://tripkey.shop
```

정상 응답이 반환되어야 한다.

Nginx Access Log를 확인한다.

```bash
sudo tail -f /var/log/nginx/access.log
```

관리 PC 브라우저에서 접속한다.

```text
http://tripkey.shop
```

접속 로그가 기록되어야 한다.

로그 확인 종료

```text
Ctrl + C
```

---

# 9. DB 서비스 검증

DB 서버에 접속한다.

```bash
ssh admin@192.168.100.30
```

MariaDB 서비스 상태를 확인한다.

```bash
sudo systemctl status mariadb
```

예상 결과

```text
active (running)
```

3306 포트를 확인한다.

```bash
sudo ss -tulnp | grep ':3306'
```

데이터베이스 목록을 확인한다.

```bash
sudo mysql -e "SHOW DATABASES;"
```

예상 결과에 아래 데이터베이스가 포함되어야 한다.

```text
integrated
```

---

# 10. WAS → DB 연동 검증

WAS 서버에 접속한다.

```bash
ssh admin@192.168.100.20
```

DB 서버 통신을 확인한다.

```bash
ping -c 4 192.168.100.30
```

MariaDB Client 설치 여부를 확인한다.

```bash
mariadb --version
```

설치되어 있지 않다면 설치한다.

```bash
sudo apt install mariadb-client -y
```

DB 접속을 확인한다.

```bash
mariadb \
-h 192.168.100.30 \
-u app \
-p
```

비밀번호를 입력한다.

```text
app-password
```

접속 후 데이터베이스를 확인한다.

```sql
SHOW DATABASES;
```

예상 결과에 아래 데이터베이스가 포함되어야 한다.

```text
integrated
```

종료한다.

```sql
EXIT;
```

---

# 11. Backup 서비스 검증

DB 서버에 접속한다.

```bash
ssh admin@192.168.100.30
```

백업 디렉터리를 확인한다.

```bash
ls -lh /infra/backup/mariadb
```

백업 파일이 존재해야 한다.

```text
mariadb-YYYY-MM-DD.sql
```

백업 스크립트를 확인한다.

```bash
ls -al /usr/local/bin/db_backup.sh
```

수동 백업을 수행한다.

```bash
sudo /usr/local/bin/db_backup.sh
```

백업 파일을 다시 확인한다.

```bash
ls -lh /infra/backup/mariadb
```

백업 파일 내용을 검증한다.

```bash
head -20 /infra/backup/mariadb/mariadb-$(date +%F).sql
```

Cron 등록 상태를 확인한다.

```bash
sudo crontab -l
```

예상 결과

```text
0 2 * * * /usr/local/bin/db_backup.sh
```

---

# 12. VPN 서비스 검증

운영 서버에 접속한다.

```bash
ssh admin@192.168.100.5
```

WireGuard 서비스 상태를 확인한다.

```bash
sudo systemctl status wg-quick@wg0
```

예상 결과

```text
active (exited)
```

WireGuard 인터페이스를 확인한다.

```bash
ip addr show wg0
```

예상 결과

```text
10.10.10.1/24
```

UDP 51820 포트를 확인한다.

```bash
sudo ss -ulpn | grep 51820
```

WireGuard 상태를 확인한다.

```bash
sudo wg
```

VPN 클라이언트 연결 후 내부 서버 통신을 확인한다.

```bash
ping 10.10.10.1
```

```bash
ping 192.168.100.5
```

```bash
ping 192.168.100.10
```

```bash
ping 192.168.100.20
```

```bash
ping 192.168.100.30
```

VPN 연결 후 내부 서버 SSH 접속을 확인한다.

```bash
ssh admin@192.168.100.5
```

```bash
ssh admin@192.168.100.10
```

```bash
ssh admin@192.168.100.20
```

```bash
ssh admin@192.168.100.30
```

---

# 13. 전체 서비스 흐름 검증

최종 서비스 흐름은 다음과 같다.

```text
User
↓
tripkey.shop
↓
legacy-web-01
192.168.100.10
↓
Nginx Reverse Proxy
↓
legacy-app-01
192.168.100.20:8000
↓
WAS Container
↓
legacy-db-01
192.168.100.30:3306
```

관리 PC 브라우저에서 접속한다.

```text
http://tripkey.shop
```

정상적으로 서비스 응답이 표시되어야 한다.

---

# 최종 검증 체크리스트

| 검증 항목                   | 결과 |
| --------------------------- | ---- |
| 서버 4대 SSH 접속 성공      | □    |
| 서버별 Hostname 정상        | □    |
| 서버별 고정 IP 정상         | □    |
| 서버 간 Ping 통신 성공      | □    |
| DNS 조회 성공               | □    |
| tripkey.shop 이름 해석 성공 | □    |
| Chrony 시간 동기화 성공     | □    |
| Nginx 서비스 정상           | □    |
| WAS 컨테이너 정상 실행      | □    |
| 8000 포트 수신 확인         | □    |
| Reverse Proxy 응답 확인     | □    |
| MariaDB 서비스 정상         | □    |
| WAS → DB 접속 성공          | □    |
| 백업 파일 생성 확인         | □    |
| Cron 등록 확인              | □    |
| WireGuard 서비스 정상       | □    |
| VPN 내부망 접근 성공        | □    |
| 전체 서비스 흐름 검증 완료  | □    |

---

# 검증 완료 기준

다음 항목을 모두 만족하면 레거시 온프레미스 환경 구축이 완료된 것으로 판단한다.

- 서버 4대 정상 운영
- SSH 접속 정상
- 고정 IP 정상 적용
- 서버 간 통신 정상
- DNS 정상 동작
- NTP 정상 동기화
- Web 서비스 정상 동작
- WAS 컨테이너 정상 실행
- Reverse Proxy 정상 동작
- MariaDB 정상 동작
- WAS → DB 접속 성공
- Backup 정상 수행
- VPN 정상 접속
- 전체 서비스 흐름 검증 성공

---

# Snapshot 생성

최종 검증 완료 후 각 서버에서 Snapshot을 생성한다.

VMware 메뉴

```text
VM
 └─ Snapshot
      └─ Take Snapshot
```

설정

```text
Name
11-System-Validation-Complete
```
