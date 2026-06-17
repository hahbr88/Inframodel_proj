#!/usr/bin/env bash
set -Eeuo pipefail

# MariaDB 서버를 실행할 때만 SST 인증 설정을 생성한다.
if [[ "${1:-}" == "mariadbd" || "${1:-}" == "mysqld" || "${1:0:1}" == "-" ]]; then
    if [[ ! -r /run/secrets/mariadb_sst_password ]]; then
        echo "ERROR: /run/secrets/mariadb_sst_password 파일을 읽을 수 없습니다." >&2
        exit 1
    fi

    sst_password="$(cat /run/secrets/mariadb_sst_password)"
    if [[ -z "$sst_password" ]]; then
        echo "ERROR: SST 비밀번호가 비어 있습니다." >&2
        exit 1
    fi

    # docker compose의 file secret은 호스트 파일 권한에 따라 mysql 사용자에게
    # 읽히지 않을 수 있다. initdb 스크립트가 읽을 수 있는 런타임 사본을 만든다.
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

    # 최초 배포 또는 전체 클러스터 재기동 때 안전 노드 하나에만 1을 지정한다.
    if [[ "${GALERA_BOOTSTRAP:-0}" == "1" ]]; then
        set -- "$@" --wsrep-new-cluster
    fi
fi

exec /usr/local/bin/docker-entrypoint.sh "$@"
