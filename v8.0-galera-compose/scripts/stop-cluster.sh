#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# node1이 마지막으로 정상 종료되도록 순서를 고정한다.
docker compose stop galera-node3
docker compose stop galera-node2
docker compose stop galera-node1
