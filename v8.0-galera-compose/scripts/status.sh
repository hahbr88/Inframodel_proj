#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

root_password="$(cat secrets/root_password.txt)"
query="SELECT @@hostname AS node, @@read_only AS read_only, (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_CLUSTER_SIZE') AS cluster_size, (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_CLUSTER_STATUS') AS cluster_status, (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_LOCAL_STATE_COMMENT') AS local_state, (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='WSREP_READY') AS ready;"

printf '%-15s %-10s %-12s %-16s %-12s %-8s\n' NODE READ_ONLY CLUSTER_SIZE CLUSTER_STATUS LOCAL_STATE READY
for container in galera-node1 galera-node2 galera-node3; do
    if ! docker inspect "$container" >/dev/null 2>&1; then
        printf '%-15s %s\n' "$container" "container-not-found"
        continue
    fi
    docker exec "$container" mariadb -uroot -p"$root_password" --batch --skip-column-names -e "$query" \
      | awk '{printf "%-15s %-10s %-12s %-16s %-12s %-8s\n", $1,$2,$3,$4,$5,$6}'
done
