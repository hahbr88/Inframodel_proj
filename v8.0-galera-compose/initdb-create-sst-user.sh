#!/usr/bin/env bash
# MariaDB official entrypoint sources files in /docker-entrypoint-initdb.d.
# Do not enable `set -u` here; it leaks into the parent entrypoint and can
# break its later `$1` checks with "unbound variable".

sst_password_file="/run/mariadb-galera/mariadb_sst_password"
if [[ ! -r "$sst_password_file" ]]; then
    sst_password_file="/run/secrets/mariadb_sst_password"
fi

sst_password="$(cat "$sst_password_file")"

# 가이드의 생성 명령은 16진수 비밀번호를 만들므로 SQL 특수문자가 포함되지 않는다.
if [[ ! "$sst_password" =~ ^[A-Fa-f0-9]+$ ]]; then
    echo "ERROR: SST 비밀번호는 openssl rand -hex로 생성한 16진수 문자열을 사용하십시오." >&2
    return 1
fi

docker_process_sql <<SQL
CREATE USER IF NOT EXISTS 'sstuser'@'localhost' IDENTIFIED BY '${sst_password}';
ALTER USER 'sstuser'@'localhost' IDENTIFIED BY '${sst_password}';
GRANT RELOAD, PROCESS, LOCK TABLES, BINLOG MONITOR, REPLICA MONITOR
    ON *.* TO 'sstuser'@'localhost';
FLUSH PRIVILEGES;
SQL
