#!/usr/bin/env bash
set -Eeuo pipefail

root_password_file="${ROOT_PASSWORD_FILE:-secrets/root_password.txt}"
container="${GALERA_CONTAINER_NAME:-galera-db}"

if [[ ! -r "$root_password_file" ]]; then
    echo "ERROR: $root_password_file is not readable." >&2
    exit 1
fi

root_password="$(cat "$root_password_file")"
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

docker exec "$container" mariadb \
  --protocol=socket \
  -uroot \
  -p"$root_password" \
  --batch \
  --skip-column-names \
  -e "$query"
