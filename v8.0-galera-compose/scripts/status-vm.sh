#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

container="${GALERA_CONTAINER_NAME:-galera-db}"
root_password_file="secrets/root_password.txt"

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker command not found." >&2
    exit 1
fi

if [[ ! -r "$root_password_file" ]]; then
    echo "ERROR: $root_password_file not found or not readable." >&2
    exit 1
fi

if ! docker inspect "$container" >/dev/null 2>&1; then
    echo "ERROR: container '$container' not found." >&2
    echo "Run: docker compose --env-file .env -f compose.vm.yaml up -d" >&2
    exit 1
fi

container_status="$(docker inspect --format '{{.State.Status}}' "$container")"
health_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container")"
restart_count="$(docker inspect --format '{{.RestartCount}}' "$container")"

printf 'CONTAINER=%s STATUS=%s HEALTH=%s RESTARTS=%s\n' \
    "$container" "$container_status" "$health_status" "$restart_count"

if [[ "$container_status" != "running" ]]; then
    echo "ERROR: container is not running. Recent logs:" >&2
    docker logs --tail 80 "$container" >&2 || true
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

print_wsrep_status() {
    local rows

    if ! rows="$(docker exec "$container" mariadb \
        --protocol=socket \
        -uroot \
        -p"$root_password" \
        --batch \
        --skip-column-names \
        -e "$query" 2>/dev/null)"; then
        echo "INFO: MariaDB socket query is not ready yet."
        return 1
    fi

    printf '%-15s %-10s %-12s %-16s %-10s %-8s %-12s\n' \
        NODE READ_ONLY CLUSTER_SIZE CLUSTER_STATUS CONNECTED READY LOCAL_STATE
    printf '%s\n' "$rows" \
      | awk '{printf "%-15s %-10s %-12s %-16s %-10s %-8s %-12s\n", $1,$2,$3,$4,$5,$6,$7}'
}

if [[ "$health_status" == "starting" ]]; then
    if print_wsrep_status; then
        echo "INFO: Docker health is still starting, but MariaDB already answers status queries."
        echo "INFO: If READY=ON and LOCAL_STATE=Synced, wait briefly or recreate with the latest compose.vm.yaml healthcheck."
    else
        echo "INFO: MariaDB/Galera is still starting or joining the cluster."
        echo "Wait and retry: ./scripts/status-vm.sh"
    fi
    exit 0
fi

if [[ "$health_status" == "unhealthy" ]]; then
    print_wsrep_status || true
    echo "ERROR: container is unhealthy. Recent logs:" >&2
    docker logs --tail 120 "$container" >&2 || true
    exit 1
fi

print_wsrep_status
