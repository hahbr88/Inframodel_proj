# 데이터베이스 백업 구성

## 개요

본 문서는 레거시 온프레미스 환경의 데이터베이스 백업 구성 절차를 정의한다.

데이터베이스 서버는 서비스 운영에 필요한 데이터를 저장하므로 정기적인 백업이 필요하다.

본 환경에서는 MariaDB Dump를 이용하여 데이터베이스를 백업하며, Cron을 통해 자동화한다.

---

# 백업 정책

| 항목      | 설정값       |
| --------- | ------------ |
| 대상 서버 | legacy-db-01 |
| 백업 방식 | MariaDB Dump |
| 실행 주기 | Daily 02:00  |
| 보관 기간 | 7일          |
| 실행 방식 | Cron         |

---

# 서버 정보

| 항목    | 값              |
| ------- | --------------- |
| 서버명  | legacy-db-01    |
| 역할    | Database Server |
| IP 주소 | 192.168.100.30  |

---

# 백업 디렉터리 생성

백업 파일 저장 디렉터리를 생성한다.

```bash
sudo mkdir -p /backup/mariadb
```

디렉터리를 확인한다.

```bash
ls -ld /backup/mariadb
```

---

# 백업 스크립트 생성

백업 스크립트를 생성한다.

```bash
sudo vi /usr/local/bin/db_backup.sh
```

내용 작성

```bash
#!/bin/bash

BACKUP_DIR="/backup/mariadb"
DATE=$(date +%F)

mysqldump --all-databases > ${BACKUP_DIR}/mariadb-${DATE}.sql
```

실행 권한을 부여한다.

```bash
sudo chmod +x /usr/local/bin/db_backup.sh
```

---

# 백업 범위 설명

현재는 서비스 데이터베이스 이름이 확정되지 않은 상태이므로 서버에 존재하는 모든 데이터베이스를 백업하도록 구성한다.

```bash
mysqldump --all-databases
```

명령어는 MariaDB 서버 내의 모든 데이터베이스를 하나의 SQL 파일로 저장한다.

향후 서비스 데이터베이스 이름이 확정될 경우 특정 데이터베이스만 백업하도록 변경할 수 있다.

예시

```bash
mysqldump DATABASE_NAME > database.sql
```

현재 단계에서는 전체 데이터베이스 백업을 기본 정책으로 사용한다.

---

# 백업 테스트

수동으로 백업을 수행한다.

```bash
sudo /usr/local/bin/db_backup.sh
```

백업 파일 생성 여부를 확인한다.

```bash
ls -lh /backup/mariadb
```

예시

```text
mariadb-2026-06-15.sql
```

---

# MariaDB 인증 방식 확인

백업 테스트 수행 시 MariaDB 인증 정책에 따라 권한 오류가 발생할 수 있다.

예시

```text
Access denied
```

이 경우 MariaDB 계정을 지정하여 백업을 수행한다.

```bash
mysqldump -u root -p --all-databases > backup.sql
```

명령어 실행 후 비밀번호 입력 창이 표시된다.

```text
Enter password:
```

MariaDB root 계정 비밀번호를 입력한 후 Enter를 누른다.

비밀번호 입력 시 화면에는 아무 문자도 표시되지 않는 것이 정상이다.

현재 문서는 기본 백업 방식 기준으로 작성하였으며, 실제 MariaDB 인증 정책에 따라 명령어를 조정할 수 있다.

---

# Cron 등록

Cron 편집기를 실행한다.

```bash
sudo crontab -e
```

아래 내용을 등록한다.

```cron
0 2 * * * /usr/local/bin/db_backup.sh
```

의미

```text
매일 오전 02:00 백업 수행
```

---

# Cron 등록 확인

등록된 작업을 확인한다.

```bash
sudo crontab -l
```

---

# 백업 파일 보관 정책

백업 파일은 최근 7일만 보관한다.

7일이 지난 백업 파일은 자동 삭제한다.

백업 스크립트를 수정한다.

```bash
sudo vi /usr/local/bin/db_backup.sh
```

추가

```bash
find /backup/mariadb -name "*.sql" -mtime +7 -delete
```

예시

```bash
#!/bin/bash

BACKUP_DIR="/backup/mariadb"
DATE=$(date +%F)

mysqldump --all-databases > ${BACKUP_DIR}/mariadb-${DATE}.sql

find /backup/mariadb -name "*.sql" -mtime +7 -delete
```

---

# 백업 파일 확인

현재 보관 중인 백업 파일을 확인한다.

```bash
ls -lh /backup/mariadb
```

---

# 백업 파일 검증

백업 파일 존재 여부를 확인한다.

````bash
ls /backup/mariadb
백업 파일 내부 내용을 확인한다.

head -20 /backup/mariadb/mariadb-2026-06-15.sql
SQL 구문이 정상적으로 생성되었는지 확인한다.

---

# 점검 항목

| 점검 항목          | 확인 |
| ------------------ | ---- |
| 백업 디렉터리 생성 | □    |
| 백업 스크립트 생성 | □    |
| 실행 권한 부여     | □    |
| 수동 백업 성공     | □    |
| Cron 등록 완료     | □    |
| 자동 백업 확인     | □    |
| 7일 보관 정책 적용 | □    |

---

# 구축 완료 기준

다음 항목을 모두 만족하면 백업 구성이 완료된 것으로 판단한다.

- 백업 디렉터리 생성 완료
- 백업 스크립트 생성 완료
- 수동 백업 성공
- Cron 등록 완료
- 자동 백업 수행 확인
- 백업 파일 생성 확인
- 7일 보관 정책 적용 완료

---

# 운영 구조

```text
legacy-db-01
      │
      ▼
MariaDB Dump
      │
      ▼
/backup/mariadb
      │
      ▼
7일 보관
````

---

# 다음 단계

데이터베이스 백업 구성이 완료되면 아래 문서를 진행한다.

- 10-wireguard-vpn.md
