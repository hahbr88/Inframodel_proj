#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${1:-}" == "mariadbd" || "${1:-}" == "mysqld" || "${1:-}" == -* ]]; then
    if [[ ! -r /run/secrets/mariadb_sst_password ]]; then
        echo "ERROR: /run/secrets/mariadb_sst_password is not readable." >&2
        exit 1
    fi

    sst_password="$(cat /run/secrets/mariadb_sst_password)"
    if [[ -z "$sst_password" ]]; then
        echo "ERROR: SST password is empty." >&2
        exit 1
    fi

    install -d -m 0700 -o mysql -g mysql /run/mariadb-galera
    printf '%s' "$sst_password" > /run/mariadb-galera/mariadb_sst_password
    chown mysql:mysql /run/mariadb-galera/mariadb_sst_password
    chmod 0400 /run/mariadb-galera/mariadb_sst_password

    umask 077
    cat > /etc/mysql/conf.d/99-sst-auth.cnf <<CNF
[mariadbd]
wsrep_sst_auth=sstuser:${sst_password}
CNF
    chown mysql:mysql /etc/mysql/conf.d/99-sst-auth.cnf

    if [[ "${GALERA_BOOTSTRAP:-0}" == "1" ]]; then
        set -- "$@" --wsrep-new-cluster
    fi
fi

exec /usr/local/bin/docker-entrypoint.sh "$@"
