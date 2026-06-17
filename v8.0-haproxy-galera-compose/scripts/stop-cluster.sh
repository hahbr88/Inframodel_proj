#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

docker compose --env-file .env stop haproxy
docker compose --env-file .env stop db3
docker compose --env-file .env stop db2
docker compose --env-file .env stop db1
