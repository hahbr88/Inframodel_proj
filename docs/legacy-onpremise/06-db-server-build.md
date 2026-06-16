# 데이터베이스 서버 구축

## 개요

본 문서는 레거시 온프레미스 환경의 데이터베이스 서버(`legacy-db-01`) 구축 절차를 정의한다.

데이터베이스 서버는 서비스 데이터를 저장하고 관리하는 역할을 수행한다.

본 환경에서는 MariaDB를 사용하며 애플리케이션 서버(`legacy-app-01`)와 연동하여 서비스를 제공한다.

데이터베이스 백업은 `09 Database Backup` 문서에서 진행한다.

---

# 서버 정보

| 항목      | 설정값                       |
| ------- | ------------------------- |
| 서버명     | legacy-db-01              |
| 역할      | Database Server           |
| 운영체제    | Ubuntu Server 24.04.4 LTS |
| CPU     | 2 Core                    |
| Memory  | 4 GB                      |
| Storage | 60 GB                     |
| IP 주소   | 192.168.100.30/24         |
| DB Port | 3306                      |

---

# 관리자 계정

| 항목       | 값         |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# 사전 조건

```text
01 VMware Installation
02 Network Configuration
05 WAS Server Build
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
Static hostname: legacy-db-01
```

```bash
ip addr
```

예상 결과

```text
192.168.100.30/24
```

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

---

# MariaDB 설치

```bash
sudo apt install mariadb-server -y
```

버전 확인

```bash
mariadb --version
```

---

# MariaDB 서비스 확인

```bash
sudo systemctl status mariadb
```

예상 결과

```text
active (running)
```

자동 시작 확인

```bash
sudo systemctl is-enabled mariadb
```

예상 결과

```text
enabled
```

---

# MariaDB 보안 설정

```bash
sudo mysql_secure_installation
```

설정

```text
Switch to unix_socket authentication?      Y
Change the root password?                  Y
Remove anonymous users?                    Y
Disallow root login remotely?              Y
Remove test database and access to it?     Y
Reload privilege tables now?               Y
```

---

# MariaDB 접속 확인

```bash
sudo mysql
```

버전 확인

```sql
SELECT VERSION();
```

종료

```sql
EXIT;
```

---

# 외부 접속 설정

설정 백업

```bash
sudo cp \
/etc/mysql/mariadb.conf.d/50-server.cnf \
/etc/mysql/mariadb.conf.d/50-server.cnf.bak
```

설정 수정

```bash
sudo vi /etc/mysql/mariadb.conf.d/50-server.cnf
```

수정

```text
bind-address = 0.0.0.0
```

---

# MariaDB 재시작

```bash
sudo systemctl restart mariadb
```

```bash
sudo systemctl status mariadb
```

---

# 데이터베이스 생성

MariaDB 접속

```bash
sudo mysql
```

DB 생성

```sql
CREATE DATABASE integrated;
```

확인

```sql
SHOW DATABASES;
```

예상 결과

```text
integrated
```

---

# 서비스 계정 생성

```sql
CREATE USER 'app'@'192.168.100.20'
IDENTIFIED BY 'app-password';
```

```sql
GRANT ALL PRIVILEGES
ON integrated.*
TO 'app'@'192.168.100.20';
```

```sql
FLUSH PRIVILEGES;
```

확인

```sql
SELECT User, Host
FROM mysql.user;
```

종료

```sql
EXIT;
```

---

# 3306 포트 확인

```bash
sudo ss -tulnp | grep ':3306'
```

예상 결과

```text
0.0.0.0:3306
```

---

# 방화벽 설정

현재 상태 확인

```bash
sudo ufw status
```

MariaDB 포트 허용

```bash
sudo ufw allow from 192.168.100.20 to any port 3306 proto tcp
```

상태 확인

```bash
sudo ufw status
```

---

# DB 서버 자체 로그인 검증

```bash
mariadb -u app -p
```

비밀번호

```text
app-password
```

종료

```sql
EXIT;
```

---

# WAS 서버 접속

```bash
ssh admin@192.168.100.20
```

---

# WAS → DB 통신 확인

```bash
ping -c 4 192.168.100.30
```

정상 응답 확인

---

# WAS → DB 로그인 검증

MariaDB Client 설치

```bash
sudo apt install mariadb-client -y
```

DB 접속

```bash
mariadb \
-h 192.168.100.30 \
-u app \
-p
```

비밀번호

```text
app-password
```

로그인 성공 확인

종료

```sql
EXIT;
```

---

# 서비스 구조 검증

```text
Internet
↓
legacy-web-01
192.168.100.10
↓
legacy-app-01
192.168.100.20
↓
legacy-db-01
192.168.100.30
```

정상 동작 확인

---

# 재부팅 검증

```bash
sudo reboot
```

재접속

```bash
ssh admin@192.168.100.30
```

상태 확인

```bash
sudo systemctl status mariadb
```

```bash
sudo ss -tulnp | grep ':3306'
```

```bash
sudo mysql -e "SHOW DATABASES;"
```

---

# Snapshot 생성

```text
VM
 └─ Snapshot
      └─ Take Snapshot
```

```text
Name
06-DB-Complete
```

---

# 구축 완료 기준

* admin 계정 로그인 가능
* MariaDB 설치 완료
* MariaDB 서비스 정상 동작
* 자동 시작 확인
* bind-address 설정 완료
* 데이터베이스 생성 완료
* 서비스 계정 생성 완료
* 권한 부여 완료
* 3306 포트 수신 확인
* 방화벽 설정 완료
* WAS 서버 접속 성공
* WAS → DB 로그인 성공
* 재부팅 후 정상 동작
* Snapshot 생성 완료

---

# 다음 단계

```text
07 DNS Server Build
```
