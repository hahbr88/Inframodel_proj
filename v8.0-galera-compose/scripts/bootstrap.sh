#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

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

# 이 스크립트는 새 클러스터 또는 안전하게 전체 종료한 뒤 node1을 기준으로 재기동할 때 사용한다.
docker compose build
GALERA_BOOTSTRAP_NODE1=1 docker compose up -d galera-node1
wait_healthy galera-node1

docker compose up -d galera-node2
wait_healthy galera-node2

docker compose up -d galera-node3
wait_healthy galera-node3

# node1에서 bootstrap 플래그를 제거한다. node2와 node3가 Primary Component를 유지하므로 안전하게 재합류한다.
GALERA_BOOTSTRAP_NODE1=0 docker compose up -d --force-recreate galera-node1
wait_healthy galera-node1

scripts/status.sh
