#!/usr/bin/env bash
# MariaDB official entrypoint sources files in /docker-entrypoint-initdb.d.
# Do not enable `set -u` here because it leaks into the parent entrypoint.

sst_password_file="/run/mariadb-galera/mariadb_sst_password"
if [[ ! -r "$sst_password_file" ]]; then
    sst_password_file="/run/secrets/mariadb_sst_password"
fi

sst_password="$(cat "$sst_password_file")"

if [[ ! "$sst_password" =~ ^[A-Fa-f0-9]+$ ]]; then
    echo "ERROR: SST password must be generated with openssl rand -hex." >&2
    return 1
fi

docker_process_sql <<SQL
CREATE USER IF NOT EXISTS 'sstuser'@'localhost' IDENTIFIED BY '${sst_password}';
ALTER USER 'sstuser'@'localhost' IDENTIFIED BY '${sst_password}';
GRANT RELOAD, PROCESS, LOCK TABLES, BINLOG MONITOR, REPLICA MONITOR
    ON *.* TO 'sstuser'@'localhost';

CREATE USER IF NOT EXISTS 'haproxy_check'@'%' IDENTIFIED BY '';
FLUSH PRIVILEGES;
SQL
