#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

root_password="$(cat secrets/root_password.txt)"
query="
SELECT
  @@hostname AS node,
  @@read_only AS read_only,
  (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_CLUSTER_SIZE') AS cluster_size,
  (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_CLUSTER_STATUS') AS cluster_status,
  (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_CONNECTED') AS connected,
  (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_READY') AS ready,
  (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_LOCAL_STATE_COMMENT') AS local_state;
"

printf '%-8s %-10s %-12s %-16s %-10s %-8s %-12s\n' \
    NODE READ_ONLY CLUSTER_SIZE CLUSTER_STATUS CONNECTED READY LOCAL_STATE

for container in db1 db2 db3; do
    if ! docker inspect "$container" >/dev/null 2>&1; then
        printf '%-8s %s\n' "$container" "container-not-found"
        continue
    fi

    docker exec "$container" mariadb \
        --protocol=socket \
        -uroot \
        -p"$root_password" \
        --batch \
        --skip-column-names \
        -e "$query" \
      | awk '{printf "%-8s %-10s %-12s %-16s %-10s %-8s %-12s\n", $1,$2,$3,$4,$5,$6,$7}'
done

echo
docker compose --env-file .env ps haproxy
