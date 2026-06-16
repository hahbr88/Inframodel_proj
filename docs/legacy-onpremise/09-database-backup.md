# 데이터베이스 백업 구성

## 개요

본 문서는 레거시 온프레미스 환경의 데이터베이스 백업 구성 절차를 정의한다.

데이터베이스 서버는 서비스 운영에 필요한 데이터를 저장하므로 정기적인 백업이 필요하다.

본 환경에서는 MariaDB Dump를 이용하여 데이터베이스를 백업하며 Cron을 통해 자동화한다.

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

# 관리자 계정

| 항목     | 값        |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# 사전 조건

```text
06 DB Server Build
```

완료 상태여야 한다.

---

# 서버 상태 확인

DB 서버 접속

```bash
ssh admin@192.168.100.30
```

현재 로그인 계정 확인

```bash
whoami
```

예상 결과

```text
admin
```

서버명 확인

```bash
hostnamectl
```

예상 결과

```text
legacy-db-01
```

IP 확인

```bash
ip addr
```

예상 결과

```text
192.168.100.30
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

# 백업 디렉터리 생성

백업 디렉터리를 생성한다.

```bash
sudo mkdir -p /infra/backup/mariadb
```

확인

```bash
ls -ld /infra/backup/mariadb
```

---

# 백업 스크립트 생성

```bash
sudo vi /usr/local/bin/db_backup.sh
```

내용 입력

```bash
#!/bin/bash

BACKUP_DIR="/infra/backup/mariadb"
DATE=$(date +%F)

sudo mysqldump --all-databases \
> ${BACKUP_DIR}/mariadb-${DATE}.sql

find ${BACKUP_DIR} \
-name "*.sql" \
-mtime +7 \
-delete
```

저장 후 종료

---

# 실행 권한 부여

```bash
sudo chmod +x /usr/local/bin/db_backup.sh
```

확인

```bash
ls -al /usr/local/bin/db_backup.sh
```

---

# 수동 백업 테스트

```bash
sudo /usr/local/bin/db_backup.sh
```

오류 없이 종료되어야 한다.

---

# 백업 파일 확인

```bash
ls -lh /infra/backup/mariadb
```

예상 결과

```text
mariadb-YYYY-MM-DD.sql
```

---

# 백업 파일 검증

파일 앞부분 확인

```bash
head -20 /infra/backup/mariadb/mariadb-$(date +%F).sql
```

데이터베이스 생성 구문 확인

```bash
grep "CREATE DATABASE" \
/infra/backup/mariadb/mariadb-$(date +%F).sql
```

정상적으로 SQL 구문이 출력되어야 한다.

---

# Cron 등록

Cron 편집기 실행

```bash
sudo crontab -e
```

추가

```cron
0 2 * * * /usr/local/bin/db_backup.sh
```

의미

```text
매일 오전 02:00 백업 수행
```

---

# Cron 등록 확인

```bash
sudo crontab -l
```

예상 결과

```text
0 2 * * * /usr/local/bin/db_backup.sh
```

---

# 보관 정책 확인

현재 보관 중인 파일 확인

```bash
ls -lh /infra/backup/mariadb
```

7일이 지난 백업 파일은 자동 삭제된다.

---

# 서비스 구조 확인

```text
legacy-db-01
      │
      ▼
MariaDB Dump
      │
      ▼
/infra/backup/mariadb
      │
      ▼
7일 보관
```

---

# 재부팅 검증

```bash
sudo reboot
```

재접속

```bash
ssh admin@192.168.100.30
```

Cron 확인

```bash
sudo crontab -l
```

백업 디렉터리 확인

```bash
ls -ld /infra/backup/mariadb
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
09-Backup-Complete
```

---

# 구축 완료 기준

- admin 계정 로그인 가능
- 백업 디렉터리 생성 완료
- 백업 스크립트 생성 완료
- 실행 권한 부여 완료
- 수동 백업 성공
- 백업 파일 생성 확인
- Cron 등록 완료
- Cron 등록 확인 완료
- 7일 보관 정책 적용 완료
- 백업 파일 검증 완료
- 재부팅 후 정상 동작
- Snapshot 생성 완료

---

# 다음 단계

```text
10 VPN Server Build
```
