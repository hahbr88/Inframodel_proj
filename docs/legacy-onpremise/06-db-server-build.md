# 데이터베이스 서버 구축

## 개요

본 문서는 레거시 온프레미스 환경의 데이터베이스 서버(legacy-db-01) 구축 절차를 정의한다.

데이터베이스 서버는 서비스 데이터를 저장하고 관리하는 역할을 수행한다.

본 환경에서는 MariaDB를 사용하며, 애플리케이션 서버(legacy-app-01)와 연동하여 서비스를 제공한다.

데이터베이스 백업 구성은 별도 문서(09-db-backup.md)에서 진행한다.

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

---

# 서버 상태 확인

서버 정보를 확인한다.

```bash
hostnamectl
```

IP 주소를 확인한다.

```bash
ip addr
```

---

# 패키지 업데이트

패키지 저장소 정보를 최신 상태로 갱신한다.

```bash
sudo apt update
```

패키지를 최신 상태로 업데이트한다.

```bash
sudo apt upgrade -y
```

---

# MariaDB 설치

MariaDB를 설치한다.

```bash
sudo apt install mariadb-server -y
```

설치 완료 후 서비스 상태를 확인한다.

```bash
sudo systemctl status mariadb
```

서비스가 active (running) 상태로 표시되어야 한다.

---

# 자동 시작 확인

서버 재부팅 시 자동 실행 여부를 확인한다.

```bash
sudo systemctl is-enabled mariadb
```

확인 결과는 아래와 같아야 한다.

```text
enabled
```

---

# MariaDB 접속 확인

MariaDB에 접속한다.

```bash
sudo mysql
```

버전을 확인한다.

```sql
SELECT VERSION();
```

종료한다.

```sql
EXIT;
```

---

# 외부 접속 설정 확인

애플리케이션 서버(legacy-app-01)가 데이터베이스 서버에 접속할 수 있어야 한다.

현재 bind-address 설정을 확인한다.

```bash
sudo grep -R "bind-address" /etc/mysql/mariadb.conf.d/
```

설정 파일을 확인한다.

```bash
sudo vi /etc/mysql/mariadb.conf.d/50-server.cnf
```

애플리케이션 서버 연동이 가능하도록 설정되어 있는지 확인한다.

설정 변경 후에는 서비스를 재시작한다.

```bash
sudo systemctl restart mariadb
```

---

# 데이터베이스 생성

프로젝트에서 사용할 데이터베이스를 생성한다.

데이터베이스명은 프로젝트 산출물 기준으로 적용한다.

```sql
CREATE DATABASE <DB_NAME>;
```

생성된 데이터베이스를 확인한다.

```sql
SHOW DATABASES;
```

---

# 서비스 계정 생성

애플리케이션 서버와 데이터베이스 연동을 위한 전용 계정을 생성한다.

전체 허용(%) 방식은 사용하지 않는다.

애플리케이션 서버 IP만 허용한다.

```sql
CREATE USER '<DB_USER>'@'192.168.100.20'
IDENTIFIED BY '<DB_PASSWORD>';
```

생성된 계정에 데이터베이스 권한을 부여한다.

```sql
GRANT ALL PRIVILEGES
ON <DB_NAME>.*
TO '<DB_USER>'@'192.168.100.20';
```

권한을 적용한다.

```sql
FLUSH PRIVILEGES;
```

생성된 계정을 확인한다.

```sql
SELECT User, Host
FROM mysql.user;
```

---

# 포트 확인

MariaDB 서비스가 정상적으로 동작하는지 확인한다.

```bash
ss -tulpen | grep ':3306'
```

3306 포트가 LISTEN 상태로 확인되어야 한다.

---

# 애플리케이션 서버 연동 확인

애플리케이션 서버에서 데이터베이스 서버 통신을 확인한다.

애플리케이션 서버에서 실행한다.

```bash
ping -c 4 192.168.100.30
```

정상적으로 응답이 반환되어야 한다.

필요 시 생성한 서비스 계정으로 DB 접속을 확인한다.

```bash
mysql -h 192.168.100.30 -u <DB_USER> -p
```

---

# 운영 구조

서비스 요청은 아래 순서로 처리된다.

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

데이터베이스 서버는 애플리케이션 서버를 통해서만 접근한다.

---

# 점검 항목

| 점검 항목              | 확인 |
| ------------------ | -- |
| 서버 접속 확인           | □  |
| 서버명 확인             | □  |
| IP 주소 확인           | □  |
| MariaDB 설치 완료      | □  |
| MariaDB 실행 확인      | □  |
| 자동 시작 확인           | □  |
| bind-address 설정 확인 | □  |
| 데이터베이스 생성 완료       | □  |
| 서비스 계정 생성 완료       | □  |
| 권한 부여 완료           | □  |
| 3306 포트 확인         | □  |
| 애플리케이션 서버 연동 확인    | □  |

---

# 구축 완료 기준

다음 항목을 모두 만족하면 데이터베이스 서버 구축이 완료된 것으로 판단한다.

* MariaDB 설치 완료
* MariaDB 정상 실행
* 데이터베이스 생성 완료
* 서비스 계정 생성 완료
* 권한 부여 완료
* 3306 포트 수신 확인
* 애플리케이션 서버 연동 성공

---

# 다음 단계

데이터베이스 서버 구축이 완료되면 아래 문서를 진행한다.

* 07-dns-bind9.md
