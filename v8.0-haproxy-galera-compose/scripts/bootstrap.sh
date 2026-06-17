#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

for file in .env secrets/root_password.txt secrets/app_password.txt secrets/sst_password.txt; do
    if [[ ! -s "$file" ]]; then
        echo "ERROR: missing required file: $file" >&2
        exit 1
    fi
done

wait_healthy() {
    local container="$1"
    local status

    for _ in $(seq 1 180); do
        status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container" 2>/dev/null || true)"
        if [[ "$status" == "healthy" ]]; then
            echo "$container: healthy"
            return 0
        fi

        if [[ "$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null || true)" == "exited" ]]; then
            docker logs --tail 100 "$container" >&2 || true
            return 1
        fi

        sleep 2
    done

    echo "ERROR: $container healthcheck timeout" >&2
    docker logs --tail 100 "$container" >&2 || true
    return 1
}

docker compose --env-file .env build

GALERA_BOOTSTRAP_NODE1=1 docker compose --env-file .env up -d db1
wait_healthy db1

docker compose --env-file .env up -d db2
wait_healthy db2

docker compose --env-file .env up -d db3
wait_healthy db3

GALERA_BOOTSTRAP_NODE1=0 docker compose --env-file .env up -d --force-recreate db1
wait_healthy db1

docker compose --env-file .env up -d haproxy
docker compose --env-file .env ps
bash scripts/status.sh
